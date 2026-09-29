from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_29_managed_executable_carrier_corrected_type_shape_contract.json"
RCV28 = ROOT / "apexforge/p12_5_rcv_28_managed_executable_carrier_historical_census_smoke_test.py"
CARRIER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs"

EXPECTED_NAMES = [
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

def declaration(data, name):
    for item in data["source_requirements"]["declarations"]:
        if item["name"] == name:
            return item
    raise AssertionError(f"declaration missing: {name}")

def main():
    print("=== P12.5-RCV-29 MANAGED EXECUTABLE CARRIER CORRECTED TYPE-SHAPE CONTRACT ===")
    for p in (CONTRACT, RCV28):
        req(p.exists(), f"missing required file: {p}")

    cp = run(sys.executable, str(RCV28))
    req(cp.returncode == 0, "RCV-28 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_29_RCV28_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-executable-carrier-corrected-type-shape-contract/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-28", "predecessor changed")

    basis = data["historical_basis"]
    req(basis["source_path"] == "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs", "source path changed")
    req(basis["materialized_r1_build_valid"] is False, "R1 incorrectly classified valid")
    req(basis["historical_final_pass_directly_recovered"] is False, "unsupported historical final pass claim introduced")
    req(basis["original_commit_identity_equivalence"] is False, "commit identity equivalence claimed")
    req(basis["corrected_shape_is_recovery_contract"] is True, "recovery-contract classification removed")

    corrections = {(x["observed"], x["selected"], x["surface"]) for x in data["corrections"]}
    req(len(corrections) == 3, "correction count changed")
    req(("IjeadOnlyList<ManagedGenericTypeLike>", "IReadOnlyList<ManagedGenericTypeLike>", "ManagedCallExpression.TypeArguments") in corrections, "TypeArguments correction missing")
    req(("IjeadOnlyList<ManagedConstraintReference>", "IReadOnlyList<ManagedConstraintReference>", "ManagedTypeVariableReference.Constraints") in corrections, "Constraints correction missing")
    req(("ManagedUnharyExpression", "ManagedUnaryExpression", "historical smoke probe unary construction") in corrections, "unary correction missing")

    src = data["source_requirements"]
    req(src["usings"] == ["System.Collections.Generic", "System.Numerics"], "using set changed")
    req(src["namespace"] == "ApexForge.Runtime", "namespace changed")
    req(src["declaration_count"] == 25, "declaration count changed")
    names = [x["name"] for x in src["declarations"]]
    req(names == EXPECTED_NAMES, f"declaration order/shape changed: {names}")

    call = declaration(data, "ManagedCallExpression")
    req(call["parameters"] == [
        ["string", "Target"],
        ["IReadOnlyList<ManagedExecutableExpression>", "Arguments"],
        ["IReadOnlyList<ManagedGenericTypeLike>", "TypeArguments"],
    ], "ManagedCallExpression shape changed")

    variable = declaration(data, "ManagedTypeVariableReference")
    req(variable["parameters"] == [
        ["string", "Name"],
        ["string", "Owner"],
        ["IReadOnlyList<ManagedConstraintReference>", "Constraints"],
    ], "ManagedTypeVariableReference shape changed")

    unary = declaration(data, "ManagedUnaryExpression")
    req(unary["parameters"] == [
        ["string", "Operator"],
        ["ManagedExecutableExpression", "Operand"],
    ], "ManagedUnaryExpression shape changed")

    function = declaration(data, "ManagedExecutableFunction")
    req(function["parameters"] == [
        ["string", "Id"],
        ["string", "Name"],
        ["IReadOnlyList<ManagedFunctionParameter>", "Parameters"],
        ["ManagedExecutableExpression?", "ReturnExpression"],
        ["int", "Order"],
        ["IReadOnlyList<ManagedLocalBinding>", "LocalBindings"],
        ["IReadOnlyList<ManagedFunctionStatement>", "Body"],
        ["ManagedGenericTypeLike?", "ReturnType"],
        ["IReadOnlyList<ManagedTypeVariableReference>", "TypeParameters"],
    ], "ManagedExecutableFunction shape changed")

    inv = data["representation_invariants"]
    req(inv["integer_representation"] == "System.Numerics.BigInteger", "integer representation changed")
    req(inv["float_representation"] == "System.Double_BINARY64", "float representation changed")
    req(inv["string_representation"] == "System.String", "string representation changed")
    req(inv["boolean_representation"] == "System.Boolean", "boolean representation changed")
    req(inv["collection_interface"] == "IReadOnlyList<T>", "collection interface changed")
    req(inv["records_are_data_carriers_only"] is True, "carrier role widened")
    req(inv["no_runtime_execution_methods"] is True, "execution methods authorized")
    req(inv["no_validation_semantic_duplication"] is True, "semantic validation duplication authorized")

    forbidden = set(data["forbidden_concerns"])
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
        "ManagedRuntimeHost",
        "RuntimeHostIngress",
    ):
        req(token in forbidden, f"forbidden concern missing: {token}")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["owner_project"] == "ApexForge.Runtime", "carrier owner changed")
    for key in (
        "carrier_defines_language_semantics",
        "carrier_executes",
        "carrier_dispatches",
        "carrier_serializes",
        "carrier_owns_native_abi",
        "carrier_admits_handoffs",
    ):
        req(auth[key] is False, f"carrier authority widened: {key}")

    req(data["implementation"] == "DEFERRED", "implementation selected during contract gate")
    if CARRIER.exists():
        req((ROOT / "apexforge/p12_5_rcv_30_managed_executable_carrier_implementation_foundation.json").exists(), "later carrier implementation lacks RCV-30 lineage")

    print("P12_5_RCV_29_PROFILE=apexforge.p12.managed-executable-carrier-corrected-type-shape-contract/v1")
    print("P12_5_RCV_29_CORRECTION_COUNT=3")
    print("P12_5_RCV_29_DECLARATION_COUNT=25")
    print("P12_5_RCV_29_COLLECTION_INTERFACE=IReadOnlyList<T>")
    print("P12_5_RCV_29_INTEGER_REPRESENTATION=System.Numerics.BigInteger")
    print("P12_5_RCV_29_FLOAT_REPRESENTATION=System.Double_BINARY64")
    print("P12_5_RCV_29_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_29_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_29_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_29_MANAGED_EXECUTABLE_CARRIER_CORRECTED_TYPE_SHAPE_CONTRACT=PASS")
    print("P12_5_RCV_29_NEXT=P12.5-RCV-30_MANAGED_EXECUTABLE_CARRIER_IMPLEMENTATION_FOUNDATION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
