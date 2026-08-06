"""Executable P11.5E-B immutable narrative source AST contract."""

from __future__ import annotations

import ast
import subprocess
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

from language.narrative_source import (
    NarrativeSourceCharacter,
    NarrativeSourceChoice,
    NarrativeSourceChoicePath,
    NarrativeSourceContinuity,
    NarrativeSourceContinuityConstraint,
    NarrativeSourceDialogue,
    NarrativeSourceDocument,
    NarrativeSourceIdentifier,
    NarrativeSourcePerspective,
    NarrativeSourceReference,
    NarrativeSourceScalar,
    NarrativeSourceScene,
    NarrativeSourceState,
    NarrativeSourceStateFact,
    NarrativeSourceStory,
    NarrativeSourceTimeline,
)
from language.source import SourcePosition, SourceSpan


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = REPOSITORY_ROOT / "apexforge"
BASELINE_TAG = "afp-p11.5d-freeze"
EXPECTED_HEAD = "c264a2c1f1eb9e1058bc859b78da86c3dad1b28b"
EXPECTED_BRANCH = "p11.5e-narrative-source-syntax"

AUDIT_PATHS = {
    "apexforge/p11_5e_narrative_source_syntax_foundation_architecture_audit_smoke_test.py",
    "docs/p11/P11_5E_NARRATIVE_SOURCE_SYNTAX_FOUNDATION_ARCHITECTURE_AUDIT.md",
}
IMPLEMENTATION_PATHS = {
    "apexforge/language/narrative_source.py",
    "apexforge/p11_5e_immutable_narrative_source_ast_smoke_test.py",
    "docs/p11/P11_5E_IMMUTABLE_NARRATIVE_SOURCE_AST_CONTRACT.md",
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


def span(start: int, end: int) -> SourceSpan:
    return SourceSpan(
        source_name="story.apex",
        start=SourcePosition(line=1, column=start + 1, offset=start),
        end=SourcePosition(line=1, column=end + 1, offset=end),
    )


def identifier(text: str, start: int) -> NarrativeSourceIdentifier:
    return NarrativeSourceIdentifier(text, span(start, start + len(text)))


def reference(
    expected_kind: str,
    text: str,
    start: int,
) -> NarrativeSourceReference:
    return NarrativeSourceReference(
        expected_kind,
        identifier(text, start),
    )


def scalar(
    kind: str,
    text: str,
    start: int,
) -> NarrativeSourceScalar:
    return NarrativeSourceScalar(kind, text, span(start, start + len(text)))


def require_raises(expected_type, operation, message: str) -> None:
    try:
        operation()
    except expected_type:
        return
    raise AssertionError(message)


def test_frozen_baseline_and_exact_reviewed_ownership() -> None:
    require(
        git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "P11.5E-B is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "P11.5E-B predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5D controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip() == EXPECTED_HEAD,
        "P11.5D controlling freeze resolves incorrectly",
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
        "reviewed P11.5E candidate path set changed",
    )


def test_public_source_ast_contract() -> None:
    import language.narrative_source as source_module

    require(
        source_module.__all__
        == (
            "NarrativeSourceIdentifier",
            "NarrativeSourceScalar",
            "NarrativeSourceReference",
            "NarrativeSourceCharacter",
            "NarrativeSourceScene",
            "NarrativeSourceDialogue",
            "NarrativeSourceChoicePath",
            "NarrativeSourceChoice",
            "NarrativeSourcePerspective",
            "NarrativeSourceTimeline",
            "NarrativeSourceStateFact",
            "NarrativeSourceState",
            "NarrativeSourceContinuityConstraint",
            "NarrativeSourceContinuity",
            "NarrativeSourceStory",
            "NarrativeSourceDocument",
        ),
        "P11.5E-B public exports changed",
    )

    require(
        tuple(item.name for item in fields(NarrativeSourceIdentifier))
        == ("text", "span"),
        "NarrativeSourceIdentifier fields changed",
    )
    require(
        tuple(item.name for item in fields(NarrativeSourceScalar))
        == ("kind", "text", "span"),
        "NarrativeSourceScalar fields changed",
    )
    require(
        tuple(item.name for item in fields(NarrativeSourceReference))
        == ("expected_kind", "name"),
        "NarrativeSourceReference fields changed",
    )
    require(
        tuple(item.name for item in fields(NarrativeSourceDocument))
        == ("story", "span"),
        "NarrativeSourceDocument fields changed",
    )

    name = identifier("Ada", 0)
    require_raises(
        FrozenInstanceError,
        lambda: setattr(name, "text", "Borin"),
        "source identifier is mutable",
    )
    require_raises(
        ValueError,
        lambda: NarrativeSourceScalar("boolean", "True", span(0, 4)),
        "non-canonical boolean text accepted",
    )
    require_raises(
        ValueError,
        lambda: NarrativeSourceReference("unknown", name),
        "unsupported reference kind accepted",
    )


def make_document() -> NarrativeSourceDocument:
    ada_name = identifier("Ada", 10)
    borin_name = identifier("Borin", 20)
    arrival_name = identifier("Arrival", 30)
    archive_name = identifier("Archive", 40)

    ada_character = NarrativeSourceCharacter(
        span(0, 9),
        ada_name,
        span(0, 13),
    )
    duplicate_ada = NarrativeSourceCharacter(
        span(14, 23),
        identifier("Ada", 24),
        span(14, 27),
    )
    borin_character = NarrativeSourceCharacter(
        span(28, 37),
        borin_name,
        span(28, 42),
    )

    arrival_scene = NarrativeSourceScene(
        span(43, 48),
        arrival_name,
        span(43, 55),
    )
    archive_scene = NarrativeSourceScene(
        span(56, 61),
        archive_name,
        span(56, 68),
    )

    dialogue = NarrativeSourceDialogue(
        span(69, 77),
        identifier("Warning", 78),
        span(86, 91),
        reference("scene", "Arrival", 92),
        span(100, 107),
        reference("character", "Ada", 108),
        span(112, 124),
        (
            reference("character", "Borin", 125),
            reference("character", "Witness", 131),
            reference("character", "Borin", 139),
        ),
        span(69, 145),
    )

    choice_path = NarrativeSourceChoicePath(
        span(146, 150),
        scalar("string", "Enter", 151),
        span(156, 167),
        reference("scene", "Hidden", 168),
        span(146, 210),
        span(175, 184),
        scalar("identifier", "door_open", 185),
        span(194, 205),
        scalar("identifier", "secret_revealed", 206),
    )
    choice = NarrativeSourceChoice(
        span(222, 228),
        identifier("Decision", 229),
        span(237, 242),
        reference("scene", "Archive", 243),
        (choice_path,),
        span(222, 260),
    )

    perspective = NarrativeSourcePerspective(
        span(261, 272),
        identifier("AdaView", 273),
        span(280, 289),
        reference("character", "Ada", 290),
        span(261, 293),
    )

    timeline = NarrativeSourceTimeline(
        span(294, 302),
        identifier("Main", 303),
        span(307, 313),
        (
            reference("scene", "Arrival", 314),
            reference("scene", "Archive", 322),
            reference("scene", "Arrival", 330),
        ),
        span(294, 337),
    )

    state = NarrativeSourceState(
        span(338, 353),
        identifier("Facts", 354),
        (
            NarrativeSourceStateFact(
                span(359, 363),
                reference("character", "Ada", 364),
                identifier("trusts_borin", 368),
                scalar("boolean", "true", 381),
                span(359, 385),
            ),
            NarrativeSourceStateFact(
                span(386, 390),
                reference("character", "Ada", 391),
                identifier("trusts_borin", 395),
                scalar("boolean", "false", 408),
                span(386, 413),
            ),
        ),
        span(338, 414),
    )

    continuity = NarrativeSourceContinuity(
        span(415, 425),
        identifier("IdentityLaw", 426),
        (
            NarrativeSourceContinuityConstraint(
                span(437, 444),
                (reference("character", "Ada", 445),),
                scalar("string", "Ada remembers the archive.", 449),
                span(437, 475),
            ),
        ),
        span(415, 476),
    )

    story = NarrativeSourceStory(
        span(477, 482),
        identifier("Experimental", 483),
        (ada_character, duplicate_ada, borin_character),
        (arrival_scene, archive_scene),
        (dialogue,),
        (choice,),
        (perspective,),
        (timeline,),
        (state,),
        (continuity,),
        span(477, 600),
    )
    return NarrativeSourceDocument(story, span(477, 600))


def test_order_duplicate_scalar_reference_and_span_preservation() -> None:
    document = make_document()
    story = document.story

    require(
        tuple(item.name.text for item in story.characters)
        == ("Ada", "Ada", "Borin"),
        "character source order or duplicate evidence changed",
    )
    require(
        tuple(item.name.text for item in story.scenes)
        == ("Arrival", "Archive"),
        "scene source order changed",
    )
    require(
        tuple(
            item.name.text
            for item in story.dialogues[0].participants
        )
        == ("Borin", "Witness", "Borin"),
        "participant order or duplicate evidence changed",
    )
    require(
        tuple(item.name.text for item in story.timelines[0].scenes)
        == ("Arrival", "Archive", "Arrival"),
        "timeline order or duplicate evidence changed",
    )
    require(
        tuple(fact.value.text for fact in story.states[0].facts)
        == ("true", "false"),
        "boolean source text changed",
    )
    require(
        all(
            fact.value.kind == "boolean"
            for fact in story.states[0].facts
        ),
        "boolean scalar kinds changed",
    )
    require(
        story.choices[0].paths[0].label.kind == "string"
        and story.choices[0].paths[0].condition.kind == "identifier"
        and story.choices[0].paths[0].consequence.kind == "identifier",
        "choice scalar forms changed",
    )
    require(
        story.choices[0].paths[0].destination.expected_kind == "scene"
        and story.dialogues[0].speaker.expected_kind == "character",
        "unresolved reference kind evidence changed",
    )
    require(
        story.characters[0].name.span.start.offset == 10
        and story.dialogues[0].participants[1].name.span.start.offset == 131
        and story.continuities[0].constraints[0].assertion.span.start.offset == 449,
        "source spans changed",
    )
    require(
        make_document() == document,
        "identical source-AST construction changed equality",
    )


def test_passive_boundary_and_frozen_predecessor_preservation() -> None:
    module_path = PACKAGE_DIRECTORY / "language" / "narrative_source.py"
    text = module_path.read_text(encoding="utf-8")
    tree = ast.parse(text)

    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    require(
        public_functions == set(),
        "source AST module exposes an unexpected public operation",
    )

    forbidden = (
        "BuildDiagnostic",
        "APX-NARRATIVE-",
        "parse_narrative",
        "lower_narrative",
        "build_narrative_semantic_graph",
        "validate_narrative_semantic_graph",
        "language.parser",
        "language.compiler",
        "language.project",
        "runtime.",
        "tooling.cli",
    )
    require(
        all(marker not in text for marker in forbidden),
        "P11.5E-B escaped its passive source-AST boundary",
    )

    for relative in (
        "apexforge/language/source.py",
        "apexforge/language/lexer.py",
        "apexforge/language/parser.py",
        "apexforge/language/compiler.py",
        "apexforge/language/project.py",
        "apexforge/language/narrative_model.py",
        "apexforge/language/narrative_graph.py",
        "apexforge/language/narrative_validation.py",
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
    test_public_source_ast_contract()
    test_order_duplicate_scalar_reference_and_span_preservation()
    test_passive_boundary_and_frozen_predecessor_preservation()
    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "P11.5E-B smoke test mutated repository status")

    print("AFP-P11.5E-B immutable narrative source AST smoke test passed.")
    print("P11.5D annotated freeze and exact predecessor HEAD: PASS")
    print("Exact five-file reviewed candidate ownership: PASS")
    print("Immutable source identifier, scalar, reference, declaration, story, and document records: PASS")
    print("Source order and duplicate retention: PASS")
    print("Identifier, string, boolean, and unresolved-reference evidence: PASS")
    print("Declared-name, reference, scalar, keyword, and complete-node spans: PASS")
    print("No lexer, parser, compiler, project, graph, validation, diagnostic, runtime, or editor integration: PASS")
    print("Frozen narrative and operational baseline preservation: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
