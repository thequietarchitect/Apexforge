"""P13.10 portable read-only presentation documents and TDP preview contracts.

Embedding owners supply authorized P13 material. No UI registration, telemetry,
policy, execution, causal inference or producer evidence creation occurs here.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from tooling.debug_cli import DebuggerCLI, Mode
from tooling.debug_dap import DAPAdapter, text
from tooling.debug_inspection import InspectionField, available
from tooling.debug_evidence import EvidenceKind as K
from tooling.debug_replay import build_replay, ReplayMode
from tooling.debug_session import ExecutionReference
from tooling.resource_observability import ResourceOwnership

SCHEMA = "apexforge.debug-views/v1"
STATUSES = ("available", "partial", "unavailable", "unsupported", "not_applicable", "redacted", "ambiguous")
LIMITS = ("VIEW_NOT_SEMANTIC_OBJECT", "EVIDENCE_BEFORE_ATTRIBUTION",
          "ACTOR_ATTRIBUTION_NOT_INFERRED", "LIVE_RUNTIME_CONTROL_UNAVAILABLE")


class ViewError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise ViewError(code)


@dataclass(frozen=True)
class ViewNode:
    view_id: str
    kind: str
    label: str
    availability: str
    reference: str
    payload: str

    def __post_init__(self):
        require(all(type(x) is str for x in (self.view_id, self.kind, self.label,
                self.availability, self.reference, self.payload)), "invalid_view_node")
        require(self.availability in STATUSES, "invalid_view_availability")
        require(text(json.loads(self.payload)) == self.payload, "noncanonical_view_payload")

    def record(self):
        return dict(id=self.view_id, kind=self.kind, label=self.label,
                    availability=self.availability, reference=self.reference,
                    data=json.loads(self.payload))


@dataclass(frozen=True)
class ViewEdge:
    source: str
    target: str
    relation: str
    evidence_reference: str

    def __post_init__(self):
        require(all(type(x) is str and x for x in (self.source, self.target, self.relation,
                                                  self.evidence_reference)), "invalid_view_edge")

    def record(self):
        return dict(source=self.source, target=self.target, relation=self.relation,
                    evidenceReference=self.evidence_reference)


@dataclass(frozen=True)
class ViewDocument:
    kind: str
    title: str
    context: str
    availability: str
    nodes: tuple[ViewNode, ...] = ()
    edges: tuple[ViewEdge, ...] = ()
    ordering: str = "presentation_order"
    limitations: tuple[str, ...] = LIMITS

    def __post_init__(self):
        require(all(type(x) is str for x in (self.kind, self.title, self.context,
                self.availability, self.ordering)), "invalid_view_document")
        require(text(json.loads(self.context)) == self.context, "noncanonical_view_context")
        require(type(self.nodes) is tuple and all(type(n) is ViewNode for n in self.nodes)
            and type(self.edges) is tuple and all(type(e) is ViewEdge for e in self.edges), "immutable_view_required")
        require(self.availability in STATUSES and type(self.limitations) is tuple,
                "invalid_view_document")
        require(all(type(x) is str for x in self.limitations), "immutable_limitations_required")
        ids = {n.view_id for n in self.nodes}
        require(len(ids) == len(self.nodes), "duplicate_view_id")
        require(all(e.source in ids and e.target in ids for e in self.edges), "dangling_view_edge")

    @property
    def view_id(self):
        return "view:" + self.kind

    def record(self):
        return dict(schema=SCHEMA, viewId=self.view_id, kind=self.kind, title=self.title,
            context=json.loads(self.context), availability=self.availability,
            nodes=[n.record() for n in self.nodes], edges=[e.record() for e in self.edges],
            ordering=self.ordering, limitations=self.limitations, readOnly=True)

    def canonical_form(self):
        return text(self.record())


@dataclass(frozen=True)
class ResourceInput:
    """Supplied custody evidence, not a new resource owner or authority check."""
    execution: ExecutionReference
    ownership: ResourceOwnership
    binding: InspectionField
    cleanup: InspectionField

    def __post_init__(self):
        require(type(self.execution) is ExecutionReference and type(self.ownership) is ResourceOwnership
            and type(self.binding) is InspectionField and type(self.cleanup) is InspectionField,
            "invalid_resource_evidence")


@dataclass(frozen=True)
class ViewBundle:
    documents: tuple[ViewDocument, ...]

    def __post_init__(self):
        require(type(self.documents) is tuple and all(type(d) is ViewDocument for d in self.documents)
            and len({d.kind for d in self.documents}) == len(self.documents), "invalid_view_bundle")

    def view(self, kind):
        found = tuple(d for d in self.documents if d.kind == kind)
        require(len(found) == 1, "view_unavailable")
        return found[0]

    def canonical_form(self):
        return text(dict(schema=SCHEMA, documents=[d.record() for d in self.documents]))


def _node(kind, index, label, value, status="available", reference=""):
    return ViewNode(kind + ":" + str(index), kind, label, status, reference, text(value))


class _Projection:
    """Private serial DAP projection; no transport, live control or cursor changes."""
    def __init__(self, app):
        self.adapter = DAPAdapter(app)
        self.sequence = 0
        self.ask("initialize")
        bound = self.ask("attach" if app.mode is Mode.LIVE else "launch",
                         mode="supplied-session" if app.mode is Mode.LIVE else "retained")
        require(bound is not None, "session_binding_unavailable")
        require(self.ask("configurationDone") is not None, "session_binding_unavailable")

    def ask(self, command, **args):
        self.sequence += 1
        response = self.adapter.handle(dict(seq=self.sequence, type="request", command=command, arguments=args))[0]
        return response["body"] if response["success"] else None


def build_views(application, *, resources=(), step_mode="semantic"):
    """Project a supplied client into detached immutable documents.

    Observational replay constructs a timeline, never moves the client's cursor.
    Resource binding is supplied evidence, not authentication or authority.
    """
    require(type(application) is DebuggerCLI, "invalid_view_input")
    require(type(resources) is tuple and all(type(r) is ResourceInput for r in resources), "immutable_resources_required")
    require(step_mode in ("semantic", "source", "native-correlation"), "unsupported_step_plan")
    app = application
    projection = _Projection(app)
    try:
        # Session and execution identities are references, never view IDs.
        execution = app.inspection.execution if app.inspection is not None else (
            app.history.evidence.binding.execution if app.history is not None else
            app.correlation.execution if app.correlation is not None else
            app.owner.session.execution if app.owner is not None else None)
        sessions = tuple(s for s in (
            None if app.owner is None else app.owner.session.reference,
            None if app.history is None else app.history.evidence.binding.session,
            None if app.correlation is None else app.correlation.session) if s is not None)
        require(not sessions or all(s == sessions[0] for s in sessions), "view_session_mismatch")
        executions = tuple(e for e in (
            None if app.owner is None else app.owner.session.execution,
            None if app.history is None else app.history.evidence.binding.execution,
            None if app.correlation is None else app.correlation.execution) if e is not None)
        require(all(e == execution for e in executions), "view_execution_mismatch")
        require(all(r.execution == execution for r in resources), "resource_execution_mismatch")
        context = text({"mode": app.mode.value, "session": "redacted" if app.redacted else
            sessions[0].session_id if sessions else "unavailable",
            "execution": "redacted" if app.redacted else execution.execution_id if execution else "unavailable"})
        docs = []

        def document(kind, title, nodes=(), edges=(), status="available", ordering="presentation_order", extra=()):
            result = ViewDocument(kind, title, context, status, tuple(nodes), tuple(edges), ordering, LIMITS + extra)
            docs.append(result)
            return result

        def rows(kind, title, command, **args):
            body = projection.ask(command, **args)
            if body is None:
                return document(kind, title, status="unavailable")
            values = body.get("rows", ())
            return document(kind, title, [_node(kind, i, r["label"], r["value"],
                "redacted" if app.redacted else "available") for i, r in enumerate(values)],
                status="redacted" if app.redacted else "available")

        mapping_layers = "redacted" if app.redacted else "unavailable" if app.correlation is None else {
            "SOURCE": tuple((c.air.operation.operation_id, c.source.status.value) for c in app.correlation.chains),
            "AIR": "available", "GENERATED_NATIVE_REGION": tuple((c.air.operation.operation_id, c.native.status.value) for c in app.correlation.chains),
            "MACHINE_ADDRESS": "unsupported"}
        document("overview", "Debugger Overview", (
            _node("overview", 0, "CAPABILITIES", app.capabilities),
            _node("overview", 1, "LIVE_RUNTIME_CONTROL", "UNAVAILABLE"),
            _node("overview", 2, "EVIDENCE", "redacted" if app.redacted else "available" if app.history else "unavailable"),
            _node("overview", 3, "REPLAY", "available" if app.history else "unavailable"),
            _node("overview", 4, "MAPPING", mapping_layers)),
            status="partial")
        supplied = projection.ask("apexforge/inspection")
        scopes = () if supplied is None else supplied["scopes"]
        for kind, title, scope in (("state", "Semantic State", "State"),
            ("directive", "Directive Context", "Directive Context"),
            ("program_authority", "Observed Program Authority", "Observed Program Authority"),
            ("debugger_authority", "Debugger Session Authorization", "Debugger Execution Context")):
            selected = [s for s in scopes if s["name"] == scope]
            body = projection.ask("variables", variablesReference=selected[0]["variablesReference"]) if selected else None
            values = () if body is None else body["variables"]
            projected = [_node(kind, i, v["name"], v,
                "redacted" if app.redacted else "unavailable" if v["value"] == "<unavailable>" else "available")
                for i, v in enumerate(values)]
            if not app.redacted and app.inspection is not None:
                names = ("plan", "correlation") if kind == "directive" else ("principal",) if kind == "program_authority" else ()
                for name in names:
                    item = getattr(app.inspection, name)
                    projected.append(_node(kind, len(projected), name.upper(), item.record(), item.status.value))
            if kind == "debugger_authority" and app.owner is not None:
                projected.append(_node(kind, len(projected), "SESSION_PRINCIPAL",
                    "redacted" if app.redacted else app.owner.session.reference.principal_id,
                    "redacted" if app.redacted else "available"))
                projected.append(_node(kind, len(projected), "CONTROL_AUTHORIZATION",
                    "not_evaluated_by_view; capability_is_not_authorization", "unavailable"))
            document(kind, title, projected, status="unavailable" if body is None else "redacted" if app.redacted else "available")
        rows("correlation", "Source / AIR / Generated Native", "apexforge/correlate", reference="current")

        # Graph projection uses only actual P13.5 relationships, including support.
        graph = None if app.history is None or app.redacted else app.history.evidence.graph
        for kind, title in (("evidence", "Evidence Graph"), ("provenance", "Provenance Graph"), ("causal", "Recorded Causal Evidence")):
            selected = () if graph is None else graph.nodes
            if kind == "causal" and graph is not None:
                causal_ids = {i for f, scope, ordinal, i in app.history.evidence.family_order if f == "causal-selection"}
                selected = tuple(n for n in graph.nodes if n.reference.kind in (K.CAUSAL_DECISION, K.CAUSAL_PATH)
                                 or n.node_id in causal_ids)
            selected = tuple(sorted(selected, key=lambda n: n.node_id))
            ids = {n.node_id for n in selected}
            edges = () if graph is None else tuple(sorted((e for e in graph.edges if e.source in ids and e.target in ids),
                key=lambda e: (e.source, e.relation.value, e.target, e.support)))
            local = lambda reference: "view:" + kind + ":" + reference
            document(kind, title, [ViewNode(local(n.node_id), n.reference.kind.value, n.reference.kind.value,
                n.payload.status.value, n.reference.canonical_form(), text(n.payload.record())) for n in selected],
                [ViewEdge(local(e.source), local(e.target), e.relation.value, e.support) for e in edges],
                status="redacted" if app.redacted else "available" if graph is not None else "unavailable",
                ordering="evidence_reference_order", extra=("CAUSAL_EVIDENCE_NOT_ROOT_CAUSE", "PARTIAL_CHAINS_VALID"))

        records, timeline_status, order = (), "unavailable", app.replay_domain.value
        if app.history is not None:
            timeline = build_replay(app.history, app.replay_domain, family=app.replay_family,
                mode=ReplayMode.LIVE_SESSION_REPLAY if app.mode is Mode.LIVE else ReplayMode.RETAINED_EVIDENCE_REPLAY,
                session=None if app.owner is None else app.owner.session)
            timeline_status = {"complete_retained": "available", "partial": "partial", "redacted": "redacted"}.get(timeline.availability.value, "unavailable")
            records = () if app.redacted else tuple(_node("timeline", r.sequence, r.evidence.reference.kind.value,
                {"sequence": r.sequence, "domain": r.domain.value, "logicalKey": r.logical_key,
                 "evidenceReference": r.evidence.node_id, "availability": r.evidence.payload.status.value},
                r.evidence.payload.status.value, r.evidence.node_id) for r in timeline.records)
        document("timeline", "Retained Observation Timeline", records,
                 status="redacted" if app.redacted else timeline_status, ordering=order,
                 extra=("REPLAY_POSITION_NOT_LIVE_EXECUTION_POSITION", "NO_UNIVERSAL_TIMELINE"))
        rows("comparison", "Comparison Domains", "apexforge/compare", domain="summary")
        plan = rows("step_plan", "Planned Observation Target", "apexforge/planStep", mode=step_mode)
        # Prominent planning-only metadata remains even when no target is available.
        docs[-1] = ViewDocument(plan.kind, plan.title, context, plan.availability,
            (_node("step_plan", -1, "STEP_PLAN_ONLY", True), _node("step_plan", -2, "REQUESTED_MODE", step_mode)) + plan.nodes,
            limitations=LIMITS + ("STEP_PLAN_NOT_EXECUTION_ADVANCEMENT",))

        resource_nodes = () if app.redacted else tuple(_node("resources", i, r.ownership.scope,
            {"custody": r.ownership.canonical_record(), "binding": r.binding.record(),
             "cleanup": r.cleanup.record(), "mscRole": "RESOURCE_CONTINUITY_ANALYTICAL_LENS"},
            "partial" if r.binding.status.value != "available" or any(x.status.value != "known" for x in
                (r.ownership.owner, r.ownership.purpose, r.ownership.intended_lifetime)) else "available")
            for i, r in enumerate(sorted(resources, key=lambda r:
                text((r.ownership.canonical_record(), r.binding.record(), r.cleanup.record())))))
        document("resources", "Resource Continuity", resource_nodes,
            status="redacted" if app.redacted else "unavailable" if not resources else
                "partial" if any(n.availability == "partial" for n in resource_nodes) else "available",
            extra=("RETAINED_RESOURCE_REQUIRES_OWNER_PURPOSE_LIFETIME_VALID_BINDING", "CLEANUP_BOUNDARY_NOT_CLEANUP_PROOF"))

        # Navigation is a presentation of explicit graph associations, not new edges.
        if graph is not None:
            links = tuple(_node("navigation", i, e.relation.value,
                {"source": e.source, "target": e.target, "support": e.support}, reference=e.support)
                for i, e in enumerate(sorted(graph.edges, key=lambda e: (e.source, e.relation.value, e.target, e.support))))
        else:
            links = ()
        document("navigation", "Evidence-Supported Navigation", links,
                 status="redacted" if app.redacted else "available" if graph is not None else "unavailable")
        # State-to-AIR references remain supplied references, never fuzzy links.
        if app.inspection is not None and not app.redacted:
            refs = tuple(_node("state_air", i, e.key, e.source_air.record(), e.source_air.status.value)
                         for i, e in enumerate(app.inspection.state.entries))
            document("state_air", "State / AIR References", refs)
        else:
            document("state_air", "State / AIR References", status="redacted" if app.redacted else "unavailable")
        return ViewBundle(tuple(docs))
    finally:
        projection.adapter.close_projection()


ROLES = (("SENTINEL", "observes/detects"), ("TDP", "evaluates dynamics/response"),
         ("CONTAINMENT", "isolates"), ("MEDIC", "diagnoses/reconstructs"), ("VERIFICATION", "proves recovery"))
SECTIONS = (("Overview", "overview"), ("Live Monitor", "timeline"),
    ("Transvergent Analytics", ""), ("Mosaic / FAME", ""), ("Varenic Trajectories", ""),
    ("Incidents & Containment", "evidence"), ("Medic Lab", "provenance"),
    ("Policy & Throttle", ""), ("Reports", ""), ("Simulation", ""), ("System Health", "overview"))


@dataclass(frozen=True)
class TDPPreview:
    sections: tuple
    roles: tuple = ROLES

    def __post_init__(self):
        require(type(self.sections) is tuple and self.roles == ROLES, "immutable_preview_required")
        available(self.sections)

    def canonical_form(self):
        return text(dict(schema=SCHEMA, kind="tdp_preview", previewOnly=True, operational=False,
            liveTelemetry=False, evidenceBeforeAttribution=True, actorAttribution="not_inferred",
            roles=self.roles, sections=self.sections))


def tdp_preview(bundle):
    require(type(bundle) is ViewBundle, "invalid_preview_input")
    sections = []
    for name, kind in SECTIONS:
        if kind:
            view = bundle.view(kind)
            status = "partial" if view.availability not in ("unavailable", "redacted") else view.availability
            reason = {"Live Monitor": "retained_observations_not_continuous_telemetry",
                "Incidents & Containment": "observations_not_classified_incidents_no_containment",
                "Medic Lab": "evidence_references_only_no_remediation",
                "System Health": "debugger_availability_not_system_security_health"}.get(name, "supplied_debugger_evidence_only")
            refs = (view.view_id,)
        elif name == "Reports":
            status, reason, refs = "available", "serialize_supplied_views_only", tuple(d.view_id for d in bundle.documents)
        else:
            status, reason, refs = "deferred_to_tdp_domain", "DEFERRED_TDP_TELEMETRY_PROVIDER" if name == "Transvergent Analytics" else "DEFERRED_P15_TDP_PROVIDER", ()
        sections.append((name, status, reason, refs))
    return TDPPreview(tuple(sections))
