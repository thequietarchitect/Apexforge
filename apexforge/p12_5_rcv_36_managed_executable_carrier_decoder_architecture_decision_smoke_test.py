from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_36_managed_executable_carrier_decoder_architecture_decision.json"
RCV35 = ROOT / "apexforge/p12_5_rcv_35_managed_executable_carrier_decoder_architecture_census_smoke_test.py"
CARRIER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs"
RUNTIME_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"
FUTURE_DECODER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-36 MANAGED EXECUTABLE CARRIER DECODER ARCHITECTURE DECISION ===")
    for p in (CONTRACT, RCV35, CARRIER, RUNTIME_DIR, HOST_DIR):
        req(p.exists(), f"missing required path: {p}")

    cp = run(sys.executable, str(RCV35))
    req(cp.returncode == 0, "RCV-35 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_36_RCV35_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-executable-carrier-decoder-architecture-decision/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-35", "predecessor changed")

    hist = data["historical_evidence"]
    req(hist["historical_managed_carrier_decoder_recovered"] is False, "unsupported historical decoder claim introduced")
    req(hist["existing_managed_json_deserializer"] == "CanonicalExecutionEnvelope.FromJson", "existing managed JSON evidence changed")
    req(hist["existing_managed_json_api"] == "System.Text.Json.JsonSerializer.Deserialize", "existing managed JSON API evidence changed")
    req(hist["historical_identity_claim"] is False, "historical identity improperly claimed")

    d = data["decision"]
    req(d["decoder_architecture"] == "SYSTEM_TEXT_JSON_DOM", "decoder architecture changed")
    req(d["decoder_mechanism"] == "System.Text.Json.JsonDocument_JsonElement", "decoder mechanism changed")
    req(d["future_decoder_type"] == "ApexForge.Runtime.ManagedExecutableCarrierDecoder", "future decoder type changed")
    req(d["owner_project"] == "ApexForge.Runtime", "decoder owner changed")
    req(d["component_role"] == "STATELESS_CLOSED_WORLD_STRUCTURAL_DECODER", "decoder role changed")
    req(d["manual_node_dispatch"] is True, "manual closed-world dispatch removed")
    req(d["direct_polymorphic_json_serializer"] is False, "implicit polymorphic serializer selected")
    req(d["utf8_json_reader_initial_implementation"] is False, "Utf8JsonReader selected unexpectedly")
    req(d["custom_external_json_library"] is False, "external JSON dependency selected")
    req(d["decoder_type_name_selected"] is True, "decoder type selection lost")
    req(d["decoder_method_shape"] == "UNSELECTED", "method shape selected too early")
    req(d["implementation"] == "DEFERRED", "implementation selected during architecture gate")

    for key, value in data["rationale"].items():
        req(value is True, f"decoder rationale invariant weakened: {key}")

    deferred = data["deferred_policies"]
    req(deferred["canonical_transport_json_shape"] == "REQUIRES_CENSUS", "JSON shape census bypassed")
    for key in (
        "decoder_method_shape",
        "type_discriminator_contract",
        "json_number_handling",
        "integer_parse_policy",
        "float_parse_policy",
        "special_float_transport_handling",
        "unknown_property_policy",
        "duplicate_property_policy",
        "nullability_policy",
    ):
        req(deferred[key] == "UNSELECTED", f"policy selected too early: {key}")

    if FUTURE_DECODER.exists():
        req((ROOT / "apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json").exists(), "later decoder implementation lacks RCV-43 lineage")

    refs = []
    for directory in (RUNTIME_DIR, HOST_DIR):
        for p in sorted(directory.glob("*.cs")):
            if p.resolve() == CARRIER.resolve():
                continue
            text = p.read_text(encoding="utf-8-sig")
            hits = [token for token in ("ManagedExecutableCarrierDecoder", "JsonDocument", "JsonElement", "Utf8JsonReader") if token in text]
            if hits:
                refs.append((p.relative_to(ROOT).as_posix(), hits))
    if refs:
        req({path for path, _ in refs} == {"runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"}, f"decoder entered unauthorized surfaces: {refs[:8]}")
        req((ROOT / "apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json").exists(), "later decoder implementation lacks RCV-43 lineage")

    boundary = data["boundary"]
    req(boundary["construction_bridge"] == "ABSENT", "construction bridge appeared")
    req(boundary["decoder_implementation"] == "DEFERRED", "decoder implementation selected")
    req(boundary["runtime_crossing"] == "NOT_AUTHORIZED", "runtime crossing authorized")
    req(boundary["external_serialization"] == "UNSELECTED", "external serialization selected")
    req(boundary["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport selected")
    req(boundary["target_neutral_handoff_coupling"] is False, "handoff coupling selected")
    req(boundary["execution_dispatch"] == "DEFERRED", "execution dispatch selected")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["decoder_may_construct_only_authorized_carrier_nodes"] is True, "decoder construction boundary removed")
    req(auth["decoder_may_copy_canonical_structure"] is True, "structural copy permission removed")
    req(auth["decoder_may_reinterpret_semantics"] is False, "decoder gained reinterpretation authority")
    req(auth["decoder_may_execute"] is False, "decoder gained execution authority")
    req(auth["decoder_may_dispatch"] is False, "decoder gained dispatch authority")
    req(auth["decoder_may_select_transport"] is False, "decoder gained transport authority")
    req(auth["decoder_may_mutate_canonical_source"] is False, "decoder gained source mutation authority")

    print("P12_5_RCV_36_PROFILE=apexforge.p12.managed-executable-carrier-decoder-architecture-decision/v1")
    print("P12_5_RCV_36_DECODER_ARCHITECTURE=SYSTEM_TEXT_JSON_DOM")
    print("P12_5_RCV_36_DECODER_MECHANISM=System.Text.Json.JsonDocument_JsonElement")
    print("P12_5_RCV_36_FUTURE_DECODER_TYPE=ApexForge.Runtime.ManagedExecutableCarrierDecoder")
    print("P12_5_RCV_36_MANUAL_NODE_DISPATCH=True")
    print("P12_5_RCV_36_DIRECT_POLYMORPHIC_JSON_SERIALIZER=False")
    print("P12_5_RCV_36_DECODER_METHOD_SHAPE=UNSELECTED")
    print("P12_5_RCV_36_JSON_NUMBER_HANDLING=UNSELECTED")
    print("P12_5_RCV_36_SPECIAL_FLOAT_TRANSPORT_HANDLING=UNSELECTED")
    print("P12_5_RCV_36_DECODER_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_36_RUNTIME_CROSSING=NOT_AUTHORIZED")
    print("P12_5_RCV_36_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_36_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_36_MANAGED_EXECUTABLE_CARRIER_DECODER_ARCHITECTURE_DECISION=PASS")
    print("P12_5_RCV_36_NEXT=P12.5-RCV-37_CANONICAL_AIR_TRANSPORT_JSON_SHAPE_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
