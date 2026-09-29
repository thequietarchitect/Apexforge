from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_32_managed_executable_carrier_derivation_source_decision.json"
RCV31 = ROOT / "apexforge/p12_5_rcv_31_managed_executable_carrier_derivation_boundary_census_smoke_test.py"
LOWERING_INPUT = ROOT / "apexforge/native_backend/lowering_input.py"
TARGET_NEUTRAL = ROOT / "apexforge/native_backend/target_neutral_lowering.py"
AIR_SERIALIZATION = ROOT / "apexforge/air/serialization.py"
AIR_MODEL = ROOT / "apexforge/air/model.py"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
CARRIER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs"

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-32 MANAGED EXECUTABLE CARRIER DERIVATION SOURCE DECISION ===")
    for p in (CONTRACT, RCV31, LOWERING_INPUT, TARGET_NEUTRAL, AIR_SERIALIZATION, AIR_MODEL, HANDOFF, CARRIER):
        req(p.exists(), f"missing required file: {p}")

    cp = run(sys.executable, str(RCV31))
    req(cp.returncode == 0, "RCV-31 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_32_RCV31_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-executable-carrier-derivation-source-decision/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-31", "predecessor changed")

    ev = data["evidence"]
    req(ev["historical_q_derivation_bridge_reference_count"] == 0, "historical bridge count changed")
    req(ev["historical_q_production_python_managed_carrier_reference_count"] == 0, "historical Python carrier count changed")
    req(ev["historical_q_existing_handoff_boundary_reference_count"] == 22, "historical handoff count changed")
    req(ev["historical_verified_air_transport_compatibility_census_passed"] is True, "historical compatibility evidence lost")
    req(ev["historical_final_derivation_source_decision_directly_recovered"] is False, "unsupported historical decision claim introduced")
    req(ev["original_commit_identity_equivalence"] is False, "original commit identity improperly claimed")

    lowering = LOWERING_INPUT.read_text(encoding="utf-8-sig")
    target = TARGET_NEUTRAL.read_text(encoding="utf-8-sig")
    serialization = AIR_SERIALIZATION.read_text(encoding="utf-8-sig")
    model = AIR_MODEL.read_text(encoding="utf-8-sig")
    handoff = HANDOFF.read_text(encoding="utf-8-sig")
    carrier = CARRIER.read_text(encoding="utf-8-sig")

    req("class VerifiedAIRLoweringInput" in lowering, "VerifiedAIRLoweringInput missing")
    req("verified: VerifiedAIRProgram" in lowering, "Verified AIR ownership binding missing")
    req("transport_json: str" in lowering, "canonical AIR transport container missing")
    req("air_to_dict" in lowering, "canonical serialization delegate not used by lowering input")
    req("def air_to_dict" in serialization, "air_to_dict delegate missing")
    req("class VerifiedAIRProgram" in model, "VerifiedAIRProgram missing")
    req('"canonical_air_transport": binding.lowering_input.transport_json' in target, "target-neutral product no longer preserves canonical AIR transport")

    # The managed handoff is intentionally insufficient to derive the executable graph.
    for token in ("ManagedExecutableExpression", "ManagedExecutableFunction", "CanonicalAirTransport", "CanonicalJson"):
        req(token not in handoff, f"managed handoff unexpectedly contains carrier derivation payload: {token}")

    # The carrier itself remains a pure representation definition.
    for token in ("JsonSerializer", "VerifiedAIRProgram", "TargetNeutralLoweringHandoff", "Execute(", "Dispatch("):
        req(token not in carrier, f"derivation/execution concern entered carrier definition: {token}")

    d = data["decision"]
    req(d["derivation_source"] == "CANONICAL_AIR_TRANSPORT", "derivation source changed")
    req(d["derivation_direction"] == "CANONICAL_AIR_TRANSPORT_TO_MANAGED_EXECUTABLE_CARRIER", "derivation direction changed")
    req(d["logical_source_owner"] == "air.model.VerifiedAIRProgram", "logical source owner changed")
    req(d["canonical_serialization_delegate"] == "air.serialization.air_to_dict", "serialization delegate changed")
    req(d["existing_source_container"] == "apexforge.native_backend.VerifiedAIRLoweringInput.transport_json", "source container changed")
    req(d["derivation_owner_project"] == "ApexForge.Runtime", "derivation owner project changed")
    req(d["concrete_derivation_component"] == "UNSELECTED", "concrete derivation component selected too early")
    req(d["decoder_implementation"] == "DEFERRED", "decoder implementation selected too early")
    req(d["target_neutral_lowering_product_is_source"] is False, "target-neutral product selected as source")
    req(d["target_neutral_managed_handoff_is_source"] is False, "managed handoff selected as source")
    req(d["verified_air_python_object_graph_is_direct_cross_runtime_source"] is False, "direct Python object crossing selected")
    req(d["carrier_serialization_selected"] is False, "carrier serialization selected")
    req(d["external_serialization"] == "UNSELECTED", "external serialization selected")
    req(d["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport selected")
    req(d["execution_dispatch"] == "DEFERRED", "execution dispatch selected")
    req(d["historical_identity_claim"] is False, "historical identity improperly claimed")

    r = data["rationale"]
    for key in (
        "canonical_air_transport_contains_full_structural_air",
        "canonical_air_transport_is_deterministic",
        "canonical_air_transport_is_bound_to_verified_air",
        "target_neutral_handoff_lacks_executable_graph",
        "target_neutral_product_wraps_canonical_air_transport_but_is_not_needed_as_semantic_source",
        "direct_python_object_crossing_would_require_unselected_transport",
        "selection_does_not_authorize_runtime_crossing",
        "selection_does_not_authorize_json_decoder",
    ):
        req(r[key] is True, f"rationale invariant weakened: {key}")

    a = data["authority"]
    req(a["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(a["verified_air_owner"] == "air.model.VerifiedAIRProgram", "Verified AIR owner changed")
    req(a["carrier_owner_project"] == "ApexForge.Runtime", "carrier owner changed")
    req(a["carrier_derivation_may_copy_structure"] is True, "structural derivation permission missing")
    req(a["carrier_derivation_may_reinterpret_semantics"] is False, "derivation gained reinterpretation authority")
    req(a["carrier_derivation_may_execute"] is False, "derivation gained execution authority")
    req(a["carrier_derivation_may_dispatch"] is False, "derivation gained dispatch authority")
    req(a["carrier_derivation_may_select_transport"] is False, "derivation gained transport authority")

    req(data["implementation"] == "DEFERRED", "implementation selected during decision gate")

    print("P12_5_RCV_32_PROFILE=apexforge.p12.managed-executable-carrier-derivation-source-decision/v1")
    print("P12_5_RCV_32_DERIVATION_SOURCE=CANONICAL_AIR_TRANSPORT")
    print("P12_5_RCV_32_DERIVATION_DIRECTION=CANONICAL_AIR_TRANSPORT_TO_MANAGED_EXECUTABLE_CARRIER")
    print("P12_5_RCV_32_LOGICAL_SOURCE_OWNER=air.model.VerifiedAIRProgram")
    print("P12_5_RCV_32_CANONICAL_SERIALIZATION_DELEGATE=air.serialization.air_to_dict")
    print("P12_5_RCV_32_DERIVATION_OWNER_PROJECT=ApexForge.Runtime")
    print("P12_5_RCV_32_CONCRETE_DERIVATION_COMPONENT=UNSELECTED")
    print("P12_5_RCV_32_DECODER_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_32_TARGET_NEUTRAL_HANDOFF_IS_SOURCE=False")
    print("P12_5_RCV_32_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_32_CROSS_RUNTIME_TRANSPORT=DEFERRED_NO_TRANSPORT_AUTHORIZED")
    print("P12_5_RCV_32_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_32_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_32_MANAGED_EXECUTABLE_CARRIER_DERIVATION_SOURCE_DECISION=PASS")
    print("P12_5_RCV_32_NEXT=P12.5-RCV-33_MANAGED_EXECUTABLE_CARRIER_DERIVATION_MAPPING_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
