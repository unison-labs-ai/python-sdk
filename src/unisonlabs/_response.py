"""Raw-response and streaming-response wrappers for resource methods.

These allow callers to access the underlying ``httpx.Response`` without
having to instrument the transport layer:

    with client.with_streaming_response.documents.get("/path") as resp:
        for chunk in resp.iter_bytes():
            ...

    raw = client.with_raw_response.documents.get("/path")
    raw.headers["x-request-id"]
    doc = raw.parse()
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, AsyncIterator, Callable, Generic, Iterator, TypeVar

import httpx

_T = TypeVar("_T")


class RawResponse(Generic[_T]):
    """Wraps a parsed response value alongside its raw ``httpx.Response``."""

    def __init__(self, *, raw: httpx.Response, parsed: _T) -> None:
        self.http_response = raw
        self._parsed = parsed

    @property
    def headers(self) -> httpx.Headers:
        return self.http_response.headers

    @property
    def status_code(self) -> int:
        return self.http_response.status_code

    @property
    def request_id(self) -> str | None:
        return self.http_response.headers.get("x-request-id")

    def parse(self) -> _T:
        """Return the already-parsed typed response value."""
        return self._parsed

    def text(self) -> str:
        return self.http_response.text

    def json(self) -> object:
        return self.http_response.json()

    def read(self) -> bytes:
        return self.http_response.read()


class StreamingResponse(Generic[_T]):
    """Context-manager wrapper that exposes a streaming ``httpx.Response``.

    The response body is *not* read until you consume it via iteration or
    one of the read helpers.  The connection is released when the context
    manager exits.
    """

    def __init__(self, *, request_fn: Callable[[], Any], raw: httpx.Response) -> None:
        self.http_response = raw
        self._request_fn = request_fn

    @property
    def headers(self) -> httpx.Headers:
        return self.http_response.headers

    @property
    def status_code(self) -> int:
        return self.http_response.status_code

    def iter_bytes(self, chunk_size: int | None = None) -> Iterator[bytes]:
        yield from self.http_response.iter_bytes(chunk_size)

    def iter_text(self, chunk_size: int | None = None) -> Iterator[str]:
        yield from self.http_response.iter_text(chunk_size)

    def iter_lines(self) -> Iterator[str]:
        yield from self.http_response.iter_lines()

    def read(self) -> bytes:
        return self.http_response.read()

    def text(self) -> str:
        return self.http_response.text

    def close(self) -> None:
        self.http_response.close()

    def __enter__(self) -> "StreamingResponse[_T]":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncStreamingResponse(Generic[_T]):
    """Async context-manager equivalent of ``StreamingResponse``."""

    def __init__(self, *, raw: httpx.Response) -> None:
        self.http_response = raw

    @property
    def headers(self) -> httpx.Headers:
        return self.http_response.headers

    @property
    def status_code(self) -> int:
        return self.http_response.status_code

    async def iter_bytes(self, chunk_size: int | None = None) -> AsyncIterator[bytes]:
        async for chunk in self.http_response.aiter_bytes(chunk_size):
            yield chunk

    async def iter_text(self, chunk_size: int | None = None) -> AsyncIterator[str]:
        async for chunk in self.http_response.aiter_text(chunk_size):
            yield chunk

    async def iter_lines(self) -> AsyncIterator[str]:
        async for line in self.http_response.aiter_lines():
            yield line

    async def read(self) -> bytes:
        return await self.http_response.aread()

    async def close(self) -> None:
        await self.http_response.aclose()

    async def __aenter__(self) -> "AsyncStreamingResponse[_T]":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
