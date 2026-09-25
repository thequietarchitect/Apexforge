from __future__ import annotations

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge" / "p12_5_rcv_2_recovered_lineage_provenance.json"
DOC = ROOT / "apexforge" / "p12_5_rcv_2_recovered_lineage_provenance.md"
P12_4_SMOKE = ROOT / "apexforge" / "p12_4h_artifact_object_emission_terminal_closure_smoke_test.py"

data = json.loads(CONTRACT.read_text(encoding="utf-8"))
doc = DOC.read_text(encoding="utf-8")

assert data["profile"] == "apexforge.p12.recovered-lineage-provenance/v1"
assert data["stage"] == "P12.5-RCV-2"
assert data["status"] == "RECOVERY_PROVENANCE_ESTABLISHED"

recovery = data["recovery"]
assert recovery["branch"] == "p12-native-backend-recovered"
assert recovery["classification"] == "RECOVERED_AUDITED_LINEAGE"
assert recovery["base_commit"] == "13f7646f1052746f54f906076d66d29117ee2718"
assert recovery["base_freeze_tag"] == "afp-p12.4-freeze"
assert recovery["base_freeze_tag_object"] == "7c475986ed3ed1d58cc30148603fbfe8b09529ee"
assert recovery["base_state"] == "COMPLETE_FROZEN_PUBLISHED"

original = data["unavailable_original_continuation"]
assert original["commit"] == "b7d5b1c1355c648f52f7293b675a9862f5655a98"
assert original["known_stage"] == "P12.5E-E-P"
assert original["known_state"] == "CLOSED_PASS_COMMITTED"
assert original["availability_at_recovery"] == "UNAVAILABLE_ON_DELL_AND_REMOTE"
assert original["commit_identity_equivalence_claim"] is False

policy = data["policy"]
assert policy["reconstruct_original_commit_ids"] is False
assert policy["reuse_original_branch_name"] is False
assert policy["rebuild_from_verified_freeze"] is True
assert policy["revalidate_each_recovered_stage"] is True
assert policy["preserve_original_history_as_historical_evidence"] is True
assert policy["recovered_commits_are_new_identities"] is True

artifacts = data["known_original_p_artifacts"]
assert artifacts["managed_executable_carrier_sha256"] == "93A12A19AD7AF2EE4A8165A13C0B72E5005E09EEA022F856EFB8B52ECBE97157"
assert artifacts["carrier_smoke_sha256"] == "09B4C737BD9C77AA335C06BA450285EF2A4304880997E38A98B7BB932A5026E5"

environment = data["environment_at_recovery"]
assert environment["python"] == "3.9.13"
assert environment["dotnet_sdk"] == "10.0.302"
assert environment["environment_equivalence_to_original"] == "NOT_ASSUMED"

assert P12_4_SMOKE.is_file()

required_doc = (
    "explicit recovered P12.5 lineage",
    "does not claim Git identity equivalence",
    "new audited lineage",
    "revalidated on the current machine",
    "Matching file bytes does not recreate the unavailable Git commit identity.",
    "P12.5-RCV-3 RECOVERED P12.5 READINESS AND RECONSTRUCTION CENSUS",
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

assert git("rev-parse", "afp-p12.4-freeze^{}") == "13f7646f1052746f54f906076d66d29117ee2718"
assert git("rev-parse", "refs/tags/afp-p12.4-freeze") == "7c475986ed3ed1d58cc30148603fbfe8b09529ee"
subprocess.run(
    ["git", "merge-base", "--is-ancestor", "13f7646f1052746f54f906076d66d29117ee2718", "HEAD"],
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
)

print("P12_5_RCV_2_PROFILE=apexforge.p12.recovered-lineage-provenance/v1")
print("P12_5_RCV_2_CLASSIFICATION=RECOVERED_AUDITED_LINEAGE")
print("P12_5_RCV_2_BASE=P12.4_FREEZE")
print("P12_5_RCV_2_ORIGINAL_COMMIT_IDENTITY_EQUIVALENCE=False")
print("P12_5_RCV_2_REVALIDATION_REQUIRED=True")
print("P12_5_RCV_2_RECOVERED_LINEAGE_PROVENANCE=PASS")
