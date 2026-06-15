"""Unison brain Python SDK — synchronous and asynchronous clients."""

from __future__ import annotations

import logging
import os
from typing import Mapping, Optional

import httpx

from ._exceptions import UnisonError
from ._http import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, AsyncHttpTransport, HttpTransport
from ._wrappers import (
    AsyncUnisonBrainWithRawResponse,
    AsyncUnisonBrainWithStreamingResponse,
    UnisonBrainWithRawResponse,
    UnisonBrainWithStreamingResponse,
)
from .resources.auth import AsyncAuthResource, AuthResource
from .resources.documents import AsyncDocumentsResource, DocumentsResource
from .resources.entities import AsyncEntitiesResource, EntitiesResource
from .resources.facts import AsyncFactsResource, FactsResource
from .resources.jobs import AsyncJobsResource, JobsResource
from .resources.links import AsyncLinksResource, LinksResource
from .resources.review import AsyncReviewResource, ReviewResource
from .types import BrainDocument, BrainStatus, ContextResponse, SearchResponse, WhoAmIResponse

__all__ = ["UnisonBrain", "AsyncUnisonBrain", "Client", "AsyncClient"]

_DEFAULT_API_URL = "https://brain.unisonlabs.ai"

logger = logging.getLogger("unisonlabs")


def _setup_logging() -> None:
    """Configure logging from the ``UNISON_LOG`` environment variable.

    Recognised values: ``"debug"`` and ``"info"`` (case-insensitive).
    Any other value is ignored.
    """
    env = os.environ.get("UNISON_LOG", "").lower()
    if env in ("debug", "info"):
        logging.basicConfig(
            format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        level = logging.DEBUG if env == "debug" else logging.INFO
        logger.setLevel(level)
        logging.getLogger("httpx").setLevel(level)


_setup_logging()


def _parse_custom_headers_env(var: str) -> dict[str, str]:
    """Parse a newline-delimited ``Key: Value`` header string from an env var."""
    raw = os.environ.get(var)
    if not raw:
        return {}
    result: dict[str, str] = {}
    for line in raw.split("\n"):
        colon = line.find(":")
        if colon >= 0:
            result[line[:colon].strip()] = line[colon + 1 :].strip()
    return result


class UnisonBrain:
    """Synchronous client for the Unison brain API.

    Reads ``UNISON_TOKEN`` and ``UNISON_API_URL`` from the environment if not provided.
    ``UNISON_CUSTOM_HEADERS`` (newline-delimited ``Key: Value`` pairs) is merged into
    every request as default headers.
    ``UNISON_LOG`` (``"debug"`` | ``"info"``) configures SDK-level logging.
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
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
    ) -> None:
        if token is None:
            token = os.environ.get("UNISON_TOKEN")
        if token is None:
            raise UnisonError("No API token provided. Pass token= or set the UNISON_TOKEN environment variable.")
        self.token = token

        if base_url is None:
            base_url = os.environ.get("UNISON_API_URL", _DEFAULT_API_URL)
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

        # Merge UNISON_CUSTOM_HEADERS env var then caller-supplied default_headers
        env_headers = _parse_custom_headers_env("UNISON_CUSTOM_HEADERS")
        merged_headers: dict[str, str] = {**env_headers, **(dict(default_headers) if default_headers else {})}

        self._transport = HttpTransport(
            self.base_url,
            self.token,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            default_headers=merged_headers if merged_headers else None,
            default_query=dict(default_query) if default_query else None,
        )

        self.auth = AuthResource(self._transport)
        self.documents = DocumentsResource(self._transport)
        self.entities = EntitiesResource(self._transport)
        self.facts = FactsResource(self._transport)
        self.links = LinksResource(self._transport)
        self.review = ReviewResource(self._transport)
        self.jobs = JobsResource(self._transport)

        self.with_raw_response = UnisonBrainWithRawResponse(self._transport)
        self.with_streaming_response = UnisonBrainWithStreamingResponse(self._transport)

    # ------------------------------------------------------------------
    # Convenience top-level shortcuts (mirrors BrainClient surface from the brief)
    # ------------------------------------------------------------------

    def search(self, q: str, *, limit: Optional[int] = None, **kwargs) -> SearchResponse:  # type: ignore[return]
        """Hybrid semantic+keyword search."""
        return self.documents.search(q, k=limit, **kwargs)

    def context(self, q: str, **kwargs) -> ContextResponse:  # type: ignore[return]
        """Prompt-ready recall: fused contextMd + hits, with a weakEvidence abstention flag."""
        return self.documents.context(q, **kwargs)

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

    def add(self, path: str, body_md: str, **kwargs) -> BrainDocument:  # type: ignore[return]
        """Alias for ``write()`` — add a document to the brain.

        Mirrors the ``client.add()`` convenience method in the supermemory SDK.
        """
        return self.documents.write(path, body_md, **kwargs)

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
        default_headers: Optional[Mapping[str, str]] = None,
        set_default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
        set_default_query: Optional[Mapping[str, object]] = None,
    ) -> "UnisonBrain":
        """Create a new client instance re-using the current options with overrides.

        ``default_headers`` / ``default_query`` are *merged* on top of the
        current defaults.  Use ``set_default_headers`` / ``set_default_query``
        to *replace* them entirely.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("default_headers and set_default_headers are mutually exclusive")
        if default_query is not None and set_default_query is not None:
            raise ValueError("default_query and set_default_query are mutually exclusive")

        existing_headers = dict(self._transport._default_headers)
        existing_query = dict(self._transport._default_query)

        if set_default_headers is not None:
            new_headers: Mapping[str, str] = set_default_headers
        elif default_headers is not None:
            new_headers = {**existing_headers, **default_headers}
        else:
            new_headers = existing_headers

        if set_default_query is not None:
            new_query: Mapping[str, object] = set_default_query
        elif default_query is not None:
            new_query = {**existing_query, **default_query}
        else:
            new_query = existing_query

        return UnisonBrain(
            token=token or self.token,
            base_url=base_url or self.base_url,
            max_retries=max_retries if max_retries is not None else self.max_retries,
            timeout=timeout if timeout is not None else self.timeout,
            default_headers=new_headers or None,
            default_query=new_query or None,
        )


class AsyncUnisonBrain:
    """Asynchronous client for the Unison brain API.

    Reads ``UNISON_TOKEN`` and ``UNISON_API_URL`` from the environment if not provided.
    ``UNISON_CUSTOM_HEADERS`` (newline-delimited ``Key: Value`` pairs) is merged into
    every request as default headers.
    ``UNISON_LOG`` (``"debug"`` | ``"info"``) configures SDK-level logging.
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
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
    ) -> None:
        if token is None:
            token = os.environ.get("UNISON_TOKEN")
        if token is None:
            raise UnisonError("No API token provided. Pass token= or set the UNISON_TOKEN environment variable.")
        self.token = token

        if base_url is None:
            base_url = os.environ.get("UNISON_API_URL", _DEFAULT_API_URL)
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

        env_headers = _parse_custom_headers_env("UNISON_CUSTOM_HEADERS")
        merged_headers: dict[str, str] = {**env_headers, **(dict(default_headers) if default_headers else {})}

        self._transport = AsyncHttpTransport(
            self.base_url,
            self.token,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            default_headers=merged_headers if merged_headers else None,
            default_query=dict(default_query) if default_query else None,
        )

        self.auth = AsyncAuthResource(self._transport)
        self.documents = AsyncDocumentsResource(self._transport)
        self.entities = AsyncEntitiesResource(self._transport)
        self.facts = AsyncFactsResource(self._transport)
        self.links = AsyncLinksResource(self._transport)
        self.review = AsyncReviewResource(self._transport)
        self.jobs = AsyncJobsResource(self._transport)

        self.with_raw_response = AsyncUnisonBrainWithRawResponse(self._transport)
        self.with_streaming_response = AsyncUnisonBrainWithStreamingResponse(self._transport)

    async def search(self, q: str, *, limit: Optional[int] = None, **kwargs) -> SearchResponse:  # type: ignore[return]
        return await self.documents.search(q, k=limit, **kwargs)

    async def context(self, q: str, **kwargs) -> ContextResponse:  # type: ignore[return]
        """Prompt-ready recall: fused contextMd + hits, with a weakEvidence abstention flag."""
        return await self.documents.context(q, **kwargs)

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

    async def add(self, path: str, body_md: str, **kwargs) -> BrainDocument:  # type: ignore[return]
        """Alias for ``write()`` — add a document to the brain."""
        return await self.documents.write(path, body_md, **kwargs)

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
        default_headers: Optional[Mapping[str, str]] = None,
        set_default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, object]] = None,
        set_default_query: Optional[Mapping[str, object]] = None,
    ) -> "AsyncUnisonBrain":
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("default_headers and set_default_headers are mutually exclusive")
        if default_query is not None and set_default_query is not None:
            raise ValueError("default_query and set_default_query are mutually exclusive")

        existing_headers = dict(self._transport._default_headers)
        existing_query = dict(self._transport._default_query)

        if set_default_headers is not None:
            new_headers: Mapping[str, str] = set_default_headers
        elif default_headers is not None:
            new_headers = {**existing_headers, **default_headers}
        else:
            new_headers = existing_headers

        if set_default_query is not None:
            new_query: Mapping[str, object] = set_default_query
        elif default_query is not None:
            new_query = {**existing_query, **default_query}
        else:
            new_query = existing_query

        return AsyncUnisonBrain(
            token=token or self.token,
            base_url=base_url or self.base_url,
            max_retries=max_retries if max_retries is not None else self.max_retries,
            timeout=timeout if timeout is not None else self.timeout,
            default_headers=new_headers or None,
            default_query=new_query or None,
        )


Client = UnisonBrain
AsyncClient = AsyncUnisonBrain
