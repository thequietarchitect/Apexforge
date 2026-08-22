# P11.16D canonical non-durable resolution evidence gate.

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C_FREEZE = "715d41c733674b1b8681b0d3eb27b9143181bce7"
C_TAG = "afp-p11-16c-freeze"

B_MANIFEST = ROOT / "docs/p11/P11_16B_FINAL_VERIFICATION_MATRIX_MANIFEST.json"
C_CORRECTION = ROOT / "docs/p11/P11_16C_DURABLE_SEMANTIC_EXECUTION_CORRECTION.json"
D_MANIFEST = ROOT / "docs/p11/P11_16D_NON_DURABLE_RESOLUTION_MANIFEST.json"
D_DOC = ROOT / "docs/p11/P11_16D_HISTORICAL_ENVIRONMENT_TOOLCHAIN_RESOLUTION.md"

B_MANIFEST_BLOB_SHA256 = "950719EC51C523FCA3BF2BC39771AD068109EA3E8E7A23407E4C15C38E53AC2E"
C_CORRECTION_BLOB_SHA256 = "580244859CBE5CCC0E3CE0CF7C6282555BFAB7669325D262FFC03493F0E9C24C"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_bytes(*args: str) -> bytes:
    proc = subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stderr.decode("utf-8", "replace"))
    return proc.stdout


def git_text(*args: str) -> str:
    return git_bytes(*args).decode("utf-8").strip()


def main() -> int:
    require(git_text("rev-parse", "HEAD") == C_FREEZE, "HEAD must remain frozen C")
    require(git_text("cat-file", "-t", C_TAG) == "tag", "C tag must remain annotated")
    require(git_text("rev-parse", C_TAG + "^{commit}") == C_FREEZE, "C tag target changed")

    require(
        hashlib.sha256(git_bytes("show", "HEAD:docs/p11/P11_16B_FINAL_VERIFICATION_MATRIX_MANIFEST.json")).hexdigest().upper()
        == B_MANIFEST_BLOB_SHA256,
        "frozen B manifest blob changed",
    )
    require(
        hashlib.sha256(git_bytes("show", "HEAD:docs/p11/P11_16C_DURABLE_SEMANTIC_EXECUTION_CORRECTION.json")).hexdigest().upper()
        == C_CORRECTION_BLOB_SHA256,
        "frozen C correction blob changed",
    )

    base = json.loads(B_MANIFEST.read_text(encoding="utf-8"))
    correction = json.loads(C_CORRECTION.read_text(encoding="utf-8"))
    manifest = json.loads(D_MANIFEST.read_text(encoding="utf-8"))

    require(manifest["stage"] == "P11.16D", "D stage changed")
    require(manifest["scope"] == "VERIFICATION_EVIDENCE_ONLY", "D scope changed")
    require(manifest["production_mutation"] is False, "production mutation flag changed")
    require(manifest["repository_fixture_restoration"] is False, "fixture restoration flag changed")
    require(manifest["non_durable_total"] == 130, "non-durable total changed")

    expected_matrix = {
        "DURABLE_CURRENT": 48,
        "HISTORICAL_EXACT_FREEZE": 82,
        "ENVIRONMENT_FIXTURE_BOUND": 32,
        "EXTERNAL_TOOLCHAIN_BOUND": 16,
    }
    require(manifest["corrected_matrix_counts"] == expected_matrix, "corrected matrix counts changed")

    expected_resolutions = {
        "EXACT_ANNOTATED_FREEZE_BLOB_ANCHOR": 82,
        "PACKAGED_ENTRY_ENVIRONMENT_BOUND": 2,
        "P11VALIDATION_HISTORICALLY_REQUIRED_CANONICALLY_UNAVAILABLE": 30,
        "TOOLCHAIN_AVAILABLE_CURRENT_PASS": 2,
        "TOOLCHAIN_AVAILABLE_P11VALIDATION_CANONICALLY_UNAVAILABLE": 5,
        "TOOLCHAINS_AVAILABLE_HISTORICAL_EXACT_FREEZE_SUPERSESSION": 1,
        "VISUAL_STUDIO_AVAILABLE_CANONICAL_SOURCE_VALID_WORKTREE_LINE_ENDING_BOUND": 8,
    }
    require(manifest["resolution_code_counts"] == expected_resolutions, "resolution counts changed")

    rows = manifest["rows"]
    require(len(rows) == 130, "D row count changed")
    paths = [row["path"] for row in rows]
    require(len(paths) == len(set(paths)) == 130, "D paths are not unique")

    observed = Counter(row["resolution_code"] for row in rows)
    require(dict(observed) == expected_resolutions, "row-level resolution arithmetic changed")

    historical = [row for row in rows if row["corrected_class"] == "HISTORICAL_EXACT_FREEZE"]
    require(len(historical) == 82, "historical row count changed")
    require(
        all(
            row["resolution_code"] == "EXACT_ANNOTATED_FREEZE_BLOB_ANCHOR"
            and row["resolution_evidence"]["kind"] == "ANNOTATED"
            and row["resolution_evidence"]["exact_blob_match"] is True
            for row in historical
        ),
        "historical annotated anchor evidence changed",
    )

    environment = manifest["environment_evidence"]
    require(environment["row_count"] == 32, "environment row count changed")
    require(environment["packaged_entry_rows"] == 2, "packaged entry row count changed")
    require(environment["p11validation_environment_rows"] == 30, "P11Validation environment count changed")
    require(environment["p11validation_external_rows"] == 5, "P11Validation external count changed")
    require(
        environment["p11validation"]["resolution"]
        == "HISTORICALLY_REQUIRED_CANONICALLY_UNAVAILABLE",
        "P11Validation resolution changed",
    )
    require(environment["p11validation"]["repository_restoration"] == "NONE", "fixture restoration changed")

    external = manifest["external_toolchain_evidence"]
    require(external["row_count"] == 16, "external row count changed")
    require(external["visual_studio_rows"] == 15, "VS row count changed")
    require(external["vscode_rows"] == 5, "VS Code row count changed")
    require(external["powershell_rows"] == 1, "PowerShell row count changed")
    require(all(item["available"] for item in external["toolchains"].values()), "toolchain availability changed")
    require(len(external["visual_studio_t5_2_source_integrity"]) == 5, "T5.2 source count changed")
    require(
        all(item["canonical_integrity"] is True for item in external["visual_studio_t5_2_source_integrity"]),
        "T5.2 canonical source integrity changed",
    )

    correction_map = {item["path"]: item["to_class"] for item in correction["corrections"]}
    corrected = {
        entry["path"]: correction_map.get(entry["path"], entry["primary_class"])
        for entry in base["entries"]
    }
    expected_non_durable = sorted(path for path, cls in corrected.items() if cls != "DURABLE_CURRENT")
    require(sorted(paths) == expected_non_durable, "D does not cover exact corrected non-durable set")

    doc = D_DOC.read_text(encoding="utf-8")
    for marker in (
        "`HISTORICAL_EXACT_FREEZE`: **82**",
        "`ENVIRONMENT_FIXTURE_BOUND`: **32**",
        "`EXTERNAL_TOOLCHAIN_BOUND`: **16**",
        "P11.16D non-durable surface: **130**",
        "HISTORICALLY_REQUIRED_CANONICALLY_UNAVAILABLE",
        "exact annotated anchors: **82**",
        "**P11.16E â€” Repository-Wide Final Verification**",
    ):
        require(marker in doc, "D documentation marker missing: " + marker)

    print("P11_16D_SCOPE=VERIFICATION_EVIDENCE_ONLY")
    print("P11_16D_PRODUCTION_FILES=0")
    print("P11_16D_NON_DURABLE_TOTAL=130")
    print("P11_16D_HISTORICAL_RESOLVED=82")
    print("P11_16D_ENVIRONMENT_RESOLVED=32")
    print("P11_16D_EXTERNAL_RESOLVED=16")
    print("P11_16D_HISTORICAL_ANNOTATED_ANCHORS=82")
    print("P11_16D_P11VALIDATION_RESOLUTION=HISTORICALLY_REQUIRED_CANONICALLY_UNAVAILABLE")
    print("P11_16D_TOOLCHAINS_AVAILABLE=PASS")
    print("P11_16D_VISUAL_STUDIO_CANONICAL_SOURCE_INTEGRITY=PASS")
    print("P11_16D_PRODUCTION_MUTATION=NONE")
    print("P11_16D_REPOSITORY_FIXTURE_RESTORATION=NONE")
    print("P11_16D_NEXT=P11_16E_REPOSITORY_WIDE_FINAL_VERIFICATION")
    print("P11_16D_CANONICAL_NON_DURABLE_RESOLUTION=PASS")
    print("P11_16D_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
