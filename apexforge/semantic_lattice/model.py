"""P11.8B immutable Parametric Semantic Lattice core model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple


def _text(value: object, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")


def _value(value: Any, field: str) -> None:
    if type(value) in (str, int, float, bool, type(None)):
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _value(item, f"{field}[{index}]")
        return
    raise TypeError(f"{field} must be an immutable scalar or tuple")


@dataclass(frozen=True)
class SemanticLatticeAxis:
    canonical_id: str

    def __post_init__(self) -> None:
        _text(self.canonical_id, "SemanticLatticeAxis.canonical_id")


CORE_SEMANTIC_LATTICE_AXES: Tuple[SemanticLatticeAxis, ...] = tuple(
    SemanticLatticeAxis(axis_id)
    for axis_id in (
        "structural.declaration",
        "narrative.identity_relation",
        "authority.integrity",
        "priority",
        "continuity",
        "convergence",
        "causal.provenance",
        "tam.traceability",
    )
)


@dataclass(frozen=True)
class SemanticLatticeParameter:
    axis_id: str
    key: str
    value: Any

    def __post_init__(self) -> None:
        _text(self.axis_id, "SemanticLatticeParameter.axis_id")
        _text(self.key, "SemanticLatticeParameter.key")
        _value(self.value, "SemanticLatticeParameter.value")


@dataclass(frozen=True)
class ParametricSemanticLattice:
    axes: Tuple[SemanticLatticeAxis, ...] = CORE_SEMANTIC_LATTICE_AXES
    parameters: Tuple[SemanticLatticeParameter, ...] = ()

    def __post_init__(self) -> None:
        if type(self.axes) is not tuple or type(self.parameters) is not tuple:
            raise TypeError("lattice axes and parameters must be exact tuples")
        if any(type(axis) is not SemanticLatticeAxis for axis in self.axes):
            raise TypeError("lattice axes must contain exact SemanticLatticeAxis values")
        if any(type(item) is not SemanticLatticeParameter for item in self.parameters):
            raise TypeError("lattice parameters must contain exact SemanticLatticeParameter values")


__all__ = (
    "SemanticLatticeAxis",
    "SemanticLatticeParameter",
    "ParametricSemanticLattice",
    "CORE_SEMANTIC_LATTICE_AXES",
)
