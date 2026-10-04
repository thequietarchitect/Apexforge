"""P13.7 controlled retained fixtures; terminal client never owns execution."""
from __future__ import annotations

import ast
from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tooling.debug_cli import (DebuggerCLI, CLIError, Mode, main, shell,
    EXIT_SUCCESS, EXIT_USAGE, CLIENT_VERSION, HELP)
from tooling.debug_session import Capability as C
from tooling.debug_inspection import inspect_execution
from tooling.debug_correlation import build_correlation
from tooling.debug_metadata import EvidenceReference
from tooling.debug_replay import OrderingDomain
from authority.model import AuthorityGrant
import p13_6_deterministic_replay_trace_comparison_test as replay_fixture
from p13_4_source_air_native_correlation_step_planning_test import (
    source_index, source_inputs, native_inputs, position, order)
from p13_2_debug_session_control_foundation_test import fixture as session_fixture
from p13_5_tam_causal_trace_provenance_inspection_test import guards


def invoke(application, *args):
    stdout, stderr = StringIO(), StringIO()
    code = main(args, application=application, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def rows(output, key):
    return tuple(json.loads(line.split("=", 1)[1]) for line in output.splitlines()
                 if line.startswith(key + "="))


class CLITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse owner-driven managed and frozen bounded-native P13.6 fixtures.
        replay_fixture.ReplayTests.setUpClass()
        cls.managed = replay_fixture.ReplayTests.managed[0]
        cls.native = replay_fixture.ReplayTests.native[0]
        source = cls.managed[0].compiler.content.decode().replace("set count = 1", "set count = 2")
        cls.divergent = replay_fixture.managed_source(source)
        cls.sensitive = replay_fixture.managed_source(
            'directive Main {\n state secret : string = "PRIVATE_CLI_SENTINEL_73"\n}\n')
        cls.causal = []
        for low, high in ((1, 9), (9, 1)):
            source = "directive Main {\n state count = 0\n cause choice {\n" + \
                "path low @ %d { set count = 1 }\npath high @ %d { set count = 2 }\n}\n}\n" % (low, high)
            cls.causal.append(replay_fixture.managed_source(source))

    def retained(self, *, redacted=False, native=False, divergent=False):
        owner, fake, history = replay_fixture.observe(
            *(self.native if native else self.managed), redacted=redacted)
        other = replay_fixture.observe(*(self.divergent if divergent else self.managed),
            redacted=redacted)[2]
        app = DebuggerCLI(history=history, comparison=other,
            replay_domain=OrderingDomain.TRACE_FAMILY_ORDER if native else OrderingDomain.TRACE_STREAM_ORDER,
            replay_family="native-evidence" if native else "")
        return owner, fake, app

    def planned(self, *, native=False, resolved=True):
        if native:
            owner, fake, verified, mapping, args = native_inputs()
            index = build_correlation(owner.session, verified, mapping.sidecar, mapping.association, **args)
        else:
            owner, index, _ = source_index()
            fake = None
        pos = position(index)
        known = order(index, pos, tuple(range(len(index.chains)))) if resolved else None
        return owner, fake, DebuggerCLI(mode=Mode.LIVE, owner=owner,
            correlation=index, position=pos, known_order=known)

    def success(self, app, *args):
        code, stdout, stderr = invoke(app, *args)
        self.assertEqual((code, stderr), (EXIT_SUCCESS, ""))
        return stdout

    def test_help_deterministic_and_explicit_limits(self):
        self.assertEqual(self.success(DebuggerCLI(), "help"), HELP)
        self.assertEqual(self.success(DebuggerCLI(), "help"), HELP)
        self.assertIn("STEP_PLAN_ONLY=True", HELP)
        self.assertIn("CONTROL_REQUEST_ACCEPTED != CONTROL_EFFECT_OBSERVED", HELP)

    def test_capabilities_deterministic_and_not_authority(self):
        _, _, app = self.retained()
        output = self.success(app, "capabilities")
        values = rows(output, "CAPABILITIES")[0]
        self.assertEqual(values, sorted(values))
        self.assertIn("replay", values)
        self.assertNotIn("control_request", values)
        self.assertFalse(rows(output, "CAPABILITY_IS_AUTHORIZATION")[0])
        for absent in ("live_pause_resume", "breakpoint_execution", "raw_machine_step", "DAP"):
            self.assertNotIn(absent, values)

    def test_status_retained_and_live_session(self):
        owner, fake, app = self.retained()
        output = self.success(app, "status")
        self.assertEqual(rows(output, "MODE"), ("retained/offline",))
        self.assertEqual(rows(output, "CLIENT"), (CLIENT_VERSION,))
        self.assertEqual(rows(output, "LIVE_PAUSE_RESUME"), ("unsupported",))
        live = DebuggerCLI(mode=Mode.LIVE, history=app.history, owner=owner)
        output = self.success(live, "status")
        self.assertEqual(rows(output, "MODE"), ("live-session",))
        self.assertEqual(rows(output, "SESSION")[0][1], "active")
        self.assertFalse(rows(output, "EXTERNAL_LIVE_TRANSPORT")[0])
        self.assertEqual(fake.consumed, [])

    def test_created_attached_closing_closed_status_does_not_reopen(self):
        owner, fake = session_fixture(active=False)
        app = DebuggerCLI(mode=Mode.LIVE, owner=owner)
        self.assertEqual(rows(self.success(app, "session"), "SESSION")[0][1], "created")
        owner.attach(fake.execution)
        self.assertEqual(rows(self.success(app, "session"), "SESSION")[0][1], "attached")
        owner.begin_close()
        self.assertEqual(rows(self.success(app, "session"), "SESSION")[0][1], "closing")
        owner.finish_close()
        self.assertEqual(rows(self.success(app, "session"), "SESSION")[0][1], "closed")
        self.assertEqual(invoke(app, "inspect")[0], EXIT_USAGE)

    def test_inspection_state_types_order_directive_result(self):
        _, _, app = self.retained()
        snapshot = app.history.inspection
        output = self.success(app, "state")
        entries = rows(output, "STATE")
        self.assertEqual([e[0] for e in entries], sorted(e.key for e in snapshot.state.entries))
        for actual, supplied in zip(entries, snapshot.state.entries):
            self.assertEqual(actual[1:], json.loads(json.dumps(
                (supplied.declared_type.record(), supplied.observed_value.record()))))
        inspection = self.success(app, "inspect")
        self.assertIn("PLAN=", inspection)
        self.assertIn("RESULT=", inspection)
        self.assertEqual(rows(self.success(app, "directive"), "DIRECTIVE")[0],
                         json.loads(json.dumps(snapshot.directive.record())))
        self.assertEqual(rows(self.success(app, "result"), "RESULT")[0],
                         json.loads(json.dumps(snapshot.result.record())))

    def test_unavailable_state_remains_explicit(self):
        binding, _ = self.managed
        owner, _, history = replay_fixture.observe(binding, None)
        app = DebuggerCLI(history=history)
        output = self.success(app, "state")
        self.assertTrue(all(e[2][0] == "unavailable" for e in rows(output, "STATE")))
        self.assertIn("unavailable", output)

    def test_authority_is_observed_not_debugger_authorization(self):
        _, _, app = self.retained()
        with guards():
            output = self.success(app, "authority")
        self.assertIn("OBSERVED_PROGRAM_AUTHORITY", output)
        self.assertIn("DEBUG_SESSION_CONTROL_AUTHORIZATION", output)
        self.assertFalse(rows(output, "OBSERVED_AUTHORITY_GRANTS_DEBUGGER_CONTROL")[0])

    def test_source_correlation_and_operation_lookup(self):
        _, _, app = self.planned()
        output = self.success(app, "correlate", "current")
        self.assertEqual(rows(output, "SOURCE")[0][0], "available")
        self.assertEqual(rows(output, "AIR")[0][0], "available")
        self.assertEqual(rows(output, "GENERATED_NATIVE_REGION")[0][0], "not_applicable")
        self.assertEqual(rows(output, "MACHINE_ADDRESS"), ("unsupported",))
        operation = app.position.operation_id
        self.assertEqual(output, self.success(app, "correlate", operation))

    def test_handbuilt_native_correlation_unmapped_and_no_address(self):
        _, _, app = self.planned(native=True)
        output = self.success(app, "correlate", "current")
        self.assertEqual(rows(output, "SOURCE")[0][0], "unavailable")
        self.assertEqual(rows(output, "GENERATED_NATIVE_REGION")[0][0], "available")
        self.assertEqual(rows(output, "MACHINE_ADDRESS"), ("unsupported",))
        self.assertNotIn("instruction_pointer", output)

    def test_ambiguous_source_candidates_all_preserved(self):
        _, _, _, _, _, _, mapping = source_inputs()
        sidecar = mapping.sidecar
        first = next(e for e in sidecar.evidence if e.operation_id == sidecar.operations[0].operation_id)
        extra = EvidenceReference(sidecar.operations[1].operation_id, first.source_index, first.source_map_index)
        evidence = tuple(sorted(sidecar.evidence + (extra,), key=lambda e:
                               (e.operation_id, e.source_index, e.source_map_index)))
        owner, index, _ = source_index(replace(sidecar, evidence=evidence))
        app = DebuggerCLI(mode=Mode.LIVE, owner=owner, correlation=index)
        output = self.success(app, "correlate", index.chains[1].air.operation.operation_id)
        supplied = rows(output, "SOURCE")[0]
        self.assertEqual((supplied[0], len(supplied[1])), ("ambiguous", 2))

    def test_retained_correlation_can_be_viewed_after_close(self):
        owner, _, live = self.planned()
        app = DebuggerCLI(owner=owner, correlation=live.correlation, position=live.position)
        owner.begin_close()
        owner.finish_close()
        self.assertIn('SOURCE=["available"', self.success(app, "correlate", "current"))
        self.assertEqual(invoke(app, "plan-step", "semantic")[0], EXIT_USAGE)
        self.assertEqual(invoke(live, "correlate", "current")[0], EXIT_USAGE)

    def test_evidence_list_show_and_neighbors_delegate_graph(self):
        _, _, app = self.retained()
        graph = app.history.evidence.graph
        output = self.success(app, "evidence", "list")
        self.assertEqual([e[0] for e in rows(output, "EVIDENCE")], [n.node_id for n in graph.nodes])
        node = graph.nodes[0].node_id
        self.assertEqual(len(rows(self.success(app, "evidence", "show", node), "EVIDENCE")), 1)
        for action in ("predecessors", "successors"):
            expected = getattr(graph, action)(node)
            observed = rows(self.success(app, "evidence", action, node), "EVIDENCE")
            self.assertEqual([n[0] for n in observed], [n.node_id for n in expected])

    def test_provenance_links_and_causal_not_attribution(self):
        _, _, app = self.retained()
        output = self.success(app, "provenance")
        self.assertEqual(len(rows(output, "LINK")), len(app.history.evidence.graph.edges))
        node = app.history.evidence.graph.nodes[0].node_id
        links = rows(self.success(app, "provenance", node), "LINK")
        self.assertTrue(all(n[0] == node or n[2] == node for n in links))
        self.assertTrue(rows(output, "EVIDENCE_BEFORE_ATTRIBUTION")[0])
        self.assertEqual(rows(output, "ACTOR_ATTRIBUTION"), ("not_inferred",))
        causal = self.success(app, "causal")
        self.assertIn("occurrence may be ambiguous", causal)
        self.assertEqual(rows(causal, "ACTOR_ATTRIBUTION"), ("not_inferred",))

    def test_replay_navigation_sequence_and_boundary(self):
        _, _, app = self.retained()
        self.assertEqual(rows(self.success(app, "replay", "first"), "REPLAY_SEQUENCE"), (0,))
        self.assertEqual(rows(self.success(app, "replay", "next"), "REPLAY_SEQUENCE"), (1,))
        self.assertEqual(rows(self.success(app, "replay", "previous"), "REPLAY_SEQUENCE"), (0,))
        self.assertEqual(rows(self.success(app, "replay", "previous"), "REPLAY_SEQUENCE"), (0,))
        last = rows(self.success(app, "replay", "last"), "REPLAY_SEQUENCE")[0]
        self.assertEqual(rows(self.success(app, "replay", "next"), "REPLAY_SEQUENCE"), (last,))
        self.assertEqual(rows(self.success(app, "replay", "seek", "2"), "REPLAY_SEQUENCE"), (2,))
        before = app.cursor
        self.assertEqual(invoke(app, "replay", "seek", str(last + 1))[0], EXIT_USAGE)
        self.assertEqual(before, app.cursor)
        self.assertFalse(rows(self.success(app, "replay", "first"), "RE_EXECUTION")[0])

    def test_native_retained_replay_and_artifact_receipt_comparison(self):
        _, _, app = self.retained(native=True)
        # Native comparison uses a matching native history, not the managed default.
        app.comparison = replay_fixture.observe(*self.native)[2]
        output = self.success(app, "replay", "first")
        self.assertEqual(rows(output, "ORDERING_DOMAIN"), ("trace_family_order",))
        comparisons = rows(self.success(app, "compare", "summary"), "COMPARISON")
        actual = {r[0]: r[1] for r in comparisons}
        self.assertEqual(actual["native_artifact"], "identical")
        self.assertEqual(actual["build_receipt"], "identical")
        self.assertIn("native-image", self.success(app, "evidence", "list"))

    def test_compare_summary_and_real_state_trace_provenance_differences(self):
        _, _, app = self.retained(divergent=True)
        output = self.success(app, "compare", "summary")
        actual = {r[0]: r[1] for r in rows(output, "COMPARISON")}
        for domain in ("state", "trace", "provenance"):
            self.assertEqual(actual[domain], domain + "_divergence")
            single = rows(self.success(app, "compare", domain), "COMPARISON")
            self.assertEqual(len(single), 1)
            self.assertEqual(single[0][1], domain + "_divergence")
        self.assertEqual(rows(output, "ACTOR_ATTRIBUTION"), ("not_inferred",))
        self.assertEqual(rows(output, "CAUSAL_EXPLANATION"), ("not_inferred",))

    def test_real_causal_divergence_without_root_cause(self):
        histories = tuple(replay_fixture.observe(*f)[2] for f in self.causal)
        app = DebuggerCLI(history=histories[0], comparison=histories[1])
        output = self.success(app, "compare", "causal")
        self.assertEqual(rows(output, "COMPARISON")[0][1], "causal_evidence_divergence")
        self.assertEqual(rows(output, "CAUSAL_EXPLANATION"), ("not_inferred",))

    def test_step_semantic_source_native_is_plan_only(self):
        for mode, native in (("semantic", False), ("source", False), ("native-correlation", True)):
            owner, fake, app = self.planned(native=native)
            with guards():
                output = self.success(app, "plan-step", mode)
            self.assertTrue(rows(output, "STEP_PLAN_ONLY")[0])
            self.assertEqual(rows(output, "PLANNED_OBSERVATION_TARGET")[0][0], "available")
            self.assertTrue(rows(output, "TARGET"))
            self.assertNotIn("execution advanced", output)
            if fake is not None:
                self.assertEqual(fake.consumed, [])

    def test_unresolved_step_does_not_predict_branch(self):
        _, _, app = self.planned(resolved=False)
        output = self.success(app, "plan-step", "semantic")
        self.assertEqual(rows(output, "PLANNED_OBSERVATION_TARGET"), (["unavailable", "needs_runtime_observation"],))
        self.assertEqual(rows(output, "TARGET"), ())

    def test_each_accepted_control_request_is_not_delivered_or_effect(self):
        for command in ("request-stop", "request-continue", "request-terminate"):
            owner, fake = session_fixture()
            app = DebuggerCLI(mode=Mode.LIVE, owner=owner)
            with patch.object(owner, "deliver", side_effect=AssertionError("CLI delivered control")):
                output = self.success(app, command, "0")
            self.assertEqual(rows(output, "CONTROL_REQUEST_DISPOSITION")[0][0], "accepted")
            self.assertFalse(rows(output, "CONTROL_EFFECT_OBSERVED")[0])
            self.assertFalse(rows(output, "RUNTIME_CONTROL_INTEGRATED")[0])
            self.assertEqual(fake.consumed, [])
            self.assertNotIn("execution stopped", output)
            self.assertNotIn("execution continued", output)

    def test_observer_missing_capability_authority_and_unsupported_reject(self):
        for condition in ("observer", "denied", "unsupported"):
            owner, fake = session_fixture(capabilities=(C.ATTACH, C.OBSERVE) if condition == "observer" else tuple(C),
                supported=() if condition == "unsupported" else None)
            if condition == "denied":
                # Use a fresh established authority fixture, no CLI permission engine.
                grants = tuple(AuthorityGrant(owner.session.reference.principal_id, c.value,
                    fake.execution.authorization_scope) for c in (C.ATTACH, C.OBSERVE))
                owner, fake = session_fixture(grants=grants)
            output = self.success(DebuggerCLI(mode=Mode.LIVE, owner=owner), "request-stop", "0")
            self.assertEqual(rows(output, "CONTROL_REQUEST_DISPOSITION")[0][0],
                {"observer": "rejected", "denied": "authorization_denied", "unsupported": "unsupported"}[condition])
            self.assertEqual(fake.consumed, [])

    def test_closed_control_rejected_retained_view_survives(self):
        owner, fake, retained = self.retained()
        live = DebuggerCLI(mode=Mode.LIVE, owner=owner, history=retained.history)
        owner.begin_close()
        owner.finish_close()
        output = self.success(live, "request-stop", "0")
        self.assertEqual(rows(output, "CONTROL_REQUEST_DISPOSITION")[0][0], "session_closed")
        self.assertEqual(invoke(live, "state")[0], EXIT_USAGE)
        self.success(retained, "state")
        self.success(retained, "replay", "first")
        self.assertEqual(fake.consumed, [])

    def test_duplicate_sequence_uses_existing_owner_ordering(self):
        owner, fake = session_fixture()
        app = DebuggerCLI(mode=Mode.LIVE, owner=owner)
        self.success(app, "request-stop", "4")
        output = self.success(app, "request-stop", "4")
        self.assertEqual(rows(output, "CONTROL_REQUEST_DISPOSITION")[0], ["stale", "duplicate_sequence"])
        self.assertEqual(fake.consumed, [])

    def test_usage_errors_unknown_malformed_and_missing_capability(self):
        app = DebuggerCLI()
        for command in ((), ("alien",), ("step",), ("continue",), ("!dir",), ("eval", "1"),
            ("--force",), ("inspect", "extra"), ("replay", "seek"), ("replay", "next", "1"),
            ("evidence", "show"), ("evidence", "list", "x"), ("compare", "nonsense"),
            ("plan-step", "workflow"), ("request-stop", "-1")):
            code, stdout, stderr = invoke(app, *command)
            self.assertEqual((code, stdout), (EXIT_USAGE, ""))
            self.assertTrue(stderr.startswith("apexforge-debug: error:"))
        for command in (("inspect",), ("state",), ("evidence", "list"), ("compare", "summary"),
                        ("plan-step", "semantic"), ("correlate", "current"), ("request-stop", "0")):
            self.assertEqual(invoke(app, *command)[0], EXIT_USAGE)

    def test_redaction_all_renderers_errors_and_repr(self):
        _, _, app = self.retained(redacted=True)
        secret = str(self.managed[1].result_fingerprint)
        forms = []
        for command in (("state",), ("inspect",), ("result",), ("directive",), ("authority",),
            ("evidence", "list"), ("evidence", "show", secret), ("provenance", secret), ("causal",),
            ("replay", "first"), ("compare", "summary"), ("correlate", "current"), ("alien", secret)):
            response = app.dispatch(command)
            forms += [response.stdout, response.stderr]
        text = "".join(forms) + repr(app)
        self.assertNotIn(secret, text)
        self.assertNotIn(self.managed[1].context.state_fingerprint, text)
        self.assertIn("redacted", text)
        self.assertIn("redacted_comparison_unavailable", text)
        self.assertTrue(all(e[2][0] == "redacted" for e in rows(self.success(app, "state"), "STATE")))

    def test_shell_bad_command_quote_eof_and_quit(self):
        for commands in ('alien\n"unterminated\nhelp\nquit\nstate\n', 'status\n'):
            output, errors = StringIO(), StringIO()
            code = shell(DebuggerCLI(), stdin=StringIO(commands), stdout=output, stderr=errors)
            self.assertEqual(code, EXIT_SUCCESS)
            self.assertIn("apexforge-debug> ", output.getvalue())
            if "alien" in commands:
                self.assertIn(HELP, output.getvalue())
                self.assertIn("malformed_command", errors.getvalue())
                self.assertNotIn("unavailable_inspection", errors.getvalue())
        self.assertEqual(main(("--interactive",), stdin=StringIO(""), stdout=StringIO(), stderr=StringIO()), 0)

    def test_sensitive_string_and_producer_hashes_never_render_when_redacted(self):
        secret = "PRIVATE_CLI_SENTINEL_73"
        _, _, visible = replay_fixture.observe(*self.sensitive)
        self.assertIn(secret, self.success(DebuggerCLI(history=visible), "state"))
        owner, fake, hidden = replay_fixture.observe(*self.sensitive, redacted=True)
        app = DebuggerCLI(history=hidden, comparison=hidden)
        content = repr(app)
        with guards():
            for command in (("inspect",), ("state",), ("authority",), ("result",), ("directive",),
                ("evidence", "list"), ("evidence", "show", secret), ("provenance", secret), ("causal",),
                ("replay", "first"), ("compare", "summary"), ("correlate", secret), ("alien", secret)):
                response = app.dispatch(command)
                content += response.stdout + response.stderr
        self.assertNotIn(secret, content)
        self.assertNotIn(self.sensitive[1].result_fingerprint, content)
        self.assertNotIn(self.sensitive[1].context.state_fingerprint, content)
        self.assertEqual(fake.consumed, [])

    def test_terminal_control_characters_escaped(self):
        from tooling.debug_cli import render
        output = render((("VALUE", "\x1b[31msecret\nline"),))
        self.assertNotIn("\x1b", output)
        self.assertEqual(len(output.splitlines()), 1)

    def test_equivalent_inputs_have_equal_presentation_and_are_not_mutated(self):
        _, _, a = self.retained()
        _, _, b = self.retained()
        before = (a.history.canonical_form(), a.history.inspection.canonical_form(),
                  self.managed[1].fingerprint())
        for command in (("status",), ("capabilities",), ("inspect",), ("authority",), ("evidence", "list"),
            ("provenance",), ("replay", "first"), ("replay", "next"), ("compare", "summary")):
            self.assertEqual(invoke(a, *command), invoke(b, *command))
        self.assertEqual(before, (a.history.canonical_form(), a.history.inspection.canonical_form(),
                                 self.managed[1].fingerprint()))

    def test_cross_session_execution_and_correlation_binding_rejected(self):
        owner, _, app = self.retained()
        other, _ = session_fixture(target=owner.session.execution, session_id="session:other")
        with self.assertRaises(ValueError):
            DebuggerCLI(mode=Mode.LIVE, owner=other, history=app.history)
        other_history = replay_fixture.observe(*self.divergent)[2]
        with self.assertRaises(ValueError):
            DebuggerCLI(history=app.history, inspection=other_history.inspection)
        _, _, plan = self.planned()
        with self.assertRaises(ValueError):
            DebuggerCLI(history=app.history, correlation=plan.correlation)

    def test_live_correlation_revalidates_after_client_owner_rebinding(self):
        owner, _, app = self.planned()
        other, _ = session_fixture(target=owner.session.execution, session_id="session:other")
        app.owner = other
        for command in (("correlate", "current"), ("plan-step", "semantic")):
            self.assertEqual(invoke(app, *command)[0], EXIT_USAGE)

    def test_static_separation_and_guarded_client_calls(self):
        tree = ast.parse((ROOT / "apexforge/tooling/debug_cli.py").read_text())
        forbidden = {"execute", "run_air_program", "dispatch_native", "build_native", "allows",
            "select_path", "Popen", "eval", "exec", "system", "deliver", "open", "read_bytes", "write_bytes"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.ImportFrom, ast.Import)):
                names = [node.module] if isinstance(node, ast.ImportFrom) else [n.name for n in node.names]
                self.assertTrue(all(n not in ("runtime.engine", "workflow.air_runner", "authority.engine",
                    "apexforge.native_backend.native_execution", "subprocess", "os") for n in names))
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else "")
                self.assertNotIn(name, forbidden)
        _, _, app = self.retained(divergent=True)
        _, _, plan = self.planned()
        with guards():
            for command in (("inspect",), ("state",), ("authority",), ("evidence", "list"), ("provenance",),
                            ("causal",), ("replay", "first"), ("compare", "summary")):
                self.success(app, *command)
            self.success(plan, "correlate", "current")
            self.success(plan, "plan-step", "semantic")


if __name__ == "__main__":
    unittest.main()
