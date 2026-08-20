"""P11-TAM-H narrative semantic evidence trace production."""

from __future__ import annotations

from pathlib import Path
import subprocess

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
from language.narrative_validation import (
    NarrativeValidationFinding,
    NarrativeValidationReport,
    validate_narrative_semantic_graph,
)
from tam import (
    TraceDomain,
    TraceMap,
    trace_map_from_narrative_evidence,
    trace_record_from_narrative_evidence,
)


PREDECESSOR_TAG = "afp-p11-tam-g-freeze"
PREDECESSOR_COMMIT = "c3043f8d7e1f37ed05f0a86a5b6b5613d7b1263b"


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


def _expect(exc_type, operation):
    try:
        operation()
    except exc_type as error:
        return error
    raise AssertionError("Expected {}.".format(exc_type.__name__))


def _fixture():
    story_id = NarrativeIdentity("story", ("Chronicle",))
    hero = NarrativeIdentity("character", ("Hero",))
    guide = NarrativeIdentity("character", ("Guide",))
    start = NarrativeIdentity("scene", ("Start",))
    ending = NarrativeIdentity("scene", ("Ending",))
    dialogue_id = NarrativeIdentity("dialogue", ("Greeting",))
    choice_id = NarrativeIdentity("choice", ("Advance",))
    perspective_id = NarrativeIdentity("perspective", ("HeroView",))
    timeline_id = NarrativeIdentity("timeline", ("Mainline",))
    state_id = NarrativeIdentity("narrative_state", ("WorldState",))
    continuity_id = NarrativeIdentity("continuity", ("CoreContinuity",))

    characters = (
        NarrativeCharacter(hero),
        NarrativeCharacter(guide),
    )
    scenes = (
        NarrativeScene(start, "The Beginning", "A door waits."),
        NarrativeScene(ending, "The Ending", "The path continues."),
    )
    dialogue = NarrativeDialogue(
        dialogue_id,
        start,
        guide,
        (hero, guide),
        "The way is open.",
    )
    path = NarrativeChoicePath(
        "Continue",
        ending,
        condition="ready",
        consequence="advance",
    )
    choice = NarrativeChoice(choice_id, start, (path,))
    perspective = NarrativePerspective(perspective_id, hero)
    timeline = NarrativeTimeline(timeline_id, (start, ending))
    fact_ready = NarrativeStateFact(hero, "status", "ready")
    fact_blocked = NarrativeStateFact(hero, "status", "blocked")
    state = NarrativeState(state_id, (fact_ready, fact_blocked))
    constraint = NarrativeContinuityConstraint(
        (hero, guide),
        "The guide remembers the hero.",
    )
    continuity = NarrativeContinuity(continuity_id, (constraint,))
    story = NarrativeStory(
        story_id,
        characters,
        scenes,
        (dialogue,),
        (choice,),
        (perspective,),
        (timeline,),
        (state,),
        (continuity,),
    )

    # Frozen P11.5 owners produce real graph/validation evidence for the fixture.
    graph = build_narrative_semantic_graph(story)
    report = validate_narrative_semantic_graph(graph)

    model_evidence = (
        story_id,
        characters[0],
        scenes[0],
        dialogue,
        path,
        choice,
        perspective,
        timeline,
        fact_ready,
        state,
        constraint,
        continuity,
        story,
    )
    graph_evidence = graph.nodes + graph.edges + (graph,)
    validation_evidence = report.findings + (report,)
    evidence = model_evidence + graph_evidence + validation_evidence

    return (
        evidence,
        story,
        graph,
        report,
        scenes[0],
        path,
        fact_ready,
    )


def _assert_predecessor() -> None:
    tag = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(tag.returncode == 0, tag.stderr.strip())
    _require(
        tag.stdout.strip() == PREDECESSOR_COMMIT,
        "TAM-G freeze target changed",
    )
    ancestry = _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD")
    _require(ancestry.returncode == 0, "TAM-G is not an ancestor of TAM-H")


def _assert_supported_projection() -> None:
    evidence, _, _, _, _, _, _ = _fixture()

    first = tuple(
        trace_record_from_narrative_evidence(value, evidence_index=index)
        for index, value in enumerate(evidence)
    )
    second = tuple(
        trace_record_from_narrative_evidence(value, evidence_index=index)
        for index, value in enumerate(evidence)
    )
    _require(first == second, "same narrative evidence produced different records")

    for record in first:
        _require(
            record.domain == TraceDomain("narrative"),
            "narrative evidence escaped narrative domain",
        )
        _require(
            record.canonical_identity is None,
            "TAM fabricated string identity for tuple-based narrative identity",
        )
        _require(
            record.source_span is None,
            "semantic narrative evidence fabricated SourceSpan",
        )
        _require(
            record.provenance == (),
            "narrative evidence fabricated TAM provenance",
        )
        _require(
            record.upstream_trace_ids == ()
            and record.downstream_trace_ids == (),
            "narrative evidence fabricated TAM graph links",
        )

    owners = {record.owner for record in first}
    _require(
        owners
        == {
            "language.narrative_model",
            "language.narrative_graph",
            "language.narrative_validation",
        },
        "narrative evidence owner boundary changed",
    )


def _assert_semantic_content_preserved() -> None:
    _, _, _, _, scene, path, fact = _fixture()

    changed_scene = NarrativeScene(
        scene.identity,
        scene.title,
        "Different body.",
    )
    _require(
        trace_record_from_narrative_evidence(
            scene,
            evidence_index=0,
        ).trace_id
        != trace_record_from_narrative_evidence(
            changed_scene,
            evidence_index=0,
        ).trace_id,
        "scene prose was not preserved",
    )

    changed_path = NarrativeChoicePath(
        path.label,
        path.destination,
        condition="different",
        consequence=path.consequence,
    )
    _require(
        trace_record_from_narrative_evidence(
            path,
            evidence_index=0,
        ).trace_id
        != trace_record_from_narrative_evidence(
            changed_path,
            evidence_index=0,
        ).trace_id,
        "choice-path semantics were not preserved",
    )

    changed_fact = NarrativeStateFact(
        fact.subject,
        fact.name,
        "different",
    )
    _require(
        trace_record_from_narrative_evidence(
            fact,
            evidence_index=0,
        ).trace_id
        != trace_record_from_narrative_evidence(
            changed_fact,
            evidence_index=0,
        ).trace_id,
        "narrative state fact was not preserved",
    )


def _assert_graph_and_validation_are_consumed() -> None:
    _, _, graph, report, _, _, _ = _fixture()

    graph_record = trace_record_from_narrative_evidence(
        graph,
        evidence_index=0,
    )
    report_record = trace_record_from_narrative_evidence(
        report,
        evidence_index=1,
    )
    _require(
        graph_record.owner == "language.narrative_graph",
        "semantic graph ownership changed",
    )
    _require(
        report_record.owner == "language.narrative_validation",
        "validation report ownership changed",
    )

    alternate_graph = NarrativeSemanticGraph(
        graph.story,
        graph.nodes,
        tuple(reversed(graph.edges)),
    )
    _require(
        trace_record_from_narrative_evidence(
            graph,
            evidence_index=0,
        ).trace_id
        != trace_record_from_narrative_evidence(
            alternate_graph,
            evidence_index=0,
        ).trace_id
        if len(graph.edges) > 1
        else True,
        "graph edge order was not preserved",
    )

    if report.findings:
        finding = report.findings[0]
        _require(
            type(finding) is NarrativeValidationFinding,
            "frozen validator did not return canonical finding evidence",
        )
        _require(
            trace_record_from_narrative_evidence(
                finding,
                evidence_index=0,
            ).owner
            == "language.narrative_validation",
            "validation finding ownership changed",
        )


def _assert_map_projection() -> None:
    evidence, _, _, _, _, _, _ = _fixture()

    first = trace_map_from_narrative_evidence(evidence)
    second = trace_map_from_narrative_evidence(evidence)
    _require(type(first) is TraceMap, "narrative evidence did not return TraceMap")
    _require(first == second, "same narrative evidence produced different maps")
    _require(
        first.records
        == tuple(
            trace_record_from_narrative_evidence(
                value,
                evidence_index=index,
            )
            for index, value in enumerate(evidence)
        ),
        "narrative evidence input order changed",
    )
    _require(
        trace_map_from_narrative_evidence(()).records == (),
        "empty narrative evidence fabricated records",
    )


def _assert_no_narrative_execution() -> None:
    text = (_root() / "apexforge/tam/production.py").read_text(encoding="utf-8")
    forbidden = (
        "build_narrative_semantic_graph(",
        "validate_narrative_semantic_graph(",
        "lower_narrative_source(",
        "parse_narrative_source(",
        "analyze_narrative_source(",
        "analyze_narrative_project_sources(",
        "NarrativeExecutionState",
        "NarrativeExecutionResult",
        "NarrativeChoiceEvidence",
        "NarrativeExecutionTraceEvent",
        "NarrativeSession",
        "NarrativeSessionMaterial",
        "NarrativeSessionPresentation",
        "create_narrative_session(",
        "step_narrative_session(",
        "terminate_narrative_session(",
        "narrative_session_presentation(",
        "render_narrative_session(",
        "interact_narrative_session(",
        "load_narrative_execution_material(",
        "load_narrative_session_material(",
        "write_narrative_session_atomic(",
        "runtime.narrative_",
        "tooling.narrative_",
    )
    for token in forbidden:
        _require(
            token not in text,
            "TAM-H acquired operative narrative behavior: " + token,
        )


def _assert_source_ast_boundary() -> None:
    text = (_root() / "apexforge/tam/production.py").read_text(encoding="utf-8")
    _require(
        "NarrativeSource" not in text,
        "TAM-H duplicated narrative source-AST ownership",
    )


def _assert_type_guards() -> None:
    evidence, _, _, _, _, _, _ = _fixture()

    _expect(
        TypeError,
        lambda: trace_record_from_narrative_evidence(
            object(),
            evidence_index=0,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_record_from_narrative_evidence(
            evidence[0],
            evidence_index=True,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_map_from_narrative_evidence(list(evidence)),
    )


def _assert_frozen_owners_unchanged() -> None:
    paths = (
        "apexforge/tam/model.py",
        "apexforge/language/narrative_model.py",
        "apexforge/language/narrative_graph.py",
        "apexforge/language/narrative_validation.py",
        "apexforge/language/narrative_source.py",
        "apexforge/language/narrative_parser.py",
        "apexforge/language/narrative_lowering.py",
        "apexforge/language/narrative_analysis.py",
        "apexforge/language/narrative_project_analysis.py",
        "apexforge/runtime/narrative_binding.py",
        "apexforge/runtime/narrative_execution.py",
        "apexforge/runtime/narrative_observability.py",
        "apexforge/runtime/narrative_transition.py",
        "apexforge/tooling/narrative_artifact.py",
        "apexforge/tooling/narrative_execution.py",
        "apexforge/tooling/narrative_interactive.py",
        "apexforge/tooling/narrative_project.py",
        "apexforge/tooling/narrative_rendering.py",
        "apexforge/tooling/narrative_session.py",
        "apexforge/semantic_lattice/adapters.py",
        "apexforge/language/compiler.py",
        "apexforge/tooling/cli.py",
        "apexforge/language_server/diagnostics.py",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "TAM-H mutated frozen narrative owner")


def main() -> None:
    _assert_predecessor()
    _assert_supported_projection()
    _assert_semantic_content_preserved()
    _assert_graph_and_validation_are_consumed()
    _assert_map_projection()
    _assert_no_narrative_execution()
    _assert_source_ast_boundary()
    _assert_type_guards()
    _assert_frozen_owners_unchanged()

    print("P11_TAM_G_FREEZE_ANCESTRY=PASS")
    print("NARRATIVE_MODEL_EVIDENCE_CONSUMPTION=PASS")
    print("NARRATIVE_GRAPH_EVIDENCE_CONSUMPTION=PASS")
    print("NARRATIVE_VALIDATION_EVIDENCE_CONSUMPTION=PASS")
    print("NARRATIVE_DOMAIN=NARRATIVE")
    print("NARRATIVE_IDENTITY_KIND_PATH=PRESERVED_STRUCTURALLY")
    print("NARRATIVE_PROSE=PRESERVED")
    print("CHOICE_PATH_SEMANTICS=PRESERVED")
    print("NARRATIVE_STATE_FACTS=PRESERVED")
    print("GRAPH_NODE_EDGE_EVIDENCE=PRESERVED")
    print("VALIDATION_RESULT=OBSERVED_NOT_RECOMPUTED")
    print("NARRATIVE_CANONICAL_IDENTITY_STRING=NONE_NO_FABRICATION")
    print("NARRATIVE_SOURCE_AST=DISTINCT_OWNER")
    print("NARRATIVE_EVIDENCE_INPUT_ORDER=PRESERVED")
    print("SOURCE_SPAN=NONE_NO_FABRICATION")
    print("GRAPH_LINK_INFERENCE=NONE")
    print("SAME_INPUT_SAME_TRACE_ID=PASS")
    print("SAME_INPUT_SAME_TRACE_MAP=PASS")
    print("NARRATIVE_GRAPH_CONSTRUCTION=NONE")
    print("NARRATIVE_VALIDATION_EXECUTION=NONE")
    print("NARRATIVE_LOWERING=NONE")
    print("NARRATIVE_PARSING=NONE")
    print("NARRATIVE_ANALYSIS_EXECUTION=NONE")
    print("NARRATIVE_RUNTIME_EXECUTION=NONE")
    print("SESSION_MUTATION=NONE")
    print("PRESENTATION_EXECUTION=NONE")
    print("COMPILER_MUTATION=NONE")
    print("CLI_LSP_INTEGRATION=NONE")
    print("SEMANTIC_EXECUTION=NONE")
    print("P11_TAM_H_NARRATIVE_EVIDENCE_TRACE_PRODUCTION=PASS")


if __name__ == "__main__":
    main()