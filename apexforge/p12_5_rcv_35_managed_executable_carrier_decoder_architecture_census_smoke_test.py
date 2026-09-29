from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_35_managed_executable_carrier_decoder_architecture_census.json"
RCV34 = ROOT / "apexforge/p12_5_rcv_34_managed_executable_carrier_derivation_mapping_contract_smoke_test.py"
CARRIER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs"
ENVELOPE = ROOT / "runtimes/dotnet/ApexForge.Runtime/CanonicalExecutionEnvelope.cs"
RUNTIME_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"

CARRIER_CONSTRUCTORS = (
    "new ManagedIntegerLiteral(",
    "new ManagedFloatLiteral(",
    "new ManagedStringLiteral(",
    "new ManagedBooleanLiteral(",
    "new ManagedIdentifierReference(",
    "new ManagedUnaryExpression(",
    "new ManagedBinaryExpression(",
    "new ManagedCallExpression(",
    "new ManagedNamedTypeReference(",
    "new ManagedApexTypeReference(",
    "new ManagedTypeVariableReference(",
    "new ManagedNamedConstraintReference(",
    "new ManagedApexTypeConstraintReference(",
    "new ManagedFunctionParameter(",
    "new ManagedLocalBinding(",
    "new ManagedFunctionReturn(",
    "new ManagedFunctionWhen(",
    "new ManagedExecutableFunction(",
)

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-35 MANAGED EXECUTABLE CARRIER DECODER ARCHITECTURE CENSUS ===")
    for p in (CONTRACT, RCV34, CARRIER, ENVELOPE, RUNTIME_DIR, HOST_DIR):
        req(p.exists(), f"missing required path: {p}")

    cp = run(sys.executable, str(RCV34))
    req(cp.returncode == 0, "RCV-34 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_35_RCV34_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-executable-carrier-decoder-architecture-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-34", "predecessor changed")

    hist = data["historical_evidence"]
    req(hist["historical_managed_carrier_decoder_recovered"] is False, "unsupported historical carrier decoder claimed")
    req(hist["historical_managed_air_transport_reference_count"] == 2, "historical managed transport count changed")
    req(hist["historical_managed_json_deserializer"] == "CanonicalExecutionEnvelope.FromJson", "historical managed deserializer changed")
    req(hist["historical_managed_json_serializer_api"] == "System.Text.Json.JsonSerializer.Deserialize", "historical JSON API changed")
    req(hist["historical_target_neutral_handoff_external_serialization"] == "UNSELECTED", "handoff serialization history changed")
    req(hist["historical_carrier_external_serialization"] == "NOT_RECOVERED", "unsupported carrier serialization history claimed")
    req(hist["original_commit_identity_equivalence"] is False, "original commit identity improperly claimed")

    source = data["source_contract"]
    req(source["derivation_source"] == "CANONICAL_AIR_TRANSPORT", "derivation source changed")
    req(source["canonical_serialization_delegate"] == "air.serialization.air_to_dict", "canonical serializer changed")
    req(source["authorized_mapping_count"] == 18, "mapping count changed")
    req(source["closed_world_mapping"] is True, "closed-world mapping weakened")

    envelope = ENVELOPE.read_text(encoding="utf-8-sig")
    req("public static CanonicalExecutionEnvelope FromJson(string json)" in envelope, "historical/current envelope FromJson surface missing")
    req("JsonSerializer.Deserialize<CanonicalExecutionEnvelope>" in envelope, "existing managed JSON facility changed")

    carrier = CARRIER.read_text(encoding="utf-8-sig")
    carrier_tokens = {
        "from_json": "FromJson" in carrier,
        "json_serializer": "JsonSerializer" in carrier,
        "json_document": "JsonDocument" in carrier,
        "json_element": "JsonElement" in carrier,
        "utf8_reader": "Utf8JsonReader" in carrier,
    }
    for key, present in carrier_tokens.items():
        req(not present, f"carrier decoder concern appeared inside carrier definition: {key}")

    runtime_decoder_refs = []
    host_decoder_refs = []
    runtime_construction_refs = []
    for directory, sink in ((RUNTIME_DIR, runtime_decoder_refs), (HOST_DIR, host_decoder_refs)):
        for p in sorted(directory.glob("*.cs")):
            if p.resolve() == CARRIER.resolve():
                continue
            text = p.read_text(encoding="utf-8-sig")
            hits = []
            for token in ("ManagedExecutableDecoder", "ManagedExecutableCarrierDecoder", "JsonDocument", "JsonElement", "Utf8JsonReader"):
                if token in text:
                    hits.append(token)
            if hits:
                sink.append((p.relative_to(ROOT).as_posix(), hits))
            if directory == RUNTIME_DIR:
                constructor_hits = [token for token in CARRIER_CONSTRUCTORS if token in text]
                if constructor_hits:
                    runtime_construction_refs.append((p.relative_to(ROOT).as_posix(), constructor_hits))

    # Existing envelope JSON is allowed. A carrier decoder may now exist only
    # as the later RCV-43 runtime implementation, never in the host.
    if runtime_decoder_refs or runtime_construction_refs:
        allowed = {"runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"}
        req({path for path, _ in runtime_decoder_refs} <= allowed, f"decoder entered unauthorized runtime surfaces: {runtime_decoder_refs[:8]}")
        req({path for path, _ in runtime_construction_refs} <= allowed, f"construction entered unauthorized runtime surfaces: {runtime_construction_refs[:8]}")
        req((ROOT / "apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json").exists(), "later decoder implementation lacks RCV-43 lineage")
    req(len(host_decoder_refs) == 0, f"host carrier decoder architecture already present: {host_decoder_refs[:8]}")

    candidates = data["candidate_decoder_architectures"]
    ids = [x["id"] for x in candidates]
    req(ids == [
        "SYSTEM_TEXT_JSON_DOM",
        "SYSTEM_TEXT_JSON_READER",
        "SYSTEM_TEXT_JSON_DIRECT_SERIALIZER",
        "OTHER_EXPLICIT_DECODER",
    ], "decoder candidate set changed")

    dom = candidates[0]
    req(dom["mechanism"] == "JsonDocument/JsonElement", "DOM candidate changed")
    req(dom["supports_closed_world_manual_dispatch"] is True, "DOM closed-world capability changed")
    req(dom["requires_explicit_number_policy"] is True, "DOM number policy requirement removed")
    req(dom["requires_explicit_special_float_policy"] is True, "DOM special-float policy requirement removed")

    reader = candidates[1]
    req(reader["mechanism"] == "Utf8JsonReader", "reader candidate changed")
    req(reader["supports_closed_world_manual_dispatch"] is True, "reader closed-world capability changed")

    direct = candidates[2]
    req(direct["mechanism"] == "JsonSerializer.Deserialize", "direct serializer candidate changed")
    req(direct["status"] == "CANDIDATE_WITH_POLYMORPHISM_RISK", "direct serializer risk classification changed")
    req(direct["requires_explicit_polymorphic_configuration"] is True, "polymorphic requirement removed")

    expected = data["census_expectations"]
    for key, value in expected.items():
        req(value is False, f"census expectation widened: {key}")

    unresolved = data["unresolved"]
    req(unresolved["decoder_architecture"] == "UNSELECTED", "decoder architecture selected during census")
    req(unresolved["decoder_type_name"] == "UNSELECTED", "decoder type selected during census")
    req(unresolved["decoder_method_shape"] == "UNSELECTED", "decoder method selected during census")
    req(unresolved["json_number_handling"] == "UNSELECTED", "JSON number policy selected")
    req(unresolved["integer_parse_policy"] == "UNSELECTED", "integer parse policy selected")
    req(unresolved["float_parse_policy"] == "UNSELECTED", "float parse policy selected")
    req(unresolved["special_float_transport_handling"] == "UNSELECTED", "special float policy selected")
    req(unresolved["type_discriminator_contract"] == "UNSELECTED", "discriminator selected")
    req(unresolved["unknown_property_policy"] == "UNSELECTED", "unknown-property policy selected")
    req(unresolved["duplicate_property_policy"] == "UNSELECTED", "duplicate-property policy selected")
    req(unresolved["runtime_crossing"] == "NOT_AUTHORIZED", "runtime crossing authorized")
    req(unresolved["external_serialization"] == "UNSELECTED", "external serialization selected")
    req(unresolved["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport selected")
    req(unresolved["execution_dispatch"] == "DEFERRED", "execution dispatch selected")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["decoder_owner_project_if_selected"] == "ApexForge.Runtime", "candidate decoder owner changed")
    req(auth["decoder_may_construct_authorized_carrier_nodes"] is True, "decoder structural construction permission missing")
    req(auth["decoder_may_reinterpret_semantics"] is False, "decoder gained semantic authority")
    req(auth["decoder_may_execute"] is False, "decoder gained execution authority")
    req(auth["decoder_may_dispatch"] is False, "decoder gained dispatch authority")
    req(auth["decoder_may_select_transport"] is False, "decoder gained transport authority")

    print("P12_5_RCV_35_PROFILE=apexforge.p12.managed-executable-carrier-decoder-architecture-census/v1")
    print("P12_5_RCV_35_HISTORICAL_MANAGED_CARRIER_DECODER_RECOVERED=False")
    print("P12_5_RCV_35_EXISTING_ENVELOPE_JSON_DESERIALIZER=True")
    print("P12_5_RCV_35_CARRIER_FROM_JSON_PRESENT=False")
    print("P12_5_RCV_35_CARRIER_JSON_SERIALIZER_PRESENT=False")
    print("P12_5_RCV_35_CARRIER_JSON_DOCUMENT_PRESENT=False")
    print("P12_5_RCV_35_CARRIER_UTF8_JSON_READER_PRESENT=False")
    print("P12_5_RCV_35_RUNTIME_CARRIER_CONSTRUCTION_BRIDGE_REFERENCE_COUNT=0")
    print("P12_5_RCV_35_DECODER_CANDIDATE_COUNT=4")
    print("P12_5_RCV_35_DECODER_ARCHITECTURE=UNSELECTED")
    print("P12_5_RCV_35_JSON_NUMBER_HANDLING=UNSELECTED")
    print("P12_5_RCV_35_SPECIAL_FLOAT_TRANSPORT_HANDLING=UNSELECTED")
    print("P12_5_RCV_35_RUNTIME_CROSSING=NOT_AUTHORIZED")
    print("P12_5_RCV_35_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_35_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_35_MANAGED_EXECUTABLE_CARRIER_DECODER_ARCHITECTURE_CENSUS=PASS")
    print("P12_5_RCV_35_NEXT=P12.5-RCV-36_MANAGED_EXECUTABLE_CARRIER_DECODER_ARCHITECTURE_DECISION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
