"""P11.9C immutable AETHER-AIR predecessor, evidence, and intent-trace records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

from .model import AetherBehaviorIntent


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
class AetherPredecessorReference:
    """Passive reference to an identity owned by a canonical predecessor domain."""

    source_domain: str
    source_kind: str
    source_identity: Tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.source_domain, "AetherPredecessorReference.source_domain")
        _text(self.source_kind, "AetherPredecessorReference.source_kind")
        _identity(self.source_identity, "AetherPredecessorReference.source_identity")


@dataclass(frozen=True)
class AetherEvidence:
    """Immutable passive evidence supporting an AETHER-AIR intent trace."""

    kind: str
    facts: Tuple[Tuple[str, Any], ...] = ()
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.kind, "AetherEvidence.kind")
        if type(self.facts) is not tuple:
            raise TypeError("AetherEvidence.facts must be an exact tuple")
        for index, fact in enumerate(self.facts):
            if type(fact) is not tuple or len(fact) != 2:
                raise TypeError("AetherEvidence.facts entries must be exact key/value tuples")
            key, value = fact
            _text(key, f"AetherEvidence.facts[{index}].key")
            _value(value, f"AetherEvidence.facts[{index}].value")
        if type(self.provenance) is not tuple:
            raise TypeError("AetherEvidence.provenance must be an exact tuple")
        for index, item in enumerate(self.provenance):
            _text(item, f"AetherEvidence.provenance[{index}]")


@dataclass(frozen=True)
class AetherIntentTrace:
    """Passive trace from one canonical predecessor reference to an existing intent."""

    predecessor: AetherPredecessorReference
    intent: AetherBehaviorIntent
    evidence: Tuple[AetherEvidence, ...] = ()

    def __post_init__(self) -> None:
        if type(self.predecessor) is not AetherPredecessorReference:
            raise TypeError(
                "AetherIntentTrace.predecessor must be an exact AetherPredecessorReference"
            )
        if type(self.intent) is not AetherBehaviorIntent:
            raise TypeError("AetherIntentTrace.intent must be an exact AetherBehaviorIntent")
        if type(self.evidence) is not tuple:
            raise TypeError("AetherIntentTrace.evidence must be an exact tuple")
        if any(type(item) is not AetherEvidence for item in self.evidence):
            raise TypeError(
                "AetherIntentTrace.evidence must contain exact AetherEvidence values"
            )


__all__ = (
    "AetherPredecessorReference",
    "AetherEvidence",
    "AetherIntentTrace",
)
