"""P12.6-8 integration acceptance: opt-in neutrality and fail-closed boundaries."""
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
from tooling.trace_integration import (compile_with_metadata, associate_plan, ManagedContextIdentity,
    execute_managed_retained, NativePreDispatch, dispatch_native_retained, execute_native_retained,
    RetentionLimits, ObservationError)
from tooling.trace_retention import TraceFamily, TraceCollection, RuntimeEvidence, RetainedRecord, TAMEvidence, OperationAssociation
from language.compiler import compile_source_with_map
from air.verify import AIRVerifier
from air.model import Fact
from workflow.air_runner import build_default_context, RegistryExecutionPlan, build_registry_execution_plan
from runtime.engine import RuntimeEngine, ExecutionResult
from runtime.context import ExecutionContext
from runtime.state import StateSnapshot
from authority.engine import AuthorityEngine
from causality.engine import CausalEngine
from standard_library.core import DEFAULT_STANDARD_LIBRARY
from apexforge.native_backend.result import CanonicalExecutionResult
from apexforge.native_backend import native_execution as native
from apexforge.native_backend.source_mapping import build_native_with_mapping
from apexforge.native_backend.native_execution_contract import NativeExecutionError
from p12_6_3_metadata_identity_association_test import SOURCE
from p12_6_4_source_native_mapping_test import native_fixture
from p12_5_native_profile_contract_test import plan_for


def managed_fixture():
    metadata = compile_with_metadata(SOURCE.encode(), "src/main.apex")
    plan = plan_for(metadata.compiled.program)
    return metadata, associate_plan(metadata.verified, plan, metadata)


class CompilerPlanTests(unittest.TestCase):
    def test_compiler_neutrality_determinism_and_source_diagnostics(self):
        ordinary = compile_source_with_map(SOURCE, source_name="src/main.apex")
        metadata, binding = managed_fixture()
        self.assertEqual(ordinary, metadata.compiled)
        self.assertEqual(AIRVerifier().verify(ordinary.program).require_verified(), metadata.verified)
        self.assertEqual(ordinary.program.causal_decisions[0].paths[0].actions,
                         metadata.compiled.program.causal_decisions[0].paths[0].actions)
        self.assertTrue(ordinary.program.causal_decisions[0].paths[0].actions)
        again, second = managed_fixture()
        self.assertEqual(metadata.fingerprint(), again.fingerprint())
        self.assertEqual(binding.fingerprint(), second.fingerprint())
        self.assertTrue(any(r.operation is not None for r in metadata.tam.records))
        bad_source = SOURCE.replace("set count", "set missing")
        errors = []
        for call in (lambda: compile_source_with_map(bad_source, source_name="src/main.apex"),
                     lambda: compile_with_metadata(bad_source.encode(), "src/main.apex")):
            try:
                call()
            except Exception as exc:
                errors.append(exc)
        self.assertEqual(len(errors), 2)
        self.assertEqual(type(errors[0]), type(errors[1]))
        self.assertEqual(errors[0].diagnostic, errors[1].diagnostic)
        multi = "directive One { state x = 0 }\ndirective Two { state y = 0 }"
        self.assertEqual(len(compile_source_with_map(multi).program.directives), 2)
        with self.assertRaises(ValueError):
            compile_with_metadata(multi.encode(), "src/multi.apex")

    def test_actual_registry_plan_and_stale_components(self):
        metadata, binding = managed_fixture()
        class Registry:
            def resolve(self, name):
                return metadata.compiled.program
        actual = build_registry_execution_plan(Registry(), "Main")
        actual_verified = AIRVerifier().verify(actual.program).require_verified()
        actual_binding = associate_plan(actual_verified, actual, metadata)
        actual_binding.validate()
        self.assertEqual(actual_binding.association.routing_fingerprint, binding.association.routing_fingerprint)
        for field in ("air_fingerprint", "routing_fingerprint", "sidecar_fingerprint"):
            with self.assertRaises(ValueError):
                replace(binding, association=replace(binding.association, **{field: "0" * 64})).validate()
        with self.assertRaises(ValueError):
            replace(binding, mapping_fingerprint="0" * 64).validate()
        with self.assertRaises(ValueError):
            replace(metadata, content=metadata.content + b" ").validate()
        stale_map = replace(metadata.mapping, sidecar=replace(metadata.mapping.sidecar, air_fingerprint="0" * 64,
                                                             operations=(), evidence=()), correspondence=())
        with self.assertRaises(ValueError):
            replace(metadata, mapping=stale_map).validate()
        changed = replace(actual.program, states=(replace(actual.program.states[0], initial=99),))
        with self.assertRaises(ValueError):
            associate_plan(AIRVerifier().verify(changed).require_verified(), plan_for(changed), metadata)
        with self.assertRaises(ValueError):
            replace(binding, plan=replace(binding.plan, entry_directive="directive:Missing")).validate()
        key = next(iter(binding.plan.directive_owners))
        binding.plan.directive_owners[key] = changed
        with self.assertRaises(ValueError):
            binding.validate()

    def test_forged_producer_and_limits_reject(self):
        metadata, binding = managed_fixture()
        with self.assertRaises(ValueError):
            replace(metadata.tam.records[0], evidence=TAMEvidence(replace(metadata.tam.records[0].evidence.record, producer="forged.owner")))
        with self.assertRaises(ValueError):
            compile_with_metadata(SOURCE.encode(), "C:/host/source.apex")
        with self.assertRaises(ValueError):
            compile_with_metadata(SOURCE.encode(), "src/main.apex", limits=RetentionLimits(source_bytes=1))
        with self.assertRaises(FrozenInstanceError):
            metadata.content = b"changed"


class ManagedTests(unittest.TestCase):
    def test_exactly_once_neutrality_order_and_determinism(self):
        metadata, binding = managed_fixture()
        context = build_default_context(binding.verified.program)
        baseline = RuntimeEngine().execute(binding.verified, context, entry_directives=(binding.plan.entry_directive,))
        execute, select, allows = RuntimeEngine.execute, CausalEngine.select_path, AuthorityEngine.allows
        with patch.object(RuntimeEngine, "execute", autospec=True, side_effect=execute) as run, \
             patch.object(CausalEngine, "select_path", autospec=True, side_effect=select) as causal, \
             patch.object(AuthorityEngine, "allows", autospec=True, side_effect=allows) as authority:
            retained = execute_managed_retained(binding, context=context)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(causal.call_count, 1)
        self.assertEqual(authority.call_count, 1)
        self.assertEqual(retained.result, baseline)
        self.assertIs(type(retained.result), ExecutionResult)
        repeated = execute_managed_retained(binding, context=context)
        self.assertEqual(retained.fingerprint(), repeated.fingerprint())
        retained.validate(binding, context, RuntimeEngine(), baseline)
        by_family = {c.family: c for c in retained.collections}
        for ref in retained.interleaving:
            record = by_family[ref.family].records[ref.ordinal]
            self.assertEqual(record.evidence.record, baseline.trace.steps[ref.parent_index])
            self.assertIsNone(record.operation)
        self.assertEqual(tuple(r.parent_index for r in retained.interleaving), tuple(range(len(baseline.trace.steps))))
        state_records = tuple(r for r in by_family[TraceFamily.RUNTIME].records if r.evidence.record.kind == "state.delta")
        self.assertEqual(len(state_records), 2)
        self.assertNotEqual(state_records[0].identity(), state_records[1].identity())
        with self.assertRaises(ValueError):
            replace(state_records[0], operation=OperationAssociation(metadata.mapping.sidecar.operations[-1], 0))
        self.assertEqual(tuple(f.name for f in fields(CanonicalExecutionResult)), ("input_fingerprint", "status", "outputs"))

    def test_wrong_context_and_custom_owners_reject_before_execution(self):
        metadata, binding = managed_fixture()
        context = build_default_context(binding.verified.program)
        runtime = RuntimeEngine()
        identity = ManagedContextIdentity.capture(binding, context, runtime)
        class CustomRuntime(RuntimeEngine):
            pass
        class CustomPolicy:
            def allows(self, check):
                raise AssertionError("policy must not be probed")
        class CustomCausality(CausalEngine):
            pass
        variants = (
            dict(runtime=CustomRuntime()),
            dict(context=ExecutionContext(context.state, CustomPolicy())),
            dict(runtime=RuntimeEngine(causality=CustomCausality())),
            dict(runtime=RuntimeEngine(standard_library=DEFAULT_STANDARD_LIBRARY.with_entries(()))),
            dict(expected_context=replace(identity, policy_fingerprint="0" * 64)),
            dict(expected_context=identity, runtime=RuntimeEngine(max_invocation_depth=2)),
            dict(expected_context=identity, context=ExecutionContext(StateSnapshot.from_mapping({"state:count": 9}), context.authority)),
            dict(context=ExecutionContext(StateSnapshot.from_mapping({"state:count": "C:/host/private"}), context.authority)),
        )
        with patch.object(RuntimeEngine, "execute", side_effect=AssertionError("preflight must reject")):
            for kwargs in variants:
                with self.assertRaises(ValueError):
                    execute_managed_retained(binding, **kwargs)

    def test_payload_order_duplicate_and_context_substitution(self):
        metadata, binding = managed_fixture()
        context, runtime = build_default_context(binding.verified.program), RuntimeEngine()
        retained = execute_managed_retained(binding, context=context, runtime=runtime)
        steps = list(retained.result.trace.steps)
        index = next(i for i, s in enumerate(steps) if s.kind == "state.delta")
        steps[index] = replace(steps[index], facts=tuple(Fact(f.key, 99) if f.key == "value" else f for f in steps[index].facts))
        changed_result = replace(retained.result, trace=replace(retained.result.trace, steps=tuple(steps)))
        with self.assertRaises(ValueError):
            replace(retained, result=changed_result).validate(binding, context, runtime, retained.result)
        for field in retained.context.__dataclass_fields__:
            with self.assertRaises(ValueError):
                replace(retained, context=replace(retained.context, **{field: "0" * 64})).validate(binding, context, runtime, retained.result)
        with self.assertRaises(ValueError):
            replace(retained, unsupported=([0, "unsupported.event"],))
        collection = retained.collections[0]
        with self.assertRaises(ValueError):
            replace(collection, records=(collection.records[0], collection.records[0]))
        with self.assertRaises(ValueError):
            replace(retained, interleaving=tuple(reversed(retained.interleaving))).validate(binding, context, runtime, retained.result)
        with self.assertRaises(ValueError):
            replace(retained, result_fingerprint="0" * 64).validate(binding, context, runtime, retained.result)

    def test_explicit_partial_coverage_and_retention_limit_preserve_result(self):
        source = SOURCE.replace("set count = 1\n            set count = 1", "invoke Other") + """
directive Other {
 state other = 0
 cause second { path p @ 1 { set other = 2 } }
}
"""
        compiled = compile_source_with_map(source)
        verified = AIRVerifier().verify(compiled.program).require_verified()
        plan = RegistryExecutionPlan(compiled.program, "directive:Main", {d.id.casefold(): compiled.program for d in compiled.program.directives})
        binding = associate_plan(verified, plan)
        baseline = RuntimeEngine().execute(verified, build_default_context(compiled.program), entry_directives=(plan.entry_directive,))
        with self.assertRaises(ObservationError) as caught:
            execute_managed_retained(binding)
        self.assertEqual(caught.exception.owner_result, baseline)
        partial = execute_managed_retained(binding, require_complete=False)
        self.assertEqual(partial.result, baseline)
        self.assertTrue(partial.unsupported)
        self.assertTrue(any("invoke" in kind for _, kind in partial.unsupported))
        with self.assertRaises(ObservationError) as limited:
            execute_managed_retained(binding, require_complete=False, limits=RetentionLimits(records=1))
        self.assertEqual(limited.exception.owner_result, baseline)

    def test_no_second_semantics_audit_and_revalidation_without_execution(self):
        tree = ast.parse((ROOT / "apexforge/tooling/trace_integration.py").read_text())
        forbidden = {"id", "eval", "exec", "infer_type", "resolve", "select_path", "allows", "_evaluate_assignment", "_decode"}
        calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute))}
        self.assertFalse(calls & forbidden)
        self.assertEqual(sum(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "execute" for n in ast.walk(tree)), 1)
        metadata, binding = managed_fixture()
        context, runtime = build_default_context(binding.verified.program), RuntimeEngine()
        retained = execute_managed_retained(binding, context=context, runtime=runtime)
        with patch.object(RuntimeEngine, "execute", side_effect=AssertionError("replay")), \
             patch.object(CausalEngine, "select_path", side_effect=AssertionError("reselect")), \
             patch.object(AuthorityEngine, "allows", side_effect=AssertionError("recheck")):
            metadata.validate()
            binding.validate()
            retained.validate(binding, context, runtime, retained.result)


class NativeTests(unittest.TestCase):
    def test_live_pre_post_determinism_neutrality_and_cleanup(self):
        verified, plan, content, mapping = native_fixture()
        binding = associate_plan(verified, plan)
        build_root = ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p12-6-8-", dir=build_root) as directory:
            baseline = native.execute_native(verified, plan, Path(directory))
            dispatch = native.dispatch_native
            images = []
            builder = build_native_with_mapping
            def capture(*args, **kwargs):
                mapped = builder(*args, **kwargs)
                images.append(mapped.artifact.image)
                return mapped
            with patch("tooling.trace_integration.build_native_with_mapping", side_effect=capture), \
                 patch.object(native, "dispatch_native", wraps=dispatch) as run:
                retained = execute_native_retained(binding, Path(directory))
                self.assertEqual(run.call_count, 1)
            repeated = execute_native_retained(binding, Path(directory))
            self.assertEqual(retained.evidence, baseline)
            self.assertEqual(retained.evidence, repeated.evidence)
            self.assertEqual(retained.fingerprint(), repeated.fingerprint())
            self.assertEqual(retained.pre.fingerprint(), repeated.pre.fingerprint())
            self.assertEqual(retained.pre.image_fingerprint, repeated.pre.image_fingerprint)
            self.assertEqual(retained.pre.receipt_fingerprint, baseline.result.input_fingerprint)
            self.assertEqual(retained.pre.scope.generated_c_fingerprint, native.digest(content))
            self.assertTrue(all(not p.exists() and not p.parent.exists() for p in images))
            retained.validate_snapshot(binding, baseline)
            self.assertIsNone(retained.collection.records[0].operation)
            for field in retained.post.__dataclass_fields__:
                with self.assertRaises(ValueError):
                    replace(retained, post=replace(retained.post, **{field: "0" * 64})).validate_snapshot(binding, baseline)
            for changed in (replace(baseline, output_fingerprint="0" * 64),
                            replace(baseline, result=replace(baseline.result, status="FAILURE")),
                            replace(baseline, receipt_json="{}")):
                with self.assertRaises(ValueError):
                    retained.validate_snapshot(binding, changed)

    def test_pre_dispatch_negatives_reject_before_run(self):
        verified, plan, content, mapping = native_fixture()
        binding = associate_plan(verified, plan)
        root = ROOT / "build"
        root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p12-6-8-pre-", dir=root) as directory:
            mapped = build_native_with_mapping(verified, plan, Path(directory))
            pre = NativePreDispatch.capture(binding, mapped)
            with patch.object(native, "dispatch_native", side_effect=AssertionError("must reject before dispatch")):
                for field in ("receipt_fingerprint", "image_fingerprint", "mapping_fingerprint"):
                    with self.assertRaises(ValueError):
                        dispatch_native_retained(binding, mapped, pre=replace(pre, **{field: "0" * 64}))
                with self.assertRaises(ValueError):
                    dispatch_native_retained(binding, replace(mapped, mapping_fingerprint="0" * 64))
                with self.assertRaises(ValueError):
                    dispatch_native_retained(binding, replace(mapped, receipt_fingerprint="0" * 64))
                mapped.artifact.image.write_bytes(mapped.artifact.image.read_bytes() + b" ")
                with self.assertRaises(ValueError):
                    dispatch_native_retained(binding, mapped, pre=pre)

    def test_failure_exception_and_post_dispatch_image_substitution(self):
        verified, plan, content, mapping = native_fixture()
        binding = associate_plan(verified, plan)
        root = ROOT / "build"
        root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p12-6-8-post-", dir=root) as directory:
            mapped = build_native_with_mapping(verified, plan, Path(directory))
            with patch.object(native, "_run", side_effect=NativeExecutionError("NATIVE_EXECUTION_FAILED", "original detail")):
                with self.assertRaises(NativeExecutionError) as caught:
                    dispatch_native_retained(binding, mapped)
            self.assertEqual(caught.exception.code, "NATIVE_EXECUTION_FAILED")
            self.assertEqual(str(caught.exception), "NATIVE_EXECUTION_FAILED: original detail")
            self.assertEqual(caught.exception.p12_6_observation.pre_dispatch_fingerprint, NativePreDispatch.capture(binding, mapped).fingerprint())
            dispatch = native.dispatch_native
            def altered(*args, **kwargs):
                evidence = dispatch(*args, **kwargs)
                mapped.artifact.image.write_bytes(mapped.artifact.image.read_bytes() + b" ")
                return evidence
            with patch.object(native, "dispatch_native", side_effect=altered):
                with self.assertRaises(ObservationError) as failed:
                    dispatch_native_retained(binding, mapped)
            self.assertIsInstance(failed.exception.owner_result, native.NativeExecutionEvidence)

    def test_compiler_actions_still_not_native_admitted(self):
        metadata, binding = managed_fixture()
        actions = metadata.compiled.program.causal_decisions[0].paths[0].actions
        root = ROOT / "build"
        root.mkdir(exist_ok=True)
        with patch.object(native, "build_native", side_effect=AssertionError("admission must reject first")):
            with self.assertRaises(NativeExecutionError):
                execute_native_retained(binding, root)
        self.assertEqual(metadata.compiled.program.causal_decisions[0].paths[0].actions, actions)
        self.assertTrue(actions)

if __name__ == "__main__":
    unittest.main(verbosity=2)
