"""Unison brain Python SDK — synchronous and asynchronous clients."""
from __future__ import annotations

import os
from typing import Optional

import httpx

from ._exceptions import UnisonError
from ._http import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, AsyncHttpTransport, HttpTransport
from .resources.auth import AsyncAuthResource, AuthResource
from .resources.documents import AsyncDocumentsResource, DocumentsResource
from .resources.entities import AsyncEntitiesResource, EntitiesResource
from .resources.facts import AsyncFactsResource, FactsResource
from .resources.jobs import AsyncJobsResource, JobsResource
from .resources.links import AsyncLinksResource, LinksResource
from .resources.review import AsyncReviewResource, ReviewResource
from .types import BrainDocument, BrainStatus, SearchResponse, WhoAmIResponse

__all__ = ["UnisonBrain", "AsyncUnisonBrain", "Client", "AsyncClient"]

_DEFAULT_API_URL = "https://api.unisonlabs.ai"


class UnisonBrain:
    """Synchronous client for the Unison brain API.

    Reads UNISON_TOKEN and UNISON_API_URL from the environment if not provided.
    """

    token: str
    base_url: str
    max_retries: int
    timeout: float

    def __init__(
        self,
        token: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        if token is None:
            token = os.environ.get("UNISON_TOKEN")
        if token is None:
            raise UnisonError(
                "No API token provided. Pass token= or set the UNISON_TOKEN environment variable."
            )
        self.token = token

        if base_url is None:
            base_url = os.environ.get("UNISON_API_URL", _DEFAULT_API_URL)
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

        self._transport = HttpTransport(
            self.base_url,
            self.token,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
        )

        self.auth = AuthResource(self._transport)
        self.documents = DocumentsResource(self._transport)
        self.entities = EntitiesResource(self._transport)
        self.facts = FactsResource(self._transport)
        self.links = LinksResource(self._transport)
        self.review = ReviewResource(self._transport)
        self.jobs = JobsResource(self._transport)

    # Convenience top-level shortcuts (mirrors BrainClient surface from the brief)

    def search(self, q: str, *, limit: Optional[int] = None, **kwargs) -> SearchResponse:  # type: ignore[return]
        """Hybrid semantic+keyword search."""
        return self.documents.search(q, k=limit, **kwargs)

    def get(self, path: str) -> BrainDocument:
        """Read a document by path."""
        return self.documents.get(path)

    def write(self, path: str, body_md: str, **kwargs) -> BrainDocument:  # type: ignore[return]
        """Write a document."""
        return self.documents.write(path, body_md, **kwargs)

    def edit_doc(self, path: str, old_str: str, new_str: str, **kwargs) -> BrainDocument:  # type: ignore[return]
        """Surgical edit of a document."""
        return self.documents.edit(path, old_str, new_str, **kwargs)

    def status(self) -> BrainStatus:
        """Brain health and counts."""
        return self.documents.status()

    def whoami(self) -> WhoAmIResponse:
        """Confirm authentication and check granted scopes."""
        return self.auth.whoami()

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "UnisonBrain":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def with_options(
        self,
        *,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> "UnisonBrain":
        """Create a new client instance re-using the same options with overrides."""
        return UnisonBrain(
            token=token or self.token,
            base_url=base_url or self.base_url,
            max_retries=max_retries if max_retries is not None else self.max_retries,
            timeout=timeout if timeout is not None else self.timeout,
        )


class AsyncUnisonBrain:
    """Asynchronous client for the Unison brain API.

    Reads UNISON_TOKEN and UNISON_API_URL from the environment if not provided.
    """

    token: str
    base_url: str
    max_retries: int
    timeout: float

    def __init__(
        self,
        token: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        if token is None:
            token = os.environ.get("UNISON_TOKEN")
        if token is None:
            raise UnisonError(
                "No API token provided. Pass token= or set the UNISON_TOKEN environment variable."
            )
        self.token = token

        if base_url is None:
            base_url = os.environ.get("UNISON_API_URL", _DEFAULT_API_URL)
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

        self._transport = AsyncHttpTransport(
            self.base_url,
            self.token,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
        )

        self.auth = AsyncAuthResource(self._transport)
        self.documents = AsyncDocumentsResource(self._transport)
        self.entities = AsyncEntitiesResource(self._transport)
        self.facts = AsyncFactsResource(self._transport)
        self.links = AsyncLinksResource(self._transport)
        self.review = AsyncReviewResource(self._transport)
        self.jobs = AsyncJobsResource(self._transport)

    async def search(self, q: str, *, limit: Optional[int] = None, **kwargs) -> SearchResponse:  # type: ignore[return]
        return await self.documents.search(q, k=limit, **kwargs)

    async def get(self, path: str) -> BrainDocument:
        return await self.documents.get(path)

    async def write(self, path: str, body_md: str, **kwargs) -> BrainDocument:  # type: ignore[return]
        return await self.documents.write(path, body_md, **kwargs)

    async def edit_doc(self, path: str, old_str: str, new_str: str, **kwargs) -> BrainDocument:  # type: ignore[return]
        return await self.documents.edit(path, old_str, new_str, **kwargs)

    async def status(self) -> BrainStatus:
        return await self.documents.status()

    async def whoami(self) -> WhoAmIResponse:
        return await self.auth.whoami()

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> "AsyncUnisonBrain":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def with_options(
        self,
        *,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> "AsyncUnisonBrain":
        return AsyncUnisonBrain(
            token=token or self.token,
            base_url=base_url or self.base_url,
            max_retries=max_retries if max_retries is not None else self.max_retries,
            timeout=timeout if timeout is not None else self.timeout,
        )


Client = UnisonBrain
AsyncClient = AsyncUnisonBrain
