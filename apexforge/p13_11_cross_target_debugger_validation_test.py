"""P13.11 validation only: execution/evidence targets x presentation targets.

Test adapters decode presentation records; they do not implement semantics.
All real execution happens in controlled fixture setup, never client queries.
"""
import ast
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tooling.debug_cli import DebuggerCLI, Mode
from tooling.debug_dap import text, field_value
from tooling.debug_visualstudio import VisualStudioClient
from tooling.debug_views import build_views, tdp_preview, ResourceInput, ViewError
from tooling.debug_evidence import build_evidence_view, EvidenceKind as K, Relation
from tooling.debug_inspection import missing, available
from tooling.debug_replay import (ReplayHistory, build_replay, ReplayCursor, compare_histories,
                                  ComparisonDomain as D, OrderingDomain as O)
from tooling.debug_correlation import StepMode, plan_next
from tooling.debug_metadata import EvidenceReference
from tooling.resource_observability import ResourceOwnership, ResourceClass, OwnershipEvidence, EvidenceStatus
from tooling.trace_integration import associate_plan, execute_managed_retained
from air.verify import AIRVerifier
from workflow.air_runner import run_air_program
from p12_5_native_profile_contract_test import plan_for
from p12_6_4_source_native_mapping_test import native_fixture
from p12_7_2_bounded_behavioral_equivalence_test import managed_projection, native_projection, require_common_domain
from p13_4_source_air_native_correlation_step_planning_test import position, source_inputs, source_index
from p13_5_tam_causal_trace_provenance_inspection_test import guards, anchors
from p13_2_debug_session_control_foundation_test import fixture as session_fixture
import p13_5_tam_causal_trace_provenance_inspection_test as evidence_fixture
import p13_7_cli_debugger_test as cli_fixture
import p13_8_dap_vscode_debugger_test as dap_fixture


def plain(value):
    return json.loads(text(value))


def clone(app, **changes):
    fields = {name: getattr(app, name) for name in ("mode", "owner", "history", "comparison",
              "inspection", "correlation", "position", "known_order", "replay_domain", "replay_family")}
    fields.update(changes)
    return DebuggerCLI(**fields)


def cli_rows(response):
    if response.code != 0:
        raise AssertionError("CLI projection unavailable: " + response.stderr)
    return [(line.split("=", 1)[0], json.loads(line.split("=", 1)[1]))
            for line in response.stdout.splitlines()]


def body_rows(body):
    return [(r["label"], r["value"]) for r in body["rows"]]


class Surfaces:
    """Independent presentation cursors over exactly the same supplied anchors."""
    def __init__(self, app):
        self.app = app
        self.cli = clone(app)
        self.dap = dap_fixture.Connection(clone(app))
        self.dap.start(live=app.mode is Mode.LIVE)
        self.vs = VisualStudioClient(clone(app))
        result = self.vs.connect()
        if not result.success:
            raise AssertionError(result.code)
        self.views = build_views(clone(app))

    def dap_body(self, command, **args):
        response = self.dap.ask(command, **args)[0]
        if not response["success"]:
            raise AssertionError(response["message"])
        return response["body"]

    def vs_body(self, command, **args):
        response = self.vs.command(command, **args)
        if not response.success:
            raise AssertionError(response.code)
        return response.view()


class CrossTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cli_fixture.CLITests.setUpClass()
        cls.fixtures = cli_fixture.CLITests()
        cls.generated = native_fixture()[2]
        # One already-admitted common-domain program, using existing owners only.
        binding, retained = cli_fixture.CLITests.native
        require_common_domain(binding.verified, binding.plan)
        cls.common_canonical = run_air_program(binding.verified.program,
                                               entry_directives=(binding.plan.entry_directive,))
        cls.common_managed = execute_managed_retained(binding)
        cls.common_native = retained

    def app(self, native=False, index=0, mapped=True, comparison=None):
        pair = (cli_fixture.replay_fixture.ReplayTests.native if native else
                cli_fixture.replay_fixture.ReplayTests.managed)[index]
        binding, retained = pair
        owner, fake, history = cli_fixture.replay_fixture.observe(binding, retained)
        correlation = None
        if mapped:
            helper = evidence_fixture.EvidenceTests()
            helper.native = retained if native else None
            helper.generated = self.generated
            correlation = helper.correlation(owner, binding, retained)
            anchor = replace(anchors(owner, binding, retained), correlation_fingerprint=correlation.fingerprint())
            evidence = build_evidence_view(owner.session, binding, anchor, retained=retained, correlation=correlation)
            history = ReplayHistory(evidence, history.inspection)
        app = DebuggerCLI(owner=owner, history=history, comparison=history if comparison is None else comparison,
            correlation=correlation, position=None if correlation is None else position(correlation),
            replay_domain=O.TRACE_FAMILY_ORDER if native else O.TRACE_STREAM_ORDER,
            replay_family="native-evidence" if native else "")
        return owner, fake, app

    def assert_custom(self, surfaces, cli_args, dap_command, vs_command, **args):
        expected = cli_rows(surfaces.cli.dispatch(cli_args))
        self.assertEqual(expected, body_rows(surfaces.dap_body(dap_command, **args)))
        vs_args = {key:value for key,value in args.items() if key != "mode" or not vs_command.startswith("Plan ")}
        self.assertEqual(expected, body_rows(surfaces.vs_body(vs_command, **vs_args)))
        return expected

    def state_matrix(self, app):
        with guards():
            s = Surfaces(app)
            direct = app.inspection.state.entries
            cli = [r for name, r in cli_rows(s.cli.dispatch(("state",))) if name == "STATE"]
            s.dap_body("apexforge/inspection")
            dap = s.dap_body("variables", variablesReference=10)["variables"]
            vs = s.vs_body("State")["variables"]
            view = [json.loads(n.payload) for n in s.views.view("state").nodes]
        self.assertEqual(dap, vs)
        self.assertEqual(dap, view)
        self.assertEqual([v["name"] for v in dap], [e.key for e in direct])
        self.assertEqual([r[0] for r in cli], [e.key for e in direct])
        for entry, rendered, row in zip(direct, dap, cli):
            expected = "<redacted>" if app.redacted else field_value(entry.observed_value)
            self.assertEqual(rendered["value"], expected)
            self.assertEqual(rendered["type"], text(entry.declared_type.value))
            self.assertEqual(row[1], plain(entry.declared_type.record()))
            self.assertEqual("<redacted>" if row[2][0] == "redacted" else
                text(row[2][1]) if row[2][0] == "available" else "<" + row[2][0] + ">", expected)
        return s

    def test_managed_state_identity_type_order_and_values(self):
        self.state_matrix(self.app()[2])

    def test_native_state_identity_type_order_and_values(self):
        self.state_matrix(self.app(native=True)[2])

    def test_unavailable_state_parity(self):
        owner, _, history = cli_fixture.replay_fixture.observe(cli_fixture.CLITests.managed[0], None)
        self.state_matrix(DebuggerCLI(owner=owner, history=history))

    def test_redacted_state_parity(self):
        owner, _, history = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.sensitive, redacted=True)
        self.state_matrix(DebuggerCLI(owner=owner, history=history, comparison=history))

    def test_whole_evidence_redaction_also_hides_supplied_visible_snapshot_everywhere(self):
        owner, _, hidden = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.sensitive, redacted=True)
        _, _, visible = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.sensitive)
        app = DebuggerCLI(owner=owner, history=ReplayHistory(hidden.evidence, visible.inspection), comparison=hidden)
        self.state_matrix(app)

    def test_execution_air_plan_directive_result_reference_identity_matrix(self):
        for native in (False, True):
            owner, _, app = self.app(native)
            s = Surfaces(app)
            status = dict(cli_rows(s.cli.dispatch(("status",))))
            self.assertEqual(status["SESSION"][0], owner.session.reference.session_id)
            self.assertEqual(status["EXECUTION"], owner.session.execution.execution_id)
            self.assertEqual(json.loads(s.views.view("overview").context)["execution"], status["EXECUTION"])
            context = s.vs_body("Debugger Session Authorization")["variables"]
            self.assertEqual(next(json.loads(v["value"]) for v in context if v["name"] == "EXECUTION"), status["EXECUTION"])
            inspect = dict(cli_rows(s.cli.dispatch(("inspect",))))
            for name in ("PLAN", "DIRECTIVE", "RESULT"):
                self.assertEqual(inspect[name], plain(getattr(app.inspection, name.lower()).record()))
            self.assertEqual(app.inspection.execution, app.history.evidence.binding.execution)
            self.assertEqual(app.correlation.execution.air_fingerprint, owner.session.execution.air_fingerprint)
            self.assertEqual(app.correlation.execution.routing_fingerprint, owner.session.execution.routing_fingerprint)
            evidence = s.views.view("evidence")
            self.assertEqual({n.reference for n in evidence.nodes}, {n.reference.canonical_form() for n in app.history.evidence.graph.nodes})

    def test_program_and_debugger_authority_separate_on_every_surface(self):
        for native in (False, True):
            _, _, app = self.app(native)
            s = Surfaces(app)
            cli = dict(cli_rows(s.cli.dispatch(("authority",))))
            self.assertEqual(cli["OBSERVED_PROGRAM_AUTHORITY"], plain(app.inspection.authority.record()))
            self.assertFalse(cli["OBSERVED_AUTHORITY_GRANTS_DEBUGGER_CONTROL"])
            self.assertIn("separate", cli["DEBUG_SESSION_CONTROL_AUTHORIZATION"])
            s.dap_body("apexforge/inspection")
            authority = s.dap_body("variables", variablesReference=12)["variables"]
            self.assertEqual(authority, s.vs_body("Observed Program Authority")["variables"])
            self.assertNotEqual(s.views.view("program_authority").view_id, s.views.view("debugger_authority").view_id)
            self.assertIn("not_evaluated_by_view", s.views.view("debugger_authority").canonical_form())

    def correlation_matrix(self, app):
        s = Surfaces(app)
        chain = app.correlation.lookup(app.position.operation_id)
        rows = self.assert_custom(s, ("correlate", "current"), "apexforge/correlate", "Correlate", reference="current")
        self.assertEqual(rows, [(n.label, json.loads(n.payload)) for n in s.views.view("correlation").nodes])
        values = dict(rows)
        self.assertEqual(values["SOURCE"][0], chain.source.status.value)
        self.assertEqual(values["SOURCE"][1], [json.loads(v.canonical_form()) for v in chain.source.values])
        self.assertEqual(values["AIR"][1], json.loads(chain.air.canonical_form()))
        self.assertEqual(values["GENERATED_NATIVE_REGION"][0], chain.native.status.value)
        self.assertEqual(values["GENERATED_NATIVE_REGION"][1], [json.loads(v.canonical_form()) for v in chain.native.values])
        self.assertEqual(values["MACHINE_ADDRESS"], "unsupported")
        return values

    def test_managed_source_air_non_native_correlation_parity(self):
        values = self.correlation_matrix(self.app()[2])
        self.assertEqual(values["SOURCE"][0], "available")
        self.assertEqual(values["GENERATED_NATIVE_REGION"][0], "not_applicable")

    def test_native_unmapped_source_generated_region_parity(self):
        values = self.correlation_matrix(self.app(True)[2])
        self.assertEqual(values["SOURCE"][0], "unavailable")
        self.assertEqual(values["GENERATED_NATIVE_REGION"][0], "available")

    def test_ambiguous_mapping_all_candidates_preserved_everywhere(self):
        original = source_inputs()[-1].sidecar
        first = next(e for e in original.evidence if e.operation_id == original.operations[0].operation_id)
        extra = EvidenceReference(original.operations[1].operation_id, first.source_index, first.source_map_index)
        evidence = tuple(sorted(original.evidence + (extra,), key=lambda e: (e.operation_id, e.source_index, e.source_map_index)))
        owner, index, _ = source_index(replace(original, evidence=evidence))
        app = DebuggerCLI(owner=owner, correlation=index, position=position(index, 1))
        values = self.correlation_matrix(app)
        self.assertEqual(values["SOURCE"][0], "ambiguous")
        self.assertEqual(len(values["SOURCE"][1]), 2)

    def evidence_matrix(self, app):
        s = Surfaces(app)
        graph = app.history.evidence.graph
        rows = self.assert_custom(s, ("evidence", "list"), "apexforge/evidence", "Evidence")
        expected = {n.node_id: [n.reference.kind.value, n.reference.producer_identity, plain(n.payload.record())] for n in graph.nodes}
        self.assertEqual({r[0]: r[1:] for label, r in rows if label == "EVIDENCE"}, expected)
        for node in s.views.view("evidence").nodes:
            identity = node.view_id.removeprefix("view:evidence:")
            producer = graph.node(identity)
            self.assertEqual(node.reference, producer.reference.canonical_form())
            self.assertEqual(json.loads(node.payload), plain(producer.payload.record()))
            self.assertNotEqual(node.view_id, identity)
        rows = self.assert_custom(s, ("provenance",), "apexforge/provenance", "Provenance")
        expected_edges = {(e.source, e.relation.value, e.target, e.support) for e in graph.edges}
        self.assertEqual({tuple(r) for label, r in rows if label == "LINK"}, expected_edges)
        for kind in ("evidence", "provenance"):
            prefix = "view:" + kind + ":"
            edges = s.views.view(kind).edges
            self.assertEqual({(e.source.removeprefix(prefix), e.relation, e.target.removeprefix(prefix), e.evidence_reference) for e in edges}, expected_edges)
        return s

    def test_managed_evidence_trace_provenance_scope_plan_result_parity(self):
        _, _, app = self.app()
        self.evidence_matrix(app)
        scope = cli_fixture.CLITests.managed[1].scope.fingerprint()
        self.assertTrue(any(n.reference.scope_fingerprint == scope for n in app.history.evidence.graph.nodes))
        kinds = {n.reference.kind for n in app.history.evidence.graph.nodes}
        self.assertTrue({K.SCOPE, K.RESULT, K.PLAN, K.TRACE_FAMILY, K.TAM, K.SOURCE_MAPPING} <= kinds)

    def test_native_artifact_mapping_receipt_result_association_parity(self):
        _, _, app = self.app(True)
        self.evidence_matrix(app)
        retained = cli_fixture.CLITests.native[1]
        graph = app.history.evidence.graph
        by_kind = lambda k: [n for n in graph.nodes if n.reference.kind is k]
        self.assertEqual(by_kind(K.ARTIFACT)[0].reference.producer_identity, retained.post.image_fingerprint)
        self.assertEqual(by_kind(K.BUILD_RECEIPT)[0].reference.producer_identity, retained.post.receipt_fingerprint)
        self.assertEqual(by_kind(K.NATIVE_MAPPING)[0].reference.producer_identity, retained.mapping.fingerprint())
        self.assertEqual(by_kind(K.RESULT_ASSOCIATION)[0].reference.producer_identity, retained.post.fingerprint())
        self.assertEqual(app.history.evidence.execution_receipt.status.value, "unsupported")

    def test_recorded_causal_evidence_selection_parity(self):
        _, _, history = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.causal[0])
        s = Surfaces(DebuggerCLI(history=history, comparison=history))
        rows = self.assert_custom(s, ("causal",), "apexforge/causal", "Causal Evidence")
        displayed = {r[0] for label, r in rows if label == "EVIDENCE"}
        self.assertEqual(displayed, {n.view_id.removeprefix("view:causal:") for n in s.views.view("causal").nodes})
        selected = [e for e in history.evidence.graph.edges if e.relation is Relation.SELECTED_PATH]
        self.assertTrue(selected)
        self.assertTrue(all(e.evidence_reference == e.source.removeprefix("view:causal:")
                            for e in s.views.view("causal").edges if e.relation == "selected_path"))
        self.assertIn("CAUSAL_EVIDENCE_NOT_ROOT_CAUSE", s.views.view("causal").limitations)

    def test_ambiguous_causal_occurrence_not_guessed_on_any_surface(self):
        original = cli_fixture.CLITests.causal[0][0].verified.program
        first = original.causal_decisions[0]
        other = replace(first, id="decision:other")
        program = replace(original, directives=(replace(original.directives[0], causal_decisions=(first.id, other.id)),), causal_decisions=(first, other))
        binding = associate_plan(AIRVerifier().verify(program).require_verified(), plan_for(program))
        retained = execute_managed_retained(binding)
        _, _, history = cli_fixture.replay_fixture.observe(binding, retained)
        s = Surfaces(DebuggerCLI(history=history))
        rows = self.assert_custom(s, ("causal",), "apexforge/causal", "Causal Evidence")
        self.assertIn("ambiguous", text(rows))
        self.assertIn("ambiguous", s.views.view("causal").canonical_form())
        self.assertFalse(any(e.relation is Relation.SELECTED_PATH for e in history.evidence.graph.edges))

    def test_attribution_boundary_every_evidence_presentation(self):
        for native in (False, True):
            s = Surfaces(self.app(native)[2])
            for cli, dap, vs in ((("evidence", "list"), "apexforge/evidence", "Evidence"),
                                 (("provenance",), "apexforge/provenance", "Provenance"),
                                 (("causal",), "apexforge/causal", "Causal Evidence")):
                rows = self.assert_custom(s, cli, dap, vs)
                self.assertIn(("EVIDENCE_BEFORE_ATTRIBUTION", True), rows)
                self.assertIn(("ACTOR_ATTRIBUTION", "not_inferred"), rows)
            self.assertTrue(json.loads(tdp_preview(s.views).canonical_form())["evidenceBeforeAttribution"])

    def test_replay_sequences_seek_boundaries_and_evidence_identity_matrix(self):
        for native in (False, True):
            _, _, app = self.app(native)
            s = Surfaces(app)
            timeline = build_replay(app.history, app.replay_domain, family=app.replay_family)
            self.assertTrue(timeline.records)
            entries = s.views.view("timeline").nodes
            self.assertEqual([n.reference for n in entries], [r.evidence.node_id for r in timeline.records])
            self.assertEqual(s.views.view("timeline").ordering, timeline.domain.value)
            cases = (("first", "apexforge/replayFirst", "Replay First", 0),
                ("last", "apexforge/replayLast", "Replay Last", len(timeline.records)-1),
                ("seek", "apexforge/replaySeek", "Replay Seek", min(1,len(timeline.records)-1)))
            for action, dap, vs, sequence in cases:
                args = ("replay", action) + ((str(sequence),) if action == "seek" else ())
                rows = self.assert_custom(s, args, dap, vs, **({"sequence":sequence} if action=="seek" else {}))
                values = dict(rows)
                record = ReplayCursor.first(timeline).seek(timeline, sequence).current(timeline)
                self.assertEqual(values["REPLAY_SEQUENCE"], record.sequence)
                self.assertEqual(values["EVIDENCE_REFERENCE"], record.evidence.node_id)
                self.assertEqual(values["ORDERING_DOMAIN"], record.domain.value)
                self.assertFalse(values["RE_EXECUTION"])
            self.assert_custom(s, ("replay", "first"), "apexforge/replayFirst", "Replay First")
            self.assert_custom(s, ("replay", "previous"), "apexforge/replayPrevious", "Replay Previous")
            self.assert_custom(s, ("replay", "last"), "apexforge/replayLast", "Replay Last")
            self.assert_custom(s, ("replay", "next"), "apexforge/replayNext", "Replay Next")

    def test_comparison_divergence_domains_same_classifications(self):
        _, _, left = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.managed)
        _, _, different = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.divergent)
        _, _, causal_a = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.causal[0])
        _, _, causal_b = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.causal[1])
        for a, b in ((left, different), (causal_a, causal_b), (replace(left, volatile=(("pid", 73),)), left)):
            app = DebuggerCLI(history=a, comparison=b)
            s = Surfaces(app)
            direct = compare_histories(a, b, tuple(D))
            rows = self.assert_custom(s, ("compare", "summary"), "apexforge/compare", "Compare", domain="summary")
            self.assertEqual([r for label,r in rows if label=="COMPARISON"], plain(tuple(r.record() for r in direct.domains)))
            self.assertEqual(rows, [(n.label,json.loads(n.payload)) for n in s.views.view("comparison").nodes])
            self.assertIn(("CAUSAL_EXPLANATION","not_inferred"),rows)
            classes = {r.domain.value:r.classification.value for r in direct.domains}
            if b is different:
                for name in ("state","trace","provenance","result"):
                    self.assertEqual(classes[name], name+"_divergence")
            if a is causal_a:
                self.assertEqual(classes["causal_evidence"],"causal_evidence_divergence")
            if a.volatile:
                supported = compare_histories(a,b,cli_fixture.replay_fixture.SEMANTIC)
                self.assertEqual(supported.volatile_classification.value,"volatile_only_divergence")
                self.assertIn(("VOLATILE_DIFFERENCES",["pid"]),rows)
                self.assertFalse(any(v.endswith("_divergence") for v in classes.values()))

    def test_all_step_plan_modes_same_target_and_planning_only(self):
        for mode,native in (("semantic",False),("source",False),("native-correlation",True)):
            owner, fake, app = self.fixtures.planned(native=native)
            s = Surfaces(app)
            direct = plan_next(app.correlation,owner.session,app.position,
                {"semantic":StepMode.SEMANTIC_STEP,"source":StepMode.SOURCE_STEP,"native-correlation":StepMode.NATIVE_CORRELATION_STEP}[mode],app.known_order)
            rows = self.assert_custom(s,("plan-step",mode),"apexforge/planStep",
                {"semantic":"Plan Semantic Step","source":"Plan Source Step","native-correlation":"Plan Native Correlation"}[mode],mode=mode)
            self.assertIn(("STEP_PLAN_ONLY",True),rows)
            self.assertEqual([r for label,r in rows if label=="TARGET"],plain(tuple((t.ordering_key,json.loads(t.chain.canonical_form())) for t in direct.targets)))
            view = build_views(clone(app),step_mode=mode).view("step_plan")
            self.assertEqual([json.loads(n.payload) for n in view.nodes if n.label=="TARGET"],[r for label,r in rows if label=="TARGET"])
            self.assertTrue(json.loads(view.nodes[0].payload))
            if fake is not None:
                self.assertEqual(fake.consumed,[])

    def test_runtime_capability_truth_everywhere(self):
        s = Surfaces(self.app()[2])
        cli = dict(cli_rows(s.cli.dispatch(("status",))))
        self.assertEqual(cli["LIVE_PAUSE_RESUME"],"unsupported")
        self.assertFalse(cli["EXTERNAL_LIVE_TRANSPORT"])
        self.assertFalse(set(cli["CAPABILITIES"]) & {"live_pause_resume","breakpoint_execution","raw_machine_step"})
        init = dap_fixture.Connection(clone(s.app)).ask("initialize")[0]["body"]
        self.assertFalse(init["apexforge/capabilities"]["runtimeControl"])
        self.assertFalse(init["apexforge/capabilities"]["breakpointExecution"])
        self.assertFalse(init["supportsInstructionBreakpoints"])
        vs = VisualStudioClient(clone(s.app)).connect().view()
        self.assertEqual(vs,init)
        self.assertIn('"UNAVAILABLE"', s.views.view("overview").canonical_form())
        preview = json.loads(tdp_preview(s.views).canonical_form())
        self.assertFalse(preview["operational"])
        self.assertFalse(preview["liveTelemetry"])

    def test_standard_dap_control_and_breakpoint_honesty(self):
        s = Surfaces(self.app()[2])
        for command in ("continue","pause","next","stepIn","stepOut","terminate","setVariable","setExpression"):
            messages=s.dap.ask(command,threadId=1)
            self.assertEqual(len(messages),1)
            self.assertFalse(messages[0]["success"])
            self.assertEqual(messages[0]["message"],"runtime_control_or_mutation_unavailable")
        line=s.app.correlation.chains[0].source.values[0].span.start.line
        body=s.dap_body("setBreakpoints",sourceReference=100,breakpoints=[{"line":line}])
        self.assertTrue(all(not b["verified"] and b["apexforge/planning"]["planningOnly"] for b in body["breakpoints"]))
        self.assertEqual(plain(body),s.vs_body("Plan Breakpoints",sourceReference=100,breakpoints=[{"line":line}]))

    def test_redacted_sentinel_and_withheld_hashes_all_output_surfaces(self):
        owner,_,hidden=cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.sensitive,redacted=True)
        _,_,visible=cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.sensitive)
        s=Surfaces(DebuggerCLI(owner=owner,history=ReplayHistory(hidden.evidence,visible.inspection),comparison=hidden))
        output=s.views.canonical_form()+tdp_preview(s.views).canonical_form()
        with guards():
            for args in (("state",),("inspect",),("authority",),("evidence","list"),("provenance",),("causal",),("compare","summary"),("replay","first"),("unknown",)):
                output+=repr(s.cli.dispatch(args))
            s.dap_body("apexforge/inspection")
            for cmd,args in (("variables",{"variablesReference":10}),("evaluate",{"expression":"state:secret"}),
                ("apexforge/evidence",{}),("apexforge/provenance",{}),("apexforge/compare",{}),("apexforge/replayFirst",{}),
                ("source",{"source":{"path":"PRIVATE_CLI_SENTINEL_73"}}),("evaluate",{"expression":"PRIVATE_CLI_SENTINEL_73"})):
                output+=text(s.dap.ask(cmd,**args))
            for cmd in ("State","Evidence","Provenance","Compare","Replay First"):
                output+=repr(s.vs.command(cmd))
            output+=repr(s.vs.command("PRIVATE_CLI_SENTINEL_73"))
        self.assertNotIn("PRIVATE_CLI_SENTINEL_73",output)
        self.assertNotIn(cli_fixture.CLITests.sensitive[1].result_fingerprint,output)
        self.assertNotIn(cli_fixture.CLITests.sensitive[1].context.state_fingerprint,output)

    def test_failure_security_parity_no_host_eval_pid_or_source_path(self):
        s=Surfaces(self.app()[2])
        with guards():
            for args in (("continue",),("step",),("eval","1+1"),("attach","123"),("shell","dir"),("run","evil.exe"),("--force",)):
                self.assertNotEqual(s.cli.dispatch(args).code,0)
            for cmd in ("Continue","Step Into","Immediate Window","Shell","Attach PID","Run File","Grant Authority"):
                self.assertFalse(s.vs.command(cmd,expression="1+1",processId=123).success)
            for cmd,args in (("evaluate",{"expression":"1+1"}),("source",{"source":{"path":"../../private"}}),
                ("attach",{"mode":"supplied-session","processId":123}),("launch",{"program":"evil.exe"}),
                ("host/exec",{"argv":"dir"}),("setExpression",{"expression":"x=1"})):
                self.assertFalse(s.dap.ask(cmd,**args)[0]["success"])

    def test_rebinding_rejected_by_client_constructor_and_bound_projections(self):
        owner,_,app=self.app()
        other_owner,_,other=self.app(native=True)
        with self.assertRaises(ValueError):
            clone(app,owner=other_owner)
        with self.assertRaises(ValueError):
            clone(app,correlation=other.correlation,position=other.position)
        s=Surfaces(app)
        s.cli.history=other.history
        s.dap.adapter._app.history=other.history
        s.vs._adapter._app.history=other.history
        self.assertNotEqual(s.cli.dispatch(("evidence","list")).code,0)
        self.assertFalse(s.dap.ask("apexforge/evidence")[0]["success"])
        self.assertFalse(s.vs.command("Evidence").success)
        # Both retained and supplied-live clients must preserve their bound target.
        live=clone(app,mode=Mode.LIVE)
        live.history=other.history
        self.assertNotEqual(live.dispatch(("state",)).code,0)
        wrong,_=session_fixture(target=owner.session.execution,session_id="session:wrong")
        modified=clone(app)
        modified.owner=wrong
        with self.assertRaises(ViewError):
            build_views(modified)

    def test_closed_live_rejects_retained_survives_and_disconnect_keeps_evidence(self):
        owner,fake,app=self.app()
        live=Surfaces(clone(app,mode=Mode.LIVE))
        before=app.history.canonical_form()
        owner.begin_close();owner.finish_close()
        disposition = dict(cli_rows(live.cli.dispatch(("request-stop","1"))))
        self.assertNotEqual(disposition["CONTROL_REQUEST_DISPOSITION"][0],"accepted")
        self.assertFalse(disposition["CONTROL_EFFECT_OBSERVED"])
        self.assertFalse(live.dap.ask("apexforge/inspection")[0]["success"])
        self.assertFalse(live.vs.command("State").success)
        self.assertTrue(live.vs.disconnect().success)
        self.assertTrue(live.dap.ask("disconnect")[0]["success"])
        retained=Surfaces(DebuggerCLI(history=app.history,comparison=app.history))
        self.assert_custom(retained,("replay","first"),"apexforge/replayFirst","Replay First")
        self.assertTrue(retained.views.view("evidence").nodes)
        self.assertEqual(before,app.history.canonical_form())
        self.assertEqual(fake.consumed,[])

    def test_independently_produced_managed_and_native_determinism_matrix(self):
        for native in (False,True):
            a,b=self.app(native,index=0)[2],self.app(native,index=1)[2]
            self.assertIsNot(a.history,b.history)
            self.assertEqual(a.inspection.canonical_form(),b.inspection.canonical_form())
            self.assertEqual(a.correlation.canonical_form(),b.correlation.canonical_form())
            self.assertEqual(a.history.evidence.canonical_form(),b.history.evidence.canonical_form())
            self.assertEqual(a.history.canonical_form(),b.history.canonical_form())
            self.assertEqual(compare_histories(a.history,a.history,tuple(D)).canonical_form(),
                             compare_histories(b.history,b.history,tuple(D)).canonical_form())
            x,y=Surfaces(a),Surfaces(b)
            for cli,dap,vs,args in ((("state",),"apexforge/inspection","Inspect",{}),
                (("evidence","list"),"apexforge/evidence","Evidence",{}),
                (("compare","summary"),"apexforge/compare","Compare",{})):
                self.assertEqual(x.cli.dispatch(cli),y.cli.dispatch(cli))
                self.assertEqual(x.dap_body(dap,**args),y.dap_body(dap,**args))
                self.assertEqual(x.vs.command(vs,**args),y.vs.command(vs,**args))
            self.assertEqual(x.views.canonical_form(),y.views.canonical_form())

    def test_tdp_preview_truthfulness_and_resource_custody_fidelity(self):
        owner,_,app=self.app()
        known=lambda s:OwnershipEvidence(EvidenceStatus.KNOWN,s)
        custody=ResourceOwnership("retained-evidence",ResourceClass.SHR,known("producer"),known("inspection"),
            known("retention"),known("retention-contract"),known("explicit-release"))
        binding=available(app.history.evidence.binding.execution.provenance_fingerprint)
        cleanup=missing("cleanup_not_observed")
        resource=ResourceInput(owner.session.execution,custody,binding,cleanup)
        views=build_views(app,resources=(resource,))
        data=json.loads(views.view("resources").nodes[0].payload)
        self.assertEqual(data["custody"],plain(custody.canonical_record()))
        self.assertEqual(data["binding"],plain(binding.record()))
        self.assertEqual(data["cleanup"],plain(cleanup.record()))
        sections={s[0]:s for s in tdp_preview(views).sections}
        for name in ("Transvergent Analytics","Mosaic / FAME","Varenic Trajectories","Policy & Throttle","Simulation"):
            self.assertEqual(sections[name][1],"deferred_to_tdp_domain")
        self.assertIn("not_continuous_telemetry",sections["Live Monitor"][2])
        self.assertIn("no_containment",sections["Incidents & Containment"][2])
        self.assertIn("no_remediation",sections["Medic Lab"][2])
        self.assertEqual(sections["Overview"][3],(views.view("overview").view_id,))

    def test_p12_7_common_domain_semantic_relationship_not_second_engine(self):
        canonical=managed_projection(self.common_canonical)
        managed=managed_projection(self.common_managed.result)
        native=native_projection(self.common_native.evidence.result)
        self.assertEqual(canonical,managed)
        self.assertEqual(canonical,native)
        owner,_,history=cli_fixture.replay_fixture.observe(cli_fixture.CLITests.native[0],self.common_managed)
        self.state_matrix(DebuggerCLI(owner=owner,history=history))
        self.state_matrix(self.app(native=True)[2])

    def test_all_client_queries_semantically_passive_and_no_second_executor(self):
        for native in (False,True):
            owner,fake,app=self.app(native)
            before=(owner.session.canonical_form(),app.history.canonical_form(),app.correlation.canonical_form())
            with guards():
                s=Surfaces(app)
                self.assert_custom(s,("evidence","list"),"apexforge/evidence","Evidence")
                self.assert_custom(s,("compare","summary"),"apexforge/compare","Compare",domain="summary")
                s.vs.disconnect();s.dap.ask("disconnect")
            self.assertEqual(before,(owner.session.canonical_form(),app.history.canonical_form(),app.correlation.canonical_form()))
            self.assertEqual(fake.consumed,[])
        forbidden={"run_air_program","execute","dispatch_native","build_native","allows","select_path","Popen","eval","exec","system","deliver","read_bytes","write_bytes"}
        for filename in ("debug_cli.py","debug_dap.py","debug_visualstudio.py","debug_views.py"):
            tree=ast.parse((ROOT/"apexforge/tooling"/filename).read_text())
            for n in ast.walk(tree):
                if isinstance(n,(ast.Import,ast.ImportFrom)):
                    names=[n.module] if isinstance(n,ast.ImportFrom) else [a.name for a in n.names]
                    self.assertFalse(set(names)&{"runtime.engine","workflow.air_runner","authority.engine","subprocess","os"})
                if isinstance(n,ast.Call):
                    name=n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else ""
                    self.assertNotIn(name,forbidden)


if __name__ == "__main__":
    unittest.main()
