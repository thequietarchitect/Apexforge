"""Executable P11.5D-B passive narrative graph validation contract."""

from __future__ import annotations

import ast
import subprocess
from collections import Counter
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

from language.narrative_graph import build_narrative_semantic_graph
from language.narrative_model import (
    NarrativeCharacter,
    NarrativeChoice,
    NarrativeChoicePath,
    NarrativeContinuity,
    NarrativeContinuityConstraint,
    NarrativeDialogue,
    NarrativeIdentity,
    NarrativePerspective,
    NarrativeScene,
    NarrativeState,
    NarrativeStateFact,
    NarrativeStory,
    NarrativeTimeline,
)
from language.narrative_validation import (
    NarrativeValidationFinding,
    NarrativeValidationReport,
    validate_narrative_semantic_graph,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = REPOSITORY_ROOT / "apexforge"
BASELINE_TAG = "afp-p11.5c-freeze"
EXPECTED_HEAD = "d7d19bb84845400c4b004c52e011c89a4a9b1c0d"
EXPECTED_BRANCH = "p11.5d-narrative-graph-validation"

AUDIT_PATHS = {
    "apexforge/p11_5d_narrative_graph_validation_architecture_audit_smoke_test.py",
    "docs/p11/P11_5D_NARRATIVE_GRAPH_VALIDATION_ARCHITECTURE_AUDIT.md",
}
IMPLEMENTATION_PATHS = {
    "apexforge/language/narrative_validation.py",
    "apexforge/p11_5d_passive_narrative_graph_validation_smoke_test.py",
    "docs/p11/P11_5D_PASSIVE_NARRATIVE_GRAPH_VALIDATION_CONTRACT.md",
}
REVIEWED_PATHS = AUDIT_PATHS | IMPLEMENTATION_PATHS


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=REPOSITORY_ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def identity(kind: str, *path: str) -> NarrativeIdentity:
    return NarrativeIdentity(kind, path)


def require_raises(expected_type, operation, message: str) -> None:
    try:
        operation()
    except expected_type:
        return
    raise AssertionError(message)


def test_frozen_baseline_and_exact_reviewed_ownership() -> None:
    require(
        git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "P11.5D-B is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "P11.5D-B predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5C controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip() == EXPECTED_HEAD,
        "P11.5C controlling freeze resolves incorrectly",
    )

    committed = {
        item
        for item in git(
            "diff",
            "--name-only",
            f"{BASELINE_TAG}..HEAD",
        ).splitlines()
        if item
    }
    working = {
        line[3:].replace("\\", "/")
        for line in git(
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).splitlines()
        if len(line) >= 4
        and not line[3:].replace("\\", "/").startswith(
            "examples/P11Validation/"
        )
    }
    require(
        committed | working == REVIEWED_PATHS,
        "P11.5D reviewed candidate path set changed",
    )
    require(
        all((REPOSITORY_ROOT / path).is_file() for path in REVIEWED_PATHS),
        "one or more reviewed P11.5D files are missing",
    )


def test_public_result_model_contract() -> None:
    import language.narrative_validation as validation_module

    require(
        validation_module.__all__
        == (
            "NarrativeValidationFinding",
            "NarrativeValidationReport",
            "validate_narrative_semantic_graph",
        ),
        "P11.5D-B public exports changed",
    )
    require(
        tuple(item.name for item in fields(NarrativeValidationFinding))
        == (
            "classification",
            "identities",
            "node_indexes",
            "edge_indexes",
            "evidence",
        ),
        "NarrativeValidationFinding fields changed",
    )
    require(
        tuple(item.name for item in fields(NarrativeValidationReport))
        == ("story", "findings"),
        "NarrativeValidationReport fields changed",
    )

    story_id = identity("story", "Story")
    character = identity("character", "Ada")
    finding = NarrativeValidationFinding(
        "referenced_only_identity",
        (character,),
        (1,),
    )
    require_raises(
        FrozenInstanceError,
        lambda: setattr(finding, "classification", "temporal_cycle"),
        "NarrativeValidationFinding is mutable",
    )
    require_raises(
        ValueError,
        lambda: NarrativeValidationFinding(
            "unknown",
            (character,),
            (1,),
        ),
        "unknown validation classification was accepted",
    )
    report = NarrativeValidationReport(story_id, (finding,))
    require_raises(
        FrozenInstanceError,
        lambda: setattr(report, "findings", ()),
        "NarrativeValidationReport is mutable",
    )


def make_experimental_story() -> NarrativeStory:
    story_id = identity("story", "ExperimentalContinuity")
    ada = identity("character", "Ada")
    borin = identity("character", "Borin")
    witness = identity("character", "UndeclaredWitness")
    arrival = identity("scene", "Arrival")
    archive = identity("scene", "Archive")
    departure = identity("scene", "Departure")
    hidden = identity("scene", "UndeclaredHiddenChamber")

    return NarrativeStory(
        story_id,
        (
            NarrativeCharacter(ada),
            NarrativeCharacter(ada),
            NarrativeCharacter(borin),
        ),
        (
            NarrativeScene(arrival),
            NarrativeScene(archive),
            NarrativeScene(departure),
        ),
        (
            NarrativeDialogue(
                identity("dialogue", "Warning"),
                arrival,
                ada,
                (borin, witness, borin),
            ),
        ),
        (
            NarrativeChoice(
                identity("choice", "ArchiveDecision"),
                archive,
                (
                    NarrativeChoicePath(
                        "Enter the hidden chamber",
                        hidden,
                        "door_open",
                        "secret_revealed",
                    ),
                    NarrativeChoicePath(
                        "Leave the archive",
                        departure,
                        "door_closed",
                        "archive_abandoned",
                    ),
                ),
            ),
        ),
        (
            NarrativePerspective(
                identity("perspective", "AdaView"),
                ada,
            ),
            NarrativePerspective(
                identity("perspective", "AdaViewEcho"),
                ada,
            ),
        ),
        (
            NarrativeTimeline(
                identity("timeline", "MainTimeline"),
                (arrival, archive, arrival, departure),
            ),
        ),
        (
            NarrativeState(
                identity("narrative_state", "ConflictingFacts"),
                (
                    NarrativeStateFact(ada, "trusts_borin", "true"),
                    NarrativeStateFact(ada, "trusts_borin", "false"),
                    NarrativeStateFact(witness, "is_visible", "false"),
                ),
            ),
        ),
        (
            NarrativeContinuity(
                identity("continuity", "ConflictingConstraints"),
                (
                    NarrativeContinuityConstraint(
                        (ada,),
                        "Ada remembers the archive.",
                    ),
                    NarrativeContinuityConstraint(
                        (ada,),
                        "Ada has never encountered the archive.",
                    ),
                    NarrativeContinuityConstraint(
                        (witness,),
                        "The witness remains unknown.",
                    ),
                ),
            ),
        ),
    )


def test_experimental_classification_contract() -> None:
    graph = build_narrative_semantic_graph(make_experimental_story())
    first = validate_narrative_semantic_graph(graph)
    second = validate_narrative_semantic_graph(graph)
    require(first == second, "identical graph changed validation output")
    require(first.story == graph.story, "validation report story changed")

    counts = Counter(
        finding.classification
        for finding in first.findings
    )
    require(
        counts
        == Counter(
            {
                "duplicate_declaration": 1,
                "referenced_only_identity": 2,
                "conflicting_state_value": 1,
                "temporal_cycle": 1,
                "repeated_relation_evidence": 2,
                "continuity_assertion_cluster": 1,
                "perspective_cluster": 1,
            }
        ),
        f"experimental classifications changed: {counts}",
    )

    classifications = tuple(
        finding.classification
        for finding in first.findings
    )
    require(
        classifications
        == (
            "duplicate_declaration",
            "referenced_only_identity",
            "referenced_only_identity",
            "conflicting_state_value",
            "temporal_cycle",
            "repeated_relation_evidence",
            "repeated_relation_evidence",
            "continuity_assertion_cluster",
            "perspective_cluster",
        ),
        "P11.5D-B classification family ordering changed",
    )

    repeated = [
        finding
        for finding in first.findings
        if finding.classification == "repeated_relation_evidence"
    ]
    repeated_relations = {
        dict(finding.evidence)["relation"]
        for finding in repeated
    }
    require(
        repeated_relations == {"participant", "timeline_scene"},
        "indexed repeated relation evidence changed",
    )

    continuity = next(
        finding
        for finding in first.findings
        if finding.classification
        == "continuity_assertion_cluster"
    )
    require(
        "contradict" not in dict(continuity.evidence),
        "continuity cluster acquired unsupported contradiction inference",
    )

    perspective = next(
        finding
        for finding in first.findings
        if finding.classification == "perspective_cluster"
    )
    require(
        "conflict" not in dict(perspective.evidence),
        "perspective cluster acquired unsupported conflict inference",
    )


def test_passive_boundary_and_frozen_predecessor_preservation() -> None:
    module_path = PACKAGE_DIRECTORY / "language" / "narrative_validation.py"
    text = module_path.read_text(encoding="utf-8")
    tree = ast.parse(text)

    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    require(
        public_functions == {"validate_narrative_semantic_graph"},
        "P11.5D-B exposes an unexpected public operation",
    )

    forbidden = (
        "BuildDiagnostic",
        "APX-NARRATIVE-",
        "APX-STORY-",
        "APX-CONTINUITY-",
        "SourceSpan",
        "AIRProgram",
        "language.parser",
        "language.compiler",
        "language.project",
        "runtime.",
        "tooling.cli",
    )
    require(
        all(marker not in text for marker in forbidden),
        "P11.5D-B escaped its passive validation boundary",
    )

    for relative in (
        "apexforge/language/narrative_model.py",
        "apexforge/language/narrative_graph.py",
        "apexforge/language/parser.py",
        "apexforge/language/compiler.py",
        "apexforge/language/project.py",
        "apexforge/air/model.py",
        "apexforge/air/serialization.py",
        "apexforge/runtime/engine.py",
        "apexforge/tooling/cli.py",
    ):
        baseline = git("show", f"{BASELINE_TAG}:{relative}").encode("utf-8")
        require(
            (REPOSITORY_ROOT / relative).read_bytes() == baseline,
            f"frozen predecessor or operational file changed: {relative}",
        )


def main() -> None:
    before = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    test_frozen_baseline_and_exact_reviewed_ownership()
    test_public_result_model_contract()
    test_experimental_classification_contract()
    test_passive_boundary_and_frozen_predecessor_preservation()
    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "P11.5D-B smoke test mutated repository status")

    print("AFP-P11.5D-B passive narrative graph validation smoke test passed.")
    print("P11.5C annotated freeze and exact predecessor HEAD: PASS")
    print("Exact five-file reviewed candidate ownership: PASS")
    print("Immutable finding, report, and validator API: PASS")
    print("Deterministic experimental evidence classification: PASS")
    print("Duplicate, reference, state, cycle, and repeated-relation findings: PASS")
    print("Continuity and perspective remain non-contradiction clusters: PASS")
    print("No parser, compiler, runtime, diagnostic, source-span, or CLI integration: PASS")
    print("Frozen P11.5C graph and operational baseline preservation: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
