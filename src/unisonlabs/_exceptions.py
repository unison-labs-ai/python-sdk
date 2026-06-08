from __future__ import annotations

from typing import Any, Optional, cast

import httpx


class UnisonError(Exception):
    pass


class APIError(UnisonError):
    message: str
    request: httpx.Request
    body: Optional[object]

    def __init__(self, message: str, request: httpx.Request, *, body: Optional[object] = None) -> None:
        super().__init__(message)
        self.message = message
        self.request = request
        self.body = body

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.message!r})"


class APIStatusError(APIError):
    response: httpx.Response
    status_code: int

    def __init__(self, message: str, *, response: httpx.Response, body: Optional[object] = None) -> None:
        super().__init__(message, response.request, body=body)
        self.response = response
        self.status_code = response.status_code


class APIConnectionError(APIError):
    def __init__(self, message: str = "Connection error.", *, request: httpx.Request) -> None:
        super().__init__(message, request, body=None)


class APITimeoutError(APIConnectionError):
    def __init__(self, request: httpx.Request) -> None:
        super().__init__("Request timed out.", request=request)


class BadRequestError(APIStatusError):
    status_code: int = 400


class AuthenticationError(APIStatusError):
    status_code: int = 401


class PermissionDeniedError(APIStatusError):
    status_code: int = 403


class NotFoundError(APIStatusError):
    status_code: int = 404


class ConflictError(APIStatusError):
    status_code: int = 409


class UnprocessableEntityError(APIStatusError):
    status_code: int = 422


class RateLimitError(APIStatusError):
    status_code: int = 429


class InternalServerError(APIStatusError):
    pass


class APIResponseValidationError(APIError):
    """Raised when an API response cannot be validated against the expected schema.

    This mirrors the same exception name used in Stainless-generated SDKs so
    that downstream code can catch it portably.
    """

    response: httpx.Response
    status_code: int

    def __init__(
        self,
        *,
        response: httpx.Response,
        message: str = "Data returned by API invalid for expected schema.",
        body: Optional[object] = None,
    ) -> None:
        super().__init__(message, response.request, body=body)
        self.response = response
        self.status_code = response.status_code


class BrainContractError(UnisonError):
    """Raised client-side when a path violates the brain FS contract before making a network call."""

    def __init__(self, message: str, *, path: str) -> None:
        super().__init__(message)
        self.path = path


def _make_status_error(response: httpx.Response, body: Any) -> APIStatusError:
    err_msg = _extract_message(body) or f"HTTP {response.status_code}"
    if response.status_code == 400:
        return BadRequestError(err_msg, response=response, body=body)
    if response.status_code == 401:
        return AuthenticationError(err_msg, response=response, body=body)
    if response.status_code == 403:
        return PermissionDeniedError(err_msg, response=response, body=body)
    if response.status_code == 404:
        return NotFoundError(err_msg, response=response, body=body)
    if response.status_code == 409:
        return ConflictError(err_msg, response=response, body=body)
    if response.status_code == 422:
        return UnprocessableEntityError(err_msg, response=response, body=body)
    if response.status_code == 429:
        return RateLimitError(err_msg, response=response, body=body)
    if response.status_code >= 500:
        return InternalServerError(err_msg, response=response, body=body)
    return APIStatusError(err_msg, response=response, body=body)


def _extract_message(body: Any) -> str:
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            return cast(str, error.get("message", ""))
        if isinstance(error, str):
            return error
        message = body.get("message")
        if isinstance(message, str):
            return message
    return ""
