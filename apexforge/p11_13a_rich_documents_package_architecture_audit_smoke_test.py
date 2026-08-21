"""P11.13A rich-documents/package-architecture audit smoke test.

This slice is intentionally audit-only. It freezes the stage-boundary evidence
and ownership decisions required before P11.13B introduces any rich-document or
package-tier production model.

Later P11.13 slices must not reuse this whole smoke as a forward-compatible
regression once the intentionally-absent P11.13 production owners exist.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
import subprocess
import sys

from language.narrative_model import (
    NarrativeCharacter,
    NarrativeContinuity,
    NarrativeScene,
    NarrativeStory,
)
from semantic_lattice.authoring import adapt_codex_semantic_lattice_proposal
from semantic_lattice.validation import validate_codex_semantic_lattice_proposal
from standard_library import (
    P10_STANDARD_LIBRARY_VERSION,
    StandardLibraryRegistry,
)
from tooling import project_loader
import tooling.cli as cli


PREDECESSOR_TAG = "afp-p11-12h-freeze"
PREDECESSOR_COMMIT = "278e8716d666bc663bc9570f2b367958d2abba83"

H_HASHES = {
    "apexforge/incremental_cache/integration.py":
        "973058C2CA9CE698FCF515B278B6A9B7D10617A2726B9D999890D8F452897E36",
    "apexforge/p11_12h_three_layer_incremental_cache_final_acceptance_smoke_test.py":
        "2A918CD790BB7530D4043C4B2939FFA208BFBA1D6C86398765972A91FFEF5BD2",
    "docs/p11/P11_12H_THREE_LAYER_INCREMENTAL_CACHE_FINAL_ACCEPTANCE.md":
        "EFE3F74514E8619ADFA6B66BC84D66FAED12BE1F7510F22A68B58C3D5E16E1F5",
}

EXPECTED_AUDIT_ARTIFACTS = (
    "apexforge/p11_13a_rich_documents_package_architecture_audit_smoke_test.py",
    "docs/p11/P11_13A_RICH_DOCUMENTS_PACKAGE_ARCHITECTURE_AUDIT.md",
)

PACKAGE_TIER_IDS = (
    "core",
    "standard",
    "domain",
    "experimental",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _production_python_files():
    package = _root() / "apexforge"
    for path in sorted(package.rglob("*.py")):
        relative = path.relative_to(_root()).as_posix()
        if "__pycache__" in path.parts:
            continue
        if path.name.endswith("_smoke_test.py"):
            continue
        if "/fixtures/" in "/" + relative:
            continue
        yield path


def _named_candidates(needles):
    rows = []
    for path in _production_python_files():
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(
                node,
                (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                continue
            lowered = node.name.casefold()
            if any(needle in lowered for needle in needles):
                rows.append(
                    (
                        path.relative_to(_root()).as_posix(),
                        node.__class__.__name__,
                        node.name,
                    )
                )
    return tuple(rows)


def _literal_occurrences(literal: str):
    rows = []
    lowered_literal = literal.casefold()
    for path in _production_python_files():
        text = path.read_text(encoding="utf-8")
        if lowered_literal not in text.casefold():
            continue
        rows.append(path.relative_to(_root()).as_posix())
    return tuple(rows)


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.12H freeze target changed",
    )
    _require(
        _git(
            "merge-base",
            "--is-ancestor",
            PREDECESSOR_TAG,
            "HEAD",
        ).returncode == 0,
        "P11.12H freeze is not ancestor of P11.13A",
    )

    for relative, expected in H_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen H hash changed".format(relative),
        )


def _assert_stage_boundary_absence() -> None:
    _require(
        ".apexdoc" not in inspect.getsource(project_loader).casefold(),
        "project loader already contains .apexdoc before P11.13 production",
    )
    _require(
        not _literal_occurrences(".apexdoc"),
        ".apexdoc production literal appeared before P11.13B/D",
    )

    absence_specs = (
        ("rich-document", ("apexdocument", "richdocument", "rich_document")),
        ("semantic-table", ("semantictable", "semantic_table")),
        ("semantic-diagram", ("semanticdiagram", "semantic_diagram")),
        ("world-bible", ("worldbible", "world_bible")),
        ("character-sheet", ("charactersheet", "character_sheet")),
        (
            "simulation-description",
            ("simulationdescription", "simulation_description"),
        ),
        ("package-descriptor", ("packagedescriptor", "package_descriptor")),
        ("package-tier", ("packagetier", "package_tier")),
    )
    for label, needles in absence_specs:
        _require(
            not _named_candidates(needles),
            "{} owner unexpectedly exists at P11.13A boundary".format(label),
        )

    for literal in (
        "lockfile",
        "package registry",
        "dependency solver",
        "package signing",
        "remote package",
    ):
        _require(
            not _literal_occurrences(literal),
            "future P14 package-manager concept leaked into P11.13A: "
            + literal,
        )


def _assert_existing_owner_boundaries() -> None:
    narrative_types = (
        NarrativeCharacter,
        NarrativeScene,
        NarrativeContinuity,
        NarrativeStory,
    )
    _require(
        all(value.__module__ == "language.narrative_model"
            for value in narrative_types),
        "canonical narrative model ownership moved",
    )

    _require(
        adapt_codex_semantic_lattice_proposal.__module__
        == "semantic_lattice.authoring",
        "Codex semantic-lattice authoring owner moved",
    )
    _require(
        validate_codex_semantic_lattice_proposal.__module__
        == "semantic_lattice.validation",
        "Codex semantic-lattice validation owner moved",
    )

    _require(
        StandardLibraryRegistry.__module__.startswith("standard_library"),
        "standard-library registry owner moved",
    )
    _require(
        isinstance(P10_STANDARD_LIBRARY_VERSION, str),
        "P10 standard-library version contract changed",
    )


def _assert_loader_and_cli_boundaries() -> None:
    manifest_fields = tuple(
        project_loader.ProjectManifest.__dataclass_fields__
    )
    _require(
        manifest_fields == ("name", "sources", "entry", "schema"),
        "ProjectManifest fields changed before P11.13 integration",
    )

    loaded_project_fields = tuple(
        project_loader.LoadedProject.__dataclass_fields__
    )
    _require(
        loaded_project_fields
        == ("root", "manifest_path", "manifest", "sources", "project_kind"),
        "LoadedProject fields changed before P11.13 integration",
    )

    _require(
        "project_builder" in inspect.signature(cli.main).parameters,
        "CLI main lost ProjectBuilder injection seam",
    )
    for function in (
        cli._run_build,
        cli._run_check,
        cli._run_execute,
    ):
        _require(
            "builder" in inspect.signature(function).parameters,
            "{} lost builder injection seam".format(function.__name__),
        )


def _assert_audit_only_artifact_set() -> None:
    status = _git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    _require(status.returncode == 0, status.stderr.strip())

    actual = tuple(
        line[3:].replace("\\", "/")
        for line in status.stdout.splitlines()
        if line.strip()
    )

    head_result = _git("rev-parse", "HEAD")
    _require(head_result.returncode == 0, head_result.stderr.strip())
    head = head_result.stdout.strip()

    if head == PREDECESSOR_COMMIT:
        _require(
            set(actual) == set(EXPECTED_AUDIT_ARTIFACTS),
            "P11.13A precommit must contain exactly two audit-only artifacts: {}".format(
                actual
            ),
        )

        tracked_diff = tuple(
            line.strip().replace("\\", "/")
            for line in _git(
                "diff",
                "--name-only",
                PREDECESSOR_TAG,
            ).stdout.splitlines()
            if line.strip()
        )
        _require(
            not tracked_diff,
            "P11.13A precommit audit modified tracked predecessor content",
        )
        return

    parent_result = _git("rev-parse", "HEAD^")
    _require(parent_result.returncode == 0, parent_result.stderr.strip())
    _require(
        parent_result.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.13A committed-head parent is not the frozen predecessor",
    )

    if actual:
        _require(
            actual
            == (
                "apexforge/p11_13a_rich_documents_package_architecture_audit_smoke_test.py",
            ),
            "P11.13A committed-head repair state contains unexpected working-tree changes: {}".format(
                actual
            ),
        )

    committed = tuple(
        line.strip().replace("\\", "/")
        for line in _git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).stdout.splitlines()
        if line.strip()
    )
    _require(
        set(committed) == set(EXPECTED_AUDIT_ARTIFACTS),
        "P11.13A committed HEAD must contain exactly two audit-only artifacts: {}".format(
            committed
        ),
    )

    predecessor_delta = tuple(
        line.strip().replace("\\", "/")
        for line in _git(
            "diff",
            "--name-only",
            PREDECESSOR_TAG,
            "HEAD",
            "--",
            "apexforge",
            "docs",
        ).stdout.splitlines()
        if line.strip()
    )
    _require(
        set(predecessor_delta) == set(EXPECTED_AUDIT_ARTIFACTS),
        "P11.13A committed predecessor delta exceeded the two audit artifacts: {}".format(
            predecessor_delta
        ),
    )


def main() -> None:
    _assert_predecessor()
    _assert_stage_boundary_absence()
    _assert_existing_owner_boundaries()
    _assert_loader_and_cli_boundaries()
    _assert_audit_only_artifact_set()

    print("P11_12H_FREEZE_ANCESTRY=PASS")
    print("P11_12H_FROZEN_HASHES=PASS")
    print("P11_13A_MODE=AUDIT_ONLY")
    print("P11_13A_PRODUCTION_MUTATION=NONE")
    print("P11_13A_AUDIT_ARTIFACT_COUNT=2")
    print("APEXDOC_PRODUCTION=ABSENT_STAGE_BOUNDARY")
    print("RICH_DOCUMENT_OWNER=ABSENT_STAGE_BOUNDARY")
    print("PACKAGE_DESCRIPTOR_OWNER=ABSENT_STAGE_BOUNDARY")
    print("PACKAGE_TIER_OWNER=ABSENT_STAGE_BOUNDARY")
    print("PROJECT_MANIFEST_FIELDS=name,sources,entry,schema")
    print("PROJECT_MANIFEST_INTEGRATION=DEFERRED")
    print("CLI_INTEGRATION=DEFERRED")
    print("NARRATIVE_OWNER_DUPLICATION=FORBIDDEN")
    print("NARRATIVE_CANONICAL_OWNER=language.narrative_model")
    print("CODEX_AUTHORING_OWNER=semantic_lattice.authoring")
    print("CODEX_VALIDATION_OWNER=semantic_lattice.validation")
    print("P11_13_C_CODEX_ROLE=OPTIONAL_ADVISORY")
    print("P11_13_C_DETERMINISTIC_COMPILATION_DEPENDENCY=FORBIDDEN")
    print("PACKAGE_TIER_IDS={}".format(",".join(PACKAGE_TIER_IDS)))
    print("PACKAGE_MANAGER_REMOTE_REGISTRY_SOLVER_LOCKFILE=DEFERRED_TO_P14")
    print("TAP_OWNERSHIP=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("PREDECESSOR_PRODUCTION_MUTATION=NONE")
    print("P11_13A_RICH_DOCUMENTS_PACKAGE_ARCHITECTURE_AUDIT=PASS")


if __name__ == "__main__":
    main()