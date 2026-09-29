from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_33_managed_executable_carrier_derivation_mapping_census.json"
RCV32 = ROOT / "apexforge/p12_5_rcv_32_managed_executable_carrier_derivation_source_decision_smoke_test.py"
AIR_EXPR = ROOT / "apexforge/air/expressions.py"
AIR_FUNC = ROOT / "apexforge/air/functions.py"
TYPE_MODEL = ROOT / "apexforge/type_system/model.py"
TYPE_GENERICS = ROOT / "apexforge/type_system/generics.py"
TYPE_CONSTRAINTS = ROOT / "apexforge/type_system/constraints.py"
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
    print("=== P12.5-RCV-33 MANAGED EXECUTABLE CARRIER DERIVATION MAPPING CENSUS ===")
    for p in (CONTRACT, RCV32, AIR_EXPR, AIR_FUNC, TYPE_MODEL, TYPE_GENERICS, TYPE_CONSTRAINTS, CARRIER, RUNTIME_DIR, HOST_DIR):
        req(p.exists(), f"missing required path: {p}")

    cp = run(sys.executable, str(RCV32))
    req(cp.returncode == 0, "RCV-32 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_33_RCV32_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-executable-carrier-derivation-mapping-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-32", "predecessor changed")

    source = data["selected_source_context"]
    req(source["derivation_source"] == "CANONICAL_AIR_TRANSPORT", "derivation source changed")
    req(source["logical_source_owner"] == "air.model.VerifiedAIRProgram", "source owner changed")
    req(source["canonical_serialization_delegate"] == "air.serialization.air_to_dict", "serialization delegate changed")
    req(source["derivation_owner_project"] == "ApexForge.Runtime", "derivation owner changed")

    hist = data["historical_evidence"]
    req(hist["canonical_executable_dataclass_count"] == 13, "canonical executable dataclass count changed")
    req(hist["generic_type_like_members"] == ["str", "ApexType", "ApexTypeVariable"], "GenericTypeLike topology changed")
    req(hist["constraint_like_members"] == ["str", "ApexTypeConstraint"], "ConstraintLike topology changed")
    req(hist["historical_explicit_mapping_contract_recovered"] is False, "unsupported historical mapping contract claimed")
    req(hist["historical_derivation_bridge_reference_count"] == 0, "historical derivation bridge count changed")
    req(hist["original_commit_identity_equivalence"] is False, "commit identity improperly claimed")

    expr = AIR_EXPR.read_text(encoding="utf-8-sig")
    func = AIR_FUNC.read_text(encoding="utf-8-sig")
    model = TYPE_MODEL.read_text(encoding="utf-8-sig")
    generics = TYPE_GENERICS.read_text(encoding="utf-8-sig")
    constraints = TYPE_CONSTRAINTS.read_text(encoding="utf-8-sig")
    carrier = CARRIER.read_text(encoding="utf-8-sig")

    for name in (
        "AIRIntegerLiteral", "AIRFloatLiteral", "AIRStringLiteral", "AIRBooleanLiteral",
        "AIRIdentifierReference", "AIRUnaryExpression", "AIRBinaryExpression", "AIRCallExpression",
    ):
        req(f"class {name}" in expr, f"canonical expression missing: {name}")

    for name in ("AIRParameter", "AIRLocalBinding", "AIRFunctionReturn", "AIRFunctionWhen", "AIRFunction"):
        req(f"class {name}" in func, f"canonical function/control node missing: {name}")

    req("class ApexType" in model, "ApexType missing")
    req("class ApexTypeVariable" in generics, "ApexTypeVariable missing")
    req("GenericTypeLike" in generics, "GenericTypeLike missing")
    req("class ApexTypeConstraint" in constraints, "ApexTypeConstraint missing")
    req("ConstraintLike" in constraints, "ConstraintLike missing")

    census = data["mapping_census"]
    req(census["concrete_candidate_mapping_count"] == 18, "candidate mapping count changed")
    pairs = [(x["source"], x["target"]) for x in census["candidate_mappings"]]
    req(pairs == EXPECTED_PAIRS, f"candidate mapping topology changed: {pairs}")
    req(census["managed_topology_only_declaration_count"] == 7, "topology-only declaration count changed")
    req(census["managed_topology_only_declarations"] == TOPOLOGY_ONLY, "topology-only declaration set changed")
    req(census["mapping_status"] == "CANDIDATE_ONLY_NOT_AUTHORIZED", "mapping authorized during census")
    req(census["field_name_normalization"] == "snake_case_to_PascalCase_where_structurally_corresponding", "field normalization changed")
    req(census["collection_shape_translation"] == "tuple_to_IReadOnlyList", "collection normalization changed")
    req(census["optional_shape_translation"] == "Optional[T]_to_nullable_reference_or_interface", "optional normalization changed")

    for _, target in EXPECTED_PAIRS:
        req(target in carrier, f"managed carrier target missing: {target}")
    for target in TOPOLOGY_ONLY:
        req(target in carrier, f"managed topology declaration missing: {target}")

    # Accept only the later RCV-43 construction bridge.
    refs = []
    for directory in (RUNTIME_DIR, HOST_DIR):
        for p in sorted(directory.glob("*.cs")):
            if p.resolve() == CARRIER.resolve():
                continue
            text = p.read_text(encoding="utf-8-sig")
            hits = sorted({target for _, target in EXPECTED_PAIRS if target in text})
            if hits:
                refs.append((p.relative_to(ROOT).as_posix(), hits))
    if refs:
        req({path for path, _ in refs} == {"runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"}, f"construction bridge entered unauthorized surfaces: {refs[:8]}")
        req((ROOT / "apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json").exists(), "later decoder implementation lacks RCV-43 lineage")

    boundary = data["boundary"]
    req(boundary["decoder_component"] == "UNSELECTED", "decoder component selected during census")
    req(boundary["decoder_implementation"] == "DEFERRED", "decoder implementation selected")
    req(boundary["construction_bridge"] == "ABSENT", "construction bridge appeared")
    req(boundary["runtime_crossing"] == "NOT_AUTHORIZED", "runtime crossing authorized")
    req(boundary["external_serialization"] == "UNSELECTED", "external serialization selected")
    req(boundary["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "transport selected")
    req(boundary["execution_dispatch"] == "DEFERRED", "execution dispatch selected")
    req(boundary["target_neutral_handoff_coupling"] is False, "handoff coupling selected")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["mapping_may_copy_canonical_structure"] is True, "structural copy permission missing")
    req(auth["mapping_may_normalize_container_shape"] is True, "container normalization permission missing")
    req(auth["mapping_may_reinterpret_semantics"] is False, "mapping gained reinterpretation authority")
    req(auth["mapping_may_execute"] is False, "mapping gained execution authority")
    req(auth["mapping_may_dispatch"] is False, "mapping gained dispatch authority")
    req(auth["mapping_may_select_transport"] is False, "mapping gained transport authority")

    print("P12_5_RCV_33_PROFILE=apexforge.p12.managed-executable-carrier-derivation-mapping-census/v1")
    print("P12_5_RCV_33_CANONICAL_EXECUTABLE_DATACLASS_COUNT=13")
    print("P12_5_RCV_33_CONCRETE_CANDIDATE_MAPPING_COUNT=18")
    print("P12_5_RCV_33_MANAGED_TOPOLOGY_ONLY_DECLARATION_COUNT=7")
    print("P12_5_RCV_33_MAPPING_STATUS=CANDIDATE_ONLY_NOT_AUTHORIZED")
    print("P12_5_RCV_33_EXISTING_CONSTRUCTION_BRIDGE_REFERENCE_COUNT=0")
    print("P12_5_RCV_33_DECODER_COMPONENT=UNSELECTED")
    print("P12_5_RCV_33_DECODER_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_33_RUNTIME_CROSSING=NOT_AUTHORIZED")
    print("P12_5_RCV_33_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_33_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_33_MANAGED_EXECUTABLE_CARRIER_DERIVATION_MAPPING_CENSUS=PASS")
    print("P12_5_RCV_33_NEXT=P12.5-RCV-34_MANAGED_EXECUTABLE_CARRIER_DERIVATION_MAPPING_CONTRACT")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
