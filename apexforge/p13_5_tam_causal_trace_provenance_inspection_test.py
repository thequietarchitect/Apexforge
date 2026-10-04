"""P13.5 supplied evidence integrity, passivity, redaction and attribution limits."""
from __future__ import annotations

import ast
from contextlib import ExitStack
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from air.model import Fact
from air.verify import AIRVerifier
from tooling.trace_integration import (execute_managed_retained, execute_native_retained,
    associate_plan, compile_with_metadata)
from tooling.trace_retention import TraceFamily
from tooling.debug_session import ExecutionReference, Capability
from tooling.debug_inspection import (bind_inspection, inspect_execution, missing, available,
    Availability as F)
from tooling.debug_correlation import build_correlation, Availability as C
from tooling.debug_evidence import (EvidenceKind as K, Availability as A, Relation as R,
    EvidenceError, EvidenceBinding, EvidenceGraph, EvidenceSelection, build_evidence_view)
from p12_6_8_controlled_trace_integration_test import managed_fixture
from p12_6_4_source_native_mapping_test import native_fixture
from p12_5_native_profile_contract_test import plan_for
from p13_3_semantic_state_authority_inspection_test import reference
from p13_2_debug_session_control_foundation_test import fixture as session_fixture
from p13_4_source_air_native_correlation_step_planning_test import no_execution


def anchors(owner, binding, retained=None):
    return EvidenceBinding(owner.session.reference, owner.session.execution, binding.fingerprint(),
        "" if retained is None else retained.fingerprint(),
        "" if binding.compiler is None else binding.compiler.fingerprint())


def guards():
    stack = ExitStack()
    stack.enter_context(no_execution())
    for path in ("authority.engine.AuthorityEngine.allows", "causality.engine.CausalEngine.select_path",
                 "runtime.state.StateSnapshot.apply", "tooling.trace_integration.execute_managed_retained",
                 "tooling.trace_integration.execute_native_retained"):
        stack.enter_context(patch(path, side_effect=AssertionError("evidence inspector invoked semantic owner")))
    return stack


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata, cls.managed_binding = managed_fixture()
        cls.managed = execute_managed_retained(cls.managed_binding)
        verified, plan, cls.generated, _ = native_fixture()
        cls.native_binding = associate_plan(verified, plan)
        build = ROOT / "build"
        build.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p13-evidence-", dir=build) as directory:
            cls.native = execute_native_retained(cls.native_binding, Path(directory))
            assert tuple(Path(directory).iterdir()) == ()

    def inputs(self, native=False, retained=True, identifier="execution:evidence"):
        binding = self.native_binding if native else self.managed_binding
        result = (self.native if native else self.managed) if retained else None
        target = reference(binding, result, identifier)
        owner, fake = session_fixture(target=target)
        return owner, fake, binding, result, anchors(owner, binding, result)

    def view(self, native=False, **kwargs):
        owner, fake, binding, result, anchor = self.inputs(native)
        return owner, build_evidence_view(owner.session, binding, anchor, retained=result, **kwargs)

    def correlation(self, owner, binding, retained):
        native = retained is self.native
        mapping = retained.mapping if native else binding.compiler.mapping
        sidecar = mapping.sidecar
        association = mapping.association if native else binding.association
        args = dict(required_operations=tuple(op.identity for op in sidecar.operations),
            expected_sidecar_fingerprint=sidecar.fingerprint(),
            expected_association_fingerprint=association.fingerprint())
        if native:
            args.update(native_mapping=mapping, generated_content=self.generated,
                expected_native_mapping_fingerprint=mapping.fingerprint(),
                artifact_association=retained.post, provenance_scope=retained.pre.scope,
                expected_artifact_association_fingerprint=retained.post.fingerprint())
        else:
            args.update(source_contents=(binding.compiler.content,), source_mapping=mapping,
                        expected_source_mapping_fingerprint=mapping.fingerprint(),
                        native_status=C.NOT_APPLICABLE)
        return build_correlation(owner.session, binding.verified, sidecar, association, **args)

    def test_deterministic_references_nodes_edges_and_immutable_graph(self):
        _, a = self.view()
        _, b = self.view()
        self.assertEqual(a.canonical_form(), b.canonical_form())
        self.assertEqual(a.fingerprint(), b.fingerprint())
        graph = EvidenceGraph(tuple(reversed(a.graph.nodes)), tuple(reversed(a.graph.edges)))
        self.assertEqual(a.graph.fingerprint(), graph.fingerprint())
        for node in graph.nodes:
            self.assertEqual(node.reference.canonical_form(), replace(node.reference).canonical_form())
        with self.assertRaises(FrozenInstanceError):
            graph.nodes = ()

    def test_explicit_availability_and_unavailable_is_not_false(self):
        _, view = self.view()
        missing_artifact = view.evidence_for(K.ARTIFACT)
        self.assertEqual(missing_artifact.status, A.UNAVAILABLE)
        self.assertEqual(missing_artifact.reason, "evidence_not_supplied")
        self.assertFalse(hasattr(missing_artifact, "value"))
        for status in (A.UNAVAILABLE, A.UNSUPPORTED, A.NOT_APPLICABLE, A.REDACTED):
            value = EvidenceSelection(status, reason="not_supplied")
            self.assertEqual(value.status, status)
            self.assertEqual(value.nodes, ())
        with self.assertRaises(EvidenceError):
            EvidenceSelection(A.AVAILABLE)

    def test_real_managed_trace_families_scope_and_separate_orders(self):
        _, view = self.view()
        families = view.evidence_for(K.TRACE_FAMILY).nodes
        self.assertEqual({n.payload.value[0] for n in families},
            {"tam", "core-runtime", "causal-selection", "authority-observation", "runtime-diagnostic"})
        self.assertEqual(tuple(x[:3] for x in view.interleaving),
            tuple((r.parent_index, r.family.value, r.ordinal) for r in self.managed.interleaving))
        self.assertTrue(all(view.graph.node(x[3]).reference.scope_fingerprint ==
                           self.managed.scope.fingerprint() for x in view.interleaving))
        self.assertFalse(hasattr(view, "semantic_order"))
        self.assertFalse(hasattr(view, "causal_order"))
        runtime = [view.graph.node(x[3]) for x in view.family_order if x[0] == "core-runtime"]
        self.assertTrue(runtime)
        self.assertTrue(all(n.reference.kind is K.TRACE for n in runtime))

    def test_concrete_compiler_tam_and_explicit_operation_links(self):
        _, view = self.view()
        tam = view.evidence_for(K.TAM)
        self.assertEqual(tam.status, A.AVAILABLE)
        self.assertEqual(len(tam.nodes), len(self.metadata.tam.records))
        self.assertEqual({n.reference.producer_identity for n in tam.nodes},
                         {r.identity() for r in self.metadata.tam.records})
        mapped = [e for e in view.graph.edges if e.relation is R.MAPS_TO]
        self.assertEqual(len(mapped), sum(r.operation is not None for r in self.metadata.tam.records))
        for n in tam.nodes:
            self.assertEqual(n.reference.execution_identity, "")  # reusable compiler evidence
        self.assertTrue(any(e.relation is R.RECORDED_TAM_LINK for e in view.graph.edges))

    def test_causal_alternatives_and_selected_path_only_from_real_retained_record(self):
        owner, view = self.view()
        self.assertTrue(view.evidence_for(K.CAUSAL_DECISION).nodes)
        selected = [e for e in view.graph.edges if e.relation is R.SELECTED_PATH]
        self.assertTrue(selected)
        for edge in selected:
            node = view.graph.node(edge.source)
            self.assertIn(node.reference.producer_identity,
                {r.identity() for c in self.managed.collections if c.family is TraceFamily.CAUSAL for r in c.records})
            self.assertEqual(edge.support, edge.source)
        owner, _, binding, _, anchor = self.inputs(retained=False)
        with guards():
            definitions = build_evidence_view(owner.session, binding, anchor)
        self.assertFalse(any(e.relation is R.SELECTED_PATH for e in definitions.graph.edges))
        self.assertTrue(any(e.relation is R.DEFINES_PATH for e in definitions.graph.edges))
        self.assertFalse(hasattr(definitions, "select_path"))

    def test_ambiguous_canonical_path_association_is_not_guessed(self):
        # Actual owner executes two canonical decisions sharing cause/path identity.
        program = self.managed_binding.verified.program
        first = program.causal_decisions[0]
        duplicate = replace(first, id="decision:other")
        directive = replace(program.directives[0], causal_decisions=(first.id, duplicate.id))
        program = replace(program, directives=(directive,), causal_decisions=(first, duplicate))
        verified = AIRVerifier().verify(program).require_verified()
        binding = associate_plan(verified, plan_for(program))
        retained = execute_managed_retained(binding)
        owner, _ = session_fixture(target=reference(binding, retained))
        with guards():
            view = build_evidence_view(owner.session, binding, anchors(owner, binding, retained), retained=retained)
        causal = [n for n in view.graph.nodes if n.reference.producer_schema == "causality.engine/selection/v1"]
        self.assertTrue(causal)
        self.assertTrue(all(n.payload.value[-1][1] == "ambiguous" for n in causal))
        self.assertFalse(any(e.relation is R.SELECTED_PATH for e in view.graph.edges))

    def test_state_result_difference_is_not_causal_proof(self):
        owner, _, binding, _, anchor = self.inputs(retained=False)
        view = build_evidence_view(owner.session, binding, anchor)
        self.assertFalse(any(e.relation is R.SELECTED_PATH for e in view.graph.edges))
        # The API has no state-difference input or causal-inference relation.
        self.assertNotIn("caused_by", {e.relation.value for e in view.graph.edges})
        self.assertNotIn("state_difference", build_evidence_view.__code__.co_varnames)

    def test_real_native_receipt_artifact_mapping_result_associations(self):
        _, view = self.view(True)
        self.assertEqual(view.evidence_for(K.BUILD_RECEIPT).nodes[0].reference.producer_identity,
                         self.native.post.receipt_fingerprint)
        self.assertEqual(view.evidence_for(K.ARTIFACT).nodes[0].reference.producer_identity,
                         self.native.post.image_fingerprint)
        self.assertEqual(view.evidence_for(K.NATIVE_MAPPING).nodes[0].reference.producer_identity,
                         self.native.mapping.fingerprint())
        self.assertEqual(view.evidence_for(K.RESULT_ASSOCIATION).nodes[0].reference.producer_identity,
                         self.native.post.fingerprint())
        self.assertEqual(view.execution_receipt.status, F.UNSUPPORTED)
        receipt = view.evidence_for(K.BUILD_RECEIPT).nodes[0]
        successors = view.graph.successors(receipt.node_id)
        self.assertIn(K.ARTIFACT, {n.reference.kind for n in successors})
        self.assertFalse(view.evidence_for(K.SOURCE).nodes)  # no invented source for hand-built AIR
        scope = next(n for n in view.evidence_for(K.SCOPE).nodes
                     if n.reference.producer_identity == self.native.pre.scope.fingerprint())
        self.assertIn(K.PLAN, {n.reference.kind for n in view.graph.successors(scope.node_id)})
        result = view.evidence_for(K.RESULT).nodes[0]
        self.assertIn(K.EXECUTION, {n.reference.kind for n in view.graph.successors(result.node_id)})

    def test_partial_chain_valid_without_retained_result(self):
        owner, _, binding, _, anchor = self.inputs(retained=False)
        view = build_evidence_view(owner.session, binding, anchor)
        self.assertEqual(view.evidence_for(K.RESULT).status, A.UNAVAILABLE)
        self.assertEqual(view.evidence_for(K.SOURCE_MAPPING).status, A.AVAILABLE)
        self.assertEqual(view.evidence_for(K.NATIVE_MAPPING).status, A.UNAVAILABLE)
        self.assertEqual(view.coverage.status, F.UNAVAILABLE)

    def test_source_and_native_correlation_integration_is_passive(self):
        for native in (False, True):
            owner, fake, binding, retained, anchor = self.inputs(native)
            correlation = self.correlation(owner, binding, retained)
            anchor = replace(anchor, correlation_fingerprint=correlation.fingerprint())
            before = correlation.fingerprint()
            with guards():
                view = build_evidence_view(owner.session, binding, anchor, retained=retained,
                                           correlation=correlation)
            self.assertEqual(correlation.fingerprint(), before)
            self.assertTrue(view.evidence_for(K.AIR_OPERATION).nodes)
            self.assertEqual(bool(view.evidence_for(K.NATIVE_REGION).nodes), native)
            self.assertEqual(fake.consumed, [])
            with self.assertRaises(EvidenceError):
                build_evidence_view(owner.session, binding,
                    replace(anchor, correlation_fingerprint="A" * 64), retained=retained, correlation=correlation)

    def test_mismatched_air_plan_scope_and_source_mapping_rejected(self):
        owner, _, binding, retained, anchor = self.inputs()
        cases = (
            replace(binding, association=replace(binding.association, air_fingerprint="A" * 64)),
            replace(binding, association=replace(binding.association, routing_fingerprint="A" * 64)),
            replace(binding, mapping_fingerprint="A" * 64),
        )
        for bad in cases:
            with self.assertRaises(ValueError):
                build_evidence_view(owner.session, bad, anchor, retained=retained)
        scope = replace(retained.scope, input_fingerprint="A" * 64)
        with self.assertRaises(ValueError):
            build_evidence_view(owner.session, binding, anchor, retained=replace(retained, scope=scope))

    def test_native_wrong_artifact_receipt_and_mapping_rejected(self):
        owner, _, binding, retained, anchor = self.inputs(True)
        cases = (replace(retained, post=replace(retained.post, image_fingerprint="A" * 64)),
                 replace(retained, pre=replace(retained.pre, receipt_fingerprint="A" * 64)),
                 replace(retained, evidence=replace(retained.evidence, receipt_json='{"image":"wrong"}')),
                 replace(retained, post=replace(retained.post, mapping_fingerprint="A" * 64)))
        for bad in cases:
            with self.subTest(bad=type(bad).__name__), self.assertRaises(ValueError):
                build_evidence_view(owner.session, binding, anchor, retained=bad)

    def test_integrity_checks_apply_even_if_caller_supplies_recomputed_anchor(self):
        owner, _, binding, retained, _ = self.inputs(True)
        wrong = replace(retained, pre=replace(retained.pre, mapping_fingerprint="A" * 64))
        with self.assertRaises(EvidenceError):
            build_evidence_view(owner.session, binding, anchors(owner, binding, wrong), retained=wrong)
        owner, _, binding, retained, _ = self.inputs()
        bad_order = replace(retained, interleaving=tuple(reversed(retained.interleaving)))
        with self.assertRaises(EvidenceError):
            build_evidence_view(owner.session, binding, anchors(owner, binding, bad_order), retained=bad_order)

    def test_trace_collection_other_scope_and_missing_stream_rejected(self):
        owner, _, binding, retained, anchor = self.inputs()
        collection = retained.collections[0]
        other_scope = replace(collection.scope, input_fingerprint="A" * 64)
        other = replace(collection, scope=other_scope,
                        records=tuple(replace(r, scope=other_scope) for r in collection.records))
        bad = replace(retained, collections=(other,) + retained.collections[1:])
        with self.assertRaises(ValueError):
            build_evidence_view(owner.session, binding, anchors(owner, binding, bad), retained=bad)
        bad = replace(retained, interleaving=retained.interleaving[:-1])
        with self.assertRaises(EvidenceError):
            build_evidence_view(owner.session, binding, anchors(owner, binding, bad), retained=bad)

    def test_cross_session_execution_and_closed_binding_rejected(self):
        owner, _, binding, retained, anchor = self.inputs()
        other, _ = session_fixture(session_id="session:other", target=owner.session.execution)
        with self.assertRaises(EvidenceError):
            build_evidence_view(other.session, binding, anchor, retained=retained)
        other, _ = session_fixture(target=replace(owner.session.execution, execution_id="execution:other"))
        with self.assertRaises(EvidenceError):
            build_evidence_view(other.session, binding, anchor, retained=retained)
        owner.begin_close()
        owner.finish_close()
        with self.assertRaises(EvidenceError):
            build_evidence_view(owner.session, binding, anchor, retained=retained)

    def test_result_navigation_does_not_mutate_inspection(self):
        for native in (False, True):
            owner, _, binding, retained, anchor = self.inputs(native)
            snapshot = inspect_execution(owner.session.execution, binding, retained=retained)
            inspection = bind_inspection(snapshot, owner.session)
            before = snapshot.fingerprint()
            with guards():
                view = build_evidence_view(owner.session, binding, anchor, retained=retained)
                navigation = view.result_evidence(owner.session, inspection)
            self.assertEqual(navigation.status, A.AVAILABLE)
            self.assertIn(K.RESULT_ASSOCIATION, {n.reference.kind for n in navigation.nodes})
            self.assertIn(K.TRACE_FAMILY, {n.reference.kind for n in navigation.nodes})
            self.assertEqual(snapshot.fingerprint(), before)
            wrong = replace(snapshot, result=available(snapshot.result.value[:-1] + ("A" * 64,)))
            with self.assertRaises(EvidenceError):
                view.result_evidence(owner.session, bind_inspection(wrong, owner.session))
            other, _ = session_fixture(session_id="session:other", target=owner.session.execution)
            with self.assertRaises(ValueError):
                view.result_evidence(other.session, bind_inspection(snapshot, other.session))

    def test_observed_authority_is_not_control_authority_and_not_evaluated(self):
        owner, _, binding, retained, _ = self.inputs()
        owner, fake = session_fixture(target=owner.session.execution,
                                      capabilities=(Capability.ATTACH, Capability.OBSERVE))
        with guards():
            view = build_evidence_view(owner.session, binding, anchors(owner, binding, retained), retained=retained)
        self.assertTrue(view.evidence_for(K.AUTHORITY).nodes)
        self.assertNotIn(Capability.REQUEST_TERMINATE, owner.session.granted)
        self.assertEqual(fake.consumed, [])

    def test_redacted_payload_and_producer_hashes_do_not_leak(self):
        _, visible = self.view()
        _, redacted = self.view(redacted=True)
        text = repr(redacted) + redacted.canonical_form()
        self.assertTrue(all(n.payload.status is F.REDACTED for n in redacted.graph.nodes))
        self.assertEqual(redacted.evidence_for(K.TRACE).status, A.REDACTED)
        for n in visible.graph.nodes:
            self.assertNotIn(n.reference.producer_identity, text)
        self.assertNotIn(self.managed.scope.fingerprint(), text)
        self.assertNotEqual(redacted.fingerprint(), visible.fingerprint())

    def test_redacted_client_fingerprint_independent_of_sensitive_values(self):
        # Equivalent graph shape with different low-entropy state/trace values.
        source = self.metadata.content.decode().replace("set count = 1", "set count = 9")
        compiler = compile_with_metadata(source.encode(), "src/main.apex")
        binding = associate_plan(compiler.verified, plan_for(compiler.verified.program), compiler)
        retained = execute_managed_retained(binding)
        owner, _ = session_fixture(target=reference(binding, retained, "execution:evidence"))
        view = build_evidence_view(owner.session, binding, anchors(owner, binding, retained),
                                   retained=retained, redacted=True)
        _, original = self.view(redacted=True)
        self.assertEqual(view.canonical_form(), original.canonical_form())
        self.assertEqual(view.fingerprint(), original.fingerprint())

    def test_queries_are_pure_and_do_not_infer_external_attribution(self):
        owner, view = self.view(True)
        before = view.fingerprint()
        with guards():
            artifact = view.evidence_for(K.ARTIFACT).nodes[0]
            predecessor = view.graph.predecessors(artifact.node_id)
            successors = view.graph.successors(predecessor[0].node_id)
        self.assertTrue(successors)
        self.assertEqual(view.fingerprint(), before)
        self.assertFalse(any(word in {n.reference.kind.value for n in view.graph.nodes}
                             for word in ("person", "actor", "attribution", "anomaly")))
        self.assertFalse(hasattr(view, "attribute_actor"))
        self.assertFalse(any(e.relation.value in ("caused_by", "owned_by", "authorized_under")
                             for e in view.graph.edges))

    def test_timestamp_and_diagnostic_display_excluded_from_fingerprints(self):
        _, a = self.view(timestamp="2026-01-01")
        _, b = self.view(timestamp="2030-01-01")
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertNotIn(str(ROOT), a.canonical_form())
        self.assertFalse(hasattr(a, "pid"))

    def test_trace_display_messages_cannot_create_attribution_or_change_identity(self):
        owner, _, binding, retained, anchor = self.inputs()
        original = build_evidence_view(owner.session, binding, anchor, retained=retained)
        # Display prose is outside retained record identity. Preserve canonical facts.
        collection = next(c for c in retained.collections if c.family is TraceFamily.RUNTIME)
        target = collection.records[0]
        step = replace(target.evidence.record, message="PersonSecret allegedly caused event; pid=private")
        record = replace(target, evidence=replace(target.evidence, record=step))
        collection = replace(collection, records=(record,) + collection.records[1:])
        index = next(r.parent_index for r in retained.interleaving
                     if r.family is TraceFamily.RUNTIME and r.ordinal == 0)
        steps = list(retained.result.trace.steps)
        steps[index] = step
        result = replace(retained.result, trace=replace(retained.result.trace, steps=tuple(steps)))
        modified = replace(retained, result=result, collections=tuple(
            collection if c.family is TraceFamily.RUNTIME else c for c in retained.collections))
        with guards():
            view = build_evidence_view(owner.session, binding, anchor, retained=modified)
        self.assertEqual(view.fingerprint(), original.fingerprint())
        self.assertNotIn("PersonSecret", repr(view) + view.canonical_form())

    def test_static_and_real_fixture_semantic_passivity(self):
        path = ROOT / "apexforge/tooling/debug_evidence.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        forbidden = {"execute", "run_air_program", "dispatch_native", "select_path", "allows",
            "emit_native_source_mapping", "compile_source", "compile_with_metadata", "Popen",
            "open", "read_bytes", "write_bytes", "set_state", "grant_authority"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn(node.module, ("runtime.engine", "workflow.air_runner", "authority.engine",
                    "causality.engine", "apexforge.native_backend.native_execution", "subprocess"))
                self.assertFalse(any(x.name in forbidden for x in node.names))
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else "")
                self.assertNotIn(name, forbidden)
        for native in (False, True):
            owner, fake, binding, retained, anchor = self.inputs(native)
            before = retained.fingerprint()
            with guards():
                view = build_evidence_view(owner.session, binding, anchor, retained=retained)
                view.evidence_for(K.TRACE_FAMILY)
            self.assertEqual(retained.fingerprint(), before)
            self.assertEqual(fake.consumed, [])


if __name__ == "__main__":
    unittest.main()
