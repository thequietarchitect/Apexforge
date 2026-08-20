"""Deterministic whole-map composition for canonical TAM evidence."""

from __future__ import annotations

from typing import Tuple

from tam.model import TraceMap


def compose_trace_maps(
    trace_maps: Tuple[TraceMap, ...],
) -> TraceMap:
    """Compose already-produced trace maps without rewriting their records."""

    if type(trace_maps) is not tuple:
        raise TypeError("trace_maps must be an exact tuple")

    records = []
    for index, trace_map in enumerate(trace_maps):
        if type(trace_map) is not TraceMap:
            raise TypeError(
                "trace_maps[{}] must be an exact TraceMap".format(index)
            )
        records.extend(trace_map.records)

    return TraceMap(tuple(records))


__all__ = ("compose_trace_maps",)