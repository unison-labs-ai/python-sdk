"""Links resource — directed graph edges."""
from __future__ import annotations

from typing import Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import LinkListResponse


class LinksResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._t = transport

    def list(self, *, limit: Optional[int] = None) -> LinkListResponse:
        """List all directed graph edges."""
        params = {}
        if limit is not None:
            params["limit"] = limit
        data = self._t.request("GET", "/v1/brain/links", params=params)
        return LinkListResponse(**data)

    def create(self, from_id: str, to_id: str, kind: str) -> None:
        """Create a directed link between two nodes."""
        self._t.request("POST", "/v1/brain/links", json={"fromId": from_id, "toId": to_id, "kind": kind})


class AsyncLinksResource:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._t = transport

    async def list(self, *, limit: Optional[int] = None) -> LinkListResponse:
        params = {}
        if limit is not None:
            params["limit"] = limit
        data = await self._t.request("GET", "/v1/brain/links", params=params)
        return LinkListResponse(**data)

    async def create(self, from_id: str, to_id: str, kind: str) -> None:
        await self._t.request("POST", "/v1/brain/links", json={"fromId": from_id, "toId": to_id, "kind": kind})
