"""P13.5 projections of supplied evidence; never an evidence producer/executor.

Embedding owners validate and authorize carriers before supplying immutable
anchors. Graph edges describe explicit associations, never external attribution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json

from tooling.debug_session import DebugSession, SessionReference, ExecutionReference, Lifecycle, Capability
from tooling.debug_inspection import (InspectionField, Availability as FieldAvailability,
    available, missing, inspect_execution, inspect_authority, SessionInspection)
from tooling.debug_correlation import CorrelationIndex
from tooling.trace_integration import PlanMetadata, ManagedRetention, NativeRetention
from tooling.trace_retention import (TraceFamily, TraceCollection, RetainedRecord,
    TAMEvidence, _payload)

SCHEMA = "apexforge.debug-evidence/v1"
EVIDENCE_BEFORE_ATTRIBUTION = True


class EvidenceError(ValueError):
    """Diagnostic codes never interpolate supplied payloads."""


def _require(condition, code):
    if not condition:
        raise EvidenceError(code)


def _form(kind, value):
    return json.dumps((SCHEMA, kind, value), ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _digest(value):
    return sha256(value.encode("utf-8")).hexdigest().upper()


class Canonical:
    def fingerprint(self):
        return _digest(self.canonical_form())


def _public_payload(value):
    if value is None:
        return missing("producer_optional_field_absent").record()
    if type(value) is tuple:
        if len(value) == 3 and value[0] in tuple(s.value for s in FieldAvailability
            if s is not FieldAvailability.AVAILABLE) and value[1] is None and type(value[2]) is str:
            return value  # Existing explicit P13.3 missing-field record.
        return tuple(_public_payload(x) for x in value)
    return value


class EvidenceKind(Enum):
    EXECUTION = "execution"
    AIR = "air-program"
    PLAN = "execution-plan-association"
    SOURCE = "source-document"
    SOURCE_MAPPING = "source-mapping"
    AIR_MAPPING = "air-metadata"
    AIR_OPERATION = "air-operation"
    NATIVE_MAPPING = "native-mapping"
    NATIVE_REGION = "generated-native-region"
    TRACE_FAMILY = "trace-collection"
    TRACE = "retained-trace"
    TAM = "compiler-tam"
    CAUSAL_DECISION = "causal-decision"
    CAUSAL_PATH = "causal-path"
    AUTHORITY = "observed-program-authority"
    SCOPE = "provenance-scope"
    BUILD_RECEIPT = "native-build-receipt"
    ARTIFACT = "native-image"
    RESULT = "execution-result"
    RESULT_ASSOCIATION = "retained-result-association"


class Availability(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    NOT_APPLICABLE = "not_applicable"
    REDACTED = "redacted"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class EvidenceReference(Canonical):
    kind: EvidenceKind
    producer_identity: str
    producer_schema: str
    air_fingerprint: str = ""
    scope_fingerprint: str = ""
    execution_identity: str = ""

    def __post_init__(self):
        _require(type(self.kind) is EvidenceKind and all(type(x) is str for x in
            (self.producer_identity, self.producer_schema, self.air_fingerprint,
             self.scope_fingerprint, self.execution_identity)) and bool(self.producer_identity)
            and bool(self.producer_schema), "invalid_evidence_reference")

    def canonical_form(self):
        return _form("reference", (self.kind.value, self.producer_identity, self.producer_schema,
            self.air_fingerprint, self.scope_fingerprint, self.execution_identity))


@dataclass(frozen=True)
class EvidenceNode(Canonical):
    reference: EvidenceReference
    payload: InspectionField

    def __post_init__(self):
        _require(type(self.reference) is EvidenceReference and type(self.payload) is InspectionField,
                 "invalid_evidence_node")

    @property
    def node_id(self):
        return self.reference.fingerprint()

    def canonical_form(self):
        return _form("node", (self.reference.canonical_form(), self.payload.record()))


class Relation(Enum):
    ASSOCIATED_WITH = "associated_with"
    BELONGS_TO_EXECUTION = "belongs_to_execution"
    RETAINED_BY = "retained_by"
    MAPS_TO = "maps_to"
    DEFINES_PATH = "defines_path"
    SELECTED_PATH = "selected_path"
    RECORDED_TAM_LINK = "recorded_tam_link"


@dataclass(frozen=True)
class EvidenceEdge(Canonical):
    source: str
    target: str
    relation: Relation
    support: str

    def __post_init__(self):
        _require(type(self.relation) is Relation and all(type(x) is str and bool(x)
            for x in (self.source, self.target, self.support)), "invalid_evidence_edge")

    def canonical_form(self):
        return _form("edge", (self.source, self.target, self.relation.value, self.support))


@dataclass(frozen=True)
class EvidenceGraph(Canonical):
    nodes: tuple[EvidenceNode, ...]
    edges: tuple[EvidenceEdge, ...]

    def __post_init__(self):
        _require(type(self.nodes) is tuple and all(type(x) is EvidenceNode for x in self.nodes)
            and type(self.edges) is tuple and all(type(x) is EvidenceEdge for x in self.edges),
            "immutable_graph_required")
        _require(len({n.node_id for n in self.nodes}) == len(self.nodes), "duplicate_evidence_node")
        object.__setattr__(self, "nodes", tuple(sorted(self.nodes, key=lambda n: n.node_id)))
        object.__setattr__(self, "edges", tuple(sorted(set(self.edges), key=lambda e: e.canonical_form())))
        ids = {n.node_id for n in self.nodes}
        _require(all(e.source in ids and e.target in ids and e.support in ids for e in self.edges),
                 "dangling_evidence_edge")

    def canonical_form(self):
        return _form("graph", (tuple(n.canonical_form() for n in self.nodes),
                               tuple(e.canonical_form() for e in self.edges)))

    def node(self, node_id):
        matches = tuple(n for n in self.nodes if n.node_id == node_id)
        _require(len(matches) == 1, "unknown_evidence_node")
        return matches[0]

    def predecessors(self, node_id):
        self.node(node_id)
        return tuple(self.node(i) for i in sorted({e.source for e in self.edges if e.target == node_id}))

    def successors(self, node_id):
        self.node(node_id)
        return tuple(self.node(i) for i in sorted({e.target for e in self.edges if e.source == node_id}))


@dataclass(frozen=True)
class EvidenceSelection:
    status: Availability
    nodes: tuple[EvidenceNode, ...] = ()
    reason: str = ""

    def __post_init__(self):
        _require(type(self.status) is Availability and type(self.nodes) is tuple and
            all(type(n) is EvidenceNode for n in self.nodes) and type(self.reason) is str,
            "invalid_evidence_selection")
        _require((self.status in (Availability.AVAILABLE, Availability.AMBIGUOUS) and bool(self.nodes)
            and not self.reason) or (self.status not in (Availability.AVAILABLE, Availability.AMBIGUOUS)
            and not self.nodes and bool(self.reason)), "evidence_availability_mismatch")


@dataclass(frozen=True)
class EvidenceBinding:
    """Trusted owner-captured anchors; constructing them is not authentication."""
    session: SessionReference
    execution: ExecutionReference = field(repr=False)
    plan_fingerprint: str = field(repr=False)
    retention_fingerprint: str = field(default="", repr=False)
    compiler_fingerprint: str = field(default="", repr=False)
    correlation_fingerprint: str = field(default="", repr=False)

    def __post_init__(self):
        _require(type(self.session) is SessionReference and type(self.execution) is ExecutionReference
            and all(type(x) is str for x in (self.plan_fingerprint, self.retention_fingerprint,
                                            self.compiler_fingerprint, self.correlation_fingerprint)),
                 "invalid_evidence_binding")

    def validate_session(self, session):
        _require(type(session) is DebugSession and session.reference == self.session,
                 "evidence_session_mismatch")
        _require(session.execution == self.execution, "evidence_execution_mismatch")
        _require(session.state is Lifecycle.ACTIVE and Capability.OBSERVE in session.granted,
                 "evidence_session_unavailable")


@dataclass(frozen=True)
class EvidenceView(Canonical):
    binding: EvidenceBinding = field(repr=False)
    graph: EvidenceGraph
    result_node_ids: tuple[str, ...]
    # These are producer trace positions, never a semantic or causal schedule.
    family_order: tuple[tuple[str, str, int, str], ...]
    interleaving: tuple[tuple[int, str, int, str], ...]
    coverage: InspectionField
    execution_receipt: InspectionField
    redacted: bool = False
    timestamp: str | None = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        _require(type(self.binding) is EvidenceBinding and type(self.graph) is EvidenceGraph and
            type(self.result_node_ids) is tuple and type(self.family_order) is tuple and
            type(self.interleaving) is tuple and type(self.coverage) is InspectionField and
            type(self.execution_receipt) is InspectionField and type(self.redacted) is bool and
            (self.timestamp is None or type(self.timestamp) is str), "invalid_evidence_view")
        for node_id in self.result_node_ids:
            _require(self.graph.node(node_id).reference.kind is EvidenceKind.RESULT, "invalid_result_reference")

    def canonical_form(self):
        # Binding anchors deliberately excluded from client-visible redacted identity.
        return _form("view", (self.graph.canonical_form(), self.result_node_ids, self.family_order,
            self.interleaving, self.coverage.record(), self.execution_receipt.record(), self.redacted))

    def evidence_for(self, kind):
        _require(type(kind) is EvidenceKind, "unsupported_evidence_kind")
        if self.redacted:
            return EvidenceSelection(Availability.REDACTED, reason="evidence_view_redacted")
        values = tuple(n for n in self.graph.nodes if n.reference.kind is kind)
        return EvidenceSelection(Availability.AVAILABLE, values) if values else EvidenceSelection(
            Availability.UNAVAILABLE, reason="evidence_not_supplied")

    def result_evidence(self, session, inspection):
        self.binding.validate_session(session)
        _require(type(inspection) is SessionInspection, "invalid_result_inspection")
        inspection.validate_session(session)
        _require(inspection.execution == self.binding.execution, "result_execution_mismatch")
        if self.redacted or inspection.snapshot.result.status is FieldAvailability.REDACTED:
            return EvidenceSelection(Availability.REDACTED, reason="result_evidence_redacted")
        if inspection.snapshot.result.status is not FieldAvailability.AVAILABLE:
            return EvidenceSelection(Availability.UNAVAILABLE, reason="inspection_result_unavailable")
        supplied = inspection.snapshot.result.value
        _require(type(supplied) is tuple and len(supplied) == 5, "invalid_result_inspection")
        _require(any(self.graph.node(i).reference.producer_identity == supplied[2]
                     for i in self.result_node_ids), "inspection_result_mismatch")
        _require(any(n.reference.kind is EvidenceKind.RESULT_ASSOCIATION and
            n.reference.producer_identity == supplied[-1] for n in self.graph.nodes),
            "inspection_result_association_mismatch")
        ids = {i for i in self.result_node_ids}
        ids.update(e.target for e in self.graph.edges if e.source in self.result_node_ids)
        return EvidenceSelection(Availability.AVAILABLE, tuple(self.graph.node(i) for i in sorted(ids)))


def _validate_managed(retained):
    _require(retained.scope.input_fingerprint == retained.context.fingerprint(), "managed_context_scope_mismatch")
    collections = {c.family: c for c in retained.collections}
    _require(len(collections) == len(retained.collections), "duplicate_trace_family")
    positions = []
    for entry in retained.interleaving:
        _require(entry.family in collections and entry.ordinal < len(collections[entry.family].records)
            and entry.parent_index < len(retained.result.trace.steps), "invalid_retained_interleaving")
        record = collections[entry.family].records[entry.ordinal]
        _require(record.evidence.record == retained.result.trace.steps[entry.parent_index],
                 "trace_result_mismatch")
        positions.append(entry.parent_index)
    _require(positions == sorted(set(positions)), "invalid_retained_stream_order")
    expected = {(c.family, r.ordinal) for c in retained.collections if c.family is not TraceFamily.DIAGNOSTIC
                for r in c.records}
    _require(expected == {(r.family, r.ordinal) for r in retained.interleaving}, "missing_retained_stream_record")
    unsupported = tuple(i for i, kind in retained.unsupported)
    _require(len(set(unsupported)) == len(unsupported) and not (set(unsupported) & set(positions)) and
        set(positions) | set(unsupported) == set(range(len(retained.result.trace.steps))), "invalid_trace_coverage")
    _require(all(i < len(retained.result.trace.steps) and retained.result.trace.steps[i].kind == kind
                 for i, kind in retained.unsupported), "unsupported_trace_mismatch")
    diagnostic = collections.get(TraceFamily.DIAGNOSTIC)
    _require(diagnostic is not None and tuple(r.evidence.record for r in diagnostic.records) ==
             retained.result.diagnostics, "diagnostic_result_mismatch")


def _validate_native(retained, execution):
    mapping, scope, post = retained.mapping, retained.pre.scope, retained.post
    _require((mapping.sidecar.air_fingerprint, mapping.association.routing_fingerprint,
              mapping.association.entry_directive, mapping.profile) ==
             (execution.air_fingerprint, execution.routing_fingerprint,
              execution.entry_directive, execution.profile), "native_plan_mismatch")
    _require((scope.sidecar_fingerprint, scope.association_fingerprint, scope.native_mapping_fingerprint,
              scope.generated_c_fingerprint, scope.native_profile) ==
             (mapping.sidecar.fingerprint(), mapping.association.fingerprint(), mapping.fingerprint(),
              mapping.generated_source.content_fingerprint, mapping.profile), "native_scope_mismatch")
    _require(retained.pre.mapping_fingerprint == mapping.fingerprint(), "native_mapping_mismatch")
    _require(len(retained.collection.records) == 1 and retained.collection.family is TraceFamily.NATIVE
        and retained.collection.records[0].evidence.record == retained.evidence, "native_trace_mismatch")
    try:
        receipt = json.loads(retained.evidence.receipt_json)
    except (ValueError, TypeError):
        raise EvidenceError("invalid_native_receipt") from None
    _require(type(receipt) is dict and _digest(retained.evidence.receipt_json) == post.receipt_fingerprint,
             "receipt_fingerprint_mismatch")
    _require(tuple(receipt.get(k) for k in ("air", "routing", "entry", "owner_air", "profile", "source", "image")) ==
        (execution.air_fingerprint, execution.routing_fingerprint, execution.entry_directive,
         execution.air_fingerprint, execution.profile, scope.generated_c_fingerprint, post.image_fingerprint),
        "receipt_artifact_mismatch")
    return receipt


def build_evidence_view(session, binding, anchors, *, retained=None, correlation=None,
                        redacted=False, timestamp=None):
    """Project trusted supplied carriers. No validators that execute/re-emit are used."""
    _require(type(anchors) is EvidenceBinding and type(binding) is PlanMetadata and
             type(redacted) is bool, "invalid_evidence_inputs")
    anchors.validate_session(session)
    execution = anchors.execution
    _require(binding.fingerprint() == anchors.plan_fingerprint, "stale_plan_association")
    compiler = binding.compiler
    _require(("" if compiler is None else compiler.fingerprint()) == anchors.compiler_fingerprint,
             "stale_compiler_evidence")
    _require(retained is None or type(retained) in (ManagedRetention, NativeRetention), "unsupported_retention")
    _require(("" if retained is None else retained.fingerprint()) == anchors.retention_fingerprint,
             "stale_retained_evidence")
    # Reuse P13.3's passive result/authority/program checks; do not retain its payload.
    projection = inspect_execution(execution, binding, retained=retained)
    native = type(retained) is NativeRetention
    scope = None if retained is None else (retained.pre.scope if native else retained.scope)
    collections = () if retained is None else ((retained.collection,) if native else retained.collections)
    if retained is not None:
        if native:
            receipt = _validate_native(retained, execution)
        else:
            _validate_managed(retained)
    if compiler is not None:
        _require(compiler.mapping.fingerprint() == binding.mapping_fingerprint and
            compiler.scope.air_fingerprint == execution.air_fingerprint and
            compiler.scope.sidecar_fingerprint == binding.association.sidecar_fingerprint and
            compiler.scope.source_mapping_fingerprint == binding.mapping_fingerprint and
            compiler.tam.scope == compiler.scope and compiler.tam.family is TraceFamily.TAM,
            "compiler_evidence_scope_mismatch")
        collections += (compiler.tam,)
    if correlation is not None:
        _require(type(correlation) is CorrelationIndex, "invalid_correlation_evidence")
        correlation.validate_session(session)
        _require(correlation.fingerprint() == anchors.correlation_fingerprint,
                 "stale_correlation_evidence")
        _require(correlation.execution == execution and correlation.source_mapping_fingerprint ==
                 binding.mapping_fingerprint, "correlation_evidence_mismatch")
        expected_assoc = retained.mapping.association if native else binding.association
        _require(correlation.association_fingerprint == expected_assoc.fingerprint() and
                 correlation.sidecar_fingerprint == expected_assoc.sidecar_fingerprint,
                 "correlation_association_mismatch")
        if native:
            _require(all(r.mapping_fingerprint == retained.mapping.fingerprint() for c in correlation.chains
                         for r in c.native.values), "correlation_native_mapping_mismatch")

    if correlation is None:
        _require(anchors.correlation_fingerprint == "", "correlation_evidence_not_supplied")
    nodes, edges = {}, []
    def add(kind, identity, schema, payload=(), scope_id="", local=False):
        reference = EvidenceReference(kind, identity, schema, execution.air_fingerprint,
                                      scope_id, execution.fingerprint() if local else "")
        node = EvidenceNode(reference, available(_public_payload(payload)))
        _require(node.node_id not in nodes or nodes[node.node_id] == node, "conflicting_evidence_projection")
        nodes[node.node_id] = node
        return node.node_id

    def edge(source, target, relation, support):
        edges.append(EvidenceEdge(source, target, relation, support))

    air = add(EvidenceKind.AIR, execution.air_fingerprint, "canonical-air")
    plan = add(EvidenceKind.PLAN, binding.fingerprint(), "apexforge.trace-integration/v1",
               (binding.association.fingerprint(), execution.routing_fingerprint, execution.entry_directive))
    exe = add(EvidenceKind.EXECUTION, execution.fingerprint(), "apexforge.debug-session/v1", local=True)
    edge(plan, air, Relation.ASSOCIATED_WITH, plan)
    edge(plan, exe, Relation.ASSOCIATED_WITH, exe)
    mapping_nodes = {}
    for kind, fp in ((EvidenceKind.AIR_MAPPING, binding.association.sidecar_fingerprint),
                     (EvidenceKind.SOURCE_MAPPING, binding.mapping_fingerprint)):
        if fp:
            mapping_nodes[kind] = add(kind, fp, "apexforge.metadata-identity/v1" if
                kind is EvidenceKind.AIR_MAPPING else "apexforge.source-air-correspondence/v1")
            edge(mapping_nodes[kind], air, Relation.ASSOCIATED_WITH, plan)
    if compiler is not None:
        for source in compiler.mapping.sidecar.sources:
            src = add(EvidenceKind.SOURCE, source.fingerprint(), "apexforge.metadata-identity/v1",
                      source.canonical_identity())
            edge(src, mapping_nodes[EvidenceKind.SOURCE_MAPPING], Relation.ASSOCIATED_WITH,
                 mapping_nodes[EvidenceKind.SOURCE_MAPPING])
    result_ids = ()
    association_node = None
    if retained is not None:
        scope_node = add(EvidenceKind.SCOPE, scope.fingerprint(), scope.schema,
            tuple((name, getattr(scope, name)) for name in scope.__dataclass_fields__), scope.fingerprint())
        edge(scope_node, exe, Relation.BELONGS_TO_EXECUTION, exe)
        edge(scope_node, plan, Relation.ASSOCIATED_WITH, scope_node)
        result = add(EvidenceKind.RESULT, projection.result.value[2], "canonical-native-result" if native else
                     "apexforge.trace-integration/v1", scope_id=scope.fingerprint(), local=True)
        result_ids = (result,)
        edge(result, exe, Relation.BELONGS_TO_EXECUTION, exe)
        association_node = add(EvidenceKind.RESULT_ASSOCIATION, retained.post.fingerprint() if native else
            retained.fingerprint(), "apexforge.trace-retention/v1" if native else
            "apexforge.trace-integration/v1", scope_id=scope.fingerprint(), local=True)
        edge(result, association_node, Relation.RETAINED_BY, association_node)
        edge(association_node, scope_node, Relation.ASSOCIATED_WITH, association_node)
        if native:
            nm = add(EvidenceKind.NATIVE_MAPPING, retained.mapping.fingerprint(),
                     "apexforge.native-generated-source-mapping/v1")
            mapping_nodes[EvidenceKind.NATIVE_MAPPING] = nm
            native_sidecar = add(EvidenceKind.AIR_MAPPING, retained.mapping.sidecar.fingerprint(),
                                 "apexforge.metadata-identity/v1")
            edge(nm, native_sidecar, Relation.ASSOCIATED_WITH, scope_node)
            artifact = add(EvidenceKind.ARTIFACT, retained.post.image_fingerprint, "native-image/sha256")
            build_receipt = add(EvidenceKind.BUILD_RECEIPT, retained.post.receipt_fingerprint,
                               "native-backend-build-receipt", ("build_receipt_reused_as_result_input",))
            edge(nm, air, Relation.ASSOCIATED_WITH, scope_node)
            edge(build_receipt, artifact, Relation.ASSOCIATED_WITH, build_receipt)
            edge(build_receipt, nm, Relation.ASSOCIATED_WITH, scope_node)
            edge(association_node, build_receipt, Relation.ASSOCIATED_WITH, association_node)
            edge(association_node, artifact, Relation.ASSOCIATED_WITH, association_node)
            edge(result, build_receipt, Relation.ASSOCIATED_WITH, association_node)

    # Canonical alternatives are definitions, not observations of activation.
    paths = {}
    program = binding.verified.program
    for decision in program.causal_decisions:
        did = add(EvidenceKind.CAUSAL_DECISION, _digest(_form("decision", (execution.air_fingerprint, decision.id))),
            "canonical-causal-air", (decision.id, decision.cause, decision.policy,
                tuple(d.id for d in program.directives if decision.id in d.causal_decisions)))
        for path in decision.paths:
            pid = add(EvidenceKind.CAUSAL_PATH, _digest(_form("path", (execution.air_fingerprint, decision.id, path.id))),
                "canonical-causal-air", (decision.id, path.id, path.weight))
            paths[(decision.id, path.id)] = pid
            edge(did, pid, Relation.DEFINES_PATH, air)

    family_order, record_nodes = [], {}
    for collection in collections:
        _require(type(collection) is TraceCollection, "unsupported_trace_collection")
        scoped = scope is not None and collection.scope == scope
        coll = add(EvidenceKind.TRACE_FAMILY, collection.fingerprint(), collection.scope.schema,
                   (collection.family.value, collection.unresolved_tam_links), collection.scope.fingerprint(), scoped)
        collection_scope = add(EvidenceKind.SCOPE, collection.scope.fingerprint(), collection.scope.schema,
            tuple((name, getattr(collection.scope, name)) for name in collection.scope.__dataclass_fields__),
            collection.scope.fingerprint())
        edge(coll, collection_scope, Relation.ASSOCIATED_WITH, coll)
        if scoped:
            edge(coll, association_node, Relation.RETAINED_BY, association_node)
            edge(result_ids[0], coll, Relation.ASSOCIATED_WITH, association_node)
        elif compiler is not None and collection == compiler.tam:
            edge(coll, mapping_nodes[EvidenceKind.SOURCE_MAPPING], Relation.ASSOCIATED_WITH, coll)
        tam_nodes = {}
        for record in collection.records:
            _require(type(record) is RetainedRecord and record.scope == collection.scope,
                     "trace_scope_mismatch")
            family, producer, payload = _payload(record.evidence)
            kind = EvidenceKind.TAM if family is TraceFamily.TAM else (
                EvidenceKind.AUTHORITY if family is TraceFamily.AUTHORITY else EvidenceKind.TRACE)
            if family is TraceFamily.AUTHORITY:
                payload = inspect_authority(program, record).record()
            if family is TraceFamily.CAUSAL:
                facts = {f.key: f.value for f in record.evidence.record.facts}
                selected = facts.get("selected", facts.get("path"))
                matches = tuple((d.id, p.id) for d in program.causal_decisions for p in d.paths
                    if p.id == selected and ("cause" not in facts or d.cause == facts["cause"]))
                # Match explicit IDs only; do not evaluate weights or pair adjacent records.
                payload += (("canonical_path_association", "available" if len(matches) == 1 else
                             ("ambiguous" if matches else "unavailable"), tuple(sorted(matches))),)
            node = add(kind, record.identity(), producer, payload, record.scope.fingerprint(), scoped)
            record_nodes[(collection.family, collection.scope.fingerprint(), record.ordinal)] = node
            family_order.append((collection.family.value, collection.scope.fingerprint(), record.ordinal, node))
            edge(node, coll, Relation.RETAINED_BY, coll)
            if family is TraceFamily.CAUSAL and len(matches) == 1:
                edge(node, paths[matches[0]], Relation.SELECTED_PATH, node)
            if record.operation is not None:
                _require(compiler is not None, "operation_mapping_unavailable")
                record.operation.validate(record.evidence, record.scope, compiler.mapping)
                op = add(EvidenceKind.AIR_OPERATION, record.operation.operation.operation_id,
                         "apexforge.metadata-identity/v1", (record.operation.operation.canonical_identity(),))
                edge(node, op, Relation.MAPS_TO, node)
            if family is TraceFamily.TAM:
                tam_nodes[record.evidence.record.trace_id] = node
        if collection.family is TraceFamily.TAM:
            for record in collection.records:
                original = record.evidence.record
                for link in original.upstream_trace_ids:
                    if link in tam_nodes:
                        edge(tam_nodes[link], tam_nodes[original.trace_id], Relation.RECORDED_TAM_LINK,
                             tam_nodes[original.trace_id])
                for link in original.downstream_trace_ids:
                    if link in tam_nodes:
                        edge(tam_nodes[original.trace_id], tam_nodes[link], Relation.RECORDED_TAM_LINK,
                             tam_nodes[original.trace_id])
    interleaving = () if retained is None or native else tuple((r.parent_index, r.family.value, r.ordinal,
        record_nodes[(r.family, scope.fingerprint(), r.ordinal)]) for r in retained.interleaving)
    if correlation is not None:
        for chain in correlation.chains:
            op = add(EvidenceKind.AIR_OPERATION, chain.air.operation.operation_id,
                     "apexforge.metadata-identity/v1", (chain.air.operation.canonical_identity(),))
            # Metadata projection can differ in detail from a TAM operation attachment.
            for source in chain.source.values:
                src = add(EvidenceKind.SOURCE, source.document.fingerprint(), "apexforge.metadata-identity/v1",
                          source.document.canonical_identity())
                edge(src, op, Relation.MAPS_TO, mapping_nodes[EvidenceKind.SOURCE_MAPPING])
            for region in chain.native.values:
                node = add(EvidenceKind.NATIVE_REGION, region.fingerprint(), SCHEMA,
                           (region.canonical_form(),))
                _require(EvidenceKind.NATIVE_MAPPING in mapping_nodes, "native_region_provenance_unavailable")
                edge(op, node, Relation.MAPS_TO, mapping_nodes[EvidenceKind.NATIVE_MAPPING])

    graph = EvidenceGraph(tuple(nodes.values()), tuple(edges))
    coverage = missing("trace_coverage_not_supplied") if retained is None else (
        available(("native_evidence_only",)) if native else available(retained.unsupported))
    execution_receipt = missing("distinct_execution_receipt_not_retained", FieldAvailability.UNSUPPORTED)
    if redacted:
        # Conservative whole-view redaction: content hashes can leak low-entropy
        # secrets too. Keep shape/relations, replace all producer-derived IDs.
        # Stable producer insertion order within kind, never a rank of secret hashes.
        ordered = sorted(nodes.values(), key=lambda n: n.reference.kind.value)
        replacements, safe_nodes = {}, []
        for ordinal, node in enumerate(ordered):
            ref = EvidenceReference(node.reference.kind, "redacted-slot:" + str(ordinal), SCHEMA)
            safe = EvidenceNode(ref, missing("evidence_payload_redacted", FieldAvailability.REDACTED))
            replacements[node.node_id] = safe.node_id
            safe_nodes.append(safe)
        graph = EvidenceGraph(tuple(safe_nodes), tuple(EvidenceEdge(replacements[e.source], replacements[e.target],
            e.relation, replacements[e.support]) for e in graph.edges))
        result_ids = tuple(replacements[i] for i in result_ids)
        family_order = tuple((family, "redacted-scope", ordinal, replacements[node])
                             for family, _, ordinal, node in family_order)
        interleaving = tuple((parent, family, ordinal, replacements[node])
                             for parent, family, ordinal, node in interleaving)
        coverage = missing("evidence_coverage_redacted", FieldAvailability.REDACTED)
        execution_receipt = missing("evidence_receipt_redacted", FieldAvailability.REDACTED)
    return EvidenceView(anchors, graph, result_ids, tuple(family_order), interleaving,
                        coverage, execution_receipt, redacted, timestamp)
