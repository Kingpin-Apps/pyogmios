from __future__ import annotations

from pydantic import BaseModel


class LastKnownTip(BaseModel):
    slot: int | None = None
    id: int | str | None = None
    height: int | None = None


class RuntimeStats(BaseModel):
    cpu_time: int | None = None
    current_heap_size: int | None = None
    gc_cpu_time: int | None = None
    max_heap_size: int | None = None


class SessionDurations(BaseModel):
    max: int | float | None = None
    mean: int | float | None = None
    min: int | float | None = None


class Metrics(BaseModel):
    active_connections: int | None = None
    runtime_stats: RuntimeStats = None
    session_durations: SessionDurations = None
    total_connections: int | None = None
    total_messages: int | None = None
    total_unrouted: int | None = None


class ServerHealth(BaseModel):
    start_time: str | None = None
    last_known_tip: LastKnownTip | None = None
    last_tip_update: str | None = None
    network_synchronization: float | None = None
    current_era: str | None = None
    metrics: Metrics | None = None
    connection_status: str | None = None
    current_epoch: int | None = None
    slot_in_epoch: int | None = None
    version: str | None = None
    network: str | None = None
