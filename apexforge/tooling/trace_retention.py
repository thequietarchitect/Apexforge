"""P12.6-6 supplied observational references; no event production or semantics."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union
import math
import re
import json

from air.model import Fact
from language.source import SourceSpan, SourcePosition, SourceText
from tam.model import TraceRecord, TraceIdentity, TraceDomain
from tam.production import trace_identity_for_source_map_entry
from runtime.diagnostics import TraceStep, Diagnostic
from runtime.narrative_execution import NarrativeExecutionTraceEvent, NarrativeExecutionTraceFact
from apexforge.native_backend.native_execution import NativeExecutionEvidence, digest
from apexforge.native_backend.result import CanonicalExecutionResult
from apexforge.native_backend.payload import CanonicalExecutionPayload
from apexforge.native_backend.value import CanonicalExecutionValue
from tooling.debug_metadata import OperationReference, _require, _hash, _index, _digest

SCHEMA = "apexforge.trace-retention/v1"

class TraceFamily(Enum):
    TAM = "tam"
    RUNTIME = "core-runtime"
    DIAGNOSTIC = "runtime-diagnostic"
    CAUSAL = "causal-selection"
    AUTHORITY = "authority-observation"
    NARRATIVE = "narrative-runtime"
    NATIVE = "native-evidence"


def _portable(value):
    _require(type(value) is str and not any(ord(c) < 32 for c in value), "canonical text required")
    _require("\\" not in value and not value.startswith("/") and re.match(r"^[A-Za-z]:[/\\]", value) is None,
             "machine-path contamination")
    return value


def _scalar(value):
    if type(value) is str:
        return ("str", _portable(value))
    _require(type(value) in (int, bool, float, type(None)), "unsupported mutable/opaque fact value")
    if type(value) is float:
        _require(math.isfinite(value), "nonfinite fact value")
    return (type(value).__name__, value)


def _span(span):
    if span is None:
        return None
    _require(type(span) is SourceSpan and type(span.start) is SourcePosition and type(span.end) is SourcePosition,
             "canonical span required")
    _portable(span.source_name)
    return (span.source_name, (span.start.line, span.start.column, span.start.offset),
            (span.end.line, span.end.column, span.end.offset))


@dataclass(frozen=True)
class TAMEvidence:
    record: TraceRecord

@dataclass(frozen=True)
class RuntimeEvidence:
    record: TraceStep

@dataclass(frozen=True)
class DiagnosticEvidence:
    record: Diagnostic

@dataclass(frozen=True)
class CausalEvidence:
    record: TraceStep

@dataclass(frozen=True)
class AuthorityEvidence:
    record: TraceStep

@dataclass(frozen=True)
class NarrativeEvidence:
    record: NarrativeExecutionTraceEvent

@dataclass(frozen=True)
class NativeEvidence:
    record: NativeExecutionEvidence


# Exact existing producer signatures. Importing this module never invokes them.
_TAM_SIGNATURES = {
 ("source", "language.source", "source-span"),
 ("transformation", "language.compiler", "source-map-entry"),
 ("token", "language.lexer", "token"),
 ("declaration", "language.identities", "project-declared-identity"),
 ("ownership", "language.declarations", "project-declaration-owner"),
 ("reference", "language.resolution_queries", "project-resolution-query"),
 ("reference", "language.resolution_queries", "project-resolved-binding"),
 ("reference", "language.resolution_queries", "project-unresolved-resolution"),
 ("reference", "language.resolution_queries", "project-ambiguous-resolution"),
 ("scope", "language.resolution_context", "project-resolution-context"),
 ("reference", "language.resolution_candidates", "project-resolution-candidate"),
}
for owner, representation in (("model", "apex-type"), ("constraints", "apex-type-constraint"),
    ("generics", "apex-type-variable"), ("inference", "function-signature"),
    ("substitution", "generic-substitution"), ("specialization", "generic-specialization")):
    _TAM_SIGNATURES.add(("type", "type_system." + owner, representation))
for representation in ("principal", "authority-check", "authority-grant"):
    _TAM_SIGNATURES.add(("authority", "authority.model", representation))
for owner, representations in (("narrative_model", ("identity", "character", "scene", "dialogue", "choice-path",
    "choice", "perspective", "timeline", "state-fact", "state", "continuity-constraint", "continuity", "story")),
    ("narrative_graph", ("graph-node", "graph-edge", "semantic-graph")),
    ("narrative_validation", ("validation-finding", "validation-report"))):
    for representation in representations:
        _TAM_SIGNATURES.add(("narrative", "language." + owner, "narrative-" + representation))
_TAM_SIGNATURES = frozenset(_TAM_SIGNATURES)
_RUNTIME_KEYS = {
 "runtime.start": ("version", "roots"), "runtime.finish": ("events", "updates"),
 "directive.start": ("directive", "name", "principal", "depth"),
 "directive.finish": ("directive", "depth"), "directive.skip": ("directive",),
 "state.delta": ("assignments", "path", "state", "operation", "value"),
 "event.emit": ("event", "event_id"), "effect.intent": ("effect", "effect_type"),
 "when.evaluate": ("branch", "depth", "result"),
}


def _payload(value):
    t, r = type(value), value.record if type(value) in (TAMEvidence, RuntimeEvidence, DiagnosticEvidence,
        CausalEvidence, AuthorityEvidence, NarrativeEvidence, NativeEvidence) else None
    _require(r is not None, "unsupported trace family")
    if t is TAMEvidence:
        _require(type(r) is TraceRecord and type(r.schema_version) is int and r.schema_version == 1,
                 "unsupported TAM schema")
        _require(type(r.trace_id) is TraceIdentity and type(r.domain) is TraceDomain, "typed TAM identity required")
        _require(r.owner == r.producer and (r.domain.canonical_id, r.producer, r.representation) in _TAM_SIGNATURES,
                 "unavailable/unsupported TAM producer")
        parts = (r.trace_id.value, r.domain.canonical_id, r.producer, r.owner, r.representation,
                 r.canonical_identity)
        for part in parts:
            if part is not None:
                _portable(part)
        _require(type(r.provenance) is tuple and type(r.upstream_trace_ids) is tuple and
                 type(r.downstream_trace_ids) is tuple, "immutable TAM links required")
        for p in r.provenance:
            _portable(p)
        for link in r.upstream_trace_ids + r.downstream_trace_ids:
            _require(type(link) is TraceIdentity, "typed TAM link required")
            _portable(link.value)
        return TraceFamily.TAM, r.producer + "/" + r.representation + "/v1", (
            parts, r.schema_version, _span(r.source_span), r.provenance,
            tuple(x.value for x in r.upstream_trace_ids), tuple(x.value for x in r.downstream_trace_ids))
    if t is DiagnosticEvidence:
        _require(type(r) is Diagnostic and type(r.message) is str and type(r.severity) is str and
                 r.severity in ("error", "warning", "info"), "typed immutable diagnostic required")
        return TraceFamily.DIAGNOSTIC, "runtime.engine/diagnostic/v1", tuple(_portable(x) for x in
            (r.severity, r.code, r.node_id))
    if t is NativeEvidence:
        _require(type(r) is NativeExecutionEvidence and type(r.result) is CanonicalExecutionResult and
                 type(r.result.outputs) is CanonicalExecutionPayload and type(r.result.outputs.values) is tuple,
                 "immutable native evidence required")
        for v in r.result.outputs.values:
            _require(type(v) is CanonicalExecutionValue, "canonical native value required")
            for field in (v.name, v.representation, v.data):
                _portable(field)
        r.result.validate()
        _hash(r.output_fingerprint)
        _require(type(r.receipt_json) is str, "immutable receipt required")
        _require(r.result.input_fingerprint == digest(r.receipt_json.encode("utf-8")), "wrong receipt/result binding")
        return TraceFamily.NATIVE, "native_backend.native_execution/dispatch/v1", (
            r.result.input_fingerprint, r.output_fingerprint, r.result.fingerprint())
    _require(type(r.facts) is tuple, "immutable ordered facts required")
    if t is NarrativeEvidence:
        _require(type(r) is NarrativeExecutionTraceEvent and type(r.message) is str and
                 type(r.kind) is str and r.kind == "narrative_transition", "unsupported/ mutable narrative event")
        allowed = ("source_scene", "selected_choice", "selected_path_index", "destination_scene", "failure_kind", "outcome")
        family, producer, fact_type = TraceFamily.NARRATIVE, "runtime.narrative_observability/transition/v1", NarrativeExecutionTraceFact
    else:
        _require(type(r) is TraceStep and type(r.message) is str and type(r.kind) is str,
                 "typed immutable runtime observation required")
        fact_type = Fact
        if t is RuntimeEvidence:
            _require(r.kind in _RUNTIME_KEYS, "unsupported runtime event kind")
            allowed = _RUNTIME_KEYS[r.kind]
            family, producer = TraceFamily.RUNTIME, "runtime.engine/trace/v1"
        elif t is AuthorityEvidence:
            _require(r.kind == "authority.check", "authority decision must be supplied, not inferred")
            allowed = ("allowed", "capability", "check", "principal", "resource")
            family, producer = TraceFamily.AUTHORITY, "runtime.engine/authority-observation/v1"
        else:
            _require(r.kind in ("causal.evaluate", "causal.select"), "unsupported causal observation")
            allowed = ("cause", "selected", "weight") if r.kind == "causal.evaluate" else ("path", "weight")
            family, producer = TraceFamily.CAUSAL, "causality.engine/selection/v1"
    keys = []
    fields = []
    for fact in r.facts:
        _require(type(fact) is fact_type, "typed immutable fact required")
        key = _portable(fact.key)
        _require(key in allowed or (family is TraceFamily.CAUSAL and r.kind == "causal.evaluate" and
                 key.startswith("path.") and key.endswith(".weight")), "unsupported canonical fact field")
        if family is not TraceFamily.NARRATIVE:
            if key in ("allowed", "result"):
                _require(type(fact.value) is bool, "exact boolean observation required")
            elif key in ("assignments", "depth", "roots", "events", "updates", "weight") or key.endswith(".weight"):
                _require(type(fact.value) is int, "exact integer observation required")
            elif key != "value":
                _require(type(fact.value) is str, "exact string observation required")
        else:
            _require(type(fact.value) is str, "exact narrative string fact required")
        keys.append(key)
        fields.append((key, _scalar(fact.value)))
    _require(len(set(keys)) == len(keys), "duplicate fact key")
    required = set(allowed)
    if family is TraceFamily.NARRATIVE:
        required -= {"destination_scene", "failure_kind"}
    _require(required <= set(keys), "missing required producer facts")
    return family, producer, (r.kind, tuple(fields))


@dataclass(frozen=True)
class ProvenanceScope:
    input_fingerprint: str
    air_fingerprint: str
    sidecar_fingerprint: str = ""
    source_mapping_fingerprint: str = ""
    association_fingerprint: str = ""
    routing_fingerprint: str = ""
    native_mapping_fingerprint: str = ""
    native_profile: str = ""
    generated_c_fingerprint: str = ""
    schema: str = SCHEMA

    def __post_init__(self):
        _require(all(type(getattr(self, name)) is str for name in self.__dataclass_fields__),
                 "exact canonical provenance strings required")
        _require(self.schema == SCHEMA, "unknown trace schema")
        for name in ("input_fingerprint", "air_fingerprint"):
            _hash(getattr(self, name))
        for name in ("sidecar_fingerprint", "source_mapping_fingerprint", "association_fingerprint",
                     "routing_fingerprint", "native_mapping_fingerprint", "generated_c_fingerprint"):
            value = getattr(self, name)
            if value:
                _hash(value)
        _portable(self.native_profile)
        if self.native_mapping_fingerprint:
            from apexforge.native_backend.native_execution_contract import PROFILE
            _require(self.native_profile == PROFILE and bool(self.routing_fingerprint) and
                     bool(self.generated_c_fingerprint) and bool(self.association_fingerprint), "incomplete/wrong native scope")
        else:
            _require(not self.native_profile and not self.generated_c_fingerprint, "native mapping reference required")

    def fingerprint(self):
        return _digest(tuple(getattr(self, f) for f in self.__dataclass_fields__))

    @classmethod
    def for_source(cls, mapping, compiled, ledger, verified, source, content, *, plan=None):
        from tooling.source_air_mapping import SourceAIRMapping
        from tooling.debug_metadata import MetadataAssociation
        _require(type(mapping) is SourceAIRMapping, "existing source mapping required")
        mapping.validate(compiled, ledger, verified, source, content)
        association = None if plan is None else MetadataAssociation.for_plan(mapping.sidecar, verified, plan,
            (content,), tuple(op.identity for op in mapping.sidecar.operations))
        return cls(source.fingerprint(), mapping.sidecar.air_fingerprint, mapping.sidecar.fingerprint(),
                   mapping.fingerprint(), "" if association is None else association.fingerprint(),
                   "" if association is None else association.routing_fingerprint)

    @classmethod
    def for_native(cls, mapping, verified, plan, content, *, source_mapping=None, source_contents=()):
        from apexforge.native_backend.source_mapping import NativeSourceMapping
        _require(type(mapping) is NativeSourceMapping, "existing native mapping required")
        mapping.validate(verified, plan, content, source_mapping=source_mapping, source_contents=source_contents)
        return cls(mapping.association.fingerprint(), mapping.sidecar.air_fingerprint, mapping.sidecar.fingerprint(),
                   "" if source_mapping is None else source_mapping.fingerprint(), mapping.association.fingerprint(),
                   mapping.association.routing_fingerprint, mapping.fingerprint(), mapping.profile,
                   mapping.generated_source.content_fingerprint)


@dataclass(frozen=True)
class OperationAssociation:
    operation: OperationReference
    source_map_index: int

    def __post_init__(self):
        _require(type(self.operation) is OperationReference, "existing operation reference required")
        _index(self.source_map_index)

    def validate(self, evidence, scope, mapping):
        # Only the existing compiler TAM SourceMap entry has exact producer correspondence here.
        _require(type(evidence) is TAMEvidence and evidence.record.representation == "source-map-entry",
                 "producer lacks operation occurrence; inference forbidden")
        _require(scope.source_mapping_fingerprint == mapping.fingerprint() and
                 scope.sidecar_fingerprint == mapping.sidecar.fingerprint(), "wrong mapping association")
        _require(self.operation in mapping.sidecar.operations and self.source_map_index < len(mapping.sidecar.source_map.entries),
                 "operation not present in mapping")
        entry = mapping.sidecar.source_map.entries[self.source_map_index]
        r = evidence.record
        _require(r.trace_id == trace_identity_for_source_map_entry(entry, entry_index=self.source_map_index) and
                 r.source_span == entry.span and r.canonical_identity == entry.air_id, "wrong source evidence")
        _require(any(e.operation_id == self.operation.operation_id and e.source_map_index == self.source_map_index
                     for e in mapping.sidecar.evidence), "unsupported operation correspondence")

    def canonical_identity(self):
        return self.operation.canonical_identity(), self.source_map_index


@dataclass(frozen=True)
class RetainedRecord:
    scope: ProvenanceScope
    ordinal: int
    evidence: Union[TAMEvidence, RuntimeEvidence, DiagnosticEvidence, CausalEvidence, AuthorityEvidence, NarrativeEvidence, NativeEvidence]
    operation: Optional[OperationAssociation] = None

    def __post_init__(self):
        _require(type(self.scope) is ProvenanceScope, "governed scope required")
        _index(self.ordinal)
        _payload(self.evidence)  # defensively validate every nested canonical value
        if self.operation is not None:
            _require(type(self.operation) is OperationAssociation and type(self.evidence) is TAMEvidence and
                     self.evidence.record.representation == "source-map-entry", "insufficient producer operation evidence")

    @property
    def family(self):
        return _payload(self.evidence)[0]

    def identity(self):
        family, producer, payload = _payload(self.evidence)
        return "af-trace:" + _digest((SCHEMA, family.value, producer, self.scope.fingerprint(), self.ordinal,
            payload, None if self.operation is None else self.operation.canonical_identity()))


@dataclass(frozen=True)
class TraceCollection:
    scope: ProvenanceScope
    family: TraceFamily
    records: tuple[RetainedRecord, ...]
    unresolved_tam_links: tuple[str, ...] = ()

    def __post_init__(self):
        _require(type(self.scope) is ProvenanceScope and type(self.family) is TraceFamily, "typed scope/family required")
        _require(type(self.records) is tuple and all(type(r) is RetainedRecord for r in self.records), "immutable records required")
        _require(all(r.scope == self.scope and r.family is self.family for r in self.records), "mixed family/scope")
        _require(tuple(r.ordinal for r in self.records) == tuple(range(len(self.records))), "invalid producer ordinal/order")
        ids = tuple(r.identity() for r in self.records)
        _require(len(set(ids)) == len(ids), "duplicate trace identity")
        _require(type(self.unresolved_tam_links) is tuple, "immutable external TAM link declarations required")
        for link in self.unresolved_tam_links:
            _portable(link)
        _require(self.unresolved_tam_links == tuple(sorted(set(self.unresolved_tam_links))),
                 "noncanonical external TAM declarations")
        if self.family is TraceFamily.TAM:
            ids = tuple(r.evidence.record.trace_id for r in self.records)
            _require(len(set(ids)) == len(ids), "duplicate original TAM identity")
            missing = {link.value for r in self.records for link in
                       r.evidence.record.upstream_trace_ids + r.evidence.record.downstream_trace_ids if link not in ids}
            _require(missing == set(self.unresolved_tam_links), "undeclared/wrong external TAM links")
        else:
            _require(not self.unresolved_tam_links, "TAM links cannot cross untyped trace families")

    @classmethod
    def supplied(cls, scope, family, evidence, *, operations=(), source_mapping=None, source_contents=(), unresolved_links=()):
        _require(type(evidence) is tuple, "available immutable producer collection required")
        _require(type(operations) is tuple and (not operations or len(operations) == len(evidence)), "explicit association order required")
        records = tuple(RetainedRecord(scope, i, value, None if not operations else operations[i])
                        for i, value in enumerate(evidence))
        result = cls(scope, family, records, unresolved_links)
        for record in records:
            if type(record.evidence) is TAMEvidence and record.evidence.record.source_span is not None:
                _require(source_mapping is not None and scope.source_mapping_fingerprint == source_mapping.fingerprint() and
                         scope.sidecar_fingerprint == source_mapping.sidecar.fingerprint(), "source mapping unavailable/mismatch")
                _require(type(source_contents) is tuple and len(source_contents) == len(source_mapping.sidecar.sources),
                         "governed source snapshots required")
                span = record.evidence.record.source_span
                matches = []
                for source, content in zip(source_mapping.sidecar.sources, source_contents):
                    source.validate_content(content)
                    if source.logical_name == span.source_name:
                        matches.append(SourceText(source.logical_name, content.decode("utf-8")).span(span.start.offset, span.end.offset))
                _require(matches == [span], "source/span mismatch")
            if record.operation is not None:
                _require(source_mapping is not None, "source mapping unavailable")
                record.operation.validate(record.evidence, scope, source_mapping)
        return result

    def validate_supplied(self, expected_scope, evidence, *, operations=(), source_mapping=None, source_contents=(), unresolved_links=()):
        expected = self.supplied(expected_scope, self.family, evidence, operations=operations, source_mapping=source_mapping, source_contents=source_contents, unresolved_links=unresolved_links)
        _require(self.fingerprint() == expected.fingerprint(), "stale/substituted trace provenance/payload")

    def fingerprint(self):
        return _digest((SCHEMA, self.scope.fingerprint(), self.family.value, tuple(r.identity() for r in self.records), self.unresolved_tam_links))


@dataclass(frozen=True)
class NativeResultAssociation:
    scope_fingerprint: str
    collection_fingerprint: str
    mapping_fingerprint: str
    receipt_fingerprint: str
    image_fingerprint: str
    output_fingerprint: str
    result_fingerprint: str

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            _hash(getattr(self, name))

    @classmethod
    def supplied(cls, collection, mapped, evidence, verified, plan, *, source_mapping=None, source_contents=()):
        from apexforge.native_backend.source_mapping import MappedNativeArtifact
        _require(type(collection) is TraceCollection and type(mapped) is MappedNativeArtifact, "typed collection/artifact required")
        _payload(NativeEvidence(evidence))
        mapped.validate(verified, plan, source_mapping=source_mapping, source_contents=source_contents)
        # Reuse the mapping owner, never inspect generated C or infer executed operations.
        from apexforge.native_backend.source_mapping import emit_native_source_mapping
        content, mapping = emit_native_source_mapping(verified, plan, source_mapping=source_mapping, source_contents=source_contents)
        expected_scope = ProvenanceScope.for_native(mapping, verified, plan, content,
            source_mapping=source_mapping, source_contents=source_contents)
        _require(collection.scope == expected_scope, "wrong AIR/routing/mapping scope")
        _require(evidence.receipt_json == mapped.artifact.receipt_json, "wrong receipt")
        if collection.family is TraceFamily.NATIVE:
            collection.validate_supplied(expected_scope, (NativeEvidence(evidence),))
        _require(collection.family in (TraceFamily.TAM, TraceFamily.NATIVE),
                 "interpreter observations cannot claim native execution without a producer scope contract")
        receipt = json.loads(evidence.receipt_json)
        return cls(collection.scope.fingerprint(), collection.fingerprint(), mapped.mapping_fingerprint,
            mapped.receipt_fingerprint, receipt["image"], evidence.output_fingerprint, evidence.result.fingerprint())

    def validate(self, collection, mapped, expected_evidence, verified, plan, **kwargs):
        _require(self == self.supplied(collection, mapped, expected_evidence, verified, plan, **kwargs),
                 "substituted artifact/output/result association")

    def fingerprint(self):
        return _digest((SCHEMA, "native-result-association", tuple(getattr(self, f) for f in self.__dataclass_fields__)))
