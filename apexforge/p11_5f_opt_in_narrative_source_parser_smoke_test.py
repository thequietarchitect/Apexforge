'''Executable P11.5F-B opt-in narrative source parser contract.'''

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from language.diagnostics import BuildDiagnostic
from language.narrative_parser import (
    NarrativeSourceParseError,
    parse_narrative_source,
)
from language.narrative_source import NarrativeSourceDocument


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = REPOSITORY_ROOT / "apexforge"
BASELINE_TAG = "afp-p11.5e-freeze"
EXPECTED_HEAD = "eba9a27a34563a8df5f77b796c82b032ab2b0485"
EXPECTED_BRANCH = "p11.5f-opt-in-narrative-source-parser"

AUDIT_PATHS = {
    "apexforge/p11_5f_opt_in_narrative_source_parser_architecture_audit_smoke_test.py",
    "docs/p11/P11_5F_OPT_IN_NARRATIVE_SOURCE_PARSER_ARCHITECTURE_AUDIT.md",
}
IMPLEMENTATION_PATHS = {
    "apexforge/language/narrative_parser.py",
    "apexforge/p11_5f_opt_in_narrative_source_parser_smoke_test.py",
    "docs/p11/P11_5F_OPT_IN_NARRATIVE_SOURCE_PARSER_CONTRACT.md",
}
REVIEWED_PATHS = AUDIT_PATHS | IMPLEMENTATION_PATHS

VALID_SOURCE = r'''story ExperimentalContinuity {
    character Ada
    character Ada
    character Borin
    scene Arrival
    scene Archive
    dialogue Warning {
        scene Arrival
        speaker Ada
        participants [Borin, UndeclaredWitness, Borin]
    }
    choice ArchiveDecision {
        scene Archive
        path "Enter the hidden chamber" {
            destination UndeclaredHiddenChamber
            condition door_open
            consequence secret_revealed
        }
        path "Return" {
            destination Arrival
            consequence false
        }
    }
    perspective AdaView {
        viewpoint Ada
    }
    timeline MainTimeline {
        scenes [Arrival, Archive, Arrival]
    }
    narrative_state KnownFacts {
        fact Ada.trusts_borin = true
        fact Ada.trusts_borin = false
        fact Ada.note = "Line one\nLine two"
    }
    continuity IdentityLaw {
        require Ada: "Ada remembers the archive."
        require Ada, Borin: "Shared memory."
    }
}'''


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


def test_baseline_and_ownership() -> None:
    require(
        git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "P11.5F-B is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "P11.5F-B predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5E controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip() == EXPECTED_HEAD,
        "P11.5E controlling freeze resolves incorrectly",
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
        "reviewed P11.5F candidate path set changed",
    )


def test_public_api_and_complete_parse() -> None:
    import language.narrative_parser as parser_module

    require(
        parser_module.__all__
        == ("NarrativeSourceParseError", "parse_narrative_source"),
        "P11.5F-B public exports changed",
    )
    require_raises(
        TypeError,
        lambda: parse_narrative_source(object()),
        "non-string narrative source accepted",
    )
    require_raises(
        TypeError,
        lambda: parse_narrative_source(
            "story X {}",
            source_name=object(),
        ),
        "non-string narrative source name accepted",
    )

    first = parse_narrative_source(
        VALID_SOURCE,
        source_name="story.apex",
    )
    second = parse_narrative_source(
        VALID_SOURCE,
        source_name="story.apex",
    )
    require(
        type(first) is NarrativeSourceDocument,
        "parser did not return exact NarrativeSourceDocument",
    )
    require(first == second, "identical source parsed nondeterministically")
    require(
        first.span.source_name == "story.apex"
        and first.span.start.offset == 0
        and first.span.end.offset == len(VALID_SOURCE),
        "document span changed",
    )

    story = first.story
    require(
        tuple(item.name.text for item in story.characters)
        == ("Ada", "Ada", "Borin"),
        "character order or duplicate evidence changed",
    )
    require(
        tuple(
            item.name.text
            for item in story.dialogues[0].participants
        )
        == ("Borin", "UndeclaredWitness", "Borin"),
        "participant order or duplicate evidence changed",
    )
    require(
        tuple(item.name.text for item in story.timelines[0].scenes)
        == ("Arrival", "Archive", "Arrival"),
        "timeline order or duplicate evidence changed",
    )
    require(
        tuple(fact.value.kind for fact in story.states[0].facts)
        == ("boolean", "boolean", "string"),
        "state scalar kinds changed",
    )
    require(
        tuple(fact.value.text for fact in story.states[0].facts)
        == ("true", "false", "Line one\nLine two"),
        "state scalar values changed",
    )
    require(
        story.choices[0].paths[0].condition.kind == "identifier"
        and story.choices[0].paths[0].consequence.kind == "identifier"
        and story.choices[0].paths[1].consequence.kind == "boolean",
        "choice scalar kinds changed",
    )
    require(
        story.dialogues[0].scene.expected_kind == "scene"
        and story.dialogues[0].speaker.expected_kind == "character"
        and story.choices[0].paths[0].destination.expected_kind == "scene",
        "unresolved-reference kind evidence changed",
    )
    require(
        tuple(
            item.name.text
            for item in story.continuities[0].constraints[1].subjects
        )
        == ("Ada", "Borin"),
        "continuity subject order changed",
    )


def test_source_spans() -> None:
    document = parse_narrative_source(
        VALID_SOURCE,
        source_name="spans.apex",
    )
    story = document.story
    story_name_offset = VALID_SOURCE.index("ExperimentalContinuity")
    witness_offset = VALID_SOURCE.index("UndeclaredWitness")
    hidden_offset = VALID_SOURCE.index("UndeclaredHiddenChamber")
    assertion_offset = VALID_SOURCE.index(
        '"Ada remembers the archive."'
    )

    require(
        story.name.span.start.offset == story_name_offset,
        "story-name span changed",
    )
    require(
        story.dialogues[0].participants[1].name.span.start.offset
        == witness_offset,
        "participant span changed",
    )
    require(
        story.choices[0].paths[0].destination.name.span.start.offset
        == hidden_offset,
        "destination span changed",
    )
    require(
        story.continuities[0].constraints[0].assertion.span.start.offset
        == assertion_offset,
        "continuity assertion span changed",
    )
    require(
        story.keyword_span.start.line == 1
        and story.keyword_span.start.column == 1
        and story.characters[0].keyword_span.start.line == 2,
        "line/column provenance changed",
    )


def assert_syntax_failure(
    source: str,
    fragment: str,
    offset: int,
) -> None:
    error = require_raises(
        NarrativeSourceParseError,
        lambda: parse_narrative_source(
            source,
            source_name="invalid.apex",
        ),
        "invalid source parsed successfully",
    )
    diagnostic = error.diagnostic
    require(
        type(diagnostic) is BuildDiagnostic,
        "syntax failure lacks exact BuildDiagnostic",
    )
    require(
        diagnostic.severity == "error"
        and diagnostic.stage == "parse"
        and diagnostic.code == "APX-NARRATIVE-SYNTAX",
        "syntax diagnostic classification changed",
    )
    require(fragment in diagnostic.message, "syntax message changed")
    require(
        diagnostic.span is not None
        and diagnostic.span.source_name == "invalid.apex"
        and diagnostic.span.start.offset == offset,
        "syntax diagnostic span changed",
    )
    require(
        str(error) == diagnostic.render(),
        "syntax exception rendering changed",
    )


def test_syntax_failures() -> None:
    assert_syntax_failure(
        "",
        "Expected narrative keyword 'story'",
        0,
    )
    missing_path = "story X { choice C { scene S } }"
    assert_syntax_failure(
        missing_path,
        "at least one 'path'",
        missing_path.index("}"),
    )
    empty_list = (
        "story X { dialogue D { scene S speaker A participants [] } }"
    )
    assert_syntax_failure(
        empty_list,
        "Expected an identifier",
        empty_list.index("]"),
    )
    unknown = "story X { unknown Y }"
    assert_syntax_failure(
        unknown,
        "Unknown narrative declaration",
        unknown.index("unknown"),
    )
    extra = "story X {} story Y {}"
    assert_syntax_failure(
        extra,
        "Expected end of source",
        extra.index("story", 1),
    )
    empty_label = (
        'story X { choice C { scene S path "" { destination S } } }'
    )
    assert_syntax_failure(
        empty_label,
        "must not be empty",
        empty_label.index('""'),
    )
    bad_escape = (
        'story X { continuity C { require A: "bad\\q" } }'
    )
    assert_syntax_failure(
        bad_escape,
        "Unsupported narrative string escape",
        bad_escape.index("\\q"),
    )


def test_dedicated_boundary_and_frozen_files() -> None:
    parser_path = PACKAGE_DIRECTORY / "language" / "narrative_parser.py"
    text = parser_path.read_text(encoding="utf-8")
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
        public_classes == {"NarrativeSourceParseError"},
        "unexpected public parser class exposed",
    )
    require(
        public_functions == {"parse_narrative_source"},
        "unexpected public parser function exposed",
    )
    forbidden = (
        "language.lexer",
        "language.parser",
        "language.compiler",
        "language.project",
        "language.narrative_model",
        "language.narrative_graph",
        "language.narrative_validation",
        "runtime.",
        "tooling.cli",
        "build_narrative_semantic_graph",
        "validate_narrative_semantic_graph",
    )
    require(
        all(marker not in text for marker in forbidden),
        "opt-in parser escaped its parsing boundary",
    )

    for relative in (
        "apexforge/language/narrative_source.py",
        "apexforge/language/source.py",
        "apexforge/language/diagnostics.py",
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
    test_baseline_and_ownership()
    test_public_api_and_complete_parse()
    test_source_spans()
    test_syntax_failures()
    test_dedicated_boundary_and_frozen_files()
    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "P11.5F-B smoke test mutated repository status")

    print("AFP-P11.5F-B opt-in narrative source parser smoke test passed.")
    print("P11.5E annotated freeze and exact predecessor HEAD: PASS")
    print("Exact five-file reviewed candidate ownership: PASS")
    print("Dedicated parser public API and type boundaries: PASS")
    print("Complete narrative grammar parsing: PASS")
    print("Source order and duplicate retention: PASS")
    print("Identifier, string, boolean, and unresolved-reference evidence: PASS")
    print("Document, story, keyword, name, field, reference, scalar, and block spans: PASS")
    print("First deterministic APX-NARRATIVE-SYNTAX diagnostics: PASS")
    print("No ordinary lexer/parser, semantic, graph, validation, compiler, project, runtime, CLI, or editor integration: PASS")
    print("Frozen P11.5E and operational baseline preservation: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
