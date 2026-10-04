"""P13.6 controlled owner reconstruction and pure observation comparison."""
from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from air.model import StateDefinition
from air.verify import AIRVerifier
from type_system.model import BOOL, INT
from tooling.trace_integration import (associate_plan, execute_managed_retained,
    execute_native_retained, compile_with_metadata)
from tooling.trace_retention import TraceFamily
from tooling.debug_inspection import inspect_execution
from tooling.debug_evidence import build_evidence_view, EvidenceKind as K
from tooling.debug_replay import (ReplayError, ReplayHistory, OrderingDomain as O, ReplayMode as M,
    ReplayAvailability as A, ReplayCursor, capture_history, build_replay, seek_reference,
    Reconstructability as RC, describe_reconstruction, ComparisonDomain as D, Divergence as V,
    compare_histories)
from p12_6_8_controlled_trace_integration_test import managed_fixture
from p12_6_4_source_native_mapping_test import native_fixture
from p12_5_native_profile_contract_test import fixture as air_fixture, plan_for
from p13_3_semantic_state_authority_inspection_test import reference
from p13_2_debug_session_control_foundation_test import fixture as session_fixture
from p13_5_tam_causal_trace_provenance_inspection_test import anchors, guards


SEMANTIC = (D.INPUT, D.AIR, D.STATE, D.AUTHORITY, D.CAUSAL, D.RESULT, D.TRACE, D.MAPPING, D.PROVENANCE)


def classes(result):
    return {r.domain: r.classification for r in result.domains}


def observe(binding, retained, *, identifier="execution:replay", session_id="session:replay",
            redacted=False, timestamp=None, volatile=()):
    owner, fake = session_fixture(session_id=session_id, target=reference(binding, retained, identifier))
    directive = None if retained is None or hasattr(retained, "pre") else next(
        r for c in retained.collections if c.family is TraceFamily.RUNTIME for r in c.records
        if r.evidence.record.kind == "directive.start")
    snapshot = inspect_execution(owner.session.execution, binding, retained=retained,
        directive_record=directive,
        redacted_keys=tuple(s.id for s in binding.verified.program.states) if redacted else ())
    evidence = build_evidence_view(owner.session, binding, anchors(owner, binding, retained),
                                   retained=retained, redacted=redacted)
    history = capture_history(owner.session, evidence, inspection=snapshot, timestamp=timestamp, volatile=volatile)
    return owner, fake, history


def managed_source(source):
    compiler = compile_with_metadata(source.encode(), "src/main.apex")
    binding = associate_plan(compiler.verified, plan_for(compiler.verified.program), compiler)
    return binding, execute_managed_retained(binding)


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.managed = []
        for _ in range(2):
            _, binding = managed_fixture()  # fresh canonical objects, not a reused execution
            cls.managed.append((binding, execute_managed_retained(binding)))
        cls.native = []
        build = ROOT / "build"
        build.mkdir(exist_ok=True)
        for _ in range(2):
            verified, plan, _, _ = native_fixture()
            binding = associate_plan(verified, plan)
            with tempfile.TemporaryDirectory(prefix="p13-replay-", dir=build) as directory:
                with patch("runtime.engine.RuntimeEngine.execute", side_effect=AssertionError("native fallback")):
                    retained = execute_native_retained(binding, Path(directory))
                assert tuple(Path(directory).iterdir()) == ()
            cls.native.append((binding, retained))

    def history(self, index=0, native=False, **kwargs):
        return observe(*(self.native if native else self.managed)[index], **kwargs)

    def test_independent_managed_reconstruction_semantic_equality(self):
        self.assertIsNot(self.managed[0][0].verified.program, self.managed[1][0].verified.program)
        self.assertEqual(self.managed[0][1].result_fingerprint, self.managed[1][1].result_fingerprint)
        _, _, a = self.history(0)
        _, _, b = self.history(1)
        with guards():
            result = compare_histories(a, b, SEMANTIC)
        self.assertTrue(all(r.classification is V.IDENTICAL for r in result.domains))
        self.assertEqual(result.canonical_form(), compare_histories(a, b, tuple(reversed(SEMANTIC))).canonical_form())

    def test_independent_native_reconstruction_conditioned_equality(self):
        _, _, a = self.history(0, native=True)
        _, _, b = self.history(1, native=True)
        self.assertIsNot(self.native[0][0].verified.program, self.native[1][0].verified.program)
        self.assertEqual(self.native[0][1].post.image_fingerprint, self.native[1][1].post.image_fingerprint)
        self.assertEqual(self.native[0][1].evidence.receipt_json, self.native[1][1].evidence.receipt_json)
        with guards():
            result = compare_histories(a, b, (D.AIR, D.STATE, D.RESULT, D.NATIVE_ARTIFACT, D.BUILD_RECEIPT,
                D.MAPPING, D.PROVENANCE, D.TRACE), ordering=O.TRACE_FAMILY_ORDER, family="native-evidence")
        self.assertTrue(all(r.classification is V.IDENTICAL for r in result.domains))

    def test_deterministic_replay_records_and_order(self):
        _, _, a = self.history(0)
        _, _, b = self.history(1)
        x, y = build_replay(a), build_replay(b)
        self.assertEqual(x.fingerprint(), y.fingerprint())
        self.assertEqual(tuple(r.sequence for r in x.records), tuple(range(len(x.records))))
        retained = self.managed[0][1]
        self.assertEqual(tuple(r.logical_key for r in x.records),
            tuple((r.parent_index, r.family.value, r.ordinal) for r in retained.interleaving))
        self.assertEqual(x.records[0].canonical_form(), replace(x.records[0]).canonical_form())
        self.assertEqual(x.availability, A.COMPLETE_RETAINED)

    def test_navigation_forward_backward_first_last_seek(self):
        _, _, history = self.history()
        replay = build_replay(history)
        with guards():
            start = ReplayCursor.first(replay)
            second = start.next(replay)
            self.assertEqual(second.sequence, 1)
            self.assertEqual(second.previous(replay), start)
            end = ReplayCursor.last(replay)
            self.assertEqual(end.next(replay), end)
            self.assertEqual(start.previous(replay), start)
            self.assertEqual(start.seek(replay, 3).current(replay), replay.records[3])
        with self.assertRaises(ReplayError):
            start.seek(replay, -1)
        with self.assertRaises(FrozenInstanceError):
            start.sequence = 4

    def test_evidence_semantic_reference_seek_and_ambiguity(self):
        _, _, history = self.history()
        replay = build_replay(history)
        first = replay.records[0]
        self.assertEqual(seek_reference(replay, first.evidence.reference.producer_identity).records, (first,))
        self.assertEqual(seek_reference(replay, "not-recorded").status, A.UNAVAILABLE)
        broad = seek_reference(replay, history.evidence.binding.execution.air_fingerprint)
        self.assertEqual(broad.status, A.AMBIGUOUS_REFERENCE)
        self.assertGreater(len(broad.records), 1)
        tam = build_replay(history, O.TRACE_FAMILY_ORDER, family="tam")
        graph = history.evidence.graph
        op = next(n for n in graph.nodes if n.reference.kind is K.AIR_OPERATION)
        selected = seek_reference(tam, op.reference.producer_identity)
        self.assertEqual(len(selected.records), 1)

    def test_no_evidence_or_inspection_mutation(self):
        _, fake, history = self.history()
        before = (history.evidence.fingerprint(), history.inspection.fingerprint(), self.managed[0][1].fingerprint())
        with guards():
            replay = build_replay(history)
            ReplayCursor.first(replay).next(replay).current(replay)
            compare_histories(history, history, SEMANTIC)
        self.assertEqual(before, (history.evidence.fingerprint(), history.inspection.fingerprint(),
                                  self.managed[0][1].fingerprint()))
        self.assertEqual(fake.consumed, [])

    def test_partial_replay_and_missing_events_not_fabricated(self):
        binding, _ = self.managed[0]
        _, _, history = observe(binding, None)
        replay = build_replay(history, O.TRACE_FAMILY_ORDER, family="tam")
        self.assertEqual(replay.availability, A.PARTIAL)
        self.assertEqual(len(replay.records), len(binding.compiler.tam.records))
        self.assertEqual(build_replay(history).availability, A.UNAVAILABLE)
        result = compare_histories(history, history, (D.TRACE,), ordering=O.TRACE_FAMILY_ORDER, family="tam")
        self.assertEqual(result.domains[0].classification, V.INSUFFICIENT_EVIDENCE)
        self.assertFalse(build_replay(history).records)

    def test_native_stream_unavailable_without_invented_interleaving(self):
        _, _, history = self.history(native=True)
        self.assertEqual(build_replay(history).availability, A.UNAVAILABLE)
        family = build_replay(history, O.TRACE_FAMILY_ORDER, family="native-evidence")
        self.assertEqual(len(family.records), 1)
        self.assertEqual(family.availability, A.COMPLETE_RETAINED)

    def test_ordering_domains_do_not_collapse(self):
        _, _, history = self.history()
        stream = build_replay(history)
        family = build_replay(history, O.TRACE_FAMILY_ORDER, family="causal-selection")
        self.assertNotEqual(stream.domain, family.domain)
        self.assertTrue(all(r.logical_key[0] == "causal-selection" for r in family.records))
        for mode in (O.SEMANTIC_ORDER, O.SOURCE_ORDER, O.CAUSAL_ORDER, O.DEBUGGER_EVENT_ORDER,
                     O.NATIVE_CORRELATION_ORDER):
            self.assertEqual(build_replay(history, mode).availability, A.UNSUPPORTED_MODE)
        with self.assertRaises(ReplayError):
            build_replay(history, O.TRACE_FAMILY_ORDER)

    def test_managed_reconstruction_description_is_deterministic_but_hashes_insufficient(self):
        _, _, a = self.history(0)
        _, _, b = self.history(1)
        with guards():
            x = describe_reconstruction(a, managed_context=self.managed[0][1].context)
            y = describe_reconstruction(b, managed_context=self.managed[1][1].context)
        self.assertEqual(x.fingerprint(), y.fingerprint())
        self.assertEqual(x.status, RC.INSUFFICIENT_INPUT_EVIDENCE)
        self.assertIn(self.managed[0][1].context.state_fingerprint, x.inputs.value)
        self.assertIn("hashes_are_not_original", x.reason)

    def test_missing_reconstruction_inputs_explicit(self):
        _, _, history = self.history()
        descriptor = describe_reconstruction(history)
        self.assertEqual(descriptor.status, RC.INSUFFICIENT_INPUT_EVIDENCE)
        with self.assertRaises(ReplayError):
            describe_reconstruction(history, managed_context=replace(self.managed[0][1].context,
                                                                   state_fingerprint="A" * 64))
        binding, _ = self.managed[0]
        _, _, partial = observe(binding, None)
        self.assertEqual(describe_reconstruction(partial).status, RC.INSUFFICIENT_INPUT_EVIDENCE)

    def test_native_description_is_toolchain_conditioned_no_reconstruction_execution(self):
        _, _, history = self.history(native=True)
        receipt = self.native[0][1].evidence.receipt_json
        with guards():
            descriptor = describe_reconstruction(history, native_receipt_json=receipt)
        self.assertEqual(descriptor.status, RC.TOOLCHAIN_CONDITIONED)
        self.assertTrue(descriptor.conditions.value[0])
        self.assertIn("compatible_captured_tools", descriptor.reason)
        self.assertEqual(describe_reconstruction(history).status, RC.INSUFFICIENT_INPUT_EVIDENCE)
        with self.assertRaises(ReplayError):
            describe_reconstruction(history, native_receipt_json=receipt + " ")

    def test_real_state_result_trace_mapping_provenance_divergence(self):
        source = self.managed[0][0].compiler.content.decode().replace("set count = 1", "set count = 2")
        binding, retained = managed_source(source)
        _, _, left = self.history()
        _, _, right = observe(binding, retained)
        with guards():
            result = compare_histories(left, right, (D.INPUT, D.AIR, D.STATE, D.RESULT, D.TRACE, D.MAPPING, D.PROVENANCE))
        self.assertEqual(classes(result), {
            D.INPUT: V.INPUT_DIVERGENCE, D.AIR: V.AIR_DIVERGENCE, D.STATE: V.STATE_DIVERGENCE,
            D.RESULT: V.RESULT_DIVERGENCE, D.TRACE: V.TRACE_DIVERGENCE,
            D.MAPPING: V.MAPPING_DIVERGENCE, D.PROVENANCE: V.PROVENANCE_DIVERGENCE})

    def test_real_type_difference_is_not_coerced(self):
        histories = []
        for value, declared in ((1, INT), (True, BOOL)):
            program = air_fixture()
            program = replace(program, states=(StateDefinition("state:value", value, declared),),
                causal_decisions=(), directives=(replace(program.directives[0], causal_decisions=()),))
            verified = AIRVerifier().verify(program).require_verified()
            binding = associate_plan(verified, plan_for(program))
            retained = execute_managed_retained(binding)
            histories.append(observe(binding, retained)[2])
        result = compare_histories(*histories, (D.STATE,))
        self.assertEqual(result.domains[0].classification, V.STATE_DIVERGENCE)
        self.assertEqual(result.domains[0].first_difference, 0)

    def test_causal_evidence_difference_has_no_root_cause_verdict(self):
        histories = []
        for low, high in ((1, 9), (9, 1)):
            source = "directive Main {\n state count = 0\n cause choice {\n" + \
                "path low @ %d { set count = 1 }\npath high @ %d { set count = 2 }\n}\n}\n" % (low, high)
            binding, retained = managed_source(source)
            histories.append(observe(binding, retained)[2])
        with guards():
            result = compare_histories(*histories, (D.CAUSAL, D.PROVENANCE))
        self.assertEqual(classes(result)[D.CAUSAL], V.CAUSAL_EVIDENCE_DIVERGENCE)
        self.assertFalse(hasattr(result, "root_cause"))
        self.assertFalse(hasattr(result, "actor_attribution"))

    def test_authority_evidence_comparison_does_not_rerun_policy(self):
        _, _, a = self.history(0)
        _, _, b = self.history(1)
        with guards():
            result = compare_histories(a, b, (D.AUTHORITY,))
        self.assertEqual(result.domains[0].classification, V.IDENTICAL)

    def test_first_trace_difference_deterministic_and_domain_explicit(self):
        source = self.managed[0][0].compiler.content.decode().replace("set count = 1", "set count = 2")
        _, _, a = self.history()
        _, _, b = observe(*managed_source(source))
        x = compare_histories(a, b, (D.TRACE,))
        y = compare_histories(a, b, (D.TRACE,))
        self.assertEqual(x.fingerprint(), y.fingerprint())
        self.assertIsNotNone(x.domains[0].first_difference)
        self.assertEqual(x.domains[0].ordering, O.TRACE_STREAM_ORDER)
        self.assertTrue(x.domains[0].supporting_references[0])

    def test_volatile_fields_and_local_occurrences_do_not_create_semantic_failure(self):
        _, _, a = self.history(identifier="execution:a", session_id="session:a", timestamp="one",
                               volatile=(("pid", 11), ("temporary_root", "root-one")))
        _, _, b = self.history(identifier="execution:b", session_id="session:b", timestamp="two",
                               volatile=(("pid", 22), ("temporary_root", "root-two")))
        with guards():
            result = compare_histories(a, b, SEMANTIC)
        self.assertTrue(all(r.classification is V.IDENTICAL for r in result.domains))
        self.assertEqual(result.volatile_classification, V.VOLATILE_ONLY_DIVERGENCE)
        self.assertIn("execution_identity", result.volatile_differences)
        self.assertIn("pid", result.volatile_differences)
        self.assertFalse(hasattr(result, "semantic_failure"))
        self.assertEqual(a.fingerprint(), replace(a, timestamp="other", volatile=(("pid", 99),)).fingerprint())

    def test_redacted_replay_comparison_and_description_do_not_leak(self):
        _, _, a = self.history(redacted=True)
        _, _, b = self.history(1, redacted=True)
        _, _, visible = self.history()
        with guards():
            replay = build_replay(a)
            result = compare_histories(a, b, SEMANTIC)
            descriptor = describe_reconstruction(a, managed_context=self.managed[0][1].context)
        self.assertEqual(replay.availability, A.REDACTED)
        self.assertTrue(all(r.classification is V.REDACTED_COMPARISON_UNAVAILABLE for r in result.domains))
        text = repr(replay) + replay.canonical_form() + repr(result) + result.canonical_form() + \
            repr(descriptor) + descriptor.canonical_form()
        for node in visible.evidence.graph.nodes:
            self.assertNotIn(node.reference.producer_identity, text)
        self.assertNotIn(self.managed[0][1].context.state_fingerprint, text)
        self.assertTrue(all(not refs for d in result.domains for refs in d.supporting_references))

    def test_mixed_redaction_rejected(self):
        owner, _, visible = self.history()
        binding, retained = self.managed[0]
        redacted = inspect_execution(owner.session.execution, binding, retained=retained,
                                    redacted_keys=tuple(s.id for s in binding.verified.program.states))
        with self.assertRaises(ReplayError):
            capture_history(owner.session, visible.evidence, inspection=redacted)

    def test_live_cross_session_and_closed_session_rejected_retained_survives(self):
        owner, _, history = self.history()
        live = build_replay(history, mode=M.LIVE_SESSION_REPLAY, session=owner.session)
        cursor = ReplayCursor.first(live, owner.session)
        other, _ = session_fixture(session_id="session:other", target=owner.session.execution)
        with self.assertRaises(ValueError):
            cursor.next(live, other.session)
        owner.begin_close()
        owner.finish_close()
        with self.assertRaises(ValueError):
            cursor.current(live, owner.session)
        with self.assertRaises(ValueError):
            build_replay(history, mode=M.LIVE_SESSION_REPLAY, session=owner.session)
        retained = build_replay(history)
        self.assertEqual(ReplayCursor.first(retained).current(retained), retained.records[0])
        self.assertEqual(compare_histories(history, history, (D.STATE,)).domains[0].classification, V.IDENTICAL)

    def test_stale_cursor_and_cross_execution_history_rejected(self):
        _, _, a = self.history()
        _, _, b = self.history(identifier="execution:other")
        cursor = ReplayCursor.first(build_replay(a))
        with self.assertRaises(ReplayError):
            cursor.current(build_replay(b))
        with self.assertRaises(ReplayError):
            ReplayHistory(a.evidence, b.inspection)

    def test_missing_comparison_domains_remain_unavailable(self):
        binding, _ = self.managed[0]
        _, _, history = observe(binding, None)
        result = compare_histories(history, history, (D.STATE, D.RESULT, D.TRACE, D.NATIVE_ARTIFACT))
        self.assertEqual(classes(result)[D.STATE], V.INSUFFICIENT_EVIDENCE)
        self.assertEqual(classes(result)[D.RESULT], V.INSUFFICIENT_EVIDENCE)
        self.assertEqual(classes(result)[D.TRACE], V.INSUFFICIENT_EVIDENCE)
        self.assertEqual(classes(result)[D.NATIVE_ARTIFACT], V.NOT_APPLICABLE)

    def test_comparison_does_not_turn_observation_order_into_causal_order(self):
        _, _, history = self.history()
        result = compare_histories(history, history, (D.TRACE,), ordering=O.CAUSAL_ORDER)
        self.assertEqual(result.domains[0].classification, V.INSUFFICIENT_EVIDENCE)
        self.assertEqual(result.domains[0].ordering, O.CAUSAL_ORDER)

    def test_static_execution_separation_and_guarded_replay(self):
        tree = ast.parse((ROOT / "apexforge/tooling/debug_replay.py").read_text(encoding="utf-8"))
        forbidden = {"execute", "run_air_program", "dispatch_native", "build_native", "execute_native_retained",
            "execute_managed_retained", "select_path", "allows", "Popen", "open", "read_bytes", "write_bytes",
            "apply", "compile_source", "compile_with_metadata", "grant_authority"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn(node.module, ("runtime.engine", "authority.engine", "causality.engine",
                    "workflow.air_runner", "apexforge.native_backend.native_execution", "subprocess"))
                self.assertFalse(any(n.name in forbidden for n in node.names))
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else "")
                self.assertNotIn(name, forbidden)
        owner, _, history = self.history()
        with guards():
            captured = capture_history(owner.session, history.evidence, inspection=history.inspection)
            replay = build_replay(captured)
            ReplayCursor.first(replay).next(replay).current(replay)
            describe_reconstruction(captured, managed_context=self.managed[0][1].context)
            compare_histories(captured, captured, SEMANTIC)


if __name__ == "__main__":
    unittest.main()
