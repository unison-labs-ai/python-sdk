"""Tests for parity-2 feature additions."""

from __future__ import annotations

import httpx
import pytest
import respx

import unisonlabs
from unisonlabs import (
    APIResponseValidationError,
    AsyncStream,
    AsyncUnisonBrain,
    DefaultAsyncHttpxClient,
    DefaultHttpxClient,
    RawResponse,
    Stream,
    UnisonBrain,
    file_from_path,
)

# ---------------------------------------------------------------------------
# DefaultHttpxClient / DefaultAsyncHttpxClient
# ---------------------------------------------------------------------------


def test_default_httpx_client_is_httpx_client() -> None:
    c = DefaultHttpxClient()
    assert isinstance(c, httpx.Client)
    c.close()


def test_default_async_httpx_client_is_async_client() -> None:
    c = DefaultAsyncHttpxClient()
    assert isinstance(c, httpx.AsyncClient)


def test_default_httpx_client_used_in_sdk() -> None:
    c = DefaultHttpxClient()
    client = UnisonBrain(token="usk_live_test", http_client=c)
    client.close()


# ---------------------------------------------------------------------------
# file_from_path
# ---------------------------------------------------------------------------


def test_file_from_path(tmp_path) -> None:
    f = tmp_path / "note.txt"
    f.write_bytes(b"hello")
    name, content = file_from_path(str(f))
    assert name == "note.txt"
    assert content == b"hello"


def test_file_from_path_nested(tmp_path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    f = sub / "data.md"
    f.write_bytes(b"# Heading")
    name, content = file_from_path(str(f))
    assert name == "data.md"
    assert content == b"# Heading"


# ---------------------------------------------------------------------------
# APIResponseValidationError
# ---------------------------------------------------------------------------


def test_api_response_validation_error_attrs() -> None:
    req = httpx.Request("GET", "https://api.unisonlabs.ai/v1/test")
    raw = httpx.Response(200, json={"unexpected": True}, request=req)
    err = APIResponseValidationError(response=raw)
    assert err.status_code == 200
    assert err.response is raw
    assert isinstance(err, unisonlabs.APIError)


def test_api_response_validation_error_exported() -> None:
    assert hasattr(unisonlabs, "APIResponseValidationError")


# ---------------------------------------------------------------------------
# Stream / AsyncStream exports
# ---------------------------------------------------------------------------


def test_stream_exported() -> None:
    assert Stream is unisonlabs.Stream


def test_async_stream_exported() -> None:
    assert AsyncStream is unisonlabs.AsyncStream


def test_stream_iterates_sse() -> None:
    sse_body = b"data: {}\n\ndata: {}\n\ndata: [DONE]\n\n"
    resp = httpx.Response(200, content=sse_body)

    class SimpleModel:
        def __init__(self, **kw) -> None:
            pass

    s = Stream(cast_to=SimpleModel, response=resp)
    items = list(s)
    assert len(items) == 2


# ---------------------------------------------------------------------------
# default_headers / default_query constructor params
# ---------------------------------------------------------------------------


@respx.mock
def test_default_headers_sent_on_every_request() -> None:
    route = respx.get("https://api.unisonlabs.ai/v1/auth/whoami").mock(
        return_value=httpx.Response(
            200,
            json={
                "user": {"id": "u1", "email": "a@b.com"},
                "tenant": {"id": "t1", "name": "Acme", "verified": True},
                "scopes": [],
            },
        )
    )
    with UnisonBrain(token="usk_live_test", default_headers={"X-Custom-Agent": "mybot"}) as client:
        client.whoami()
    assert route.called
    assert route.calls[0].request.headers.get("x-custom-agent") == "mybot"


@respx.mock
def test_default_query_sent_on_every_request() -> None:
    route = respx.get("https://api.unisonlabs.ai/v1/brain/status").mock(
        return_value=httpx.Response(200, json={"docCount": 1, "entityCount": 0, "factCount": 0})
    )
    with UnisonBrain(token="usk_live_test", default_query={"workspace": "test-ws"}) as client:
        client.status()
    assert route.called
    url_str = str(route.calls[0].request.url)
    assert "workspace=test-ws" in url_str


# ---------------------------------------------------------------------------
# with_options: default_headers / set_default_headers
# ---------------------------------------------------------------------------


@respx.mock
def test_with_options_default_headers_merged() -> None:
    route = respx.get("https://api.unisonlabs.ai/v1/auth/whoami").mock(
        return_value=httpx.Response(
            200,
            json={
                "user": {"id": "u1", "email": "a@b.com"},
                "tenant": {"id": "t1", "name": "Acme", "verified": True},
                "scopes": [],
            },
        )
    )
    with UnisonBrain(token="usk_live_test", default_headers={"X-Base": "base"}) as base:
        child = base.with_options(default_headers={"X-Extra": "extra"})
    child.whoami()
    assert route.called
    req = route.calls[0].request
    assert req.headers.get("x-base") == "base"
    assert req.headers.get("x-extra") == "extra"
    child.close()


@respx.mock
def test_with_options_set_default_headers_replaces() -> None:
    route = respx.get("https://api.unisonlabs.ai/v1/auth/whoami").mock(
        return_value=httpx.Response(
            200,
            json={
                "user": {"id": "u1", "email": "a@b.com"},
                "tenant": {"id": "t1", "name": "Acme", "verified": True},
                "scopes": [],
            },
        )
    )
    with UnisonBrain(token="usk_live_test", default_headers={"X-Base": "base"}) as base:
        child = base.with_options(set_default_headers={"X-New": "new"})
    child.whoami()
    assert route.called
    req = route.calls[0].request
    assert req.headers.get("x-base") is None
    assert req.headers.get("x-new") == "new"
    child.close()


def test_with_options_mutual_exclusion() -> None:
    client = UnisonBrain(token="usk_live_test")
    with pytest.raises(ValueError, match="mutually exclusive"):
        client.with_options(
            default_headers={"A": "1"},
            set_default_headers={"B": "2"},
        )
    client.close()


# ---------------------------------------------------------------------------
# UNISON_CUSTOM_HEADERS env var
# ---------------------------------------------------------------------------


@respx.mock
def test_custom_headers_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UNISON_CUSTOM_HEADERS", "X-Env-Header: envvalue\nX-Another: second")
    route = respx.get("https://api.unisonlabs.ai/v1/auth/whoami").mock(
        return_value=httpx.Response(
            200,
            json={
                "user": {"id": "u1", "email": "a@b.com"},
                "tenant": {"id": "t1", "name": "Acme", "verified": True},
                "scopes": [],
            },
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        client.whoami()
    assert route.called
    req = route.calls[0].request
    assert req.headers.get("x-env-header") == "envvalue"
    assert req.headers.get("x-another") == "second"


# ---------------------------------------------------------------------------
# with_raw_response
# ---------------------------------------------------------------------------


@respx.mock
def test_with_raw_response_status() -> None:
    respx.get("https://api.unisonlabs.ai/v1/brain/status").mock(
        return_value=httpx.Response(
            200,
            headers={"x-request-id": "req-abc"},
            json={"docCount": 5, "entityCount": 2, "factCount": 3},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        raw = client.with_raw_response.status()
    assert isinstance(raw, RawResponse)
    assert raw.status_code == 200
    assert raw.headers.get("x-request-id") == "req-abc"
    parsed = raw.parse()
    assert parsed.docCount == 5


@respx.mock
def test_with_raw_response_documents_search() -> None:
    respx.get("https://api.unisonlabs.ai/v1/brain/search").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"doc": {"path": "/tenant/foo.md"}, "score": 0.9}]},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        raw = client.with_raw_response.documents.search("foo")
    assert isinstance(raw, RawResponse)
    assert raw.parse().results[0].doc.path == "/tenant/foo.md"


# ---------------------------------------------------------------------------
# client.add() convenience
# ---------------------------------------------------------------------------


@respx.mock
def test_client_add_convenience() -> None:
    respx.put("https://api.unisonlabs.ai/v1/brain/doc").mock(
        return_value=httpx.Response(
            200,
            json={"path": "/private/notes/my-note.md"},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        doc = client.add("/private/notes/my-note.md", "# Note body")
    assert doc.path == "/private/notes/my-note.md"


@respx.mock
@pytest.mark.asyncio
async def test_async_client_add_convenience() -> None:
    respx.put("https://api.unisonlabs.ai/v1/brain/doc").mock(
        return_value=httpx.Response(
            200,
            json={"path": "/private/notes/async-note.md"},
        )
    )
    async with AsyncUnisonBrain(token="usk_live_test") as client:
        doc = await client.add("/private/notes/async-note.md", "# Async Note")
    assert doc.path == "/private/notes/async-note.md"
