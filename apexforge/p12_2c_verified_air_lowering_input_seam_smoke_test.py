from __future__ import annotations

from hashlib import sha256
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from air.model import AIRProgram, VerifiedAIRProgram
from air.serialization import air_to_dict
from apexforge.native_backend import (
    CANONICAL_SERIALIZATION_DELEGATE,
    CANONICAL_VERIFIED_AIR_OWNER,
    VerifiedAIRLoweringInput,
    build_verified_air_lowering_input,
)


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def make_program() -> AIRProgram:
    return AIRProgram(
        version="p12.2c",
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
    lowered = build_verified_air_lowering_input(verified)
    require(isinstance(lowered, VerifiedAIRLoweringInput), "lowering-input type changed")
    require(lowered.verified is verified, "lowering seam did not preserve exact VerifiedAIRProgram")
    require(lowered.program is program, "lowering seam did not expose verified AIRProgram")
    require(lowered.source_owner == "air.model.VerifiedAIRProgram", "canonical Verified AIR owner changed")
    require(CANONICAL_VERIFIED_AIR_OWNER == "air.model.VerifiedAIRProgram", "Verified AIR ownership marker changed")
    require(CANONICAL_SERIALIZATION_DELEGATE == "air.serialization.air_to_dict", "serialization delegation changed")
    direct_data = air_to_dict(program)
    expected_json = json.dumps(direct_data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    expected_fingerprint = sha256(expected_json.encode("utf-8")).hexdigest().upper()
    require(lowered.transport_json == expected_json, "lowering seam diverged from air_to_dict transport")
    require(lowered.transport_fingerprint == expected_fingerprint, "transport fingerprint changed")
    second = build_verified_air_lowering_input(VerifiedAIRProgram(make_program()))
    require(second.transport_fingerprint == expected_fingerprint, "transport fingerprint is nondeterministic")
    raw_rejected = False
    try:
        build_verified_air_lowering_input(program)  # type: ignore[arg-type]
    except TypeError:
        raw_rejected = True
    require(raw_rejected, "raw AIRProgram bypassed VerifiedAIRProgram boundary")
    lowering_text = (ROOT / "apexforge/native_backend/lowering_input.py").read_text(encoding="utf-8")
    require("from air.model import AIRProgram, VerifiedAIRProgram" in lowering_text, "canonical AIR import changed")
    require("from air.serialization import air_to_dict" in lowering_text, "canonical serializer delegation missing")
    require("class AIRProgram" not in lowering_text, "parallel AIRProgram model introduced")
    require("class VerifiedAIRProgram" not in lowering_text, "parallel VerifiedAIRProgram model introduced")
    require("RegistryExecutionPlan" not in lowering_text, "execution-plan binding entered P12.2C prematurely")
    require("ApexForge.VisualStudio" not in lowering_text, "Visual Studio dependency leaked into lowering seam")
    print(f"P12_2C_TRANSPORT_FINGERPRINT={expected_fingerprint}")
    print("P12_2C_CANONICAL_AIR_OWNER=air.model.VerifiedAIRProgram")
    print("P12_2C_SERIALIZATION_DELEGATE=air.serialization.air_to_dict")
    print("P12_2C_VERIFIED_AIR_ACCEPTED=PASS")
    print("P12_2C_RAW_AIRPROGRAM_REJECTED=PASS")
    print("P12_2C_TRANSPORT_FINGERPRINT_DETERMINISTIC=PASS")
    print("P12_2C_PARALLEL_AIR_MODEL_CREATED=False")
    print("P12_2C_VERIFICATION_REDEFINED=False")
    print("P12_2C_REGISTRY_EXECUTION_PLAN=DEFERRED_TO_P12_2D")
    print("P12_2C_VERIFIED_AIR_LOWERING_INPUT_SEAM=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
