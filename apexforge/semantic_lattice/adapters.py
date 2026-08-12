"""P11.8E canonical source-domain projections into semantic-lattice records.

These adapters preserve source-owned identities. They do not resolve, rank,
execute, authorize, load, or mutate source-domain objects.
"""

from __future__ import annotations

from typing import Any

from air.model import (
    AIRAuthority,
    AIRDirective,
    AIRPrincipal,
    AIRRole,
    AIRWorkflow,
    EventDefinition,
    EventRecord,
    StateDefinition,
)
from authority.model import AuthorityCheck, AuthorityGrant, Principal
from language.identities import ProjectDeclaredIdentity
from language.narrative_model import NarrativeIdentity
from quad_vector.model import QuadVectorInput, ResultantVector

from .model import SemanticLatticeParameter
from .records import SemanticLatticeEvidence, SemanticLatticeSubjectReference


def _text(value: object, field: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")
    return value


def project_air_subject(value: object) -> SemanticLatticeSubjectReference:
    """Project one canonical AIR-owned identity without manufacturing an ID."""

    if type(value) is StateDefinition:
        kind, identity = "state", value.id
    elif type(value) is EventDefinition:
        kind, identity = "event_definition", value.id
    elif type(value) is EventRecord:
        kind, identity = "event_record", value.id
    elif type(value) is AIRDirective:
        kind, identity = "directive", value.id
    elif type(value) is AIRAuthority:
        kind, identity = "authority", value.id
    elif type(value) is AIRWorkflow:
        kind, identity = "workflow", value.id
    elif type(value) is AIRPrincipal:
        kind, identity = "principal", value.name
    elif type(value) is AIRRole:
        kind, identity = "role", value.name
    else:
        raise TypeError("value must be a supported exact AIR identity owner")
    return SemanticLatticeSubjectReference(
        source_domain="air",
        source_kind=kind,
        source_identity=(_text(identity, "AIR identity"),),
    )


def project_declared_air_identity(
    value: ProjectDeclaredIdentity,
) -> SemanticLatticeSubjectReference:
    """Project the already-canonical AIR ID carried by project identity metadata."""

    if type(value) is not ProjectDeclaredIdentity:
        raise TypeError("value must be an exact ProjectDeclaredIdentity")
    return SemanticLatticeSubjectReference(
        source_domain="air",
        source_kind=value.kind,
        source_identity=(_text(value.current_air_id, "ProjectDeclaredIdentity.current_air_id"),),
    )


def project_authority_subject(value: object) -> SemanticLatticeSubjectReference:
    """Project authority objects that actually own canonical IDs."""

    if type(value) is Principal:
        kind, identity = "principal", value.id
    elif type(value) is AuthorityCheck:
        kind, identity = "check", value.id
    else:
        raise TypeError("value must be an exact Principal or AuthorityCheck")
    return SemanticLatticeSubjectReference(
        source_domain="authority",
        source_kind=kind,
        source_identity=(_text(identity, "authority identity"),),
    )


def project_authority_grant_evidence(
    value: AuthorityGrant,
) -> SemanticLatticeEvidence:
    """Represent an ID-less AuthorityGrant as evidence rather than inventing identity."""

    if type(value) is not AuthorityGrant:
        raise TypeError("value must be an exact AuthorityGrant")
    return SemanticLatticeEvidence(
        kind="authority_grant",
        facts=(
            ("principal", value.principal),
            ("capability", value.capability),
            ("resource", value.resource),
        ),
        provenance=("authority:grant",),
    )


def project_narrative_subject(
    identity: NarrativeIdentity,
) -> SemanticLatticeSubjectReference:
    """Project the source-owned NarrativeIdentity(kind, path) directly."""

    if type(identity) is not NarrativeIdentity:
        raise TypeError("identity must be an exact NarrativeIdentity")
    return SemanticLatticeSubjectReference(
        source_domain="narrative",
        source_kind=identity.kind,
        source_identity=identity.path,
    )


def project_quad_vector_input_subject(
    value: QuadVectorInput,
) -> SemanticLatticeSubjectReference:
    """Project the canonical QuadVectorInput identity."""

    if type(value) is not QuadVectorInput:
        raise TypeError("value must be an exact QuadVectorInput")
    return SemanticLatticeSubjectReference(
        source_domain="quad_vector",
        source_kind="input",
        source_identity=(_text(value.identity, "QuadVectorInput.identity"),),
    )


def project_resultant_vector_evidence(
    value: ResultantVector,
) -> SemanticLatticeEvidence:
    """Project ID-less resultant state as passive evidence only."""

    if type(value) is not ResultantVector:
        raise TypeError("value must be an exact ResultantVector")
    contribution_facts = tuple(
        (
            item.lane.value,
            (item.magnitude, item.order, item.provenance),
        )
        for item in value.contributions
    )
    return SemanticLatticeEvidence(
        kind="quad_vector_resultant",
        facts=(
            ("coordinates", (value.x, value.y)),
            ("contributions", contribution_facts),
        ),
        provenance=value.provenance,
    )


def project_tam_traceability_parameter(
    key: str,
    value: Any,
) -> SemanticLatticeParameter:
    """Project TAM traceability metadata without fabricating a TAM subject model."""

    selected_key = _text(key, "key")
    return SemanticLatticeParameter(
        axis_id="tam.traceability",
        key=selected_key,
        value=value,
    )


__all__ = (
    "project_air_subject",
    "project_authority_grant_evidence",
    "project_authority_subject",
    "project_declared_air_identity",
    "project_narrative_subject",
    "project_quad_vector_input_subject",
    "project_resultant_vector_evidence",
    "project_tam_traceability_parameter",
)
