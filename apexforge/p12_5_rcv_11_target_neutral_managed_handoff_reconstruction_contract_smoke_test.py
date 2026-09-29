from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_11_target_neutral_managed_handoff_reconstruction_contract.json"
RCV10 = ROOT / "apexforge/p12_5_rcv_10_host_ingress_contract_decision_smoke_test.py"
LOWERING = ROOT / "apexforge/native_backend/target_neutral_lowering.py"
MANAGED_HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-11 TARGET-NEUTRAL MANAGED HANDOFF RECONSTRUCTION CONTRACT ===")
    req(CONTRACT.exists(), "RCV-11 contract missing")
    req(RCV10.exists(), "RCV-10 smoke missing")

    cp = run(sys.executable, str(RCV10))
    req(cp.returncode == 0, "RCV-10 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_11_RCV10_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    req(data["profile"] == "apexforge.p12.target-neutral-managed-handoff-reconstruction-contract/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-10", "predecessor changed")

    r = data["reconstruction"]
    req(r["subject"] == "TARGET_NEUTRAL_LOWERING_PRODUCT", "handoff subject changed")
    req(r["managed_type"] == "ApexForge.Runtime.TargetNeutralLoweringHandoff", "managed handoff type changed")
    req(r["source_schema"] == "apexforge.target-neutral-lowering/v1", "source schema changed")
    req(r["owner_project"] == "ApexForge.Runtime", "handoff owner changed")
    req(r["host_admission_method"] == "ManagedRuntimeHost.AdmitTargetNeutralHandoff", "admission method changed")
    req(r["host_admission_behavior"] == "VALIDATE_AND_RETURN", "admission behavior changed")
    req(r["language_semantic_authority"] is False, "handoff gained language semantic authority")
    req(r["execution_authority"] is False, "handoff gained execution authority")
    req(r["lowering_authority"] is False, "handoff gained lowering authority")

    a = data["authority"]
    req(a["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(a["verified_air_owner"] == "air.model.VerifiedAIRProgram", "Verified AIR owner changed")
    req(a["execution_plan_owner"] == "workflow.air_runner.RegistryExecutionPlan", "execution plan owner changed")

    rep = data["representation"]
    for key in ("field_mapping", "external_serialization", "file_format", "stdin_format", "command_line_format"):
        req(rep[key] == "UNSELECTED", f"{key} selected too early")

    c = data["constraints"]
    for key in (
        "must_preserve_p12_2_schema",
        "must_not_redefine_language_semantics",
        "must_not_execute_on_admission",
        "must_not_call_native_abi_on_admission",
        "must_not_infer_executable_semantics_from_fingerprint",
        "must_validate_before_return",
    ):
        req(c[key] is True, f"constraint weakened: {key}")

    req(LOWERING.exists(), "P12.2 target-neutral lowering missing")
    lower = LOWERING.read_text(encoding="utf-8")
    req("apexforge.target-neutral-lowering/v1" in lower, "P12.2 schema missing")
    req("TargetNeutralLoweringProduct" in lower, "P12.2 lowering product missing")

    req(MANAGED_HOST.exists(), "ManagedRuntimeHost missing")
    host_text = MANAGED_HOST.read_text(encoding="utf-8")
    # RCV-11 was governance-only. A later implementation is valid only with
    # the authorizing RCV-15 lineage artifact.
    if "AdmitTargetNeutralHandoff" in host_text or HANDOFF.exists():
        req((ROOT / "apexforge/p12_5_rcv_15_target_neutral_handoff_implementation_foundation.json").exists(), "later handoff implementation lacks RCV-15 lineage")

    print("P12_5_RCV_11_PROFILE=apexforge.p12.target-neutral-managed-handoff-reconstruction-contract/v1")
    print("P12_5_RCV_11_HANDOFF_SUBJECT=TARGET_NEUTRAL_LOWERING_PRODUCT")
    print("P12_5_RCV_11_MANAGED_TYPE=ApexForge.Runtime.TargetNeutralLoweringHandoff")
    print("P12_5_RCV_11_SOURCE_SCHEMA=apexforge.target-neutral-lowering/v1")
    print("P12_5_RCV_11_ADMISSION_BEHAVIOR=VALIDATE_AND_RETURN")
    print("P12_5_RCV_11_FIELD_MAPPING=UNSELECTED")
    print("P12_5_RCV_11_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_11_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_11_TARGET_NEUTRAL_MANAGED_HANDOFF_RECONSTRUCTION_CONTRACT=PASS")
    print("P12_5_RCV_11_NEXT=P12.5-RCV-12_TARGET_NEUTRAL_HANDOFF_REPRESENTATION_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
