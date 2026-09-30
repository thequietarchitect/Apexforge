"""Focused P12.6-6 supplied evidence, determinism and provenance contracts."""
from __future__ import annotations
import ast
from dataclasses import replace, fields, FrozenInstanceError
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tooling.trace_retention import (SCHEMA, TraceFamily, ProvenanceScope, TAMEvidence, RuntimeEvidence,
    DiagnosticEvidence, CausalEvidence, AuthorityEvidence, NarrativeEvidence, NativeEvidence,
    OperationAssociation, RetainedRecord, TraceCollection, NativeResultAssociation)
from tam.production import trace_map_from_source_map
from tam.model import TraceRecord, TraceIdentity
from runtime.diagnostics import TraceStep, Diagnostic
from runtime.narrative_execution import NarrativeExecutionTraceEvent, NarrativeExecutionTraceFact
from air.model import facts, Fact
from runtime.context import ExecutionContext
from workflow.air_runner import run_air_program
from causality.engine import CausalEngine
from p12_6_4_source_native_mapping_test import compiler_fixture, native_fixture
from p12_6_3_metadata_identity_association_test import SOURCE
from apexforge.native_backend.source_mapping import build_native_with_mapping
from apexforge.native_backend import native_execution as native
from apexforge.native_backend.result import CanonicalExecutionResult


def source_fixture():
    c, ledger, v, source, mapping = compiler_fixture()
    scope = ProvenanceScope.for_source(mapping, c, ledger, v, source, SOURCE.encode())
    records = tuple(TAMEvidence(r) for r in trace_map_from_source_map(c.source_map).records)
    return c, ledger, v, source, mapping, scope, records


def source_collection(scope, records, mapping, **kwargs):
    ids = {r.record.trace_id for r in records}
    external = tuple(sorted({link.value for r in records for link in r.record.upstream_trace_ids + r.record.downstream_trace_ids if link not in ids}))
    return TraceCollection.supplied(scope, TraceFamily.TAM, records, source_mapping=mapping,
                                    source_contents=(SOURCE.encode(),), unresolved_links=external, **kwargs)


class RetentionTests(unittest.TestCase):
    def test_real_tam_immutable_determinism(self):
        c, ledger, v, source, mapping, scope, records = source_fixture()
        first = source_collection(scope, records, mapping)
        again = source_collection(scope, records, mapping)
        self.assertEqual(first.fingerprint(), again.fingerprint())
        self.assertEqual(tuple(r.identity() for r in first.records), tuple(r.identity() for r in again.records))
        self.assertEqual(tuple(r.evidence.record for r in first.records), trace_map_from_source_map(c.source_map).records)
        first.validate_supplied(scope, records, source_mapping=mapping, source_contents=(SOURCE.encode(),))
        with self.assertRaises(ValueError):
            TraceCollection.supplied(scope, TraceFamily.TAM, records[:1], source_mapping=mapping, source_contents=(SOURCE.encode(),))
        with self.assertRaises(FrozenInstanceError):
            first.records = ()
        with self.assertRaises(ValueError):
            replace(first, records=list(first.records))
        mutable = TraceStep("state.delta", "display", (Fact("value", []),))
        with self.assertRaises(ValueError):
            RetainedRecord(scope, 0, RuntimeEvidence(mutable))
        with self.assertRaises(ValueError):
            source_collection(scope, records + (records[0],), mapping)

    def test_repeated_state_delta_execution_scope_no_inference(self):
        c, ledger, v, source, mapping, scope, records = source_fixture()
        result = run_air_program(c.program)
        supplied = tuple(RuntimeEvidence(s) for s in result.trace.steps if s.kind == "state.delta")
        self.assertEqual(len(supplied), 2)
        collection = TraceCollection.supplied(scope, TraceFamily.RUNTIME, supplied)
        self.assertTrue(all(r.operation is None for r in collection.records))
        repeated = TraceCollection.supplied(scope, TraceFamily.RUNTIME, (supplied[0], supplied[0]))
        self.assertNotEqual(repeated.records[0].identity(), repeated.records[1].identity())
        changed = replace(supplied[0].record, facts=tuple(Fact(f.key, 99) if f.key == "value" else f for f in supplied[0].record.facts))
        self.assertNotEqual(RetainedRecord(scope, 0, RuntimeEvidence(changed)).identity(), collection.records[0].identity())
        with self.assertRaises(ValueError):
            RetainedRecord(scope, 0, supplied[0], OperationAssociation(mapping.sidecar.operations[-1], 0))
        distinct_source = SOURCE.replace("set count = 1", "set count = 2", 1)
        distinct_program = compiler_fixture(distinct_source)[0].program
        distinct = tuple(RuntimeEvidence(s) for s in run_air_program(distinct_program).trace.steps if s.kind == "state.delta")
        ordered = TraceCollection.supplied(scope, TraceFamily.RUNTIME, distinct)
        with self.assertRaises(ValueError):
            ordered.validate_supplied(scope, tuple(reversed(distinct)))
        self.assertEqual(result.trace, run_air_program(c.program).trace)

    def test_families_actual_producers_remain_distinct(self):
        c, ledger, v, source, mapping, scope, records = source_fixture()
        result = run_air_program(c.program)
        causal = CausalEngine().select_path(c.program.causal_decisions[0]).trace_steps
        authority = tuple(s for s in result.trace.steps if s.kind == "authority.check")
        self.assertTrue(authority)
        cases = ((TraceFamily.CAUSAL, tuple(CausalEvidence(s) for s in causal)),
                 (TraceFamily.AUTHORITY, tuple(AuthorityEvidence(s) for s in authority)),
                 (TraceFamily.DIAGNOSTIC, (DiagnosticEvidence(Diagnostic("info", "OBSERVED", "display", c.program.directives[0].id)),)))
        for family, evidence in cases:
            coll = TraceCollection.supplied(scope, family, evidence)
            self.assertEqual(coll.family, family)
            self.assertTrue(all(r.family is family for r in coll.records))
        # Obtain narrative observations from the existing producer using its existing fixture.
        from p11_6e_narrative_trace_diagnostics_termination_semantics_smoke_test import make_story
        from runtime.narrative_execution import NarrativeExecutionState
        from runtime.narrative_observability import execute_narrative_choice
        story, bindings, hero, scene, _, _, choice, _ = make_story()
        narrative = execute_narrative_choice(NarrativeExecutionState(story.identity, scene), bindings, choice, 1)
        narr = TraceCollection.supplied(scope, TraceFamily.NARRATIVE, tuple(NarrativeEvidence(e) for e in narrative.trace))
        self.assertEqual(narr.family, TraceFamily.NARRATIVE)
        self.assertEqual(len(narr.records), 1)
        with self.assertRaises(ValueError):
            TraceCollection.supplied(scope, TraceFamily.RUNTIME, (CausalEvidence(causal[0]),))

    def test_diagnostic_display_outside_fingerprint(self):
        *_, scope, records = source_fixture()
        a = DiagnosticEvidence(Diagnostic("error", "KNOWN", "elapsed=1 pid=123 C:/host", "directive:Main"))
        b = DiagnosticEvidence(replace(a.record, message="elapsed=99 pid=456 /other/host"))
        self.assertEqual(RetainedRecord(scope, 0, a).identity(), RetainedRecord(scope, 0, b).identity())
        with self.assertRaises(ValueError):
            RetainedRecord(scope, 0, DiagnosticEvidence(replace(a.record, node_id="C:/host/private")))
        with self.assertRaises(ValueError):
            RetainedRecord(scope, 0, RuntimeEvidence(TraceStep("state.delta", "display", facts(timestamp=1))))

    def test_operation_association_exact_tam_only(self):
        c, ledger, v, source, mapping, scope, records = source_fixture()
        evidence_ref = mapping.sidecar.evidence[-1]
        entry = mapping.sidecar.source_map.entries[evidence_ref.source_map_index]
        record = next(r for r in records if r.record.representation == "source-map-entry" and r.record.source_span == entry.span and r.record.canonical_identity == entry.air_id)
        op = next(o for o in mapping.sidecar.operations if o.operation_id == evidence_ref.operation_id)
        association = OperationAssociation(op, evidence_ref.source_map_index)
        coll = source_collection(scope, (record,), mapping, operations=(association,))
        self.assertEqual(coll.records[0].operation.operation.operation_id, op.operation_id)
        other = next(o for o in mapping.sidecar.operations if o != op)
        with self.assertRaises(ValueError):
            source_collection(scope, (record,), mapping, operations=(replace(association, operation=other),))
        with self.assertRaises(ValueError):
            source_collection(scope, (record,), mapping, operations=(replace(association, source_map_index=999),))
        foreign = replace(op, ordinal=999)
        with self.assertRaises(ValueError):
            source_collection(scope, (record,), mapping, operations=(replace(association, operation=foreign),))

    def test_source_air_scope_stale_negatives(self):
        c, ledger, v, source, mapping, scope, records = source_fixture()
        coll = source_collection(scope, records, mapping)
        with self.assertRaises(ValueError):
            ProvenanceScope.for_source(mapping, c, ledger, v, source, SOURCE.encode() + b" ")
        changed = replace(c.program, states=(replace(c.program.states[0], initial=99),))
        from air.verify import AIRVerifier
        with self.assertRaises(ValueError):
            ProvenanceScope.for_source(mapping, c, ledger, AIRVerifier().verify(changed).require_verified(), source, SOURCE.encode())
        for name in ("air_fingerprint", "input_fingerprint", "sidecar_fingerprint", "source_mapping_fingerprint"):
            with self.assertRaises(ValueError):
                coll.validate_supplied(replace(scope, **{name: "0" * 64}), records, source_mapping=mapping, source_contents=(SOURCE.encode(),))
        bad = replace(records[0].record, source_span=replace(records[0].record.source_span, source_name="other.apex"))
        with self.assertRaises(ValueError):
            source_collection(scope, (TAMEvidence(bad),), mapping)

    def test_unknown_schema_producer_payload_order(self):
        *_, mapping, scope, records = source_fixture()
        with self.assertRaises(ValueError):
            replace(scope, schema="v999")
        for evidence in (None, {}, "infer missing trace"):
            with self.assertRaises(ValueError):
                RetainedRecord(scope, 0, evidence)
        with self.assertRaises(ValueError):
            TraceCollection.supplied(scope, "tam", records)
        with self.assertRaises(ValueError):
            TraceCollection.supplied(scope, TraceFamily.TAM, None)
        for field, value in (("schema_version", 999), ("producer", "unknown.producer")):
            with self.assertRaises(ValueError):
                RetainedRecord(scope, 0, TAMEvidence(replace(records[0].record, **{field: value})))
        for ordinal in (-1, True, 3):
            with self.assertRaises(ValueError):
                TraceCollection(scope, TraceFamily.TAM, (RetainedRecord(scope, ordinal, records[0]),))
        with self.assertRaises(ValueError):
            source_collection(scope, (TAMEvidence(replace(records[0].record, provenance=("C:/host/path",))),), mapping)

    def test_malformed_authority_and_scope_types_reject(self):
        *_, scope, records = source_fixture()
        bad = AuthorityEvidence(TraceStep("authority.check", "display", facts(allowed="true", capability="c", check="check:c", principal="p", resource="r")))
        with self.assertRaises(ValueError):
            RetainedRecord(scope, 0, bad)
        with self.assertRaises(ValueError):
            replace(scope, routing_fingerprint=False)
        with self.assertRaises(ValueError):
            RetainedRecord(scope, 0, DiagnosticEvidence(Diagnostic("info", "KNOWN", [], "")))

    def test_existing_tam_behavioral_contracts(self):
        import p11_tam_c_deterministic_trace_production_foundation_smoke_test as source
        import p11_tam_i_token_evidence_trace_production_smoke_test as token
        import p11_tam_g_authority_evidence_trace_production_smoke_test as authority
        checks = ((source, ("_assert_real_source_map_projection", "_assert_empty_source_map", "_assert_identity_determinism", "_assert_pure_adapter_surface")),
                  (token, ("_assert_real_token_projection", "_assert_kind_value_and_span_preserved", "_assert_map_projection", "_assert_type_guards", "_assert_no_lexing_or_parser_ownership")),
                  (authority, ("_assert_authority_projection", "_assert_principal_subject_boundary", "_assert_check_facts_preserved", "_assert_grant_evidence_boundary", "_assert_map_projection", "_assert_no_authority_execution", "_assert_air_authority_boundary", "_assert_type_guards")))
        for module, names in checks:
            for name in names:
                getattr(module, name)()

    def test_existing_narrative_behavioral_contracts(self):
        import p11_6e_narrative_trace_diagnostics_termination_semantics_smoke_test as narrative
        narrative.test_success_trace_and_transition_authority()
        narrative.test_failure_diagnostics_and_fail_closed_condition()
        narrative.test_termination_and_no_implicit_behavior()

    def test_no_second_semantics_static_and_runtime(self):
        text = (ROOT / "apexforge/tooling/trace_retention.py").read_text()
        tree = ast.parse(text)
        forbidden = {"id", "eval", "exec", "select_path", "allows", "infer_type", "resolve", "evaluate", "execute", "dispatch_native", "compile_source", "trace_map_from_source_map"}
        calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute))}
        self.assertFalse(calls & forbidden)
        c, ledger, v, source, mapping, scope, records = source_fixture()
        with patch("runtime.engine.RuntimeEngine.execute", side_effect=AssertionError("execution")), \
             patch("causality.engine.CausalEngine.select_path", side_effect=AssertionError("selection")), \
             patch("authority.engine.AuthorityEngine.allows", side_effect=AssertionError("policy")), \
             patch("language.compiler.compile_source_with_map", side_effect=AssertionError("recompile")):
            source_collection(scope, records, mapping).validate_supplied(scope, records,
                source_mapping=mapping, source_contents=(SOURCE.encode(),))


class NativeAssociationTests(unittest.TestCase):
    def test_live_native_result_separation_determinism_and_substitution(self):
        v, plan, content, mapping = native_fixture()
        scope = ProvenanceScope.for_native(mapping, v, plan, content)
        root = ROOT / "build"
        root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p12-6-6-", dir=root) as directory:
            mapped = build_native_with_mapping(v, plan, Path(directory))
            evidence = native.dispatch_native(mapped.artifact, v, plan)
            before = evidence.result.canonical_form()
            coll = TraceCollection.supplied(scope, TraceFamily.NATIVE, (NativeEvidence(evidence),))
            assoc = NativeResultAssociation.supplied(coll, mapped, evidence, v, plan)
            assoc.validate(coll, mapped, evidence, v, plan)
            again = native.dispatch_native(mapped.artifact, v, plan)
            self.assertEqual(evidence, again)
            self.assertEqual(assoc.fingerprint(), NativeResultAssociation.supplied(coll, mapped, again, v, plan).fingerprint())
            self.assertEqual(before, evidence.result.canonical_form())
            self.assertEqual(tuple(f.name for f in fields(CanonicalExecutionResult)), ("input_fingerprint", "status", "outputs"))
            self.assertIsNone(coll.records[0].operation)
            for name in assoc.__dataclass_fields__:
                with self.assertRaises(ValueError):
                    replace(assoc, **{name: "0" * 64}).validate(coll, mapped, evidence, v, plan)
            for name in ("routing_fingerprint", "native_mapping_fingerprint", "air_fingerprint"):
                with self.assertRaises(ValueError):
                    NativeResultAssociation.supplied(replace(coll, scope=replace(scope, **{name: "0" * 64}),
                        records=(replace(coll.records[0], scope=replace(scope, **{name: "0" * 64})),)), mapped, evidence, v, plan)
            with self.assertRaises(ValueError):
                replace(scope, native_profile="wrong-profile")
            with self.assertRaises(ValueError):
                NativeResultAssociation.supplied(coll, replace(mapped, receipt_fingerprint="0" * 64), evidence, v, plan)
            with self.assertRaises(ValueError):
                NativeResultAssociation.supplied(coll, mapped, replace(evidence, receipt_json="{}"), v, plan)
            with self.assertRaises(ValueError):
                assoc.validate(coll, mapped, replace(evidence, result=replace(evidence.result, status="FAILURE")), v, plan)
            with self.assertRaises(ValueError):
                ProvenanceScope.for_native(mapping, v, plan, content + b" ")
            mutable = replace(evidence, result=replace(evidence.result, outputs=replace(evidence.result.outputs, values=list(evidence.result.outputs.values))))
            with self.assertRaises(ValueError):
                RetainedRecord(scope, 0, NativeEvidence(mutable))
            mapped.artifact.image.write_bytes(mapped.artifact.image.read_bytes() + b" ")
            with self.assertRaises(ValueError):
                assoc.validate(coll, mapped, evidence, v, plan)


if __name__ == "__main__":
    unittest.main(verbosity=2)
