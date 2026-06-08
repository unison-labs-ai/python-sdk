"""Low-level HTTP transport for the Unison SDK.

Wraps httpx with:
- Automatic Bearer token injection
- Automatic retry with exponential backoff (default 2 retries)
- Retry-After header support: on 429 the server-specified delay takes precedence
- Array query-param serialisation (repeated key, not comma-separated)
- Structured error raising
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ._exceptions import (
    APIConnectionError,
    APITimeoutError,
    _make_status_error,
)

logger = logging.getLogger("unisonlabs")

_RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504}
DEFAULT_MAX_RETRIES = 2
DEFAULT_TIMEOUT = 60.0
_MAX_RETRY_AFTER = 60.0


def _retry_delay(attempt: int, response: Optional[httpx.Response] = None) -> float:
    """Return seconds to wait before the next attempt.

    Respects the ``Retry-After`` header on 429 responses (up to
    ``_MAX_RETRY_AFTER`` seconds so a misbehaving server cannot stall the
    caller indefinitely). Falls back to exponential backoff otherwise.
    """
    if response is not None and response.status_code == 429:
        header = response.headers.get("retry-after") or response.headers.get("Retry-After")
        if header is not None:
            try:
                delay = float(header)
                return min(delay, _MAX_RETRY_AFTER)
            except ValueError:
                pass
    return min(0.5 * (2 ** (attempt - 1)), 8.0)


def _build_query_params(params: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Serialise query params; lists are repeated-key encoded."""
    result: List[Tuple[str, str]] = []
    for k, v in params.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            for item in v:
                result.append((k, str(item)))
        else:
            result.append((k, str(v)))
    return result


class HttpTransport:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.max_retries = max_retries
        self.timeout = timeout
        self._client = http_client or httpx.Client(timeout=timeout, follow_redirects=True)

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        qp = _build_query_params(params or {})

        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt <= self.max_retries:
            try:
                resp = self._client.request(
                    method,
                    url,
                    headers=self._auth_headers(),
                    params=qp if qp else None,
                    json=json,
                )
                logger.debug("%s %s -> %d", method, path, resp.status_code)
                if resp.status_code >= 400:
                    try:
                        body = resp.json()
                    except Exception:
                        body = resp.text
                    if resp.status_code in _RETRYABLE_STATUS and attempt < self.max_retries:
                        attempt += 1
                        wait = _retry_delay(attempt, resp)
                        logger.debug("retry %d after %.1fs (status %d)", attempt, wait, resp.status_code)
                        time.sleep(wait)
                        last_exc = _make_status_error(resp, body)
                        continue
                    raise _make_status_error(resp, body)
                try:
                    return resp.json()
                except Exception:
                    return None
            except httpx.TimeoutException as e:
                req = e.request  # type: ignore[union-attr]
                if attempt < self.max_retries:
                    attempt += 1
                    time.sleep(_retry_delay(attempt))
                    last_exc = APITimeoutError(req)
                    continue
                raise APITimeoutError(req) from e
            except httpx.RequestError as e:
                req = e.request
                if attempt < self.max_retries:
                    attempt += 1
                    time.sleep(_retry_delay(attempt))
                    last_exc = APIConnectionError(str(e), request=req)
                    continue
                raise APIConnectionError(str(e), request=req) from e
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Unreachable")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpTransport":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncHttpTransport:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.max_retries = max_retries
        self.timeout = timeout
        self._client = http_client or httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> Any:
        import asyncio

        url = f"{self.base_url}{path}"
        qp = _build_query_params(params or {})

        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt <= self.max_retries:
            try:
                resp = await self._client.request(
                    method,
                    url,
                    headers=self._auth_headers(),
                    params=qp if qp else None,
                    json=json,
                )
                logger.debug("%s %s -> %d", method, path, resp.status_code)
                if resp.status_code >= 400:
                    try:
                        body = resp.json()
                    except Exception:
                        body = resp.text
                    if resp.status_code in _RETRYABLE_STATUS and attempt < self.max_retries:
                        attempt += 1
                        wait = _retry_delay(attempt, resp)
                        logger.debug("retry %d after %.1fs (status %d)", attempt, wait, resp.status_code)
                        await asyncio.sleep(wait)
                        last_exc = _make_status_error(resp, body)
                        continue
                    raise _make_status_error(resp, body)
                try:
                    return resp.json()
                except Exception:
                    return None
            except httpx.TimeoutException as e:
                req = e.request  # type: ignore[union-attr]
                if attempt < self.max_retries:
                    attempt += 1
                    await asyncio.sleep(_retry_delay(attempt))
                    last_exc = APITimeoutError(req)
                    continue
                raise APITimeoutError(req) from e
            except httpx.RequestError as e:
                req = e.request
                if attempt < self.max_retries:
                    attempt += 1
                    await asyncio.sleep(_retry_delay(attempt))
                    last_exc = APIConnectionError(str(e), request=req)
                    continue
                raise APIConnectionError(str(e), request=req) from e
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Unreachable")

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpTransport":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
