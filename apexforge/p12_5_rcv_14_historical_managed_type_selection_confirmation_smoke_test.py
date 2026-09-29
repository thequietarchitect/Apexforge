from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_14_historical_managed_type_selection_confirmation.json"
RCV13 = ROOT / "apexforge/p12_5_rcv_13_target_neutral_handoff_field_mapping_contract_smoke_test.py"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"

EXPECTED = [
    ("Schema", "string"),
    ("VerifiedAirFingerprint", "string"),
    ("RoutingFingerprint", "string"),
    ("EntryDirective", "string"),
    ("DirectiveOwnerIds", "IReadOnlyList<string>"),
    ("ProductFingerprint", "string"),
]

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-14 HISTORICAL MANAGED TYPE SELECTION CONFIRMATION ===")
    req(CONTRACT.exists(), "RCV-14 contract missing")
    req(RCV13.exists(), "RCV-13-R1 smoke missing")

    cp = run(sys.executable, str(RCV13))
    req(cp.returncode == 0, "RCV-13-R1 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_14_RCV13_R1_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    req(data["profile"] == "apexforge.p12.historical-managed-type-selection-confirmation/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-13-R1", "predecessor changed")

    mt = data["managed_type"]
    req(mt["name"] == "ApexForge.Runtime.TargetNeutralLoweringHandoff", "managed type changed")
    req(mt["declaration"] == "public sealed record", "managed declaration changed")
    req(mt["owner_project"] == "ApexForge.Runtime", "owner project changed")
    req(mt["required_schema_constant"] == "apexforge.target-neutral-lowering/v1", "schema constant changed")
    actual = [(x["name"], x["type"]) for x in mt["fields"]]
    req(actual == EXPECTED, f"managed field types changed: {actual}")

    val = data["validation"]
    req("Ordinal" in val["Schema"], "schema comparison policy changed")
    req("64 hex chars" in val["VerifiedAirFingerprint"], "Verified AIR fingerprint rule changed")
    req("64 hex chars" in val["RoutingFingerprint"], "routing fingerprint rule changed")
    req("64 uppercase hex chars" in val["ProductFingerprint"], "product fingerprint rule changed")
    req("non-whitespace" in val["EntryDirective"], "entry directive rule changed")
    req("every item non-null/non-whitespace" in val["DirectiveOwnerIds"], "owner-id validation changed")

    adm = data["admission"]
    req(adm["host_type"] == "ApexForge.Runtime.ManagedRuntimeHost", "host type changed")
    req(adm["method"] == "AdmitTargetNeutralHandoff", "admission method changed")
    req(adm["behavior"] == "VALIDATE_AND_RETURN", "admission behavior changed")
    req(adm["implementation"] == "DEFERRED", "admission implementation selected too early")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["handoff_defines_language_semantics"] is False, "handoff gained semantic authority")
    req(auth["handoff_executes"] is False, "handoff gained execution authority")
    req(auth["handoff_lowers"] is False, "handoff gained lowering authority")
    req(auth["handoff_serializes"] is False, "handoff gained serialization authority")

    req(data["implementation"] == "DEFERRED", "implementation selected too early")
    if HANDOFF.exists() or "AdmitTargetNeutralHandoff" in HOST.read_text(encoding="utf-8-sig"):
        req((ROOT / "apexforge/p12_5_rcv_15_target_neutral_handoff_implementation_foundation.json").exists(), "later handoff implementation lacks RCV-15 lineage")

    for name, typ in EXPECTED:
        print(f"P12_5_RCV_14_FIELD={name}|TYPE={typ}")
    print("P12_5_RCV_14_DECLARATION=public sealed record")
    print("P12_5_RCV_14_REQUIRED_SCHEMA=apexforge.target-neutral-lowering/v1")
    print("P12_5_RCV_14_ADMISSION=VALIDATE_AND_RETURN")
    print("P12_5_RCV_14_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_14_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_14_HISTORICAL_MANAGED_TYPE_SELECTION_CONFIRMATION=PASS")
    print("P12_5_RCV_14_NEXT=P12.5-RCV-15_TARGET_NEUTRAL_HANDOFF_IMPLEMENTATION_FOUNDATION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
