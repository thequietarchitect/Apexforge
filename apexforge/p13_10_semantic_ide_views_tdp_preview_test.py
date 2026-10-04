"""Portable semantic views over existing controlled P13 evidence fixtures."""
import ast
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tooling.debug_views import (build_views, tdp_preview, ViewError, ResourceInput,
                                ROLES, SECTIONS)
from tooling.debug_cli import DebuggerCLI, Mode
from tooling.debug_inspection import available, missing
from tooling.debug_replay import ReplayHistory, OrderingDomain
from tooling.debug_evidence import build_evidence_view, Relation
from tooling.resource_observability import ResourceOwnership, ResourceClass, OwnershipEvidence, EvidenceStatus
from p13_4_source_air_native_correlation_step_planning_test import position
from p13_4_source_air_native_correlation_step_planning_test import source_inputs, source_index
from tooling.debug_metadata import EvidenceReference
from air.verify import AIRVerifier
from tooling.trace_integration import associate_plan, execute_managed_retained
from p12_5_native_profile_contract_test import plan_for
from p13_5_tam_causal_trace_provenance_inspection_test import guards, anchors
import p13_5_tam_causal_trace_provenance_inspection_test as evidence_fixture
import p13_7_cli_debugger_test as fixtures


class ViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.CLITests.setUpClass()
        cls.fixture = fixtures.CLITests()

    def retained(self, **kwargs):
        return self.fixture.retained(**kwargs)

    def bundle(self, **kwargs):
        return build_views(self.retained(**kwargs)[2])

    def mapped(self):
        owner, _, app = self.retained()
        binding, retained = fixtures.CLITests.managed
        helper = evidence_fixture.EvidenceTests()
        helper.native = None
        index = helper.correlation(owner, binding, retained)
        anchor = replace(anchors(owner, binding, retained), correlation_fingerprint=index.fingerprint())
        view = build_evidence_view(owner.session, binding, anchor,
                                   retained=retained, correlation=index)
        app = DebuggerCLI(owner=owner, history=ReplayHistory(view, app.inspection),
                          correlation=index, position=position(index))
        return app, build_views(app)

    def test_deterministic_overview_and_identity_separation(self):
        owner, _, app = self.retained()
        app.owner = owner
        bundle = build_views(app)
        overview = bundle.view("overview")
        context = json.loads(overview.context)
        self.assertEqual(context["session"], owner.session.reference.session_id)
        self.assertEqual(context["execution"], owner.session.execution.execution_id)
        self.assertNotEqual(overview.view_id, context["execution"])
        values = {n.label: json.loads(n.payload) for n in overview.nodes}
        self.assertEqual(values["LIVE_RUNTIME_CONTROL"], "UNAVAILABLE")
        self.assertEqual(values["CAPABILITIES"], sorted(app.capabilities))
        self.assertEqual(bundle.canonical_form(), build_views(app).canonical_form())

    def test_state_order_types_readonly(self):
        _, _, app = self.retained()
        state = build_views(app).view("state")
        self.assertEqual([n.label for n in state.nodes], [e.key for e in app.inspection.state.entries])
        self.assertTrue(all(json.loads(n.payload)["type"] for n in state.nodes))
        self.assertTrue(all(json.loads(n.payload)["presentationHint"]["attributes"] == ["readOnly"] for n in state.nodes))
        self.assertTrue(state.record()["readOnly"])

    def test_unavailable_values_explicit(self):
        _, _, history = fixtures.replay_fixture.observe(fixtures.CLITests.managed[0], None)
        state = build_views(DebuggerCLI(history=history)).view("state")
        self.assertTrue(all(n.availability == "unavailable" for n in state.nodes))
        self.assertTrue(all(json.loads(n.payload)["value"] == "<unavailable>" for n in state.nodes))

    def test_directive_plan_and_correlation_context_supplied(self):
        _, _, app = self.retained()
        view = build_views(app).view("directive")
        plan = next(n for n in view.nodes if n.label == "PLAN")
        self.assertEqual(json.loads(plan.payload), json.loads(json.dumps(app.inspection.plan.record())))
        self.assertIn("Directive Context", view.title)

    def test_authority_graphs_stay_separate_and_no_grants(self):
        owner, _, app = self.retained()
        app.owner = owner
        bundle = build_views(app)
        program, debugger = bundle.view("program_authority"), bundle.view("debugger_authority")
        self.assertNotEqual(program.view_id, debugger.view_id)
        self.assertEqual(program.edges, ())
        self.assertEqual(debugger.edges, ())
        self.assertIn("PRINCIPAL", [n.label for n in program.nodes])
        nodes = {n.label: json.loads(n.payload) for n in debugger.nodes}
        self.assertEqual(nodes["SESSION_PRINCIPAL"], owner.session.reference.principal_id)
        self.assertIn("capability_is_not_authorization", nodes["CONTROL_AUTHORIZATION"])

    def test_mapped_source_air_non_native_and_no_machine_address(self):
        app, bundle = self.mapped()
        nodes = {n.label: json.loads(n.payload) for n in bundle.view("correlation").nodes}
        self.assertEqual(nodes["SOURCE"][0], "available")
        self.assertEqual(nodes["AIR"][0], "available")
        self.assertEqual(nodes["GENERATED_NATIVE_REGION"][0], "not_applicable")
        self.assertEqual(nodes["MACHINE_ADDRESS"], "unsupported")

    def test_handbuilt_native_source_unavailable_and_region_available(self):
        _, _, app = self.fixture.planned(native=True)
        nodes = {n.label: json.loads(n.payload) for n in build_views(app).view("correlation").nodes}
        self.assertEqual(nodes["SOURCE"][0], "unavailable")
        self.assertEqual(nodes["GENERATED_NATIVE_REGION"][0], "available")
        self.assertEqual(nodes["MACHINE_ADDRESS"], "unsupported")

    def test_ambiguous_source_mapping_preserved(self):
        mapping = source_inputs()[-1]
        original = mapping.sidecar
        first = next(e for e in original.evidence if e.operation_id == original.operations[0].operation_id)
        extra = EvidenceReference(original.operations[1].operation_id, first.source_index, first.source_map_index)
        evidence = tuple(sorted(original.evidence + (extra,), key=lambda e: (e.operation_id, e.source_index, e.source_map_index)))
        owner, index, _ = source_index(replace(original, evidence=evidence))
        app = DebuggerCLI(owner=owner, correlation=index, position=position(index, 1))
        view = build_views(app).view("correlation")
        source = next(json.loads(n.payload) for n in view.nodes if n.label == "SOURCE")
        self.assertEqual(source[0], "ambiguous")
        self.assertEqual(len(source[1]), 2)

    def test_evidence_nodes_and_edges_exactly_from_supplied_graph(self):
        _, _, app = self.retained()
        view = build_views(app).view("evidence")
        graph = app.history.evidence.graph
        self.assertEqual({n.view_id for n in view.nodes}, {"view:evidence:" + n.node_id for n in graph.nodes})
        self.assertTrue(all(n.view_id not in {p.node_id for p in graph.nodes} for n in view.nodes))
        self.assertEqual({(e.source.removeprefix("view:evidence:"), e.target.removeprefix("view:evidence:"), e.relation, e.evidence_reference) for e in view.edges},
                         {(e.source, e.target, e.relation.value, e.support) for e in graph.edges})

    def test_provenance_graph_partial_chains_not_attribution(self):
        bundle = self.bundle()
        provenance = bundle.view("provenance")
        self.assertEqual([(e.source.removeprefix("view:provenance:"), e.target.removeprefix("view:provenance:"), e.relation) for e in provenance.edges],
                         [(e.source.removeprefix("view:evidence:"), e.target.removeprefix("view:evidence:"), e.relation) for e in bundle.view("evidence").edges])
        self.assertIn("PARTIAL_CHAINS_VALID", provenance.limitations)
        self.assertIn("ACTOR_ATTRIBUTION_NOT_INFERRED", provenance.limitations)

    def test_causal_selection_recorded_no_root_cause(self):
        _, _, history = fixtures.replay_fixture.observe(*fixtures.CLITests.causal[0])
        app = DebuggerCLI(history=history)
        view = build_views(app).view("causal")
        self.assertTrue(view.nodes)
        original = {(e.source, e.target, e.relation.value, e.support) for e in history.evidence.graph.edges}
        self.assertTrue(all((e.source.removeprefix("view:causal:"), e.target.removeprefix("view:causal:"), e.relation, e.evidence_reference) in original for e in view.edges))
        self.assertIn("CAUSAL_EVIDENCE_NOT_ROOT_CAUSE", view.limitations)

    def test_causal_occurrence_ambiguity_preserved_not_selected_by_view(self):
        original = fixtures.CLITests.causal[0][0].verified.program
        first = original.causal_decisions[0]
        second = replace(first, id="decision:other")
        directive = replace(original.directives[0], causal_decisions=(first.id, second.id))
        program = replace(original, directives=(directive,), causal_decisions=(first, second))
        verified = AIRVerifier().verify(program).require_verified()
        binding = associate_plan(verified, plan_for(program))
        retained = execute_managed_retained(binding)
        _, _, history = fixtures.replay_fixture.observe(binding, retained)
        with guards():
            view = build_views(DebuggerCLI(history=history)).view("causal")
        causal = [n for n in view.nodes if "canonical_path_association" in n.payload]
        self.assertTrue(causal)
        self.assertTrue(all("ambiguous" in n.payload for n in causal))
        self.assertFalse(any(e.relation == "selected_path" for e in view.edges))

    def test_trace_stream_timeline_recorded_order_not_live_position(self):
        _, _, app = self.retained()
        view = build_views(app).view("timeline")
        self.assertEqual(view.ordering, "trace_stream_order")
        self.assertEqual([json.loads(n.payload)["sequence"] for n in view.nodes], list(range(len(view.nodes))))
        self.assertTrue(all(json.loads(n.payload)["domain"] == view.ordering for n in view.nodes))
        self.assertIn("REPLAY_POSITION_NOT_LIVE_EXECUTION_POSITION", view.limitations)
        self.assertIsNone(app.cursor)

    def test_trace_family_and_unavailable_semantic_order_distinct(self):
        _, _, app = self.retained(native=True)
        family = build_views(app).view("timeline")
        self.assertEqual(family.ordering, "trace_family_order")
        app.replay_domain = OrderingDomain.SEMANTIC_ORDER
        semantic = build_views(app).view("timeline")
        self.assertEqual(semantic.ordering, "semantic_order")
        self.assertEqual(semantic.availability, "unavailable")
        self.assertEqual(semantic.nodes, ())

    def test_comparison_domains_and_volatile_separation(self):
        _, _, app = self.retained(divergent=True)
        app.history = replace(app.history, volatile=(("pid", 123),))
        view = build_views(app).view("comparison")
        values = [(n.label, json.loads(n.payload)) for n in view.nodes]
        self.assertTrue(any(label == "COMPARISON" and value[1] == "state_divergence" for label, value in values))
        self.assertTrue(any(label == "VOLATILE_DIFFERENCES" for label, value in values))
        self.assertIn(("CAUSAL_EXPLANATION", "not_inferred"), values)

    def test_volatile_only_does_not_change_other_views(self):
        _, _, app = self.retained()
        before = build_views(app)
        app.history = replace(app.history, timestamp="later", volatile=(("pid", 77),))
        after = build_views(app)
        for kind in ("overview", "state", "provenance", "timeline"):
            self.assertEqual(before.view(kind).canonical_form(), after.view(kind).canonical_form())
        domains = [json.loads(n.payload) for n in after.view("comparison").nodes if n.label == "COMPARISON"]
        self.assertFalse(any(d[1].endswith("_divergence") for d in domains))

    def test_step_plans_prominent_even_if_unavailable(self):
        for mode, native in (("semantic", False), ("source", False), ("native-correlation", True)):
            _, fake, app = self.fixture.planned(native=native)
            view = build_views(app, step_mode=mode).view("step_plan")
            values = {n.label: json.loads(n.payload) for n in view.nodes}
            self.assertIs(values["STEP_PLAN_ONLY"], True)
            self.assertEqual(values["REQUESTED_MODE"], mode)
            self.assertIn("STEP_PLAN_NOT_EXECUTION_ADVANCEMENT", view.limitations)
            if fake is not None:
                self.assertEqual(fake.consumed, [])
        unavailable = self.bundle().view("step_plan")
        self.assertEqual(unavailable.availability, "unavailable")
        self.assertTrue(json.loads(unavailable.nodes[0].payload))

    def resource(self, app, bound=True):
        known = lambda s: OwnershipEvidence(EvidenceStatus.KNOWN, s)
        owner = ResourceOwnership("retained-evidence", ResourceClass.SHR, known("producer"),
            known("inspection"), known("capture"), known("retention-contract"), known("explicit-release"))
        return ResourceInput(app.history.evidence.binding.execution, owner,
                             available("supplied-provenance-binding") if bound else missing("binding_not_supplied"),
                             missing("cleanup_not_observed"))

    def test_resource_custody_and_cleanup_not_inferred(self):
        _, _, app = self.retained()
        resource = self.resource(app)
        view = build_views(app, resources=(resource,)).view("resources")
        data = json.loads(view.nodes[0].payload)
        self.assertEqual(data["custody"][1], "SHR")
        self.assertEqual(data["cleanup"][0], "unavailable")
        self.assertEqual(data["mscRole"], "RESOURCE_CONTINUITY_ANALYTICAL_LENS")
        self.assertIn("RETAINED_RESOURCE_REQUIRES_OWNER_PURPOSE_LIFETIME_VALID_BINDING", view.limitations)
        partial = build_views(app, resources=(self.resource(app, False),)).view("resources")
        self.assertEqual(partial.nodes[0].availability, "partial")
        second = replace(resource, ownership=replace(resource.ownership, scope="other-retained-evidence"))
        self.assertEqual(build_views(app, resources=(resource, second)).canonical_form(),
                         build_views(app, resources=(second, resource)).canonical_form())
        tied = replace(resource, binding=available("other-supplied-binding"), cleanup=available("supplied-release-evidence"))
        self.assertEqual(build_views(app, resources=(resource, tied)).canonical_form(),
                         build_views(app, resources=(tied, resource)).canonical_form())

    def test_resource_cross_execution_rebinding_rejected(self):
        _, _, app = self.retained()
        resource = self.resource(app)
        wrong = replace(resource, execution=replace(resource.execution, execution_id="execution:other"))
        with self.assertRaisesRegex(ViewError, "resource_execution_mismatch"):
            build_views(app, resources=(wrong,))

    def test_navigation_links_exact_existing_support_and_state_air(self):
        app, bundle = self.mapped()
        graph = app.history.evidence.graph
        original = {(e.source, e.target, e.support) for e in graph.edges}
        self.assertTrue(all((d["source"], d["target"], d["support"]) in original
            for d in (json.loads(n.payload) for n in bundle.view("navigation").nodes)))
        self.assertTrue(any(e.relation is Relation.MAPS_TO for e in graph.edges))
        self.assertTrue(any(graph.node(e.source).reference.kind.value == "execution-result" for e in graph.edges))
        state_air = bundle.view("state_air")
        self.assertEqual([json.loads(n.payload) for n in state_air.nodes],
                         json.loads(json.dumps([e.source_air.record() for e in app.inspection.state.entries])))

    def test_immutable_docs_and_detached_json_copies(self):
        bundle = self.bundle()
        with self.assertRaises(FrozenInstanceError):
            bundle.documents = ()
        with self.assertRaises(FrozenInstanceError):
            bundle.view("state").nodes[0].payload = "secret"
        copy = bundle.view("state").record()
        copy["nodes"].clear()
        self.assertTrue(bundle.view("state").nodes)

    def test_serialization_schema_and_stable_equivalent_inputs(self):
        a, b = self.bundle(), self.bundle()
        self.assertEqual(a, b)
        self.assertEqual(a.canonical_form(), b.canonical_form())
        self.assertEqual(json.loads(a.canonical_form())["schema"], "apexforge.debug-views/v1")
        self.assertTrue(all(d.record()["readOnly"] for d in a.documents))

    def test_redacted_sentinel_absent_every_view_preview_repr_and_hash(self):
        _, _, hidden = fixtures.replay_fixture.observe(*fixtures.CLITests.sensitive, redacted=True)
        _, _, visible = fixtures.replay_fixture.observe(*fixtures.CLITests.sensitive)
        app = DebuggerCLI(history=ReplayHistory(hidden.evidence, visible.inspection), comparison=hidden)
        bundle = build_views(app)
        output = bundle.canonical_form() + tdp_preview(bundle).canonical_form() + repr(bundle)
        self.assertNotIn("PRIVATE_CLI_SENTINEL_73", output)
        self.assertNotIn(fixtures.CLITests.sensitive[1].result_fingerprint, output)
        self.assertNotIn(fixtures.CLITests.sensitive[1].context.state_fingerprint, output)
        self.assertTrue(all(n.availability == "redacted" for n in bundle.view("state").nodes))
        for kind in ("evidence", "provenance", "causal", "timeline"):
            self.assertEqual(bundle.view(kind).availability, "redacted")
            self.assertEqual(bundle.view(kind).nodes, ())

    def test_tdp_section_order_and_deterministic_composition(self):
        bundle = self.bundle()
        preview = tdp_preview(bundle)
        self.assertEqual([s[0] for s in preview.sections], [s[0] for s in SECTIONS])
        self.assertEqual(preview.canonical_form(), tdp_preview(bundle).canonical_form())
        ids = {d.view_id for d in bundle.documents}
        self.assertTrue(all(ref in ids for s in preview.sections for ref in s[3]))

    def test_tdp_live_monitor_retained_not_continuous(self):
        sections = {s[0]: s for s in tdp_preview(self.bundle()).sections}
        self.assertIn("not_continuous_telemetry", sections["Live Monitor"][2])
        self.assertEqual(sections["Overview"][1], "partial")
        self.assertIn("not_system_security_health", sections["System Health"][2])

    def test_tdp_provider_panels_deferred_no_synthetic_metrics(self):
        preview = tdp_preview(self.bundle())
        sections = {s[0]: s for s in preview.sections}
        for name in ("Transvergent Analytics", "Mosaic / FAME", "Varenic Trajectories", "Policy & Throttle", "Simulation"):
            self.assertEqual(sections[name][1], "deferred_to_tdp_domain")
            self.assertEqual(sections[name][3], ())
        self.assertEqual(sections["Transvergent Analytics"][2], "DEFERRED_TDP_TELEMETRY_PROVIDER")
        self.assertIn("no_containment", sections["Incidents & Containment"][2])
        self.assertIn("no_remediation", sections["Medic Lab"][2])
        data = json.loads(preview.canonical_form())
        self.assertFalse(data["operational"])
        self.assertFalse(data["liveTelemetry"])

    def test_tdp_roles_authorities_and_attribution_distinct(self):
        preview = tdp_preview(self.bundle())
        self.assertEqual(preview.roles, ROLES)
        self.assertEqual(len({name for name, role in preview.roles}), 5)
        data = json.loads(preview.canonical_form())
        self.assertTrue(data["evidenceBeforeAttribution"])
        self.assertEqual(data["actorAttribution"], "not_inferred")

    def test_views_do_not_mutate_sessions_producers_or_replay_cursor(self):
        owner, fake, app = self.retained(native=True)
        before = owner.session.canonical_form(), app.history.canonical_form(), app.cursor
        with guards():
            bundle = build_views(app)
            tdp_preview(bundle)
        self.assertEqual(before, (owner.session.canonical_form(), app.history.canonical_form(), app.cursor))
        self.assertEqual(fake.consumed, [])

    def test_closed_live_session_rejected_retained_supported(self):
        owner, _, app = self.retained()
        live = DebuggerCLI(mode=Mode.LIVE, owner=owner, history=app.history)
        owner.begin_close()
        owner.finish_close()
        with self.assertRaisesRegex(ViewError, "session_binding_unavailable"):
            build_views(live)
        self.assertTrue(build_views(app).view("evidence").nodes)

    def test_session_and_execution_labels_cannot_rebind_material(self):
        owner, _, app = self.retained()
        from p13_2_debug_session_control_foundation_test import fixture
        wrong, _ = fixture(target=owner.session.execution, session_id="session:wrong")
        app.owner = wrong
        with self.assertRaisesRegex(ViewError, "view_session_mismatch"):
            build_views(app)
        different, _, other = self.retained(divergent=True)
        # Use an actual other execution reference, not matching-looking labels.
        target = other.comparison.evidence.binding.execution
        wrong, _ = fixture(target=target, session_id=owner.session.reference.session_id)
        app.owner = wrong
        with self.assertRaisesRegex(ViewError, "view_execution_mismatch"):
            build_views(app)

    def test_static_execution_host_mutation_separation(self):
        tree = ast.parse((ROOT / "apexforge/tooling/debug_views.py").read_text())
        forbidden = {"execute", "run_air_program", "dispatch_native", "build_native", "allows", "select_path",
                     "Popen", "eval", "exec", "system", "deliver", "open", "read_bytes", "write_bytes",
                     "submit", "begin_close", "finish_close", "inventory_artifacts", "observe_current_process"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [node.module] if isinstance(node, ast.ImportFrom) else [n.name for n in node.names]
                self.assertFalse(set(names) & {"subprocess", "os", "runtime.engine", "authority.engine", "workflow.air_runner"})
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                self.assertNotIn(name, forbidden)


if __name__ == "__main__":
    unittest.main()
