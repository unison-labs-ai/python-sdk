"""Unison brain Python SDK."""
from __future__ import annotations

from . import types
from ._client import AsyncClient, AsyncUnisonBrain, Client, UnisonBrain
from ._exceptions import (
    APIConnectionError,
    APIError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    BrainContractError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnisonError,
    UnprocessableEntityError,
)
from ._http import DefaultAsyncHttpxClient, DefaultHttpxClient
from ._response import AsyncStreamingResponse, RawResponse, StreamingResponse
from ._streaming import AsyncStream, Stream
from ._utils import file_from_path
from ._version import __title__, __version__
from .types import (
    BrainDocument,
    BrainEntity,
    BrainFact,
    BrainLink,
    BrainStatus,
    DeviceCodeResponse,
    EntityListResponse,
    EntityResolveResponse,
    FactListResponse,
    FsEntry,
    FsListResponse,
    FsReadResponse,
    GrepResponse,
    InvalidateFactResponse,
    JobItem,
    JobListResponse,
    JobStatsResponse,
    LinkListResponse,
    ListResponse,
    ProvisionResponse,
    RequestKeyResponse,
    SearchResponse,
    SearchResult,
    ShareResponse,
    TokenResponse,
    VerifyResponse,
    WhoAmIResponse,
)

__all__ = [
    "types",
    "__version__",
    "__title__",
    # Clients
    "UnisonBrain",
    "AsyncUnisonBrain",
    "Client",
    "AsyncClient",
    # Errors
    "UnisonError",
    "APIError",
    "APIStatusError",
    "APITimeoutError",
    "APIConnectionError",
    "APIResponseValidationError",
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
    "BrainContractError",
    # HTTP utilities
    "DefaultHttpxClient",
    "DefaultAsyncHttpxClient",
    # Response wrappers
    "RawResponse",
    "StreamingResponse",
    "AsyncStreamingResponse",
    # Streaming
    "Stream",
    "AsyncStream",
    # File utilities
    "file_from_path",
    # Response types
    "WhoAmIResponse",
    "ProvisionResponse",
    "VerifyResponse",
    "RequestKeyResponse",
    "DeviceCodeResponse",
    "TokenResponse",
    "BrainDocument",
    "BrainEntity",
    "BrainFact",
    "BrainLink",
    "BrainStatus",
    "SearchResponse",
    "SearchResult",
    "GrepResponse",
    "ListResponse",
    "FsEntry",
    "FsListResponse",
    "FsReadResponse",
    "EntityListResponse",
    "EntityResolveResponse",
    "FactListResponse",
    "InvalidateFactResponse",
    "LinkListResponse",
    "ShareResponse",
    "JobItem",
    "JobListResponse",
    "JobStatsResponse",
]
