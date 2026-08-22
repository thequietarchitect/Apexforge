"""Minimal immutable agent-domain declarations for P11.14B."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


def _require_canonical_id(value: object, owner: str) -> str:
    """Require an exact, non-empty, already-trimmed string identifier."""

    if type(value) is not str:
        raise TypeError(
            "{} must be an exact str; received {}".format(
                owner,
                type(value).__name__,
            )
        )
    if not value.strip():
        raise ValueError("{} must not be empty or whitespace".format(owner))
    if value != value.strip():
        raise ValueError("{} must already be trimmed".format(owner))
    return value


@dataclass(frozen=True)
class AgentIdentity:
    """Canonical passive identity for one declared agent."""

    canonical_id: str

    def __post_init__(self) -> None:
        _require_canonical_id(
            self.canonical_id,
            "AgentIdentity.canonical_id",
        )


@dataclass(frozen=True)
class ProfessionalArchetype:
    """Passive professional classification descriptor with no authority semantics."""

    canonical_id: str

    def __post_init__(self) -> None:
        _require_canonical_id(
            self.canonical_id,
            "ProfessionalArchetype.canonical_id",
        )


@dataclass(frozen=True)
class AgentDefinition:
    """Minimal immutable agent declaration with ordered archetype references."""

    identity: AgentIdentity
    archetype_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.identity) is not AgentIdentity:
            raise TypeError(
                "AgentDefinition.identity must be an exact AgentIdentity"
            )
        if type(self.archetype_ids) is not tuple:
            raise TypeError(
                "AgentDefinition.archetype_ids must be an exact tuple"
            )

        seen = set()
        for index, archetype_id in enumerate(self.archetype_ids):
            _require_canonical_id(
                archetype_id,
                "AgentDefinition.archetype_ids item {}".format(index),
            )
            if archetype_id in seen:
                raise ValueError(
                    "AgentDefinition.archetype_ids must not contain duplicates"
                )
            seen.add(archetype_id)


__all__ = (
    "AgentIdentity",
    "ProfessionalArchetype",
    "AgentDefinition",
)