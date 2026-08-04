"""Executable architecture contract for the P11.5A narrative audit."""

from __future__ import annotations

import ast
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from language.grammar import GRAMMAR_KEYWORD_TOKENS, TOP_LEVEL_DECLARATIONS
from language.lexer import KEYWORDS
from p11_4d_passive_resolver_candidate_index_smoke_test import (
    repository_bytecode_state,
    repository_status,
)
from p11_4h_contextual_resolution_outcome_classification_smoke_test import (
    test_project_generics_air_artifact_and_compatibility as accepted_compatibility,
)


PACKAGE_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_DIRECTORY.parent
AUDIT_DOCUMENT = (
    REPOSITORY_ROOT
    / "docs"
    / "p11"
    / "P11_5A_NARRATIVE_SEMANTIC_FOUNDATION_ARCHITECTURE_AUDIT.md"
)
BASELINE_COMMIT = "c6570766703d00bba4e1aff7d712a0d271c9ecc1"
BASELINE_TAG = "afp-p11.4h-freeze"
BASELINE_TAG_OBJECT = "e8f8ed425f0ef265bdc9842b8abc5ecd96b2c78a"
AUTHORIZED_PATHS = {
    "apexforge/p11_5a_narrative_semantic_foundation_architecture_audit_smoke_test.py",
    "docs/p11/P11_5A_NARRATIVE_SEMANTIC_FOUNDATION_ARCHITECTURE_AUDIT.md",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_lines(*arguments: str) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    require(completed.stderr == "", f"git {' '.join(arguments)} wrote stderr")
    return tuple(line for line in completed.stdout.splitlines() if line)


def changed_paths_since_baseline() -> set[str]:
    paths: set[str] = set()
    for arguments in (
        ("diff", "--name-only", f"{BASELINE_COMMIT}..HEAD"),
        ("diff", "--name-only"),
        ("diff", "--cached", "--name-only"),
        ("ls-files", "--others", "--exclude-standard"),
    ):
        paths.update(git_lines(*arguments))
    return paths


def production_python_files() -> tuple[Path, ...]:
    paths = []
    for path in PACKAGE_DIRECTORY.rglob("*.py"):
        if path.name.endswith("_smoke_test.py") or "tests" in path.parts:
            continue
        paths.append(path)
    return tuple(sorted(paths))


def test_frozen_baseline_and_exact_ownership(document: str) -> None:
    normalized = " ".join(document.split())
    require(BASELINE_COMMIT in document, "audit omits the exact P11.4H commit")
    require(BASELINE_TAG in document, "audit omits the controlling freeze tag")
    require(
        BASELINE_TAG_OBJECT in document,
        "audit omits the exact controlling tag-object identity",
    )
    require(
        "P11.4H remains the frozen predecessor" in normalized,
        "audit does not identify P11.4H as its frozen predecessor",
    )
    require(
        "P11.5A is the first P11.5 stage" in normalized,
        "audit does not identify P11.5A as the first P11.5 stage",
    )
    require(
        git_lines("cat-file", "-t", BASELINE_TAG) == ("tag",),
        "controlling freeze is not an annotated tag",
    )
    require(
        git_lines("rev-parse", BASELINE_TAG) == (BASELINE_TAG_OBJECT,),
        "controlling freeze tag object changed",
    )
    require(
        git_lines("rev-list", "-n", "1", BASELINE_TAG) == (BASELINE_COMMIT,),
        "controlling freeze no longer peels to P11.4H",
    )
    require(
        changed_paths_since_baseline() == AUTHORIZED_PATHS,
        "P11.5A changed a path outside its one test and one document",
    )
    require(
        all(path.exists() for path in (Path(__file__), AUDIT_DOCUMENT)),
        "a P11.5A audit-owned file is missing",
    )


def test_roadmap_vocabulary_and_validation_responsibilities(document: str) -> None:
    require(
        "P11.5  Rich Storytelling Semantic Foundation" in document,
        "audit omits the exact P11.5 roadmap title",
    )
    terms = (
        "story",
        "character",
        "scene",
        "dialogue",
        "choice",
        "perspective",
        "timeline",
        "narrative state",
        "continuity",
    )
    lowered = document.casefold()
    require(
        all(term in lowered for term in terms),
        "audit omits a minimum narrative semantic term",
    )
    require(
        "Narrative Semantic Graph" in document
        and "not decorative text" in lowered,
        "audit does not establish semantic graph treatment",
    )
    responsibilities = (
        "impossible timelines",
        "characters knowing unrevealed information",
        "broken scene dependencies",
        "contradictory identities",
        "missing dialogue participants",
        "unreachable choices",
        "unresolved narrative references",
        "accidental continuity changes",
    )
    require(
        all(item in lowered for item in responsibilities),
        "audit omits a roadmap validation responsibility",
    )


def test_architecture_boundaries_and_determinism(document: str) -> None:
    required_separations = (
        "story structure != rendered prose",
        "character identity != character state",
        "character knowledge != compiler knowledge",
        "scene ordering != runtime scheduling",
        "dialogue semantics != plain string storage",
        "choice branching != automatic branch selection",
        "perspective != global truth",
        "timeline != wall-clock execution",
        "narrative state != runtime state",
        "continuity validation != narrative generation",
        "Narrative Semantic Graph != AIR",
        "Narrative Semantic Graph != artifact v1",
    )
    require(
        all(item in document for item in required_separations),
        "audit omits a required semantic separation",
    )
    relation_families = (
        "narrative containment",
        "identity participation",
        "temporal ordering",
        "scene dependency",
        "dialogue participation",
        "knowledge and revelation",
        "choice branching and reachability",
        "narrative-state transition",
        "perspective",
        "continuity constraints",
    )
    lowered = document.casefold()
    require(
        all(item in lowered for item in relation_families),
        "audit omits a Narrative Semantic Graph relation family",
    )
    determinism_evidence = (
        "identical narrative semantic input",
        "object addresses",
        "hash-table iteration",
        "source ordering",
        "canonical identity",
        "contradictory narrative identities",
        "probabilistic resolution",
    )
    require(
        all(item in lowered for item in determinism_evidence),
        "audit omits a deterministic graph constraint",
    )
    require(
        "P11.5B  Minimal Narrative Semantic Model Contract" in document
        and "P11.5B is proposed only" in document,
        "audit improperly defines or begins P11.5B",
    )


def test_no_storytelling_syntax_records_graph_or_diagnostics() -> None:
    narrative_keywords = {"story", "character", "scene", "dialogue", "choice"}
    require(
        narrative_keywords.isdisjoint(KEYWORDS)
        and narrative_keywords.isdisjoint(GRAMMAR_KEYWORD_TOKENS)
        and narrative_keywords.isdisjoint(TOP_LEVEL_DECLARATIONS),
        "P11.5A introduced a storytelling keyword or grammar declaration",
    )
    forbidden_names = {
        "NarrativeSemanticGraph",
        "StoryDeclaration",
        "CharacterDeclaration",
        "SceneDeclaration",
        "DialogueDeclaration",
        "ChoiceDeclaration",
        "ContinuityValidator",
        "NarrativeDiagnostic",
    }
    declared_names: set[str] = set()
    production_text = []
    for path in production_python_files():
        text = path.read_text(encoding="utf-8")
        production_text.append(text)
        tree = ast.parse(text, filename=str(path))
        declared_names.update(
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        )
    combined = "\n".join(production_text)
    require(
        forbidden_names.isdisjoint(declared_names),
        "a forbidden narrative production declaration exists",
    )
    require(
        "APX-NARRATIVE-" not in combined,
        "a narrative diagnostic code exists in production",
    )
    parser_text = (PACKAGE_DIRECTORY / "language" / "parser.py").read_text(
        encoding="utf-8"
    )
    require(
        all(f"parse_{keyword}" not in parser_text for keyword in narrative_keywords),
        "a storytelling grammar parser path exists",
    )
    integration_markers = (
        "NarrativeSemanticGraph",
        "StoryDeclaration",
        "CharacterDeclaration",
        "SceneDeclaration",
        "DialogueDeclaration",
        "ChoiceDeclaration",
    )
    project_text = (PACKAGE_DIRECTORY / "language" / "project.py").read_text(
        encoding="utf-8"
    )
    require(
        all(marker not in project_text for marker in integration_markers),
        "project construction acquired automatic narrative integration",
    )


def test_temporary_fixture_and_accepted_compatibility() -> None:
    original_directory = Path.cwd().resolve()
    temporary_path: Path
    with TemporaryDirectory(prefix="apexforge-p11-5a-") as temporary:
        temporary_path = Path(temporary).resolve()
        try:
            temporary_path.relative_to(REPOSITORY_ROOT.resolve())
        except ValueError:
            pass
        else:
            raise AssertionError("temporary fixture was created in the repository")
        require(
            Path.cwd().resolve() == original_directory,
            "temporary audit fixture changed the working directory",
        )
    require(
        not temporary_path.exists() and Path.cwd().resolve() == original_directory,
        "temporary audit fixture escaped its context manager",
    )
    accepted_compatibility()


def main() -> None:
    original_directory = Path.cwd().resolve()
    status_before = repository_status()
    bytecode_before = repository_bytecode_state()
    document = AUDIT_DOCUMENT.read_text(encoding="utf-8")

    def forbidden_network(*_args, **_kwargs):
        raise AssertionError("P11.5A attempted network access")

    with patch("socket.create_connection", side_effect=forbidden_network), patch(
        "socket.socket", side_effect=forbidden_network
    ):
        test_frozen_baseline_and_exact_ownership(document)
        test_roadmap_vocabulary_and_validation_responsibilities(document)
        test_architecture_boundaries_and_determinism(document)
        test_no_storytelling_syntax_records_graph_or_diagnostics()
        test_temporary_fixture_and_accepted_compatibility()

    require(Path.cwd().resolve() == original_directory, "working directory changed")
    require(repository_status() == status_before, "running the test changed Git status")
    require(
        repository_bytecode_state() == bytecode_before,
        "running the test changed repository bytecode state",
    )
    print("AFP-P11.5A narrative semantic foundation audit smoke test passed.")
    print("Frozen P11.4H predecessor and exact two-file ownership: PASS")
    print("Nine-term narrative vocabulary and validation responsibilities: PASS")
    print("Graph relation families, semantic separations, and determinism: PASS")
    print("No syntax, records, graph, diagnostics, or project integration: PASS")
    print("P11.4H operational compatibility reuse: PASS")
    print("Network, temporary fixture, Git, working directory, and bytecode: PASS")


if __name__ == "__main__":
    main()
