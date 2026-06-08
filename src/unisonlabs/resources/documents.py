"""Documents resource — CRUD + tag + search + grep on brain documents."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .._fs_contract import resolve_write_path
from .._http import AsyncHttpTransport, HttpTransport
from ..types import (
    BrainDocument,
    DeleteDocResponse,
    FsListResponse,
    FsReadResponse,
    GrepResponse,
    ListResponse,
    NeighborsResponse,
    SearchResponse,
    ShareResponse,
    TagDocResponse,
)


def _parse_doc(data: Any) -> BrainDocument:
    if isinstance(data, dict):
        if "document" in data:
            return BrainDocument(**data["document"])
        return BrainDocument(**data)
    raise ValueError(f"Unexpected document data: {type(data)}")


class DocumentsResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._t = transport

    def search(
        self,
        q: str,
        *,
        k: Optional[int] = None,
        kind: Optional[List[str]] = None,
        tag: Optional[List[str]] = None,
        memory_type: Optional[str] = None,
        as_of: Optional[str] = None,
    ) -> SearchResponse:
        """Hybrid keyword+semantic search over the brain."""
        params: Dict[str, Any] = {"q": q}
        if k is not None:
            params["k"] = k
        if kind is not None:
            params["kind"] = kind
        if tag is not None:
            params["tag"] = tag
        if memory_type is not None:
            params["memoryType"] = memory_type
        if as_of is not None:
            params["asOf"] = as_of
        data = self._t.request("GET", "/v1/brain/search", params=params)
        return SearchResponse(**data)

    def grep(
        self,
        pattern: str,
        *,
        case_sensitive: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> GrepResponse:
        """Regex scan over document bodies."""
        params: Dict[str, Any] = {"pattern": pattern}
        if case_sensitive is not None:
            params["caseSensitive"] = str(case_sensitive).lower()
        if limit is not None:
            params["limit"] = limit
        data = self._t.request("GET", "/v1/brain/grep", params=params)
        return GrepResponse(**data)

    def get(self, path: str) -> BrainDocument:
        """Read a single document (includes body)."""
        data = self._t.request("GET", "/v1/brain/doc", params={"path": path})
        return _parse_doc(data)

    def write(
        self,
        path: str,
        body_md: str,
        *,
        kind: Optional[str] = None,
        title: Optional[str] = None,
        tldr: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: Optional[str] = None,
        expected_content_hash: Optional[str] = None,
        source: Optional[Dict[str, str]] = None,
    ) -> BrainDocument:
        """Write (create or overwrite) a document."""
        resolved = resolve_write_path(path)
        payload: Dict[str, Any] = {"path": resolved, "bodyMd": body_md}
        if kind is not None:
            payload["kind"] = kind
        if title is not None:
            payload["title"] = title
        if tldr is not None:
            payload["tldr"] = tldr
        if tags is not None:
            payload["tags"] = tags
        if visibility is not None:
            payload["visibility"] = visibility
        if expected_content_hash is not None:
            payload["expectedContentHash"] = expected_content_hash
        if source is not None:
            payload["source"] = source
        data = self._t.request("PUT", "/v1/brain/doc", json=payload)
        return _parse_doc(data)

    def edit(
        self,
        path: str,
        old_str: str,
        new_str: str,
        *,
        expected_content_hash: Optional[str] = None,
    ) -> BrainDocument:
        """Surgical in-place edit. old_str must match exactly once."""
        payload: Dict[str, Any] = {"path": path, "oldStr": old_str, "newStr": new_str}
        if expected_content_hash is not None:
            payload["expectedContentHash"] = expected_content_hash
        data = self._t.request("PATCH", "/v1/brain/doc", json=payload)
        return _parse_doc(data)

    def delete(self, path: str) -> DeleteDocResponse:
        """Delete a document."""
        data = self._t.request("DELETE", "/v1/brain/doc", params={"path": path})
        return DeleteDocResponse(**data)

    def tag(
        self,
        path: str,
        *,
        add: Optional[List[str]] = None,
        remove: Optional[List[str]] = None,
    ) -> BrainDocument:
        """Add or remove tags on a document."""
        payload: Dict[str, Any] = {"path": path}
        if add is not None:
            payload["add"] = add
        if remove is not None:
            payload["remove"] = remove
        data = self._t.request("POST", "/v1/brain/doc/tag", json=payload)
        resp = TagDocResponse(**data) if "document" in (data or {}) else None
        if resp and resp.document:
            return resp.document
        return _parse_doc(data)

    def share(self, *, kind: str, id: str) -> ShareResponse:
        """Promote a private item to tenant-visible."""
        data = self._t.request("POST", "/v1/brain/share", json={"kind": kind, "id": id})
        return ShareResponse(**data)

    def list(
        self,
        *,
        prefix: Optional[str] = None,
        kind: Optional[List[str]] = None,
        tag: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> ListResponse:
        """List documents, optionally filtered."""
        params: Dict[str, Any] = {}
        if prefix is not None:
            params["prefix"] = prefix
        if kind is not None:
            params["kind"] = kind
        if tag is not None:
            params["tag"] = tag
        if limit is not None:
            params["limit"] = limit
        data = self._t.request("GET", "/v1/brain/list", params=params)
        return ListResponse(**data)

    def fs_list(self, path: str) -> FsListResponse:
        """Directory listing."""
        data = self._t.request("GET", "/v1/brain/fs", params={"path": path})
        return FsListResponse(**data)

    def fs_read(self, path: str) -> FsReadResponse:
        """Raw content including read-only tiers."""
        data = self._t.request("GET", "/v1/brain/fs/read", params={"path": path})
        return FsReadResponse(**data)

    def neighbors(
        self,
        id_or_path: str,
        *,
        kind: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> NeighborsResponse:
        """Graph neighbors of a document or entity."""
        params: Dict[str, Any] = {"idOrPath": id_or_path}
        if kind is not None:
            params["kind"] = kind
        if limit is not None:
            params["limit"] = limit
        data = self._t.request("GET", "/v1/brain/neighbors", params=params)
        return NeighborsResponse(**data)

    def status(self):  # type: ignore[override]
        from ..types import BrainStatus

        data = self._t.request("GET", "/v1/brain/status")
        return BrainStatus(**data)


class AsyncDocumentsResource:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._t = transport

    async def search(
        self,
        q: str,
        *,
        k: Optional[int] = None,
        kind: Optional[List[str]] = None,
        tag: Optional[List[str]] = None,
        memory_type: Optional[str] = None,
        as_of: Optional[str] = None,
    ) -> SearchResponse:
        params: Dict[str, Any] = {"q": q}
        if k is not None:
            params["k"] = k
        if kind is not None:
            params["kind"] = kind
        if tag is not None:
            params["tag"] = tag
        if memory_type is not None:
            params["memoryType"] = memory_type
        if as_of is not None:
            params["asOf"] = as_of
        data = await self._t.request("GET", "/v1/brain/search", params=params)
        return SearchResponse(**data)

    async def grep(
        self,
        pattern: str,
        *,
        case_sensitive: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> GrepResponse:
        params: Dict[str, Any] = {"pattern": pattern}
        if case_sensitive is not None:
            params["caseSensitive"] = str(case_sensitive).lower()
        if limit is not None:
            params["limit"] = limit
        data = await self._t.request("GET", "/v1/brain/grep", params=params)
        return GrepResponse(**data)

    async def get(self, path: str) -> BrainDocument:
        data = await self._t.request("GET", "/v1/brain/doc", params={"path": path})
        return _parse_doc(data)

    async def write(
        self,
        path: str,
        body_md: str,
        *,
        kind: Optional[str] = None,
        title: Optional[str] = None,
        tldr: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: Optional[str] = None,
        expected_content_hash: Optional[str] = None,
        source: Optional[Dict[str, str]] = None,
    ) -> BrainDocument:
        resolved = resolve_write_path(path)
        payload: Dict[str, Any] = {"path": resolved, "bodyMd": body_md}
        if kind is not None:
            payload["kind"] = kind
        if title is not None:
            payload["title"] = title
        if tldr is not None:
            payload["tldr"] = tldr
        if tags is not None:
            payload["tags"] = tags
        if visibility is not None:
            payload["visibility"] = visibility
        if expected_content_hash is not None:
            payload["expectedContentHash"] = expected_content_hash
        if source is not None:
            payload["source"] = source
        data = await self._t.request("PUT", "/v1/brain/doc", json=payload)
        return _parse_doc(data)

    async def edit(
        self,
        path: str,
        old_str: str,
        new_str: str,
        *,
        expected_content_hash: Optional[str] = None,
    ) -> BrainDocument:
        payload: Dict[str, Any] = {"path": path, "oldStr": old_str, "newStr": new_str}
        if expected_content_hash is not None:
            payload["expectedContentHash"] = expected_content_hash
        data = await self._t.request("PATCH", "/v1/brain/doc", json=payload)
        return _parse_doc(data)

    async def delete(self, path: str) -> DeleteDocResponse:
        data = await self._t.request("DELETE", "/v1/brain/doc", params={"path": path})
        return DeleteDocResponse(**data)

    async def tag(
        self,
        path: str,
        *,
        add: Optional[List[str]] = None,
        remove: Optional[List[str]] = None,
    ) -> BrainDocument:
        payload: Dict[str, Any] = {"path": path}
        if add is not None:
            payload["add"] = add
        if remove is not None:
            payload["remove"] = remove
        data = await self._t.request("POST", "/v1/brain/doc/tag", json=payload)
        if isinstance(data, dict) and "document" in data:
            resp = TagDocResponse(**data)
            if resp.document:
                return resp.document
        return _parse_doc(data)

    async def share(self, *, kind: str, id: str) -> ShareResponse:
        data = await self._t.request("POST", "/v1/brain/share", json={"kind": kind, "id": id})
        return ShareResponse(**data)

    async def list(
        self,
        *,
        prefix: Optional[str] = None,
        kind: Optional[List[str]] = None,
        tag: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> ListResponse:
        params: Dict[str, Any] = {}
        if prefix is not None:
            params["prefix"] = prefix
        if kind is not None:
            params["kind"] = kind
        if tag is not None:
            params["tag"] = tag
        if limit is not None:
            params["limit"] = limit
        data = await self._t.request("GET", "/v1/brain/list", params=params)
        return ListResponse(**data)

    async def fs_list(self, path: str) -> FsListResponse:
        data = await self._t.request("GET", "/v1/brain/fs", params={"path": path})
        return FsListResponse(**data)

    async def fs_read(self, path: str) -> FsReadResponse:
        data = await self._t.request("GET", "/v1/brain/fs/read", params={"path": path})
        return FsReadResponse(**data)

    async def neighbors(
        self,
        id_or_path: str,
        *,
        kind: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> NeighborsResponse:
        params: Dict[str, Any] = {"idOrPath": id_or_path}
        if kind is not None:
            params["kind"] = kind
        if limit is not None:
            params["limit"] = limit
        data = await self._t.request("GET", "/v1/brain/neighbors", params=params)
        return NeighborsResponse(**data)

    async def status(self):  # type: ignore[override]
        from ..types import BrainStatus

        data = await self._t.request("GET", "/v1/brain/status")
        return BrainStatus(**data)
