"""Immutable professional-archetype catalog for P11.14C."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .model import ProfessionalArchetype


def _require_canonical_id(value: object, owner: str) -> str:
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
class ProfessionalArchetypeCatalog:
    """Immutable authored-order catalog of professional archetypes."""

    archetypes: Tuple[ProfessionalArchetype, ...] = ()

    def __post_init__(self) -> None:
        if type(self.archetypes) is not tuple:
            raise TypeError(
                "ProfessionalArchetypeCatalog.archetypes must be an exact tuple"
            )

        seen = set()
        for index, archetype in enumerate(self.archetypes):
            if type(archetype) is not ProfessionalArchetype:
                raise TypeError(
                    "ProfessionalArchetypeCatalog.archetypes item {} must be "
                    "an exact ProfessionalArchetype".format(index)
                )
            canonical_id = archetype.canonical_id
            if canonical_id in seen:
                raise ValueError(
                    "ProfessionalArchetypeCatalog.archetypes must not contain "
                    "duplicate canonical IDs"
                )
            seen.add(canonical_id)

    def resolve(self, canonical_id: str) -> ProfessionalArchetype:
        """Resolve one canonical archetype without mutating the catalog."""

        _require_canonical_id(
            canonical_id,
            "ProfessionalArchetypeCatalog.resolve canonical_id",
        )

        for archetype in self.archetypes:
            if archetype.canonical_id == canonical_id:
                return archetype

        raise ValueError(
            "unknown professional archetype canonical ID {!r}".format(
                canonical_id
            )
        )


__all__ = ("ProfessionalArchetypeCatalog",)