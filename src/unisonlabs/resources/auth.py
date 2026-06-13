"""Auth resource — provision/verify/whoami/device-flow."""

from __future__ import annotations

from typing import Optional

from .._http import AsyncHttpTransport, HttpTransport
from ..types import (
    DeviceCodeResponse,
    ProvisionResponse,
    RequestKeyResponse,
    TokenResponse,
    VerifyResponse,
    WhoAmIResponse,
)


class AuthResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._t = transport

    def whoami(self) -> WhoAmIResponse:
        """Confirm auth and check granted scopes."""
        data = self._t.request("GET", "/v1/auth/whoami")
        return WhoAmIResponse(**data)

    def provision(self, email: str) -> ProvisionResponse:
        """Headless account creation.

        Returns an immediately usable (unverified) usk_ key.
        If the email is already registered, raises ConflictError — call
        request_key() instead.
        """
        data = self._t.request("POST", "/v1/auth/provision", json={"email": email})
        return ProvisionResponse(**data)

    def verify(self, email: str, code: str) -> VerifyResponse:
        """Verify the emailed OTP to make a workspace durable, or recover a key."""
        data = self._t.request("POST", "/v1/auth/verify", json={"email": email, "code": code})
        return VerifyResponse(**data)

    def request_key(self, email: str) -> RequestKeyResponse:
        """Request a recovery OTP for an existing verified account."""
        data = self._t.request("POST", "/v1/auth/request-key", json={"email": email})
        return RequestKeyResponse(**data)

    def device_code(self, client_id: str, scope: Optional[str] = None) -> DeviceCodeResponse:
        """Start the device-flow login."""
        body: dict = {"clientId": client_id}
        if scope is not None:
            body["scope"] = scope
        data = self._t.request("POST", "/v1/auth/device/code", json=body)
        return DeviceCodeResponse(**data)

    def device_token(self, device_code: str) -> TokenResponse:
        """Poll the device-flow token endpoint."""
        data = self._t.request("POST", "/v1/auth/device/token", json={"deviceCode": device_code})
        return TokenResponse(**data)

    def exchange_code(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        client_id: str,
    ) -> TokenResponse:
        """Exchange a PKCE authorization code for an access token."""
        data = self._t.request(
            "POST",
            "/v1/auth/token",
            json={
                "grantType": "authorization_code",
                "code": code,
                "codeVerifier": code_verifier,
                "redirectUri": redirect_uri,
                "clientId": client_id,
            },
        )
        return TokenResponse(**data)


class AsyncAuthResource:
    def __init__(self, transport: AsyncHttpTransport) -> None:
        self._t = transport

    async def whoami(self) -> WhoAmIResponse:
        data = await self._t.request("GET", "/v1/auth/whoami")
        return WhoAmIResponse(**data)

    async def provision(self, email: str) -> ProvisionResponse:
        data = await self._t.request("POST", "/v1/auth/provision", json={"email": email})
        return ProvisionResponse(**data)

    async def verify(self, email: str, code: str) -> VerifyResponse:
        data = await self._t.request("POST", "/v1/auth/verify", json={"email": email, "code": code})
        return VerifyResponse(**data)

    async def request_key(self, email: str) -> RequestKeyResponse:
        data = await self._t.request("POST", "/v1/auth/request-key", json={"email": email})
        return RequestKeyResponse(**data)

    async def device_code(self, client_id: str, scope: Optional[str] = None) -> DeviceCodeResponse:
        body: dict = {"clientId": client_id}
        if scope is not None:
            body["scope"] = scope
        data = await self._t.request("POST", "/v1/auth/device/code", json=body)
        return DeviceCodeResponse(**data)

    async def device_token(self, device_code: str) -> TokenResponse:
        data = await self._t.request("POST", "/v1/auth/device/token", json={"deviceCode": device_code})
        return TokenResponse(**data)

    async def exchange_code(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        client_id: str,
    ) -> TokenResponse:
        data = await self._t.request(
            "POST",
            "/v1/auth/token",
            json={
                "grantType": "authorization_code",
                "code": code,
                "codeVerifier": code_verifier,
                "redirectUri": redirect_uri,
                "clientId": client_id,
            },
        )
        return TokenResponse(**data)
