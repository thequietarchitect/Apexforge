from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_34_managed_executable_carrier_derivation_mapping_contract.json"
RCV33 = ROOT / "apexforge/p12_5_rcv_33_managed_executable_carrier_derivation_mapping_census_smoke_test.py"
CARRIER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs"
RUNTIME_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"

EXPECTED_PAIRS = [
    ("AIRIntegerLiteral", "ManagedIntegerLiteral"),
    ("AIRFloatLiteral", "ManagedFloatLiteral"),
    ("AIRStringLiteral", "ManagedStringLiteral"),
    ("AIRBooleanLiteral", "ManagedBooleanLiteral"),
    ("AIRIdentifierReference", "ManagedIdentifierReference"),
    ("AIRUnaryExpression", "ManagedUnaryExpression"),
    ("AIRBinaryExpression", "ManagedBinaryExpression"),
    ("AIRCallExpression", "ManagedCallExpression"),
    ("AIRParameter", "ManagedFunctionParameter"),
    ("AIRLocalBinding", "ManagedLocalBinding"),
    ("AIRFunctionReturn", "ManagedFunctionReturn"),
    ("AIRFunctionWhen", "ManagedFunctionWhen"),
    ("AIRFunction", "ManagedExecutableFunction"),
    ("str(GenericTypeLike)", "ManagedNamedTypeReference"),
    ("ApexType", "ManagedApexTypeReference"),
    ("ApexTypeVariable", "ManagedTypeVariableReference"),
    ("str(ConstraintLike)", "ManagedNamedConstraintReference"),
    ("ApexTypeConstraint", "ManagedApexTypeConstraintReference"),
]

TOPOLOGY_ONLY = [
    "ManagedExecutableExpression",
    "ManagedTypeReference",
    "ManagedGenericTypeLike",
    "ManagedTypeLike",
    "ManagedTypeIdentity",
    "ManagedConstraintReference",
    "ManagedFunctionStatement",
]

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-34 MANAGED EXECUTABLE CARRIER DERIVATION MAPPING CONTRACT ===")
    for p in (CONTRACT, RCV33, CARRIER, RUNTIME_DIR, HOST_DIR):
        req(p.exists(), f"missing required path: {p}")

    cp = run(sys.executable, str(RCV33))
    req(cp.returncode == 0, "RCV-33 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_34_RCV33_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-executable-carrier-derivation-mapping-contract/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-33", "predecessor changed")

    src = data["source_contract"]
    req(src["derivation_source"] == "CANONICAL_AIR_TRANSPORT", "derivation source changed")
    req(src["logical_source_owner"] == "air.model.VerifiedAIRProgram", "source owner changed")
    req(src["canonical_serialization_delegate"] == "air.serialization.air_to_dict", "serialization delegate changed")
    req(src["derivation_owner_project"] == "ApexForge.Runtime", "derivation owner changed")

    mapping = data["mapping_contract"]
    req(mapping["authorized_mapping_count"] == 18, "authorized mapping count changed")
    pairs = [(x["source"], x["target"]) for x in mapping["authorized_mappings"]]
    req(pairs == EXPECTED_PAIRS, f"authorized mapping topology changed: {pairs}")
    req(mapping["topology_only_declaration_count"] == 7, "topology-only count changed")
    req(mapping["topology_only_declarations"] == TOPOLOGY_ONLY, "topology-only set changed")
    req(mapping["field_name_normalization"] == "snake_case_to_PascalCase_where_structurally_corresponding", "field normalization changed")
    req(mapping["collection_shape_translation"] == "tuple_to_IReadOnlyList_preserve_order", "collection rule changed")
    req(mapping["optional_shape_translation"] == "Optional[T]_to_nullable_reference_or_interface", "optional rule changed")
    req(mapping["integer_translation"] == "PYTHON_INTEGER_TO_SYSTEM_NUMERICS_BIGINTEGER_EXACT", "integer translation changed")
    req(mapping["float_translation"] == "CANONICAL_AIR_FLOAT_TO_SYSTEM_DOUBLE_BINARY64", "float translation changed")
    req(mapping["string_translation"] == "UNICODE_SCALAR_CONTENT_PRESERVED_AS_DOTNET_STRING", "string translation changed")
    req(mapping["boolean_translation"] == "BOOLEAN_VALUE_PRESERVED", "boolean translation changed")

    recursive = data["recursive_rules"]
    for key, value in recursive.items():
        req(value is True, f"recursive/order invariant weakened: {key}")

    closed = data["closed_world_rules"]
    req(closed["unknown_expression_kind"] == "REJECT", "unknown expressions no longer rejected")
    req(closed["unknown_function_statement_kind"] == "REJECT", "unknown statements no longer rejected")
    req(closed["unknown_generic_type_kind"] == "REJECT", "unknown generic types no longer rejected")
    req(closed["unknown_constraint_kind"] == "REJECT", "unknown constraints no longer rejected")
    req(closed["missing_required_field"] == "REJECT", "missing fields no longer rejected")
    req(closed["unexpected_semantic_coercion"] == "REJECT", "semantic coercion allowed")
    req(closed["silent_default_injection"] == "FORBIDDEN", "silent defaults allowed")

    carrier = CARRIER.read_text(encoding="utf-8-sig")
    for _, target in EXPECTED_PAIRS:
        req(target in carrier, f"managed carrier target missing: {target}")
    for target in TOPOLOGY_ONLY:
        req(target in carrier, f"managed topology declaration missing: {target}")

    # Contract-only at this gate; accept only the later RCV-43 bridge.
    bridge_refs = []
    for directory in (RUNTIME_DIR, HOST_DIR):
        for p in sorted(directory.glob("*.cs")):
            if p.resolve() == CARRIER.resolve():
                continue
            text = p.read_text(encoding="utf-8-sig")
            hits = []
            for token in (
                "ManagedIntegerLiteral(",
                "ManagedFloatLiteral(",
                "ManagedStringLiteral(",
                "ManagedBooleanLiteral(",
                "ManagedIdentifierReference(",
                "ManagedUnaryExpression(",
                "ManagedBinaryExpression(",
                "ManagedCallExpression(",
                "ManagedExecutableFunction(",
            ):
                if token in text:
                    hits.append(token)
            if hits:
                bridge_refs.append((p.relative_to(ROOT).as_posix(), hits))
    if bridge_refs:
        req({path for path, _ in bridge_refs} == {"runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"}, f"construction bridge entered unauthorized surfaces: {bridge_refs[:8]}")
        req((ROOT / "apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json").exists(), "later decoder implementation lacks RCV-43 lineage")

    boundary = data["boundary"]
    req(boundary["decoder_component"] == "UNSELECTED", "decoder selected during mapping contract")
    req(boundary["decoder_implementation"] == "DEFERRED", "decoder implementation selected")
    req(boundary["construction_bridge"] == "ABSENT", "construction bridge state changed")
    req(boundary["runtime_crossing"] == "NOT_AUTHORIZED", "runtime crossing authorized")
    req(boundary["json_number_handling"] == "UNSELECTED", "JSON number handling selected early")
    req(boundary["special_float_transport_handling"] == "UNSELECTED", "special float handling selected early")
    req(boundary["external_serialization"] == "UNSELECTED", "external serialization selected")
    req(boundary["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "transport selected")
    req(boundary["target_neutral_handoff_coupling"] is False, "handoff coupling selected")
    req(boundary["execution_dispatch"] == "DEFERRED", "execution dispatch selected")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["mapping_is_structural_projection_only"] is True, "structural-only classification removed")
    req(auth["mapping_may_reinterpret_semantics"] is False, "mapping gained reinterpretation authority")
    req(auth["mapping_may_execute"] is False, "mapping gained execution authority")
    req(auth["mapping_may_dispatch"] is False, "mapping gained dispatch authority")
    req(auth["mapping_may_select_transport"] is False, "mapping gained transport authority")
    req(auth["mapping_may_mutate_canonical_source"] is False, "mapping gained source mutation authority")

    req(data["historical_identity_claim"] is False, "historical identity improperly claimed")
    req(data["implementation"] == "DEFERRED", "implementation selected during contract gate")

    print("P12_5_RCV_34_PROFILE=apexforge.p12.managed-executable-carrier-derivation-mapping-contract/v1")
    print("P12_5_RCV_34_AUTHORIZED_MAPPING_COUNT=18")
    print("P12_5_RCV_34_TOPOLOGY_ONLY_DECLARATION_COUNT=7")
    print("P12_5_RCV_34_CLOSED_WORLD_MAPPING=True")
    print("P12_5_RCV_34_COLLECTION_ORDER_PRESERVED=True")
    print("P12_5_RCV_34_INTEGER_TRANSLATION=PYTHON_INTEGER_TO_SYSTEM_NUMERICS_BIGINTEGER_EXACT")
    print("P12_5_RCV_34_FLOAT_TRANSLATION=CANONICAL_AIR_FLOAT_TO_SYSTEM_DOUBLE_BINARY64")
    print("P12_5_RCV_34_DECODER_COMPONENT=UNSELECTED")
    print("P12_5_RCV_34_JSON_NUMBER_HANDLING=UNSELECTED")
    print("P12_5_RCV_34_RUNTIME_CROSSING=NOT_AUTHORIZED")
    print("P12_5_RCV_34_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_34_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_34_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_34_MANAGED_EXECUTABLE_CARRIER_DERIVATION_MAPPING_CONTRACT=PASS")
    print("P12_5_RCV_34_NEXT=P12.5-RCV-35_MANAGED_EXECUTABLE_CARRIER_DECODER_ARCHITECTURE_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
