#!/usr/bin/env python3
"""Local relay for using a Headroom instance on another machine."""

from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from typing import Iterable

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse


HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def _headers(items: Iterable[tuple[str, str]]) -> dict[str, str]:
    return {k: v for k, v in items if k.lower() not in HOP_BY_HOP}


def create_app(remote_url: str, timeout: float) -> FastAPI:
    remote = remote_url.rstrip("/")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.client = httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=10.0))
        try:
            yield
        finally:
            await app.state.client.aclose()

    app = FastAPI(title="Headroom Relay", lifespan=lifespan)

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def relay(path: str, request: Request):
        url = f"{remote}/{path}"
        if request.url.query:
            url = f"{url}?{request.url.query}"

        client: httpx.AsyncClient = request.app.state.client
        upstream = client.build_request(
            request.method,
            url,
            headers=_headers(request.headers.items()),
            content=await request.body(),
        )
        response = await client.send(upstream, stream=True)
        headers = _headers(response.headers.items())

        async def body():
            try:
                async for chunk in response.aiter_raw():
                    yield chunk
            finally:
                await response.aclose()

        if request.method == "GET" and path in {"health", "livez", "readyz"}:
            content = await response.aread()
            await response.aclose()
            return Response(content, status_code=response.status_code, headers=headers)

        return StreamingResponse(body(), status_code=response.status_code, headers=headers)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Relay local traffic to a remote Headroom server")
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, default=8787)
    parser.add_argument("--remote-url", required=True)
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args()

    uvicorn.run(
        create_app(args.remote_url, args.timeout),
        host=args.listen_host,
        port=args.listen_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
