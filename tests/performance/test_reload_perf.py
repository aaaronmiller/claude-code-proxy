"""Performance test for ConfigResolver SSE notification latency (T083).

Measures time from resolver.set() call to subscriber being notified.
Assert p95 < 1 second (leaves headroom under 5s SC-002 budget).
"""

from __future__ import annotations

import time
import statistics
import threading
from src.core.config_resolver import resolver, ConfigLayer, FieldSchema


def test_reload_perf() -> None:
    # Ensure resolver initialized
    resolver._ensure_initialized()

    # Register a dedicated test schema if absent
    test_field = "perf_reload_field"
    if test_field not in resolver._schemas:
        resolver.register_schema(
            test_field, FieldSchema(type=str, default="default", is_secret=False)
        )

    event = threading.Event()
    received_time = None

    def subscriber(change: dict) -> None:
        nonlocal received_time
        received_time = time.perf_counter()
        event.set()

    resolver.subscribe(subscriber)

    latencies_ms = []
    iterations = 1000

    for i in range(iterations):
        event.clear()
        t0 = time.perf_counter()
        resolver.set(test_field, f"value{i}", source_layer=ConfigLayer.CLI)
        # Wait for notification (should be fast)
        event.wait(timeout=1.0)
        t1 = time.perf_counter()
        assert received_time is not None, "Subscriber not called"
        latency = (t1 - t0) * 1000
        latencies_ms.append(latency)
        received_time = None  # reset for next iteration

    p95 = statistics.quantiles(latencies_ms, n=20)[-1]
    assert p95 < 1000, f"p95 notification latency {p95:.1f}ms exceeds 1s threshold"


if __name__ == "__main__":
    test_reload_perf()
    print("✓ T083 reload performance test passed (p95 < 1s)")
