from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class WhoAmIUser(BaseModel):
    id: str
    email: str


class WhoAmITenant(BaseModel):
    id: str
    name: str
    verified: bool


class WhoAmIResponse(BaseModel):
    user: WhoAmIUser
    tenant: WhoAmITenant
    scopes: List[str]


class ProvisionResponse(BaseModel):
    apiKey: str
    tenantId: str
    status: str
    emailSent: bool
    message: str


class VerifyResponse(BaseModel):
    verified: bool
    tenantId: str
    apiKey: Optional[str] = None


class RequestKeyResponse(BaseModel):
    status: str


class BrainDocSource(BaseModel):
    kind: str
    ref: str


class BrainDocument(BaseModel):
    path: str
    title: Optional[str] = None
    tldr: Optional[str] = None
    kind: Optional[str] = None
    tags: Optional[List[str]] = None
    visibility: Optional[str] = None
    body: Optional[str] = None
    contentHash: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    source: Optional[BrainDocSource] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)

    def to_json(self) -> str:
        return self.model_dump_json(exclude_none=True)


class SearchResult(BaseModel):
    doc: BrainDocument
    score: float
    highlight: Optional[str] = None
    sources: Optional[List[Any]] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]


class GrepResponse(BaseModel):
    results: List[BrainDocument]


class DocResponse(BaseModel):
    document: Optional[BrainDocument] = None

    @classmethod
    def from_raw(cls, data: Any) -> "DocResponse":
        if isinstance(data, dict) and "document" in data:
            return cls(document=BrainDocument(**data["document"]))
        if isinstance(data, dict):
            return cls(document=BrainDocument(**data))
        return cls()


class ListResponse(BaseModel):
    documents: List[BrainDocument]


class FsEntry(BaseModel):
    name: str
    kind: Literal["dir", "file"]
    path: str
    mtime: Optional[str] = None


class FsListResponse(BaseModel):
    entries: List[FsEntry]


class FsReadResponse(BaseModel):
    content: Optional[str]
    path: str


class DeleteDocResponse(BaseModel):
    deleted: bool


class TagDocResponse(BaseModel):
    document: Optional[BrainDocument] = None


class ShareResponse(BaseModel):
    shared: bool


class BrainEntity(BaseModel):
    id: str
    kind: str
    displayName: str
    slug: Optional[str] = None
    aliases: Optional[List[str]] = None
    props: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)

    def to_json(self) -> str:
        return self.model_dump_json(exclude_none=True)


class EntityListResponse(BaseModel):
    entities: List[BrainEntity]


class EntityResolveResponse(BaseModel):
    entity: Optional[BrainEntity] = None


class BrainFact(BaseModel):
    id: str
    subjectId: str
    predicate: str
    factText: str
    objectJson: Optional[Any] = None
    objectEntityId: Optional[str] = None
    validFrom: Optional[str] = None
    validTo: Optional[str] = None
    confidence: Optional[float] = None
    supersedesId: Optional[str] = None
    invalidated: Optional[bool] = None
    createdAt: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)

    def to_json(self) -> str:
        return self.model_dump_json(exclude_none=True)


class FactListResponse(BaseModel):
    facts: List[BrainFact]


class InvalidateFactResponse(BaseModel):
    invalidated: bool


class BrainLink(BaseModel):
    fromId: str
    toId: str
    kind: str


class LinkListResponse(BaseModel):
    links: List[BrainLink]


class BrainStatus(BaseModel):
    docCount: int
    docWithEmbedding: Optional[int] = None
    entityCount: int
    factCount: int
    lastIngestAt: Optional[str] = None
    pendingJobs: Optional[int] = None
    staleWikiPageCount: Optional[int] = None


class NeighborsResponse(BaseModel):
    documents: List[BrainDocument]


class ConflictItem(BaseModel):
    id: str
    entityIds: Optional[List[str]] = None
    reasoning: Optional[str] = None
    createdAt: Optional[str] = None


class ConflictsResponse(BaseModel):
    conflicts: List[ConflictItem]


class ConflictResolveResponse(BaseModel):
    resolved: Optional[bool] = None


class MergeItem(BaseModel):
    id: str
    entityIds: Optional[List[str]] = None
    mergedAt: Optional[str] = None


class MergesResponse(BaseModel):
    merges: List[MergeItem]


class UndoMergeResponse(BaseModel):
    queued: Optional[bool] = None


class JobItem(BaseModel):
    id: str
    kind: str
    status: str
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    error: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: List[JobItem]


class JobStatsResponse(BaseModel):
    counts: Optional[Dict[str, int]] = None


class JobRetryResponse(BaseModel):
    queued: Optional[bool] = None


class DeviceCodeResponse(BaseModel):
    deviceCode: str
    userCode: str
    verificationUri: str
    verificationUriComplete: Optional[str] = None
    interval: int
    expiresIn: int


class TokenResponse(BaseModel):
    accessToken: str
    tokenType: str
    scope: Optional[str] = None


__all__ = [
    "WhoAmIResponse",
    "WhoAmIUser",
    "WhoAmITenant",
    "ProvisionResponse",
    "VerifyResponse",
    "RequestKeyResponse",
    "BrainDocument",
    "BrainDocSource",
    "SearchResult",
    "SearchResponse",
    "GrepResponse",
    "DocResponse",
    "ListResponse",
    "FsEntry",
    "FsListResponse",
    "FsReadResponse",
    "DeleteDocResponse",
    "TagDocResponse",
    "ShareResponse",
    "BrainEntity",
    "EntityListResponse",
    "EntityResolveResponse",
    "BrainFact",
    "FactListResponse",
    "InvalidateFactResponse",
    "BrainLink",
    "LinkListResponse",
    "BrainStatus",
    "NeighborsResponse",
    "ConflictItem",
    "ConflictsResponse",
    "ConflictResolveResponse",
    "MergeItem",
    "MergesResponse",
    "UndoMergeResponse",
    "JobItem",
    "JobListResponse",
    "JobStatsResponse",
    "JobRetryResponse",
    "DeviceCodeResponse",
    "TokenResponse",
]
