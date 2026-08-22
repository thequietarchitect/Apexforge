"""P11.15C fingerprint-integrity successor architecture boundary."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "19f1e1cc00eb88da46e1968f4cb9dfa274f067f3"
PREDECESSOR_TAG = "afp-p11-15b-freeze"
EXPECTED_BRANCH = (
    "p11-15c-build-artifact-fingerprint-integrity-successor-architecture-boundary"
)

FROZEN_HASHES = {
    "apexforge/interoperability/__init__.py":
        "6DA040DF8EC6727CD9449A37C5EC07C8F8DD1C98D3F25F824B29F23F2261CA7B",
    "apexforge/interoperability/build_artifact.py":
        "1C0E288FE4A9D4B620D715CC35554767062DA8296456B2612F7B9F25BCF9BBAD",
    "apexforge/p11_15b_passive_build_artifact_interchange_smoke_test.py":
        "11E8C68C8170D76A9653D84AE74114D87F39C35A0F9A4B478C5BC4ED0A31BC84",
    "docs/p11/P11_15B_PASSIVE_BUILD_ARTIFACT_INTERCHANGE.md":
        "9F8496B820CE6436A8527B2DFD17CD93CD636596A02795C85EFCBC65BEB0E196",
    "apexforge/p11_15a_interoperability_ownership_first_contract_architecture_boundary_smoke_test.py":
        "7F5F4FB3E81241763C4B323F397C8A111A7C7D9C90ABB8A4B09CDCEEC0DA84F9",
    "docs/p11/P11_15A_INTEROPERABILITY_OWNERSHIP_FIRST_CONTRACT_ARCHITECTURE_BOUNDARY.md":
        "F87A7221A389189BBC8195B7A3CB00F2995127986DD6EAF98B35D10CFAD18570",
    "apexforge/tooling/build_artifact.py":
        "FBB3B49E85D549705AF5BD0ED0459063DCEAB4487A65E68BAF24E6DD6972B76B",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper()


def main() -> int:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.15B freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.15B freeze is not ancestor of P11.15C",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.15C branch changed")

    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))

    require(
        not (
            ROOT
            / "apexforge"
            / "interoperability"
            / "build_artifact_integrity.py"
        ).exists(),
        "P11.15D production module appeared during C",
    )

    b_source = (
        ROOT / "apexforge" / "interoperability" / "build_artifact.py"
    ).read_text(encoding="utf-8")
    require(
        "def verify_build_artifact_interchange_fingerprint(" not in b_source,
        "D surface was added by mutating frozen B",
    )

    narrative_execution = (
        ROOT / "apexforge" / "tooling" / "narrative_execution.py"
    ).read_text(encoding="utf-8")
    narrative_session = (
        ROOT / "apexforge" / "tooling" / "narrative_session.py"
    ).read_text(encoding="utf-8")

    duplicated_markers = (
        'fingerprint["algorithm"]',
        'fingerprint["value"]',
        'del payload["fingerprint"]',
        'expected = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()',
        'raise ValueError("build artifact fingerprint mismatch")',
    )
    for marker in duplicated_markers:
        require(
            marker in narrative_execution,
            "narrative_execution lost duplicated integrity marker: " + marker,
        )
        require(
            marker in narrative_session,
            "narrative_session lost duplicated integrity marker: " + marker,
        )

    require(
        'frozenset(("algorithm", "value"))' in narrative_execution
        or '"algorithm", "value"' in narrative_execution,
        "narrative_execution fingerprint exact-key rule missing",
    )
    require(
        'frozenset(("algorithm", "value"))' in narrative_session,
        "narrative_session fingerprint exact-key rule missing",
    )

    # B has no production consumer outside its own defining module.
    for relative in (
        "apexforge/tooling/build_artifact.py",
        "apexforge/tooling/cli.py",
        "apexforge/tooling/narrative_execution.py",
        "apexforge/tooling/narrative_session.py",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        require(
            "inspect_build_artifact_interchange" not in text,
            "{} unexpectedly consumes B".format(relative),
        )
        require(
            "interoperability.build_artifact" not in text,
            "{} unexpectedly imports B".format(relative),
        )

    doc = (
        ROOT
        / "docs"
        / "p11"
        / "P11_15C_BUILD_ARTIFACT_FINGERPRINT_INTEGRITY_SUCCESSOR_ARCHITECTURE_BOUNDARY.md"
    ).read_text(encoding="utf-8")

    for marker in (
        "P11.15B itself has no production consumer.",
        "one concrete duplicated interoperability concern",
        "interoperability.build_artifact_integrity",
        "def verify_build_artifact_interchange_fingerprint(",
        "No new result record is justified.",
        "D does not enforce canonical outer bytes",
        "D does not validate:",
        "D performs no reconstruction",
        "Rewiring narrative readers to consume D is deferred",
        "Every successor remains architecture-first.",
    ):
        require(marker in doc, "P11.15C document omitted marker: " + marker)

    print("P11_15B_FREEZE_ANCESTRY=PASS")
    print("P11_15C_ARCHITECTURE_ONLY=PASS")
    print("P11_15C_PRODUCTION_FILE_CHANGES=NONE")
    print("P11_15B_PRODUCTION_CONSUMERS=NONE")
    print("P11_15_DUPLICATED_FINGERPRINT_INTEGRITY=CONFIRMED")
    print("P11_15_GENERIC_LOADER=NOT_JUSTIFIED")
    print("P11_15_MAPPING_RETENTION=NOT_JUSTIFIED")
    print("P11_15_SCHEMA_MIGRATION=NOT_JUSTIFIED")
    print("P11_15_FILE_NETWORK_RPC_TRANSPORT=NOT_JUSTIFIED")
    print("P11_15_FFI_NATIVE_ABI=P12_DEFERRED")
    print("P11_15D_OWNER=interoperability.build_artifact_integrity")
    print("P11_15D_FUNCTION=verify_build_artifact_interchange_fingerprint")
    print("P11_15D_INPUT=EXACT_BUILD_ARTIFACT_INTERCHANGE")
    print("P11_15D_RETURN=DECLARED_VERIFIED_FINGERPRINT_STR")
    print("P11_15D_SCHEMA_CONTENT_CONSISTENCY=REQUIRED")
    print("P11_15D_FINGERPRINT_KEYS=ALGORITHM_VALUE_EXACT")
    print("P11_15D_FINGERPRINT_ALGORITHM=REUSE_TOOLING_CONSTANT")
    print("P11_15D_HASH_RULE=SHA256_CANONICAL_PAYLOAD_WITHOUT_FINGERPRINT")
    print("P11_15D_FULL_ARTIFACT_VALIDATION=DEFERRED")
    print("P11_15D_CANONICAL_OUTER_BYTES=NOT_REQUIRED")
    print("P11_15D_ARTIFACT_RECONSTRUCTION=NONE")
    print("P11_15D_CONSUMER_INTEGRATION=DEFERRED")
    print("P11_15C_BUILD_ARTIFACT_FINGERPRINT_INTEGRITY_SUCCESSOR_ARCHITECTURE_BOUNDARY=PASS")
    print("P11_15C_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())