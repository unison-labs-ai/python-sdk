# Unison brain Python SDK

[![PyPI version](https://img.shields.io/pypi/v/unisonlabs.svg?label=pypi%20(stable))](https://pypi.org/project/unisonlabs/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The official Python SDK for the [Unison brain API](https://docs.unisonlabs.ai) — memory infrastructure for AI agents and teams.

Both synchronous and asynchronous clients are included, powered by [httpx](https://www.python-httpx.org/).

**AI agents:** read [AGENTS.md](AGENTS.md) — it covers install, auth with a `usk_` key, and the search-first / write-back loop in four steps.

## Quickstart

```bash
pip install unisonlabs
export UNISON_TOKEN=usk_live_...
```

```python
from unisonlabs import UnisonBrain

client = UnisonBrain()                                         # reads UNISON_TOKEN env var
results = client.search("architecture decisions", limit=5)     # hybrid search
doc = client.write("/private/notes/my-note.md", "# Note\n...")  # write
doc2 = client.get("/private/notes/my-note.md")                # read back
print(doc2.body)                                               # full markdown body
client.close()
```

## MCP Server

Use the Unison brain MCP server to give AI assistants direct access to your brain:

```json
{
  "mcpServers": {
    "unison-brain": {
      "command": "npx",
      "args": ["-y", "@unisonlabs/mcp"],
      "env": {
        "UNISON_TOKEN": "usk_live_...",
        "UNISON_API_URL": "https://api.unisonlabs.ai"
      }
    }
  }
}
```

## Installation

```sh
pip install unisonlabs
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `UNISON_TOKEN` | required | Your `usk_live_...` API token |
| `UNISON_API_URL` | `https://api.unisonlabs.ai` | Base URL for the brain API |

Set these in your environment or a `.env` file. The client reads them automatically.

## Usage

### Synchronous

```python
import os
from unisonlabs import UnisonBrain

client = UnisonBrain(
    token=os.environ.get("UNISON_TOKEN"),  # default — can be omitted
)

# Confirm auth and check scopes
me = client.whoami()
print(me.user.email, me.scopes)

# Search (hybrid keyword + semantic)
results = client.search("architecture decisions", limit=5)
for hit in results.results:
    print(f"[{hit.score:.2f}] {hit.doc.path}")

# Read a document
doc = client.get("/tenant/projects/architecture.md")
print(doc.body)

# Write a document
# Writable roots: /private/..., /tenant/..., /teams/<slug>/...
doc = client.write(
    "/private/notes/my-note.md",
    "# My Note\n\nContent here.",
    title="My Note",
    tags=["draft"],
)

# Surgical edit (old_str must match exactly once)
client.edit_doc("/private/notes/my-note.md", "Content here.", "Updated content.")

# Entity graph
resp = client.entities.resolve("Alice")
if resp.entity:
    facts = client.entities.facts(resp.entity.id)

# Record a fact
client.facts.record(
    subject_id="entity-id",
    predicate="works_at",
    fact_text="Joined Unison in 2026",
    confidence=0.9,
)

# Brain status
status = client.status()
print(f"{status.docCount} docs, {status.entityCount} entities")

client.close()
```

### Async

```python
import asyncio
from unisonlabs import AsyncUnisonBrain

async def main() -> None:
    async with AsyncUnisonBrain() as client:
        results = await client.search("auth decision", limit=3)
        for hit in results.results:
            print(hit.doc.path)

asyncio.run(main())
```

### Context manager

```python
with UnisonBrain() as client:
    doc = client.get("/tenant/notes/foo.md")
```

### with_options

```python
fast_client = client.with_options(timeout=10.0, max_retries=0)
```

## Headless machine auth (no browser)

Three-step flow to provision a token programmatically:

```python
import httpx

# Step 1 — provision (creates an unverified account + returns a usk_ key)
resp = httpx.post(
    "https://api.unisonlabs.ai/v1/auth/provision",
    json={"email": "agent@example.com"},
)
api_key = resp.json()["apiKey"]  # immediately usable (unverified, 72h expiry)

# Step 2 — verify with the OTP emailed to agent@example.com
from unisonlabs import UnisonBrain
client = UnisonBrain(token=api_key)
verify_resp = client.auth.verify("agent@example.com", input("OTP: "))
# Tenant is now durable; key never expires unless rotated

# Key recovery (already-verified accounts)
client.auth.request_key("agent@example.com")
new_key_resp = client.auth.verify("agent@example.com", input("Recovery OTP: "))
print(new_key_resp.apiKey)
```

## Resources

### `client.documents`

| Method | Description |
|---|---|
| `search(q, *, k, kind, tag, memory_type, as_of)` | Hybrid search |
| `grep(pattern, *, case_sensitive, limit)` | Regex scan over document bodies |
| `get(path)` | Read a document (includes body) |
| `write(path, body_md, *, kind, title, tldr, tags, visibility, ...)` | Write/create a document |
| `edit(path, old_str, new_str)` | Surgical in-place edit |
| `delete(path)` | Delete a document |
| `tag(path, *, add, remove)` | Add/remove tags |
| `share(*, kind, id)` | Promote private to tenant-visible |
| `list(*, prefix, kind, tag, limit)` | List documents |
| `fs_list(path)` | Directory listing |
| `fs_read(path)` | Raw content (including read-only tiers) |
| `neighbors(id_or_path, *, kind, limit)` | Graph neighbours |
| `status()` | Health + counts |

### `client.entities`

| Method | Description |
|---|---|
| `list(*, kind, status, limit)` | List entities |
| `resolve(name, *, kind_hint)` | Find by name (fuzzy+alias) |
| `get(entity_id)` | Get one entity |
| `upsert(kind, display_name, *, slug, aliases, props, status)` | Create or update |
| `facts(entity_id, *, as_of, include_invalidated)` | Facts about an entity |
| `timeline(entity_id, *, from_, to)` | Chronological facts |

### `client.facts`

| Method | Description |
|---|---|
| `list(*, limit, include_invalidated)` | Browse all facts |
| `record(subject_id, predicate, fact_text, *, ...)` | Record a new fact |
| `correct(fact_id, **fields)` | Correct/supersede a fact |
| `invalidate(fact_id)` | Soft-delete (sets validTo=now) |

### `client.links`

| Method | Description |
|---|---|
| `list(*, limit)` | List directed graph edges |
| `create(from_id, to_id, kind)` | Create a link |

### `client.auth`

| Method | Description |
|---|---|
| `whoami()` | Confirm auth + check scopes |
| `provision(email)` | Headless account creation |
| `verify(email, code)` | Verify OTP / key recovery |
| `request_key(email)` | Request recovery OTP |
| `device_code(client_id, scope?)` | Start device flow |
| `device_token(device_code)` | Poll device flow |
| `exchange_code(code, code_verifier, redirect_uri, client_id)` | PKCE exchange |

### `client.review` (requires `brain:admin`)

| Method | Description |
|---|---|
| `conflicts()` | Pending dedup merge pairs |
| `resolve_conflict(conflict_id, verdict)` | `'merge'` or `'distinct'` |
| `merges(*, limit)` | Recent merges (undo feed) |
| `undo_merge(merge_id)` | Enqueue unmerge |

### `client.jobs` (requires `brain:admin`)

| Method | Description |
|---|---|
| `list(*, status, kind, limit)` | Job queue visibility |
| `stats()` | Job counts by status |
| `retry(job_id)` | Re-queue failed job |

## Brain FS contract

All document paths must end in `.md`. Writable roots:

| Root | Visibility |
|---|---|
| `/private/...` | Private to the calling user |
| `/tenant/...` | Entire tenant |
| `/teams/<slug>/...` | That team-space |

Unqualified paths (no leading `/`) are automatically rewritten to `/private/notes/<slug>.md`. Invalid roots (`/actions/`, `/raw/`, unknown namespaces) raise `BrainContractError` before any network call.

## Error handling

```python
import unisonlabs

try:
    doc = client.get("/tenant/missing.md")
except unisonlabs.NotFoundError as e:
    print(f"404: {e.message}")
except unisonlabs.AuthenticationError:
    print("Invalid token")
except unisonlabs.RateLimitError:
    print("Rate limited — back off")
except unisonlabs.APIConnectionError as e:
    print(f"Connection failed: {e}")
```

| Status | Exception |
|---|---|
| 400 | `BadRequestError` |
| 401 | `AuthenticationError` |
| 403 | `PermissionDeniedError` |
| 404 | `NotFoundError` |
| 409 | `ConflictError` |
| 422 | `UnprocessableEntityError` |
| 429 | `RateLimitError` |
| >=500 | `InternalServerError` |
| network | `APIConnectionError` |
| timeout | `APITimeoutError` |

## Retries

The client retries 2 times by default with exponential backoff on connection errors, timeouts, and 408/409/429/5xx responses.

```python
client = UnisonBrain(max_retries=0)  # disable retries
```

## Requirements

Python 3.9 or higher.

## Contributing

Open issues and pull requests at [github.com/unison-labs-ai/python-sdk](https://github.com/unison-labs-ai/python-sdk).
See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, conventions, and PR guidelines.
Security issues: email security@unisonlabs.ai — do not open a public issue.
