"""Live RCV-52 census; deliberately outside the frozen RCV gate inventory."""
from __future__ import annotations

from dataclasses import fields, replace
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from air.model import AIRProgram
from air.types import AIR_VERSION
from air.verify import AIRVerifier
from apexforge.native_backend import (
    bind_registry_execution_plan,
    build_verified_air_lowering_input,
    lower_target_neutral,
)
from workflow.air_runner import RegistryExecutionPlan


def main() -> int:
    # A minimal verifier fixture, not a claimed executable ApexForge program.
    program = AIRProgram(AIR_VERSION, (), (), (), (), (), ())
    verified = AIRVerifier().verify(program).require_verified()
    assert verified.program is program
    assert [field.name for field in fields(verified)] == ["program"]
    assert [field.name for field in fields(RegistryExecutionPlan)] == [
        "program", "entry_directive", "directive_owners"
    ]
    invalid = replace(program, version="invalid-census-version")
    try:
        AIRVerifier().verify(invalid).require_verified()
    except ValueError as exc:
        assert "AIR001" in str(exc)
    else:
        raise AssertionError("canonical verifier accepted invalid AIR version")

    lowering = build_verified_air_lowering_input(verified)
    plan = RegistryExecutionPlan(program, "directive:missing", {})
    binding = bind_registry_execution_plan(lowering, plan)
    first = lower_target_neutral(binding)
    second = lower_target_neutral(binding)
    assert first.canonical_json == second.canonical_json
    assert first.product_fingerprint == second.product_fingerprint
    record = json.loads(first.canonical_json)
    assert record["canonical_air_transport"] == lowering.transport_json
    assert record["entry_directive"] == "directive:missing"
    # Characterize the existing boundary honestly: binding is not execution admission.
    try:
        bind_registry_execution_plan(lowering, replace(plan, program=invalid))
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched plan was accepted")
    exports = (ROOT / "runtimes/native/link/apexforge_native.def").read_text()
    assert exports.split() == [
        "LIBRARY", "apexforge_native", "EXPORTS",
        "apexforge_release_handle", "apexforge_release_buffer"
    ]
    print("RCV_52_CANONICAL_VERIFIER_INVALID_AIR_REJECTION=PASS")
    print("RCV_52_PLAN_PROGRAM_MISMATCH_REJECTION=PASS")
    print("RCV_52_STRUCTURAL_LOWERING_REPEAT_DETERMINISM=PASS")
    print("RCV_52_BINDING_VALIDATES_EXECUTABLE_ENTRY=False")
    print("RCV_52_NATIVE_EXPORTS=LIFECYCLE_ONLY")
    print("RCV_52_NATIVE_PROGRAM_EXECUTION_PROVEN=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
