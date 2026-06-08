"""Entities resource — entity graph operations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import (
    BrainEntity,
    EntityListResponse,
    EntityResolveResponse,
    FactListResponse,
)


class EntitiesResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        kind: Optional[List[str]] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> EntityListResponse:
        """List entities."""
        params: Dict[str, Any] = {}
        if kind is not None:
            params["kind"] = kind
        if status is not None:
            params["status"] = status
        if limit is not None:
            params["limit"] = limit
        data = self._t.request("GET", "/v1/brain/entities", params=params)
        return EntityListResponse(**data)

    def resolve(self, name: str, *, kind_hint: Optional[str] = None) -> EntityResolveResponse:
        """Find an entity by name (exact then fuzzy+alias)."""
        params: Dict[str, Any] = {"name": name}
        if kind_hint is not None:
            params["kindHint"] = kind_hint
        data = self._t.request("GET", "/v1/brain/entities/resolve", params=params)
        return EntityResolveResponse(**data)

    def get(self, entity_id: str) -> BrainEntity:
        """Get one entity by id."""
        data = self._t.request("GET", f"/v1/brain/entities/{entity_id}")
        if isinstance(data, dict) and "entity" in data:
            return BrainEntity(**data["entity"])
        return BrainEntity(**data)

    def upsert(
        self,
        kind: str,
        display_name: str,
        *,
        slug: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        props: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
    ) -> BrainEntity:
        """Upsert an entity."""
        payload: Dict[str, Any] = {"kind": kind, "displayName": display_name}
        if slug is not None:
            payload["slug"] = slug
        if aliases is not None:
            payload["aliases"] = aliases
        if props is not None:
            payload["props"] = props
        if status is not None:
            payload["status"] = status
        data = self._t.request("POST", "/v1/brain/entities", json=payload)
        if isinstance(data, dict) and "entity" in data:
            return BrainEntity(**data["entity"])
        return BrainEntity(**data)

    def facts(
        self,
        entity_id: str,
        *,
        as_of: Optional[str] = None,
        include_invalidated: Optional[bool] = None,
    ) -> FactListResponse:
        """Facts about a specific entity."""
        params: Dict[str, Any] = {}
        if as_of is not None:
            params["asOf"] = as_of
        if include_invalidated is not None:
            params["includeInvalidated"] = str(include_invalidated).lower()
        data = self._t.request("GET", f"/v1/brain/entities/{entity_id}/facts", params=params)
        return FactListResponse(**data)

    def timeline(
        self,
        entity_id: str,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
    ) -> FactListResponse:
        """Chronological facts for an entity."""
        params: Dict[str, Any] = {}
        if from_ is not None:
            params["from"] = from_
        if to is not None:
            params["to"] = to
        data = self._t.request("GET", f"/v1/brain/entities/{entity_id}/timeline", params=params)
        return FactListResponse(**data)


class AsyncEntitiesResource:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        kind: Optional[List[str]] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> EntityListResponse:
        params: Dict[str, Any] = {}
        if kind is not None:
            params["kind"] = kind
        if status is not None:
            params["status"] = status
        if limit is not None:
            params["limit"] = limit
        data = await self._t.request("GET", "/v1/brain/entities", params=params)
        return EntityListResponse(**data)

    async def resolve(self, name: str, *, kind_hint: Optional[str] = None) -> EntityResolveResponse:
        params: Dict[str, Any] = {"name": name}
        if kind_hint is not None:
            params["kindHint"] = kind_hint
        data = await self._t.request("GET", "/v1/brain/entities/resolve", params=params)
        return EntityResolveResponse(**data)

    async def get(self, entity_id: str) -> BrainEntity:
        data = await self._t.request("GET", f"/v1/brain/entities/{entity_id}")
        if isinstance(data, dict) and "entity" in data:
            return BrainEntity(**data["entity"])
        return BrainEntity(**data)

    async def upsert(
        self,
        kind: str,
        display_name: str,
        *,
        slug: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        props: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
    ) -> BrainEntity:
        payload: Dict[str, Any] = {"kind": kind, "displayName": display_name}
        if slug is not None:
            payload["slug"] = slug
        if aliases is not None:
            payload["aliases"] = aliases
        if props is not None:
            payload["props"] = props
        if status is not None:
            payload["status"] = status
        data = await self._t.request("POST", "/v1/brain/entities", json=payload)
        if isinstance(data, dict) and "entity" in data:
            return BrainEntity(**data["entity"])
        return BrainEntity(**data)

    async def facts(
        self,
        entity_id: str,
        *,
        as_of: Optional[str] = None,
        include_invalidated: Optional[bool] = None,
    ) -> FactListResponse:
        params: Dict[str, Any] = {}
        if as_of is not None:
            params["asOf"] = as_of
        if include_invalidated is not None:
            params["includeInvalidated"] = str(include_invalidated).lower()
        data = await self._t.request("GET", f"/v1/brain/entities/{entity_id}/facts", params=params)
        return FactListResponse(**data)

    async def timeline(
        self,
        entity_id: str,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
    ) -> FactListResponse:
        params: Dict[str, Any] = {}
        if from_ is not None:
            params["from"] = from_
        if to is not None:
            params["to"] = to
        data = await self._t.request("GET", f"/v1/brain/entities/{entity_id}/timeline", params=params)
        return FactListResponse(**data)
