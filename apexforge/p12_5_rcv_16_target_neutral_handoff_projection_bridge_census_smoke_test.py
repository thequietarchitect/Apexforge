from __future__ import annotations
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_16_target_neutral_handoff_projection_bridge_census.json"
RCV15 = ROOT / "apexforge/p12_5_rcv_15_target_neutral_handoff_implementation_foundation_smoke_test.py"
LOWERING = ROOT / "apexforge/native_backend/target_neutral_lowering.py"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def parse_product():
    src = LOWERING.read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TargetNeutralLoweringProduct"), None)
    req(cls is not None, "TargetNeutralLoweringProduct missing")
    fields = []
    properties = []
    for n in cls.body:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            fields.append(n.target.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(isinstance(d, ast.Name) and d.id == "property" for d in n.decorator_list):
                properties.append(n.name)
    return fields, properties, src

def parse_managed_fields():
    src = HANDOFF.read_text(encoding="utf-8-sig")
    m = re.search(r"public sealed record TargetNeutralLoweringHandoff\((.*?)\)\s*\{", src, re.S)
    req(m is not None, "managed handoff record declaration missing")
    block = m.group(1)
    fields = []
    for raw in block.splitlines():
        line = raw.strip().rstrip(",")
        if not line:
            continue
        mm = re.match(r"(.+?)\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        req(mm is not None, f"unable to parse managed field declaration: {line}")
        fields.append((mm.group(2), mm.group(1)))
    return fields, src

def main():
    print("=== P12.5-RCV-16 TARGET-NEUTRAL HANDOFF PROJECTION BRIDGE CENSUS ===")
    for p in (CONTRACT, RCV15, LOWERING, HANDOFF):
        req(p.exists(), f"missing required file: {p}")

    cp = run(sys.executable, str(RCV15))
    req(cp.returncode == 0, "RCV-15 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_16_RCV15_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.target-neutral-handoff-projection-bridge-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-15", "predecessor changed")
    req(data["source_product"]["schema"] == "apexforge.target-neutral-lowering/v1", "schema changed")

    fields, props, source = parse_product()
    req(fields == ["binding", "canonical_json", "product_fingerprint", "schema"], f"source product fields changed: {fields}")
    for p in ("verified_air_fingerprint", "routing_fingerprint", "entry_directive", "directive_owner_ids"):
        req(p in props, f"derived source property missing: {p}")

    managed_fields, handoff_source = parse_managed_fields()
    expected_managed = [
        ("Schema", "string"),
        ("VerifiedAirFingerprint", "string"),
        ("RoutingFingerprint", "string"),
        ("EntryDirective", "string"),
        ("DirectiveOwnerIds", "IReadOnlyList<string>"),
        ("ProductFingerprint", "string"),
    ]
    req(managed_fields == expected_managed, f"managed handoff shape changed: {managed_fields}")

    expected_projection = [
        ("Schema", "product.schema"),
        ("VerifiedAirFingerprint", "product.verified_air_fingerprint"),
        ("RoutingFingerprint", "product.routing_fingerprint"),
        ("EntryDirective", "product.entry_directive"),
        ("DirectiveOwnerIds", "product.directive_owner_ids"),
        ("ProductFingerprint", "product.product_fingerprint"),
    ]
    actual_projection = [(x["managed_field"], x["source_expression"]) for x in data["projection"]]
    req(actual_projection == expected_projection, f"projection changed: {actual_projection}")

    exclusions = data["exclusions"]
    req(exclusions["canonical_json"] == "NOT_PROJECTED_TO_HISTORICAL_MANAGED_HANDOFF", "canonical_json projection policy changed")
    req(exclusions["binding_object"] == "NOT_PROJECTED_AS_OBJECT", "binding object projection policy changed")
    req(exclusions["execution_plan_object"] == "NOT_PROJECTED_AS_OBJECT", "execution plan object projection policy changed")
    req(exclusions["verified_air_program_object"] == "NOT_PROJECTED_AS_OBJECT", "verified AIR object projection policy changed")

    bridge = data["bridge"]
    req(bridge["implementation"] == "ABSENT_AT_CENSUS_GATE", "bridge implementation selected too early")
    req(bridge["owner"] == "UNSELECTED", "bridge owner selected too early")
    req(bridge["semantic_authority"] is False, "bridge gained semantic authority")
    req(bridge["execution_authority"] is False, "bridge gained execution authority")

    # Accept the later projection only when its RCV-19 authority is present.
    candidates = [
        ROOT / "apexforge/native_backend/managed_handoff_projection.py",
        ROOT / "apexforge/native_backend/target_neutral_handoff_projection.py",
        ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoffProjection.cs",
    ]
    for p in candidates:
        if p.exists():
            req(p.name == "managed_handoff_projection.py" and (ROOT / "apexforge/p12_5_rcv_19_projection_value_object_implementation_foundation.json").exists(), f"projection implementation lacks RCV-19 lineage: {p}")

    print("P12_5_RCV_16_PROFILE=apexforge.p12.target-neutral-handoff-projection-bridge-census/v1")
    for field, source_expr in expected_projection:
        print(f"P12_5_RCV_16_PROJECTION={field}<-{source_expr}")
    print("P12_5_RCV_16_CANONICAL_JSON_PROJECTED=False")
    print("P12_5_RCV_16_BINDING_OBJECT_PROJECTED=False")
    print("P12_5_RCV_16_BRIDGE_OWNER=UNSELECTED")
    print("P12_5_RCV_16_BRIDGE_IMPLEMENTATION=ABSENT")
    print("P12_5_RCV_16_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_16_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_16_TARGET_NEUTRAL_HANDOFF_PROJECTION_BRIDGE_CENSUS=PASS")
    print("P12_5_RCV_16_NEXT=P12.5-RCV-17_PROJECTION_BRIDGE_OWNERSHIP_CONTRACT")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
