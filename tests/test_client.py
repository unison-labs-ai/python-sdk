"""Tests for the UnisonBrain client and its sub-resources.

All HTTP calls are intercepted with respx so no real network traffic is made.
"""

from __future__ import annotations

import httpx
import pytest
import respx

import unisonlabs
from unisonlabs import AsyncUnisonBrain, UnisonBrain
from unisonlabs._exceptions import BrainContractError, UnisonError

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_client_requires_token() -> None:
    import os

    old = os.environ.pop("UNISON_TOKEN", None)
    try:
        with pytest.raises(UnisonError, match="UNISON_TOKEN"):
            UnisonBrain()
    finally:
        if old is not None:
            os.environ["UNISON_TOKEN"] = old


def test_client_accepts_token_arg() -> None:
    client = UnisonBrain(token="usk_live_test")
    assert client.token == "usk_live_test"
    client.close()


def test_client_reads_token_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UNISON_TOKEN", "usk_env_test")
    client = UnisonBrain()
    assert client.token == "usk_env_test"
    client.close()


def test_client_sets_default_base_url() -> None:
    client = UnisonBrain(token="usk_live_test")
    assert client.base_url == "https://api.unisonlabs.ai"
    client.close()


def test_client_base_url_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UNISON_API_URL", "https://custom.example.com/")
    client = UnisonBrain(token="usk_live_test")
    assert client.base_url == "https://custom.example.com"  # trailing slash stripped
    client.close()


def test_with_options_creates_new_instance() -> None:
    client = UnisonBrain(token="usk_live_test")
    c2 = client.with_options(timeout=30.0)
    assert c2 is not client
    assert c2.timeout == 30.0
    client.close()
    c2.close()


# ---------------------------------------------------------------------------
# FS contract enforcement
# ---------------------------------------------------------------------------


def test_fs_contract_unqualified_path() -> None:
    from unisonlabs._fs_contract import resolve_write_path

    assert resolve_write_path("my-note.md") == "/private/notes/my-note.md"


def test_fs_contract_private_prefix_passthrough() -> None:
    from unisonlabs._fs_contract import resolve_write_path

    assert resolve_write_path("/private/notes/foo.md") == "/private/notes/foo.md"


def test_fs_contract_tenant_prefix_passthrough() -> None:
    from unisonlabs._fs_contract import resolve_write_path

    assert resolve_write_path("/tenant/people/alice.md") == "/tenant/people/alice.md"


def test_fs_contract_teams_prefix_passthrough() -> None:
    from unisonlabs._fs_contract import resolve_write_path

    assert resolve_write_path("/teams/eng/docs/arch.md") == "/teams/eng/docs/arch.md"


def test_fs_contract_removed_root_raises() -> None:
    from unisonlabs._fs_contract import resolve_write_path

    with pytest.raises(BrainContractError):
        resolve_write_path("/actions/foo.md")


def test_fs_contract_read_only_root_raises() -> None:
    from unisonlabs._fs_contract import resolve_write_path

    with pytest.raises(BrainContractError):
        resolve_write_path("/system/views/foo.md")


def test_fs_contract_unknown_root_raises() -> None:
    from unisonlabs._fs_contract import resolve_write_path

    with pytest.raises(BrainContractError):
        resolve_write_path("/scratch/foo.md")


# ---------------------------------------------------------------------------
# HTTP-level tests with respx mocks
# ---------------------------------------------------------------------------


@respx.mock
def test_whoami() -> None:
    respx.get("https://api.unisonlabs.ai/v1/auth/whoami").mock(
        return_value=httpx.Response(
            200,
            json={
                "user": {"id": "u1", "email": "a@b.com"},
                "tenant": {"id": "t1", "name": "Acme", "verified": True},
                "scopes": ["brain:read", "brain:write"],
            },
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        result = client.whoami()
    assert result.user.email == "a@b.com"
    assert "brain:read" in result.scopes


@respx.mock
def test_search() -> None:
    respx.get("https://api.unisonlabs.ai/v1/brain/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "doc": {"path": "/tenant/notes/foo.md", "title": "Foo"},
                        "score": 0.95,
                    }
                ]
            },
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        result = client.search("auth decision", limit=5)
    assert len(result.results) == 1
    assert result.results[0].doc.path == "/tenant/notes/foo.md"
    assert result.results[0].score == 0.95


@respx.mock
def test_write_document() -> None:
    respx.put("https://api.unisonlabs.ai/v1/brain/doc").mock(
        return_value=httpx.Response(
            200,
            json={"path": "/private/notes/my-note.md", "title": "My Note"},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        doc = client.write("/private/notes/my-note.md", "# My Note\n...")
    assert doc.path == "/private/notes/my-note.md"


@respx.mock
def test_get_document() -> None:
    respx.get("https://api.unisonlabs.ai/v1/brain/doc").mock(
        return_value=httpx.Response(
            200,
            json={"path": "/tenant/notes/foo.md", "body": "# Foo\nContent"},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        doc = client.get("/tenant/notes/foo.md")
    assert doc.body == "# Foo\nContent"


@respx.mock
def test_edit_document() -> None:
    respx.patch("https://api.unisonlabs.ai/v1/brain/doc").mock(
        return_value=httpx.Response(
            200,
            json={"path": "/private/notes/my-note.md"},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        doc = client.edit_doc("/private/notes/my-note.md", "old text", "new text")
    assert doc.path == "/private/notes/my-note.md"


@respx.mock
def test_delete_document() -> None:
    respx.delete("https://api.unisonlabs.ai/v1/brain/doc").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    with UnisonBrain(token="usk_live_test") as client:
        result = client.documents.delete("/tenant/notes/foo.md")
    assert result.deleted is True


@respx.mock
def test_list_documents() -> None:
    respx.get("https://api.unisonlabs.ai/v1/brain/list").mock(
        return_value=httpx.Response(
            200,
            json={"documents": [{"path": "/tenant/notes/a.md"}, {"path": "/tenant/notes/b.md"}]},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        result = client.documents.list(prefix="/tenant/notes/")
    assert len(result.documents) == 2


@respx.mock
def test_entities_resolve() -> None:
    respx.get("https://api.unisonlabs.ai/v1/brain/entities/resolve").mock(
        return_value=httpx.Response(
            200,
            json={"entity": {"id": "eid1", "kind": "person", "displayName": "Daniel"}},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        result = client.entities.resolve("Daniel")
    assert result.entity is not None
    assert result.entity.displayName == "Daniel"


@respx.mock
def test_entities_upsert() -> None:
    respx.post("https://api.unisonlabs.ai/v1/brain/entities").mock(
        return_value=httpx.Response(
            200,
            json={"id": "eid2", "kind": "company", "displayName": "Unison"},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        entity = client.entities.upsert("company", "Unison")
    assert entity.displayName == "Unison"


@respx.mock
def test_facts_record() -> None:
    respx.post("https://api.unisonlabs.ai/v1/brain/facts").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "fid1",
                "subjectId": "eid1",
                "predicate": "works_at",
                "factText": "Joined Unison in 2026",
                "confidence": 0.9,
            },
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        fact = client.facts.record("eid1", "works_at", "Joined Unison in 2026", confidence=0.9)
    assert fact.predicate == "works_at"
    assert fact.confidence == 0.9


@respx.mock
def test_facts_invalidate() -> None:
    respx.delete("https://api.unisonlabs.ai/v1/brain/facts/fid1").mock(
        return_value=httpx.Response(200, json={"invalidated": True})
    )
    with UnisonBrain(token="usk_live_test") as client:
        result = client.facts.invalidate("fid1")
    assert result.invalidated is True


@respx.mock
def test_links_create_and_list() -> None:
    respx.post("https://api.unisonlabs.ai/v1/brain/links").mock(return_value=httpx.Response(200, json={}))
    respx.get("https://api.unisonlabs.ai/v1/brain/links").mock(
        return_value=httpx.Response(
            200,
            json={"links": [{"fromId": "a", "toId": "b", "kind": "see_also"}]},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        client.links.create("a", "b", "see_also")
        links = client.links.list()
    assert links.links[0].kind == "see_also"


@respx.mock
def test_status() -> None:
    respx.get("https://api.unisonlabs.ai/v1/brain/status").mock(
        return_value=httpx.Response(
            200,
            json={"docCount": 42, "entityCount": 10, "factCount": 100},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        s = client.status()
    assert s.docCount == 42


@respx.mock
def test_auth_provision() -> None:
    respx.post("https://api.unisonlabs.ai/v1/auth/provision").mock(
        return_value=httpx.Response(
            200,
            json={
                "apiKey": "usk_live_abc",
                "tenantId": "t1",
                "status": "unverified",
                "emailSent": True,
                "message": "Check your inbox.",
            },
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        result = client.auth.provision("agent@example.com")
    assert result.apiKey == "usk_live_abc"
    assert result.status == "unverified"


@respx.mock
def test_auth_verify() -> None:
    respx.post("https://api.unisonlabs.ai/v1/auth/verify").mock(
        return_value=httpx.Response(
            200,
            json={"verified": True, "tenantId": "t1", "apiKey": "usk_live_new"},
        )
    )
    with UnisonBrain(token="usk_live_test") as client:
        result = client.auth.verify("agent@example.com", "123456")
    assert result.verified is True
    assert result.apiKey == "usk_live_new"


@respx.mock
def test_4xx_raises_api_status_error() -> None:
    respx.get("https://api.unisonlabs.ai/v1/brain/doc").mock(
        return_value=httpx.Response(
            404,
            json={"error": {"code": "not_found", "message": "Document not found"}},
        )
    )
    with UnisonBrain(token="usk_live_test", max_retries=0) as client:
        with pytest.raises(unisonlabs.NotFoundError):
            client.get("/tenant/missing.md")


@respx.mock
def test_auth_header_sent() -> None:
    route = respx.get("https://api.unisonlabs.ai/v1/auth/whoami").mock(
        return_value=httpx.Response(
            200,
            json={
                "user": {"id": "u1", "email": "a@b.com"},
                "tenant": {"id": "t1", "name": "Acme", "verified": True},
                "scopes": ["brain:read"],
            },
        )
    )
    with UnisonBrain(token="usk_live_mykey") as client:
        client.whoami()
    assert route.called
    sent_auth = route.calls[0].request.headers.get("authorization")
    assert sent_auth == "Bearer usk_live_mykey"


# ---------------------------------------------------------------------------
# Async client
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_async_search() -> None:
    respx.get("https://api.unisonlabs.ai/v1/brain/search").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"doc": {"path": "/tenant/notes/x.md"}, "score": 0.8}]},
        )
    )
    async with AsyncUnisonBrain(token="usk_live_test") as client:
        result = await client.search("query")
    assert result.results[0].doc.path == "/tenant/notes/x.md"


@respx.mock
@pytest.mark.asyncio
async def test_async_write() -> None:
    respx.put("https://api.unisonlabs.ai/v1/brain/doc").mock(
        return_value=httpx.Response(
            200,
            json={"path": "/private/notes/async-note.md"},
        )
    )
    async with AsyncUnisonBrain(token="usk_live_test") as client:
        doc = await client.write("/private/notes/async-note.md", "# Async")
    assert doc.path == "/private/notes/async-note.md"


# ---------------------------------------------------------------------------
# Retry-After header support (parity feature)
# ---------------------------------------------------------------------------


def test_retry_delay_respects_retry_after_header() -> None:
    from unisonlabs._http import _retry_delay

    resp = httpx.Response(429, headers={"Retry-After": "3"})
    delay = _retry_delay(attempt=1, response=resp)
    assert delay == 3.0


def test_retry_delay_caps_retry_after_at_max() -> None:
    from unisonlabs._http import _MAX_RETRY_AFTER, _retry_delay

    resp = httpx.Response(429, headers={"Retry-After": "9999"})
    delay = _retry_delay(attempt=1, response=resp)
    assert delay == _MAX_RETRY_AFTER


def test_retry_delay_falls_back_to_exponential_on_non_429() -> None:
    from unisonlabs._http import _retry_delay

    resp = httpx.Response(503)
    delay = _retry_delay(attempt=1, response=resp)
    # 0.5 * 2^(1-1) = 0.5
    assert delay == 0.5


def test_retry_delay_falls_back_when_no_response() -> None:
    from unisonlabs._http import _retry_delay

    delay = _retry_delay(attempt=2)
    # 0.5 * 2^(2-1) = 1.0
    assert delay == 1.0


def test_retry_delay_ignores_invalid_retry_after_value() -> None:
    from unisonlabs._http import _retry_delay

    resp = httpx.Response(429, headers={"Retry-After": "not-a-number"})
    # Should fall back to exponential
    delay = _retry_delay(attempt=1, response=resp)
    assert delay == 0.5


@respx.mock
def test_rate_limit_retry_with_retry_after() -> None:
    """On 429 with Retry-After the client retries and succeeds."""
    route = respx.get("https://api.unisonlabs.ai/v1/brain/status")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "rate limited"}),
        httpx.Response(200, json={"docCount": 7, "entityCount": 2, "factCount": 1}),
    ]
    with UnisonBrain(token="usk_live_test", max_retries=1) as client:
        status = client.status()
    assert status.docCount == 7
    assert route.call_count == 2
