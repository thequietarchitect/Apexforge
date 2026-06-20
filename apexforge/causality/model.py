"""Causal AIR model objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

from air.model import EventEmission, StateAssignment


@dataclass(frozen=True, order=True)
class CausalPath:
    id: str
    weight: int
    assignments: Tuple[StateAssignment, ...] = ()
    emits: Tuple[EventEmission, ...] = ()
    effects: tuple = ()
    rationale: str = ""


@dataclass(frozen=True, order=True)
class CausalDecision:
    id: str
    cause: str
    paths: Tuple[CausalPath, ...]
    policy: Literal["max_weight"] = "max_weight"