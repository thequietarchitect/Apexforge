"""P13.4 immutable mapping projections and owner-evidence step plans.

Metadata order is not a live execution schedule. Planning needs a separately
supplied known observation order; it never selects a path or advances execution.
No file access, emission, compilation, execution, or control dispatch occurs here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
import re

from language.source import SourceSpan, SourceText
from air.model import VerifiedAIRProgram
from tooling.debug_metadata import (SourceIdentity, OperationReference, AssignmentLocator,
                                    MetadataSidecar, MetadataAssociation)
from tooling.source_air_mapping import SourceAIRMapping
from apexforge.native_backend.source_mapping import NativeSourceMapping
from tooling.trace_retention import NativeResultAssociation, ProvenanceScope
from tooling.debug_session import DebugSession, SessionReference, ExecutionReference, Lifecycle, Capability
from tooling.debug_inspection import SessionInspection

SCHEMA = "apexforge.debug-correlation/v1"


class CorrelationError(ValueError):
    pass


def _require(condition, reason):
    if not condition:
        raise CorrelationError(reason)


def _text(value):
    _require(type(value) is str and re.fullmatch(r"[A-Za-z0-9_.:/-]+", value) is not None
             and not value.startswith("/") and ".." not in value, "invalid_reference")


def _hash(value):
    _require(type(value) is str and re.fullmatch(r"[0-9A-F]{64}", value) is not None,
             "invalid_fingerprint")


def _number(value):
    _require(type(value) is int and value >= 0, "invalid_occurrence")


def _form(kind, value):
    return json.dumps((SCHEMA, kind, value), ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


class Canonical:
    def fingerprint(self):
        return sha256(self.canonical_form().encode("utf-8")).hexdigest().upper()


class Availability(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    NOT_APPLICABLE = "not_applicable"
    AMBIGUOUS = "ambiguous"


def _span(span):
    return (span.source_name, (span.start.line, span.start.column, span.start.offset),
            (span.end.line, span.end.column, span.end.offset))


@dataclass(frozen=True)
class SourceReference(Canonical):
    document: SourceIdentity
    span: SourceSpan
    construct: tuple[str, str, str]

    def __post_init__(self):
        _require(type(self.document) is SourceIdentity and type(self.span) is SourceSpan
                 and self.span.source_name == self.document.logical_name, "source_identity_mismatch")
        _require(type(self.construct) is tuple and len(self.construct) == 3 and
                 all(type(x) is str for x in self.construct), "invalid_construct")

    def canonical_form(self):
        return _form("source", (self.document.canonical_identity(), _span(self.span), self.construct))

    def location_key(self):
        return (self.document.canonical_identity(), _span(self.span))


@dataclass(frozen=True)
class AIRReference(Canonical):
    operation: OperationReference

    def __post_init__(self):
        _require(type(self.operation) is OperationReference, "invalid_air_reference")

    @property
    def directive(self):
        locator = self.operation.identity.locator
        return locator.directive_id if type(locator) is AssignmentLocator else None

    def canonical_form(self):
        return _form("air", self.operation.canonical_identity())


@dataclass(frozen=True)
class NativeRegionReference(Canonical):
    generated_document: SourceIdentity
    span: SourceSpan
    operation_id: str
    mapping_fingerprint: str
    association_fingerprint: str
    # Artifact provenance is unavailable unless an owner supplies linked evidence.
    artifact_references: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        _require(type(self.generated_document) is SourceIdentity and type(self.span) is SourceSpan
                 and self.span.source_name == self.generated_document.logical_name,
                 "native_document_mismatch")
        _text(self.operation_id)
        _hash(self.mapping_fingerprint)
        _hash(self.association_fingerprint)
        _require(type(self.artifact_references) is tuple, "invalid_artifact_references")
        for pair in self.artifact_references:
            _require(type(pair) is tuple and len(pair) == 2, "invalid_artifact_reference")
            _text(pair[0])
            _hash(pair[1])
        _require(tuple(sorted(set(self.artifact_references))) == self.artifact_references,
                 "noncanonical_artifact_references")

    @property
    def machine_address_availability(self):
        return Availability.UNSUPPORTED

    def canonical_form(self):
        return _form("generated-native-region", (self.generated_document.canonical_identity(),
            _span(self.span), self.operation_id, self.mapping_fingerprint,
            self.association_fingerprint, self.artifact_references, "machine-address-unsupported"))


@dataclass(frozen=True)
class Candidates(Canonical):
    status: Availability
    values: tuple[SourceReference | NativeRegionReference, ...] = ()
    reason: str = ""

    def __post_init__(self):
        _require(type(self.status) is Availability and type(self.values) is tuple and
                 all(type(x) in (SourceReference, NativeRegionReference) for x in self.values),
                 "invalid_candidates")
        _require(not self.values or len({type(x) for x in self.values}) == 1, "mixed_candidates")
        ordered = tuple(sorted(set(self.values), key=lambda x: x.canonical_form()))
        object.__setattr__(self, "values", ordered)
        expected = Availability.AVAILABLE if len(ordered) == 1 else Availability.AMBIGUOUS
        _require((bool(ordered) and self.status is expected and self.reason == "") or
                 (not ordered and self.status in (Availability.UNAVAILABLE, Availability.UNSUPPORTED,
                  Availability.NOT_APPLICABLE) and type(self.reason) is str and bool(self.reason)),
                 "availability_mismatch")

    def canonical_form(self):
        return _form("candidates", (self.status.value, tuple(x.canonical_form() for x in self.values), self.reason))


def _candidates(values, reason, status=Availability.UNAVAILABLE):
    values = tuple(set(values))
    if values:
        return Candidates(Availability.AVAILABLE if len(values) == 1 else Availability.AMBIGUOUS, values)
    return Candidates(status, (), reason)


@dataclass(frozen=True)
class CorrelationChain(Canonical):
    execution: ExecutionReference
    air: AIRReference
    source: Candidates
    native: Candidates

    def __post_init__(self):
        _require(type(self.execution) is ExecutionReference and type(self.air) is AIRReference
                 and type(self.source) is Candidates and type(self.native) is Candidates,
                 "invalid_chain")
        _require(self.air.operation.identity.air_fingerprint == self.execution.air_fingerprint,
                 "chain_program_mismatch")
        _require(all(type(x) is SourceReference for x in self.source.values) and all(
            type(x) is NativeRegionReference and x.operation_id == self.air.operation.operation_id
            for x in self.native.values), "chain_layer_mismatch")

    def canonical_form(self):
        return _form("chain", (self.execution.canonical_form(), self.air.canonical_form(),
                               self.source.canonical_form(), self.native.canonical_form()))


@dataclass(frozen=True)
class CorrelationIndex(Canonical):
    session: SessionReference
    execution: ExecutionReference
    sidecar_fingerprint: str
    association_fingerprint: str
    source_mapping_fingerprint: str
    chains: tuple[CorrelationChain, ...]

    def __post_init__(self):
        _require(type(self.session) is SessionReference and type(self.execution) is ExecutionReference,
                 "invalid_index_binding")
        for value in (self.sidecar_fingerprint, self.association_fingerprint):
            _hash(value)
        if self.source_mapping_fingerprint:
            _hash(self.source_mapping_fingerprint)
        _require(type(self.chains) is tuple and all(type(x) is CorrelationChain and
            x.execution == self.execution for x in self.chains), "index_execution_mismatch")
        _require(tuple(x.air.operation.ordinal for x in self.chains) == tuple(range(len(self.chains))),
                 "index_operation_order_mismatch")

    def validate_session(self, session):
        _require(type(session) is DebugSession and session.reference == self.session,
                 "session_mismatch")
        _require(session.execution == self.execution, "execution_mismatch")
        _require(session.state is Lifecycle.ACTIVE and Capability.OBSERVE in session.granted,
                 "session_unavailable")

    def lookup(self, operation_id):
        found = tuple(x for x in self.chains if x.air.operation.operation_id == operation_id)
        _require(len(found) == 1, "operation_unavailable")
        return found[0]

    def canonical_form(self):
        return _form("index", (self.session.canonical_form(), self.execution.canonical_form(),
            self.sidecar_fingerprint, self.association_fingerprint, self.source_mapping_fingerprint,
            tuple(x.canonical_form() for x in self.chains)))


def build_correlation(session, verified, sidecar, association, *, required_operations,
                      expected_sidecar_fingerprint, expected_association_fingerprint,
                      source_contents=(), source_mapping=None, expected_source_mapping_fingerprint="",
                      native_mapping=None, expected_native_mapping_fingerprint="",
                      generated_content=None, native_status=Availability.UNAVAILABLE,
                      artifact_association=None, provenance_scope=None,
                      expected_artifact_association_fingerprint=""):
    """Consume owner-validated carriers and externally captured fingerprints.

    Association validation here is structural, not authentication. The embedding
    observation owner supplies execution occurrence and mapping provenance.
    Native validation does not call the existing re-emitting validator.
    """
    _require(type(session) is DebugSession and session.execution is not None, "invalid_session")
    _require(type(verified) is VerifiedAIRProgram and type(sidecar) is MetadataSidecar and
             type(association) is MetadataAssociation, "invalid_mapping_carriers")
    execution = session.execution
    _require(session.state is Lifecycle.ACTIVE and Capability.OBSERVE in session.granted,
             "session_unavailable")
    sidecar.validate(verified, source_contents, required_operations)
    _require(sidecar.fingerprint() == expected_sidecar_fingerprint, "stale_sidecar")
    _require(association.fingerprint() == expected_association_fingerprint, "stale_association")
    _require((association.sidecar_fingerprint, association.air_fingerprint,
              association.routing_fingerprint, association.entry_directive) ==
             (sidecar.fingerprint(), execution.air_fingerprint,
              execution.routing_fingerprint, execution.entry_directive), "association_execution_mismatch")
    if source_mapping is not None:
        _require(type(source_mapping) is SourceAIRMapping, "invalid_source_mapping")
        _require(source_mapping.sidecar == sidecar and source_mapping.fingerprint() ==
                 expected_source_mapping_fingerprint, "stale_source_mapping")
    else:
        _require(expected_source_mapping_fingerprint == "", "missing_source_mapping")
    artifacts = ()
    if native_mapping is not None:
        _require(type(native_mapping) is NativeSourceMapping, "invalid_native_mapping")
        _require(native_mapping.sidecar == sidecar and native_mapping.association == association,
                 "native_program_association_mismatch")
        _require(native_mapping.fingerprint() == expected_native_mapping_fingerprint,
                 "stale_native_mapping")
        _require(native_mapping.profile == execution.profile, "native_profile_mismatch")
        _require(native_mapping.source_mapping_fingerprint ==
                 (source_mapping.fingerprint() if source_mapping is not None else "UNMAPPED_SOURCE"),
                 "native_source_mapping_mismatch")
        native_mapping.generated_source.validate_content(generated_content)
        text = SourceText(native_mapping.generated_source.logical_name, generated_content.decode("utf-8"))
        for region in native_mapping.regions:
            _require(text.span(region.span.start.offset, region.span.end.offset) == region.span,
                     "invalid_generated_region")
        if artifact_association is not None:
            _require(type(artifact_association) is NativeResultAssociation and
                type(provenance_scope) is ProvenanceScope and artifact_association.fingerprint() ==
                expected_artifact_association_fingerprint and artifact_association.scope_fingerprint ==
                provenance_scope.fingerprint() and artifact_association.mapping_fingerprint ==
                native_mapping.fingerprint() and provenance_scope.native_mapping_fingerprint ==
                native_mapping.fingerprint() and provenance_scope.air_fingerprint == execution.air_fingerprint
                and provenance_scope.routing_fingerprint == execution.routing_fingerprint
                and provenance_scope.association_fingerprint == association.fingerprint()
                and provenance_scope.sidecar_fingerprint == sidecar.fingerprint()
                and provenance_scope.source_mapping_fingerprint == expected_source_mapping_fingerprint
                and provenance_scope.native_profile == execution.profile
                and provenance_scope.generated_c_fingerprint == native_mapping.generated_source.content_fingerprint,
                "artifact_association_mismatch")
            _require(execution.provenance_fingerprint == provenance_scope.fingerprint(),
                     "artifact_execution_mismatch")
            artifacts = tuple(sorted((('image', artifact_association.image_fingerprint),
                ('receipt', artifact_association.receipt_fingerprint),
                ('result', artifact_association.result_fingerprint),
                ('scope', provenance_scope.fingerprint()))))
        else:
            _require(provenance_scope is None and expected_artifact_association_fingerprint == "",
                     "missing_artifact_association")
    else:
        _require(expected_native_mapping_fingerprint == "" and generated_content is None and
                 artifact_association is None and provenance_scope is None, "missing_native_mapping")
        _require(expected_artifact_association_fingerprint == "", "missing_artifact_association")
        _require(native_status in (Availability.UNAVAILABLE, Availability.UNSUPPORTED,
                                  Availability.NOT_APPLICABLE), "invalid_native_availability")
    chains = []
    for operation in sidecar.operations:
        sources = []
        for evidence in sidecar.evidence:
            if evidence.operation_id == operation.operation_id:
                entry = sidecar.source_map.entries[evidence.source_map_index]
                sources.append(SourceReference(sidecar.sources[evidence.source_index], entry.span,
                                               (entry.air_id, entry.kind, entry.reference)))
        regions = () if native_mapping is None else tuple(NativeRegionReference(
            native_mapping.generated_source, r.span, operation.operation_id,
            native_mapping.fingerprint(), association.fingerprint(), artifacts)
            for r in native_mapping.regions if r.operation == operation)
        chains.append(CorrelationChain(execution, AIRReference(operation),
            _candidates(sources, "no_producer_source_evidence"),
            _candidates(regions, "native_mapping_not_supplied", native_status)))
    return CorrelationIndex(session.reference, execution, sidecar.fingerprint(), association.fingerprint(),
                            expected_source_mapping_fingerprint, tuple(chains))


@dataclass(frozen=True)
class LineageView(Canonical):
    label: str
    category: str
    owned_source: Candidates
    origin: Candidates

    def __post_init__(self):
        _require(type(self.label) is str and bool(self.label) and self.category in
                 ("SOURCE_BACKED", "COMPILER_SYNTHETIC", "GENERATED_CONTAINER", "METADATA_ONLY")
                 and type(self.owned_source) is Candidates and type(self.origin) is Candidates,
                 "invalid_lineage_view")
        _require(self.category == "SOURCE_BACKED" or not self.owned_source.values,
                 "synthetic_owned_source_forbidden")

    def canonical_form(self):
        return _form("lineage", (self.label, self.category, self.owned_source.canonical_form(),
                                  self.origin.canonical_form()))


def inspect_lineage(index, source_mapping, label):
    """Origin links never become owned syntax or source-step targets."""
    _require(type(source_mapping) is SourceAIRMapping and source_mapping.fingerprint() ==
             index.source_mapping_fingerprint, "lineage_mapping_mismatch")
    matches = tuple(r for r in source_mapping.lineage if r.label == label)
    _require(len(matches) == 1, "lineage_unavailable_or_ambiguous")
    record = matches[0]
    def reference(entry_index, reason):
        if entry_index < 0:
            return _candidates((), reason)
        entry = source_mapping.sidecar.source_map.entries[entry_index]
        source = next(s for s in source_mapping.sidecar.sources if s.logical_name == entry.span.source_name)
        return _candidates((SourceReference(source, entry.span,
                            (entry.air_id, entry.kind, entry.reference)),), reason)
    return LineageView(record.label, record.category,
        reference(record.source_map_index, "no_owned_physical_syntax"),
        reference(record.originating_entry_index, "origin_not_supplied"))


def correlate_inspection(index, session, inspection, operation_id):
    """Current operation is explicitly supplied; never inferred from inspected state."""
    index.validate_session(session)
    _require(type(inspection) is SessionInspection, "invalid_inspection")
    inspection.validate_session(session)
    _require(inspection.execution == index.execution, "inspection_execution_mismatch")
    return index.lookup(operation_id)


class StepMode(Enum):
    SEMANTIC_STEP = "semantic_step"
    SOURCE_STEP = "source_step"
    DIRECTIVE_STEP = "directive_step"
    WORKFLOW_STEP = "workflow_step"
    NATIVE_CORRELATION_STEP = "native_correlation_step"


@dataclass(frozen=True)
class ObservedPosition(Canonical):
    session: SessionReference
    execution: ExecutionReference
    index_fingerprint: str
    operation_id: str
    occurrence: int
    observation_reference: str
    timestamp: str | None = field(default=None, compare=False)

    def __post_init__(self):
        _require(type(self.session) is SessionReference and type(self.execution) is ExecutionReference,
                 "invalid_position_binding")
        _hash(self.index_fingerprint)
        _text(self.operation_id)
        _number(self.occurrence)
        _text(self.observation_reference)
        _require(self.timestamp is None or type(self.timestamp) is str, "invalid_timestamp")

    def canonical_form(self):
        return _form("observed-position", (self.session.canonical_form(), self.execution.canonical_form(),
            self.index_fingerprint, self.operation_id, self.occurrence, self.observation_reference))


@dataclass(frozen=True)
class KnownObservationOrder(Canonical):
    """Owner-supplied resolved order, not metadata's declaration/alternative order.

    Starts at the supplied current occurrence. A boundary entry identifies a
    confirmed directive entry at a sequence index; absence means unresolved.
    Completeness describes this evidence window, never runtime completion.
    """
    position: ObservedPosition
    operations: tuple[str, ...]
    evidence_reference: str
    complete: bool = False
    directive_boundaries: tuple[tuple[int, str, str], ...] = ()

    def __post_init__(self):
        _require(type(self.position) is ObservedPosition and type(self.operations) is tuple and
                 bool(self.operations) and self.operations[0] == self.position.operation_id,
                 "invalid_known_order")
        for op in self.operations:
            _text(op)
        _text(self.evidence_reference)
        _require(type(self.complete) is bool and type(self.directive_boundaries) is tuple,
                 "invalid_known_order")
        _require(tuple(sorted(self.directive_boundaries)) == self.directive_boundaries and
                 len({x[0] for x in self.directive_boundaries}) == len(self.directive_boundaries),
                 "ambiguous_directive_boundary")
        for offset, directive, evidence in self.directive_boundaries:
            _number(offset)
            _require(0 < offset < len(self.operations), "invalid_directive_boundary")
            _text(directive)
            _text(evidence)

    def canonical_form(self):
        return _form("known-observation-order", (self.position.canonical_form(), self.operations,
            self.evidence_reference, self.complete, self.directive_boundaries))


@dataclass(frozen=True)
class StepTarget(Canonical):
    session: SessionReference
    execution: ExecutionReference
    index_fingerprint: str
    mode: StepMode
    chain: CorrelationChain
    ordering_key: tuple[int, int]
    evidence_reference: str

    def __post_init__(self):
        _require(type(self.session) is SessionReference and type(self.execution) is ExecutionReference
                 and type(self.mode) is StepMode and type(self.chain) is CorrelationChain and
                 self.chain.execution == self.execution, "invalid_target_binding")
        _hash(self.index_fingerprint)
        _require(type(self.ordering_key) is tuple and len(self.ordering_key) == 2, "invalid_target_order")
        for value in self.ordering_key:
            _number(value)
        _text(self.evidence_reference)

    def validate(self, index, session):
        index.validate_session(session)
        _require(self.session == index.session and self.execution == index.execution and
                 self.index_fingerprint == index.fingerprint(), "target_binding_mismatch")
        _require(index.lookup(self.chain.air.operation.operation_id) == self.chain, "target_chain_mismatch")

    def canonical_form(self):
        return _form("step-target", (self.session.canonical_form(), self.execution.canonical_form(),
            self.index_fingerprint, self.mode.value, self.chain.canonical_form(), self.ordering_key,
            self.evidence_reference))


@dataclass(frozen=True)
class StepPlan(Canonical):
    position: ObservedPosition
    mode: StepMode
    status: Availability
    targets: tuple[StepTarget, ...]
    reason: str

    def __post_init__(self):
        _require(type(self.position) is ObservedPosition and type(self.mode) is StepMode and
            type(self.status) is Availability and type(self.targets) is tuple and all(
                type(x) is StepTarget and x.mode is self.mode and x.session == self.position.session and
                x.execution == self.position.execution and x.index_fingerprint == self.position.index_fingerprint
                for x in self.targets) and type(self.reason) is str, "invalid_plan")
        _require(bool(self.targets) == (self.status in (Availability.AVAILABLE, Availability.AMBIGUOUS)),
                 "plan_availability_mismatch")

    def canonical_form(self):
        return _form("step-plan", (self.position.canonical_form(), self.mode.value, self.status.value,
            tuple(x.canonical_form() for x in self.targets), self.reason))


def plan_next(index, session, position, mode, known_order=None):
    index.validate_session(session)
    _require(type(position) is ObservedPosition and position.session == index.session and
        position.execution == index.execution and position.index_fingerprint == index.fingerprint(),
        "position_binding_mismatch")
    _require(type(mode) is StepMode, "unsupported_step_mode")
    current = index.lookup(position.operation_id)

    def missing(status, reason):
        return StepPlan(position, mode, status, (), reason)

    def target(chain, offset, evidence, status=Availability.AVAILABLE, reason=""):
        value = StepTarget(index.session, index.execution, index.fingerprint(), mode, chain,
                           (position.occurrence + offset, chain.air.operation.ordinal), evidence)
        value.validate(index, session)
        return StepPlan(position, mode, status, (value,), reason)

    if mode is StepMode.WORKFLOW_STEP:
        return missing(Availability.UNSUPPORTED, "workflow_order_not_exposed")
    if mode is StepMode.NATIVE_CORRELATION_STEP:
        if not current.native.values:
            return missing(current.native.status, current.native.reason)
        return target(current, 0, position.observation_reference, current.native.status,
                      "generated_region_only_no_machine_instruction_step")
    if known_order is None:
        return missing(Availability.UNAVAILABLE, "needs_runtime_observation")
    _require(type(known_order) is KnownObservationOrder and known_order.position == position,
             "known_order_binding_mismatch")
    ordered = tuple(index.lookup(op) for op in known_order.operations)
    for offset, directive, evidence in known_order.directive_boundaries:
        _require(ordered[offset].air.directive == directive, "directive_boundary_mismatch")
    if mode is StepMode.DIRECTIVE_STEP:
        if not known_order.directive_boundaries:
            return missing(Availability.UNAVAILABLE, "needs_observed_directive_boundary")
        offset, _, evidence = known_order.directive_boundaries[0]
        return target(ordered[offset], offset, evidence)
    if mode is StepMode.SOURCE_STEP and current.source.status is not Availability.AVAILABLE:
        return missing(Availability.UNAVAILABLE, "current_source_unresolved_use_semantic_mode")
    for offset, chain in enumerate(ordered[1:], 1):
        if mode is StepMode.SEMANTIC_STEP:
            return target(chain, offset, known_order.evidence_reference)
        if chain.source.status is Availability.AMBIGUOUS:
            return target(chain, offset, known_order.evidence_reference, Availability.AMBIGUOUS,
                          "all_source_candidates_preserved")
        if chain.source.status is Availability.AVAILABLE and chain.source.values[0].location_key() != \
                current.source.values[0].location_key():
            return target(chain, offset, known_order.evidence_reference,
                          reason="same_span_collapsed_unmapped_operations_skipped")
    return missing(Availability.NOT_APPLICABLE if known_order.complete else Availability.UNAVAILABLE,
                   "no_more_targets_in_supplied_window" if known_order.complete else "needs_runtime_observation")
