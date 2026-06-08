"""Utility helpers for the Unison SDK."""
from __future__ import annotations

import os
import pathlib
from typing import Tuple


# FileTypes mirrors the convention used in Stainless-generated SDKs:
# a (filename, bytes) tuple suitable for passing to httpx multipart.
FileTypes = Tuple[str, bytes]


def file_from_path(path: str) -> FileTypes:
    """Read a file from *path* and return a ``(filename, bytes)`` tuple.

    The returned value can be passed directly to any SDK method that accepts
    file content, e.g. a future ``documents.upload_file()`` method.

    Example::

        from unisonlabs import file_from_path
        payload = file_from_path("/path/to/report.pdf")
    """
    contents = pathlib.Path(path).read_bytes()
    filename = os.path.basename(path)
    return (filename, contents)
