"""Executable P11.5C-B Narrative Semantic Graph construction contract."""

from __future__ import annotations

import ast
import subprocess
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

from language.narrative_graph import (
    NarrativeGraphEdge,
    NarrativeGraphNode,
    NarrativeSemanticGraph,
    build_narrative_semantic_graph,
)
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


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = REPOSITORY_ROOT / "apexforge"
BASELINE_TAG = "afp-p11.2i-freeze"
SEMANTIC_PREDECESSOR_TAG = "afp-p11.5b-freeze"
EXPECTED_BRANCH = "p11.5c-narrative-semantic-graph"
P11_5C_A_OWNED_PATHS = {
    "apexforge/p11_5c_narrative_semantic_graph_construction_architecture_audit_smoke_test.py",
    "docs/p11/P11_5C_NARRATIVE_SEMANTIC_GRAPH_CONSTRUCTION_ARCHITECTURE_AUDIT.md",
}
P11_5C_B_OWNED_PATHS = {
    "apexforge/language/narrative_graph.py",
    "apexforge/p11_5c_narrative_semantic_graph_construction_smoke_test.py",
    "docs/p11/P11_5C_NARRATIVE_SEMANTIC_GRAPH_CONSTRUCTION_CONTRACT.md",
}
REVIEWED_PATHS = P11_5C_A_OWNED_PATHS | P11_5C_B_OWNED_PATHS


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_git(*arguments: str) -> str:
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


def test_freeze_identity_and_candidate_ownership() -> None:
    require(
        run_git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.2I controlling freeze is not annotated",
    )
    require(
        run_git("cat-file", "-t", SEMANTIC_PREDECESSOR_TAG).strip() == "tag",
        "P11.5B semantic predecessor freeze is not annotated",
    )
    require(
        subprocess.run(
            (
                "git",
                "merge-base",
                "--is-ancestor",
                SEMANTIC_PREDECESSOR_TAG,
                BASELINE_TAG,
            ),
            cwd=REPOSITORY_ROOT,
        ).returncode
        == 0,
        "P11.5B is no longer an ancestor of the P11.2I integration freeze",
    )
    require(
        run_git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "P11.5C is running on an unexpected branch",
    )

    committed = {
        item
        for item in run_git(
            "diff", "--name-only", f"{BASELINE_TAG}..HEAD"
        ).splitlines()
        if item
    }
    working = {
        line[3:].replace("\\", "/")
        for line in run_git(
            "status", "--porcelain=v1", "--untracked-files=all"
        ).splitlines()
        if len(line) >= 4
        and not line[3:].replace("\\", "/").startswith(
            "examples/P11Validation/"
        )
    }
    require(
        committed | working == REVIEWED_PATHS,
        "P11.5C candidate ownership is not the exact reviewed five paths",
    )
    require(
        all((REPOSITORY_ROOT / item).is_file() for item in REVIEWED_PATHS),
        "a reviewed P11.5C file is missing",
    )


def test_public_graph_model_contract() -> None:
    import language.narrative_graph as graph_module

    require(
        graph_module.__all__
        == (
            "NarrativeGraphNode",
            "NarrativeGraphEdge",
            "NarrativeSemanticGraph",
            "build_narrative_semantic_graph",
        ),
        "public graph exports changed",
    )
    require(
        tuple(item.name for item in fields(NarrativeGraphNode))
        == ("identity", "declared"),
        "NarrativeGraphNode fields changed",
    )
    require(
        tuple(item.name for item in fields(NarrativeGraphEdge))
        == ("relation", "source", "target", "evidence"),
        "NarrativeGraphEdge fields changed",
    )
    require(
        tuple(item.name for item in fields(NarrativeSemanticGraph))
        == ("story", "nodes", "edges"),
        "NarrativeSemanticGraph fields changed",
    )

    story_id = identity("story", "Story")
    story_node = NarrativeGraphNode(story_id, True)
    require_raises(
        FrozenInstanceError,
        lambda: setattr(story_node, "declared", False),
        "graph node is mutable",
    )
    require_raises(
        TypeError,
        lambda: NarrativeGraphNode(story_id, 1),
        "non-bool declared flag accepted",
    )
    require_raises(
        ValueError,
        lambda: NarrativeGraphEdge("unknown", story_id, story_id),
        "unknown graph relation accepted",
    )
    edge = NarrativeGraphEdge(
        "contains",
        story_id,
        identity("scene", "Scene"),
        (("z", "last"), ("a", "first")),
    )
    require(
        edge.evidence == (("a", "first"), ("z", "last")),
        "edge evidence was not canonically ordered",
    )
    require_raises(
        ValueError,
        lambda: NarrativeGraphEdge(
            "contains",
            story_id,
            story_id,
            (("a", "1"), ("a", "2")),
        ),
        "duplicate evidence keys accepted",
    )


def make_story() -> NarrativeStory:
    story_id = identity("story", "Atlas")
    ada = identity("character", "Ada")
    borin = identity("character", "Borin")
    witness = identity("character", "Witness")
    gate = identity("scene", "Gate")
    archive = identity("scene", "Archive")
    ending = identity("scene", "Ending")
    dialogue_id = identity("dialogue", "Warning")
    choice_id = identity("choice", "Crossroads")
    perspective_id = identity("perspective", "AdaView")
    timeline_id = identity("timeline", "Main")
    state_id = identity("narrative_state", "KnownFacts")
    continuity_id = identity("continuity", "IdentityLaw")

    return NarrativeStory(
        story_id,
        (
            NarrativeCharacter(ada),
            NarrativeCharacter(ada),
            NarrativeCharacter(borin),
        ),
        (
            NarrativeScene(gate),
            NarrativeScene(archive),
        ),
        (
            NarrativeDialogue(
                dialogue_id,
                gate,
                ada,
                (borin, witness, borin),
            ),
        ),
        (
            NarrativeChoice(
                choice_id,
                gate,
                (
                    NarrativeChoicePath(
                        "Enter",
                        archive,
                        "gate_open",
                        "archive_reached",
                    ),
                    NarrativeChoicePath("Leave", ending),
                ),
            ),
        ),
        (NarrativePerspective(perspective_id, ada),),
        (NarrativeTimeline(timeline_id, (gate, archive, ending)),),
        (
            NarrativeState(
                state_id,
                (
                    NarrativeStateFact(ada, "Mood", "Calm"),
                    NarrativeStateFact(witness, "Known", "false"),
                ),
            ),
        ),
        (
            NarrativeContinuity(
                continuity_id,
                (
                    NarrativeContinuityConstraint(
                        (ada, witness),
                        "Identity remains stable",
                    ),
                ),
            ),
        ),
    )


def test_deterministic_projection_and_duplicate_evidence() -> None:
    story = make_story()
    first = build_narrative_semantic_graph(story)
    second = build_narrative_semantic_graph(story)
    require(first == second, "identical narrative input changed graph output")
    require(
        first.nodes[0] == NarrativeGraphNode(story.identity, True),
        "story is not the first graph node",
    )

    ada = identity("character", "Ada")
    witness = identity("character", "Witness")
    ending = identity("scene", "Ending")
    require(
        sum(node == NarrativeGraphNode(ada, True) for node in first.nodes) == 2,
        "duplicate declared character evidence was collapsed",
    )
    require(
        sum(
            node == NarrativeGraphNode(witness, False)
            for node in first.nodes
        )
        == 1,
        "referenced-only identity was not appended exactly once",
    )
    require(
        sum(node == NarrativeGraphNode(ending, False) for node in first.nodes)
        == 1,
        "referenced-only destination was not appended",
    )

    relations = tuple(edge.relation for edge in first.edges)
    declared_count = (
        len(story.characters)
        + len(story.scenes)
        + len(story.dialogues)
        + len(story.choices)
        + len(story.perspectives)
        + len(story.timelines)
        + len(story.states)
        + len(story.continuities)
    )
    require(
        relations[:declared_count] == ("contains",) * declared_count,
        "declaration containment is not the first relation family",
    )
    require(
        relations.count("participant") == 3,
        "participant duplicates or ordering were lost",
    )
    require(
        relations.count("leads_to") == 2,
        "choice path evidence was not projected",
    )
    require(
        relations.count("precedes") == 2,
        "timeline adjacency was not projected",
    )
    require(
        relations.count("state_subject") == 2,
        "narrative-state fact evidence was not projected",
    )
    require(
        relations.count("continuity_subject") == 2,
        "continuity subject evidence was not projected",
    )

    enter = next(
        edge
        for edge in first.edges
        if edge.relation == "leads_to"
        and dict(edge.evidence)["label"] == "Enter"
    )
    require(
        dict(enter.evidence)
        == {
            "condition": "gate_open",
            "consequence": "archive_reached",
            "index": "0",
            "label": "Enter",
        },
        "choice-path evidence changed",
    )


def test_passive_boundary_and_baseline_preservation() -> None:
    module_path = PACKAGE_DIRECTORY / "language" / "narrative_graph.py"
    model_path = PACKAGE_DIRECTORY / "language" / "narrative_model.py"
    text = module_path.read_text(encoding="utf-8")
    tree = ast.parse(text)

    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    require(
        public_functions == {"build_narrative_semantic_graph"},
        "graph module exposes an unexpected public operation",
    )

    forbidden = (
        "BuildDiagnostic",
        "APX-NARRATIVE-",
        "APX-STORY-",
        "APX-CONTINUITY-",
        "parse_",
        "AIRProgram",
        "artifact",
        "execute",
        "serialize",
        "language.project",
        "language.parser",
        "runtime.",
    )
    require(
        all(marker not in text for marker in forbidden),
        "P11.5C escaped its passive graph-construction boundary",
    )

    baseline_model = run_git(
        "show", f"{BASELINE_TAG}:apexforge/language/narrative_model.py"
    ).encode("utf-8")
    require(
        model_path.read_bytes() == baseline_model,
        "P11.5B narrative_model.py changed",
    )
    for relative in (
        "apexforge/language/parser.py",
        "apexforge/language/compiler.py",
        "apexforge/language/project.py",
        "apexforge/air/model.py",
        "apexforge/air/serialization.py",
        "apexforge/runtime/engine.py",
        "apexforge/tooling/cli.py",
    ):
        path = REPOSITORY_ROOT / relative
        baseline = run_git("show", f"{BASELINE_TAG}:{relative}").encode("utf-8")
        require(
            path.read_bytes() == baseline,
            f"operational baseline file changed: {relative}",
        )


def main() -> None:
    before = run_git("status", "--porcelain=v1", "--untracked-files=all")
    test_freeze_identity_and_candidate_ownership()
    test_public_graph_model_contract()
    test_deterministic_projection_and_duplicate_evidence()
    test_passive_boundary_and_baseline_preservation()
    after = run_git("status", "--porcelain=v1", "--untracked-files=all")
    require(before == after, "P11.5C-B smoke test mutated repository status")

    print("AFP-P11.5C-B Narrative Semantic Graph construction smoke test passed.")
    print("P11.2I controlling freeze and P11.5B semantic ancestry: PASS")
    print("Exact five-file reviewed candidate ownership: PASS")
    print("Immutable node, edge, graph, and builder API: PASS")
    print("Deterministic family/source ordering and duplicate retention: PASS")
    print("Referenced-only identity projection: PASS")
    print("Choice, timeline, state, and continuity evidence: PASS")
    print("No parser, compiler, runtime, diagnostic, artifact, or CLI integration: PASS")
    print("P11.5B and operational baseline preservation: PASS")


if __name__ == "__main__":
    main()
