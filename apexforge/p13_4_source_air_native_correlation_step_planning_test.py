"""P13.4 mapping integrity, pure observation targets and execution separation."""
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

from language.compiler import SourceMap
from tooling.debug_metadata import MetadataAssociation, EvidenceReference
from tooling.debug_session import ExecutionReference, Capability
from tooling.debug_correlation import (
    Availability as A, StepMode as M, CorrelationError, Candidates,
    ObservedPosition, KnownObservationOrder, build_correlation, plan_next,
    inspect_lineage, correlate_inspection,
)
from tooling.debug_inspection import inspect_execution, bind_inspection
from tooling.trace_integration import associate_plan, execute_native_retained
from apexforge.native_backend.native_execution_contract import NativeExecutionError
from apexforge.native_backend.source_mapping import emit_native_source_mapping
from p12_6_4_source_native_mapping_test import compiler_fixture, native_fixture
from p12_6_3_metadata_identity_association_test import SOURCE
from p12_5_native_profile_contract_test import plan_for
from p13_2_debug_session_control_foundation_test import fixture as session_fixture


def source_inputs(sidecar=None):
    compiled, ledger, verified, source, mapping = compiler_fixture()
    sidecar = mapping.sidecar if sidecar is None else sidecar
    association = MetadataAssociation.for_plan(sidecar, verified, plan_for(verified.program),
        (SOURCE.encode(),), tuple(op.identity for op in sidecar.operations))
    execution = ExecutionReference("execution:source", association.air_fingerprint,
        association.routing_fingerprint, association.entry_directive, "canonical.runtime/v1")
    owner, fake = session_fixture(target=execution)
    args = dict(required_operations=tuple(op.identity for op in sidecar.operations),
        expected_sidecar_fingerprint=sidecar.fingerprint(),
        expected_association_fingerprint=association.fingerprint(), source_contents=(SOURCE.encode(),),
        native_status=A.NOT_APPLICABLE)
    if sidecar == mapping.sidecar:
        args.update(source_mapping=mapping, expected_source_mapping_fingerprint=mapping.fingerprint())
    return owner, fake, verified, sidecar, association, args, mapping


def source_index(sidecar=None):
    owner, fake, verified, sidecar, association, args, mapping = source_inputs(sidecar)
    return owner, build_correlation(owner.session, verified, sidecar, association, **args), mapping


def native_inputs():
    verified, plan, content, mapping = native_fixture()
    a = mapping.association
    execution = ExecutionReference("execution:native", a.air_fingerprint, a.routing_fingerprint,
                                   a.entry_directive, mapping.profile)
    owner, fake = session_fixture(target=execution)
    args = dict(required_operations=tuple(op.identity for op in mapping.sidecar.operations),
        expected_sidecar_fingerprint=mapping.sidecar.fingerprint(),
        expected_association_fingerprint=a.fingerprint(), native_mapping=mapping,
        expected_native_mapping_fingerprint=mapping.fingerprint(), generated_content=content)
    return owner, fake, verified, mapping, args


def position(index, ordinal=0, occurrence=0):
    return ObservedPosition(index.session, index.execution, index.fingerprint(),
                            index.chains[ordinal].air.operation.operation_id, occurrence, "trace:position")


def order(index, pos, ordinals, complete=False, boundaries=()):
    return KnownObservationOrder(pos, tuple(index.chains[i].air.operation.operation_id for i in ordinals),
                                 "trace:resolved-order", complete, boundaries)


def no_execution():
    stack = ExitStack()
    for path in (
        "workflow.air_runner.run_air_program", "runtime.engine.RuntimeEngine.execute",
        "apexforge.native_backend.native_execution.dispatch_native",
        "apexforge.native_backend.source_mapping.emit_native_source_mapping",
        "apexforge.native_backend.native_execution_contract.admit_native_profile",
        "apexforge.native_backend.execution_plan_binding.bind_registry_execution_plan",
        "language.compiler.compile_source_with_operation_evidence", "subprocess.Popen",
        "pathlib.Path.read_bytes", "pathlib.Path.write_bytes", "builtins.open",
    ):
        stack.enter_context(patch(path, side_effect=AssertionError("correlation invoked an owner or filesystem")))
    return stack


class CorrelationTests(unittest.TestCase):
    def test_real_compiler_source_air_references_deterministic_and_non_native(self):
        owner, a, mapping = source_index()
        _, b, _ = source_index()
        self.assertEqual(a.canonical_form(), b.canonical_form())
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertTrue(all(x.source.status is A.AVAILABLE and x.native.status is A.NOT_APPLICABLE
                            for x in a.chains))
        for chain in a.chains:
            source = chain.source.values[0]
            self.assertEqual(source.document, mapping.sidecar.sources[0])
            self.assertEqual(source.canonical_form(), replace(source).canonical_form())
            self.assertEqual(chain.air.canonical_form(), replace(chain.air).canonical_form())
            with self.assertRaises(FrozenInstanceError):
                source.construct = ()
        self.assertEqual(tuple(c.air.operation.ordinal for c in a.chains), (0, 1, 2))
        self.assertEqual(a.chains[1].air.directive, mapping.sidecar.operations[1].identity.locator.directive_id)

    def test_real_handbuilt_air_native_regions_without_fabricated_source(self):
        owner, fake, verified, mapping, args = native_inputs()
        with no_execution():
            index = build_correlation(owner.session, verified, mapping.sidecar, mapping.association, **args)
        self.assertTrue(all(c.source.status is A.UNAVAILABLE and not c.source.values
                            and c.native.status is A.AVAILABLE for c in index.chains))
        for c in index.chains:
            region = c.native.values[0]
            self.assertEqual(region.machine_address_availability, A.UNSUPPORTED)
            self.assertFalse(hasattr(region, "machine_address"))
            self.assertEqual(region.canonical_form(), replace(region).canonical_form())
            self.assertEqual(region.mapping_fingerprint, mapping.fingerprint())
        self.assertEqual(fake.consumed, [])

    def test_compiler_native_gap_is_not_fixed_by_expanding_frozen_profile(self):
        _, _, verified, _, _, _, mapping = source_inputs()
        with self.assertRaises(NativeExecutionError):
            emit_native_source_mapping(verified, plan_for(verified.program), source_mapping=mapping,
                                       source_contents=(SOURCE.encode(),))

    def test_missing_native_evidence_is_not_execution_failure(self):
        owner, fake, verified, sidecar, association, args, _ = source_inputs()
        args["native_status"] = A.UNAVAILABLE
        index = build_correlation(owner.session, verified, sidecar, association, **args)
        self.assertTrue(all(c.native.status is A.UNAVAILABLE for c in index.chains))
        self.assertEqual(fake.consumed, [])

    def test_synthetic_origin_is_not_owned_source(self):
        _, index, mapping = source_index()
        record = next(r for r in mapping.lineage if r.category == "COMPILER_SYNTHETIC"
                      and r.originating_entry_index >= 0)
        view = inspect_lineage(index, mapping, record.label)
        self.assertEqual(view.owned_source.status, A.UNAVAILABLE)
        self.assertEqual(view.origin.status, A.AVAILABLE)
        self.assertEqual(view.category, "COMPILER_SYNTHETIC")

    def test_stale_sidecar_source_mapping_association_and_content_rejected(self):
        owner, _, verified, sidecar, association, args, _ = source_inputs()
        for key in ("expected_sidecar_fingerprint", "expected_association_fingerprint",
                    "expected_source_mapping_fingerprint"):
            with self.subTest(key=key), self.assertRaises(CorrelationError):
                build_correlation(owner.session, verified, sidecar, association, **dict(args, **{key: "A" * 64}))
        with self.assertRaises(ValueError):
            build_correlation(owner.session, verified, sidecar, association,
                              **dict(args, source_contents=(b"changed",)))

    def test_cross_program_mapping_and_routing_rejected(self):
        owner, _, verified, sidecar, association, args, _ = source_inputs()
        _, _, other_verified, native, _ = native_inputs()
        with self.assertRaises(ValueError):
            build_correlation(owner.session, other_verified, sidecar, association, **args)
        with self.assertRaises(CorrelationError):
            build_correlation(owner.session, verified, sidecar, association, **dict(args,
                native_mapping=native, expected_native_mapping_fingerprint=native.fingerprint(),
                generated_content=b"invalid"))
        wrong = replace(association, routing_fingerprint="A" * 64)
        with self.assertRaises(CorrelationError):
            build_correlation(owner.session, verified, sidecar, wrong,
                              **dict(args, expected_association_fingerprint=wrong.fingerprint()))

    def test_native_mapping_generated_content_and_artifact_association_rejected(self):
        owner, _, verified, mapping, args = native_inputs()
        for changes in (dict(expected_native_mapping_fingerprint="A" * 64),
                        dict(generated_content=b"stale"), dict(artifact_association=object())):
            with self.subTest(changes=tuple(changes)), self.assertRaises(ValueError):
                build_correlation(owner.session, verified, mapping.sidecar, mapping.association,
                                  **dict(args, **changes))

    def test_semantic_target_uses_owner_resolved_order_not_metadata_adjacency(self):
        owner, index, _ = source_index()
        pos = position(index)
        unresolved = plan_next(index, owner.session, pos, M.SEMANTIC_STEP)
        self.assertEqual(unresolved.status, A.UNAVAILABLE)
        self.assertEqual(unresolved.reason, "needs_runtime_observation")
        supplied = order(index, pos, (0, 2, 1))  # controlled observed order, not metadata sort
        a = plan_next(index, owner.session, pos, M.SEMANTIC_STEP, supplied)
        b = plan_next(index, owner.session, replace(pos), M.SEMANTIC_STEP, replace(supplied))
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertEqual(a.targets[0].chain, index.chains[2])
        self.assertEqual(a.targets[0].ordering_key, (1, 2))
        a.targets[0].validate(index, owner.session)

    def test_unresolved_branch_never_guessed_from_complete_metadata(self):
        owner, index, _ = source_index()
        pos = position(index, 1)
        plan = plan_next(index, owner.session, pos, M.SEMANTIC_STEP, order(index, pos, (1,)))
        self.assertEqual(plan.status, A.UNAVAILABLE)
        self.assertFalse(plan.targets)
        ended = plan_next(index, owner.session, pos, M.SEMANTIC_STEP, order(index, pos, (1,), True))
        self.assertEqual(ended.status, A.NOT_APPLICABLE)
        self.assertEqual(ended.reason, "no_more_targets_in_supplied_window")

    def test_source_step_advances_distinct_source_span(self):
        owner, index, _ = source_index()
        pos = position(index, 1)
        plan = plan_next(index, owner.session, pos, M.SOURCE_STEP, order(index, pos, (1, 2)))
        self.assertEqual(plan.status, A.AVAILABLE)
        self.assertNotEqual(plan.targets[0].chain.source.values[0].location_key(),
                            index.chains[1].source.values[0].location_key())

    def test_source_step_collapses_repeated_same_span_and_skips_unmapped(self):
        # Controlled producer-side evidence fixture, not altered production compiler output.
        _, _, _, _, _, _, mapping = source_inputs()
        original = mapping.sidecar
        evidence = list(original.evidence)
        same = next(e for e in evidence if e.operation_id == original.operations[0].operation_id)
        evidence = [e for e in evidence if e.operation_id != original.operations[1].operation_id]
        evidence.append(EvidenceReference(original.operations[1].operation_id, same.source_index, same.source_map_index))
        evidence = tuple(sorted(evidence, key=lambda e: (e.operation_id, e.source_index, e.source_map_index)))
        owner, index, _ = source_index(replace(original, evidence=evidence))
        pos = position(index)
        plan = plan_next(index, owner.session, pos, M.SOURCE_STEP, order(index, pos, (0, 1, 2)))
        self.assertEqual(plan.targets[0].chain, index.chains[2])
        self.assertEqual(plan.targets[0].ordering_key[0], 2)
        without = replace(original, evidence=tuple(e for e in original.evidence
                           if e.operation_id != original.operations[1].operation_id))
        owner, index, _ = source_index(without)
        pos = position(index)
        plan = plan_next(index, owner.session, pos, M.SOURCE_STEP, order(index, pos, (0, 1, 2)))
        self.assertEqual(plan.targets[0].chain, index.chains[2])
        semantic = plan_next(index, owner.session, pos, M.SEMANTIC_STEP, order(index, pos, (0, 1, 2)))
        self.assertEqual(semantic.targets[0].chain.source.status, A.UNAVAILABLE)

    def test_ambiguous_source_candidates_are_preserved_and_deterministic(self):
        _, _, _, _, _, _, mapping = source_inputs()
        original = mapping.sidecar
        first = next(e for e in original.evidence if e.operation_id == original.operations[0].operation_id)
        extra = EvidenceReference(original.operations[1].operation_id, first.source_index, first.source_map_index)
        evidence = tuple(sorted(original.evidence + (extra,), key=lambda e:
                               (e.operation_id, e.source_index, e.source_map_index)))
        owner, index, _ = source_index(replace(original, evidence=evidence))
        candidates = index.chains[1].source
        self.assertEqual(candidates.status, A.AMBIGUOUS)
        self.assertEqual(len(candidates.values), 2)
        self.assertEqual(candidates.canonical_form(), Candidates(A.AMBIGUOUS,
                         tuple(reversed(candidates.values))).canonical_form())
        pos = position(index)
        plan = plan_next(index, owner.session, pos, M.SOURCE_STEP, order(index, pos, (0, 1, 2)))
        self.assertEqual(plan.status, A.AMBIGUOUS)
        self.assertEqual(plan.targets[0].chain.source, candidates)

    def test_native_correlation_is_current_generated_region_not_cpu_step(self):
        owner, fake, verified, mapping, args = native_inputs()
        index = build_correlation(owner.session, verified, mapping.sidecar, mapping.association, **args)
        pos = position(index, 2)
        with no_execution():
            plan = plan_next(index, owner.session, pos, M.NATIVE_CORRELATION_STEP)
        target = plan.targets[0]
        self.assertEqual(target.chain, index.chains[2])
        self.assertEqual(target.ordering_key, (0, 2))
        self.assertEqual(target.chain.native.values[0].span, mapping.regions[2].span)
        self.assertIn("no_machine_instruction_step", plan.reason)
        self.assertEqual(fake.consumed, [])
        unresolved = plan_next(index, owner.session, pos, M.SOURCE_STEP, order(index, pos, (2, 3)))
        self.assertEqual(unresolved.status, A.UNAVAILABLE)

    def test_directive_boundary_requires_owner_evidence_workflow_unsupported(self):
        owner, index, _ = source_index()
        pos = position(index)
        unresolved = plan_next(index, owner.session, pos, M.DIRECTIVE_STEP, order(index, pos, (0, 1, 2)))
        self.assertEqual(unresolved.status, A.UNAVAILABLE)
        evidence = order(index, pos, (0, 1, 2), boundaries=((1, index.chains[1].air.directive, "trace:entry"),))
        plan = plan_next(index, owner.session, pos, M.DIRECTIVE_STEP, evidence)
        self.assertEqual(plan.targets[0].evidence_reference, "trace:entry")
        bad = replace(evidence, directive_boundaries=((1, "directive:wrong", "trace:entry"),))
        with self.assertRaises(CorrelationError):
            plan_next(index, owner.session, pos, M.DIRECTIVE_STEP, bad)
        self.assertEqual(plan_next(index, owner.session, pos, M.WORKFLOW_STEP).status, A.UNSUPPORTED)

    def test_session_execution_target_and_stale_index_binding(self):
        owner, index, _ = source_index()
        pos = position(index)
        plan = plan_next(index, owner.session, pos, M.SEMANTIC_STEP, order(index, pos, (0, 1)))
        other, _ = session_fixture(session_id="session:other", target=index.execution)
        with self.assertRaises(CorrelationError):
            plan.targets[0].validate(index, other.session)
        for bad in (replace(pos, session=other.session.reference),
                    replace(pos, execution=replace(index.execution, execution_id="execution:other")),
                    replace(pos, index_fingerprint="A" * 64)):
            with self.assertRaises(CorrelationError):
                plan_next(index, owner.session, bad, M.SEMANTIC_STEP)
        owner.begin_close()
        owner.finish_close()
        with self.assertRaises(CorrelationError):
            plan.targets[0].validate(index, owner.session)

    def test_observe_capability_required_no_control_authority_implied(self):
        owner, _, verified, sidecar, association, args, _ = source_inputs()
        blocked, _ = session_fixture(target=owner.session.execution, capabilities=(Capability.ATTACH,), active=False)
        with self.assertRaises(CorrelationError):
            build_correlation(blocked.session, verified, sidecar, association, **args)
        observer, fake = session_fixture(target=owner.session.execution,
                                        capabilities=(Capability.ATTACH, Capability.OBSERVE))
        index = build_correlation(observer.session, verified, sidecar, association, **args)
        plan_next(index, observer.session, position(index), M.SEMANTIC_STEP)
        self.assertEqual(fake.consumed, [])

    def test_inspection_unchanged_and_cross_session_rejected(self):
        owner, _, verified, sidecar, association, args, _ = source_inputs()
        index = build_correlation(owner.session, verified, sidecar, association, **args)
        binding = associate_plan(verified, plan_for(verified.program))
        snapshot = inspect_execution(index.execution, binding)
        bound = bind_inspection(snapshot, owner.session)
        before = snapshot.canonical_form()
        with no_execution():
            result = correlate_inspection(index, owner.session, bound, index.chains[1].air.operation.operation_id)
        self.assertEqual(result, index.chains[1])
        self.assertEqual(snapshot.canonical_form(), before)
        other, _ = session_fixture(session_id="session:other", target=index.execution)
        with self.assertRaises(ValueError):
            correlate_inspection(index, owner.session, bind_inspection(snapshot, other.session),
                                 index.chains[1].air.operation.operation_id)

    def test_real_retained_native_artifact_binding_and_no_provenance_mutation(self):
        owner, _, verified, mapping, args = native_inputs()
        binding = associate_plan(verified, plan_for(verified.program))
        build = ROOT / "build"
        build.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p13-correlation-", dir=build) as directory:
            retained = execute_native_retained(binding, Path(directory))
            self.assertEqual(tuple(Path(directory).iterdir()), ())
        scope = retained.pre.scope
        execution = replace(owner.session.execution, provenance_fingerprint=scope.fingerprint())
        owner, fake = session_fixture(target=execution)
        args.update(artifact_association=retained.post, provenance_scope=scope,
                    expected_artifact_association_fingerprint=retained.post.fingerprint())
        before = retained.fingerprint()
        with no_execution():
            index = build_correlation(owner.session, verified, mapping.sidecar, mapping.association, **args)
        self.assertEqual(retained.fingerprint(), before)
        self.assertEqual(dict(index.chains[0].native.values[0].artifact_references)["image"],
                         retained.post.image_fingerprint)
        wrong = replace(retained.post, image_fingerprint="A" * 64)
        with self.assertRaises(CorrelationError):
            build_correlation(owner.session, verified, mapping.sidecar, mapping.association,
                              **dict(args, artifact_association=wrong))
        self.assertEqual(fake.consumed, [])

    def test_volatile_timestamp_excluded_and_no_incidental_process_fields(self):
        owner, index, _ = source_index()
        pos = position(index)
        a = replace(pos, timestamp="2026-01-01T00:00:00Z")
        b = replace(pos, timestamp="2030-01-01T00:00:00Z")
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertEqual(plan_next(index, owner.session, a, M.SEMANTIC_STEP).fingerprint(),
                         plan_next(index, owner.session, b, M.SEMANTIC_STEP).fingerprint())
        for text in (index.canonical_form(), pos.canonical_form()):
            self.assertNotIn(str(ROOT), text)
        self.assertFalse(any(name in pos.__dataclass_fields__ for name in
                             ("pid", "memory_address", "os_handle", "ui_state")))

    def test_static_and_dynamic_execution_separation(self):
        path = ROOT / "apexforge/tooling/debug_correlation.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        forbidden = {"run_air_program", "execute", "dispatch_native", "emit_native_source_mapping",
                     "compile_source", "compile_source_with_operation_evidence", "admit_native_profile",
                     "Popen", "open", "read_bytes", "write_bytes", "set_state", "mutate_state"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else "")
                self.assertNotIn(name, forbidden)
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn(node.module, ("workflow.air_runner", "runtime.engine", "subprocess"))
                self.assertFalse(any(x.name in forbidden for x in node.names))
        owner, _, verified, sidecar, association, args, _ = source_inputs()
        with no_execution():
            index = build_correlation(owner.session, verified, sidecar, association, **args)
            pos = position(index)
            plan = plan_next(index, owner.session, pos, M.SEMANTIC_STEP, order(index, pos, (0, 1, 2)))
        self.assertEqual(plan.status, A.AVAILABLE)


if __name__ == "__main__":
    unittest.main()
