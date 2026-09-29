from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_28_managed_executable_carrier_historical_census.json"
RCV27 = ROOT / "apexforge/p12_5_rcv_27_managed_host_program_integration_contract_smoke_test.py"
CARRIER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs"
RUNTIME_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"

EXPECTED_TYPES = [
    "ManagedExecutableExpression",
    "ManagedIntegerLiteral",
    "ManagedFloatLiteral",
    "ManagedStringLiteral",
    "ManagedBooleanLiteral",
    "ManagedIdentifierReference",
    "ManagedUnaryExpression",
    "ManagedBinaryExpression",
    "ManagedCallExpression",
    "ManagedTypeReference",
    "ManagedGenericTypeLike",
    "ManagedTypeLike",
    "ManagedTypeIdentity",
    "ManagedNamedTypeReference",
    "ManagedApexTypeReference",
    "ManagedTypeVariableReference",
    "ManagedConstraintReference",
    "ManagedNamedConstraintReference",
    "ManagedApexTypeConstraintReference",
    "ManagedFunctionParameter",
    "ManagedFunctionStatement",
    "ManagedLocalBinding",
    "ManagedFunctionReturn",
    "ManagedFunctionWhen",
    "ManagedExecutableFunction",
]

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-28 MANAGED EXECUTABLE CARRIER HISTORICAL CENSUS ===")
    for p in (CONTRACT, RCV27, RUNTIME_DIR, HOST_DIR):
        req(p.exists(), f"missing required path: {p}")

    cp = run(sys.executable, str(RCV27))
    req(cp.returncode == 0, "RCV-27 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_28_RCV27_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-executable-carrier-historical-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-27", "predecessor changed")

    target = data["historical_target"]
    req(target["path"] == "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs", "carrier path changed")
    req(target["owner_project"] == "ApexForge.Runtime", "carrier owner changed")
    req(target["later_snapshot_presence_confirmed"] is True, "historical carrier presence lost")
    req(target["original_commit_identity_equivalence"] is False, "commit identity equivalence improperly claimed")
    req(target["historical_final_pass_directly_recovered"] is False, "unsupported historical final-pass claim introduced")

    shape = data["recovered_intended_shape"]
    req(shape["declaration_count"] == 25, "historical declaration count changed")
    req(shape["declarations"] == EXPECTED_TYPES, "historical type graph changed")
    req(shape["uses_big_integer"] is True, "BigInteger representation lost")
    req(shape["uses_binary64_double"] is True, "binary64 representation lost")
    req(shape["uses_string"] is True, "string representation lost")
    req(shape["uses_boolean"] is True, "boolean representation lost")
    req(shape["generic_type_graph"] is True, "generic type graph lost")
    req(shape["constraint_graph"] is True, "constraint graph lost")
    req(shape["function_graph"] is True, "function graph lost")
    req(shape["expected_collection_interface"] == "IReadOnlyList<T>", "collection interface changed")

    diag = data["materialized_r1_diagnostic"]
    req(diag["candidate_build_valid"] is False, "defective R1 candidate incorrectly classified build-valid")
    req(diag["carrier_smoke_passed"] is False, "defective R1 carrier smoke incorrectly classified pass")
    req(diag["managed_handoff_regression_passed"] is False, "defective R1 regression incorrectly classified pass")
    req(diag["candidate_bytes_were_left_unchanged"] is True, "historical diagnostic mutation policy changed")
    req(diag["diagnostic_result"] == "REVIEW_REQUIRED", "historical diagnostic result changed")
    req(len(diag["defects"]) == 3, "historical defect census changed")

    defects = {(x["observed"], x["intended"], x["classification"]) for x in diag["defects"]}
    req(("IjeadOnlyList<ManagedGenericTypeLike>", "IReadOnlyList<ManagedGenericTypeLike>", "TRANSCRIPTION_DEFECT") in defects, "TypeArguments defect missing")
    req(("IjeadOnlyList<ManagedConstraintReference>", "IReadOnlyList<ManagedConstraintReference>", "TRANSCRIPTION_DEFECT") in defects, "Constraints defect missing")
    req(("ManagedUnharyExpression", "ManagedUnaryExpression", "SMOKE_TRANSCRIPTION_DEFECT") in defects, "unary smoke defect missing")

    exclusions = set(data["historical_boundary_exclusions"])
    for token in (
        "JsonSerializer",
        "FromJson",
        "LibraryImport",
        "DllImport",
        "apexforge_native",
        "CanonicalExecutionEnvelope",
        "TargetNeutralLoweringHandoff",
        "Execute(",
        "Dispatch(",
    ):
        req(token in exclusions, f"historical exclusion missing: {token}")

    if CARRIER.exists():
        req((ROOT / "apexforge/p12_5_rcv_30_managed_executable_carrier_implementation_foundation.json").exists(), "later carrier implementation lacks RCV-30 lineage")

    production_refs = []
    for directory in (RUNTIME_DIR, HOST_DIR):
        for p in sorted(directory.glob("*.cs")):
            text = p.read_text(encoding="utf-8-sig")
            for name in EXPECTED_TYPES:
                if name in text:
                    production_refs.append((p.relative_to(ROOT).as_posix(), name))

    if production_refs:
        allowed_paths = {
            "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs",
            "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs",
        }
        req({path for path, _ in production_refs} <= allowed_paths, f"carrier graph entered unauthorized production surfaces: {production_refs[:10]}")
        req((ROOT / "apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json").exists(), "later decoder implementation lacks RCV-43 lineage")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    for key in (
        "carrier_defines_language_semantics",
        "carrier_executes",
        "carrier_dispatches",
        "carrier_serializes",
        "carrier_owns_native_abi",
    ):
        req(auth[key] is False, f"carrier authority widened: {key}")

    state = data["current_recovery_state"]
    req(state["carrier_implementation"] == "ABSENT_AT_CENSUS_GATE", "carrier implementation state changed")
    req(state["carrier_reconstruction_authorized"] is False, "carrier reconstruction authorized too early")
    req(state["execution_dispatch"] == "DEFERRED", "execution dispatch selected")
    req(state["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport selected")
    req(state["external_serialization"] == "UNSELECTED", "serialization selected")

    print("P12_5_RCV_28_PROFILE=apexforge.p12.managed-executable-carrier-historical-census/v1")
    print("P12_5_RCV_28_HISTORICAL_CARRIER_PATH=runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs")
    print("P12_5_RCV_28_HISTORICAL_LATER_SNAPSHOT_PRESENCE=True")
    print("P12_5_RCV_28_INTENDED_DECLARATION_COUNT=25")
    print("P12_5_RCV_28_R1_CANDIDATE_BUILD_VALID=False")
    print("P12_5_RCV_28_R1_DIAGNOSTIC=REVIEW_REQUIRED")
    print("P12_5_RCV_28_TRANSCRIPTION_DEFECT_COUNT=3")
    print("P12_5_RCV_28_CURRENT_CARRIER_IMPLEMENTATION=ABSENT")
    print("P12_5_RCV_28_CARRIER_RECONSTRUCTION_AUTHORIZED=False")
    print("P12_5_RCV_28_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_28_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_28_MANAGED_EXECUTABLE_CARRIER_HISTORICAL_CENSUS=PASS")
    print("P12_5_RCV_28_NEXT=P12.5-RCV-29_MANAGED_EXECUTABLE_CARRIER_CORRECTED_TYPE_SHAPE_CONTRACT")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
