from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from air.model import AIRProgram, VerifiedAIRProgram
from apexforge.native_backend import (
    CANONICAL_EXECUTION_PLAN_OWNER,
    RegistryExecutionPlanBinding,
    bind_registry_execution_plan,
    build_verified_air_lowering_input,
)
from workflow.air_runner import RegistryExecutionPlan


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def make_program(version: str = "p12.2d") -> AIRProgram:
    return AIRProgram(
        version=version,
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
    )


def main() -> int:
    program = make_program()
    verified = VerifiedAIRProgram(program)
    lowering_input = build_verified_air_lowering_input(verified)
    plan = RegistryExecutionPlan(
        program=program,
        entry_directive="directive:Main",
        directive_owners={
            "directive:main": program,
            "directive:child": program,
        },
    )
    binding = bind_registry_execution_plan(lowering_input, plan)
    require(isinstance(binding, RegistryExecutionPlanBinding), "execution-plan binding type changed")
    require(binding.lowering_input is lowering_input, "binding did not preserve exact lowering input")
    require(binding.execution_plan is plan, "binding did not preserve exact RegistryExecutionPlan")
    require(binding.entry_directive == "directive:Main", "entry directive changed during binding")
    require(binding.directive_owner_ids == ("directive:child", "directive:main"), "directive-owner ordering is not canonical")
    require(binding.source_owner == "workflow.air_runner.RegistryExecutionPlan", "execution-plan owner changed")
    require(CANONICAL_EXECUTION_PLAN_OWNER == "workflow.air_runner.RegistryExecutionPlan", "execution-plan ownership marker changed")
    require(len(binding.routing_fingerprint) == 64, "routing fingerprint length changed")
    equivalent_plan = RegistryExecutionPlan(
        program=make_program(),
        entry_directive="directive:Main",
        directive_owners={
            "directive:child": program,
            "directive:main": program,
        },
    )
    equivalent_binding = bind_registry_execution_plan(
        build_verified_air_lowering_input(VerifiedAIRProgram(equivalent_plan.program)),
        equivalent_plan,
    )
    require(equivalent_binding.routing_fingerprint == binding.routing_fingerprint, "routing fingerprint depends on mapping insertion order or object identity")
    mismatch_rejected = False
    try:
        mismatched_plan = RegistryExecutionPlan(
            program=make_program("p12.2d-other"),
            entry_directive="directive:Main",
            directive_owners={"directive:main": program},
        )
        bind_registry_execution_plan(lowering_input, mismatched_plan)
    except ValueError:
        mismatch_rejected = True
    require(mismatch_rejected, "execution plan for different AIR program was accepted")
    raw_input_rejected = False
    try:
        bind_registry_execution_plan(verified, plan)  # type: ignore[arg-type]
    except TypeError:
        raw_input_rejected = True
    require(raw_input_rejected, "RegistryExecutionPlan bypassed VerifiedAIRLoweringInput boundary")
    require(plan.owner_of("directive:Main") is program, "canonical RegistryExecutionPlan owner resolution changed")
    require(binding.execution_plan.owner_of("directive:Main") is program, "binding did not delegate owner resolution to canonical plan")
    binding_text = (ROOT / "apexforge/native_backend/execution_plan_binding.py").read_text(encoding="utf-8")
    require("from workflow.air_runner import RegistryExecutionPlan" in binding_text, "canonical execution-plan import changed")
    require("class RegistryExecutionPlan:" not in binding_text, "parallel RegistryExecutionPlan model introduced")
    require("def owner_of(" not in binding_text, "backend reimplemented RegistryExecutionPlan.owner_of")
    require("RuntimeEngine" not in binding_text, "runtime execution entered plan-binding seam")
    require("LLVM" not in binding_text and "clang" not in binding_text and "gcc" not in binding_text, "native codegen entered plan-binding seam")
    require("ApexForge.VisualStudio" not in binding_text, "Visual Studio dependency leaked into plan-binding seam")
    print(f"P12_2D_ROUTING_FINGERPRINT={binding.routing_fingerprint}")
    print("P12_2D_CANONICAL_EXECUTION_PLAN_OWNER=workflow.air_runner.RegistryExecutionPlan")
    print("P12_2D_VERIFIED_LOWERING_INPUT_BOUND=True")
    print("P12_2D_PLAN_PROGRAM_MISMATCH_REJECTED=PASS")
    print("P12_2D_RAW_VERIFIED_AIR_BYPASS_REJECTED=PASS")
    print("P12_2D_DIRECTIVE_OWNER_ORDER_DETERMINISTIC=PASS")
    print("P12_2D_DIRECTIVE_OWNER_RESOLUTION_DELEGATED=PASS")
    print("P12_2D_PARALLEL_EXECUTION_PLAN_MODEL_CREATED=False")
    print("P12_2D_EXECUTION_PLAN_SEMANTICS_REDEFINED=False")
    print("P12_2D_NATIVE_CODEGEN=NOT_ENTERED")
    print("P12_2D_REGISTRY_EXECUTION_PLAN_BINDING=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
