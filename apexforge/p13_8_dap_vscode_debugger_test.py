"""P13.8 bounded protocol/projection tests; no VS Code host integration claim."""
from __future__ import annotations

import ast
from dataclasses import replace
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tooling.debug_dap import (DAPAdapter, DAPError, FramingParser, frame, serve, MAX_PAYLOAD)
from tooling.debug_cli import DebuggerCLI, Mode
from tooling.debug_inspection import inspect_frame, available
from runtime.call_stack import CallFrame
from tooling.debug_replay import ReplayHistory
from p13_4_source_air_native_correlation_step_planning_test import source_index, position
from p12_6_3_metadata_identity_association_test import SOURCE
from p13_2_debug_session_control_foundation_test import fixture as session_fixture
from p13_5_tam_causal_trace_provenance_inspection_test import guards
import p13_7_cli_debugger_test as cli_fixture


class Connection:
    def __init__(self, app, **kwargs):
        self.adapter = DAPAdapter(app, **kwargs)
        self.sequence = 0

    def ask(self, command, **arguments):
        self.sequence += 1
        return self.adapter.handle(dict(seq=self.sequence, type="request", command=command, arguments=arguments))

    def start(self, live=False, **initialize):
        self.ask("initialize", **initialize)
        self.ask("attach" if live else "launch", mode="supplied-session" if live else "retained")
        return self.ask("configurationDone")


class DAPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cli_fixture.CLITests.setUpClass()
        cls.fixtures = cli_fixture.CLITests()

    def retained(self, **kwargs):
        return self.fixtures.retained(**kwargs)

    def source_client(self):
        owner, index, mapping = source_index()
        app = DebuggerCLI(owner=owner, correlation=index, position=position(index))
        doc = index.chains[0].source.values[0].document
        return owner, app, doc

    def good(self, connection, command, **arguments):
        messages = connection.ask(command, **arguments)
        self.assertTrue(messages[0]["success"], messages[0])
        return messages[0]["body"]

    def test_content_length_utf8_and_deterministic_serialization(self):
        msg = {"type": "request", "seq": 1, "command": "initialize", "arguments": {"locale": "é"}}
        self.assertEqual(frame(msg), frame(dict(reversed(tuple(msg.items())))))
        parser = FramingParser()
        self.assertEqual(parser.feed(frame(msg)), (msg,))
        parser.finish()
        encoded = json.dumps(msg, ensure_ascii=False).encode()
        self.assertEqual(FramingParser().feed(
            ("Content-Length: %d\r\n\r\n" % len(encoded)).encode() + encoded), (msg,))

    def test_fragmented_multiple_messages_and_incomplete_eof(self):
        message = {"seq": 1, "type": "request", "command": "initialize"}
        wire = frame(message)
        parser, result = FramingParser(), ()
        for byte in wire:
            result += parser.feed(bytes((byte,)))
        self.assertEqual(result, (message,))
        self.assertEqual(FramingParser().feed(wire + wire), (message, message))
        for partial in (wire[:5], wire[:-1]):
            parser = FramingParser()
            self.assertEqual(parser.feed(partial), ())
            with self.assertRaises(DAPError):
                parser.finish()
            with self.assertRaises(DAPError):
                parser.feed(b"")

    def test_malformed_header_json_duplicate_keys_and_size_limits(self):
        for header in (b"X: 2\r\n\r\n{}", b"Content-Length: -1\r\n\r\n",
            b"Content-Length: 2\r\nContent-Length: 2\r\n\r\n{}",
            b"Content-Length: 9999999\r\n\r\n", b"Content-Length: 0\r\n\r\n"):
            with self.assertRaises(DAPError):
                FramingParser().feed(header)
        for payload in (b"no", b"[]", b'{"x":NaN}', b'{"x":1,"x":2}', b"\xff"):
            with self.assertRaises(DAPError):
                FramingParser().feed(("Content-Length: %d\r\n\r\n" % len(payload)).encode() + payload)
        with self.assertRaises(DAPError):
            FramingParser().feed(b"x" * 4097)
        with self.assertRaises(DAPError):
            FramingParser().feed(b"x" * (MAX_PAYLOAD + 4097))

    def test_initialize_truthful_capabilities_and_initialized_event(self):
        _, _, app = self.retained()
        c = Connection(app)
        messages = c.ask("initialize")
        self.assertEqual(messages[1]["event"], "initialized")
        self.assertTrue(messages[0]["body"]["supportsConfigurationDoneRequest"])
        self.assertTrue(messages[0]["body"]["supportsEvaluateForHovers"])
        for key in ("supportsTerminateRequest", "supportsSetVariable", "supportsSetExpression",
                    "supportsStepBack", "supportsInstructionBreakpoints", "supportsWriteMemoryRequest"):
            self.assertFalse(messages[0]["body"][key])
        self.assertFalse(messages[0]["body"]["apexforge/capabilities"]["runtimeControl"])
        self.assertTrue(all(name.startswith("apexforge/") for name in
            messages[0]["body"]["apexforge/capabilities"]["customRequests"]))

    def test_launch_is_supplied_retained_projection_not_execution(self):
        _, fake, app = self.retained()
        c = Connection(app)
        with guards():
            c.ask("initialize")
            body = self.good(c, "launch", mode="retained")
            messages = c.ask("configurationDone")
        self.assertFalse(body["apexforge/launch"]["executesProgram"])
        self.assertEqual(messages[1]["event"], "stopped")
        self.assertEqual(messages[1]["body"]["apexforge/positionKind"], "OFFLINE_INSPECTION_POSITION")
        self.assertFalse(messages[1]["body"]["apexforge/runtimePauseObserved"])
        self.assertIn("runtime pause not observed", messages[1]["body"]["description"])
        self.assertEqual(fake.consumed, [])

    def test_supplied_attach_and_arbitrary_launch_pid_fields_rejected(self):
        owner, _, app = self.retained()
        live = DebuggerCLI(mode=Mode.LIVE, owner=owner, history=app.history)
        c = Connection(live)
        c.ask("initialize")
        self.assertFalse(c.ask("attach", mode="supplied-session", processId=123)[0]["success"])
        self.good(c, "attach", mode="supplied-session")
        self.good(c, "configurationDone")
        c = Connection(app)
        c.ask("initialize")
        for fields in ({"program": "evil.apex"}, {"adapter": "evil.exe"}, {"pythonModule": "evil"},
                       {"cwd": "elsewhere"}):
            self.assertFalse(c.ask("launch", mode="retained", **fields)[0]["success"])
        self.good(c, "launch", mode="retained")

    def test_projection_thread_and_absent_stack_no_fabrication(self):
        _, _, app = self.retained()
        c = Connection(app)
        c.start()
        threads = self.good(c, "threads")["threads"]
        self.assertEqual(len(threads), 1)
        self.assertIn("projection", threads[0]["name"])
        self.assertIn("not OS thread", threads[0]["name"])
        stack = self.good(c, "stackTrace", threadId=1)
        self.assertEqual(stack["stackFrames"], [])
        self.assertEqual(stack["apexforge/stackAvailability"], "unavailable")
        self.assertFalse(c.ask("scopes", frameId=1)[0]["success"])
        self.assertFalse(c.ask("stackTrace", threadId=True)[0]["success"])

    def test_genuine_supplied_frame_and_read_only_scopes(self):
        _, _, app = self.retained()
        supplied = inspect_frame(app.inspection.execution, CallFrame("function:example", "example", (), 0))
        snapshot = replace(app.inspection, stack=supplied)
        app = DebuggerCLI(history=replace(app.history, inspection=snapshot))
        c = Connection(app)
        c.start()
        frames = self.good(c, "stackTrace", threadId=1)["stackFrames"]
        self.assertEqual(frames[0]["name"], "example")
        self.assertEqual(frames[0]["apexforge/frameReference"][1], "function:example")
        self.assertEqual(self.good(c, "stackTrace", threadId=1, startFrame=1)["stackFrames"], [])
        scopes = self.good(c, "scopes", frameId=1)["scopes"]
        self.assertEqual([s["name"] for s in scopes], ["State", "Directive Context",
            "Observed Program Authority", "Debugger Execution Context", "Evidence", "Provenance"])
        self.assertTrue(all(not s["expensive"] for s in scopes))
        for scope in scopes:
            values = self.good(c, "variables", variablesReference=scope["variablesReference"])["variables"]
            self.assertTrue(all("readOnly" in v["presentationHint"]["attributes"] for v in values))

    def test_custom_inspection_context_scopes_without_synthetic_frame(self):
        _, _, app = self.retained()
        c = Connection(app)
        c.start()
        context = self.good(c, "apexforge/inspection")
        self.assertTrue(context["projectionOnly"])
        self.assertFalse(context["semanticStackAvailable"])
        self.assertEqual(context["scopes"][0]["name"], "State")
        state = self.good(c, "variables", variablesReference=10)["variables"]
        self.assertEqual([v["name"] for v in state], sorted(e.key for e in app.inspection.state.entries))
        self.assertTrue(all(v["variablesReference"] == 0 for v in state))
        self.assertEqual(self.good(c, "variables", variablesReference=10, start=100)["variables"], [])
        self.assertFalse(c.ask("variables", variablesReference=999)[0]["success"])

    def test_unavailable_state_variable_and_lookup_remain_explicit(self):
        binding, _ = cli_fixture.CLITests.managed
        _, _, history = cli_fixture.replay_fixture.observe(binding, None)
        c = Connection(DebuggerCLI(history=history))
        c.start()
        self.good(c, "apexforge/inspection")
        values = self.good(c, "variables", variablesReference=10)["variables"]
        self.assertTrue(all(v["value"] == "<unavailable>" for v in values))
        self.assertEqual(self.good(c, "evaluate", expression=values[0]["name"])["result"], "<unavailable>")

    def test_evaluate_known_state_is_lookup_only_no_expression_engine(self):
        _, _, app = self.retained()
        c = Connection(app)
        c.start()
        key = app.inspection.state.entries[0].key
        with guards():
            body = self.good(c, "evaluate", expression=key)
            for expression in ("1+1", "set count = 99", "__import__('os')", "!dir", "missing"):
                self.assertFalse(c.ask("evaluate", expression=expression)[0]["success"])
        self.assertTrue(body["apexforge/lookupOnly"])
        self.assertEqual(body["variablesReference"], 0)
        self.assertFalse(c.ask("setVariable", variablesReference=10, name=key, value="99")[0]["success"])

    def test_authorized_sources_content_and_no_arbitrary_path_reads(self):
        _, app, doc = self.source_client()
        c = Connection(app, source_contents=((doc, SOURCE),))
        c.start()
        sources = self.good(c, "loadedSources")["sources"]
        self.assertEqual(sources[0]["name"], doc.logical_name)
        self.assertNotIn("path", sources[0])
        with guards():
            body = self.good(c, "source", sourceReference=sources[0]["sourceReference"])
            self.assertFalse(c.ask("source", source={"path": "../../secret"})[0]["success"])
            self.assertFalse(c.ask("source", sourceReference=999)[0]["success"])
        self.assertEqual(body["content"], SOURCE)
        with self.assertRaises(DAPError):
            Connection(app, source_contents=((doc, SOURCE + " "),))

    def test_source_content_unavailable_is_not_fabricated(self):
        _, app, _ = self.source_client()
        c = Connection(app)
        c.start()
        ref = self.good(c, "loadedSources")["sources"][0]["sourceReference"]
        response = c.ask("source", sourceReference=ref)[0]
        self.assertFalse(response["success"])
        self.assertEqual(response["message"], "authorized_source_content_unavailable")

    def test_set_breakpoints_unverified_line_correlation_only_no_install(self):
        owner, app, doc = self.source_client()
        c = Connection(app)
        c.ask("initialize")
        self.good(c, "launch", mode="retained")
        line = app.correlation.chains[0].source.values[0].span.start.line
        before = app.correlation.canonical_form()
        with guards():
            body = self.good(c, "setBreakpoints", source={"sourceReference": 100},
                breakpoints=[{"line": line}, {"line": 999}])
        values = body["breakpoints"]
        self.assertTrue(all(not b["verified"] for b in values))
        self.assertTrue(all(b["apexforge/planning"]["planningOnly"] for b in values))
        self.assertTrue(values[0]["apexforge/planning"]["operationReferences"])
        self.assertEqual(values[1]["apexforge/planning"]["availability"], "unavailable")
        self.assertEqual(before, app.correlation.canonical_form())
        self.assertIn("runtime breakpoint execution unavailable", values[0]["message"])
        self.assertFalse(c.ask("setBreakpoints", source={"sourceReference": 100},
            breakpoints=[{"line": line, "condition": "evil"}])[0]["success"])

    def test_zero_based_client_breakpoint_coordinates(self):
        _, app, _ = self.source_client()
        c = Connection(app)
        c.start(linesStartAt1=False, columnsStartAt1=False)
        canonical = app.correlation.chains[0].source.values[0].span.start.line
        canonical_column = app.correlation.chains[0].source.values[0].span.start.column
        value = self.good(c, "setBreakpoints", sourceReference=100,
            breakpoints=[{"line": canonical - 1, "column": canonical_column - 1}])["breakpoints"][0]
        self.assertEqual(value["line"], canonical - 1)
        self.assertTrue(value["apexforge/planning"]["operationReferences"])

    def test_requested_column_and_frame_context_not_silently_ignored(self):
        _, app, _ = self.source_client()
        c = Connection(app)
        c.start()
        start = app.correlation.chains[0].source.values[0].span.start
        values = self.good(c, "setBreakpoints", sourceReference=100, breakpoints=[
            {"line": start.line, "column": start.column}, {"line": start.line, "column": 9999}])["breakpoints"]
        self.assertTrue(values[0]["apexforge/planning"]["operationReferences"])
        self.assertEqual(values[1]["apexforge/planning"]["availability"], "unavailable")
        self.assertEqual(values[0]["apexforge/planning"]["granularity"], "source-position")
        _, _, app = self.retained()
        c = Connection(app)
        c.start()
        key = app.inspection.state.entries[0].key
        self.assertFalse(c.ask("evaluate", expression=key, frameId=1)[0]["success"])

    def test_standard_control_step_terminate_errors_without_effect_events(self):
        owner, fake, app = self.retained()
        c = Connection(app)
        c.start()
        before = owner.session.canonical_form()
        with guards():
            for command in ("continue", "pause", "next", "stepIn", "stepOut", "terminate",
                            "setExpression", "restart", "readMemory", "writeMemory"):
                response = c.ask(command, threadId=1)
                self.assertEqual(len(response), 1)
                self.assertFalse(response[0]["success"])
                self.assertEqual(response[0]["message"], "runtime_control_or_mutation_unavailable")
        self.assertEqual(before, owner.session.canonical_form())
        self.assertEqual(fake.consumed, [])

    def test_custom_step_planning_delegates_and_labels_only_plan(self):
        for mode, native in (("semantic", False), ("source", False), ("native-correlation", True)):
            _, fake, app = self.fixtures.planned(native=native)
            c = Connection(app)
            c.start(live=True)
            with guards():
                body = self.good(c, "apexforge/planStep", mode=mode)
                correlate = self.good(c, "apexforge/correlate", reference="current")
            self.assertTrue(body["planningOnly"])
            self.assertFalse(body["reexecution"])
            self.assertIn("TARGET", [r["label"] for r in body["rows"]])
            self.assertIn("MACHINE_ADDRESS", [r["label"] for r in correlate["rows"]])
            if fake is not None:
                self.assertEqual(fake.consumed, [])

    def test_custom_replay_not_standard_step(self):
        _, _, app = self.retained()
        c = Connection(app)
        c.start()
        for command, arguments in (("apexforge/replayFirst", {}), ("apexforge/replayNext", {}),
            ("apexforge/replayPrevious", {}), ("apexforge/replayLast", {}),
            ("apexforge/replaySeek", {"sequence": 2})):
            body = self.good(c, command, **arguments)
            self.assertFalse(body["reexecution"])
            self.assertIn("REPLAY_SEQUENCE", [r["label"] for r in body["rows"]])
        self.assertFalse(c.ask("apexforge/replaySeek", sequence=-1)[0]["success"])

    def test_custom_evidence_provenance_causal_comparison_no_attribution(self):
        _, _, app = self.retained(divergent=True)
        c = Connection(app)
        c.start()
        with guards():
            for command in ("apexforge/evidence", "apexforge/provenance", "apexforge/causal"):
                body = self.good(c, command)
                values = {row["label"]: row["value"] for row in body["rows"]}
                self.assertTrue(values["EVIDENCE_BEFORE_ATTRIBUTION"])
                self.assertEqual(values["ACTOR_ATTRIBUTION"], "not_inferred")
            body = self.good(c, "apexforge/compare", domain="state")
        values = {row["label"]: row["value"] for row in body["rows"]}
        self.assertEqual(values["COMPARISON"][1], "state_divergence")
        self.assertEqual(values["CAUSAL_EXPLANATION"], "not_inferred")
        self.assertEqual(values["ACTOR_ATTRIBUTION"], "not_inferred")

    def test_distinctive_redacted_sentinel_across_all_protocol_surfaces(self):
        secret = "PRIVATE_CLI_SENTINEL_73"
        _, _, history = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.sensitive, redacted=True)
        c = Connection(DebuggerCLI(history=history, comparison=history))
        messages = list(c.start())
        commands = (("apexforge/inspection", {}), ("variables", {"variablesReference": 10}),
            ("evaluate", {"expression": "state:secret"}), ("stackTrace", {"threadId": 1}),
            ("source", {"sourceReference": 100}), ("loadedSources", {}),
            ("apexforge/evidence", {}), ("apexforge/provenance", {}), ("apexforge/compare", {}),
            ("apexforge/causal", {}), ("apexforge/replayFirst", {}),
            ("evaluate", {"expression": secret}), ("apexforge/correlate", {"reference": secret}))
        with guards():
            for name, arguments in commands:
                messages.extend(c.ask(name, **arguments))
        output = json.dumps(messages) + repr(c.adapter)
        self.assertNotIn(secret, output)
        self.assertNotIn(cli_fixture.CLITests.sensitive[1].result_fingerprint, output)
        self.assertNotIn(cli_fixture.CLITests.sensitive[1].context.state_fingerprint, output)
        self.assertIn("<redacted>", output)
        self.assertIn("redacted_comparison_unavailable", output)

    def test_full_evidence_redaction_suppresses_even_supplied_visible_snapshot(self):
        _, _, hidden = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.sensitive, redacted=True)
        _, _, visible = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.sensitive)
        history = ReplayHistory(hidden.evidence, visible.inspection)
        c = Connection(DebuggerCLI(history=history))
        c.start()
        self.good(c, "apexforge/inspection")
        variables = self.good(c, "variables", variablesReference=10)["variables"]
        self.assertTrue(all(v["value"] == "<redacted>" for v in variables))
        self.assertEqual(self.good(c, "evaluate", expression="state:secret")["result"], "<redacted>")

    def test_disconnect_closes_projection_not_execution_or_debug_session(self):
        owner, fake, app = self.retained()
        c = Connection(DebuggerCLI(mode=Mode.LIVE, owner=owner, history=app.history))
        c.start(live=True)
        before = owner.session.canonical_form()
        self.assertFalse(c.ask("disconnect", terminateDebuggee=True)[0]["success"])
        messages = c.ask("disconnect")
        self.assertTrue(messages[0]["success"])
        self.assertFalse(messages[0]["body"]["apexforge/disconnect"]["executionTerminated"])
        self.assertEqual(messages[1]["event"], "terminated")
        self.assertEqual(owner.session.canonical_form(), before)
        self.assertEqual(fake.consumed, [])
        self.assertFalse(c.ask("threads")[0]["success"])
        self.assertEqual(c.adapter._issued, set())

    def test_live_close_and_rebinding_reject_retained_can_survive(self):
        owner, _, app = self.retained()
        live = DebuggerCLI(mode=Mode.LIVE, owner=owner, history=app.history)
        c = Connection(live)
        c.start(live=True)
        owner.begin_close()
        owner.finish_close()
        self.assertFalse(c.ask("apexforge/inspection")[0]["success"])
        retained = Connection(app)
        retained.start()
        self.good(retained, "apexforge/inspection")
        app.history = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.divergent)[2]
        self.assertFalse(retained.ask("apexforge/evidence")[0]["success"])

    def test_owner_and_correlation_rebinding_rejected(self):
        owner, _, app = self.fixtures.planned()
        c = Connection(app)
        c.start(live=True)
        other, _ = session_fixture(target=owner.session.execution, session_id="session:other")
        app.owner = other
        self.assertFalse(c.ask("apexforge/correlate", reference="current")[0]["success"])

    def test_illegal_order_unknown_request_and_stale_sequence(self):
        _, _, app = self.retained()
        c = Connection(app)
        self.assertFalse(c.ask("threads")[0]["success"])
        self.good(c, "initialize")
        self.assertFalse(c.ask("initialize")[0]["success"])
        self.assertFalse(c.ask("configurationDone")[0]["success"])
        self.good(c, "launch", mode="retained")
        self.assertFalse(c.ask("threads")[0]["success"])
        self.good(c, "configurationDone")
        self.assertFalse(c.ask("configurationDone")[0]["success"])
        self.assertEqual(c.ask("unknown")[0]["message"], "unsupported_request")
        message = dict(seq=c.sequence, type="request", command="threads")
        self.assertEqual(c.adapter.handle(message)[0]["message"], "stale_request_sequence")
        with self.assertRaises(DAPError):
            c.adapter.handle(dict(seq=True, type="request", command="threads"))

    def test_framed_binary_server_no_target_launch_and_clean_eof(self):
        _, _, app = self.retained()
        requests = [dict(seq=i, type="request", command=name, arguments=args) for i, (name, args)
            in enumerate((("initialize", {}), ("launch", {"mode": "retained"}),
                ("configurationDone", {}), ("threads", {}), ("disconnect", {})), 1)]
        output = BytesIO()
        with guards():
            serve(DAPAdapter(app), BytesIO(b"".join(frame(r) for r in requests)), output)
        messages = FramingParser().feed(output.getvalue())
        self.assertEqual(len([m for m in messages if m["type"] == "response"]), 5)
        self.assertEqual(messages[-1]["event"], "terminated")
        with self.assertRaises(DAPError):
            serve(DAPAdapter(app), BytesIO(b"Content-Length: "), BytesIO())

    def test_equivalent_protocol_projections_deterministic_and_producers_unchanged(self):
        _, _, a = self.retained()
        _, _, b = self.retained()
        before = a.history.canonical_form()
        x, y = Connection(a), Connection(b)
        self.assertEqual(x.start(), y.start())
        for command, args in (("threads", {}), ("stackTrace", {"threadId": 1}),
            ("apexforge/inspection", {}), ("variables", {"variablesReference": 10}),
            ("apexforge/evidence", {}), ("apexforge/compare", {}), ("apexforge/replayFirst", {})):
            self.assertEqual(x.ask(command, **args), y.ask(command, **args))
        self.assertEqual(before, a.history.canonical_form())

    def test_eof_and_framing_failure_release_only_adapter_local_handles(self):
        for wire in (b"", b"Content-Length: "):
            owner, fake, app = self.retained()
            c = Connection(app)
            c.start()
            self.good(c, "apexforge/inspection")
            before = (owner.session.canonical_form(), app.history.canonical_form())
            if wire:
                with self.assertRaises(DAPError):
                    serve(c.adapter, BytesIO(wire), BytesIO())
            else:
                serve(c.adapter, BytesIO(wire), BytesIO())
            self.assertEqual(c.adapter._issued, set())
            self.assertFalse(c.ask("threads")[0]["success"])
            self.assertEqual(before, (owner.session.canonical_form(), app.history.canonical_form()))
            self.assertEqual(fake.consumed, [])

    def test_static_and_dynamic_separation_no_semantic_or_host_owner_calls(self):
        tree = ast.parse((ROOT / "apexforge/tooling/debug_dap.py").read_text())
        forbidden = {"execute", "run_air_program", "dispatch_native", "build_native", "allows",
            "select_path", "Popen", "eval", "exec", "system", "deliver", "open", "read_bytes", "write_bytes"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.ImportFrom, ast.Import)):
                names = [node.module] if isinstance(node, ast.ImportFrom) else [n.name for n in node.names]
                self.assertFalse(set(names) & {"runtime.engine", "workflow.air_runner", "authority.engine",
                    "apexforge.native_backend.native_execution", "subprocess", "os"})
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else "")
                self.assertNotIn(name, forbidden)
        _, _, app = self.retained(native=True)
        app.comparison = cli_fixture.replay_fixture.observe(*cli_fixture.CLITests.native)[2]
        c = Connection(app)
        with guards():
            c.start()
            for command in ("apexforge/inspection", "apexforge/evidence", "apexforge/provenance",
                            "apexforge/replayFirst", "apexforge/compare"):
                self.good(c, command)


if __name__ == "__main__":
    unittest.main()
