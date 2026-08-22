"""Passive agent / narrative-character binding for P11.14D."""

from __future__ import annotations

from dataclasses import dataclass

from language.narrative_model import NarrativeCharacter

from .model import AgentDefinition


@dataclass(frozen=True)
class AgentCharacterBinding:
    """Bind one canonical AgentDefinition to one canonical NarrativeCharacter."""

    definition: AgentDefinition
    character: NarrativeCharacter

    def __post_init__(self) -> None:
        if type(self.definition) is not AgentDefinition:
            raise TypeError(
                "AgentCharacterBinding.definition must be an exact "
                "AgentDefinition"
            )
        if type(self.character) is not NarrativeCharacter:
            raise TypeError(
                "AgentCharacterBinding.character must be an exact "
                "NarrativeCharacter"
            )


__all__ = ("AgentCharacterBinding",)