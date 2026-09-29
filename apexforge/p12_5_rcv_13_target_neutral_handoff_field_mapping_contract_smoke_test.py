from __future__ import annotations
import ast, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_13_target_neutral_handoff_field_mapping_contract.json"
RCV12 = ROOT / "apexforge/p12_5_rcv_12_target_neutral_handoff_representation_census_smoke_test.py"
LOWERING = ROOT / "apexforge/native_backend/target_neutral_lowering.py"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"

EXPECTED_FIELDS = [
    ("Schema", "string", "schema"),
    ("VerifiedAirFingerprint", "string", "verified_air_fingerprint"),
    ("RoutingFingerprint", "string", "routing_fingerprint"),
    ("EntryDirective", "string", "entry_directive"),
    ("DirectiveOwnerIds", "IReadOnlyList<string>", "directive_owner_ids"),
    ("ProductFingerprint", "string", "product_fingerprint"),
]

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def product_shape():
    src = LOWERING.read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TargetNeutralLoweringProduct"), None)
    req(cls is not None, "TargetNeutralLoweringProduct missing")
    fields = []
    props = []
    for n in cls.body:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            fields.append(n.target.id)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(isinstance(d, ast.Name) and d.id == "property" for d in n.decorator_list):
                props.append(n.name)
    return fields, props

def main():
    print("=== P12.5-RCV-13-R1 HISTORICAL HANDOFF PROJECTION CORRECTION ===")
    req(CONTRACT.exists(), "corrected RCV-13 contract missing")
    cp = run(sys.executable, str(RCV12))
    req(cp.returncode == 0, "RCV-12 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_13_R1_RCV12_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    req(data["stage"] == "P12.5-RCV-13-R1", "correction stage changed")
    req(data["status"] == "RECOVERED_GOVERNANCE_CORRECTION", "correction status changed")
    req(data["source_product"]["schema"] == "apexforge.target-neutral-lowering/v1", "schema changed")

    fields, props = product_shape()
    req(fields == ["binding", "canonical_json", "product_fingerprint", "schema"], f"source dataclass shape changed: {fields}")
    for p in ("verified_air_fingerprint", "routing_fingerprint", "entry_directive", "directive_owner_ids"):
        req(p in props, f"derived product view missing: {p}")

    hist = data["historical_managed_handoff"]
    actual = [(x["name"], x["type"], x["source"]) for x in hist["fields"]]
    req(actual == EXPECTED_FIELDS, f"historical managed projection changed: {actual}")
    req(hist["kind"] == "public sealed record", "historical record kind changed")
    req(hist["canonical_json_in_managed_handoff"] is False, "canonical_json incorrectly promoted to managed handoff")
    req(hist["required_schema_constant"] == "apexforge.target-neutral-lowering/v1", "RequiredSchema changed")

    val = data["historical_validation"]
    req("64 hexadecimal" in val["verified_air_fingerprint"], "Verified AIR fingerprint rule missing")
    req("64 hexadecimal" in val["routing_fingerprint"], "routing fingerprint rule missing")
    req("64 uppercase hexadecimal" in val["product_fingerprint"], "product fingerprint uppercase rule missing")
    req("non-whitespace" in val["entry_directive"], "entry directive validation missing")
    req("non-null" in val["directive_owner_ids"], "owner-list validation missing")

    req(data["implementation"] == "DEFERRED", "implementation selected too early")
    req(data["admission"]["behavior"] == "VALIDATE_AND_RETURN", "admission behavior changed")
    req(data["admission"]["implementation"] == "DEFERRED", "admission implementation selected too early")
    req(data["authority"]["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(data["authority"]["handoff_defines_language_semantics"] is False, "handoff gained semantic authority")

    if HANDOFF.exists() or "AdmitTargetNeutralHandoff" in HOST.read_text(encoding="utf-8-sig"):
        req((ROOT / "apexforge/p12_5_rcv_15_target_neutral_handoff_implementation_foundation.json").exists(), "later handoff implementation lacks RCV-15 lineage")

    for name, typ, source in EXPECTED_FIELDS:
        print(f"P12_5_RCV_13_R1_FIELD={name}|TYPE={typ}|SOURCE={source}")
    print("P12_5_RCV_13_R1_CANONICAL_JSON_IN_MANAGED_HANDOFF=False")
    print("P12_5_RCV_13_R1_REQUIRED_SCHEMA=apexforge.target-neutral-lowering/v1")
    print("P12_5_RCV_13_R1_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_13_R1_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_13_R1_HISTORICAL_HANDOFF_PROJECTION_CORRECTION=PASS")
    print("P12_5_RCV_13_R1_NEXT=P12.5-RCV-14_HISTORICAL_MANAGED_TYPE_SELECTION_CONFIRMATION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
