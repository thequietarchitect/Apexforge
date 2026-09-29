from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_31_managed_executable_carrier_derivation_boundary_census.json"
RCV30 = ROOT / "apexforge/p12_5_rcv_30_managed_executable_carrier_implementation_foundation_smoke_test.py"
CARRIER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs"
MANAGED_HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"
AIR_EXPR = ROOT / "apexforge/air/expressions.py"
AIR_FUNC = ROOT / "apexforge/air/functions.py"
AIR_MODEL = ROOT / "apexforge/air/model.py"
AIR_SERIALIZATION = ROOT / "apexforge/air/serialization.py"

CARRIER_NAMES = (
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
)

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def production_python_files():
    files = []
    for p in sorted((ROOT / "apexforge").rglob("*.py")):
        rel = p.relative_to(ROOT)
        if p.name.startswith("p12_"):
            continue
        if "__pycache__" in p.parts:
            continue
        files.append(p)
    return files

def main():
    print("=== P12.5-RCV-31 MANAGED EXECUTABLE CARRIER DERIVATION BOUNDARY CENSUS ===")
    for p in (CONTRACT, RCV30, CARRIER, MANAGED_HOST, HANDOFF, HOST_DIR, AIR_EXPR, AIR_FUNC, AIR_MODEL, AIR_SERIALIZATION):
        req(p.exists(), f"missing required path: {p}")

    cp = run(sys.executable, str(RCV30))
    req(cp.returncode == 0, "RCV-30 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_31_RCV30_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-executable-carrier-derivation-boundary-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-30", "predecessor changed")

    hist = data["historical_q_census"]
    req(hist["canonical_derivation_source_reference_count"] == 139, "historical canonical-source count changed")
    req(hist["managed_runtime_reference_count"] == 26, "historical managed-runtime count changed")
    req(hist["production_python_managed_carrier_reference_count"] == 0, "historical Python carrier count changed")
    req(hist["existing_derivation_bridge_reference_count"] == 0, "historical bridge count changed")
    req(hist["existing_handoff_boundary_reference_count"] == 22, "historical handoff-boundary count changed")
    req(hist["regression_stack_pass"] is True, "historical regression stack changed")
    req(hist["repository_unchanged"] is True, "historical repository mutation classification changed")
    req(hist["gate_passed"] is True, "historical Q gate classification changed")
    req(hist["original_commit_identity_equivalence"] is False, "historical commit identity improperly claimed")

    expr = AIR_EXPR.read_text(encoding="utf-8-sig")
    func = AIR_FUNC.read_text(encoding="utf-8-sig")
    model = AIR_MODEL.read_text(encoding="utf-8-sig")
    ser = AIR_SERIALIZATION.read_text(encoding="utf-8-sig")

    for token in ("AIRIntegerLiteral", "AIRFloatLiteral", "AIRStringLiteral", "AIRBooleanLiteral", "AIRCallExpression"):
        req(token in expr, f"canonical AIR expression source missing: {token}")
    for token in ("AIRParameter", "AIRLocalBinding", "AIRFunctionReturn", "AIRFunctionWhen", "AIRFunction"):
        req(token in func, f"canonical AIR function source missing: {token}")
    req("VerifiedAIRProgram" in model, "VerifiedAIRProgram missing")
    req("def air_to_dict" in ser, "canonical AIR serialization delegate missing")

    python_refs = []
    for p in production_python_files():
        text = p.read_text(encoding="utf-8-sig")
        hits = sorted({name for name in CARRIER_NAMES if name in text})
        if hits:
            python_refs.append((p.relative_to(ROOT).as_posix(), hits))
    req(len(python_refs) == 0, f"production Python already references managed carrier types: {python_refs[:8]}")

    csharp_refs = []
    runtime_dir = ROOT / "runtimes/dotnet/ApexForge.Runtime"
    for p in sorted(runtime_dir.glob("*.cs")) + sorted(HOST_DIR.glob("*.cs")):
        if p.resolve() == CARRIER.resolve():
            continue
        text = p.read_text(encoding="utf-8-sig")
        hits = sorted({name for name in CARRIER_NAMES if name in text})
        if hits:
            csharp_refs.append((p.relative_to(ROOT).as_posix(), hits))
    if csharp_refs:
        req({path for path, _ in csharp_refs} == {"runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"}, f"carrier derivation entered unauthorized managed surfaces: {csharp_refs[:8]}")
        req((ROOT / "apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json").exists(), "later decoder implementation lacks RCV-43 lineage")

    handoff_text = HANDOFF.read_text(encoding="utf-8-sig")
    host_text = MANAGED_HOST.read_text(encoding="utf-8-sig")
    req("ManagedExecutable" not in handoff_text, "target-neutral handoff coupled to managed carrier")
    req("ManagedExecutable" not in host_text, "ManagedRuntimeHost coupled to managed carrier")

    carrier_text = CARRIER.read_text(encoding="utf-8-sig")
    for forbidden in (
        "VerifiedAIRProgram",
        "AIRIntegerLiteral",
        "TargetNeutralLoweringHandoff",
        "JsonSerializer",
        "Execute(",
        "Dispatch(",
        "ManagedNativeAbi",
    ):
        req(forbidden not in carrier_text, f"derivation/execution concern entered carrier definition: {forbidden}")

    census = data["census_result"]
    req(census["managed_carrier_implementation_present"] is True, "carrier implementation state changed")
    req(census["production_python_managed_carrier_reference_expected"] == 0, "Python carrier expectation changed")
    req(census["existing_derivation_bridge_expected"] is False, "derivation bridge expected too early")
    req(census["managed_runtime_derivation_bridge_expected"] is False, "managed derivation bridge expected too early")
    req(census["target_neutral_handoff_carrier_coupling_expected"] is False, "handoff coupling expected too early")
    req(census["derivation_source"] == "UNSELECTED", "derivation source selected during census")
    req(census["derivation_owner"] == "UNSELECTED", "derivation owner selected during census")
    req(census["derivation_direction"] == "UNSELECTED", "derivation direction selected during census")
    req(census["carrier_execution_authority"] is False, "carrier gained execution authority")

    constraints = data["boundary_constraints"]
    for key, value in constraints.items():
        req(value is True, f"boundary constraint weakened: {key}")

    deferred = data["deferred"]
    req(deferred["carrier_derivation_source"] == "UNSELECTED", "carrier derivation source selected")
    req(deferred["carrier_derivation_implementation"] == "DEFERRED", "carrier derivation implementation selected")
    req(deferred["carrier_handoff_coupling"] == "DEFERRED", "carrier handoff coupling selected")
    req(deferred["external_serialization"] == "UNSELECTED", "serialization selected")
    req(deferred["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport selected")
    req(deferred["managed_execution_dispatch"] == "DEFERRED", "managed dispatch selected")
    req(deferred["native_execution_dispatch"] == "DEFERRED", "native dispatch selected")
    req(deferred["qsi_coupling"] == "DEFERRED", "QSI coupling selected")

    print("P12_5_RCV_31_PROFILE=apexforge.p12.managed-executable-carrier-derivation-boundary-census/v1")
    print("P12_5_RCV_31_HISTORICAL_CANONICAL_DERIVATION_SOURCE_REFERENCE_COUNT=139")
    print("P12_5_RCV_31_HISTORICAL_PRODUCTION_PYTHON_MANAGED_CARRIER_REFERENCE_COUNT=0")
    print("P12_5_RCV_31_HISTORICAL_EXISTING_DERIVATION_BRIDGE_REFERENCE_COUNT=0")
    print("P12_5_RCV_31_HISTORICAL_EXISTING_HANDOFF_BOUNDARY_REFERENCE_COUNT=22")
    print(f"P12_5_RCV_31_CURRENT_PRODUCTION_PYTHON_MANAGED_CARRIER_REFERENCE_COUNT={len(python_refs)}")
    print(f"P12_5_RCV_31_CURRENT_MANAGED_DERIVATION_REFERENCE_COUNT={len(csharp_refs)}")
    print("P12_5_RCV_31_CANONICAL_AIR_SOURCE_SURFACE=PASS")
    print("P12_5_RCV_31_TARGET_NEUTRAL_HANDOFF_CARRIER_COUPLING=False")
    print("P12_5_RCV_31_DERIVATION_SOURCE=UNSELECTED")
    print("P12_5_RCV_31_DERIVATION_OWNER=UNSELECTED")
    print("P12_5_RCV_31_DERIVATION_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_31_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_31_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_31_MANAGED_EXECUTABLE_CARRIER_DERIVATION_BOUNDARY_CENSUS=PASS")
    print("P12_5_RCV_31_NEXT=P12.5-RCV-32_MANAGED_EXECUTABLE_CARRIER_DERIVATION_SOURCE_DECISION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
