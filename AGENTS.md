# AGENTS.md

Guidance for AI agents. This file covers two jobs — jump to yours:

- **Use this client** — you are an agent integrating the Unison brain into a
  project → [Using the SDK](#using-the-sdk)
- **Contribute to this repo** — you are changing the SDK's code →
  [Working in this repo](#working-in-this-repo)

Follows the [AGENTS.md](https://agents.md/) convention. Human contributors: see
[`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## Using the SDK

### 1. Install

```bash
pip install unisonlabs
```

### 2. Authenticate

The client reads your key from the environment:

```bash
export UNISON_TOKEN=usk_live_...          # required
export UNISON_API_URL=https://api.unisonlabs.ai   # optional default
```

For local development against a self-hosted brain:

```bash
export UNISON_API_URL=http://localhost:4001
```

You can also pass `token=` and `base_url=` directly to the constructor.

Provision a key (no existing account needed):

```python
import httpx, os

resp = httpx.post(
    f"{os.environ['UNISON_API_URL']}/v1/auth/provision",
    json={"email": "agent@example.com"},
)
api_key = resp.json()["apiKey"]   # usk_live_... — store it; do not commit it
```

### 3. The loop — run every session

**Search before answering.** The user may have already decided it.

```python
from unisonlabs import UnisonBrain

client = UnisonBrain()
results = client.search("architecture decisions", limit=5)
for hit in results.results:
    print(f"[{hit.score:.2f}] {hit.doc.path}")
    # read the full body with client.get(hit.doc.path)
```

**Write decisions and conventions** so the next agent inherits them:

```python
client.write(
    "/private/notes/decision-auth.md",
    "# Auth decision\nWe use usk_ keys for machine callers.",
    title="Auth decision",
    tags=["decision"],
)
```

**Read a document back** (body is in `doc.body` or `doc.bodyMd`):

```python
doc = client.get("/private/notes/decision-auth.md")
print(doc.body)
```

### 4. Async client

For async contexts use `AsyncUnisonBrain`:

```python
import asyncio
from unisonlabs import AsyncUnisonBrain

async def main() -> None:
    async with AsyncUnisonBrain() as client:
        results = await client.search("auth")
        doc = await client.write("/private/notes/async-note.md", "# Hello")

asyncio.run(main())
```

### Key env vars

| Variable | Default | Description |
|---|---|---|
| `UNISON_TOKEN` | required | `usk_live_...` API key |
| `UNISON_API_URL` | `https://api.unisonlabs.ai` | Brain API base URL |

---

## Working in this repo

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Commands (run before every PR)

```bash
ruff check src/ tests/ examples/          # lint
ruff check --fix src/ tests/ examples/    # auto-fix lint
pytest                                    # unit tests (mocked — no real network)
python -c "import unisonlabs"             # verify import
```

CI runs all three on every pull_request to main.

### Conventions

- Python 3.9+. `from __future__ import annotations` at the top of every module.
- Type-annotate all public symbols.
- Pydantic v2 models for response types. Add new fields as `Optional[T] = None`.
- `BrainDocument.body` and `.bodyMd` are both populated — `body` is the user-friendly
  accessor, `bodyMd` is the wire-format field name. The `_coerce_body` model
  validator keeps them in sync.
- No new runtime dependencies without opening an issue first.
- The client enforces nothing — the server is the security boundary. Do not add
  client-side auth checks or path validation beyond `_fs_contract.py`.

### PRs

One logical change per PR. Tests must stay green. Lint must pass. Security issues:
see [SECURITY.md](SECURITY.md) — do not open a public issue.
