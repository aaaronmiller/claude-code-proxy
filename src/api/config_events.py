"""SSE endpoint for live configuration changes.

Streams `config.change` events from ConfigResolver to connected clients.
Each event is a JSON object:
  { "field_path": "...", "after_value": "...", "source_layer": "...", "seq": 123 }

Clients reconnect automatically; we use exponential backoff on the client side.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from src.core.config_resolver import get_resolver

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Broker queue (sync → async bridge) ─────────────────────────────────────────
# ConfigResolver calls subscribers from a worker thread (T053). We need to
# safely cross into the asyncio event loop. A sync queue + dedicated async
# consumer task provides that bridge.
_broker_queue: asyncio.Queue = None  # initialized lazily in _get_broker()
_broker_lock = threading.Lock()


def _get_broker() -> asyncio.Queue:
    """Get or create the broker queue on the main event loop."""
    global _broker_queue
    with _broker_lock:
        if _broker_queue is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            _broker_queue = asyncio.Queue()
        return _broker_queue


# This event will be set once the async broadcaster task starts
_broadcaster_started = threading.Event()
_broadcaster_task: asyncio.Task | None = None


def _config_change_callback(event: dict) -> None:
    """Sync callback invoked by ConfigResolver.set().
    Enqueue the event into the async broker for SSE broadcast.
    """
    broker = _get_broker()
    # Schedule put on the event loop thread-safe
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broker.put(event), loop)
        else:
            # Fallback: create a new loop in this thread (rare)
            asyncio.run(broker.put(event))
    except Exception as e:
        logger.debug(f"Failed to enqueue config change event: {e}")


# Register ourselves as a ConfigResolver subscriber on import
def _register():
    resolver = get_resolver()
    resolver.subscribe(_config_change_callback)


_register()


# ── SSE endpoint ────────────────────────────────────────────────────────────────

# Per-client connection queues
_clients: set[asyncio.Queue] = set()
_clients_lock = asyncio.Lock()


async def _broadcaster():
    """Background task that pulls from broker queue and fans out to all clients."""
    global _broker_queue
    broker = _get_broker()
    while True:
        event = await broker.get()
        # Serialize once for all clients
        data_json = json.dumps(event)
        async with _clients_lock:
            dead = set()
            for q in _clients:
                try:
                    q.put_nowait(data_json)
                except asyncio.QueueFull:
                    dead.add(q)
            # Clean up dead clients
            _clients.difference_update(dead)


@router.get("/config/events")
async def config_events(request: Request):
    """SSE endpoint that pushes config change events as they occur."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    async with _clients_lock:
        _clients.add(queue)

    # Ensure broadcaster task is running
    global _broadcaster_task
    if _broadcaster_task is None or _broadcaster_task.done():
        _broadcaster_task = asyncio.create_task(_broadcaster())

    try:

        async def event_generator():
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {"event": "config.change", "data": data}
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent timeout
                    yield {"event": "ping", "data": ""}

        return EventSourceResponse(event_generator())
    finally:
        async with _clients_lock:
            _clients.discard(queue)
