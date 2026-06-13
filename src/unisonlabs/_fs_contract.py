"""Client-side enforcement of the Unison brain FS contract.

Mirrors the server's path routing rules so that obviously-invalid paths are
rejected immediately without a round-trip.
"""

from __future__ import annotations

import re

from ._exceptions import BrainContractError

_WRITABLE_ROOTS = ("/private/", "/workspace/")
_LEGACY_ROOTS = ("/wiki/", "/skills/")
_READ_ONLY_ROOTS = ("/system/", "/sources/")
_REMOVED_ROOTS = ("/actions/", "/raw/", "/tenant/", "/teams/")

_SLUG_RE = re.compile(r"[^a-z0-9-]")


def _slugify(name: str) -> str:
    base = name.lower()
    base = _SLUG_RE.sub("-", base)
    base = base.strip("-")
    return base or "untitled"


def resolve_write_path(path: str) -> str:
    """Normalise a document path for write operations.

    Rules (mirrors server):
    1. Path under a writable root → pass through unchanged.
    2. Legacy roots (/wiki/, /skills/) → pass through (server accepts as shims).
    3. Unqualified path (no leading slash, or bare filename) → /private/notes/<slug>.md
    4. Bare root *.md (single segment like /foo.md) → /private/notes/<slug>.md
    5. Read-only roots → BrainContractError
    6. Removed roots → BrainContractError
    7. Any other namespace → BrainContractError

    All paths must end in .md.
    """
    if not path:
        raise BrainContractError("Path must not be empty.", path=path)

    # Strip trailing slash just in case
    path = path.rstrip("/")

    # Unqualified (no leading slash) → private notes
    if not path.startswith("/"):
        return _to_private_note(path)

    # Check removed roots
    for root in _REMOVED_ROOTS:
        if path.startswith(root) or path == root.rstrip("/"):
            raise BrainContractError(
                f"Path '{path}' uses a removed root ({root.rstrip('/')}). "
                "Writable roots are /private/, /workspace/.",
                path=path,
            )

    # Check read-only roots
    for root in _READ_ONLY_ROOTS:
        if path.startswith(root):
            raise BrainContractError(
                f"Path '{path}' is under a read-only root ({root.rstrip('/')}). Writes are not allowed.",
                path=path,
            )

    # Writable roots → pass through
    for root in _WRITABLE_ROOTS:
        if path.startswith(root):
            return _ensure_md(path)

    # Legacy roots → pass through (server handles)
    for root in _LEGACY_ROOTS:
        if path.startswith(root):
            return _ensure_md(path)

    # Bare root path like /foo.md (single segment)
    parts = path.lstrip("/").split("/")
    if len(parts) == 1:
        return _to_private_note(parts[0])

    # Unknown namespace
    raise BrainContractError(
        f"Path '{path}' does not start with a recognised root. Writable roots: /private/, /workspace/.",
        path=path,
    )


def _ensure_md(path: str) -> str:
    if not path.endswith(".md"):
        raise BrainContractError(
            f"Path '{path}' must end in .md.",
            path=path,
        )
    return path


def _to_private_note(name: str) -> str:
    import os

    basename = os.path.basename(name)
    if basename.endswith(".md"):
        basename = basename[:-3]
    slug = _slugify(basename)
    return f"/private/notes/{slug}.md"
