"""Low-level HTTP transport for the Unison SDK.

Wraps httpx with:
- Automatic Bearer token injection
- Optional default_headers / default_query applied to every request
- Automatic retry with exponential backoff (default 2 retries)
- Retry-After header support: on 429 the server-specified delay takes precedence
- Array query-param serialisation (repeated key, not comma-separated)
- Structured error raising
- DefaultHttpxClient / DefaultAsyncHttpxClient with SDK-appropriate defaults
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Mapping, Optional, Tuple, TYPE_CHECKING

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

# ---------------------------------------------------------------------------
# DefaultHttpxClient / DefaultAsyncHttpxClient
# ---------------------------------------------------------------------------

_DEFAULT_LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20)


class _DefaultHttpxClient(httpx.Client):
    """An ``httpx.Client`` pre-configured with the same defaults the SDK uses internally.

    Passing your own ``httpx.Client()`` to the SDK's ``http_client=`` parameter
    uses httpx's own defaults instead of the SDK's. Use this class when you need
    to customise transport/proxies while keeping SDK-level timeout and limit
    settings intact.
    """

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        kwargs.setdefault("limits", _DEFAULT_LIMITS)
        kwargs.setdefault("follow_redirects", True)
        super().__init__(**kwargs)


class _DefaultAsyncHttpxClient(httpx.AsyncClient):
    """An ``httpx.AsyncClient`` pre-configured with the same defaults the SDK uses internally."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        kwargs.setdefault("limits", _DEFAULT_LIMITS)
        kwargs.setdefault("follow_redirects", True)
        super().__init__(**kwargs)


if TYPE_CHECKING:
    DefaultHttpxClient = httpx.Client
    DefaultAsyncHttpxClient = httpx.AsyncClient
else:
    DefaultHttpxClient = _DefaultHttpxClient
    DefaultAsyncHttpxClient = _DefaultAsyncHttpxClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Transports
# ---------------------------------------------------------------------------


class HttpTransport:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: Optional[httpx.Client] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.max_retries = max_retries
        self.timeout = timeout
        self._default_headers: Dict[str, str] = dict(default_headers) if default_headers else {}
        self._default_query: Dict[str, Any] = dict(default_query) if default_query else {}
        self._client = http_client or httpx.Client(timeout=timeout, follow_redirects=True)

    def _auth_headers(self) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self.token}"}
        headers.update(self._default_headers)
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        merged_params: Dict[str, Any] = {**self._default_query, **(params or {})}
        qp = _build_query_params(merged_params)

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

    def request_raw(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> httpx.Response:
        """Like ``request()``, but returns the raw ``httpx.Response`` after retries/error-raising."""
        url = f"{self.base_url}{path}"
        merged_params: Dict[str, Any] = {**self._default_query, **(params or {})}
        qp = _build_query_params(merged_params)

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
                        time.sleep(wait)
                        last_exc = _make_status_error(resp, body)
                        continue
                    raise _make_status_error(resp, body)
                return resp
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

    def request_stream(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> httpx.Response:
        """Return a streaming ``httpx.Response`` (body not consumed)."""
        url = f"{self.base_url}{path}"
        merged_params: Dict[str, Any] = {**self._default_query, **(params or {})}
        qp = _build_query_params(merged_params)
        return self._client.stream(
            method,
            url,
            headers=self._auth_headers(),
            params=qp if qp else None,
            json=json,
        ).__enter__()

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
        default_headers: Optional[Mapping[str, str]] = None,
        default_query: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.max_retries = max_retries
        self.timeout = timeout
        self._default_headers: Dict[str, str] = dict(default_headers) if default_headers else {}
        self._default_query: Dict[str, Any] = dict(default_query) if default_query else {}
        self._client = http_client or httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    def _auth_headers(self) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self.token}"}
        headers.update(self._default_headers)
        return headers

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
        merged_params: Dict[str, Any] = {**self._default_query, **(params or {})}
        qp = _build_query_params(merged_params)

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

    async def request_raw(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> httpx.Response:
        """Like ``request()``, but returns the raw ``httpx.Response`` after retries/error-raising."""
        import asyncio

        url = f"{self.base_url}{path}"
        merged_params: Dict[str, Any] = {**self._default_query, **(params or {})}
        qp = _build_query_params(merged_params)

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
                        await asyncio.sleep(wait)
                        last_exc = _make_status_error(resp, body)
                        continue
                    raise _make_status_error(resp, body)
                return resp
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
