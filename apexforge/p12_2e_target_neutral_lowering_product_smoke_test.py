from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from air.model import AIRProgram, VerifiedAIRProgram
from apexforge.native_backend import (
    TARGET_NEUTRAL_LOWERING_SCHEMA,
    TargetNeutralLoweringProduct,
    bind_registry_execution_plan,
    build_verified_air_lowering_input,
    lower_target_neutral,
)
from workflow.air_runner import RegistryExecutionPlan


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def make_program(version: str = "p12.2e") -> AIRProgram:
    return AIRProgram(
        version=version,
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
    )


def make_product(owner_order: tuple[str, ...] = ("directive:main", "directive:child")) -> TargetNeutralLoweringProduct:
    program = make_program()
    lowering_input = build_verified_air_lowering_input(VerifiedAIRProgram(program))
    owners = {key: program for key in owner_order}
    plan = RegistryExecutionPlan(
        program=program,
        entry_directive="directive:Main",
        directive_owners=owners,
    )
    binding = bind_registry_execution_plan(lowering_input, plan)
    return lower_target_neutral(binding)


def main() -> int:
    product = make_product()
    require(isinstance(product, TargetNeutralLoweringProduct), "target-neutral lowering product type changed")
    require(product.schema == "apexforge.target-neutral-lowering/v1", "target-neutral schema changed")
    require(TARGET_NEUTRAL_LOWERING_SCHEMA == product.schema, "target-neutral schema constant changed")
    require(len(product.verified_air_fingerprint) == 64, "verified AIR fingerprint missing")
    require(len(product.routing_fingerprint) == 64, "routing fingerprint missing")
    require(len(product.product_fingerprint) == 64, "product fingerprint length changed")
    require(product.entry_directive == "directive:Main", "entry directive changed in target-neutral product")
    require(product.directive_owner_ids == ("directive:child", "directive:main"), "directive-owner identity ordering changed")
    record = json.loads(product.canonical_json)
    require(record["schema"] == TARGET_NEUTRAL_LOWERING_SCHEMA, "canonical product schema missing")
    require(record["verified_air_fingerprint"] == product.verified_air_fingerprint, "AIR fingerprint not bound into product")
    require(record["routing_fingerprint"] == product.routing_fingerprint, "routing fingerprint not bound into product")
    require(record["entry_directive"] == product.entry_directive, "entry directive not bound into product")
    require(record["directive_owner_ids"] == list(product.directive_owner_ids), "directive owners not bound into product")
    require(record["canonical_air_transport"] == product.binding.lowering_input.transport_json, "canonical AIR transport was transformed or replaced")
    equivalent = make_product(("directive:child", "directive:main"))
    require(equivalent.product_fingerprint == product.product_fingerprint, "target-neutral product depends on mapping insertion order")
    changed_program = make_program("p12.2e-changed")
    changed_input = build_verified_air_lowering_input(VerifiedAIRProgram(changed_program))
    changed_plan = RegistryExecutionPlan(program=changed_program, entry_directive="directive:Main", directive_owners={"directive:main": changed_program, "directive:child": changed_program})
    changed_product = lower_target_neutral(bind_registry_execution_plan(changed_input, changed_plan))
    require(changed_product.product_fingerprint != product.product_fingerprint, "product fingerprint ignored verified AIR identity")
    raw_rejected = False
    try:
        lower_target_neutral(product.binding.lowering_input)  # type: ignore[arg-type]
    except TypeError:
        raw_rejected = True
    require(raw_rejected, "target-neutral lowering bypassed RegistryExecutionPlanBinding")
    text = (ROOT / "apexforge/native_backend/target_neutral_lowering.py").read_text(encoding="utf-8")
    require("RegistryExecutionPlanBinding" in text, "canonical plan binding input missing")
    require("VerifiedAIRProgram" not in text, "target-neutral product bypasses lowering-input boundary")
    require("class AIRProgram" not in text, "parallel AIR model introduced")
    require("RegistryExecutionPlan(" not in text, "execution-plan semantics duplicated")
    forbidden = ("LLVM", "clang", "gcc", "msvc", "target triple", "calling convention", "object format", "linker", "machine code")
    require(not any(item.lower() in text.lower() for item in forbidden), "target-specific or ABI concern entered target-neutral lowering")
    require("ApexForge.VisualStudio" not in text, "Visual Studio dependency leaked into target-neutral lowering")
    print(f"P12_2E_PRODUCT_FINGERPRINT={product.product_fingerprint}")
    print(f"P12_2E_VERIFIED_AIR_FINGERPRINT={product.verified_air_fingerprint}")
    print(f"P12_2E_ROUTING_FINGERPRINT={product.routing_fingerprint}")
    print("P12_2E_SCHEMA=apexforge.target-neutral-lowering/v1")
    print("P12_2E_CANONICAL_AIR_TRANSPORT_PRESERVED=PASS")
    print("P12_2E_ROUTING_IDENTITY_BOUND=PASS")
    print("P12_2E_MAPPING_ORDER_INDEPENDENT=PASS")
    print("P12_2E_SOURCE_CHANGE_CHANGES_PRODUCT_IDENTITY=PASS")
    print("P12_2E_RAW_LOWERING_INPUT_BYPASS_REJECTED=PASS")
    print("P12_2E_PARALLEL_AIR_MODEL_CREATED=False")
    print("P12_2E_EXECUTION_PLAN_SEMANTICS_REDEFINED=False")
    print("P12_2E_ABI_SELECTED=False")
    print("P12_2E_MACHINE_CODE_EMITTED=False")
    print("P12_2E_TOOLCHAIN_REQUIRED=False")
    print("P12_2E_TARGET_NEUTRAL_LOWERING_PRODUCT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
