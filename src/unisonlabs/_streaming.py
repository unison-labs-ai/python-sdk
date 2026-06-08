"""Server-Sent Events streaming helpers.

Provides thin ``Stream`` / ``AsyncStream`` wrappers for SSE responses so
callers can iterate over typed chunks:

    with client.with_streaming_response.some_endpoint() as resp:
        for event in resp.stream:
            ...

The Unison brain API does not currently expose SSE endpoints, but these
classes are exported so downstream code can rely on the stable type surface
and so that integration tests can import them without ``ImportError``.
"""
from __future__ import annotations

import json
from types import TracebackType
from typing import Any, Generic, Iterator, AsyncIterator, TypeVar

import httpx

_T = TypeVar("_T")


class Stream(Generic[_T]):
    """Iterate over a synchronous SSE response."""

    response: httpx.Response

    def __init__(self, *, cast_to: type[_T], response: httpx.Response) -> None:
        self.response = response
        self._cast_to = cast_to
        self._iterator = self._stream()

    def __next__(self) -> _T:
        return next(self._iterator)

    def __iter__(self) -> Iterator[_T]:
        yield from self._iterator

    def _stream(self) -> Iterator[_T]:
        try:
            for line in self.response.iter_lines():
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue
                payload = line[len("data:"):].strip()
                if payload == "[DONE]":
                    break
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                yield self._cast_to(**data) if isinstance(data, dict) else data  # type: ignore[call-arg]
        finally:
            self.response.close()

    def __enter__(self) -> "Stream[_T]":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self.response.close()


class AsyncStream(Generic[_T]):
    """Iterate over an asynchronous SSE response."""

    response: httpx.Response

    def __init__(self, *, cast_to: type[_T], response: httpx.Response) -> None:
        self.response = response
        self._cast_to = cast_to

    def __aiter__(self) -> "AsyncStream[_T]":
        self._aiterator = self._stream()
        return self

    async def __anext__(self) -> _T:
        return await self._aiterator.__anext__()

    async def _stream(self) -> AsyncIterator[_T]:
        try:
            async for line in self.response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue
                payload = line[len("data:"):].strip()
                if payload == "[DONE]":
                    break
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                yield self._cast_to(**data) if isinstance(data, dict) else data  # type: ignore[call-arg]
        finally:
            await self.response.aclose()

    async def __aenter__(self) -> "AsyncStream[_T]":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.response.aclose()
