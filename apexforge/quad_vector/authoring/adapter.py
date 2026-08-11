"""Canonical neutral authoring adapter for the P11.7 Quad-Vector Engine.

P11.7I accepts human-authored, tool-generated, and advisory module declarations
through one validation path and translates them into canonical
QuadVectorModuleSpec snapshots.  It does not register, bind, execute, discover,
import, or load implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from ..model import QuadVectorLane, QuadVectorResourceBudget
from ..module import QuadVectorModuleKind, QuadVectorModuleSpec


class QuadVectorAuthoringSource(Enum):
    """Canonical provenance taxonomy for module declarations."""

    HUMAN = "human"
    TOOL = "tool"
    ADVISORY = "advisory"


def _require_text(value: object, *, owner: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{owner} must be a non-empty string")
    return value


@dataclass(frozen=True)
class QuadVectorModuleDeclaration:
    """Immutable neutral authoring declaration prior to registry admission."""

    source: QuadVectorAuthoringSource
    author_identity: str
    canonical_id: str
    version: str
    kind: QuadVectorModuleKind
    accepted_inputs: Tuple[str, ...]
    produced_outputs: Tuple[str, ...]
    eligible_vectors: Tuple[QuadVectorLane, ...]
    dependencies: Tuple[str, ...]
    determinism_contract: str
    authority_requirements: Tuple[str, ...]
    resource_budget: QuadVectorResourceBudget
    implementation_reference: str

    def __post_init__(self) -> None:
        if type(self.source) is not QuadVectorAuthoringSource:
            raise TypeError("source must be an exact QuadVectorAuthoringSource")
        _require_text(self.author_identity, owner="author_identity")

        # Reuse the frozen canonical module contract as the single validation
        # authority for identity, version, tuple fields, dependencies, vector
        # eligibility, determinism, authority, budget, and implementation ref.
        QuadVectorModuleSpec(
            canonical_id=self.canonical_id,
            version=self.version,
            kind=self.kind,
            determinism_contract=self.determinism_contract,
            implementation_reference=self.implementation_reference,
            accepted_inputs=self.accepted_inputs,
            produced_outputs=self.produced_outputs,
            eligible_vectors=self.eligible_vectors,
            dependencies=self.dependencies,
            authority_requirements=self.authority_requirements,
            resource_budget=self.resource_budget,
        )


@dataclass(frozen=True)
class QuadVectorAuthoredModule:
    """Immutable authored-module snapshot containing provenance and canonical spec."""

    source: QuadVectorAuthoringSource
    author_identity: str
    declaration: QuadVectorModuleDeclaration
    spec: QuadVectorModuleSpec

    def __post_init__(self) -> None:
        if type(self.source) is not QuadVectorAuthoringSource:
            raise TypeError("source must be an exact QuadVectorAuthoringSource")
        _require_text(self.author_identity, owner="author_identity")
        if type(self.declaration) is not QuadVectorModuleDeclaration:
            raise TypeError("declaration must be an exact QuadVectorModuleDeclaration")
        if type(self.spec) is not QuadVectorModuleSpec:
            raise TypeError("spec must be an exact QuadVectorModuleSpec")
        if self.source is not self.declaration.source:
            raise ValueError("source must match declaration source")
        if self.author_identity != self.declaration.author_identity:
            raise ValueError("author_identity must match declaration author_identity")


def adapt_quad_vector_module_declaration(
    declaration: QuadVectorModuleDeclaration,
) -> QuadVectorAuthoredModule:
    """Translate one validated neutral declaration into a canonical module spec."""

    if type(declaration) is not QuadVectorModuleDeclaration:
        raise TypeError(
            "declaration must be an exact QuadVectorModuleDeclaration"
        )

    spec = QuadVectorModuleSpec(
        canonical_id=declaration.canonical_id,
        version=declaration.version,
        kind=declaration.kind,
        determinism_contract=declaration.determinism_contract,
        implementation_reference=declaration.implementation_reference,
        accepted_inputs=declaration.accepted_inputs,
        produced_outputs=declaration.produced_outputs,
        eligible_vectors=declaration.eligible_vectors,
        dependencies=declaration.dependencies,
        authority_requirements=declaration.authority_requirements,
        resource_budget=declaration.resource_budget,
    )

    return QuadVectorAuthoredModule(
        source=declaration.source,
        author_identity=declaration.author_identity,
        declaration=declaration,
        spec=spec,
    )


__all__ = (
    "QuadVectorAuthoredModule",
    "QuadVectorAuthoringSource",
    "QuadVectorModuleDeclaration",
    "adapt_quad_vector_module_declaration",
)
