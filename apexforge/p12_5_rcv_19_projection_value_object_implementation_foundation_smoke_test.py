from __future__ import annotations

import ast
import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_19_projection_value_object_implementation_foundation.json"
RCV18_CONTRACT = ROOT / "apexforge/p12_5_rcv_18_projection_bridge_representation_decision.json"
IMPL = ROOT / "apexforge/native_backend/managed_handoff_projection.py"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"

EXPECTED_FIELDS = [
    ("schema", "str"),
    ("verified_air_fingerprint", "str"),
    ("routing_fingerprint", "str"),
    ("entry_directive", "str"),
    ("directive_owner_ids", "tuple[str, ...]"),
    ("product_fingerprint", "str"),
]

def req(c, m):
    if not c:
        raise AssertionError(m)

def main():
    print("=== P12.5-RCV-19 PROJECTION VALUE-OBJECT IMPLEMENTATION FOUNDATION ===")

    for p in (CONTRACT, RCV18_CONTRACT, IMPL, HANDOFF):
        req(p.exists(), f"missing required file: {p}")

    prev = json.loads(RCV18_CONTRACT.read_text(encoding="utf-8-sig"))
    req(prev["profile"] == "apexforge.p12.projection-bridge-representation-decision/v1", "RCV-18 profile changed")
    req(prev["stage"] == "P12.5-RCV-18", "RCV-18 stage changed")
    req(prev["decision"]["representation_kind"] == "FROZEN_DATACLASS_VALUE_OBJECT", "RCV-18 representation changed")
    req(prev["decision"]["owner"] == "apexforge.native_backend", "RCV-18 owner changed")
    print("P12_5_RCV_19_RCV18_CONTRACT=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.projection-value-object-implementation-foundation/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-18", "predecessor changed")
    req(data["implementation"]["kind"] == "frozen dataclass", "implementation kind changed")
    req(data["implementation"]["owner"] == "apexforge.native_backend", "implementation owner changed")
    req(data["implementation"]["historical_identity_claim"] is False, "historical identity claim introduced")

    src = IMPL.read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ManagedHandoffProjection"), None)
    req(cls is not None, "ManagedHandoffProjection missing")

    decorators = []
    fields = []
    for d in cls.decorator_list:
        try:
            decorators.append(ast.unparse(d))
        except Exception:
            pass
    for n in cls.body:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            try:
                ann = ast.unparse(n.annotation)
            except Exception:
                ann = "<unparsed>"
            fields.append((n.target.id, ann))

    req(any(x.startswith("dataclass") and "frozen=True" in x.replace(" ", "") for x in decorators), "projection is not a frozen dataclass")
    req(fields == EXPECTED_FIELDS, f"projection field shape changed: {fields}")

    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "project_managed_handoff"), None)
    req(fn is not None, "project_managed_handoff missing")

    for forbidden in (
        "json.dumps",
        "json.loads",
        "Path(",
        "open(",
        "subprocess",
        "socket",
        "requests",
        "ManagedExecutableCarrier",
    ):
        req(forbidden not in src, f"premature projection behavior found: {forbidden}")

    sys.path.insert(0, str(ROOT))
    try:
        module = importlib.import_module("apexforge.native_backend.managed_handoff_projection")
        lowering = importlib.import_module("apexforge.native_backend.target_neutral_lowering")

        lower_fp = "a" * 64
        routing_fp = "b" * 64
        product_fp = "C" * 64
        binding = SimpleNamespace(
            lowering_input=SimpleNamespace(transport_fingerprint=lower_fp),
            routing_fingerprint=routing_fp,
            entry_directive="entry-main",
            directive_owner_ids=("owner-a", "owner-b"),
        )
        product = lowering.TargetNeutralLoweringProduct(
            binding=binding,
            canonical_json='{"not":"projected"}',
            product_fingerprint=product_fp,
            schema="apexforge.target-neutral-lowering/v1",
        )

        projection = module.project_managed_handoff(product)
        req(projection.schema == product.schema, "schema projection mismatch")
        req(projection.verified_air_fingerprint == product.verified_air_fingerprint, "Verified AIR fingerprint mismatch")
        req(projection.routing_fingerprint == product.routing_fingerprint, "routing fingerprint mismatch")
        req(projection.entry_directive == product.entry_directive, "entry directive mismatch")
        req(projection.directive_owner_ids == tuple(product.directive_owner_ids), "owner ids mismatch")
        req(projection.product_fingerprint == product.product_fingerprint, "product fingerprint mismatch")
        req(not hasattr(projection, "canonical_json"), "canonical_json leaked into projection")
        req(not hasattr(projection, "binding"), "binding object leaked into projection")

        try:
            projection.schema = "changed"
            raise AssertionError("frozen projection accepted mutation")
        except Exception as exc:
            req(type(exc).__name__ in ("FrozenInstanceError", "AttributeError"), f"unexpected freeze failure type: {type(exc).__name__}")

        try:
            module.project_managed_handoff(object())
            raise AssertionError("non-product projection input was accepted")
        except TypeError:
            pass
    finally:
        try:
            sys.path.remove(str(ROOT))
        except ValueError:
            pass

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    for key in (
        "projection_defines_language_semantics",
        "projection_executes",
        "projection_lowers",
        "projection_serializes",
        "projection_selects_transport",
    ):
        req(auth[key] is False, f"projection boundary weakened: {key}")

    for key, value in data["unselected"].items():
        req(value == "UNSELECTED", f"{key} selected too early")

    print("P12_5_RCV_19_PROFILE=apexforge.p12.projection-value-object-implementation-foundation/v1")
    print("P12_5_RCV_19_TYPE=ManagedHandoffProjection")
    print("P12_5_RCV_19_KIND=FROZEN_DATACLASS_VALUE_OBJECT")
    print("P12_5_RCV_19_DIRECT_PROJECTION=PASS")
    print("P12_5_RCV_19_IMMUTABILITY=PASS")
    print("P12_5_RCV_19_CANONICAL_JSON_PROJECTED=False")
    print("P12_5_RCV_19_BINDING_OBJECT_PROJECTED=False")
    print("P12_5_RCV_19_HISTORICAL_IDENTITY_CLAIM=False")
    print("P12_5_RCV_19_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_19_CROSS_RUNTIME_TRANSPORT=UNSELECTED")
    print("P12_5_RCV_19_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_19_PROJECTION_VALUE_OBJECT_IMPLEMENTATION_FOUNDATION=PASS")
    print("P12_5_RCV_19_NEXT=P12.5-RCV-20_PROJECTION_VALUE_OBJECT_COMPATIBILITY_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
