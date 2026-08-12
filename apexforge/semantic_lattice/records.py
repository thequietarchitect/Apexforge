"""P11.8C immutable semantic-lattice subject, relationship, and evidence records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple


def _text(value: object, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")


def _identity(value: object, field: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be an exact tuple")
    if not value:
        raise ValueError(f"{field} must not be empty")
    for index, item in enumerate(value):
        _text(item, f"{field}[{index}]")


def _value(value: Any, field: str) -> None:
    if type(value) in (str, int, float, bool, type(None)):
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _value(item, f"{field}[{index}]")
        return
    raise TypeError(f"{field} must be an immutable scalar or tuple")


@dataclass(frozen=True)
class SemanticLatticeSubjectReference:
    """Passive index reference to an identity owned by another canonical domain."""

    source_domain: str
    source_kind: str
    source_identity: Tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.source_domain, "SemanticLatticeSubjectReference.source_domain")
        _text(self.source_kind, "SemanticLatticeSubjectReference.source_kind")
        _identity(
            self.source_identity,
            "SemanticLatticeSubjectReference.source_identity",
        )


@dataclass(frozen=True)
class SemanticLatticeEvidence:
    """Immutable passive evidence attached to a lattice relationship."""

    kind: str
    facts: Tuple[Tuple[str, Any], ...] = ()
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.kind, "SemanticLatticeEvidence.kind")
        if type(self.facts) is not tuple:
            raise TypeError("SemanticLatticeEvidence.facts must be an exact tuple")
        for index, fact in enumerate(self.facts):
            if type(fact) is not tuple or len(fact) != 2:
                raise TypeError(
                    "SemanticLatticeEvidence.facts entries must be exact key/value tuples"
                )
            key, value = fact
            _text(key, f"SemanticLatticeEvidence.facts[{index}].key")
            _value(value, f"SemanticLatticeEvidence.facts[{index}].value")
        if type(self.provenance) is not tuple:
            raise TypeError("SemanticLatticeEvidence.provenance must be an exact tuple")
        for index, item in enumerate(self.provenance):
            _text(item, f"SemanticLatticeEvidence.provenance[{index}]")


@dataclass(frozen=True)
class SemanticLatticeRelationship:
    """Passive typed relation between two external canonical subjects."""

    source: SemanticLatticeSubjectReference
    relation: str
    target: SemanticLatticeSubjectReference
    evidence: Tuple[SemanticLatticeEvidence, ...] = ()

    def __post_init__(self) -> None:
        if type(self.source) is not SemanticLatticeSubjectReference:
            raise TypeError("SemanticLatticeRelationship.source must be an exact subject reference")
        _text(self.relation, "SemanticLatticeRelationship.relation")
        if type(self.target) is not SemanticLatticeSubjectReference:
            raise TypeError("SemanticLatticeRelationship.target must be an exact subject reference")
        if type(self.evidence) is not tuple:
            raise TypeError("SemanticLatticeRelationship.evidence must be an exact tuple")
        if any(type(item) is not SemanticLatticeEvidence for item in self.evidence):
            raise TypeError(
                "SemanticLatticeRelationship.evidence must contain exact SemanticLatticeEvidence values"
            )


__all__ = (
    "SemanticLatticeSubjectReference",
    "SemanticLatticeEvidence",
    "SemanticLatticeRelationship",
)
