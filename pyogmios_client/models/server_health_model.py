from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class LastKnownTip(BaseModel):
    slot: Optional[int] = None
    id: Optional[int | str] = None
    height: Optional[int] = None


class RuntimeStats(BaseModel):
    cpu_time: Optional[int] = None
    current_heap_size: Optional[int] = None
    gc_cpu_time: Optional[int] = None
    max_heap_size: Optional[int] = None


class SessionDurations(BaseModel):
    max: Optional[int | float] = None
    mean: Optional[int | float] = None
    min: Optional[int | float] = None


class Metrics(BaseModel):
    active_connections: Optional[int] = None
    runtime_stats: RuntimeStats = None
    session_durations: SessionDurations = None
    total_connections: Optional[int] = None
    total_messages: Optional[int] = None
    total_unrouted: Optional[int] = None


class ServerHealth(BaseModel):
    start_time: Optional[str] = None
    last_known_tip: Optional[LastKnownTip] = None
    last_tip_update: Optional[str] = None
    network_synchronization: Optional[float] = None
    current_era: Optional[str] = None
    metrics: Optional[Metrics] = None
    connection_status: Optional[str] = None
    current_epoch: Optional[int] = None
    slot_in_epoch: Optional[int] = None
    version: Optional[str] = None
    network: Optional[str] = None
