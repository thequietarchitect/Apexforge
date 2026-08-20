"""Deterministic TAM production from existing canonical compiler evidence.

P11-TAM-C introduced pure SourceMap adapters. P11-TAM-D extended the same
observational layer to frozen declaration ownership and declared identity
metadata. P11-TAM-E adds passive reference, scope, candidate, and resolution
outcome observation. No producer in this module executes resolution.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Dict, List, Tuple, Union

from authority.model import AuthorityCheck, AuthorityGrant, Principal
from language.compiler import SourceMap, SourceMapEntry
from language.declarations import ProjectDeclarationOwner, ProjectDeclarationOwnership
from language.identities import ProjectDeclaredIdentity, ProjectIdentityIndex
from language.resolution_candidates import (
    ProjectQualification,
    ProjectResolutionCandidate,
    ProjectResolutionCandidateIndex,
)
from language.resolution_context import ProjectResolutionContext
from language.resolution_queries import (
    ProjectAmbiguousResolution,
    ProjectResolvedBinding,
    ProjectResolutionQuery,
    ProjectUnresolvedResolution,
)
from language.source import SourceSpan
from type_system.constraints import ApexTypeConstraint
from type_system.generics import ApexTypeVariable
from type_system.inference import FunctionSignature
from type_system.model import ApexType
from type_system.specialization import GenericSpecialization
from type_system.substitution import GenericSubstitution

from .model import TraceDomain, TraceIdentity, TraceMap, TraceRecord


_SOURCE_DOMAIN = TraceDomain("source")
_DECLARATION_DOMAIN = TraceDomain("declaration")
_REFERENCE_DOMAIN = TraceDomain("reference")
_SCOPE_DOMAIN = TraceDomain("scope")
_OWNERSHIP_DOMAIN = TraceDomain("ownership")
_TRANSFORMATION_DOMAIN = TraceDomain("transformation")
_TYPE_DOMAIN = TraceDomain("type")
_AUTHORITY_DOMAIN = TraceDomain("authority")

_ResolutionOutcome = Union[
    ProjectResolvedBinding,
    ProjectUnresolvedResolution,
    ProjectAmbiguousResolution,
]


def _require_index(value: object) -> int:
    if type(value) is not int:
        raise TypeError("entry_index must be an exact int")
    if value < 0:
        raise ValueError("entry_index must be non-negative")
    return value


def _position_key(position: object) -> str:
    line = getattr(position, "line")
    column = getattr(position, "column")
    offset = getattr(position, "offset", None)
    return "{}:{}:{}".format(line, column, "" if offset is None else offset)


def _span_key(span: SourceSpan) -> str:
    if not isinstance(span, SourceSpan):
        raise TypeError("span must be SourceSpan")
    return "{}|{}|{}".format(
        span.source_name,
        _position_key(span.start),
        _position_key(span.end),
    )


def _segments_key(segments: Tuple[str, ...]) -> str:
    return ".".join(segments)


def _optional_segments_key(segments: object) -> str:
    if segments is None:
        return "<none>"
    return _segments_key(segments)


def _qualification_key(qualification: ProjectQualification) -> Tuple[str, ...]:
    return (
        qualification.kind,
        _segments_key(qualification.module_segments),
        _segments_key(qualification.declaration_path),
        "legacy" if qualification.legacy else "module",
    )


def _query_key(query: ProjectResolutionQuery) -> Tuple[str, ...]:
    return (
        query.kind,
        _segments_key(query.declaration_path),
        _optional_segments_key(query.module_segments),
    )


def _context_key(context: ProjectResolutionContext) -> Tuple[str, ...]:
    imported = "|".join(
        _segments_key(module_segments)
        for module_segments in context.imported_modules
    )
    return (
        context.source_name,
        _segments_key(context.module_segments),
        imported,
    )


def _candidate_key(candidate: ProjectResolutionCandidate) -> Tuple[str, ...]:
    identity = candidate.identity
    owner = candidate.owner
    return (
        identity.kind,
        identity.declared_name,
        identity.current_air_id,
        identity.source_name,
        "" if identity.module_name is None else identity.module_name,
        identity.qualified_display_name,
        _span_key(identity.span),
        owner.kind,
        owner.air_id,
        owner.source_name,
        "" if owner.module_name is None else owner.module_name,
        _span_key(owner.span),
    ) + _qualification_key(candidate.qualification)


def _digest_identity(prefix: str, parts: Tuple[str, ...]) -> TraceIdentity:
    payload = "\x1f".join((prefix,) + parts).encode("utf-8")
    digest = sha256(payload).hexdigest()
    return TraceIdentity("tam:{}:{}".format(prefix, digest))


def trace_identity_for_source_span(span: SourceSpan) -> TraceIdentity:
    """Return the deterministic TAM identity for an existing source span."""

    return _digest_identity("source", (_span_key(span),))


def trace_identity_for_source_map_entry(
    entry: SourceMapEntry,
    *,
    entry_index: int,
) -> TraceIdentity:
    """Return the deterministic TAM identity for one ordered SourceMap entry."""

    if not isinstance(entry, SourceMapEntry):
        raise TypeError("entry must be SourceMapEntry")
    selected_index = _require_index(entry_index)
    return _digest_identity(
        "source-map-entry",
        (
            str(selected_index),
            entry.air_id,
            _span_key(entry.span),
        ),
    )


def trace_map_from_source_map(source_map: SourceMap) -> TraceMap:
    """Project an existing SourceMap into immutable observational TAM records."""

    if not isinstance(source_map, SourceMap):
        raise TypeError("source_map must be SourceMap")

    entries = tuple(source_map.entries)
    if not entries:
        return TraceMap()

    entry_ids = tuple(
        trace_identity_for_source_map_entry(entry, entry_index=index)
        for index, entry in enumerate(entries)
    )

    downstream_by_source: Dict[TraceIdentity, List[TraceIdentity]] = {}
    source_span_by_id: Dict[TraceIdentity, SourceSpan] = {}

    for entry, entry_id in zip(entries, entry_ids):
        source_id = trace_identity_for_source_span(entry.span)
        if source_id not in downstream_by_source:
            downstream_by_source[source_id] = []
            source_span_by_id[source_id] = entry.span
        downstream_by_source[source_id].append(entry_id)

    records: List[TraceRecord] = []
    emitted_sources = set()

    for entry, entry_id in zip(entries, entry_ids):
        source_id = trace_identity_for_source_span(entry.span)

        if source_id not in emitted_sources:
            records.append(
                TraceRecord(
                    trace_id=source_id,
                    domain=_SOURCE_DOMAIN,
                    producer="language.source",
                    owner="language.source",
                    representation="source-span",
                    source_span=source_span_by_id[source_id],
                    downstream_trace_ids=tuple(
                        downstream_by_source[source_id]
                    ),
                )
            )
            emitted_sources.add(source_id)

        records.append(
            TraceRecord(
                trace_id=entry_id,
                domain=_TRANSFORMATION_DOMAIN,
                producer="language.compiler",
                owner="language.compiler",
                representation="source-map-entry",
                source_span=entry.span,
                canonical_identity=entry.air_id,
                upstream_trace_ids=(source_id,),
            )
        )

    return TraceMap(tuple(records))


def trace_record_from_declaration_owner(
    declaration: ProjectDeclarationOwner,
    *,
    declaration_index: int,
) -> TraceRecord:
    """Project one frozen declaration-ownership record into TAM evidence."""

    if type(declaration) is not ProjectDeclarationOwner:
        raise TypeError("declaration must be ProjectDeclarationOwner")
    selected_index = _require_index(declaration_index)
    trace_id = _digest_identity(
        "declaration-owner",
        (
            str(selected_index),
            declaration.kind,
            declaration.air_id,
            declaration.source_name,
            "" if declaration.module_name is None else declaration.module_name,
            _span_key(declaration.span),
        ),
    )
    return TraceRecord(
        trace_id=trace_id,
        domain=_OWNERSHIP_DOMAIN,
        producer="language.declarations",
        owner="language.declarations",
        representation="project-declaration-owner",
        source_span=declaration.span,
        canonical_identity=declaration.air_id,
    )


def trace_record_from_declared_identity(
    identity: ProjectDeclaredIdentity,
    *,
    identity_index: int,
) -> TraceRecord:
    """Project one frozen declared-identity record into TAM evidence."""

    if type(identity) is not ProjectDeclaredIdentity:
        raise TypeError("identity must be ProjectDeclaredIdentity")
    selected_index = _require_index(identity_index)
    trace_id = _digest_identity(
        "declared-identity",
        (
            str(selected_index),
            identity.kind,
            identity.declared_name,
            identity.current_air_id,
            identity.source_name,
            "" if identity.module_name is None else identity.module_name,
            identity.qualified_display_name,
            _span_key(identity.span),
        ),
    )
    return TraceRecord(
        trace_id=trace_id,
        domain=_DECLARATION_DOMAIN,
        producer="language.identities",
        owner="language.identities",
        representation="project-declared-identity",
        source_span=identity.span,
        canonical_identity=identity.current_air_id,
    )


def trace_map_from_declaration_identity_indexes(
    declaration_ownership: ProjectDeclarationOwnership,
    identity_index: ProjectIdentityIndex,
) -> TraceMap:
    """Project frozen ownership and identity indexes into deterministic TAM."""

    if type(declaration_ownership) is not ProjectDeclarationOwnership:
        raise TypeError(
            "declaration_ownership must be ProjectDeclarationOwnership"
        )
    if type(identity_index) is not ProjectIdentityIndex:
        raise TypeError("identity_index must be ProjectIdentityIndex")

    ownership_records = tuple(
        trace_record_from_declaration_owner(
            declaration,
            declaration_index=index,
        )
        for index, declaration in enumerate(declaration_ownership.declarations)
    )
    identity_records = tuple(
        trace_record_from_declared_identity(
            identity,
            identity_index=index,
        )
        for index, identity in enumerate(identity_index.identities)
    )
    return TraceMap(ownership_records + identity_records)


def trace_record_from_resolution_query(
    query: ProjectResolutionQuery,
) -> TraceRecord:
    """Project an already-formed resolution query as reference evidence."""

    if type(query) is not ProjectResolutionQuery:
        raise TypeError("query must be ProjectResolutionQuery")
    return TraceRecord(
        trace_id=_digest_identity("resolution-query", _query_key(query)),
        domain=_REFERENCE_DOMAIN,
        producer="language.resolution_queries",
        owner="language.resolution_queries",
        representation="project-resolution-query",
    )


def trace_record_from_resolution_context(
    context: ProjectResolutionContext,
) -> TraceRecord:
    """Project an already-formed resolution context as scope evidence."""

    if type(context) is not ProjectResolutionContext:
        raise TypeError("context must be ProjectResolutionContext")
    return TraceRecord(
        trace_id=_digest_identity("resolution-context", _context_key(context)),
        domain=_SCOPE_DOMAIN,
        producer="language.resolution_context",
        owner="language.resolution_context",
        representation="project-resolution-context",
    )


def trace_record_from_resolution_candidate(
    candidate: ProjectResolutionCandidate,
    *,
    candidate_index: int,
) -> TraceRecord:
    """Project one passive resolution candidate without selecting it."""

    if type(candidate) is not ProjectResolutionCandidate:
        raise TypeError("candidate must be ProjectResolutionCandidate")
    selected_index = _require_index(candidate_index)
    identity = candidate.identity
    return TraceRecord(
        trace_id=_digest_identity(
            "resolution-candidate",
            (str(selected_index),) + _candidate_key(candidate),
        ),
        domain=_REFERENCE_DOMAIN,
        producer="language.resolution_candidates",
        owner="language.resolution_candidates",
        representation="project-resolution-candidate",
        source_span=identity.span,
        canonical_identity=identity.current_air_id,
    )


def trace_record_from_resolution_outcome(
    outcome: _ResolutionOutcome,
) -> TraceRecord:
    """Project an existing resolved, unresolved, or ambiguous outcome."""

    if type(outcome) is ProjectResolvedBinding:
        candidate = outcome.candidate
        return TraceRecord(
            trace_id=_digest_identity(
                "resolved-binding",
                _query_key(outcome.query) + _candidate_key(candidate),
            ),
            domain=_REFERENCE_DOMAIN,
            producer="language.resolution_queries",
            owner="language.resolution_queries",
            representation="project-resolved-binding",
            source_span=candidate.identity.span,
            canonical_identity=candidate.identity.current_air_id,
        )

    if type(outcome) is ProjectUnresolvedResolution:
        return TraceRecord(
            trace_id=_digest_identity(
                "unresolved-resolution",
                _query_key(outcome.query),
            ),
            domain=_REFERENCE_DOMAIN,
            producer="language.resolution_queries",
            owner="language.resolution_queries",
            representation="project-unresolved-resolution",
        )

    if type(outcome) is ProjectAmbiguousResolution:
        candidate_parts: Tuple[str, ...] = ()
        for candidate in outcome.candidates:
            candidate_parts += _candidate_key(candidate)
        return TraceRecord(
            trace_id=_digest_identity(
                "ambiguous-resolution",
                _query_key(outcome.query) + candidate_parts,
            ),
            domain=_REFERENCE_DOMAIN,
            producer="language.resolution_queries",
            owner="language.resolution_queries",
            representation="project-ambiguous-resolution",
        )

    raise TypeError(
        "outcome must be ProjectResolvedBinding, "
        "ProjectUnresolvedResolution, or ProjectAmbiguousResolution"
    )


def trace_map_from_resolution_observation(
    index: ProjectResolutionCandidateIndex,
    query: ProjectResolutionQuery,
    context: ProjectResolutionContext,
    outcome: _ResolutionOutcome,
) -> TraceMap:
    """Project already-existing resolution inputs and outcome without resolving."""

    if type(index) is not ProjectResolutionCandidateIndex:
        raise TypeError("index must be ProjectResolutionCandidateIndex")
    if type(query) is not ProjectResolutionQuery:
        raise TypeError("query must be ProjectResolutionQuery")
    if type(context) is not ProjectResolutionContext:
        raise TypeError("context must be ProjectResolutionContext")
    if type(outcome) not in (
        ProjectResolvedBinding,
        ProjectUnresolvedResolution,
        ProjectAmbiguousResolution,
    ):
        raise TypeError(
            "outcome must be a canonical project resolution outcome"
        )
    if outcome.query != query:
        raise ValueError("outcome.query must equal the observed query")

    if type(outcome) is ProjectResolvedBinding:
        if outcome.candidate not in index.candidates:
            raise ValueError(
                "resolved outcome candidate must belong to the observed candidate index"
            )
    elif type(outcome) is ProjectAmbiguousResolution:
        if any(candidate not in index.candidates for candidate in outcome.candidates):
            raise ValueError(
                "ambiguous outcome candidates must belong to the observed candidate index"
            )

    records = [
        trace_record_from_resolution_query(query),
        trace_record_from_resolution_context(context),
    ]
    records.extend(
        trace_record_from_resolution_candidate(
            candidate,
            candidate_index=candidate_index,
        )
        for candidate_index, candidate in enumerate(index.candidates)
    )
    records.append(trace_record_from_resolution_outcome(outcome))
    return TraceMap(tuple(records))



def _type_identity_key(value: object) -> Tuple[str, ...]:
    if type(value) is ApexType:
        parts: Tuple[str, ...] = (
            "apex-type",
            value.name,
            str(len(value.arguments)),
        )
        for index, argument in enumerate(value.arguments):
            parts += ("argument", str(index)) + _type_identity_key(argument)
        return parts

    if type(value) is ApexTypeVariable:
        parts = (
            "apex-type-variable",
            value.name,
            value.owner,
            str(len(value.constraints)),
        )
        for index, constraint in enumerate(value.constraints):
            parts += (
                "constraint",
                str(index),
                constraint.name,
                constraint.description,
            )
        return parts

    raise TypeError("value must be ApexType or ApexTypeVariable")


def _optional_type_identity_key(value: object) -> Tuple[str, ...]:
    if value is None:
        return ("none",)
    return ("type",) + _type_identity_key(value)


def _function_signature_key(value: FunctionSignature) -> Tuple[str, ...]:
    parts: Tuple[str, ...] = (
        "function-signature",
        value.name,
        "parameter-count",
        str(len(value.parameter_types)),
    )
    for index, parameter_type in enumerate(value.parameter_types):
        parts += (
            "parameter",
            str(index),
        ) + _optional_type_identity_key(parameter_type)

    parts += ("return",) + _optional_type_identity_key(value.return_type)
    parts += ("type-parameter-count", str(len(value.type_parameters)))
    for index, variable in enumerate(value.type_parameters):
        parts += (
            "type-parameter",
            str(index),
        ) + _type_identity_key(variable)
    return parts


def _generic_substitution_key(value: GenericSubstitution) -> Tuple[str, ...]:
    parts: Tuple[str, ...] = (
        "generic-substitution",
        "binding-count",
        str(len(value.bindings)),
    )
    for index, binding in enumerate(value.bindings):
        variable, value_type = binding
        parts += (
            "binding",
            str(index),
            "variable",
        ) + _type_identity_key(variable)
        parts += ("value",) + _type_identity_key(value_type)
    return parts


def _generic_specialization_key(
    value: GenericSpecialization,
) -> Tuple[str, ...]:
    parts: Tuple[str, ...] = (
        "generic-specialization",
        "target",
        value.key.target,
        "type-argument-count",
        str(len(value.key.type_arguments)),
    )
    for index, type_argument in enumerate(value.key.type_arguments):
        parts += (
            "type-argument",
            str(index),
        ) + _type_identity_key(type_argument)

    parts += (
        "parameter-count",
        str(len(value.parameter_types)),
    )
    for index, parameter_type in enumerate(value.parameter_types):
        parts += (
            "parameter",
            str(index),
        ) + _optional_type_identity_key(parameter_type)

    parts += ("return",) + _optional_type_identity_key(value.return_type)
    return parts


def trace_record_from_type_evidence(
    evidence: object,
    *,
    evidence_index: int,
) -> TraceRecord:
    """Project one already-existing canonical type-system value into TAM."""

    selected_index = _require_index(evidence_index)

    if type(evidence) is ApexType:
        owner = "type_system.model"
        representation = "apex-type"
        key = _type_identity_key(evidence)
    elif type(evidence) is ApexTypeConstraint:
        owner = "type_system.constraints"
        representation = "apex-type-constraint"
        key = (
            "apex-type-constraint",
            evidence.name,
            evidence.description,
        )
    elif type(evidence) is ApexTypeVariable:
        owner = "type_system.generics"
        representation = "apex-type-variable"
        key = _type_identity_key(evidence)
    elif type(evidence) is FunctionSignature:
        owner = "type_system.inference"
        representation = "function-signature"
        key = _function_signature_key(evidence)
    elif type(evidence) is GenericSubstitution:
        owner = "type_system.substitution"
        representation = "generic-substitution"
        key = _generic_substitution_key(evidence)
    elif type(evidence) is GenericSpecialization:
        owner = "type_system.specialization"
        representation = "generic-specialization"
        key = _generic_specialization_key(evidence)
    else:
        raise TypeError(
            "evidence must be ApexType, ApexTypeConstraint, "
            "ApexTypeVariable, FunctionSignature, GenericSubstitution, "
            "or GenericSpecialization"
        )

    return TraceRecord(
        trace_id=_digest_identity(
            "type-evidence",
            (str(selected_index),) + key,
        ),
        domain=_TYPE_DOMAIN,
        producer=owner,
        owner=owner,
        representation=representation,
    )


def trace_map_from_type_evidence(
    evidence: Tuple[object, ...],
) -> TraceMap:
    """Project an ordered tuple of already-existing type evidence into TAM."""

    if type(evidence) is not tuple:
        raise TypeError("evidence must be an exact tuple")

    records = tuple(
        trace_record_from_type_evidence(
            value,
            evidence_index=index,
        )
        for index, value in enumerate(evidence)
    )
    return TraceMap(records)


def _authority_check_key(value: AuthorityCheck) -> Tuple[str, ...]:
    return (
        "authority-check",
        value.id,
        value.principal,
        value.capability,
        value.resource,
    )


def _authority_grant_key(value: AuthorityGrant) -> Tuple[str, ...]:
    return (
        "authority-grant",
        value.principal,
        value.capability,
        value.resource,
    )


def trace_record_from_authority_evidence(
    evidence: object,
    *,
    evidence_index: int,
) -> TraceRecord:
    """Project one already-existing canonical authority value into TAM."""

    selected_index = _require_index(evidence_index)

    if type(evidence) is Principal:
        representation = "principal"
        key = ("principal", evidence.id)
        canonical_identity = evidence.id
    elif type(evidence) is AuthorityCheck:
        representation = "authority-check"
        key = _authority_check_key(evidence)
        canonical_identity = evidence.id
    elif type(evidence) is AuthorityGrant:
        representation = "authority-grant"
        key = _authority_grant_key(evidence)
        canonical_identity = None
    else:
        raise TypeError(
            "evidence must be Principal, AuthorityCheck, or AuthorityGrant"
        )

    return TraceRecord(
        trace_id=_digest_identity(
            "authority-evidence",
            (str(selected_index),) + key,
        ),
        domain=_AUTHORITY_DOMAIN,
        producer="authority.model",
        owner="authority.model",
        representation=representation,
        canonical_identity=canonical_identity,
    )


def trace_map_from_authority_evidence(
    evidence: Tuple[object, ...],
) -> TraceMap:
    """Project an ordered tuple of passive authority evidence into TAM."""

    if type(evidence) is not tuple:
        raise TypeError("evidence must be an exact tuple")

    records = tuple(
        trace_record_from_authority_evidence(
            value,
            evidence_index=index,
        )
        for index, value in enumerate(evidence)
    )
    return TraceMap(records)

__all__ = (
    "trace_identity_for_source_map_entry",
    "trace_identity_for_source_span",
    "trace_map_from_source_map",
    "trace_map_from_declaration_identity_indexes",
    "trace_record_from_declaration_owner",
    "trace_record_from_declared_identity",
    "trace_record_from_resolution_query",
    "trace_record_from_resolution_context",
    "trace_record_from_resolution_candidate",
    "trace_record_from_resolution_outcome",
    "trace_map_from_resolution_observation",
    "trace_record_from_type_evidence",
    "trace_map_from_type_evidence",
    "trace_record_from_authority_evidence",
    "trace_map_from_authority_evidence",
)