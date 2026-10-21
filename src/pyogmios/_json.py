"""JSON encoding and decoding, with orjson when it is installed (``pip install pyogmios[speedups]``)."""

from __future__ import annotations

import json
import re
from typing import Any

try:
    import orjson  # ty: ignore[unresolved-import]  # optional: pyogmios[speedups]
except ImportError:  # pragma: no cover - exercised when the speedups extra is not installed
    orjson = None  # type: ignore[assignment]

#: 20 digits in a row: the only way a JSON integer can exceed 64 bits. orjson decodes such integers
#: as floats, silently losing precision, so documents containing one are decoded with the stdlib.
_BIG_INTEGER = re.compile(rb"\d{20}")


def dumps(value: Any) -> str:
    """Encode ``value`` as a JSON string (WebSocket messages must be text frames)."""
    if orjson is not None:
        try:
            return orjson.dumps(value).decode()
        except TypeError:  # integers beyond 64 bits, which orjson does not encode
            pass
    return json.dumps(value, separators=(",", ":"))


def loads(data: str | bytes) -> Any:
    """Decode a JSON document, keeping integers of any size exact."""
    raw = data.encode() if isinstance(data, str) else data
    if orjson is not None and not _BIG_INTEGER.search(raw):
        return orjson.loads(raw)
    return json.loads(raw)
