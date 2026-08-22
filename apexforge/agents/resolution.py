"""Deterministic professional-archetype resolution for P11.14C."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .catalog import ProfessionalArchetypeCatalog
from .model import AgentDefinition, ProfessionalArchetype


@dataclass(frozen=True)
class AgentArchetypeResolution:
    """Immutable resolution of one AgentDefinition's archetype references."""

    definition: AgentDefinition
    archetypes: Tuple[ProfessionalArchetype, ...]

    def __post_init__(self) -> None:
        if type(self.definition) is not AgentDefinition:
            raise TypeError(
                "AgentArchetypeResolution.definition must be an exact "
                "AgentDefinition"
            )
        if type(self.archetypes) is not tuple:
            raise TypeError(
                "AgentArchetypeResolution.archetypes must be an exact tuple"
            )
        if len(self.archetypes) != len(self.definition.archetype_ids):
            raise ValueError(
                "AgentArchetypeResolution.archetypes length must match "
                "AgentDefinition.archetype_ids"
            )

        for index, archetype in enumerate(self.archetypes):
            if type(archetype) is not ProfessionalArchetype:
                raise TypeError(
                    "AgentArchetypeResolution.archetypes item {} must be an "
                    "exact ProfessionalArchetype".format(index)
                )
            expected_id = self.definition.archetype_ids[index]
            if archetype.canonical_id != expected_id:
                raise ValueError(
                    "AgentArchetypeResolution.archetypes item {} canonical ID "
                    "must match AgentDefinition.archetype_ids".format(index)
                )


def resolve_agent_archetypes(
    definition: AgentDefinition,
    catalog: ProfessionalArchetypeCatalog,
) -> AgentArchetypeResolution:
    """Resolve archetype IDs in frozen AgentDefinition declaration order."""

    if type(definition) is not AgentDefinition:
        raise TypeError(
            "resolve_agent_archetypes definition must be an exact "
            "AgentDefinition"
        )
    if type(catalog) is not ProfessionalArchetypeCatalog:
        raise TypeError(
            "resolve_agent_archetypes catalog must be an exact "
            "ProfessionalArchetypeCatalog"
        )

    resolved = tuple(
        catalog.resolve(archetype_id)
        for archetype_id in definition.archetype_ids
    )
    return AgentArchetypeResolution(
        definition=definition,
        archetypes=resolved,
    )


__all__ = (
    "AgentArchetypeResolution",
    "resolve_agent_archetypes",
)