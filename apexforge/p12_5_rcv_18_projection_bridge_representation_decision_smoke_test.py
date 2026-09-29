from __future__ import annotations
import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_18_projection_bridge_representation_decision.json"
RCV17 = ROOT / "apexforge/p12_5_rcv_17_projection_bridge_ownership_contract_smoke_test.py"
LOWERING = ROOT / "apexforge/native_backend/target_neutral_lowering.py"
FUTURE_IMPL = ROOT / "apexforge/native_backend/managed_handoff_projection.py"

EXPECTED = [
    ("schema", "str", "Schema"),
    ("verified_air_fingerprint", "str", "VerifiedAirFingerprint"),
    ("routing_fingerprint", "str", "RoutingFingerprint"),
    ("entry_directive", "str", "EntryDirective"),
    ("directive_owner_ids", "tuple[str, ...]", "DirectiveOwnerIds"),
    ("product_fingerprint", "str", "ProductFingerprint"),
]

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def product_surface():
    src = LOWERING.read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TargetNeutralLoweringProduct"), None)
    req(cls is not None, "TargetNeutralLoweringProduct missing")
    fields = []
    props = []
    for n in cls.body:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            fields.append(n.target.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(isinstance(d, ast.Name) and d.id == "property" for d in n.decorator_list):
                props.append(n.name)
    return fields, props

def main():
    print("=== P12.5-RCV-18 PROJECTION BRIDGE REPRESENTATION DECISION ===")
    req(CONTRACT.exists(), "RCV-18 contract missing")
    req(RCV17.exists(), "RCV-17 smoke missing")
    req(LOWERING.exists(), "canonical lowering product missing")

    cp = run(sys.executable, str(RCV17))
    req(cp.returncode == 0, "RCV-17 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_18_RCV17_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.projection-bridge-representation-decision/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-17", "predecessor changed")

    hist = data["historical_evidence"]
    req(hist["concrete_bridge_representation_recovered"] is False, "unsupported historical bridge claim introduced")
    req(hist["concrete_external_serialization_recovered"] is False, "unsupported serialization history claim introduced")
    req(hist["original_commit_identity_equivalence_claim"] is False, "commit identity equivalence improperly claimed")

    d = data["decision"]
    req(d["representation_scope"] == "SOURCE_SIDE_INTERNAL_ONLY", "representation scope changed")
    req(d["representation_kind"] == "FROZEN_DATACLASS_VALUE_OBJECT", "representation kind changed")
    req(d["future_type"] == "apexforge.native_backend.managed_handoff_projection.ManagedHandoffProjection", "future type changed")
    req(d["owner"] == "apexforge.native_backend", "representation owner changed")
    req(d["historical_identity_claim"] is False, "historical identity claim introduced")
    req(d["semantic_authority"] is False, "projection gained semantic authority")
    req(d["execution_authority"] is False, "projection gained execution authority")
    req(d["transport_authority"] is False, "projection gained transport authority")

    actual = [(x["name"], x["type"], x["managed_target"]) for x in data["fields"]]
    req(actual == EXPECTED, f"projection value-object fields changed: {actual}")

    fields, props = product_surface()
    req(fields == ["binding", "canonical_json", "product_fingerprint", "schema"], f"source product fields changed: {fields}")
    for p in ("verified_air_fingerprint", "routing_fingerprint", "entry_directive", "directive_owner_ids"):
        req(p in props, f"source derived view missing: {p}")

    construction = data["construction"]
    req(construction["source"] == "TargetNeutralLoweringProduct", "projection source changed")
    req(construction["mapping"] == "DIRECT_COPY_FROM_CANONICAL_PRODUCT_AND_DERIVED_VIEWS", "mapping policy changed")
    req(construction["canonical_json_projected"] is False, "canonical_json entered projection")
    req(construction["binding_object_projected"] is False, "binding object entered projection")
    req(construction["implementation"] == "DEFERRED", "implementation selected too early")

    val = data["validation"]
    req(val["performed_by_projection_value_object"] is False, "projection value object gained duplicate validation")
    req(val["managed_validation_remains_authoritative_for_handoff_shape"] is True, "managed validation ownership weakened")
    req(val["source_product_invariants_remain_authoritative_upstream"] is True, "source invariants ownership weakened")

    for key, value in data["unselected"].items():
        req(value == "UNSELECTED", f"{key} selected too early")

    if FUTURE_IMPL.exists():
        req((ROOT / "apexforge/p12_5_rcv_19_projection_value_object_implementation_foundation.json").exists(), "later projection implementation lacks RCV-19 lineage")

    print("P12_5_RCV_18_PROFILE=apexforge.p12.projection-bridge-representation-decision/v1")
    print("P12_5_RCV_18_REPRESENTATION=FROZEN_DATACLASS_VALUE_OBJECT")
    print("P12_5_RCV_18_OWNER=apexforge.native_backend")
    print("P12_5_RCV_18_HISTORICAL_IDENTITY_CLAIM=False")
    print("P12_5_RCV_18_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_18_CROSS_RUNTIME_TRANSPORT=UNSELECTED")
    print("P12_5_RCV_18_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_18_PROJECTION_BRIDGE_REPRESENTATION_DECISION=PASS")
    print("P12_5_RCV_18_NEXT=P12.5-RCV-19_PROJECTION_VALUE_OBJECT_IMPLEMENTATION_FOUNDATION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
