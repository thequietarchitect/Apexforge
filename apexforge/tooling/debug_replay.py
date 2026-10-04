"""P13.6 pure navigation/comparison of authorized retained observations.

No execution, reconstruction execution, evidence production, live control, policy
evaluation, filesystem access, or attribution. Producer identity remains owned
by P12; comparison projects declared evidence domains rather than one verdict.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json

from tooling.debug_evidence import EvidenceView, EvidenceNode, EvidenceKind as K, Relation
from tooling.debug_inspection import (InspectionSnapshot, InspectionField, Availability as A,
                                      available, missing)
from tooling.debug_session import DebugSession
from tooling.trace_integration import ManagedContextIdentity
from apexforge.native_backend.native_execution_contract import PROFILE

SCHEMA = "apexforge.debug-replay/v1"


class ReplayError(ValueError):
    pass


def _require(condition, code):
    if not condition:
        raise ReplayError(code)


def _form(kind, value):
    return json.dumps((SCHEMA, kind, value), ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _digest(value):
    return sha256(value.encode("utf-8")).hexdigest().upper()


class Canonical:
    def fingerprint(self):
        return _digest(self.canonical_form())


class OrderingDomain(Enum):
    SEMANTIC_ORDER = "semantic_order"
    TRACE_FAMILY_ORDER = "trace_family_order"
    TRACE_STREAM_ORDER = "trace_stream_order"
    DEBUGGER_EVENT_ORDER = "debugger_event_order"
    CAUSAL_ORDER = "causal_order"
    SOURCE_ORDER = "source_order"
    NATIVE_CORRELATION_ORDER = "native_correlation_order"


class ReplayMode(Enum):
    LIVE_SESSION_REPLAY = "live_session_replay"
    RETAINED_EVIDENCE_REPLAY = "retained_evidence_replay"


class ReplayAvailability(Enum):
    COMPLETE_RETAINED = "complete_retained"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED_MODE = "unsupported_mode"
    AMBIGUOUS_REFERENCE = "ambiguous_reference"
    REDACTED = "redacted"


@dataclass(frozen=True)
class ReplayHistory(Canonical):
    evidence: EvidenceView
    inspection: InspectionSnapshot | None = field(default=None, repr=False)
    timestamp: str | None = field(default=None, compare=False, repr=False)
    volatile: tuple[tuple[str, str | int | float], ...] = field(default=(), compare=False, repr=False)

    def __post_init__(self):
        _require(type(self.evidence) is EvidenceView and (self.inspection is None or
            type(self.inspection) is InspectionSnapshot and
            self.inspection.execution == self.evidence.binding.execution), "history_execution_mismatch")
        if self.inspection is not None:
            _require(self.evidence.redacted or not any(e.observed_value.status is A.REDACTED
                for e in self.inspection.state.entries), "mixed_redaction_not_safe")
        _require(self.timestamp is None or type(self.timestamp) is str, "invalid_observation_timestamp")
        _require(type(self.volatile) is tuple and all(type(p) is tuple and len(p) == 2 and
            p[0] in ("pid", "handle_count", "memory_address", "elapsed_duration", "working_set", "temporary_root",
                     "transport_id") and type(p[1]) in (str, int, float) for p in self.volatile), "invalid_volatile_fields")
        _require(len({p[0] for p in self.volatile}) == len(self.volatile), "duplicate_volatile_field")
        # Reuse P13.3's primitive/finite validation, never include these in identity.
        available(self.volatile)
        object.__setattr__(self, "volatile", tuple(sorted(self.volatile)))

    def canonical_form(self):
        snapshot = "not_supplied" if self.inspection is None else (
            "redacted" if self.evidence.redacted else self.inspection.canonical_form())
        return _form("history", (self.evidence.canonical_form(), snapshot))


def capture_history(session, evidence, *, inspection=None, timestamp=None, volatile=()):
    _require(type(evidence) is EvidenceView, "invalid_evidence_history")
    evidence.binding.validate_session(session)
    if inspection is not None:
        _require(type(inspection) is InspectionSnapshot, "invalid_inspection_history")
        # Navigation verifies result identity and retention association without mutation.
        if inspection.result.status is A.AVAILABLE and not evidence.redacted:
            from tooling.debug_inspection import bind_inspection
            evidence.result_evidence(session, bind_inspection(inspection, session))
    return ReplayHistory(evidence, inspection, timestamp, volatile)


@dataclass(frozen=True)
class ReplayRecord(Canonical):
    sequence: int
    domain: OrderingDomain
    logical_key: tuple
    evidence: EvidenceNode
    inspection_reference: InspectionField

    def __post_init__(self):
        _require(type(self.sequence) is int and self.sequence >= 0 and type(self.domain) is OrderingDomain
            and type(self.logical_key) is tuple and type(self.evidence) is EvidenceNode and
            type(self.inspection_reference) is InspectionField, "invalid_replay_record")
        available(self.logical_key)

    def canonical_form(self):
        return _form("record", (self.sequence, self.domain.value, self.logical_key,
                               self.evidence.canonical_form(), self.inspection_reference.record()))


@dataclass(frozen=True)
class ReplayTimeline(Canonical):
    history: ReplayHistory = field(repr=False)
    domain: OrderingDomain
    family: str
    mode: ReplayMode
    availability: ReplayAvailability
    records: tuple[ReplayRecord, ...]
    reason: str

    def __post_init__(self):
        _require(type(self.history) is ReplayHistory and type(self.domain) is OrderingDomain and
            type(self.family) is str and type(self.mode) is ReplayMode and
            type(self.availability) is ReplayAvailability and type(self.records) is tuple and
            all(type(r) is ReplayRecord and r.domain is self.domain for r in self.records), "invalid_timeline")
        _require(tuple(r.sequence for r in self.records) == tuple(range(len(self.records))),
                 "invalid_replay_sequence")

    def canonical_form(self):
        return _form("timeline", (self.history.fingerprint(), self.domain.value, self.family, self.mode.value,
            self.availability.value, tuple(r.canonical_form() for r in self.records), self.reason))

    def validate_access(self, session):
        if self.mode is ReplayMode.LIVE_SESSION_REPLAY:
            self.history.evidence.binding.validate_session(session)


def build_replay(history, domain=OrderingDomain.TRACE_STREAM_ORDER, *, family="",
                 mode=ReplayMode.RETAINED_EVIDENCE_REPLAY, session=None):
    _require(type(history) is ReplayHistory and type(domain) is OrderingDomain and
             type(mode) is ReplayMode and type(family) is str, "invalid_replay_request")
    if mode is ReplayMode.LIVE_SESSION_REPLAY:
        history.evidence.binding.validate_session(session)
    view = history.evidence
    if domain not in (OrderingDomain.TRACE_STREAM_ORDER, OrderingDomain.TRACE_FAMILY_ORDER):
        return ReplayTimeline(history, domain, family, mode, ReplayAvailability.UNSUPPORTED_MODE, (),
                              "ordering_contract_not_supplied")
    if domain is OrderingDomain.TRACE_FAMILY_ORDER:
        _require(bool(family), "trace_family_required")
        rows = tuple((ordinal, (family_id, ordinal), node) for family_id, scope, ordinal, node
                     in view.family_order if family_id == family)
    else:
        _require(family == "", "stream_is_not_family_order")
        rows = tuple((parent, (parent, family_id, ordinal), node) for parent, family_id, ordinal, node
                     in view.interleaving)
    if view.redacted:
        status, reason = ReplayAvailability.REDACTED, "redacted_observation_shape_only"
        snapshot = missing("inspection_redacted", A.REDACTED)
    else:
        incomplete = view.coverage.status is not A.AVAILABLE or (
            view.coverage.value != ("native_evidence_only",) and bool(view.coverage.value))
        status = ReplayAvailability.PARTIAL if incomplete else ReplayAvailability.COMPLETE_RETAINED
        reason = "supplied_projection_only_not_universal_execution_coverage"
        snapshot = missing("inspection_not_supplied") if history.inspection is None else available(
            history.inspection.fingerprint())
    records = tuple(ReplayRecord(i, domain, key, view.graph.node(node), snapshot)
                    for i, (_, key, node) in enumerate(rows))
    if not records and not view.redacted:
        status, reason = ReplayAvailability.UNAVAILABLE, "requested_observation_order_unavailable"
    return ReplayTimeline(history, domain, family, mode, status, records, reason)


@dataclass(frozen=True)
class ReplayPosition:
    status: ReplayAvailability
    records: tuple[ReplayRecord, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class ReplayCursor:
    timeline_fingerprint: str
    sequence: int

    @classmethod
    def first(cls, timeline, session=None):
        timeline.validate_access(session)
        _require(bool(timeline.records), "replay_position_unavailable")
        return cls(timeline.fingerprint(), 0)

    @classmethod
    def last(cls, timeline, session=None):
        timeline.validate_access(session)
        _require(bool(timeline.records), "replay_position_unavailable")
        return cls(timeline.fingerprint(), len(timeline.records) - 1)

    def seek(self, timeline, sequence, session=None):
        self.current(timeline, session)
        _require(type(sequence) is int and 0 <= sequence < len(timeline.records), "invalid_replay_seek")
        return ReplayCursor(self.timeline_fingerprint, sequence)

    def current(self, timeline, session=None):
        timeline.validate_access(session)
        _require(self.timeline_fingerprint == timeline.fingerprint() and type(self.sequence) is int and
                 0 <= self.sequence < len(timeline.records), "stale_replay_cursor")
        return timeline.records[self.sequence]

    def next(self, timeline, session=None):
        return self.seek(timeline, min(self.sequence + 1, len(timeline.records) - 1), session)

    def previous(self, timeline, session=None):
        return self.seek(timeline, max(self.sequence - 1, 0), session)


def seek_reference(timeline, reference, session=None):
    timeline.validate_access(session)
    _require(type(reference) is str and bool(reference), "invalid_replay_reference")
    graph = timeline.history.evidence.graph
    records = tuple(r for r in timeline.records if reference in
                    (r.evidence.node_id, r.evidence.reference.producer_identity,
                     r.evidence.reference.air_fingerprint) or any(
        e.source == r.evidence.node_id and e.relation is Relation.MAPS_TO and
        graph.node(e.target).reference.kind is K.AIR_OPERATION and
        graph.node(e.target).reference.producer_identity == reference for e in graph.edges))
    if not records:
        return ReplayPosition(ReplayAvailability.UNAVAILABLE, (), "reference_not_recorded")
    return ReplayPosition(ReplayAvailability.AMBIGUOUS_REFERENCE if len(records) > 1 else
                          timeline.availability, records)


class Reconstructability(Enum):
    INSUFFICIENT_INPUT_EVIDENCE = "insufficient_input_evidence"
    TOOLCHAIN_CONDITIONED = "toolchain_conditioned"
    UNSUPPORTED_PROFILE = "unsupported_profile"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class ReconstructionDescriptor(Canonical):
    status: Reconstructability
    inputs: InspectionField
    conditions: InspectionField
    expected_evidence: InspectionField
    reason: str

    def canonical_form(self):
        return _form("reconstruction-description", (self.status.value, self.inputs.record(),
            self.conditions.record(), self.expected_evidence.record(), self.reason))


def _nodes(history, kinds):
    return tuple(n for n in history.evidence.graph.nodes if n.reference.kind in kinds)


def _scope(history):
    expected = history.evidence.binding.execution.provenance_fingerprint
    found = tuple(n for n in _nodes(history, (K.SCOPE,)) if n.reference.producer_identity == expected)
    return dict(found[0].payload.value) if len(found) == 1 and not history.evidence.redacted else None


def describe_reconstruction(history, *, managed_context=None, native_receipt_json=None):
    _require(type(history) is ReplayHistory, "invalid_reconstruction_history")
    absent = missing("canonical_input_material_not_retained")
    if history.evidence.redacted:
        hidden = missing("reconstruction_evidence_redacted", A.REDACTED)
        return ReconstructionDescriptor(Reconstructability.INSUFFICIENT_INPUT_EVIDENCE,
                                        hidden, hidden, hidden, "redacted_inputs_not_reconstructed")
    execution = history.evidence.binding.execution
    scope = _scope(history)
    expected = available(tuple(sorted((n.reference.kind.value, n.reference.producer_identity) for n in
        _nodes(history, (K.RESULT, K.RESULT_ASSOCIATION, K.BUILD_RECEIPT, K.ARTIFACT, K.TRACE_FAMILY)))))
    if execution.profile not in (PROFILE, "canonical.runtime/v1"):
        return ReconstructionDescriptor(Reconstructability.UNSUPPORTED_PROFILE, absent, absent,
                                        expected, "compatible_contract_not_established")
    if scope is None:
        return ReconstructionDescriptor(Reconstructability.INSUFFICIENT_INPUT_EVIDENCE, absent, absent,
                                        expected, "retained_input_scope_unavailable")
    base = (execution.air_fingerprint, execution.routing_fingerprint, execution.entry_directive,
            execution.profile, scope["input_fingerprint"], scope["source_mapping_fingerprint"])
    if execution.profile == PROFILE:
        _require(managed_context is None, "wrong_reconstruction_input_kind")
        if native_receipt_json is None:
            return ReconstructionDescriptor(Reconstructability.INSUFFICIENT_INPUT_EVIDENCE, available(base), absent,
                                            expected, "toolchain_receipt_not_supplied")
        receipts = _nodes(history, (K.BUILD_RECEIPT,))
        _require(type(native_receipt_json) is str and len(receipts) == 1 and
            _digest(native_receipt_json) == receipts[0].reference.producer_identity, "reconstruction_receipt_mismatch")
        try:
            receipt = json.loads(native_receipt_json)
        except ValueError:
            raise ReplayError("invalid_reconstruction_receipt") from None
        _require((receipt["air"], receipt["routing"], receipt["entry"], receipt["profile"], receipt["source"]) ==
            (execution.air_fingerprint, execution.routing_fingerprint, execution.entry_directive,
             execution.profile, scope["generated_c_fingerprint"]), "reconstruction_contract_mismatch")
        return ReconstructionDescriptor(Reconstructability.TOOLCHAIN_CONDITIONED, available(base),
            available((tuple(sorted(receipt["toolchain"].items())), tuple(receipt["options"]),
                       "tested_frozen_profile_toolchain_conditions_only")), expected,
            "requires_original_canonical_air_and_compatible_captured_tools_no_execution")
    _require(native_receipt_json is None, "wrong_reconstruction_input_kind")
    if managed_context is None:
        return ReconstructionDescriptor(Reconstructability.INSUFFICIENT_INPUT_EVIDENCE, available(base), absent,
                                        expected, "initial_state_policy_configuration_not_supplied")
    _require(type(managed_context) is ManagedContextIdentity and managed_context.fingerprint() ==
        scope["input_fingerprint"] and any(n.reference.producer_identity == managed_context.plan_fingerprint
        for n in _nodes(history, (K.PLAN,))), "managed_reconstruction_context_mismatch")
    return ReconstructionDescriptor(Reconstructability.INSUFFICIENT_INPUT_EVIDENCE,
        available(base + (managed_context.state_fingerprint, managed_context.policy_fingerprint,
                          managed_context.configuration_fingerprint)),
        available(("existing_managed_context_capture/v1",)), expected,
        "input_hashes_are_not_original_state_policy_material_no_universal_reconstruction")


class ComparisonDomain(Enum):
    INPUT = "input"
    AIR = "air"
    STATE = "state"
    DIRECTIVE = "directive"
    AUTHORITY = "authority_evidence"
    CAUSAL = "causal_evidence"
    RESULT = "result"
    TRACE = "trace"
    MAPPING = "mapping"
    PROVENANCE = "provenance"
    NATIVE_ARTIFACT = "native_artifact"
    BUILD_RECEIPT = "build_receipt"


class Divergence(Enum):
    IDENTICAL = "identical"
    INPUT_DIVERGENCE = "input_divergence"
    AIR_DIVERGENCE = "air_divergence"
    STATE_DIVERGENCE = "state_divergence"
    DIRECTIVE_DIVERGENCE = "directive_divergence"
    AUTHORITY_EVIDENCE_DIVERGENCE = "authority_evidence_divergence"
    CAUSAL_EVIDENCE_DIVERGENCE = "causal_evidence_divergence"
    RESULT_DIVERGENCE = "result_divergence"
    TRACE_DIVERGENCE = "trace_divergence"
    MAPPING_DIVERGENCE = "mapping_divergence"
    PROVENANCE_DIVERGENCE = "provenance_divergence"
    NATIVE_ARTIFACT_DIVERGENCE = "native_artifact_divergence"
    BUILD_RECEIPT_DIVERGENCE = "build_receipt_divergence"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    REDACTED_COMPARISON_UNAVAILABLE = "redacted_comparison_unavailable"
    NOT_APPLICABLE = "not_applicable"
    VOLATILE_ONLY_DIVERGENCE = "volatile_only_divergence"


@dataclass(frozen=True)
class DomainComparison:
    domain: ComparisonDomain
    classification: Divergence
    first_difference: int | None
    ordering: OrderingDomain | None
    supporting_references: tuple[tuple[str, ...], tuple[str, ...]]

    def record(self):
        return (self.domain.value, self.classification.value, self.first_difference,
                None if self.ordering is None else self.ordering.value, self.supporting_references)


@dataclass(frozen=True)
class ComparisonResult(Canonical):
    left_history: str
    right_history: str
    domains: tuple[DomainComparison, ...]
    volatile_differences: tuple[str, ...]
    volatile_classification: Divergence | None

    def canonical_form(self):
        return _form("comparison", (self.left_history, self.right_history,
            tuple(d.record() for d in self.domains), self.volatile_differences,
            None if self.volatile_classification is None else self.volatile_classification.value))


def _trace_content(history, node):
    payload = node.payload.record()
    if node.reference.kind is K.AUTHORITY and node.payload.status is A.AVAILABLE:
        # inspect_authority's retained ID is a binding/provenance reference, not
        # the recorded check outcome. Compare that reference in PROVENANCE.
        data = node.payload.value
        payload = (data[0], data[1][1:], data[2])
    operations = tuple(sorted(history.evidence.graph.node(e.target).reference.producer_identity
        for e in history.evidence.graph.edges if e.source == node.node_id and e.relation is Relation.MAPS_TO))
    return (node.reference.kind.value, node.reference.producer_schema, payload, operations)


def _observation(history, domain, ordering, family):
    if history.evidence.redacted:
        return missing("redacted_comparison_unavailable", A.REDACTED), ()
    snapshot = history.inspection
    scope = _scope(history)
    if domain is ComparisonDomain.AIR:
        return available((history.evidence.binding.execution.air_fingerprint,)), ()
    if domain is ComparisonDomain.INPUT:
        return (missing("input_scope_unavailable") if scope is None else
                available((scope["input_fingerprint"],))), ()
    if domain in (ComparisonDomain.STATE, ComparisonDomain.RESULT, ComparisonDomain.DIRECTIVE):
        if snapshot is None:
            return missing("inspection_not_supplied"), ()
        if domain is ComparisonDomain.STATE:
            if snapshot.state.capture.status is not A.AVAILABLE:
                return missing("state_capture_unavailable"), ()
            return available(tuple((e.key, e.declared_type.record(), e.observed_value.record())
                for e in snapshot.state.entries)), ()
        value = snapshot.result if domain is ComparisonDomain.RESULT else snapshot.directive
        if value.status is not A.AVAILABLE:
            return value, ()
        values = value.value[:3] if domain is ComparisonDomain.RESULT else value.value[:7]
        return available(values), tuple(n.node_id for n in _nodes(history, (K.RESULT,)))
    if domain is ComparisonDomain.TRACE:
        replay = build_replay(history, ordering, family=family)
        if replay.availability in (ReplayAvailability.UNAVAILABLE, ReplayAvailability.UNSUPPORTED_MODE):
            return missing(replay.reason), ()
        if replay.availability is ReplayAvailability.PARTIAL:
            return missing("partial_trace_comparison_insufficient"), tuple(r.evidence.node_id for r in replay.records)
        return available(tuple((r.logical_key, _trace_content(history, r.evidence)) for r in replay.records)), \
            tuple(r.evidence.node_id for r in replay.records)
    if domain in (ComparisonDomain.AUTHORITY, ComparisonDomain.CAUSAL):
        wanted = "authority-observation" if domain is ComparisonDomain.AUTHORITY else "causal-selection"
        values = tuple(history.evidence.graph.node(node) for f, scope_id, ordinal, node in
                       history.evidence.family_order if f == wanted)
        exists = any(n.payload.value[0] == wanted for n in _nodes(history, (K.TRACE_FAMILY,)))
        return (available(tuple(_trace_content(history, n) for n in values)) if exists else
                missing("trace_family_not_supplied")), tuple(n.node_id for n in values)
    kinds = {
        ComparisonDomain.MAPPING: (K.SOURCE, K.SOURCE_MAPPING, K.AIR_MAPPING, K.AIR_OPERATION, K.NATIVE_MAPPING, K.NATIVE_REGION),
        ComparisonDomain.PROVENANCE: (K.SCOPE, K.PLAN, K.RESULT_ASSOCIATION, K.TRACE_FAMILY, K.TRACE, K.AUTHORITY, K.TAM),
        ComparisonDomain.NATIVE_ARTIFACT: (K.ARTIFACT,),
        ComparisonDomain.BUILD_RECEIPT: (K.BUILD_RECEIPT,),
    }[domain]
    nodes = _nodes(history, kinds)
    if not nodes:
        status = A.NOT_APPLICABLE if domain is ComparisonDomain.NATIVE_ARTIFACT and \
            history.evidence.binding.execution.profile == "canonical.runtime/v1" else A.UNAVAILABLE
        return missing("evidence_domain_not_supplied", status), ()
    rows = tuple(sorted((n.reference.kind.value, n.reference.producer_identity,
                         n.reference.scope_fingerprint) for n in nodes))
    return available(rows), tuple(n.node_id for n in nodes)


def compare_histories(left, right, domains, *, ordering=OrderingDomain.TRACE_STREAM_ORDER, family=""):
    _require(type(left) is ReplayHistory and type(right) is ReplayHistory and type(domains) is tuple
        and bool(domains) and all(type(d) is ComparisonDomain for d in domains) and
        len(set(domains)) == len(domains) and type(ordering) is OrderingDomain, "invalid_comparison")
    results = []
    differences = {d: Divergence(d.value + "_divergence") for d in ComparisonDomain}
    for domain in sorted(domains, key=lambda d: d.value):
        a, refs_a = _observation(left, domain, ordering, family)
        b, refs_b = _observation(right, domain, ordering, family)
        first = None
        if A.REDACTED in (a.status, b.status):
            classification, refs_a, refs_b = Divergence.REDACTED_COMPARISON_UNAVAILABLE, (), ()
        elif a.status is A.NOT_APPLICABLE and b.status is A.NOT_APPLICABLE:
            classification = Divergence.NOT_APPLICABLE
        elif a.status is not A.AVAILABLE or b.status is not A.AVAILABLE:
            classification = Divergence.INSUFFICIENT_EVIDENCE
        elif a.record() == b.record():
            classification = Divergence.IDENTICAL
        else:
            classification = differences[domain]
            for index in range(max(len(a.value), len(b.value))):
                if index >= min(len(a.value), len(b.value)) or a.value[index] != b.value[index]:
                    first = index
                    break
        results.append(DomainComparison(domain, classification, first,
            ordering if domain is ComparisonDomain.TRACE else None, (refs_a, refs_b)))
    def volatility(history):
        binding = history.evidence.binding
        return dict(history.volatile, session_identity=binding.session.session_id,
            execution_identity=binding.execution.execution_id, timestamp=history.timestamp,
            evidence_timestamp=history.evidence.timestamp,
            inspection_timestamp=None if history.inspection is None else history.inspection.timestamp)
    va, vb = volatility(left), volatility(right)
    changed = tuple(sorted(k for k in set(va) | set(vb) if va.get(k) != vb.get(k)))
    volatile_only = bool(changed) and all(r.classification in (Divergence.IDENTICAL, Divergence.NOT_APPLICABLE)
                                         for r in results)
    return ComparisonResult(left.fingerprint(), right.fingerprint(), tuple(results), changed,
                            Divergence.VOLATILE_ONLY_DIVERGENCE if volatile_only else None)
