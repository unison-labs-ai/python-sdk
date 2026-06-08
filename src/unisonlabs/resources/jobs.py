"""Jobs resource — job queue visibility (requires brain:admin scope)."""

from __future__ import annotations

from typing import Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import JobListResponse, JobRetryResponse, JobStatsResponse


class JobsResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        status: Optional[str] = None,
        kind: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> JobListResponse:
        """Job queue visibility. Requires brain:admin."""
        params = {}
        if status is not None:
            params["status"] = status
        if kind is not None:
            params["kind"] = kind
        if limit is not None:
            params["limit"] = limit
        data = self._t.request("GET", "/v1/brain/jobs", params=params)
        return JobListResponse(**data)

    def stats(self) -> JobStatsResponse:
        """Job counts by status. Requires brain:admin."""
        data = self._t.request("GET", "/v1/brain/jobs/stats")
        return JobStatsResponse(**data)

    def retry(self, job_id: str) -> JobRetryResponse:
        """Re-queue a failed job. Requires brain:admin."""
        data = self._t.request("POST", f"/v1/brain/jobs/{job_id}/retry")
        return JobRetryResponse(**data)


class AsyncJobsResource:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        status: Optional[str] = None,
        kind: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> JobListResponse:
        params = {}
        if status is not None:
            params["status"] = status
        if kind is not None:
            params["kind"] = kind
        if limit is not None:
            params["limit"] = limit
        data = await self._t.request("GET", "/v1/brain/jobs", params=params)
        return JobListResponse(**data)

    async def stats(self) -> JobStatsResponse:
        data = await self._t.request("GET", "/v1/brain/jobs/stats")
        return JobStatsResponse(**data)

    async def retry(self, job_id: str) -> JobRetryResponse:
        data = await self._t.request("POST", f"/v1/brain/jobs/{job_id}/retry")
        return JobRetryResponse(**data)
