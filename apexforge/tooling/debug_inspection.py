"""P13.3 immutable projections of supplied canonical evidence; no execution.

Inputs must be validated by their existing producer/embedding owner. This module
checks cross-carrier bindings and projects values; it never executes, routes,
evaluates authority, constructs missing state, or retains runtime objects.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
import math

from air.model import AIRProgram, StateDefinition, VerifiedAIRProgram
from authority.model import Principal, AuthorityCheck
from runtime.state import StateSnapshot, StateCell
from runtime.call_stack import CallFrame
from runtime.diagnostics import Diagnostic
from type_system.model import ApexType
from apexforge.native_backend.payload import CanonicalExecutionPayload
from apexforge.native_backend.value import CanonicalExecutionValue
from apexforge.native_backend.source_mapping import NativeSourceMapping
from apexforge.native_backend.lowering_input import build_verified_air_lowering_input
from tooling.debug_metadata import StateLocator
from tooling.source_air_mapping import SourceAIRMapping
from tooling.trace_retention import RetainedRecord, TraceFamily
from tooling.trace_integration import PlanMetadata, ManagedRetention, NativeRetention, managed_result_fingerprint
from tooling.debug_session import DebugSession, SessionReference, ExecutionReference, Lifecycle, Capability

SCHEMA = "apexforge.debug-inspection/v1"


class InspectionError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)  # Never interpolate a supplied sensitive value.


def _require(condition, code):
    if not condition:
        raise InspectionError(code)


def _text(value):
    _require(type(value) is str and bool(value), "invalid_reference")


def _plain(value):
    if type(value) is tuple:
        if (len(value) == 3 and type(value[0]) is str and value[0] in
                ("unavailable", "unsupported", "not_applicable", "redacted")
                and value[1] is None and type(value[2]) is str and value[2]):
            return  # Exact nested missing-field record; not an ambiguous null.
        for item in value:
            _plain(item)
    else:
        _require(type(value) in (str, int, bool, float), "mutable_or_opaque_payload")
        if type(value) is float:
            _require(math.isfinite(value), "nonfinite_payload")


def _form(kind, record):
    return json.dumps((SCHEMA, kind, record), ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


class Availability(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    NOT_APPLICABLE = "not_applicable"
    REDACTED = "redacted"


@dataclass(frozen=True)
class InspectionField:
    """Exact immutable primitives/tuples only; missing status is never a value."""
    status: Availability
    value: object = None
    reason: str = ""

    def __post_init__(self):
        _require(type(self.status) is Availability, "invalid_availability")
        if self.status is Availability.AVAILABLE:
            _require(self.reason == "", "invalid_availability")
            _plain(self.value)
        else:
            _require(self.value is None, "missing_field_has_payload")
            _text(self.reason)

    def record(self):
        # A missing field's None is unambiguous alongside its explicit status.
        return (self.status.value, self.value, self.reason)


def available(value):
    return InspectionField(Availability.AVAILABLE, value)


def missing(reason, status=Availability.UNAVAILABLE):
    return InspectionField(status, reason=reason)


def _value(value):
    if type(value) not in (bool, int, str, float):
        return missing("opaque_value_not_projectable", Availability.UNSUPPORTED)
    if type(value) is float and not math.isfinite(value):
        return missing("nonfinite_value_not_projectable", Availability.UNSUPPORTED)
    return available((type(value).__name__, value))


def _type_record(value):
    _require(type(value) is ApexType, "invalid_declared_type")
    return (value.name, tuple(_type_record(v) for v in value.arguments))


@dataclass(frozen=True)
class StateEntry:
    key: str
    declared_type: InspectionField
    observed_value: InspectionField
    source_air: InspectionField

    def __post_init__(self):
        _text(self.key)
        _require(all(type(v) is InspectionField for v in
                     (self.declared_type, self.observed_value, self.source_air)), "invalid_state_entry")

    def record(self):
        return (self.key, self.declared_type.record(), self.observed_value.record(), self.source_air.record())


@dataclass(frozen=True)
class StateView:
    execution: ExecutionReference = field(repr=False)
    entries: tuple[StateEntry, ...]
    capture: InspectionField

    def __post_init__(self):
        _require(type(self.execution) is ExecutionReference and type(self.capture) is InspectionField,
                 "invalid_state_view")
        _require(type(self.entries) is tuple and all(type(e) is StateEntry for e in self.entries),
                 "invalid_state_entries")
        keys = tuple(e.key for e in self.entries)
        _require(keys == tuple(sorted(set(keys))), "noncanonical_state_order")

    def record(self):
        return (self.capture.record(), tuple(e.record() for e in self.entries))

    def canonical_form(self):
        # Provenance may contain a value-derived hash; it is a binding, not value
        # projection material. Keep it out of client-visible state-view identity.
        return _form("state-view", ((self.execution.air_fingerprint,
            self.execution.routing_fingerprint, self.execution.entry_directive,
            self.execution.profile), self.record()))


def _span(span):
    return (span.source_name, (span.start.line, span.start.column, span.start.offset),
            (span.end.line, span.end.column, span.end.offset))


def inspect_mapping(execution, mapping):
    """Project existing correspondence; no emission, re-admission or inference."""
    _require(type(execution) is ExecutionReference, "invalid_execution")
    if mapping is None:
        return missing("mapping_not_supplied")
    _require(type(mapping) in (SourceAIRMapping, NativeSourceMapping), "unsupported_mapping")
    sidecar = mapping.sidecar
    _require(sidecar.air_fingerprint == execution.air_fingerprint, "mapping_execution_mismatch")
    native = type(mapping) is NativeSourceMapping
    if native:
        _require(mapping.association.routing_fingerprint == execution.routing_fingerprint and
                 mapping.association.entry_directive == execution.entry_directive and
                 mapping.profile == execution.profile, "mapping_execution_mismatch")
    rows = []
    for op in sidecar.operations:
        links = tuple(e for e in sidecar.evidence if e.operation_id == op.operation_id)
        sources = available(tuple((sidecar.sources[e.source_index].canonical_identity(),
            _span(sidecar.source_map.entries[e.source_map_index].span)) for e in links)) if links else missing("UNMAPPED_SOURCE")
        regions = tuple(r for r in mapping.regions if r.operation == op) if native else ()
        generated = available(tuple((mapping.generated_source.canonical_identity(), _span(r.span))
                                    for r in regions)) if regions else missing("generated_native_region_not_supplied")
        rows.append((op.operation_id, op.identity.canonical_identity(), sources.record(),
                     generated.record(), missing("machine_address_not_established", Availability.UNSUPPORTED).record()))
    return available((mapping.fingerprint(), tuple(rows)))


def inspect_state(execution, program, snapshot=None, *, mapping=None, redacted_keys=()):
    """Copy already-produced values. Missing cells do not use AIR initializers."""
    _require(type(execution) is ExecutionReference and type(program) is AIRProgram, "invalid_state_input")
    _require(build_verified_air_lowering_input(VerifiedAIRProgram(program)).transport_fingerprint ==
             execution.air_fingerprint, "program_execution_mismatch")
    _require(type(redacted_keys) is tuple and all(type(k) is str for k in redacted_keys)
             and len(set(redacted_keys)) == len(redacted_keys), "invalid_redaction_selection")
    _require(all(type(s) is StateDefinition for s in program.states), "invalid_state_definitions")
    declarations = {s.id: s for s in program.states}
    _require(len(declarations) == len(program.states), "ambiguous_state_identity")
    if snapshot is None:
        observed = {}
        capture = missing("state_snapshot_not_supplied")
    elif type(snapshot) is StateSnapshot:
        _require(type(snapshot.cells) is tuple and all(type(c) is StateCell for c in snapshot.cells),
                 "invalid_state_snapshot")
        observed = {c.key: _value(c.value) for c in snapshot.cells if c.key not in redacted_keys}
        for c in snapshot.cells:
            if c.key in redacted_keys:
                observed[c.key] = missing("value_redacted", Availability.REDACTED)
        capture = available("runtime.StateSnapshot")
    elif type(snapshot) is CanonicalExecutionPayload:
        _require(type(snapshot.values) is tuple and all(type(v) is CanonicalExecutionValue for v in snapshot.values),
                 "invalid_result_payload")
        observed = {}
        for v in snapshot.values:
            if v.name in redacted_keys:
                observed[v.name] = missing("value_redacted", Availability.REDACTED)
            else:
                v.validate()  # existing immutable value representation validation only
                observed[v.name] = available((v.representation, v.data))
        _require(len(observed) == len(snapshot.values), "ambiguous_state_identity")
        capture = available("CanonicalExecutionPayload")
    else:
        raise InspectionError("unsupported_state_carrier")
    correlation = inspect_mapping(execution, mapping)
    op_rows = correlation.value[1] if correlation.status is Availability.AVAILABLE else ()
    state_ops = {}
    if mapping is not None:
        for op, row in zip(mapping.sidecar.operations, op_rows):
            if type(op.identity.locator) is StateLocator:
                state_ops.setdefault(op.identity.locator.state_id, []).append(row)
    entries = []
    for key in sorted(set(declarations) | set(observed)):
        declared = available(_type_record(declarations[key].value_type)) if key in declarations else missing("state_declaration_not_supplied")
        value = observed.get(key, missing("state_value_not_supplied"))
        source_air = available(tuple(state_ops[key])) if key in state_ops else missing("state_operation_mapping_not_supplied")
        entries.append(StateEntry(key, declared, value, source_air))
    _require(set(redacted_keys) <= set(declarations) | set(observed), "unknown_redaction_key")
    return StateView(execution, tuple(entries), capture)


@dataclass(frozen=True)
class StateTransitionView:
    before: StateView
    after: StateView
    changed_keys: InspectionField
    cause: InspectionField

    def __post_init__(self):
        _require(type(self.before) is StateView and type(self.after) is StateView and
                 self.before.execution == self.after.execution, "transition_execution_mismatch")
        _require(type(self.changed_keys) is InspectionField and type(self.cause) is InspectionField,
                 "invalid_transition")

    def canonical_form(self):
        return _form("state-difference", (self.before.canonical_form(), self.after.canonical_form(),
                     self.changed_keys.record(), self.cause.record()))


def state_difference(before, after):
    _require(type(before) is StateView and type(after) is StateView and
             before.execution == after.execution, "transition_execution_mismatch")
    complete = before.capture.status is after.capture.status is Availability.AVAILABLE
    complete = complete and all(e.observed_value.status is Availability.AVAILABLE
                               for e in before.entries + after.entries)
    if complete:
        a = {e.key: e.observed_value.record() for e in before.entries}
        b = {e.key: e.observed_value.record() for e in after.entries}
        changed = available(tuple(k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)))
    else:
        changed = missing("difference_requires_visible_supplied_snapshots")
    return StateTransitionView(before, after, changed, missing("state_difference_is_not_causal_evidence"))


def inspect_frame(execution, frame):
    """A supplied genuine canonical frame, never a reconstructed live stack.

    LocalBinding.value is Any, so local values are deliberately not expanded.
    """
    _require(type(execution) is ExecutionReference and type(frame) is CallFrame, "invalid_frame")
    return available(("pure-function-frame", execution.air_fingerprint, frame.function_id,
        frame.function_name, frame.depth, missing("frame_capture_scope_not_supplied").record(),
        missing("local_values_not_expanded", Availability.UNSUPPORTED).record()))


def inspect_authority(program, record):
    _require(type(program) is AIRProgram and type(record) is RetainedRecord and
             record.family is TraceFamily.AUTHORITY, "invalid_authority_evidence")
    _require(build_verified_air_lowering_input(VerifiedAIRProgram(program)).transport_fingerprint ==
             record.scope.air_fingerprint, "authority_program_mismatch")
    facts = {f.key: f.value for f in record.evidence.record.facts}
    checks = tuple(c for c in program.authority_checks if c.id == facts["check"])
    if checks:
        _require(len(checks) == 1 and type(checks[0]) is AuthorityCheck, "ambiguous_authority_check")
        check = checks[0]
        _require((check.principal, check.capability, check.resource) ==
                 (facts["principal"], facts["capability"], facts["resource"]), "authority_evidence_mismatch")
        check_ref = available((record.scope.air_fingerprint, check.id))
    else:
        # Role/requirement-derived runtime checks may not be declarations.
        check_ref = missing("declared_authority_check_not_supplied")
    return available((record.identity(), record.scope.air_fingerprint, facts["check"],
        facts["principal"], facts["capability"], facts["resource"], facts["allowed"], check_ref.record()))


def inspect_principal(execution, principal):
    _require(type(execution) is ExecutionReference and type(principal) is Principal,
             "invalid_principal")
    _require(type(principal.roles) is tuple and all(type(r) is str for r in principal.roles),
             "unsupported_role_reference")
    return available((execution.air_fingerprint, principal.id, tuple(sorted(principal.roles))))


@dataclass(frozen=True)
class InspectionSnapshot:
    execution: ExecutionReference = field(repr=False)
    state: StateView
    directive: InspectionField
    principal: InspectionField
    authority: InspectionField
    plan: InspectionField
    result: InspectionField
    provenance: InspectionField
    correlation: InspectionField
    diagnostics: InspectionField
    stack: InspectionField
    timestamp: str | None = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        _require(type(self.execution) is ExecutionReference and type(self.state) is StateView and
                 self.state.execution == self.execution, "inspection_execution_mismatch")
        _require(all(type(v) is InspectionField for v in (self.directive, self.principal, self.authority,
            self.plan, self.result, self.provenance, self.correlation, self.diagnostics, self.stack)), "invalid_inspection")
        _require(self.timestamp is None or type(self.timestamp) is str, "invalid_timestamp")

    def canonical_form(self):
        # Stable VIEW identity, not a replacement semantic or provenance identity.
        redacted = any(e.observed_value.status is Availability.REDACTED for e in self.state.entries)
        execution_form = ((self.execution.air_fingerprint, self.execution.routing_fingerprint,
                           self.execution.entry_directive, self.execution.profile)
                          if redacted else self.execution.semantic_form())
        return _form("inspection", (execution_form, self.state.record(),
            tuple(v.record() for v in (self.directive, self.principal, self.authority, self.plan,
                self.result, self.provenance, self.correlation, self.diagnostics, self.stack))))

    def fingerprint(self):
        return sha256(self.canonical_form().encode("utf-8")).hexdigest().upper()


@dataclass(frozen=True)
class SessionInspection:
    session: SessionReference
    execution: ExecutionReference = field(repr=False)
    snapshot: InspectionSnapshot

    def __post_init__(self):
        _require(type(self.session) is SessionReference and type(self.execution) is ExecutionReference and
                 type(self.snapshot) is InspectionSnapshot and self.snapshot.execution == self.execution,
                 "inspection_execution_mismatch")

    def validate_session(self, session):
        _require(type(session) is DebugSession and session.reference == self.session,
                 "inspection_session_mismatch")
        _require(session.execution == self.execution, "inspection_execution_mismatch")
        _require(session.state is Lifecycle.ACTIVE and Capability.OBSERVE in session.granted,
                 "inspection_session_unavailable")

    def binding_form(self):
        return _form("session-inspection", (self.session.canonical_form(),
                     self.execution.canonical_form(), self.snapshot.fingerprint()))


def bind_inspection(snapshot, session):
    _require(type(snapshot) is InspectionSnapshot and type(session) is DebugSession,
             "invalid_inspection_binding")
    bound = SessionInspection(session.reference, snapshot.execution, snapshot)
    bound.validate_session(session)
    return bound


def inspect_execution(execution, binding, *, retained=None, snapshot=None,
                      directive_record=None, mapping=None, redacted_keys=(), timestamp=None):
    """Project validated P12 plan/retention inputs; never wraps their execution.

    Legacy retained evidence has no P13 local execution ID. The embedding owner
    must bind that occurrence correctly; structural checks are not authentication.
    """
    _require(type(execution) is ExecutionReference and type(binding) is PlanMetadata,
             "invalid_execution_input")
    association = binding.association
    _require((execution.air_fingerprint, execution.routing_fingerprint, execution.entry_directive) ==
             (association.air_fingerprint, association.routing_fingerprint, association.entry_directive),
             "plan_execution_mismatch")
    program = binding.verified.program
    _require(build_verified_air_lowering_input(binding.verified).transport_fingerprint ==
             execution.air_fingerprint, "program_execution_mismatch")
    provenance = missing("retained_evidence_not_supplied")
    result = missing("execution_result_not_supplied")
    diagnostics = missing("diagnostics_not_supplied")
    authority = missing("authority_observations_not_supplied")
    collections = ()
    if retained is not None:
        _require(type(retained) in (ManagedRetention, NativeRetention), "unsupported_result_carrier")
        native = type(retained) is NativeRetention
        scope = retained.pre.scope if native else retained.scope
        expected_association = retained.mapping.association if native else association
        _require((scope.air_fingerprint, scope.routing_fingerprint, scope.association_fingerprint) ==
                 (execution.air_fingerprint, execution.routing_fingerprint, expected_association.fingerprint()),
                 "retention_execution_mismatch")
        _require(execution.provenance_fingerprint == scope.fingerprint(), "provenance_execution_mismatch")
        collections = (retained.collection,) if native else retained.collections
        _require(all(c.scope == scope for c in collections), "trace_scope_mismatch")
        if native:
            _require(execution.profile == scope.native_profile, "profile_execution_mismatch")
            _require(retained.post.result_fingerprint == retained.evidence.result.fingerprint() and
                     retained.post.scope_fingerprint == scope.fingerprint() and
                     retained.post.collection_fingerprint == retained.collection.fingerprint() and
                     retained.post.receipt_fingerprint == retained.evidence.result.input_fingerprint and
                     retained.post.receipt_fingerprint == retained.pre.receipt_fingerprint and
                     retained.post.image_fingerprint == retained.pre.image_fingerprint and
                     retained.post.output_fingerprint == retained.evidence.output_fingerprint and
                     retained.post.mapping_fingerprint == retained.mapping.fingerprint(),
                     "result_association_mismatch")
            _require(snapshot is None or snapshot == retained.evidence.result.outputs, "result_state_mismatch")
            snapshot = retained.evidence.result.outputs
            result = available(("CanonicalExecutionResult", retained.evidence.result.status,
                retained.post.result_fingerprint, execution.profile, retained.post.fingerprint()))
            provenance = available((scope.fingerprint(), retained.post.receipt_fingerprint,
                retained.post.image_fingerprint, retained.post.mapping_fingerprint,
                retained.post.fingerprint(), tuple((c.family.value, c.fingerprint()) for c in collections)))
            diagnostics = missing("native_result_has_no_diagnostic_collection", Availability.UNSUPPORTED)
            authority = missing("native_profile_has_no_authority_observations", Availability.NOT_APPLICABLE)
            mapping = retained.mapping if mapping is None else mapping
        else:
            _require(retained.context.plan_fingerprint == binding.fingerprint(), "result_association_mismatch")
            _require(retained.result_fingerprint == managed_result_fingerprint(retained.result),
                     "result_association_mismatch")
            _require(snapshot is None or snapshot == retained.result.final_state, "result_state_mismatch")
            snapshot = retained.result.final_state
            result = available(("runtime.ExecutionResult", ("ok", retained.result.ok),
                retained.result_fingerprint, execution.profile, retained.fingerprint()))
            diagnostics = available(tuple((d.severity, d.code, d.node_id) for d in retained.result.diagnostics
                                          if type(d) is Diagnostic))
            _require(len(diagnostics.value) == len(retained.result.diagnostics), "invalid_diagnostics")
            records = tuple(r for c in collections if c.family is TraceFamily.AUTHORITY for r in c.records)
            authority = available(tuple(inspect_authority(program, r).record() for r in records))
            provenance = available((scope.fingerprint(), retained.fingerprint(),
                tuple((c.family.value, c.fingerprint()) for c in collections), retained.unsupported))
    if mapping is None and binding.compiler is not None:
        mapping = binding.compiler.mapping
    if retained is not None and mapping is not None:
        expected_mapping = scope.native_mapping_fingerprint if type(mapping) is NativeSourceMapping else scope.source_mapping_fingerprint
        _require(mapping.fingerprint() == expected_mapping, "mapping_retention_mismatch")
    directive = missing("active_directive_not_supplied")
    principal = missing("directive_principal_not_supplied")
    if directive_record is not None:
        _require(type(directive_record) is RetainedRecord and any(
            directive_record in c.records for c in collections), "directive_scope_mismatch")
        _require(directive_record.family is TraceFamily.RUNTIME and
                 directive_record.evidence.record.kind == "directive.start", "unsupported_directive_observation")
        facts = {f.key: f.value for f in directive_record.evidence.record.facts}
        directives = tuple(d for d in program.directives if d.id == facts["directive"])
        _require(len(directives) == 1, "ambiguous_directive_identity")
        d = directives[0]
        _require(d.principal == facts["principal"] and d.name == facts["name"], "directive_evidence_mismatch")
        directive = available((execution.air_fingerprint, d.id, d.name, d.principal,
            d.id == execution.entry_directive, d.causal_decisions, d.authority_checks,
            directive_record.identity(), "retained_entry_observation_not_live_activation"))
        principals = tuple(p for p in program.principals if p.id == d.principal)
        if principals:
            _require(len(principals) == 1 and type(principals[0]) is Principal, "ambiguous_principal_identity")
            p = principals[0]
            principal = inspect_principal(execution, p)
    state = inspect_state(execution, program, snapshot, mapping=mapping, redacted_keys=redacted_keys)
    correlation = inspect_mapping(execution, mapping)
    plan = available((binding.fingerprint(), association.fingerprint(), association.routing_fingerprint,
                      association.entry_directive, association.owner_fingerprints, execution.profile))
    if redacted_keys:
        # Avoid value-derived result/trace/provenance hash or diagnostic side channels.
        result = missing("value_dependent_result_reference_withheld", Availability.REDACTED)
        provenance = missing("value_dependent_provenance_references_withheld", Availability.REDACTED)
        diagnostics = missing("diagnostic_projection_withheld", Availability.REDACTED)
        authority = missing("trace_projection_withheld", Availability.REDACTED)
        directive = missing("trace_projection_withheld", Availability.REDACTED)
    return InspectionSnapshot(execution, state, directive, principal, authority, plan, result,
        provenance, correlation, diagnostics, missing("retained_results_do_not_capture_semantic_stack"), timestamp)
