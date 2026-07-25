"""Causal AIR model objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

from air.model import EventEmission, StateAssignment


@dataclass(frozen=True)
class DirectiveInvocation:
    target: str
    id: str


@dataclass(frozen=True)
class CausalPath:
    id: str
    weight: int
    assignments: tuple
    emits: tuple
    invocations: tuple = ()
    effects: tuple = ()
    rationale: str = ""

@dataclass(frozen=True)
class CausalDecision:
    id: str
    cause: str = ""
    paths: tuple[CausalPath, ...] = ()
    policy: str = "max_weight"