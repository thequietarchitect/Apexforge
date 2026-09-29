from __future__ import annotations
import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_12_target_neutral_handoff_representation_census.json"
RCV11 = ROOT / "apexforge/p12_5_rcv_11_target_neutral_managed_handoff_reconstruction_contract_smoke_test.py"
LOWERING = ROOT / "apexforge/native_backend/target_neutral_lowering.py"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
MANAGED_HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def class_info(path: Path, class_name: str):
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    node = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name), None)
    req(node is not None, f"{class_name} class missing")
    decorators = []
    for d in node.decorator_list:
        try:
            decorators.append(ast.unparse(d))
        except Exception:
            decorators.append(type(d).__name__)
    annotated = []
    assigned = []
    methods = []
    init_args = []
    for n in node.body:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            annotated.append(n.target.id)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    assigned.append(t.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(n.name)
            if n.name == "__init__":
                init_args = [a.arg for a in n.args.args if a.arg != "self"]
    return {
        "decorators": decorators,
        "annotated_fields": annotated,
        "assigned_fields": assigned,
        "methods": methods,
        "init_args": init_args,
        "source": src,
    }

def grep_count(term: str) -> int:
    cp = run("git", "grep", "-n", "-F", term, "--", ".")
    if cp.returncode not in (0, 1):
        raise AssertionError(f"git grep failed for {term}: {cp.stderr}")
    if cp.returncode == 1 or not cp.stdout.strip():
        return 0
    return len(cp.stdout.splitlines())

def main():
    print("=== P12.5-RCV-12 TARGET-NEUTRAL HANDOFF REPRESENTATION CENSUS ===")
    req(CONTRACT.exists(), "RCV-12 contract missing")
    req(RCV11.exists(), "RCV-11 smoke missing")
    req(LOWERING.exists(), "P12.2 target-neutral lowering missing")
    req(MANAGED_HOST.exists(), "ManagedRuntimeHost missing")

    cp = run(sys.executable, str(RCV11))
    req(cp.returncode == 0, "RCV-11 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_12_RCV11_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    req(data["profile"] == "apexforge.p12.target-neutral-handoff-representation-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-11", "predecessor changed")
    req(data["canonical_source"]["schema"] == "apexforge.target-neutral-lowering/v1", "schema changed")
    req(data["canonical_source"]["type"] == "TargetNeutralLoweringProduct", "canonical product type changed")
    req(data["managed_target"]["type"] == "ApexForge.Runtime.TargetNeutralLoweringHandoff", "managed target changed")
    req(data["managed_target"]["field_mapping"] == "UNSELECTED", "managed mapping selected too early")
    req(data["managed_target"]["implementation"] == "ABSENT_AT_CENSUS_GATE", "implementation state changed")

    info = class_info(LOWERING, "TargetNeutralLoweringProduct")
    req("apexforge.target-neutral-lowering/v1" in info["source"], "P12.2 lowering schema missing from source")

    # At least one observable representation mechanism must exist.
    observable = list(dict.fromkeys(info["annotated_fields"] + info["assigned_fields"] + info["init_args"]))
    req(bool(observable) or bool(info["methods"]), "TargetNeutralLoweringProduct has no observable representation surface")

    print("P12_5_RCV_12_PYTHON_DECORATORS=" + (",".join(info["decorators"]) if info["decorators"] else "NONE"))
    print("P12_5_RCV_12_PYTHON_ANNOTATED_FIELDS=" + (",".join(info["annotated_fields"]) if info["annotated_fields"] else "NONE"))
    print("P12_5_RCV_12_PYTHON_ASSIGNED_FIELDS=" + (",".join(info["assigned_fields"]) if info["assigned_fields"] else "NONE"))
    print("P12_5_RCV_12_PYTHON_INIT_ARGS=" + (",".join(info["init_args"]) if info["init_args"] else "NONE"))
    print("P12_5_RCV_12_PYTHON_METHODS=" + (",".join(info["methods"]) if info["methods"] else "NONE"))

    product_refs = grep_count("TargetNeutralLoweringProduct")
    handoff_refs = grep_count("TargetNeutralLoweringHandoff")
    schema_refs = grep_count("apexforge.target-neutral-lowering/v1")
    print(f"P12_5_RCV_12_PRODUCT_REFERENCE_COUNT={product_refs}")
    print(f"P12_5_RCV_12_HANDOFF_REFERENCE_COUNT={handoff_refs}")
    print(f"P12_5_RCV_12_SCHEMA_REFERENCE_COUNT={schema_refs}")

    req(product_refs > 0, "no repository references to TargetNeutralLoweringProduct")
    req(schema_refs > 0, "no repository references to target-neutral schema")

    # The census remains audit-only; accept only the later RCV-15 implementation.
    host_text = MANAGED_HOST.read_text(encoding="utf-8")
    if HANDOFF.exists() or "AdmitTargetNeutralHandoff" in host_text:
        req((ROOT / "apexforge/p12_5_rcv_15_target_neutral_handoff_implementation_foundation.json").exists(), "later handoff implementation lacks RCV-15 lineage")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["host_defines_language_semantics"] is False, "host gained semantic authority")
    req(auth["handoff_defines_language_semantics"] is False, "handoff gained semantic authority")
    req(auth["handoff_executes"] is False, "handoff gained execution authority")
    req(auth["handoff_lowers"] is False, "handoff gained lowering authority")

    print("P12_5_RCV_12_PROFILE=apexforge.p12.target-neutral-handoff-representation-census/v1")
    print("P12_5_RCV_12_SOURCE_TYPE=TargetNeutralLoweringProduct")
    print("P12_5_RCV_12_MANAGED_TARGET=ApexForge.Runtime.TargetNeutralLoweringHandoff")
    print("P12_5_RCV_12_FIELD_MAPPING=UNSELECTED")
    print("P12_5_RCV_12_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_12_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_12_TARGET_NEUTRAL_HANDOFF_REPRESENTATION_CENSUS=PASS")
    print("P12_5_RCV_12_NEXT=P12.5-RCV-13_TARGET_NEUTRAL_HANDOFF_FIELD_MAPPING_CONTRACT")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
