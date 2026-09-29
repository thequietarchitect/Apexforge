"""RCV-53 executable contract gate, independent of any native compiler."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from air.expressions import (AIRIntegerLiteral, AIRBooleanLiteral, AIRIdentifierReference, AIRBinaryExpression,
                             AIRUnaryExpression, AIRCallExpression)
from air.functions import AIRFunction
from air.model import (AIRDirective, AIRProgram, AIRAuthority, AIRWorkflow, AIRRole,
                       AIRWhenAction, DirectiveAuthority, DirectiveRequirement, PrincipalAuthority,
                       EventDefinition, EventEmission, StateAssignment, StateDefinition,
                       VerifiedAIRProgram)
from air.types import AIR_VERSION
from air.verify import AIRVerifier
from authority.model import Principal, AuthorityCheck
from causality.model import CausalDecision, CausalPath, DirectiveInvocation
from effects.model import EffectIntent
from type_system.model import BOOL, FLOAT, STRING
from workflow.air_runner import RegistryExecutionPlan, build_registry_execution_plan
from apexforge.native_backend.native_execution_contract import (
    PROFILE, MIN_I64, MAX_I64, NativeExecutionError, admit_native_profile,
)


def fixture():
    return AIRProgram(
        version=AIR_VERSION,
        states=(StateDefinition("state:value", AIRIntegerLiteral(-7)),
                StateDefinition("state:unchanged", MAX_I64)),
        events=(), authority_checks=(),
        causal_decisions=(CausalDecision("cause:main", paths=(CausalPath(
            "path:only", 1, assignments=(
                StateAssignment("state:value", "set_int", AIRIntegerLiteral(41)),
                StateAssignment("state:value", "set_int", 42),
            )),)),),
        directives=(AIRDirective("directive:main", "main", "principal:main", (), ("cause:main",)),),
        requirements=(), principals=(Principal("principal:main", "main"),),
    )


def plan_for(program):
    return RegistryExecutionPlan(program, program.directives[0].id,
                                 {program.directives[0].id.casefold(): program})


def with_path(program, **changes):
    decision = program.causal_decisions[0]
    return replace(program, causal_decisions=(replace(decision, paths=(replace(decision.paths[0], **changes),)),))


class ContractTests(unittest.TestCase):
    def verified_rejection(self, program):
        verified = AIRVerifier().verify(program).require_verified()
        with patch("subprocess.Popen", side_effect=AssertionError("contract must not launch processes")):
            with self.assertRaises(NativeExecutionError):
                admit_native_profile(verified, plan_for(program))

    def test_supported_registry_plan_and_order(self):
        program = fixture()
        class Registry:
            def resolve(self, name):
                assert name == "main"
                return program
        plan = build_registry_execution_plan(Registry(), "main")
        verified = AIRVerifier().verify(plan.program).require_verified()
        with patch("subprocess.Popen", side_effect=AssertionError("compiler called during admission")):
            admitted = admit_native_profile(verified, plan)
        self.assertEqual(admitted.profile, PROFILE)
        self.assertEqual(admitted.initial_values, (-7, MAX_I64))
        self.assertEqual(admitted.stores, ((0, 41), (0, 42)))
        self.assertEqual(admitted, admit_native_profile(verified, plan))

    def test_boundaries_and_decision_order(self):
        program = fixture()
        other = CausalDecision("cause:second", paths=(CausalPath("path:second", -10,
            assignments=(StateAssignment("state:unchanged", "set_int", MIN_I64),)),))
        program = replace(program, causal_decisions=program.causal_decisions + (other,),
            directives=(replace(program.directives[0], causal_decisions=(other.id, "cause:main")),))
        admission = admit_native_profile(AIRVerifier().verify(program).require_verified(), plan_for(program))
        self.assertEqual(admission.stores, ((1, MIN_I64), (0, 41), (0, 42)))

    def test_verified_unsupported_surface(self):
        p = fixture()
        path = p.causal_decisions[0].paths[0]
        cases = {
            "events": replace(p, events=(EventDefinition("event:x", "x"),)),
            "functions": replace(p, functions=(AIRFunction("function:f", "f", (), AIRIntegerLiteral(1)),)),
            "workflows": replace(p, workflows=(AIRWorkflow("workflow:w", "w", ()),)),
            "authority_checks": replace(p, authority_checks=(AuthorityCheck("check:x", "principal:main", "x", "*"),)),
            "authorities": replace(p, authorities=(AIRAuthority("authority:x", "x", ()),)),
            "roles": replace(p, roles=(AIRRole("r", ()),)),
            "requirements": replace(p, requirements=(DirectiveRequirement("x"),)),
            "effects": with_path(p, effects=(EffectIntent("effect:x", "x"),)),
            "actions": with_path(p, actions=path.assignments),
            "conditionals": with_path(p, actions=(AIRWhenAction(AIRBooleanLiteral(True), path.assignments),)),
            "invocations": with_path(p, invocations=(DirectiveInvocation("directive:main"),)),
            "alternative_paths": replace(p, causal_decisions=(replace(p.causal_decisions[0],
                paths=(path, replace(path, id="path:other"))),)),
            "add_int": with_path(p, assignments=(StateAssignment("state:value", "add_int", 1),)),
            "i64_positive_overflow": with_path(p, assignments=(StateAssignment("state:value", "set_int", MAX_I64 + 1),)),
            "i64_negative_overflow": with_path(p, assignments=(StateAssignment("state:value", "set_int", MIN_I64 - 1),)),
            "empty_assignments": with_path(p, assignments=()),
            "extra_principal": replace(p, principals=p.principals + (Principal("principal:other"),)),
            "directive_order": replace(p, directives=(replace(p.directives[0], order=1),)),
            "repeated_decision": replace(p, directives=(replace(p.directives[0], causal_decisions=("cause:main", "cause:main")),)),
            "unused_decision": replace(p, directives=(replace(p.directives[0], causal_decisions=()),)),
            "multiple_directives": replace(p, directives=p.directives + (replace(p.directives[0], id="directive:other", name="other"),)),
        }
        for name, value_type, initial in (("bool", BOOL, True), ("float", FLOAT, 1.5), ("string", STRING, "x")):
            cases[name] = replace(p, states=p.states + (StateDefinition("state:extra", initial, value_type),))
        for name, expression in (
            ("identifier", AIRIdentifierReference("state:value")),
            ("unary", AIRUnaryExpression("-", AIRIntegerLiteral(1))),
            ("binary", AIRBinaryExpression(AIRIntegerLiteral(1), "+", AIRIntegerLiteral(2))),
            ("call", AIRCallExpression("function:f")),
        ):
            cases[name] = with_path(p, assignments=(StateAssignment("state:value", "set_int", expression),))
        cases["emissions"] = with_path(cases["events"], emits=(EventEmission("event:x"),))
        cases["principal_roles"] = replace(cases["roles"], principals=(replace(p.principals[0], roles=("r",)),))
        cases["principal_authorities"] = replace(cases["authorities"],
            principals=(replace(p.principals[0], authorities=(PrincipalAuthority("x"),)),))
        cases["directive_authorities"] = replace(cases["authorities"],
            directives=(replace(p.directives[0], authorities=(DirectiveAuthority("x"),)),))
        cases["directive_checks"] = replace(cases["authority_checks"],
            directives=(replace(p.directives[0], authority_checks=("check:x",)),))
        cases["oversized_id"] = replace(p, states=p.states + (StateDefinition("x" * 257, 0),))
        cases["expression_initializer"] = replace(p, states=(replace(p.states[0],
            initial=AIRIdentifierReference("state:unchanged")), p.states[1]))
        cases["state_limit"] = replace(p, states=tuple(StateDefinition(f"state:{i}", 0) for i in range(257)),
            causal_decisions=(replace(p.causal_decisions[0], paths=(replace(path,
                assignments=(StateAssignment("state:0", "set_int", 1),)),)),))
        cases["store_limit"] = with_path(p, assignments=(path.assignments[0],) * 4097)
        for name, program in cases.items():
            with self.subTest(surface=name):
                self.verified_rejection(program)

    def test_routing_and_invalid_air(self):
        p = fixture()
        verified = AIRVerifier().verify(p).require_verified()
        for plan in (replace(plan_for(p), entry_directive="main"),
                     replace(plan_for(p), directive_owners={}),
                     replace(plan_for(p), directive_owners={"directive:main": replace(p, states=())}),
                     replace(plan_for(p), program=replace(p, states=()))):
            with self.subTest(plan=plan.entry_directive), self.assertRaises(NativeExecutionError):
                admit_native_profile(verified, plan)
        bad = replace(p, version="invalid")
        with self.assertRaises(NativeExecutionError) as result:
            admit_native_profile(VerifiedAIRProgram(bad), plan_for(bad))
        self.assertEqual(result.exception.code, "NATIVE_AIR_INVALID")
        with self.assertRaises(NativeExecutionError):
            admit_native_profile(p, plan_for(p))

    def test_unknown_node_subclass_and_malformed_container(self):
        class UnknownInteger(AIRIntegerLiteral):
            pass
        p = fixture()
        for modified in (with_path(p, assignments=(StateAssignment("state:value", "set_int", UnknownInteger(1)),)),
                         replace(p, states=list(p.states))):
            with self.assertRaises(NativeExecutionError):
                admit_native_profile(VerifiedAIRProgram(modified), plan_for(modified))

    def test_owner_python_equality_is_not_provenance(self):
        program = fixture()
        program = replace(program, states=(replace(program.states[0], initial=1), program.states[1]))
        owner = replace(program, states=(replace(program.states[0], initial=True), program.states[1]))
        self.assertEqual(owner, program)  # The Python equality trap is real.
        verified = AIRVerifier().verify(program).require_verified()
        plan = replace(plan_for(program), directive_owners={"directive:main": owner})
        with self.assertRaises(NativeExecutionError) as failure:
            admit_native_profile(verified, plan)
        self.assertEqual(failure.exception.code, "NATIVE_ROUTING_INVALID")
        with self.assertRaises(NativeExecutionError) as failure:
            admit_native_profile(verified, replace(plan_for(program), program=owner))
        self.assertEqual(failure.exception.code, "NATIVE_ROUTING_INVALID")

    def test_admission_has_no_semantic_evaluator_or_process_dependency(self):
        import ast
        source = (ROOT / "apexforge/native_backend/native_execution_contract.py").read_text()
        tree = ast.parse(source)
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertFalse(any(name.startswith(("runtime", "compiler", "causality.engine", "subprocess")) for name in imports))
        forbidden = {"eval", "exec", "compile", "execute", "select_path", "resolve_type", "infer_type"}
        calls = {node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
                 for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, (ast.Attribute, ast.Name))}
        self.assertFalse(calls & forbidden)


if __name__ == "__main__":
    unittest.main(verbosity=2)
