# Contributing to the Unison brain Python SDK

Thanks for helping improve the official Python client for the Unison brain.

## Repo layout

```
src/unisonlabs/         Python package source
  _client.py            UnisonBrain / AsyncUnisonBrain entry points
  _http.py              Low-level httpx transport with retry
  _exceptions.py        Error hierarchy
  _fs_contract.py       Write-path validation
  resources/            Per-domain resource classes
  types/                Pydantic response models
tests/
  test_client.py        Unit tests (mocked with respx — no real network)
examples/               Runnable usage examples
```

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Before opening a PR

1. `ruff check src/ tests/ examples/` must pass (run `ruff check --fix` to auto-fix).
2. `pytest` must pass with all tests green.
3. Keep changes scoped — one logical change per PR.
4. If you change the public API, update `README.md` and the docstrings.

## Conventions

- Python 3.9+. Use `from __future__ import annotations` at the top of every module.
- Type-annotate all public functions and classes.
- Pydantic v2 models for all response types; add new fields as `Optional[T] = None`.
- `BrainDocument.body` is the friendly accessor; `bodyMd` is the wire-format field.
  Both are kept in sync via the `_coerce_body` model validator.
- No extra dependencies beyond those in `pyproject.toml`; open an issue first if
  you think one is needed.
- Do not add client-side auth checks or path allow-lists — the server is the only
  security boundary.

## Reporting bugs / proposing features

Use the issue templates. For security issues, see [SECURITY.md](SECURITY.md) —
do **not** open a public issue.
