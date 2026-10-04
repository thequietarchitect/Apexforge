"""P13.3 canonical evidence projections, passivity and redaction boundaries."""
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

from air.model import StateDefinition, VerifiedAIRProgram
from air.verify import AIRVerifier
from authority.model import Principal
from authority.engine import AuthorityEngine
from runtime.engine import RuntimeEngine
from runtime.call_stack import CallFrame, LocalBinding
from runtime.state import StateSnapshot, StateCell
from type_system.model import BOOL, FLOAT, INT, STRING
from tooling.trace_integration import (
    execute_managed_retained, execute_native_retained, associate_plan,
    managed_result_fingerprint,
)
from tooling.trace_retention import TraceFamily
from tooling.debug_session import ExecutionReference, Capability as C
from tooling.debug_inspection import (
    Availability as A, InspectionError, InspectionField, InspectionSnapshot,
    available, missing, inspect_state, state_difference, inspect_execution,
    inspect_mapping, inspect_authority, inspect_principal, inspect_frame, bind_inspection,
)
from p12_6_8_controlled_trace_integration_test import managed_fixture
from p12_6_4_source_native_mapping_test import native_fixture
from p12_5_native_profile_contract_test import plan_for
from p13_2_debug_session_control_foundation_test import fixture as session_fixture


def reference(binding, retained=None, identifier="execution:inspection"):
    scope = retained.pre.scope if retained is not None and hasattr(retained, "pre") else (
        retained.scope if retained is not None else None)
    return ExecutionReference(identifier, binding.association.air_fingerprint,
        binding.association.routing_fingerprint, binding.association.entry_directive,
        scope.native_profile if scope is not None and scope.native_profile else "canonical.runtime/v1",
        "" if scope is None else scope.fingerprint())


def directive_entry(retained):
    return next(r for c in retained.collections if c.family is TraceFamily.RUNTIME
                for r in c.records if r.evidence.record.kind == "directive.start")


def no_semantic_calls():
    guards = ExitStack()
    for path in (
        "runtime.engine.RuntimeEngine.execute", "authority.engine.AuthorityEngine.allows",
        "runtime.engine.RuntimeEngine._evaluate_assignment", "runtime.engine.RuntimeEngine._evaluate_expression",
        "causality.engine.CausalEngine.select_path", "runtime.state.StateSnapshot.apply",
        "workflow.air_runner.run_air_program", "workflow.air_runner.build_registry_execution_plan",
        "apexforge.native_backend.execution_plan_binding.bind_registry_execution_plan",
        "apexforge.native_backend.native_execution.dispatch_native",
        "apexforge.native_backend.source_mapping.emit_native_source_mapping",
    ):
        guards.enter_context(patch(path, side_effect=AssertionError("inspector invoked semantic owner")))
    return guards


class InspectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata, cls.binding = managed_fixture()
        # Canonical owner executes before inspector traps are installed.
        cls.retained = execute_managed_retained(cls.binding)
        cls.execution = reference(cls.binding, cls.retained)

    def view(self, **kwargs):
        return inspect_execution(self.execution, self.binding, retained=self.retained,
                                 directive_record=directive_entry(self.retained), **kwargs)

    def test_state_order_immutable_values_and_existing_types(self):
        program = replace(self.binding.verified.program, states=(
            StateDefinition("state:z", "text", STRING), StateDefinition("state:b", False, BOOL),
            StateDefinition("state:a", 7, INT), StateDefinition("state:f", 1.25, FLOAT),
        ), causal_decisions=(), directives=(replace(self.binding.verified.program.directives[0], causal_decisions=()),))
        verified = AIRVerifier().verify(program).require_verified()
        binding = associate_plan(verified, plan_for(program))
        target = reference(binding)
        supplied = StateSnapshot((StateCell("state:z", "text"), StateCell("state:b", True),
                                  StateCell("state:a", 7), StateCell("state:f", 1.25)))
        with no_semantic_calls():
            view = inspect_state(target, program, supplied)
        self.assertEqual(tuple(e.key for e in view.entries), ("state:a", "state:b", "state:f", "state:z"))
        self.assertEqual(tuple(e.observed_value.value for e in view.entries),
                         (("int", 7), ("bool", True), ("float", 1.25), ("str", "text")))
        self.assertEqual(tuple(e.declared_type.value[0] for e in view.entries), ("int", "bool", "float", "string"))
        with self.assertRaises(FrozenInstanceError):
            view.entries[0].key = "other"
        self.assertEqual(supplied.cells[0].value, 7)

    def test_missing_state_and_availability_are_explicit(self):
        with no_semantic_calls():
            view = inspect_execution(reference(self.binding), self.binding)
        self.assertEqual(view.state.capture.status, A.UNAVAILABLE)
        self.assertTrue(all(e.observed_value.status is A.UNAVAILABLE for e in view.state.entries))
        self.assertEqual(view.result.status, A.UNAVAILABLE)
        self.assertEqual(view.directive.status, A.UNAVAILABLE)
        for status in (A.UNAVAILABLE, A.UNSUPPORTED, A.NOT_APPLICABLE, A.REDACTED):
            self.assertEqual(missing("explicit", status).status, status)
            with self.assertRaises(InspectionError):
                InspectionField(status, 0, "explicit")
        with self.assertRaises(InspectionError):
            available([])
        self.assertEqual(available(()).status, A.AVAILABLE)

    def test_structural_difference_does_not_explain_cause(self):
        program = self.binding.verified.program
        before = inspect_state(self.execution, program, StateSnapshot((StateCell("state:count", 0),)))
        after = inspect_state(self.execution, program, self.retained.result.final_state)
        difference = state_difference(before, after)
        self.assertEqual(difference.changed_keys.value, ("state:count",))
        self.assertEqual(difference.cause.status, A.UNAVAILABLE)
        self.assertEqual(difference.cause.reason, "state_difference_is_not_causal_evidence")
        self.assertEqual(state_difference(after, after).changed_keys.value, ())
        unavailable = inspect_state(self.execution, program)
        self.assertEqual(state_difference(unavailable, after).changed_keys.status, A.UNAVAILABLE)

    def test_bool_int_and_redacted_difference_not_normalized(self):
        program = self.binding.verified.program
        a = inspect_state(self.execution, program, StateSnapshot((StateCell("state:count", True),)))
        b = inspect_state(self.execution, program, StateSnapshot((StateCell("state:count", 1),)))
        self.assertEqual(state_difference(a, b).changed_keys.value, ("state:count",))
        hidden = inspect_state(self.execution, program, self.retained.result.final_state,
                               redacted_keys=("state:count",))
        self.assertEqual(state_difference(hidden, b).changed_keys.status, A.UNAVAILABLE)

    def test_directive_context_is_observed_entry_not_live_activation(self):
        with no_semantic_calls():
            view = self.view()
        directive = self.binding.verified.program.directives[0]
        self.assertEqual(view.directive.value[1], directive.id)
        self.assertEqual(view.directive.value[4], True)
        self.assertEqual(view.directive.value[5], directive.causal_decisions)
        self.assertEqual(view.directive.value[-1], "retained_entry_observation_not_live_activation")
        self.assertEqual(view.principal.value[1], directive.principal)
        self.assertEqual(view.stack.status, A.UNAVAILABLE)

    def test_principal_roles_are_not_capability_or_authority(self):
        p = Principal("principal:actor", roles=("role:z", "role:a"))
        with no_semantic_calls():
            projection = inspect_principal(self.execution, p)
        self.assertEqual(projection.value[1:], (p.id, ("role:a", "role:z")))
        observed = self.view().authority
        self.assertEqual(observed.status, A.AVAILABLE)
        self.assertTrue(observed.value)
        facts = observed.value[0][1]
        self.assertIs(type(facts[6]), bool)
        self.assertNotEqual(facts[3], facts[4])  # principal and capability separate

    def test_observed_authority_does_not_grant_debugger_control(self):
        view = self.view()
        manager, fake = session_fixture(target=self.execution,
                                       capabilities=(C.ATTACH, C.OBSERVE))
        with no_semantic_calls():
            bound = bind_inspection(view, manager.session)
        self.assertNotEqual(manager.session.reference.principal_id, view.principal.value[1])
        self.assertEqual(fake.consumed, [])
        self.assertEqual(bound.snapshot.authority, view.authority)
        self.assertEqual(len(manager.session.granted), 2)

    def test_authority_evidence_identity_and_no_policy_evaluation(self):
        record = next(r for c in self.retained.collections if c.family is TraceFamily.AUTHORITY for r in c.records)
        with no_semantic_calls():
            projected = inspect_authority(self.binding.verified.program, record)
        self.assertEqual(projected.value[0], record.identity())
        facts = {f.key: f.value for f in record.evidence.record.facts}
        self.assertEqual(projected.value[2:7], tuple(facts[k] for k in ("check", "principal", "capability", "resource", "allowed")))

    def test_plan_routing_and_result_associations_preserved(self):
        with no_semantic_calls():
            view = self.view()
        self.assertEqual(view.plan.value[:3], (self.binding.fingerprint(),
            self.binding.association.fingerprint(), self.execution.routing_fingerprint))
        self.assertEqual(view.plan.value[3], self.execution.entry_directive)
        self.assertEqual(view.result.value[1], ("ok", self.retained.result.ok))
        self.assertEqual(view.result.value[2], self.retained.result_fingerprint)
        self.assertEqual(view.result.value[-1], self.retained.fingerprint())

    def test_managed_failure_classification_preserved(self):
        # Owner performs its required check with an empty policy; inspector does not.
        from runtime.context import ExecutionContext
        from workflow.air_runner import build_default_context
        default = build_default_context(self.binding.verified.program)
        denied = execute_managed_retained(self.binding,
            context=ExecutionContext(default.state, AuthorityEngine()))
        target = reference(self.binding, denied)
        with no_semantic_calls():
            view = inspect_execution(target, self.binding, retained=denied)
        self.assertEqual(view.result.value[1], ("ok", False))
        self.assertIn("RUN001", tuple(d[1] for d in view.diagnostics.value))
        self.assertIs(view.authority.value[0][1][6], False)

    def test_source_air_mapping_reused_without_stepping(self):
        with no_semantic_calls():
            view = self.view()
        mapping = self.metadata.mapping
        self.assertEqual(view.correlation.value[0], mapping.fingerprint())
        rows = view.correlation.value[1]
        self.assertEqual(tuple(row[0] for row in rows), tuple(op.operation_id for op in mapping.sidecar.operations))
        self.assertTrue(all(row[2][0] == "available" for row in rows))
        self.assertTrue(all(row[4][0] == "unsupported" for row in rows))
        self.assertEqual(view.state.entries[0].source_air.status, A.AVAILABLE)

    def test_hand_built_air_generated_region_and_unmapped_source(self):
        verified, plan, content, mapping = native_fixture()
        binding = associate_plan(verified, plan)
        target = replace(reference(binding), profile=mapping.profile)
        with no_semantic_calls():
            projection = inspect_mapping(target, mapping)
        self.assertEqual(projection.value[0], mapping.fingerprint())
        for row in projection.value[1]:
            self.assertEqual(row[2][0:3:2], ("unavailable", "UNMAPPED_SOURCE"))
            self.assertEqual(row[3][0], "available")
            self.assertEqual(row[4][0], "unsupported")
        self.assertNotIn("machine_address", repr(projection.value[1][0][3]))

    def test_trace_provenance_references_not_payload_copies(self):
        view = self.view()
        refs = view.provenance.value
        self.assertEqual(refs[0], self.retained.scope.fingerprint())
        self.assertEqual(refs[1], self.retained.fingerprint())
        self.assertEqual(refs[2], tuple((c.family.value, c.fingerprint()) for c in self.retained.collections))
        self.assertNotIn("entered directive", view.canonical_form())
        self.assertEqual(refs[3], self.retained.unsupported)

    def test_session_execution_binding_and_close(self):
        view = self.view()
        manager, _ = session_fixture(target=self.execution)
        with no_semantic_calls():
            bound = bind_inspection(view, manager.session)
            bound.validate_session(manager.session)
        foreign, _ = session_fixture(session_id="session:foreign", target=self.execution)
        with self.assertRaises(InspectionError):
            bound.validate_session(foreign.session)
        manager.begin_close()
        with self.assertRaises(InspectionError):
            bound.validate_session(manager.session)

    def test_cross_execution_relabeling_and_retention_mismatch_rejected(self):
        view = self.view()
        other = replace(self.execution, execution_id="execution:other")
        with self.assertRaises(InspectionError):
            replace(view, execution=other)
        other_manager, _ = session_fixture(target=other)
        with self.assertRaises(InspectionError):
            bind_inspection(view, other_manager.session)
        with self.assertRaises(InspectionError):
            inspect_execution(replace(self.execution, provenance_fingerprint="0" * 64),
                              self.binding, retained=self.retained)
        with self.assertRaises(InspectionError):
            inspect_execution(replace(self.execution, routing_fingerprint="0" * 64), self.binding)
        with self.assertRaises(InspectionError):
            inspect_execution(self.execution, self.binding,
                retained=replace(self.retained, result_fingerprint="0" * 64))

    def test_redacted_value_has_no_repr_serialization_or_hash_side_channel(self):
        program = self.binding.verified.program
        a = inspect_state(self.execution, program, StateSnapshot((StateCell("state:count", "PRIVATE_ALPHA"),)),
                          redacted_keys=("state:count",))
        b = inspect_state(self.execution, program, StateSnapshot((StateCell("state:count", "PRIVATE_BETA"),)),
                          redacted_keys=("state:count",))
        self.assertEqual(a.canonical_form(), b.canonical_form())
        self.assertNotIn("PRIVATE_ALPHA", repr(a))
        self.assertNotIn("PRIVATE_ALPHA", a.canonical_form())
        view = self.view(redacted_keys=("state:count",))
        self.assertEqual(view.result.status, A.REDACTED)
        self.assertEqual(view.provenance.status, A.REDACTED)
        self.assertEqual(view.state.entries[0].observed_value.status, A.REDACTED)
        self.assertNotIn(self.retained.result_fingerprint, view.canonical_form())
        self.assertNotIn(self.retained.scope.fingerprint(), view.canonical_form())
        self.assertNotIn(self.retained.scope.fingerprint(), repr(view))
        self.assertEqual(view.fingerprint(), replace(view, timestamp="different time").fingerprint())
        with self.assertRaises(InspectionError) as error:
            InspectionField(A.REDACTED, "PRIVATE_ALPHA", "redacted")
        self.assertNotIn("PRIVATE_ALPHA", str(error.exception))

    def test_deterministic_fresh_observation_and_volatile_fields(self):
        metadata, binding = managed_fixture()
        retained = execute_managed_retained(binding)
        target = reference(binding, retained)
        other = inspect_execution(target, binding, retained=retained, directive_record=directive_entry(retained), timestamp="later")
        self.assertEqual(self.view().canonical_form(), other.canonical_form())
        self.assertEqual(self.view().fingerprint(), other.fingerprint())
        self.assertNotIn("later", repr(other))
        self.assertEqual(self.view().state.canonical_form(), other.state.canonical_form())

    def test_real_managed_semantic_passivity(self):
        result = self.retained.result
        before = (self.retained.fingerprint(), managed_result_fingerprint(result), result.final_state,
                  self.metadata.fingerprint(), self.binding.fingerprint())
        with no_semantic_calls():
            view = self.view()
        after = (self.retained.fingerprint(), managed_result_fingerprint(result), result.final_state,
                 self.metadata.fingerprint(), self.binding.fingerprint())
        self.assertEqual(before, after)
        self.assertEqual(view.state.entries[0].observed_value.value, ("int", 1))
        self.assertIs(self.retained.result, result)

    def test_real_native_retained_result_passivity_and_references(self):
        verified, plan, _, _ = native_fixture()
        binding = associate_plan(verified, plan)
        build = ROOT / "build"
        build.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p13-inspection-", dir=build) as directory:
            retained = execute_native_retained(binding, Path(directory))
            self.assertEqual(tuple(Path(directory).iterdir()), ())
        target = reference(binding, retained)
        before = (retained.fingerprint(), retained.evidence.result.fingerprint(), retained.mapping.fingerprint())
        with no_semantic_calls():
            view = inspect_execution(target, binding, retained=retained)
        self.assertEqual(before, (retained.fingerprint(), retained.evidence.result.fingerprint(), retained.mapping.fingerprint()))
        self.assertEqual(view.result.value[1], retained.evidence.result.status)
        self.assertEqual(view.result.value[-1], retained.post.fingerprint())
        self.assertIn(retained.post.receipt_fingerprint, view.provenance.value)
        self.assertIn(retained.post.image_fingerprint, view.provenance.value)
        self.assertEqual(view.authority.status, A.NOT_APPLICABLE)
        self.assertEqual(view.diagnostics.status, A.UNSUPPORTED)
        value = next(e for e in view.state.entries if e.key == "state:value")
        self.assertEqual(value.observed_value.value, ("I64", "42"))

    def test_supplied_genuine_frame_does_not_invent_a_stack(self):
        frame = CallFrame("function:example", "example", (LocalBinding("opaque", []),), 0)
        with no_semantic_calls():
            projection = inspect_frame(self.execution, frame)
        self.assertEqual(projection.value[2:5], (frame.function_id, frame.function_name, frame.depth))
        self.assertEqual(projection.value[-1][0], "unsupported")
        self.assertEqual(self.view().stack.status, A.UNAVAILABLE)
        self.assertNotIn("opaque", repr(projection))

    def test_static_read_only_surface_and_no_execution_calls(self):
        tree = ast.parse((ROOT / "apexforge/tooling/debug_inspection.py").read_text(encoding="utf-8"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertFalse(imports & {"runtime.engine", "authority.engine", "workflow.air_runner",
                                   "apexforge.native_backend.native_execution"})
        functions = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertFalse(functions & {"set_state", "mutate_state", "change_principal", "grant_authority",
                                     "activate_directive", "change_route", "overwrite_result"})
        calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute))}
        self.assertFalse(calls & {"execute", "allows", "check", "select_path", "apply", "eval", "exec",
            "dispatch_native", "emit_native_source_mapping", "build_registry_execution_plan",
            "bind_registry_execution_plan", "from_program_initials", "_evaluate_assignment"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
