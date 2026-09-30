"""Opt-in P12.6-8 tooling orchestration; canonical owners execute once."""
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Optional
from pathlib import Path
import json
import tempfile

from air.model import VerifiedAIRProgram, Fact, StateAssignment, EventRecord
from air.verify import AIRVerifier
from language.compiler import CompiledSource, CompilerOperationEvidence, SourceMap, compile_source_with_operation_evidence
from tam.production import trace_map_from_source_map, trace_identity_for_source_map_entry
from runtime.engine import RuntimeEngine, ExecutionResult, MAX_INVOCATION_DEPTH
from runtime.context import ExecutionContext
from runtime.state import StateSnapshot, StateCell, StateDelta
from runtime.diagnostics import Trace, TraceStep
from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from causality.engine import CausalEngine
from effects.model import EffectIntent
from standard_library.core import DEFAULT_STANDARD_LIBRARY
from workflow.air_runner import RegistryExecutionPlan, build_default_context
from tooling.debug_metadata import SourceIdentity, MetadataSidecar, MetadataAssociation, _require, _hash, _digest
from tooling.source_air_mapping import SourceAIRMapping, source_air_mapping
from tooling.trace_retention import (ProvenanceScope, TraceFamily, TraceCollection, TAMEvidence, RuntimeEvidence,
    CausalEvidence, AuthorityEvidence, DiagnosticEvidence, NativeEvidence, OperationAssociation,
    NativeResultAssociation, _portable, _scalar, _RUNTIME_KEYS)
from apexforge.native_backend.lowering_input import build_verified_air_lowering_input
from apexforge.native_backend import native_execution as native
from apexforge.native_backend.source_mapping import (MappedNativeArtifact, NativeSourceMapping,
    build_native_with_mapping, emit_native_source_mapping)
from apexforge.native_backend.native_execution_contract import NativeExecutionError

SCHEMA = "apexforge.trace-integration/v1"

class ObservationError(ValueError):
    """Retention failed; an already-produced owner result remains accessible."""
    def __init__(self, code, owner_result=None):
        super().__init__(code)
        self.code = code
        self.owner_result = owner_result

@dataclass(frozen=True)
class RetentionLimits:
    source_bytes: int = 4 * 1024 * 1024
    records: int = 10000

    def __post_init__(self):
        _require(all(type(x) is int and 0 < x <= 16 * 1024 * 1024 for x in (self.source_bytes, self.records)),
                 "bounded positive retention limits required")


def _limit(count, maximum):
    _require(count <= maximum, "retention resource limit exceeded")


def _tam_attachment(scope, mapping, content):
    records = tuple(TAMEvidence(r) for r in trace_map_from_source_map(mapping.sidecar.source_map).records)
    by_trace = {}
    for evidence in mapping.sidecar.evidence:
        entry = mapping.sidecar.source_map.entries[evidence.source_map_index]
        key = trace_identity_for_source_map_entry(entry, entry_index=evidence.source_map_index)
        _require(key not in by_trace, "ambiguous producer operation attachment")
        operation = next(o for o in mapping.sidecar.operations if o.operation_id == evidence.operation_id)
        by_trace[key] = OperationAssociation(operation, evidence.source_map_index)
    associations = tuple(by_trace.get(r.record.trace_id) for r in records)
    return TraceCollection.supplied(scope, TraceFamily.TAM, records, operations=associations,
                                   source_mapping=mapping, source_contents=(content,))

@dataclass(frozen=True)
class CompilerMetadata:
    source: SourceIdentity
    content: bytes
    compiled: CompiledSource
    ledger: tuple[CompilerOperationEvidence, ...]
    verified: VerifiedAIRProgram
    mapping: SourceAIRMapping
    scope: ProvenanceScope
    tam: TraceCollection

    def __post_init__(self):
        _require(type(self.content) is bytes and type(self.ledger) is tuple and type(self.source) is SourceIdentity and
                 type(self.compiled) is CompiledSource and type(self.verified) is VerifiedAIRProgram and
                 type(self.mapping) is SourceAIRMapping and type(self.scope) is ProvenanceScope and
                 type(self.tam) is TraceCollection, "immutable compiler metadata required")

    def validate(self, limits=RetentionLimits()):
        _limit(len(self.content), limits.source_bytes)
        _limit(len(self.compiled.source_map.entries) * 2, limits.records)
        expected = ProvenanceScope.for_source(self.mapping, self.compiled, self.ledger, self.verified, self.source, self.content)
        _require(self.scope == expected, "stale compiler metadata scope")
        _require(self.tam == _tam_attachment(expected, self.mapping, self.content), "substituted compiler TAM evidence")

    def fingerprint(self):
        return _digest((SCHEMA, "compiler", self.scope.fingerprint(), self.tam.fingerprint()))


def compile_with_metadata(content: bytes, logical_name: str, *, limits=RetentionLimits()):
    _require(type(content) is bytes and type(limits) is RetentionLimits, "governed bytes/limits required")
    _limit(len(content), limits.source_bytes)
    source = SourceIdentity.from_bytes(logical_name, content)
    # Existing opt-in producer is the sole compilation call; unsupported forms remain unsupported.
    compiled, ledger = compile_source_with_operation_evidence(content.decode("utf-8"), source_name=logical_name)
    _limit(len(compiled.source_map.entries) * 2, limits.records)
    verified = AIRVerifier().verify(compiled.program).require_verified()
    mapping = source_air_mapping(compiled, ledger, verified, source, content)
    scope = ProvenanceScope.for_source(mapping, compiled, ledger, verified, source, content)
    result = CompilerMetadata(source, content, compiled, ledger, verified, mapping, scope, _tam_attachment(scope, mapping, content))
    result.validate(limits)
    return result

@dataclass(frozen=True)
class PlanMetadata:
    verified: VerifiedAIRProgram
    plan: RegistryExecutionPlan
    compiler: Optional[CompilerMetadata]
    association: MetadataAssociation
    mapping_fingerprint: str

    def __post_init__(self):
        _require(type(self.verified) is VerifiedAIRProgram and type(self.plan) is RegistryExecutionPlan and
                 (self.compiler is None or type(self.compiler) is CompilerMetadata) and
                 type(self.association) is MetadataAssociation, "canonical plan association required")
        if self.mapping_fingerprint:
            _hash(self.mapping_fingerprint)
        else:
            _require(type(self.mapping_fingerprint) is str, "mapping reference required")

    def validate(self, limits=RetentionLimits()):
        _require(self == associate_plan(self.verified, self.plan, self.compiler, limits=limits), "stale execution-plan metadata")

    def fingerprint(self):
        return _digest((SCHEMA, "plan", self.association.fingerprint(), self.mapping_fingerprint))


def associate_plan(verified, plan, compiler=None, *, limits=RetentionLimits()):
    if compiler is not None:
        _require(type(compiler) is CompilerMetadata, "compiler-owned attachment required")
        compiler.validate(limits)
        sidecar = compiler.mapping.sidecar
        contents = (compiler.content,)
        mapping_reference = compiler.mapping.fingerprint()
    else:
        lower = build_verified_air_lowering_input(verified)
        sidecar = MetadataSidecar((), lower.transport_fingerprint, SourceMap(), ())
        contents, mapping_reference = (), ""
    association = MetadataAssociation.for_plan(sidecar, verified, plan, contents, tuple(o.identity for o in sidecar.operations))
    return PlanMetadata(verified, plan, compiler, association, mapping_reference)


def _state_identity(state):
    _require(type(state) is StateSnapshot and type(state.cells) is tuple, "canonical immutable initial state required")
    result = []
    for cell in state.cells:
        _require(type(cell) is StateCell, "canonical state cell required")
        result.append((_portable(cell.key), _scalar(cell.value)))
    return tuple(result)


def _policy_identity(policy):
    _require(type(policy) is AuthorityEngine and type(policy.grants) is tuple, "UNSUPPORTED_POLICY_OWNER")
    grants = []
    for grant in policy.grants:
        _require(type(grant) is AuthorityGrant, "canonical policy grant required")
        grants.append(tuple(_portable(x) for x in (grant.principal, grant.capability, grant.resource)))
    return "authority.engine/default-grants/v1", tuple(grants)

@dataclass(frozen=True)
class ManagedContextIdentity:
    plan_fingerprint: str
    state_fingerprint: str
    policy_fingerprint: str
    configuration_fingerprint: str

    def __post_init__(self):
        for field in self.__dataclass_fields__:
            _hash(getattr(self, field))

    def fingerprint(self):
        return _digest((SCHEMA, "managed-input", tuple(getattr(self, f) for f in self.__dataclass_fields__)))

    @classmethod
    def capture(cls, binding, context, runtime, limits=RetentionLimits()):
        binding.validate(limits)
        _require(type(context) is ExecutionContext and type(runtime) is RuntimeEngine, "UNSUPPORTED_RUNTIME_OWNER")
        _require(type(runtime._causality) is CausalEngine and runtime._standard_library is DEFAULT_STANDARD_LIBRARY,
                 "UNSUPPORTED_RUNTIME_OWNER")
        _require(type(runtime._max_invocation_depth) is int and runtime._max_invocation_depth > 0, "invalid runtime configuration")
        # These are governed compatibility contracts, not object/bytecode identity hashes.
        config = ("runtime.engine/default/v1", "causality.engine/max-weight/v1", "standard_library/default-frozen-p10/v1",
                  binding.plan.entry_directive, runtime._max_invocation_depth, "no-entry-guard")
        return cls(binding.fingerprint(), _digest(_state_identity(context.state)), _digest(_policy_identity(context.authority)), _digest(config))


def _facts_identity(facts):
    _require(type(facts) is tuple and all(type(f) is Fact for f in facts), "immutable owner facts required")
    return tuple((_portable(f.key), _scalar(f.value)) for f in facts)


def managed_result_fingerprint(result):
    """Tooling-owned identity of existing managed values, never a native result conversion."""
    _require(type(result) is ExecutionResult and type(result.delta) is StateDelta, "managed owner result required")
    assignments, events, effects = [], [], []
    for values in (result.delta.assignments, result.delta.events, result.delta.effects):
        _require(type(values) is tuple, "immutable managed delta required")
    for a in result.delta.assignments:
        _require(type(a) is StateAssignment, "evaluated assignment evidence required")
        assignments.append((_portable(a.state), _portable(a.operation), _scalar(a.value)))
    for e in result.delta.events:
        _require(type(e) is EventRecord, "canonical event record required")
        events.append((tuple(_portable(x) for x in (e.id, e.event, e.directive, e.principal)), _facts_identity(e.facts)))
    for e in result.delta.effects:
        _require(type(e) is EffectIntent, "canonical effect evidence required")
        effects.append((_portable(e.id), _portable(e.effect_type), _facts_identity(e.facts)))
    _require(type(result.diagnostics) is tuple, "immutable diagnostics required")
    diagnostics = tuple((d.severity, _portable(d.code), _portable(d.node_id)) for d in result.diagnostics)
    # Trace fingerprints are separately bound below. Display messages are not semantic identity material.
    return _digest((SCHEMA, "managed-owner-values", tuple(assignments), tuple(events), tuple(effects),
                    _state_identity(result.final_state), diagnostics))

@dataclass(frozen=True)
class StreamReference:
    parent_index: int
    family: TraceFamily
    ordinal: int

    def __post_init__(self):
        _require(type(self.parent_index) is int and self.parent_index >= 0 and type(self.ordinal) is int and self.ordinal >= 0 and
                 type(self.family) is TraceFamily, "producer stream position required")

@dataclass(frozen=True)
class ManagedRetention:
    context: ManagedContextIdentity
    result: ExecutionResult
    scope: ProvenanceScope
    collections: tuple[TraceCollection, ...]
    interleaving: tuple[StreamReference, ...]
    unsupported: tuple[tuple[int, str], ...]
    result_fingerprint: str

    def __post_init__(self):
        _require(type(self.context) is ManagedContextIdentity and type(self.result) is ExecutionResult and
                 type(self.scope) is ProvenanceScope and type(self.collections) is tuple and
                 all(type(c) is TraceCollection for c in self.collections) and type(self.interleaving) is tuple and
                 all(type(r) is StreamReference for r in self.interleaving) and type(self.unsupported) is tuple,
                 "immutable managed retention required")
        _require(all(type(item) is tuple and len(item) == 2 and type(item[0]) is int and item[0] >= 0 and
                     type(item[1]) is str for item in self.unsupported), "immutable unsupported coverage required")
        for _, kind in self.unsupported:
            _portable(kind)
        _hash(self.result_fingerprint)

    def fingerprint(self):
        return _digest((SCHEMA, "managed-retention", self.context.fingerprint(), self.result_fingerprint,
            tuple(c.fingerprint() for c in self.collections),
            tuple((r.parent_index, r.family.value, r.ordinal) for r in self.interleaving), self.unsupported))

    def validate(self, binding, context, runtime, expected_result, *, require_complete=True, limits=RetentionLimits()):
        identity = ManagedContextIdentity.capture(binding, context, runtime, limits)
        expected = _retain_managed(binding, identity, expected_result, require_complete, limits)
        _require(self == expected, "substituted managed trace/context/result")


def _retain_managed(binding, identity, result, require_complete, limits):
    _require(type(require_complete) is bool and type(result) is ExecutionResult and type(result.trace) is Trace and
             type(result.trace.steps) is tuple and type(result.diagnostics) is tuple, "canonical owner trace required")
    _limit(len(result.trace.steps) + len(result.diagnostics), limits.records)
    scope = ProvenanceScope(identity.fingerprint(), binding.association.air_fingerprint,
        binding.association.sidecar_fingerprint, binding.mapping_fingerprint, binding.association.fingerprint(),
        binding.association.routing_fingerprint)
    families = (TraceFamily.RUNTIME, TraceFamily.CAUSAL, TraceFamily.AUTHORITY, TraceFamily.DIAGNOSTIC)
    buckets = {f: [] for f in families}
    interleaving, unsupported = [], []
    for index, step in enumerate(result.trace.steps):
        _require(type(step) is TraceStep and type(step.kind) is str and type(step.message) is str and type(step.facts) is tuple,
                 "immutable owner trace step required")
        if step.kind in ("causal.evaluate", "causal.select"):
            family, evidence = TraceFamily.CAUSAL, CausalEvidence(step)
        elif step.kind == "authority.check":
            family, evidence = TraceFamily.AUTHORITY, AuthorityEvidence(step)
        elif step.kind in _RUNTIME_KEYS:
            family, evidence = TraceFamily.RUNTIME, RuntimeEvidence(step)
        else:
            unsupported.append((index, _portable(step.kind)))
            continue
        interleaving.append(StreamReference(index, family, len(buckets[family])))
        buckets[family].append(evidence)
    _require(not require_complete or not unsupported, "unsupported runtime trace schema; raw owner result preserved")
    buckets[TraceFamily.DIAGNOSTIC] = [DiagnosticEvidence(d) for d in result.diagnostics]
    collections = tuple(TraceCollection.supplied(scope, f, tuple(buckets[f])) for f in families)
    return ManagedRetention(identity, result, scope, collections, tuple(interleaving), tuple(unsupported), managed_result_fingerprint(result))


def execute_managed_retained(binding, *, context=None, runtime=None, expected_context=None,
                             require_complete=True, limits=RetentionLimits()):
    binding.validate(limits)
    context = build_default_context(binding.verified.program) if context is None else context
    runtime = RuntimeEngine() if runtime is None else runtime
    identity = ManagedContextIdentity.capture(binding, context, runtime, limits)
    _require(expected_context is None or (type(expected_context) is ManagedContextIdentity and expected_context == identity),
             "wrong managed execution context")
    _require(type(require_complete) is bool, "explicit coverage policy required")
    result = runtime.execute(binding.verified, context, entry_directives=(binding.plan.entry_directive,))
    try:
        _require(identity == ManagedContextIdentity.capture(binding, context, runtime, limits), "execution context changed")
        return _retain_managed(binding, identity, result, require_complete, limits)
    except (ValueError, TypeError) as exc:
        raise ObservationError("MANAGED_RETENTION_INVALID", result) from exc

@dataclass(frozen=True)
class NativePreDispatch:
    scope: ProvenanceScope
    mapping_fingerprint: str
    receipt_fingerprint: str
    image_fingerprint: str

    def __post_init__(self):
        _require(type(self.scope) is ProvenanceScope, "native scope required")
        for field in (self.mapping_fingerprint, self.receipt_fingerprint, self.image_fingerprint):
            _hash(field)

    def fingerprint(self):
        return _digest((SCHEMA, "native-pre-dispatch", self.scope.fingerprint(), self.mapping_fingerprint,
                        self.receipt_fingerprint, self.image_fingerprint))

    @classmethod
    def capture(cls, binding, mapped, *, limits=RetentionLimits()):
        binding.validate(limits)
        _require(type(mapped) is MappedNativeArtifact, "mapped owner artifact required")
        mapping = None if binding.compiler is None else binding.compiler.mapping
        contents = () if binding.compiler is None else (binding.compiler.content,)
        mapped.validate(binding.verified, binding.plan, source_mapping=mapping, source_contents=contents)
        content, actual_map = emit_native_source_mapping(binding.verified, binding.plan, source_mapping=mapping, source_contents=contents)
        scope = ProvenanceScope.for_native(actual_map, binding.verified, binding.plan, content,
                                          source_mapping=mapping, source_contents=contents)
        _require(scope.routing_fingerprint == binding.association.routing_fingerprint, "wrong native plan association")
        _limit(len(actual_map.regions), limits.records)
        return cls(scope, mapped.mapping_fingerprint, mapped.receipt_fingerprint, json.loads(mapped.artifact.receipt_json)["image"])

    def validate(self, binding, mapped, limits=RetentionLimits()):
        _require(self == self.capture(binding, mapped, limits=limits), "stale native pre-dispatch association")

@dataclass(frozen=True)
class NativeFailureObservation:
    pre_dispatch_fingerprint: str
    code: str

    def __post_init__(self):
        _hash(self.pre_dispatch_fingerprint)
        _portable(self.code)

@dataclass(frozen=True)
class NativeRetention:
    pre: NativePreDispatch
    mapping: NativeSourceMapping
    evidence: native.NativeExecutionEvidence
    collection: TraceCollection
    post: NativeResultAssociation

    def __post_init__(self):
        _require(type(self.pre) is NativePreDispatch and type(self.mapping) is NativeSourceMapping and
                 type(self.evidence) is native.NativeExecutionEvidence and type(self.collection) is TraceCollection and
                 type(self.post) is NativeResultAssociation, "immutable native retention required")

    def fingerprint(self):
        return _digest((SCHEMA, "native-retention", self.pre.fingerprint(), self.post.fingerprint()))

    def validate_snapshot(self, binding, expected_evidence, limits=RetentionLimits()):
        # No artifact file reads: lifecycle validation was completed before cleanup.
        binding.validate(limits)
        mapping = None if binding.compiler is None else binding.compiler.mapping
        contents = () if binding.compiler is None else (binding.compiler.content,)
        content, expected_map = emit_native_source_mapping(binding.verified, binding.plan, source_mapping=mapping, source_contents=contents)
        scope = ProvenanceScope.for_native(expected_map, binding.verified, binding.plan, content,
                                          source_mapping=mapping, source_contents=contents)
        _require(self.mapping == expected_map and self.pre.scope == scope and self.pre.mapping_fingerprint == expected_map.fingerprint(),
                 "substituted native mapping/input")
        self.collection.validate_supplied(scope, (NativeEvidence(expected_evidence),))
        _require(self.evidence == expected_evidence and self.pre.receipt_fingerprint == native.digest(expected_evidence.receipt_json.encode()),
                 "wrong native evidence/receipt")
        receipt = json.loads(expected_evidence.receipt_json)
        _require(receipt["air"] == scope.air_fingerprint and receipt["routing"] == scope.routing_fingerprint and
                 receipt["source"] == scope.generated_c_fingerprint and receipt["profile"] == scope.native_profile and
                 receipt["image"] == self.pre.image_fingerprint, "wrong retained native receipt")
        expected = NativeResultAssociation(scope.fingerprint(), self.collection.fingerprint(), expected_map.fingerprint(),
            self.pre.receipt_fingerprint, self.pre.image_fingerprint, expected_evidence.output_fingerprint,
            expected_evidence.result.fingerprint())
        _require(self.post == expected, "substituted native post-dispatch provenance")


def dispatch_native_retained(binding, mapped, *, pre=None, timeout=10, limits=RetentionLimits()):
    expected = NativePreDispatch.capture(binding, mapped, limits=limits)
    _require(pre is None or (type(pre) is NativePreDispatch and pre == expected), "stale native pre-dispatch provenance")
    pre = expected if pre is None else pre
    try:
        evidence = native.dispatch_native(mapped.artifact, binding.verified, binding.plan, timeout=timeout)
    except NativeExecutionError as exc:
        # Preserve original exception/code/detail; no new trace schema or canonical FAILURE result.
        exc.p12_6_observation = NativeFailureObservation(pre.fingerprint(), exc.code)
        raise
    try:
        pre.validate(binding, mapped, limits)
        source_mapping = None if binding.compiler is None else binding.compiler.mapping
        contents = () if binding.compiler is None else (binding.compiler.content,)
        collection = TraceCollection.supplied(pre.scope, TraceFamily.NATIVE, (NativeEvidence(evidence),))
        post = NativeResultAssociation.supplied(collection, mapped, evidence, binding.verified, binding.plan,
            source_mapping=source_mapping, source_contents=contents)
        result = NativeRetention(pre, mapped.mapping, evidence, collection, post)
        result.validate_snapshot(binding, evidence, limits)
        return result
    except (ValueError, TypeError) as exc:
        raise ObservationError("NATIVE_POST_RETENTION_INVALID", evidence) from exc


def execute_native_retained(binding, build_root, *, timeout=10, limits=RetentionLimits()):
    binding.validate(limits)
    source_mapping = None if binding.compiler is None else binding.compiler.mapping
    contents = () if binding.compiler is None else (binding.compiler.content,)
    # Existing admission remains before temporary build side effects.
    emit_native_source_mapping(binding.verified, binding.plan, source_mapping=source_mapping, source_contents=contents)
    with tempfile.TemporaryDirectory(prefix="apexforge-retained-", dir=build_root) as directory:
        mapped = build_native_with_mapping(binding.verified, binding.plan, Path(directory),
                                          source_mapping=source_mapping, source_contents=contents)
        pre = NativePreDispatch.capture(binding, mapped, limits=limits)
        return dispatch_native_retained(binding, mapped, pre=pre, timeout=timeout, limits=limits)
