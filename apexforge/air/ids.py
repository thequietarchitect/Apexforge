"""Deterministic AIR ID helpers."""

from __future__ import annotations


def event_record_id(
    directive_id: str,
    decision_id: str,
    path_id: str,
    index: int,
    event_id: str,
) -> str:
    return f"{directive_id}:{decision_id}:{path_id}:event:{index}:{event_id}"
