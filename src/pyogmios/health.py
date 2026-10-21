"""Ogmios server health (``GET /health``) and version checks.

The health endpoint is not part of the JSON-RPC schema, so this model is written by hand from what
Ogmios 7.0.0 returns. Every field is optional, so a server that adds or drops fields still parses.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

#: The Ogmios major version this client speaks.
SUPPORTED_MAJOR = 7

_VERSION = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def parse_version(text: str | None) -> tuple[int, int, int] | None:
    """``"v7.0.0 (ef123abd)"`` -> ``(7, 0, 0)``; ``None`` when there is no version number."""
    match = _VERSION.search(text or "")
    if match is None:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


class Health(BaseModel):
    """The server's state: its node connection, sync progress, tip, era and version."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="allow")

    version: str | None = None
    """The Ogmios version, for example ``"v7.0.0 (ef123abd)"``."""
    network: str | None = None
    """``mainnet``, ``preprod``, ``preview`` or another network name."""
    connection_status: str | None = None
    """``connected`` when Ogmios is connected to its node."""
    network_synchronization: float | None = None
    """How far the node is synced, from 0.0 to 1.0."""
    current_era: str | None = None
    current_epoch: int | None = None
    slot_in_epoch: int | None = None
    last_known_tip: dict[str, Any] | None = None
    """The node's tip: ``{"slot", "id", "height"}``."""
    last_tip_update: datetime | None = None
    start_time: datetime | None = None
    metrics: dict[str, Any] | None = None

    @property
    def server_version(self) -> tuple[int, int, int] | None:
        """The Ogmios version as ``(major, minor, patch)``."""
        return parse_version(self.version)

    @property
    def is_synced(self) -> bool:
        """Whether the node is connected and fully synced."""
        return self.connection_status == "connected" and (self.network_synchronization or 0) >= 1.0


def health_url(url: str) -> str:
    """The ``/health`` URL for a ``ws://``, ``wss://``, ``http://`` or ``https://`` Ogmios URL."""
    scheme, sep, rest = url.partition("://")
    if not sep:
        raise ValueError(f"not a URL: {url!r}")
    http_scheme = {"ws": "http", "wss": "https", "http": "http", "https": "https"}.get(
        scheme.lower()
    )
    if http_scheme is None:
        raise ValueError(f"unsupported scheme {scheme!r}: use ws, wss, http or https")
    host, _, path = rest.partition("/")
    path = path.split("?", 1)[0].rstrip("/")
    return f"{http_scheme}://{host}/{path + '/' if path else ''}health"
