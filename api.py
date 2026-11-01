"""FastAPI boundary for the stdlib key-value store core."""

from __future__ import annotations

import asyncio
import os
from collections import Counter
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel

from store import KeyValueStore


class SetRequest(BaseModel):
    value: str


class ValueResponse(BaseModel):
    key: str
    value: str


class DeleteResponse(BaseModel):
    deleted: bool


class Metrics:
    def __init__(self) -> None:
        self._requests: Counter[str] = Counter()

    def record(self, operation: str) -> None:
        self._requests[operation] += 1

    def prometheus(self) -> str:
        lines = ["# HELP kv_requests_total Requests by operation.", "# TYPE kv_requests_total counter"]
        lines.extend(f'kv_requests_total{{operation="{name}"}} {count}' for name, count in sorted(self._requests.items()))
        return "\n".join(lines) + "\n"


def create_app(log_path: str | Path = Path(os.getenv("KV_LOG_PATH", "data/store.log"))) -> FastAPI:
    store = KeyValueStore(log_path)
    metrics = Metrics()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        store.compact()

    app = FastAPI(title="Key-Value Store API", version="0.3.0", lifespan=lifespan)

    @app.put("/v1/keys/{key}", response_model=ValueResponse)
    async def set_value(key: str, request: SetRequest) -> ValueResponse:
        metrics.record("set")
        try:
            await asyncio.to_thread(store.set, key, request.value)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        return ValueResponse(key=key, value=request.value)

    @app.get("/v1/keys/{key}", response_model=ValueResponse)
    async def get_value(key: str) -> ValueResponse:
        metrics.record("get")
        try:
            value = await asyncio.to_thread(store.get, key)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        if value is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="key not found")
        return ValueResponse(key=key, value=value)

    @app.delete("/v1/keys/{key}", response_model=DeleteResponse)
    async def delete_value(key: str) -> DeleteResponse:
        metrics.record("delete")
        try:
            deleted = await asyncio.to_thread(store.delete, key)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="key not found")
        return DeleteResponse(deleted=True)

    @app.get("/metrics", include_in_schema=False)
    async def get_metrics() -> Response:
        return Response(metrics.prometheus(), media_type="text/plain; version=0.0.4")

    return app


app = create_app()
