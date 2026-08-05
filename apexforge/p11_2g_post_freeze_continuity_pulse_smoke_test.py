"""P11.2G post-freeze continuity pulse and no-op capability audit.

This smoke test adds no production behavior. It proves that the published
P11.2F freeze remains authoritative, the canonical continuity pulse remains
present, the six P11.2F capability contracts still pass, and running this test
does not mutate tracked files, staging, repository status, bytecode, the
working directory, or the frozen production/document paths.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

from p11_2f_authority_graph_legality_smoke_test import (
    main as authority_graph_main,
)
from p11_2f_canonical_linker_collision_smoke_test import (
    main as linker_collision_main,
)
from p11_2f_concordat_conflict_evidence_smoke_test import (
    main as concordat_conflict_main,
)
from p11_2f_heterogeneous_air_verifier_smoke_test import (
    main as heterogeneous_verifier_main,
)
from p11_2f_linked_air_legality_architecture_audit_smoke_test import (
    main as architecture_audit_main,
)
from p11_2f_requirement_ownership_smoke_test import (
    main as requirement_ownership_main,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SELF_PATH = (
    "apexforge/"
    "p11_2g_post_freeze_continuity_pulse_smoke_test.py"
)

FROZEN_COMMIT = "63bf36d8773c82780881bf1443dfbb8ae8bc4fc3"
FROZEN_TAG = "afp-p11.2f-freeze"
FROZEN_SUBJECT = (
    "Complete P11.2F linked AIR legality and governance boundary"
)
FROZEN_ANNOTATION = (
    "Freeze P11.2F linked AIR legality and governance boundary"
)

CANONICAL_PULSE_TOKEN = (
    "VARENIC-CREST-PULSE: APEXFORGE-P11 / TAM-v3 / "
    "QV-AETHER / STORY-SEMANTICS / APEXMOTION"
)
CHECKPOINT_PULSE_TOKEN = (
    "APEXFORGE-CONTINUITY-PROOF: P11.2F / "
    "63bf36d / afp-p11.2f-freeze / NO-REPO-MUTATION"
)

CONTINUITY_DOCUMENT = (
    REPOSITORY_ROOT
    / "docs"
    / "p11"
    / "P11_CONTINUITY_PULSE.md"
)

FROZEN_PATHS = (
    "apexforge/air/linker.py",
    "apexforge/air/verify.py",
    "apexforge/authority/registry.py",
    "apexforge/authorization/role_resolver.py",
    "apexforge/governance/__init__.py",
    "apexforge/governance/conflicts.py",
    "apexforge/language/project.py",
    "apexforge/p11_2f_authority_graph_legality_smoke_test.py",
    "apexforge/p11_2f_canonical_linker_collision_smoke_test.py",
    "apexforge/p11_2f_concordat_conflict_evidence_smoke_test.py",
    "apexforge/p11_2f_heterogeneous_air_verifier_smoke_test.py",
    "apexforge/p11_2f_linked_air_legality_architecture_audit_smoke_test.py",
    "apexforge/p11_2f_requirement_ownership_smoke_test.py",
    "apexforge/workflow/air_runner.py",
    "apexforge/workflow/directive_engine.py",
    "docs/p11/P11_2F_LINKED_AIR_LEGALITY_AND_GOVERNANCE_BOUNDARY.md",
)

CAPABILITY_TESTS = (
    ("architecture audit", architecture_audit_main),
    ("canonical linker collisions", linker_collision_main),
    ("heterogeneous AIR verification", heterogeneous_verifier_main),
    ("authority graph legality", authority_graph_main),
    ("requirement ownership", requirement_ownership_main),
    ("passive Concordat conflict evidence", concordat_conflict_main),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_process(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )


def git_text(*arguments: str) -> str:
    completed = git_process(*arguments)
    require(
        completed.returncode == 0,
        "git command failed: "
        + " ".join(arguments)
        + ("\n" + completed.stderr if completed.stderr else ""),
    )
    return completed.stdout.strip()


def repository_status() -> str:
    return git_text(
        "status",
        "--porcelain=v2",
        "--untracked-files=all",
    )


def repository_bytecode_state() -> tuple[tuple[str, int, int], ...]:
    records: list[tuple[str, int, int]] = []

    for path in REPOSITORY_ROOT.rglob("*"):
        if (
            not path.is_file()
            or path.suffix.casefold() not in {".pyc", ".pyo"}
        ):
            continue

        details = path.stat()
        records.append(
            (
                path.relative_to(REPOSITORY_ROOT).as_posix(),
                details.st_size,
                details.st_mtime_ns,
            )
        )

    return tuple(sorted(records))


def frozen_path_hashes() -> tuple[tuple[str, str], ...]:
    records: list[tuple[str, str]] = []

    for relative in FROZEN_PATHS:
        path = REPOSITORY_ROOT / relative
        require(path.is_file(), f"frozen path is missing: {relative}")
        records.append(
            (
                relative,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )

    return tuple(records)


def require_safe_status(status: str) -> None:
    for line in status.splitlines():
        if not line:
            continue

        if line.startswith("? "):
            path = line[2:].strip()
            require(
                path == SELF_PATH
                or path.startswith("examples/P11Validation/"),
                f"unexpected untracked path: {path}",
            )
            continue

        raise AssertionError(
            "tracked or staged repository change exists: "
            + line
        )


def test_published_freeze_identity() -> None:
    require(
        git_text("cat-file", "-t", FROZEN_TAG) == "tag",
        "P11.2F freeze reference is not an annotated tag",
    )
    require(
        git_text("rev-list", "-n", "1", FROZEN_TAG)
        == FROZEN_COMMIT,
        "P11.2F freeze tag target changed",
    )
    require(
        git_text("show", "-s", "--format=%s", FROZEN_COMMIT)
        == FROZEN_SUBJECT,
        "P11.2F frozen commit subject changed",
    )
    require(
        git_text(
            "for-each-ref",
            f"refs/tags/{FROZEN_TAG}",
            "--format=%(subject)",
        )
        == FROZEN_ANNOTATION,
        "P11.2F freeze annotation changed",
    )

    ancestry = git_process(
        "merge-base",
        "--is-ancestor",
        FROZEN_COMMIT,
        "HEAD",
    )
    require(
        ancestry.returncode == 0,
        "current HEAD no longer descends from the P11.2F freeze",
    )


def test_canonical_pulse_and_roadmap_continuity() -> None:
    require(
        CONTINUITY_DOCUMENT.is_file(),
        "canonical P11 continuity document is missing",
    )
    document = CONTINUITY_DOCUMENT.read_text(encoding="utf-8")
    normalized = " ".join(document.split())

    require(
        CANONICAL_PULSE_TOKEN in normalized,
        "canonical Varenic Crest pulse token changed or disappeared",
    )

    required_stages = (
        "P11.6 Token Analysis Map",
        "P11.7 Quad-Vector engine",
        "P11.8 Parametric semantic lattice",
        "P11.9 AETHER-AIR 2.0 and interstitial behavior",
        "P11.10 Advanced conditionals, convergence, and Paradox Elevation",
        "P11.11 TAP Check audit ledger",
        "P11.12 Three-layer incremental cache",
        "P11.13 Rich documents and package architecture",
        "P11.14 Agents, characters, and professional archetypes",
        "P11.15 ApexMotion and simulation interoperability",
        "P11.16 Optimization integration and freeze",
    )

    for stage in required_stages:
        require(
            stage in normalized,
            f"continuity roadmap stage disappeared: {stage}",
        )


def test_frozen_paths_are_unchanged() -> None:
    completed = git_process(
        "diff",
        "--quiet",
        FROZEN_COMMIT,
        "--",
        *FROZEN_PATHS,
    )
    require(
        completed.returncode == 0,
        "a P11.2F frozen path differs from the published commit",
    )


def test_frozen_capabilities_still_pass() -> None:
    for label, operation in CAPABILITY_TESTS:
        operation()
        print(f"P11.2G continuity delegation — {label}: PASS")


def main() -> None:
    original_directory = Path.cwd().resolve()
    status_before = repository_status()
    bytecode_before = repository_bytecode_state()
    hashes_before = frozen_path_hashes()

    require(
        sys.dont_write_bytecode,
        "run this test with -B or PYTHONDONTWRITEBYTECODE=1",
    )
    require_safe_status(status_before)

    def forbidden_network(*_args, **_kwargs):
        raise AssertionError(
            "P11.2G continuity audit attempted network access"
        )

    with patch(
        "socket.create_connection",
        side_effect=forbidden_network,
    ), patch(
        "socket.socket",
        side_effect=forbidden_network,
    ):
        test_published_freeze_identity()
        test_canonical_pulse_and_roadmap_continuity()
        test_frozen_paths_are_unchanged()
        test_frozen_capabilities_still_pass()

    require(
        Path.cwd().resolve() == original_directory,
        "P11.2G continuity audit changed the working directory",
    )
    require(
        repository_status() == status_before,
        "P11.2G continuity audit changed repository status",
    )
    require(
        repository_bytecode_state() == bytecode_before,
        "P11.2G continuity audit changed repository bytecode state",
    )
    require(
        frozen_path_hashes() == hashes_before,
        "P11.2G continuity audit changed a frozen file",
    )

    print("AFP-P11.2G post-freeze continuity pulse smoke test passed.")
    print(f"Canonical pulse: {CANONICAL_PULSE_TOKEN}")
    print(f"Checkpoint pulse: {CHECKPOINT_PULSE_TOKEN}")
    print("Annotated freeze identity and ancestry: PASS")
    print("P11.2F frozen-path immutability: PASS")
    print("Six frozen P11.2F capability contracts: PASS")
    print("Network, Git, bytecode, cwd, and repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
