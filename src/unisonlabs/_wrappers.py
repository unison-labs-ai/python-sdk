"""with_raw_response / with_streaming_response resource wrappers.

Each wrapper class mirrors the corresponding resource API but returns a
``RawResponse`` (already-read body + parsed value + headers) or a
``StreamingResponse`` context manager (body not read yet).

This lets callers inspect response headers, stream downloads, or bypass
parsing entirely without changing application code structurally:

    raw = client.with_raw_response.documents.get("/path")
    print(raw.headers["x-request-id"])
    doc = raw.parse()

    with client.with_streaming_response.documents.get("/path") as stream:
        for chunk in stream.iter_bytes(4096):
            ...
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from ._http import AsyncHttpTransport, HttpTransport
from ._response import AsyncStreamingResponse, RawResponse, StreamingResponse
from .types import (
    BrainDocument,
    BrainStatus,
    ContextResponse,
    DeleteDocResponse,
    FsListResponse,
    FsReadResponse,
    GrepResponse,
    ListResponse,
    NeighborsResponse,
    SearchResponse,
    WhoAmIResponse,
)

# ---------------------------------------------------------------------------
# Sync wrappers
# ---------------------------------------------------------------------------


class RawDocumentsResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._t = transport

    def _raw(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        return self._t.request_raw(method, path, **kwargs)

    def search(self, q: str, *, k: Optional[int] = None, **kw: Any) -> RawResponse[SearchResponse]:
        params: Dict[str, Any] = {"q": q}
        if k is not None:
            params["k"] = k
        params.update(kw)
        raw = self._raw("GET", "/v1/brain/search", params=params)
        return RawResponse(raw=raw, parsed=SearchResponse(**raw.json()))

    def context(self, q: str, *, k: Optional[int] = None, **kw: Any) -> RawResponse[ContextResponse]:
        params: Dict[str, Any] = {"q": q}
        if k is not None:
            params["k"] = k
        params.update(kw)
        raw = self._raw("GET", "/v1/brain/context", params=params)
        return RawResponse(raw=raw, parsed=ContextResponse(**raw.json()))

    def get(self, path: str) -> RawResponse[BrainDocument]:
        from .resources.documents import _parse_doc

        raw = self._raw("GET", "/v1/brain/doc", params={"path": path})
        return RawResponse(raw=raw, parsed=_parse_doc(raw.json()))

    def write(self, path: str, body_md: str, **kw: Any) -> RawResponse[BrainDocument]:
        from ._fs_contract import resolve_write_path
        from .resources.documents import _parse_doc

        resolved = resolve_write_path(path)
        payload: Dict[str, Any] = {"path": resolved, "bodyMd": body_md, **kw}
        raw = self._raw("PUT", "/v1/brain/doc", json=payload)
        return RawResponse(raw=raw, parsed=_parse_doc(raw.json()))

    def delete(self, path: str) -> RawResponse[DeleteDocResponse]:
        raw = self._raw("DELETE", "/v1/brain/doc", params={"path": path})
        return RawResponse(raw=raw, parsed=DeleteDocResponse(**raw.json()))

    def list(self, *, prefix: Optional[str] = None, **kw: Any) -> RawResponse[ListResponse]:
        params: Dict[str, Any] = {}
        if prefix is not None:
            params["prefix"] = prefix
        params.update(kw)
        raw = self._raw("GET", "/v1/brain/list", params=params)
        return RawResponse(raw=raw, parsed=ListResponse(**raw.json()))

    def grep(self, pattern: str, **kw: Any) -> RawResponse[GrepResponse]:
        params: Dict[str, Any] = {"pattern": pattern, **kw}
        raw = self._raw("GET", "/v1/brain/grep", params=params)
        return RawResponse(raw=raw, parsed=GrepResponse(**raw.json()))

    def fs_list(self, path: str) -> RawResponse[FsListResponse]:
        raw = self._raw("GET", "/v1/brain/fs", params={"path": path})
        return RawResponse(raw=raw, parsed=FsListResponse(**raw.json()))

    def fs_read(self, path: str) -> RawResponse[FsReadResponse]:
        raw = self._raw("GET", "/v1/brain/fs/read", params={"path": path})
        return RawResponse(raw=raw, parsed=FsReadResponse(**raw.json()))

    def neighbors(self, id_or_path: str, **kw: Any) -> RawResponse[NeighborsResponse]:
        params: Dict[str, Any] = {"idOrPath": id_or_path, **kw}
        raw = self._raw("GET", "/v1/brain/neighbors", params=params)
        return RawResponse(raw=raw, parsed=NeighborsResponse(**raw.json()))

    def status(self) -> RawResponse[BrainStatus]:
        raw = self._raw("GET", "/v1/brain/status")
        return RawResponse(raw=raw, parsed=BrainStatus(**raw.json()))


class StreamingDocumentsResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._t = transport

    def get(self, path: str) -> StreamingResponse[BrainDocument]:
        raw = self._t.request_stream("GET", "/v1/brain/doc", params={"path": path})
        return StreamingResponse(request_fn=lambda: None, raw=raw)

    def fs_read(self, path: str) -> StreamingResponse[FsReadResponse]:
        raw = self._t.request_stream("GET", "/v1/brain/fs/read", params={"path": path})
        return StreamingResponse(request_fn=lambda: None, raw=raw)


class UnisonBrainWithRawResponse:
    """``client.with_raw_response.*`` — exposes raw httpx.Response + parsed value."""

    def __init__(self, transport: HttpTransport) -> None:
        self.documents = RawDocumentsResource(transport)

    def whoami(self) -> RawResponse[WhoAmIResponse]:
        raw = self.documents._raw("GET", "/v1/auth/whoami")
        return RawResponse(raw=raw, parsed=WhoAmIResponse(**raw.json()))

    def status(self) -> RawResponse[BrainStatus]:
        return self.documents.status()


class UnisonBrainWithStreamingResponse:
    """``client.with_streaming_response.*`` — streams the response body."""

    def __init__(self, transport: HttpTransport) -> None:
        self.documents = StreamingDocumentsResource(transport)


# ---------------------------------------------------------------------------
# Async wrappers
# ---------------------------------------------------------------------------


class AsyncRawDocumentsResource:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._t = transport

    async def _raw(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        return await self._t.request_raw(method, path, **kwargs)

    async def search(self, q: str, *, k: Optional[int] = None, **kw: Any) -> RawResponse[SearchResponse]:
        params: Dict[str, Any] = {"q": q}
        if k is not None:
            params["k"] = k
        params.update(kw)
        raw = await self._raw("GET", "/v1/brain/search", params=params)
        return RawResponse(raw=raw, parsed=SearchResponse(**raw.json()))

    async def context(self, q: str, *, k: Optional[int] = None, **kw: Any) -> RawResponse[ContextResponse]:
        params: Dict[str, Any] = {"q": q}
        if k is not None:
            params["k"] = k
        params.update(kw)
        raw = await self._raw("GET", "/v1/brain/context", params=params)
        return RawResponse(raw=raw, parsed=ContextResponse(**raw.json()))

    async def get(self, path: str) -> RawResponse[BrainDocument]:
        from .resources.documents import _parse_doc

        raw = await self._raw("GET", "/v1/brain/doc", params={"path": path})
        return RawResponse(raw=raw, parsed=_parse_doc(raw.json()))

    async def write(self, path: str, body_md: str, **kw: Any) -> RawResponse[BrainDocument]:
        from ._fs_contract import resolve_write_path
        from .resources.documents import _parse_doc

        resolved = resolve_write_path(path)
        payload: Dict[str, Any] = {"path": resolved, "bodyMd": body_md, **kw}
        raw = await self._raw("PUT", "/v1/brain/doc", json=payload)
        return RawResponse(raw=raw, parsed=_parse_doc(raw.json()))

    async def delete(self, path: str) -> RawResponse[DeleteDocResponse]:
        raw = await self._raw("DELETE", "/v1/brain/doc", params={"path": path})
        return RawResponse(raw=raw, parsed=DeleteDocResponse(**raw.json()))

    async def list(self, *, prefix: Optional[str] = None, **kw: Any) -> RawResponse[ListResponse]:
        params: Dict[str, Any] = {}
        if prefix is not None:
            params["prefix"] = prefix
        params.update(kw)
        raw = await self._raw("GET", "/v1/brain/list", params=params)
        return RawResponse(raw=raw, parsed=ListResponse(**raw.json()))

    async def status(self) -> RawResponse[BrainStatus]:
        raw = await self._raw("GET", "/v1/brain/status")
        return RawResponse(raw=raw, parsed=BrainStatus(**raw.json()))


class AsyncStreamingDocumentsResource:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._t = transport

    async def get(self, path: str) -> AsyncStreamingResponse[BrainDocument]:
        raw = await self._t.request_raw("GET", "/v1/brain/doc", params={"path": path})
        return AsyncStreamingResponse(raw=raw)

    async def fs_read(self, path: str) -> AsyncStreamingResponse[FsReadResponse]:
        raw = await self._t.request_raw("GET", "/v1/brain/fs/read", params={"path": path})
        return AsyncStreamingResponse(raw=raw)


class AsyncUnisonBrainWithRawResponse:
    """``async_client.with_raw_response.*``"""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self.documents = AsyncRawDocumentsResource(transport)

    async def whoami(self) -> RawResponse[WhoAmIResponse]:
        raw = await self.documents._raw("GET", "/v1/auth/whoami")
        return RawResponse(raw=raw, parsed=WhoAmIResponse(**raw.json()))

    async def status(self) -> RawResponse[BrainStatus]:
        return await self.documents.status()


class AsyncUnisonBrainWithStreamingResponse:
    """``async_client.with_streaming_response.*``"""

    def __init__(self, transport: AsyncHttpTransport) -> None:
        self.documents = AsyncStreamingDocumentsResource(transport)
