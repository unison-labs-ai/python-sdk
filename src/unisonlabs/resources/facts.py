"""Facts resource — record and query brain facts."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import BrainFact, FactListResponse, InvalidateFactResponse


class FactsResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: Optional[int] = None,
        include_invalidated: Optional[bool] = None,
    ) -> FactListResponse:
        """Browse all facts."""
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if include_invalidated is not None:
            params["includeInvalidated"] = str(include_invalidated).lower()
        data = self._t.request("GET", "/v1/brain/facts", params=params)
        return FactListResponse(**data)

    def record(
        self,
        subject_id: str,
        predicate: str,
        fact_text: str,
        *,
        object_json: Optional[Any] = None,
        object_entity_id: Optional[str] = None,
        valid_from: Optional[str] = None,
        valid_to: Optional[str] = None,
        confidence: Optional[float] = None,
        supersedes_id: Optional[str] = None,
    ) -> BrainFact:
        """Record a new fact."""
        payload: Dict[str, Any] = {
            "subjectId": subject_id,
            "predicate": predicate,
            "factText": fact_text,
        }
        if object_json is not None:
            payload["objectJson"] = object_json
        if object_entity_id is not None:
            payload["objectEntityId"] = object_entity_id
        if valid_from is not None:
            payload["validFrom"] = valid_from
        if valid_to is not None:
            payload["validTo"] = valid_to
        if confidence is not None:
            payload["confidence"] = confidence
        if supersedes_id is not None:
            payload["supersedesId"] = supersedes_id
        data = self._t.request("POST", "/v1/brain/facts", json=payload)
        if isinstance(data, dict) and "fact" in data:
            return BrainFact(**data["fact"])
        return BrainFact(**data)

    def correct(self, fact_id: str, **fields: Any) -> BrainFact:
        """Correct/supersede a fact (PATCH)."""
        data = self._t.request("PATCH", f"/v1/brain/facts/{fact_id}", json=fields)
        if isinstance(data, dict) and "fact" in data:
            return BrainFact(**data["fact"])
        return BrainFact(**data)

    def invalidate(self, fact_id: str) -> InvalidateFactResponse:
        """Soft-invalidate a fact (sets validTo=now)."""
        data = self._t.request("DELETE", f"/v1/brain/facts/{fact_id}")
        return InvalidateFactResponse(**data)


class AsyncFactsResource:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: Optional[int] = None,
        include_invalidated: Optional[bool] = None,
    ) -> FactListResponse:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if include_invalidated is not None:
            params["includeInvalidated"] = str(include_invalidated).lower()
        data = await self._t.request("GET", "/v1/brain/facts", params=params)
        return FactListResponse(**data)

    async def record(
        self,
        subject_id: str,
        predicate: str,
        fact_text: str,
        *,
        object_json: Optional[Any] = None,
        object_entity_id: Optional[str] = None,
        valid_from: Optional[str] = None,
        valid_to: Optional[str] = None,
        confidence: Optional[float] = None,
        supersedes_id: Optional[str] = None,
    ) -> BrainFact:
        payload: Dict[str, Any] = {
            "subjectId": subject_id,
            "predicate": predicate,
            "factText": fact_text,
        }
        if object_json is not None:
            payload["objectJson"] = object_json
        if object_entity_id is not None:
            payload["objectEntityId"] = object_entity_id
        if valid_from is not None:
            payload["validFrom"] = valid_from
        if valid_to is not None:
            payload["validTo"] = valid_to
        if confidence is not None:
            payload["confidence"] = confidence
        if supersedes_id is not None:
            payload["supersedesId"] = supersedes_id
        data = await self._t.request("POST", "/v1/brain/facts", json=payload)
        if isinstance(data, dict) and "fact" in data:
            return BrainFact(**data["fact"])
        return BrainFact(**data)

    async def correct(self, fact_id: str, **fields: Any) -> BrainFact:
        data = await self._t.request("PATCH", f"/v1/brain/facts/{fact_id}", json=fields)
        if isinstance(data, dict) and "fact" in data:
            return BrainFact(**data["fact"])
        return BrainFact(**data)

    async def invalidate(self, fact_id: str) -> InvalidateFactResponse:
        data = await self._t.request("DELETE", f"/v1/brain/facts/{fact_id}")
        return InvalidateFactResponse(**data)
