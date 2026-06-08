"""Review resource — dedup/merge review (requires brain:admin scope)."""

from __future__ import annotations

from typing import Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import (
    ConflictResolveResponse,
    ConflictsResponse,
    MergesResponse,
    UndoMergeResponse,
)


class ReviewResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._t = transport

    def conflicts(self) -> ConflictsResponse:
        """List pending dedup merge pairs. Requires brain:admin."""
        data = self._t.request("GET", "/v1/brain/review/conflicts")
        return ConflictsResponse(**data)

    def resolve_conflict(self, conflict_id: str, verdict: str) -> ConflictResolveResponse:
        """Resolve a conflict. verdict: 'merge' | 'distinct'. Requires brain:admin."""
        data = self._t.request(
            "POST",
            f"/v1/brain/review/conflicts/{conflict_id}",
            json={"verdict": verdict},
        )
        return ConflictResolveResponse(**data)

    def merges(self, *, limit: Optional[int] = None) -> MergesResponse:
        """List recent merges (undo feed). Requires brain:admin."""
        params = {}
        if limit is not None:
            params["limit"] = limit
        data = self._t.request("GET", "/v1/brain/review/merges", params=params)
        return MergesResponse(**data)

    def undo_merge(self, merge_id: str) -> UndoMergeResponse:
        """Enqueue an unmerge. Requires brain:admin."""
        data = self._t.request("POST", f"/v1/brain/review/merges/{merge_id}/undo")
        return UndoMergeResponse(**data)


class AsyncReviewResource:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._t = transport

    async def conflicts(self) -> ConflictsResponse:
        data = await self._t.request("GET", "/v1/brain/review/conflicts")
        return ConflictsResponse(**data)

    async def resolve_conflict(self, conflict_id: str, verdict: str) -> ConflictResolveResponse:
        data = await self._t.request(
            "POST",
            f"/v1/brain/review/conflicts/{conflict_id}",
            json={"verdict": verdict},
        )
        return ConflictResolveResponse(**data)

    async def merges(self, *, limit: Optional[int] = None) -> MergesResponse:
        params = {}
        if limit is not None:
            params["limit"] = limit
        data = await self._t.request("GET", "/v1/brain/review/merges", params=params)
        return MergesResponse(**data)

    async def undo_merge(self, merge_id: str) -> UndoMergeResponse:
        data = await self._t.request("POST", f"/v1/brain/review/merges/{merge_id}/undo")
        return UndoMergeResponse(**data)
