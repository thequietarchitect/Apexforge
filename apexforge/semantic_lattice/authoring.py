"""P11.8E neutral semantic-lattice authoring and optional Codex advisory path.

Codex is an advisory provider only. Its proposals enter the same P11.8D
construction boundary as human- or tool-originated proposals.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from .construction import (
    SemanticLatticeSnapshot,
    construct_semantic_lattice_snapshot,
)
from .model import ParametricSemanticLattice
from .records import SemanticLatticeRelationship, SemanticLatticeSubjectReference


def _text(value: object, field: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")
    return value


class SemanticLatticeAuthoringSource(Enum):
    """Neutral provenance taxonomy for lattice authoring proposals."""

    HUMAN = "human"
    TOOL = "tool"
    ADVISORY = "advisory"


@dataclass(frozen=True)
class SemanticLatticeAuthoringProposal:
    """Immutable neutral proposal before canonical P11.8D construction."""

    source: SemanticLatticeAuthoringSource
    author_identity: str
    provider_identity: str
    lattice: ParametricSemanticLattice
    subjects: Tuple[SemanticLatticeSubjectReference, ...] = ()
    relationships: Tuple[SemanticLatticeRelationship, ...] = ()

    def __post_init__(self) -> None:
        if type(self.source) is not SemanticLatticeAuthoringSource:
            raise TypeError("source must be an exact SemanticLatticeAuthoringSource")
        _text(self.author_identity, "author_identity")
        _text(self.provider_identity, "provider_identity")
        # P11.8D remains the single structural construction/closure authority.
        construct_semantic_lattice_snapshot(
            self.lattice,
            subjects=self.subjects,
            relationships=self.relationships,
        )


def adapt_semantic_lattice_authoring_proposal(
    proposal: SemanticLatticeAuthoringProposal,
) -> SemanticLatticeSnapshot:
    """Route any neutral proposal through the ordinary P11.8D constructor."""

    if type(proposal) is not SemanticLatticeAuthoringProposal:
        raise TypeError("proposal must be an exact SemanticLatticeAuthoringProposal")
    return construct_semantic_lattice_snapshot(
        proposal.lattice,
        subjects=proposal.subjects,
        relationships=proposal.relationships,
    )


def adapt_codex_semantic_lattice_proposal(
    proposal: SemanticLatticeAuthoringProposal,
) -> SemanticLatticeSnapshot:
    """Adapt an optional Codex advisory proposal with no privileged path."""

    if type(proposal) is not SemanticLatticeAuthoringProposal:
        raise TypeError("proposal must be an exact SemanticLatticeAuthoringProposal")
    if proposal.source is not SemanticLatticeAuthoringSource.ADVISORY:
        raise ValueError("Codex proposals must use the advisory authoring source")
    if proposal.provider_identity != "codex":
        raise ValueError("Codex proposal provider_identity must be 'codex'")
    return adapt_semantic_lattice_authoring_proposal(proposal)


__all__ = (
    "SemanticLatticeAuthoringProposal",
    "SemanticLatticeAuthoringSource",
    "adapt_codex_semantic_lattice_proposal",
    "adapt_semantic_lattice_authoring_proposal",
)
