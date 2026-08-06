"""Executable P11.5G-B narrative semantic lowering contract."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from language.diagnostics import BuildDiagnostic
from language.narrative_lowering import (
    NarrativeSemanticLoweringError,
    lower_narrative_source,
)
from language.narrative_model import NarrativeStory
from language.narrative_parser import parse_narrative_source


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = REPOSITORY_ROOT / "apexforge"
BASELINE_TAG = "afp-p11.5f-freeze"
EXPECTED_HEAD = "f24bd96217fb541f105e3bb1f1564f4c593e5111"
EXPECTED_BRANCH = "p11.5g-narrative-semantic-lowering"

AUDIT_PATHS = {
    "apexforge/p11_5g_narrative_semantic_lowering_architecture_audit_smoke_test.py",
    "docs/p11/P11_5G_NARRATIVE_SEMANTIC_LOWERING_ARCHITECTURE_AUDIT.md",
}
IMPLEMENTATION_PATHS = {
    "apexforge/language/narrative_lowering.py",
    "apexforge/p11_5g_narrative_semantic_lowering_smoke_test.py",
    "docs/p11/P11_5G_NARRATIVE_SEMANTIC_LOWERING_CONTRACT.md",
}
REVIEWED_PATHS = AUDIT_PATHS | IMPLEMENTATION_PATHS

VALID_SOURCE = "\n".join(
    (
        "story ExperimentalContinuity {",
        "    character Ada",
        "    character Ada",
        "    character Borin",
        "",
        "    scene Arrival",
        "    scene Archive",
        "",
        "    dialogue Warning {",
        "        scene Arrival",
        "        speaker Ada",
        "        participants [Borin, UndeclaredWitness, Borin]",
        "    }",
        "",
        "    choice ArchiveDecision {",
        "        scene Archive",
        '        path "Enter" {',
        "            destination UndeclaredHiddenChamber",
        "            condition door_open",
        "            consequence secret_revealed",
        "        }",
        '        path "Return" {',
        "            destination Arrival",
        "            consequence false",
        "        }",
        "    }",
        "",
        "    perspective AdaView {",
        "        viewpoint Ada",
        "    }",
        "",
        "    timeline MainTimeline {",
        "        scenes [Arrival, Archive, Arrival]",
        "    }",
        "",
        "    narrative_state KnownFacts {",
        "        fact Ada.trusts_borin = true",
        "        fact Ada.trusts_borin = false",
        '        fact Ada.note = "quoted_fact"',
        "    }",
        "",
        "    continuity IdentityLaw {",
        '        require Ada: "Ada remembers the archive."',
        '        require Ada, Borin: "Shared memory."',
        "    }",
        "}",
    )
)


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


def require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as error:
        return error
    raise AssertionError(message)


def test_frozen_baseline_and_exact_reviewed_ownership() -> None:
    require(
        git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "P11.5G-B is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "P11.5G-B predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5F controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip() == EXPECTED_HEAD,
        "P11.5F controlling freeze resolves incorrectly",
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
        "reviewed P11.5G candidate path set changed",
    )


def test_public_lowering_contract() -> None:
    import language.narrative_lowering as lowering_module

    require(
        lowering_module.__all__
        == (
            "NarrativeSemanticLoweringError",
            "lower_narrative_source",
        ),
        "P11.5G-B public exports changed",
    )
    require(
        issubclass(NarrativeSemanticLoweringError, Exception),
        "NarrativeSemanticLoweringError is not an exception type",
    )
    require_raises(
        TypeError,
        lambda: lower_narrative_source(object()),
        "non-source document was accepted",
    )


def test_complete_lowering_and_determinism() -> None:
    document = parse_narrative_source(
        VALID_SOURCE,
        source_name="story.apex",
    )
    preserved_document = parse_narrative_source(
        VALID_SOURCE,
        source_name="story.apex",
    )

    first = lower_narrative_source(document)
    second = lower_narrative_source(document)

    require(
        type(first) is NarrativeStory,
        "lowerer did not return exact NarrativeStory",
    )
    require(first == second, "identical source lowered nondeterministically")
    require(
        document == preserved_document,
        "lowering mutated the source document",
    )

    require(
        first.identity.kind == "story"
        and first.identity.path == ("ExperimentalContinuity",),
        "story identity mapping changed",
    )
    require(
        tuple(item.identity.path for item in first.characters)
        == (("Ada",), ("Ada",), ("Borin",)),
        "character order or duplicate evidence changed",
    )
    require(
        tuple(item.identity.path for item in first.scenes)
        == (("Arrival",), ("Archive",)),
        "scene order changed",
    )

    dialogue = first.dialogues[0]
    require(
        dialogue.identity.path == ("Warning",)
        and dialogue.scene.kind == "scene"
        and dialogue.scene.path == ("Arrival",)
        and dialogue.speaker.kind == "character"
        and dialogue.speaker.path == ("Ada",),
        "dialogue identity or primary references changed",
    )
    require(
        tuple(item.path for item in dialogue.participants)
        == (("Borin",), ("UndeclaredWitness",), ("Borin",)),
        "participant order, duplicates, or unresolved evidence changed",
    )

    choice = first.choices[0]
    require(
        choice.identity.path == ("ArchiveDecision",)
        and choice.scene.path == ("Archive",),
        "choice identity or scene mapping changed",
    )
    require(
        tuple(path.label for path in choice.paths)
        == ("Enter", "Return"),
        "choice-path order or labels changed",
    )
    require(
        choice.paths[0].destination.path
        == ("UndeclaredHiddenChamber",)
        and choice.paths[0].condition == "door_open"
        and choice.paths[0].consequence == "secret_revealed"
        and choice.paths[1].consequence == "false",
        "choice path scalar or unresolved-reference mapping changed",
    )

    require(
        first.perspectives[0].identity.path == ("AdaView",)
        and first.perspectives[0].viewpoint.path == ("Ada",),
        "perspective mapping changed",
    )
    require(
        tuple(item.path for item in first.timelines[0].scenes)
        == (("Arrival",), ("Archive",), ("Arrival",)),
        "timeline order or duplicate evidence changed",
    )

    state = first.states[0]
    require(
        state.identity.kind == "narrative_state"
        and state.identity.path == ("KnownFacts",),
        "narrative-state identity mapping changed",
    )
    require(
        tuple((fact.subject.path, fact.name, fact.value) for fact in state.facts)
        == (
            (("Ada",), "trusts_borin", "true"),
            (("Ada",), "trusts_borin", "false"),
            (("Ada",), "note", "quoted_fact"),
        ),
        "state-fact order, duplicate names, or scalar text changed",
    )

    continuity = first.continuities[0]
    require(
        continuity.identity.path == ("IdentityLaw",),
        "continuity identity mapping changed",
    )
    require(
        tuple(
            tuple(subject.path for subject in constraint.subjects)
            for constraint in continuity.constraints
        )
        == ((("Ada",),), (("Ada",), ("Borin",))),
        "continuity subject order changed",
    )
    require(
        tuple(
            constraint.assertion
            for constraint in continuity.constraints
        )
        == ("Ada remembers the archive.", "Shared memory."),
        "continuity assertion mapping changed",
    )


def assert_lowering_failure(
    source: str,
    expected_fragment: str,
    expected_offset: int,
) -> None:
    document = parse_narrative_source(
        source,
        source_name="invalid.apex",
    )
    error = require_raises(
        NarrativeSemanticLoweringError,
        lambda: lower_narrative_source(document),
        "unrepresentable source lowered successfully",
    )
    require(
        type(error.diagnostic) is BuildDiagnostic,
        "lowering failure does not carry exact BuildDiagnostic",
    )
    require(
        error.diagnostic.severity == "error"
        and error.diagnostic.stage == "compile"
        and error.diagnostic.code == "APX-NARRATIVE-LOWERING",
        "lowering diagnostic classification changed",
    )
    require(
        expected_fragment in error.diagnostic.message,
        "lowering diagnostic message changed",
    )
    require(
        error.diagnostic.span is not None
        and error.diagnostic.span.source_name == "invalid.apex"
        and error.diagnostic.span.start.offset == expected_offset,
        "lowering diagnostic span changed",
    )
    require(
        str(error) == error.diagnostic.render(),
        "lowering exception rendering changed",
    )


def test_representability_failures_and_traversal_order() -> None:
    bad_label = (
        'story X { choice C { scene S path " bad " '
        '{ destination S } } }'
    )
    assert_lowering_failure(
        bad_label,
        "choice-path label",
        bad_label.index('" bad "'),
    )

    bad_condition = (
        'story X { choice C { scene S path "P" '
        '{ destination S condition "" } } }'
    )
    assert_lowering_failure(
        bad_condition,
        "choice-path condition",
        bad_condition.index('""'),
    )

    bad_state = (
        'story X { narrative_state S { fact A.x = " " } }'
    )
    assert_lowering_failure(
        bad_state,
        "state-fact value",
        bad_state.index('" "'),
    )

    bad_continuity = (
        'story X { continuity C { require A: "" } }'
    )
    assert_lowering_failure(
        bad_continuity,
        "continuity assertion",
        bad_continuity.index('""'),
    )

    ordered_failure = (
        'story X { choice C { scene S path " bad " '
        '{ destination S } } '
        'narrative_state N { fact A.x = "" } }'
    )
    assert_lowering_failure(
        ordered_failure,
        "choice-path label",
        ordered_failure.index('" bad "'),
    )


def test_one_way_boundary_and_frozen_predecessor() -> None:
    module_path = PACKAGE_DIRECTORY / "language" / "narrative_lowering.py"
    text = module_path.read_text(encoding="utf-8")
    tree = ast.parse(text)

    public_classes = {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and not node.name.startswith("_")
    }
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    require(
        public_classes == {"NarrativeSemanticLoweringError"},
        "unexpected public lowering class exposed",
    )
    require(
        public_functions == {"lower_narrative_source"},
        "unexpected public lowering function exposed",
    )

    forbidden = (
        "language.narrative_parser",
        "language.narrative_graph",
        "language.narrative_validation",
        "language.lexer",
        "language.parser",
        "language.compiler",
        "language.project",
        "runtime.",
        "tooling.cli",
        "parse_narrative_source",
        "build_narrative_semantic_graph",
        "validate_narrative_semantic_graph",
    )
    require(
        all(marker not in text for marker in forbidden),
        "lowerer escaped its dedicated semantic boundary",
    )

    for relative in (
        "apexforge/language/narrative_source.py",
        "apexforge/language/narrative_parser.py",
        "apexforge/language/narrative_model.py",
        "apexforge/language/narrative_graph.py",
        "apexforge/language/narrative_validation.py",
        "apexforge/language/source.py",
        "apexforge/language/diagnostics.py",
        "apexforge/language/lexer.py",
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
    test_public_lowering_contract()
    test_complete_lowering_and_determinism()
    test_representability_failures_and_traversal_order()
    test_one_way_boundary_and_frozen_predecessor()
    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "P11.5G-B smoke test mutated repository status")

    print("AFP-P11.5G-B narrative semantic lowering smoke test passed.")
    print("P11.5F annotated freeze and exact predecessor HEAD: PASS")
    print("Exact five-file reviewed candidate ownership: PASS")
    print("Dedicated lowering public API and exact input/output types: PASS")
    print("One-for-one source-to-semantic record mapping: PASS")
    print("Single-segment declared and referenced identity mapping: PASS")
    print("Source order, duplicates, and unresolved-reference retention: PASS")
    print("Scalar text preservation and explicit source-form evidence loss: PASS")
    print("First deterministic APX-NARRATIVE-LOWERING diagnostics: PASS")
    print("No parser, graph, validation, compiler, project, runtime, CLI, or editor integration: PASS")
    print("Frozen P11.5F and operational baseline preservation: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
