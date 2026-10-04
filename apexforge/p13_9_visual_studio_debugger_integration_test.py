"""P13.9 owner-injected command-client tests; no installed VS claim."""
import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tooling.debug_visualstudio import VisualStudioClient, Projection, MECHANISM
from tooling.debug_cli import DebuggerCLI, Mode
from tooling.debug_inspection import inspect_frame
from tooling.debug_replay import ReplayHistory
from runtime.call_stack import CallFrame
from p13_5_tam_causal_trace_provenance_inspection_test import guards
from p13_4_source_air_native_correlation_step_planning_test import source_index, position
from p12_6_3_metadata_identity_association_test import SOURCE
from p13_2_debug_session_control_foundation_test import fixture as session_fixture
import p13_7_cli_debugger_test as fixtures


class VisualStudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.CLITests.setUpClass()
        cls.fixture = fixtures.CLITests()

    def client(self, **kwargs):
        owner, fake, app = self.fixture.retained(**kwargs)
        c = VisualStudioClient(app)
        self.assertTrue(c.connect().success)
        return owner, fake, app, c

    def good(self, c, name, **args):
        result = c.command(name, **args)
        self.assertTrue(result.success, result.code)
        return result.view()

    def source(self):
        owner, index, _ = source_index()
        app = DebuggerCLI(owner=owner, correlation=index, position=position(index))
        doc = index.chains[0].source.values[0].document
        c = VisualStudioClient(app, source_contents=((doc, SOURCE),))
        self.assertTrue(c.connect().success)
        return app, c

    def test_client_identity_not_debug_session_execution_or_dap(self):
        owner, _, app, c = self.client()
        self.assertNotEqual(c.vs_session_id, owner.session.reference.session_id)
        self.assertNotEqual(c.vs_session_id, c._adapter.dap_session_id)
        self.assertEqual(app.history.evidence.binding.execution, owner.session.execution)
        self.assertEqual(MECHANISM, "VISUAL_STUDIO_COMMAND_CLIENT")
        with self.assertRaises(AttributeError):
            c.vs_session_id = "other"

    def test_capabilities_deterministic_truthful(self):
        _, _, app = self.fixture.retained()
        a, b = VisualStudioClient(app), VisualStudioClient(app)
        self.assertEqual(a.connect(), b.connect())
        caps = a._adapter._app.capabilities
        self.assertEqual(caps, tuple(sorted(caps)))
        self.assertFalse(b.command("Continue").success)

    def test_inspection_and_state_types_order_readonly(self):
        _, _, app, c = self.client()
        context = self.good(c, "Inspect")
        self.assertTrue(context["projectionOnly"])
        values = self.good(c, "State")["variables"]
        self.assertEqual([v["name"] for v in values], [e.key for e in app.inspection.state.entries])
        self.assertTrue(all(v["type"] and v["variablesReference"] == 0 for v in values))
        self.assertTrue(all(v["presentationHint"]["attributes"] == ["readOnly"] for v in values))

    def test_unavailable_values_remain_explicit(self):
        _, _, history = fixtures.replay_fixture.observe(fixtures.CLITests.managed[0], None)
        c = VisualStudioClient(DebuggerCLI(history=history))
        self.assertTrue(c.connect().success)
        self.assertTrue(all(v["value"] == "<unavailable>" for v in self.good(c, "State")["variables"]))

    def test_program_authority_and_debugger_authorization_separate(self):
        _, _, _, c = self.client()
        context = self.good(c, "Inspect")
        self.assertIn("Observed Program Authority", [s["name"] for s in context["scopes"]])
        self.assertNotEqual(self.good(c, "Observed Program Authority"),
                            self.good(c, "Debugger Session Authorization"))

    def test_source_navigation_authorized_no_paths(self):
        app, c = self.source()
        sources = self.good(c, "Sources")["sources"]
        with guards():
            self.assertEqual(self.good(c, "Source Content", sourceReference=sources[0]["sourceReference"])["content"], SOURCE)
            self.assertFalse(c.command("Source Content", source={"path": "../../private"}).success)
            self.assertFalse(c.command("Source Content", sourceReference=999).success)

    def test_native_air_correlation_machine_address_unavailable(self):
        _, _, app = self.fixture.planned(native=True)
        c = VisualStudioClient(app)
        self.assertTrue(c.connect().success)
        rows = self.good(c, "Correlate", reference="current")["rows"]
        values = {r["label"]: r["value"] for r in rows}
        self.assertIn("AIR", values)
        self.assertIn("GENERATED_NATIVE_REGION", values)
        self.assertEqual(values["MACHINE_ADDRESS"], "unsupported")

    def test_breakpoints_unverified_planning_no_effect(self):
        app, c = self.source()
        before = app.correlation.canonical_form()
        line = app.correlation.chains[0].source.values[0].span.start.line
        with guards():
            values = self.good(c, "Plan Breakpoints", sourceReference=100,
                               breakpoints=[{"line": line}, {"line": 999}])["breakpoints"]
        self.assertTrue(all(not v["verified"] and v["apexforge/planning"]["planningOnly"] for v in values))
        self.assertEqual(before, app.correlation.canonical_form())

    def test_all_step_plans_are_plans_not_advancement(self):
        for label, native in (("Plan Semantic Step", False), ("Plan Source Step", False),
                              ("Plan Native Correlation", True)):
            _, fake, app = self.fixture.planned(native=native)
            c = VisualStudioClient(app)
            self.assertTrue(c.connect().success)
            with guards():
                view = self.good(c, label)
            self.assertTrue(view["planningOnly"])
            self.assertFalse(view["reexecution"])
            if fake is not None:
                self.assertEqual(fake.consumed, [])

    def test_evidence_provenance_causal_no_attribution(self):
        _, _, _, c = self.client(divergent=True)
        with guards():
            for label in ("Evidence", "Provenance", "Causal Evidence"):
                values = {r["label"]: r["value"] for r in self.good(c, label)["rows"]}
                self.assertTrue(values["EVIDENCE_BEFORE_ATTRIBUTION"])
                self.assertEqual(values["ACTOR_ATTRIBUTION"], "not_inferred")
            values = {r["label"]: r["value"] for r in self.good(c, "Compare", domain="state")["rows"]}
        self.assertEqual(values["CAUSAL_EXPLANATION"], "not_inferred")

    def test_replay_navigation_not_runtime_stepping(self):
        _, _, app, c = self.client()
        before = app.history.canonical_form()
        with guards():
            for label in ("Replay First", "Replay Next", "Replay Previous", "Replay Last"):
                self.assertFalse(self.good(c, label)["reexecution"])
            self.good(c, "Replay Seek", sequence=2)
        self.assertEqual(before, app.history.canonical_form())

    def test_no_synthetic_stack_projection_thread_label(self):
        _, _, _, c = self.client()
        self.assertEqual(self.good(c, "Semantic Stack", threadId=1)["stackFrames"], [])
        thread = self.good(c, "Projection Threads")["threads"][0]
        self.assertIn("projection", thread["name"])
        self.assertIn("not OS thread", thread["name"])

    def test_genuine_frame_only_when_supplied(self):
        _, _, app = self.fixture.retained()
        frame = inspect_frame(app.inspection.execution, CallFrame("function:example", "example", (), 0))
        snapshot = replace(app.inspection, stack=frame)
        c = VisualStudioClient(DebuggerCLI(history=replace(app.history, inspection=snapshot)))
        self.assertTrue(c.connect().success)
        self.assertEqual(self.good(c, "Semantic Stack", threadId=1)["stackFrames"][0]["name"], "example")

    def test_watch_tooltip_lookup_not_expressions(self):
        _, _, app, c = self.client()
        key = app.inspection.state.entries[0].key
        with guards():
            for label in ("Watch Lookup", "Tooltip Lookup"):
                self.assertTrue(self.good(c, label, expression=key)["apexforge/lookupOnly"])
                for expression in ("1+1", "__import__('os')", "!dir", "set count=9"):
                    self.assertFalse(c.command(label, expression=expression).success)

    def test_no_host_process_mutation_or_live_buttons(self):
        _, _, _, c = self.client()
        with guards():
            for label in ("Attach PID", "Run File", "Shell", "Continue", "Pause", "Step Into", "Step Over",
                          "Step Out", "Set Variable", "Immediate Window", "Grant Authority"):
                self.assertFalse(c.command(label, processId=123, path="evil.exe").success)

    def test_disconnect_local_only_and_cannot_reopen(self):
        owner, fake, app = self.fixture.retained()
        c = VisualStudioClient(DebuggerCLI(mode=Mode.LIVE, owner=owner, history=app.history))
        self.assertTrue(c.connect().success)
        before = owner.session.canonical_form(), app.history.canonical_form()
        self.assertFalse(c.disconnect().view()["apexforge/disconnect"]["executionTerminated"])
        self.assertEqual(before, (owner.session.canonical_form(), app.history.canonical_form()))
        self.assertEqual(fake.consumed, [])
        self.assertFalse(c.connect().success)
        self.assertFalse(c.command("State").success)
        self.assertEqual(c._adapter._issued, set())

    def test_cross_execution_rebinding_rejected(self):
        _, _, app, c = self.client()
        app.history = fixtures.replay_fixture.observe(*fixtures.CLITests.divergent)[2]
        self.assertFalse(c.command("Evidence").success)

    def test_cross_session_rebinding_rejected(self):
        owner, _, app = self.fixture.planned()
        c = VisualStudioClient(app)
        self.assertTrue(c.connect().success)
        other, _ = session_fixture(target=owner.session.execution, session_id="session:other")
        app.owner = other
        self.assertFalse(c.command("Correlate").success)

    def test_closed_session_live_rejected_retained_survives(self):
        owner, _, app = self.fixture.retained()
        live = VisualStudioClient(DebuggerCLI(mode=Mode.LIVE, owner=owner, history=app.history))
        self.assertTrue(live.connect().success)
        owner.begin_close()
        owner.finish_close()
        self.assertFalse(live.command("Inspect").success)
        self.assertTrue(live.disconnect().success)
        retained = VisualStudioClient(app)
        self.assertTrue(retained.connect().success)
        self.good(retained, "Evidence")

    def test_redacted_sentinel_all_views_errors_repr_and_hashes(self):
        secret = "PRIVATE_CLI_SENTINEL_73"
        _, _, hidden = fixtures.replay_fixture.observe(*fixtures.CLITests.sensitive, redacted=True)
        _, _, visible = fixtures.replay_fixture.observe(*fixtures.CLITests.sensitive)
        c = VisualStudioClient(DebuggerCLI(history=ReplayHistory(hidden.evidence, visible.inspection), comparison=hidden))
        output = repr(c.connect())
        with guards():
            for label, args in (("State", {}), ("Tooltip Lookup", {"expression": "state:secret"}),
                ("Watch Lookup", {"expression": secret}), ("Evidence", {}), ("Provenance", {}),
                ("Correlate", {"reference": secret}), ("Causal Evidence", {}), ("Compare", {}),
                ("Source Content", {"sourceReference": 100}), ("Replay First", {}),
                ("Semantic Stack", {"threadId": 1}), (secret, {})):
                output += repr(c.command(label, **args))
        output += repr(c)
        self.assertNotIn(secret, output)
        self.assertNotIn(fixtures.CLITests.sensitive[1].result_fingerprint, output)
        self.assertIn("<redacted>", output)

    def test_immutable_presentation_copy_not_producer_mutation(self):
        _, _, app, c = self.client()
        before = app.history.canonical_form()
        result = c.command("State")
        with self.assertRaises(FrozenInstanceError):
            result.payload = "bad"
        result.view()["variables"].clear()
        self.assertTrue(result.view()["variables"])
        self.assertEqual(before, app.history.canonical_form())

    def test_deterministic_equivalent_projections(self):
        _, _, _, a = self.client()
        _, _, _, b = self.client()
        for name in ("Inspect", "State", "Observed Program Authority", "Evidence", "Provenance", "Compare", "Replay First"):
            self.assertEqual(a.command(name), b.command(name))

    def test_static_dynamic_separation_native_evidence(self):
        tree = ast.parse((ROOT / "apexforge/tooling/debug_visualstudio.py").read_text())
        forbidden = {"execute", "run_air_program", "dispatch_native", "build_native", "allows", "select_path",
                     "Popen", "eval", "exec", "system", "deliver", "open", "read_bytes", "write_bytes"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [node.module] if isinstance(node, ast.ImportFrom) else [n.name for n in node.names]
                self.assertFalse(set(names) & {"subprocess", "os", "runtime.engine", "authority.engine", "workflow.air_runner"})
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                self.assertNotIn(name, forbidden)
        _, _, app = self.fixture.retained(native=True)
        before = app.history.canonical_form()
        c = VisualStudioClient(app)
        with guards():
            self.assertTrue(c.connect().success)
            for label in ("Inspect", "Evidence", "Provenance", "Compare", "Replay First"):
                self.good(c, label)
            self.assertTrue(c.disconnect().success)
        self.assertEqual(before, app.history.canonical_form())


if __name__ == "__main__":
    unittest.main()
