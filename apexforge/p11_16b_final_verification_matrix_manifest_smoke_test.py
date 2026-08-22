from __future__ import annotations

import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

A_FREEZE = "56286b04905a063988d325c5e699c268cdc835a4"
A_TAG = "afp-p11-16a-freeze"
MATRIX_BASELINE = "12f1e568bec83f5d74c661e042f7bcef25f0b5b9"
SCHEMA = "apexforge.p11-final-verification-matrix/v1"
CLASSIFICATION_VERSION = "p11.16b/v1"

MANIFEST_PATH = (
    ROOT / "docs/p11/P11_16B_FINAL_VERIFICATION_MATRIX_MANIFEST.json"
)
DOC_PATH = (
    ROOT / "docs/p11/P11_16B_FINAL_VERIFICATION_MATRIX_CLASSIFICATION.md"
)

CLASSES = (
    "DURABLE_CURRENT",
    "HISTORICAL_EXACT_FREEZE",
    "ENVIRONMENT_FIXTURE_BOUND",
    "EXTERNAL_TOOLCHAIN_BOUND",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_text(*args: str) -> str:
    proc = subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            "git failed: git {}\n{}".format(" ".join(args), proc.stderr)
        )
    return proc.stdout


def git_bytes(*args: str) -> bytes:
    proc = subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            "git failed: git {}\n{}".format(
                " ".join(args), proc.stderr.decode("utf-8", "replace")
            )
        )
    return proc.stdout


def baseline_test_paths():
    paths = [
        line.strip()
        for line in git_text(
            "ls-tree", "-r", "--name-only", MATRIX_BASELINE
        ).splitlines()
        if line.strip()
    ]
    return sorted(
        path
        for path in paths
        if path.startswith("apexforge/p11_")
        and path.endswith("_smoke_test.py")
    )


def family_for(name: str):
    match = re.match(
        r"p11_(\d+)([a-z0-9_]*)_smoke_test\.py$",
        name,
        re.IGNORECASE,
    )
    if match:
        return "NUMBERED", int(match.group(1))
    if name.startswith("p11_src_"):
        return "SRC", None
    if name.startswith("p11_tam_"):
        return "TAM", None
    raise AssertionError("unclassified baseline smoke test: {}".format(name))


def risk_flags(name: str, source: str):
    lowered = source.lower()
    name_lower = name.lower()
    return {
        "requires_p11validation": "p11validation" in lowered,
        "uses_tempfile": "tempfile" in lowered,
        "uses_subprocess": "subprocess" in lowered,
        "explicit_visual_studio": (
            any(
                marker in lowered
                for marker in (
                    "visualstudio",
                    "visual studio",
                    "devenv",
                    "msbuild",
                )
            )
            or "visualstudio" in name_lower
        ),
        "explicit_vscode": (
            any(marker in lowered for marker in ("vscode", "vs code"))
            or "vscode" in name_lower
        ),
        "explicit_powershell_toolchain": (
            "powershell_tooling_compatibility" in name_lower
            or "powershell tooling compatibility" in lowered
        ),
        "exact_hash_evidence": (
            bool(re.search(r"(?i)\b[0-9a-f]{64}\b", source))
            or bool(re.search(r"(?i)\b[0-9a-f]{40}\b", source))
            or "sha256" in lowered
            or "get-filehash" in lowered
        ),
        "git_evidence": any(
            marker in lowered
            for marker in (
                "git rev-parse",
                "git cat-file",
                "git merge-base",
                "git show",
                "git status",
                "git diff",
                "git tag",
                "rev-parse",
                "cat-file",
                "merge-base",
            )
        ),
        "freeze_evidence": (
            "freeze" in name_lower
            or "frozen" in name_lower
            or "freeze" in lowered
            or "frozen" in lowered
        ),
    }


def classify(flags: dict):
    reasons = []
    if (
        flags["explicit_visual_studio"]
        or flags["explicit_vscode"]
        or flags["explicit_powershell_toolchain"]
    ):
        reasons.append("explicit_external_toolchain_identity")
        if flags["explicit_visual_studio"]:
            reasons.append("visual_studio")
        if flags["explicit_vscode"]:
            reasons.append("vscode")
        if flags["explicit_powershell_toolchain"]:
            reasons.append("powershell_tooling_compatibility")
        return "EXTERNAL_TOOLCHAIN_BOUND", sorted(reasons)

    if flags["requires_p11validation"]:
        return (
            "ENVIRONMENT_FIXTURE_BOUND",
            ["requires_examples_p11validation"],
        )

    if (
        flags["freeze_evidence"]
        and (flags["exact_hash_evidence"] or flags["git_evidence"])
    ):
        reasons.append("freeze_evidence")
        if flags["exact_hash_evidence"]:
            reasons.append("exact_hash_evidence")
        if flags["git_evidence"]:
            reasons.append("git_evidence")
        return "HISTORICAL_EXACT_FREEZE", sorted(reasons)

    if flags["exact_hash_evidence"] and flags["git_evidence"]:
        return (
            "HISTORICAL_EXACT_FREEZE",
            ["exact_hash_evidence", "git_evidence"],
        )

    return "DURABLE_CURRENT", ["current_semantic_candidate"]


def recompute():
    rows = []
    class_counts = collections.Counter()
    family_counts = collections.Counter()
    phase_counts = collections.Counter()
    risk_counts = collections.Counter()

    paths = baseline_test_paths()
    require(len(paths) == 178, "baseline test count changed")

    for rel in paths:
        raw = git_bytes("show", "{}:{}".format(MATRIX_BASELINE, rel))
        source = raw.decode("utf-8")
        name = Path(rel).name
        family, phase = family_for(name)
        flags = risk_flags(name, source)
        primary_class, reasons = classify(flags)

        class_counts[primary_class] += 1
        family_counts[family] += 1
        if phase is not None:
            phase_counts[str(phase)] += 1
        for key, value in flags.items():
            if value:
                risk_counts[key] += 1

        rows.append(
            {
                "path": rel,
                "name": name,
                "family": family,
                "phase": phase,
                "primary_class": primary_class,
                "classification_reason_codes": reasons,
                "execution_stage": (
                    "P11.16C"
                    if primary_class == "DURABLE_CURRENT"
                    else "P11.16D"
                ),
                "source_sha256": hashlib.sha256(raw).hexdigest().upper(),
                "git_blob_oid": git_text(
                    "rev-parse", "{}:{}".format(MATRIX_BASELINE, rel)
                ).strip(),
                "risk_flags": flags,
            }
        )

    return {
        "schema": SCHEMA,
        "classification_version": CLASSIFICATION_VERSION,
        "matrix_baseline_commit": MATRIX_BASELINE,
        "architecture_freeze_commit": A_FREEZE,
        "scope": "pre-P11.16 P11 smoke tests",
        "row_count": len(rows),
        "verification_classes": list(CLASSES),
        "family_counts": dict(sorted(family_counts.items())),
        "phase_counts": dict(
            sorted(phase_counts.items(), key=lambda kv: int(kv[0]))
        ),
        "class_counts": {
            key: class_counts.get(key, 0)
            for key in CLASSES
        },
        "risk_counts": dict(sorted(risk_counts.items())),
        "classification_policy": {
            "precedence": [
                "EXTERNAL_TOOLCHAIN_BOUND",
                "ENVIRONMENT_FIXTURE_BOUND",
                "HISTORICAL_EXACT_FREEZE",
                "DURABLE_CURRENT",
            ],
            "subprocess_alone_is_external": False,
            "p11validation_primary_class": "ENVIRONMENT_FIXTURE_BOUND",
            "explicit_toolchains": [
                "Visual Studio",
                "VSCode",
                "PowerShell tooling compatibility",
            ],
            "historical_exact_rule": (
                "freeze evidence plus exact-hash/git evidence, or "
                "exact-hash plus git evidence"
            ),
            "durable_rule": "no stronger non-durable classification evidence",
        },
        "entries": rows,
    }


def main() -> int:
    require(
        git_text("rev-parse", "HEAD").strip() == A_FREEZE,
        "B must remain non-production on exact frozen A HEAD",
    )
    require(
        git_text("cat-file", "-t", A_TAG).strip() == "tag",
        "A freeze tag must remain annotated",
    )
    require(
        git_text("rev-parse", A_TAG + "^{commit}").strip() == A_FREEZE,
        "A freeze tag target changed",
    )

    expected = recompute()
    actual_bytes = MANIFEST_PATH.read_bytes()
    expected_bytes = (
        json.dumps(
            expected,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")

    require(
        actual_bytes == expected_bytes,
        "P11.16B canonical matrix manifest does not match recomputation",
    )

    actual = json.loads(actual_bytes.decode("utf-8"))
    require(actual["row_count"] == 178, "manifest row count changed")
    require(
        actual["family_counts"] == {
            "NUMBERED": 157,
            "SRC": 9,
            "TAM": 12,
        },
        "manifest family counts changed",
    )
    require(
        sum(actual["class_counts"].values()) == 178,
        "verification class counts do not sum to 178",
    )

    names = [entry["path"] for entry in actual["entries"]]
    require(len(names) == len(set(names)) == 178, "manifest paths are not unique")
    require(names == sorted(names), "manifest rows are not path-sorted")

    for entry in actual["entries"]:
        require(entry["primary_class"] in CLASSES, "unknown primary class")
        require(
            entry["execution_stage"]
            == (
                "P11.16C"
                if entry["primary_class"] == "DURABLE_CURRENT"
                else "P11.16D"
            ),
            "execution routing mismatch",
        )

    require(
        actual["classification_policy"]["subprocess_alone_is_external"]
        is False,
        "subprocess alone must not imply external classification",
    )

    doc = DOC_PATH.read_text(encoding="utf-8")
    for key, value in actual["class_counts"].items():
        require(
            "`{}`: **{}**".format(key, value) in doc,
            "document class count mismatch for {}".format(key),
        )

    print("P11_16B_SCOPE=CLASSIFICATION_MANIFEST_ONLY")
    print("P11_16B_PRODUCTION_FILES=0")
    print("P11_16B_MATRIX_BASELINE=P11_15I_FREEZE")
    print("P11_16B_ROW_COUNT=178")
    print("P11_16B_NUMBERED=157")
    print("P11_16B_SRC=9")
    print("P11_16B_TAM=12")
    for key in CLASSES:
        print("P11_16B_CLASS_{}={}".format(key, actual["class_counts"][key]))
    print("P11_16B_SUBPROCESS_ALONE_EXTERNAL=FALSE")
    print("P11_16B_P11VALIDATION_PRIMARY=ENVIRONMENT_FIXTURE_BOUND")
    print("P11_16B_MANIFEST_CANONICAL_RECOMPUTATION=PASS")
    print("P11_16B_ALL_178_ROWS_UNIQUE=PASS")
    print("P11_16B_EXECUTION_ROUTING=C_FOR_DURABLE_D_FOR_NON_DURABLE")
    print("P11_16B_NEXT=P11_16C_DURABLE_SEMANTIC_EXECUTION")
    print("P11_16B_MATRIX_CLASSIFICATION_AND_MANIFEST=PASS")
    print("P11_16B_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
