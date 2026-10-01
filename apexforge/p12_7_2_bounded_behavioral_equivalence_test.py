"""Bounded three-path comparison; canonical/managed share RuntimeEngine.

No independent .NET executor is exercised. Projections extract owner results;
native membership and all execution remain delegated to frozen production APIs.
"""
from __future__ import annotations

import ast
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from air.expressions import AIRIntegerLiteral
from air.model import StateAssignment, StateDefinition, VerifiedAIRProgram
from air.verify import AIRVerifier
from causality.model import CausalDecision, CausalPath
from runtime.engine import ExecutionResult, RuntimeEngine
from runtime.state import StateSnapshot
from type_system.model import BOOL
from workflow.air_runner import build_default_context, run_air_program
from tooling.trace_integration import (
    associate_plan, execute_managed_retained, execute_native_retained,
)
from apexforge.native_backend import native_execution as native
from apexforge.native_backend.lowering_input import build_verified_air_lowering_input
from apexforge.native_backend.native_execution_contract import (
    PROFILE, MIN_I64, MAX_I64, NativeExecutionError, admit_native_profile,
)
from apexforge.native_backend.payload import CanonicalExecutionPayload
from apexforge.native_backend.result import CanonicalExecutionResult
from apexforge.native_backend.value import CanonicalExecutionValue
from p12_5_native_profile_contract_test import fixture, plan_for, with_path


class OutsideCommonDomain(ValueError):
    """A native profile limit is not a claimed equivalent execution."""
    classification = "NATIVE_PROFILE_LIMIT"

    def __init__(self, code):
        self.code = code
        super().__init__("OUTSIDE_COMMON_DOMAIN: " + code)


def require_common_domain(verified, plan):
    try:
        return admit_native_profile(verified, plan)
    except NativeExecutionError as exc:
        # Invalid AIR/routing/infrastructure must remain failures, not exclusions.
        if exc.code != "NATIVE_PROFILE_UNSUPPORTED":
            raise
        raise OutsideCommonDomain(exc.code) from exc


def snapshot_projection(snapshot):
    """Extract existing typed cells; never read or evaluate AIR."""
    if type(snapshot) is not StateSnapshot:
        raise TypeError("canonical StateSnapshot required")
    values = []
    for cell in snapshot.cells:
        if type(cell.value) is not int:
            raise ValueError("comparison domain requires exact integer cells")
        values.append(CanonicalExecutionValue(cell.key, "I64", str(cell.value)))
    payload = CanonicalExecutionPayload(tuple(values))
    payload.validate()
    return tuple((v.name, v.representation, v.data)
                 for v in sorted(payload.values, key=lambda v: v.name))


def managed_projection(result):
    if type(result) is not ExecutionResult:
        raise TypeError("canonical ExecutionResult required")
    if result.delta.events or result.delta.effects:
        raise ValueError("events/effects outside comparison domain")
    return result.ok, snapshot_projection(result.final_state)


def native_projection(result):
    if type(result) is not CanonicalExecutionResult:
        raise TypeError("canonical native result required")
    result.validate()
    if any(v.representation != "I64" for v in result.outputs.values):
        raise ValueError("native comparison domain requires I64")
    return result.status == "SUCCESS", tuple(
        (v.name, v.representation, v.data)
        for v in sorted(result.outputs.values, key=lambda v: v.name))


def require_equal_projections(canonical, managed, native_result):
    if canonical != managed or canonical != native_result:
        raise AssertionError("SEMANTIC_FAILURE: owner result projections differ")


def supported_cases():
    base = fixture()
    cases = []
    for name, initial, value in (
        ("zero", -7, 0),
        ("positive", 0, 42),
        ("negative", 7, -42),
        ("i64_minimum", MAX_I64, MIN_I64),
        ("i64_maximum", MIN_I64, MAX_I64),
    ):
        program = replace(base, states=(StateDefinition("state:value", initial),))
        program = with_path(program, assignments=(
            StateAssignment("state:value", "set_int", AIRIntegerLiteral(value)),))
        cases.append((name, program))
    # Same behavior with different declaration order; canonical cells/payloads
    # order by name, native wire values retain declaration order.
    multiple = replace(base, states=(StateDefinition("state:z", -7),
                                    StateDefinition("state:a", MAX_I64),
                                    StateDefinition("state:untouched", MIN_I64)))
    multiple = with_path(multiple, assignments=(
        StateAssignment("state:z", "set_int", 11),
        StateAssignment("state:a", "set_int", -11)))
    cases.extend((("multiple_reversed_names", multiple),
                  ("multiple_reversed_declarations",
                   replace(multiple, states=tuple(reversed(multiple.states)))),
                  ("repeated_overwrite_untouched", base)))
    first = base.causal_decisions[0]
    second = CausalDecision("cause:second", paths=(CausalPath("path:second", -10,
        assignments=(StateAssignment("state:value", "set_int", 99),)),))
    empty = CausalDecision("cause:empty", paths=(CausalPath("path:empty", 0),))
    decisions = replace(base, causal_decisions=(first, second, empty), directives=(
        replace(base.directives[0], causal_decisions=(second.id, empty.id, first.id)),))
    cases.append(("decision_reference_order_and_empty_path", decisions))
    return tuple(cases)


def compare_case(program, build_root):
    """Execute the three existing APIs twice; no expected-state evaluator."""
    verified = AIRVerifier().verify(program).require_verified()
    plan = plan_for(program)
    admission = require_common_domain(verified, plan)  # Before any execution.
    binding = associate_plan(verified, plan)
    before = build_verified_air_lowering_input(verified)
    assert type(verified) is VerifiedAIRProgram
    assert admission.profile == PROFILE
    assert before.transport_fingerprint == admission.air_fingerprint
    assert binding.association.air_fingerprint == admission.air_fingerprint
    assert binding.association.routing_fingerprint == admission.routing_fingerprint
    assert binding.association.entry_directive == admission.entry == plan.entry_directive
    assert binding.compiler is None  # Authentic legacy AIR, no invented source.
    initial = snapshot_projection(build_default_context(program).state)
    native_initial = tuple(sorted((name, "I64", str(value)) for name, value in
                                  zip(admission.state_ids, admission.initial_values)))
    assert initial == native_initial
    rounds = []
    for _ in range(2):
        context = build_default_context(program)
        assert snapshot_projection(context.state) == initial
        canonical = run_air_program(program, entry_directives=(plan.entry_directive,))
        retained = execute_managed_retained(binding, context=context)
        retained.validate(binding, context, RuntimeEngine(), canonical)
        # A failure trap, not a replacement executor or runtime instrumentation.
        # Native positive output is produced by the unmocked build/dispatch API.
        with patch.object(RuntimeEngine, "execute", side_effect=AssertionError("native fallback")):
            native_retained = execute_native_retained(binding, build_root)
            native_retained.validate_snapshot(binding, native_retained.evidence)
        evidence = native_retained.evidence
        receipt = json.loads(evidence.receipt_json)
        assert receipt["profile"] == PROFILE
        assert receipt["air"] == receipt["owner_air"] == admission.air_fingerprint
        assert receipt["routing"] == admission.routing_fingerprint
        assert receipt["entry"] == plan.entry_directive
        assert tuple(receipt["states"]) == admission.state_ids
        assert receipt["toolchain"] and receipt["image"] == native_retained.pre.image_fingerprint
        assert receipt["source"] == native_retained.pre.scope.generated_c_fingerprint
        assert evidence.result.input_fingerprint == native.digest(evidence.receipt_json.encode())
        assert native_retained.post.output_fingerprint == evidence.output_fingerprint
        assert native_retained.mapping.source_mapping_fingerprint == "UNMAPPED_SOURCE"
        assert len(native_retained.mapping.regions) == len(admission.state_ids) + len(admission.stores)
        assert tuple(v.name for v in evidence.result.outputs.values) == admission.state_ids
        assert tuple(c.key for c in canonical.final_state.cells) == tuple(sorted(admission.state_ids))
        projections = (managed_projection(canonical), managed_projection(retained.result),
                       native_projection(evidence.result))
        require_equal_projections(*projections)
        assert projections[0][0] is True
        assert tuple(row[0] for row in projections[0][1]) == tuple(sorted(admission.state_ids))
        assert snapshot_projection(context.state) == initial
        rounds.append(projections)
    assert rounds[0] == rounds[1], "nondeterministic owner projection"
    assert before == build_verified_air_lowering_input(verified), "AIR/actions mutated"
    return rounds[0][0]


class EquivalenceTests(unittest.TestCase):
    def test_supported_three_paths_and_repeated_projection(self):
        root = ROOT / "build"
        root.mkdir(exist_ok=True)
        projections = {}
        with tempfile.TemporaryDirectory(prefix="p12-7-2-", dir=root) as directory:
            for name, program in supported_cases():
                with self.subTest(case=name):
                    projections[name] = compare_case(program, Path(directory))
                    print("P12_7_2_CASE=" + name + "|THREE_PATH_REPEAT=PASS")
        self.assertEqual(projections["multiple_reversed_names"],
                         projections["multiple_reversed_declarations"])
        self.assertEqual(len(projections), 9)

    def test_outside_domain_rejects_before_all_execution(self):
        base = fixture()
        path = base.causal_decisions[0].paths[0]
        cases = (
            ("bool_state", replace(base, states=base.states + (StateDefinition("state:bool", True, BOOL),))),
            ("add_int", with_path(base, assignments=(StateAssignment("state:value", "add_int", 1),))),
            ("alternative_paths", replace(base, causal_decisions=(replace(base.causal_decisions[0],
                paths=(path, replace(path, id="path:other"))),))),
            ("ordered_actions", with_path(base, actions=path.assignments)),
        )
        for name, program in cases:
            with self.subTest(case=name):
                verified = AIRVerifier().verify(program).require_verified()
                before = build_verified_air_lowering_input(verified)
                with patch.object(RuntimeEngine, "execute", side_effect=AssertionError("excluded case executed")), \
                     patch.object(native, "_toolchain", side_effect=AssertionError("excluded case compiled")), \
                     patch.object(native, "dispatch_native", side_effect=AssertionError("excluded case dispatched")):
                    with self.assertRaises(NativeExecutionError) as rejection:
                        admit_native_profile(verified, plan_for(program))
                    self.assertEqual(rejection.exception.code, "NATIVE_PROFILE_UNSUPPORTED")
                    with self.assertRaises(OutsideCommonDomain) as classified:
                        compare_case(program, ROOT / "build")
                    self.assertEqual(classified.exception.classification, "NATIVE_PROFILE_LIMIT")
                    self.assertEqual(classified.exception.code, rejection.exception.code)
                self.assertEqual(before, build_verified_air_lowering_input(verified))
                # Native rejection never requires canonical or managed rejection.
                canonical = run_air_program(program, entry_directives=(plan_for(program).entry_directive,))
                retained = execute_managed_retained(associate_plan(verified, plan_for(program)))
                self.assertTrue(canonical.ok)
                self.assertEqual(canonical, retained.result)
                print("P12_7_2_BOUNDARY=" + name + "|OUTSIDE_COMMON_DOMAIN=NATIVE_PROFILE_LIMIT")

    def test_projection_mismatches_and_invalid_types_are_not_equivalence(self):
        canonical = managed_projection(run_air_program(fixture(), entry_directives=("directive:main",)))
        rows = canonical[1]
        for changed in ((False, rows), (True, rows[:-1]),
                        (True, (("state:other", rows[0][1], rows[0][2]),) + rows[1:]),
                        (True, ((rows[0][0], "BOOL", "true"),) + rows[1:]),
                        (True, ((rows[0][0], "I64", "123"),) + rows[1:])):
            with self.assertRaises(AssertionError):
                require_equal_projections(canonical, canonical, changed)
        with self.assertRaises(ValueError):
            snapshot_projection(StateSnapshot.from_mapping({"state:value": True}))
        with self.assertRaises(ValueError):
            native_projection(CanonicalExecutionResult("0" * 64, "SUCCESS",
                CanonicalExecutionPayload((CanonicalExecutionValue("state:value", "BOOL", "true"),))))

    def test_projection_has_no_execution_or_air_dependency(self):
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        projections = {"snapshot_projection", "managed_projection", "native_projection", "require_equal_projections"}
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in projections]
        calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
                 for fn in nodes for n in ast.walk(fn) if isinstance(n, ast.Call)
                 and isinstance(n.func, (ast.Attribute, ast.Name))}
        self.assertFalse(calls & {"execute", "run_air_program", "admit_native_profile", "select_path",
                                 "apply", "eval", "exec", "resolve_type", "infer_type", "_evaluate_assignment"})
        self.assertFalse(any(isinstance(n, ast.Name) and n.id in {"program", "verified", "plan"}
                             for fn in nodes for n in ast.walk(fn)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
