from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APEX = ROOT / "apexforge"
sys.path.insert(0, str(APEX))

CONTRACT = APEX / "p12_5_rcv_46_canonical_air_transport_to_managed_carrier_derivation_bridge_acceptance.json"
RCV32 = APEX / "p12_5_rcv_32_managed_executable_carrier_derivation_source_decision.json"
RCV44 = APEX / "p12_5_rcv_44_managed_executable_carrier_decoder_positive_conformance.json"
RCV45 = APEX / "p12_5_rcv_45_managed_executable_carrier_decoder_negative_conformance.json"
DECODER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"


def req(value, message):
    if not value:
        raise AssertionError(message)


def main() -> int:
    source_decision = json.loads(RCV32.read_text(encoding="utf-8-sig"))
    positive = json.loads(RCV44.read_text(encoding="utf-8-sig"))
    negative = json.loads(RCV45.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(source_decision["decision"]["derivation_source"] == "CANONICAL_AIR_TRANSPORT", "RCV-32 source decision changed")
    req(positive["result"] == "PASS" and negative["result"] == "PASS", "decoder conformance predecessor changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-45", "predecessor changed")

    bridge = data["bridge"]
    req(bridge["component"] == "ApexForge.Runtime.ManagedExecutableCarrierDecoder", "bridge component changed")
    req(bridge["direction"] == "CANONICAL_AIR_TRANSPORT_TO_MANAGED_EXECUTABLE_CARRIER", "bridge direction changed")
    req(bridge["logical_source_owner"] == "air.model.VerifiedAIRProgram", "logical source owner changed")
    req(bridge["source_container"].endswith("VerifiedAIRLoweringInput.transport_json"), "source container changed")
    req(bridge["additional_bridge_component_required"] is False, "second bridge component selected")

    from air.model import AIRProgram, VerifiedAIRProgram
    from native_backend.lowering_input import build_verified_air_lowering_input

    program = AIRProgram(
        version="rcv46",
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
    )
    rejected = False
    try:
        build_verified_air_lowering_input(program)  # type: ignore[arg-type]
    except TypeError:
        rejected = True
    req(rejected, "raw AIRProgram bypassed VerifiedAIRProgram")
    lowering = build_verified_air_lowering_input(VerifiedAIRProgram(program))
    req(lowering.verified.program is program, "verified program identity was not retained upstream")
    req(lowering.transport_json.startswith("{"), "canonical transport was not produced")

    source = DECODER.read_text(encoding="utf-8-sig")
    public_methods = re.findall(r"public\s+IReadOnlyList<ManagedExecutableFunction>\s+(\w+)\s*\(", source)
    req(public_methods == ["DecodeCanonicalAirTransport"], f"decoder public bridge surface changed: {public_methods}")
    for token in ("ManagedRuntimeHost", "TargetNeutralLoweringHandoff", "Execute(", "Dispatch("):
        req(token not in source, f"unauthorized bridge coupling appeared: {token}")

    acceptance = data["acceptance"]
    req(all(acceptance.values()), "bridge acceptance condition missing")
    provenance = data["provenance"]
    req(provenance["new_managed_carrier_serialization"] is False, "carrier serialization invented")
    req(provenance["new_managed_carrier_fingerprint"] is False, "competing fingerprint invented")
    req(data["authority"]["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    print("P12_5_RCV_46_DERIVATION_BRIDGE=ManagedExecutableCarrierDecoder.DecodeCanonicalAirTransport")
    print("P12_5_RCV_46_RAW_AIRPROGRAM_REJECTED_UPSTREAM=PASS")
    print("P12_5_RCV_46_VERIFIED_SOURCE_OWNER=air.model.VerifiedAIRProgram")
    print("P12_5_RCV_46_NO_SECOND_BRIDGE_COMPONENT=True")
    print("P12_5_RCV_46_DERIVATION_BRIDGE_ACCEPTANCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
