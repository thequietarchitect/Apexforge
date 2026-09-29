from __future__ import annotations

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge" / "p12_5_rcv_5_runtime_host_topology_ownership.json"
DOC = ROOT / "apexforge" / "p12_5_rcv_5_runtime_host_topology_ownership.md"
BASE_HOST = ROOT / "runtimes" / "dotnet" / "ApexForge.Runtime" / "ManagedRuntimeHost.cs"
BASE_PROJECT = ROOT / "runtimes" / "dotnet" / "ApexForge.Runtime" / "ApexForge.Runtime.csproj"
DEDICATED_HOST_DIR = ROOT / "runtimes" / "dotnet" / "ApexForge.Runtime.Host"

data = json.loads(CONTRACT.read_text(encoding="utf-8"))
doc = DOC.read_text(encoding="utf-8")

assert data["profile"] == "apexforge.p12.runtime-host-topology-ownership/v1"
assert data["stage"] == "P12.5-RCV-5"
assert data["status"] == "RECOVERED_GOVERNANCE_CANDIDATE"
assert data["recovery"]["lineage"] == "RECOVERED_AUDITED_LINEAGE"
assert data["recovery"]["provenance_commit"] == "c0bf25556f25eb655cd3692e4859304e09bc7872"
assert data["recovery"]["base_commit"] == "13f7646f1052746f54f906076d66d29117ee2718"
assert data["recovery"]["original_commit_identity_equivalence_claim"] is False

foundation = data["existing_foundation"]
assert foundation["managed_runtime_library"] == "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"
assert foundation["managed_runtime_host_type"] == "ApexForge.Runtime.ManagedRuntimeHost"
assert foundation["preserve_existing_managed_runtime_host"] is True
assert foundation["managed_runtime_host_role"] == "CANONICAL_CONTRACT_ADMISSION_AND_VALIDATION"
assert foundation["managed_runtime_host_defines_language_semantics"] is False

host = data["dedicated_host"]
assert host["project"] == "ApexForge.Runtime.Host"
assert host["path"] == "runtimes/dotnet/ApexForge.Runtime.Host"
assert host["target_framework"] == "net10.0"
assert host["output_type"] == "Exe"
assert host["references"] == ["../ApexForge.Runtime/ApexForge.Runtime.csproj"]
assert host["role"] == "ORCHESTRATION_AND_LIFECYCLE_SHELL"
assert host["defines_language_semantics"] is False
assert host["duplicates_native_interop"] is False

authority = data["authority"]
assert authority["language_semantics"] == "CANONICAL_AIR"
assert authority["managed_runtime_library"] == "ApexForge.Runtime"
assert authority["managed_host_shell"] == "ApexForge.Runtime.Host"
assert authority["native_interop_owner"] == "ApexForge.Runtime.ManagedNativeAbi"

boundaries = data["boundaries"]
assert boundaries["target_neutral_handoff"] == "NOT_YET_RECONSTRUCTED"
assert boundaries["managed_executable_carrier"] == "NOT_YET_RECONSTRUCTED"
assert boundaries["host_ingress"] == "UNSELECTED"
assert boundaries["external_serialization"] == "UNSELECTED"
assert boundaries["native_host"] == "DEFERRED"
assert boundaries["execution_dispatch"] == "DEFERRED"

permissions = data["permissions"]
assert permissions["allow_replace_existing_managed_runtime_host"] is False
assert permissions["allow_promote_p12_2_transport_to_semantic_authority"] is False
assert permissions["allow_derive_executable_semantics_from_fingerprints"] is False
assert permissions["allow_duplicate_managed_native_abi_in_host_project"] is False

assert BASE_HOST.is_file()
assert BASE_PROJECT.is_file()
if DEDICATED_HOST_DIR.exists():
    assert (ROOT / "apexforge/p12_5_rcv_6_managed_host_project_skeleton.json").is_file()

base_host_text = BASE_HOST.read_text(encoding="utf-8")
assert "public sealed class ManagedRuntimeHost" in base_host_text
assert "Admit(CanonicalExecutionEnvelope envelope)" in base_host_text

required_doc = (
    "preserved unchanged from the verified P12.4 base",
    "does not define ApexForge language semantics",
    "The dedicated host is additive",
    "Canonical AIR remains the language-semantic authority",
    "Host ingress remains unselected",
    "The P12.2 transport must not be promoted into semantic authority",
    "P12.5-RCV-6 DEDICATED MANAGED HOST PROJECT SKELETON",
)
for token in required_doc:
    assert token in doc

def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()

subprocess.run(["git", "merge-base", "--is-ancestor", "c0bf25556f25eb655cd3692e4859304e09bc7872", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True)
assert git("rev-parse", "afp-p12.4-freeze^{}") == "13f7646f1052746f54f906076d66d29117ee2718"

print("P12_5_RCV_5_PROFILE=apexforge.p12.runtime-host-topology-ownership/v1")
print("P12_5_RCV_5_EXISTING_MANAGED_RUNTIME_HOST=PRESERVE")
print("P12_5_RCV_5_DEDICATED_HOST_PROJECT=ApexForge.Runtime.Host")
print("P12_5_RCV_5_DEDICATED_HOST_ROLE=ORCHESTRATION_AND_LIFECYCLE_SHELL")
print("P12_5_RCV_5_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
print("P12_5_RCV_5_HOST_INGRESS=UNSELECTED")
print("P12_5_RCV_5_RUNTIME_HOST_TOPOLOGY_OWNERSHIP=PASS")
