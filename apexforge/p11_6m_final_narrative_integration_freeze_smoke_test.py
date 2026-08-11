"""P11.6M final narrative integration and track-freeze smoke test."""

from __future__ import annotations

import ast
from dataclasses import dataclass, FrozenInstanceError
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from language.narrative_analysis import analyze_narrative_source
from language.narrative_model import NarrativeIdentity
from language.project import build_project
from runtime.narrative_binding import (
    NarrativeConditionBinding,
    NarrativeConsequenceBinding,
    NarrativeFactAssignment,
    NarrativeFactPredicate,
    bind_narrative_story,
)
from tooling.build_artifact import (
    canonical_json_bytes,
    construct_build_artifact,
    write_build_artifact_atomic,
)
from tooling.cli import EXIT_SUCCESS, main as cli_main
from tooling.narrative_artifact import (
    NARRATIVE_BUILD_ARTIFACT_SCHEMA,
    NARRATIVE_BUILD_ARTIFACT_SCHEMA_V1,
    route_narrative_build_material,
)
from tooling.narrative_execution import (
    NarrativeExecutionRequest,
    execute_narrative_request,
    narrative_execution_request_payload,
    narrative_execution_result_bytes,
)
from tooling.narrative_interactive import (
    narrative_interactive_menu,
    run_narrative_interactive_session,
)
from tooling.narrative_rendering import (
    narrative_session_presentation,
    render_narrative_presentation,
    render_narrative_session,
)
from tooling.narrative_session import (
    NARRATIVE_SESSION_CREATE_REQUEST_SCHEMA,
    NARRATIVE_SESSION_STEP_REQUEST_SCHEMA,
    NARRATIVE_SESSION_TERMINATE_REQUEST_SCHEMA,
    NarrativeSessionCreateRequest,
    NarrativeSessionStepRequest,
    NarrativeSessionTerminateRequest,
    create_narrative_session,
    load_narrative_session,
    load_narrative_session_material,
    narrative_session_bytes,
    step_narrative_session,
    terminate_narrative_session,
    write_narrative_session_atomic,
)
from tooling.project_loader import load_project


EXPECTED_BRANCH = "p11.6m-final-integration-freeze"
EXPECTED_PREDECESSOR = "42dd1fc421ad4fce6394548b6f892051031922c3"
EXPECTED_TAG = "afp-p11.6l-freeze"
THIS_FILE = "apexforge/p11_6m_final_narrative_integration_freeze_smoke_test.py"
DOC_FILE = "docs/p11/P11_6M_FINAL_NARRATIVE_INTEGRATION_FREEZE.md"
PROTECTED_FIXTURES = {
    "examples/P11Validation/apexforge.json": (
        "8154bdc7668b7ba7979557e27db8c97ea945b3ca8993d7b0230fb3c550463405"
    ),
    "examples/P11Validation/main.apex": (
        "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9"
    ),
}
AUTHORED_ORDER = (
    "ZetaStart",
    "EndZeta",
    "ElsewhereLine",
    "AlphaStart",
    "EndAlpha",
)
REORDERED = (
    "AlphaStart",
    "EndAlpha",
    "ElsewhereLine",
    "ZetaStart",
    "EndZeta",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(
        completed.returncode == 0,
        f"git {' '.join(arguments)} failed: {completed.stderr.strip()}",
    )
    return completed.stdout.rstrip()


def identity_payload(identity: NarrativeIdentity) -> dict:
    return {"kind": identity.kind, "path": list(identity.path)}


def dialogue_block(name: str, marker: str) -> tuple[str, ...]:
    blocks = {
        "ZetaStart": (
            "    dialogue ZetaStart {",
            "        scene Start",
            "        speaker Guide",
            "        participants [Hero, Guide]",
            f'        text "{marker} Zeta: ${{fact}} if (...) invoke Main terminate AlphaChoice"',
            "    }",
        ),
        "AlphaStart": (
            "    dialogue AlphaStart {",
            "        scene Start",
            "        speaker Hero",
            "        participants [Guide, Hero]",
            '        text "Alpha exact text"',
            "    }",
        ),
        "EndZeta": (
            "    dialogue EndZeta {",
            "        scene End",
            "        speaker Guide",
            "        participants [Hero, Guide]",
            '        text "End Zeta exact text"',
            "    }",
        ),
        "EndAlpha": (
            "    dialogue EndAlpha {",
            "        scene End",
            "        speaker Hero",
            "        participants [Guide, Hero]",
            '        text "End Alpha exact text"',
            "    }",
        ),
        "ElsewhereLine": (
            "    dialogue ElsewhereLine {",
            "        scene Elsewhere",
            "        speaker Guide",
            "        participants [Guide]",
            '        text "UNRELATED-SCENE-TEXT"',
            "    }",
        ),
    }
    return blocks[name]


def narrative_source(
    marker: str = "Variant-A",
    dialogue_order: tuple[str, ...] = AUTHORED_ORDER,
) -> str:
    declarations = (
        "story FinalStory {",
        "    character Hero",
        "    character Guide",
        (
            '    scene Start { title "  The Final Gate  " '
            f'body "{marker} first line\\n${{fact}} if (...) invoke Main\\n'
            'terminate AlphaChoice" }'
        ),
        '    scene End { title "Arrival" body "The authored destination." }',
        "    scene Elsewhere",
    )
    dialogue_lines = tuple(
        line
        for name in dialogue_order
        for line in dialogue_block(name, marker)
    )
    choices_and_state = (
        "    choice ZetaChoice {",
        "        scene Start",
        '        path "Wait" { destination Elsewhere }',
        "    }",
        "    choice AlphaChoice {",
        "        scene Start",
        '        path "Continue" {',
        "            destination End",
        "            condition hero_ready",
        "            consequence mark_done",
        "        }",
        '        path "Detour" { destination Elsewhere }',
        "    }",
        "    narrative_state InitialFacts {",
        '        fact Hero.ready = "yes"',
        '        fact Guide.mood = "calm"',
        "    }",
        "}",
    )
    return "\n".join(declarations + dialogue_lines + choices_and_state)


@dataclass(frozen=True)
class Bundle:
    analysis: object
    bindings: object
    artifact: object
    material: object
    artifact_path: Path


def build_bundle(
    temporary_root: Path,
    output_name: str,
    *,
    marker: str = "Variant-A",
    dialogue_order: tuple[str, ...] = AUTHORED_ORDER,
) -> Bundle:
    analysis = analyze_narrative_source(
        narrative_source(marker, dialogue_order),
        source_name="final-story.apex",
    )
    story = analysis.semantic_story
    hero = NarrativeIdentity("character", ("Hero",))
    bindings = bind_narrative_story(
        story,
        condition_bindings=(
            NarrativeConditionBinding(
                "hero_ready",
                NarrativeFactPredicate(hero, "ready", "equals", "yes"),
            ),
        ),
        consequence_bindings=(
            NarrativeConsequenceBinding(
                "mark_done",
                (NarrativeFactAssignment(hero, "done", "yes"),),
            ),
        ),
    )
    loaded = load_project(root() / "examples/P11Validation")
    project_build = build_project(
        loaded.source_mapping(),
        entry=loaded.manifest.entry,
    )
    routed = route_narrative_build_material(
        analysis,
        bindings,
        source_name="final-story.apex",
    )
    artifact = construct_build_artifact(
        loaded,
        project_build,
        narrative_artifact=routed,
    )
    artifact_path = temporary_root / f"{output_name}.json"
    write_build_artifact_atomic(artifact, artifact_path)
    material = load_narrative_session_material(artifact_path)
    return Bundle(analysis, bindings, artifact, material, artifact_path)


def create_session(bundle: Bundle):
    story = bundle.analysis.semantic_story
    return create_narrative_session(
        bundle.material,
        NarrativeSessionCreateRequest(
            story.identity,
            story.scenes[0].identity,
            story.states[0].facts,
        ),
    )


def selected_request(bundle: Bundle, session):
    choice = NarrativeIdentity("choice", ("AlphaChoice",))
    return NarrativeExecutionRequest(session.state, choice, 0)


def write_json(path: Path, value: dict) -> bytes:
    content = canonical_json_bytes(value)
    path.write_bytes(content)
    return content


def make_v1(bundle: Bundle, path: Path) -> Path:
    value = json.loads(bundle.artifact.content.decode("utf-8"))
    value["narrative"]["schema"] = NARRATIVE_BUILD_ARTIFACT_SCHEMA_V1
    value["narrative"]["story"]["scenes"] = [
        {"identity": item["identity"]}
        for item in value["narrative"]["story"]["scenes"]
    ]
    for item in value["narrative"]["story"]["dialogues"]:
        del item["text"]
    del value["fingerprint"]
    fingerprint = hashlib.sha256(canonical_json_bytes(value)).hexdigest()
    value["fingerprint"] = {"algorithm": "sha256", "value": fingerprint}
    path.write_bytes(canonical_json_bytes(value))
    return path


def test_exact_freeze_ancestry_and_ownership() -> None:
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong branch")
    require(git("rev-parse", "HEAD") == EXPECTED_PREDECESSOR, "wrong HEAD")
    require(
        git("rev-parse", EXPECTED_TAG + "^{}") == EXPECTED_PREDECESSOR,
        "P11.6L tag does not resolve to the exact predecessor",
    )
    require(not git("diff", "--cached", "--name-only"), "files are staged")
    require(not git("diff", "--name-only", "HEAD"), "tracked files changed")
    status = {
        line.replace("\\", "/")
        for line in git("status", "--short", "--untracked-files=all").splitlines()
    }
    expected = {
        f"?? {THIS_FILE}",
        f"?? {DOC_FILE}",
        *(f"?? {path}" for path in PROTECTED_FIXTURES),
    }
    require(status == expected, f"M ownership differs: {status!r}")
    require((root() / ".git").is_dir(), ".git is unavailable")
    require(
        (root() / "apexforge/p11_6l_canonical_narrative_content_ordering_smoke_test.py").is_file(),
        "frozen P11.6L smoke is unavailable",
    )
    for relative_path, expected_hash in PROTECTED_FIXTURES.items():
        observed = hashlib.sha256((root() / relative_path).read_bytes()).hexdigest()
        require(observed == expected_hash, f"protected fixture changed: {relative_path}")


def test_source_model_artifact_and_material() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        first = build_bundle(temporary_root, "first")
        repeated = build_bundle(temporary_root, "repeated")
        analysis = first.analysis
        source_story = analysis.source_document.story
        story = analysis.semantic_story

        require(source_story.name.text == "FinalStory", "source story identity changed")
        require(
            tuple(item.name.text for item in source_story.characters)
            == ("Hero", "Guide"),
            "source character identities/order changed",
        )
        require(
            tuple(item.name.text for item in source_story.scenes)
            == ("Start", "End", "Elsewhere"),
            "source scene identities/order changed",
        )
        require(
            source_story.scenes[0].title.text == "  The Final Gate  "
            and source_story.scenes[0].body.text
            == "Variant-A first line\n${fact} if (...) invoke Main\nterminate AlphaChoice",
            "source scene prose changed",
        )
        require(
            tuple(item.name.text for item in source_story.dialogues) == AUTHORED_ORDER,
            "source dialogue declaration order changed",
        )
        require(
            tuple(item.name.text for item in source_story.choices)
            == ("ZetaChoice", "AlphaChoice"),
            "source choice order changed",
        )
        require(len(source_story.choices[1].paths) == 2, "multiple source paths lost")

        require(story.identity == NarrativeIdentity("story", ("FinalStory",)),
                "semantic story identity changed")
        require(tuple(item.identity.path[-1] for item in story.dialogues) == AUTHORED_ORDER,
                "semantic dialogue order changed")
        require(story.scenes[0].title == "  The Final Gate  ", "semantic title changed")
        require("${fact}" in story.scenes[0].body, "executable-looking prose changed")
        require(story.choices[1].paths[0].condition == "hero_ready",
                "condition identity changed")
        require(story.choices[1].paths[0].consequence == "mark_done",
                "consequence identity changed")
        require(story.choices[1].paths[0].destination.path == ("End",),
                "explicit destination changed")
        require(story.states[0].facts[0].name == "ready",
                "canonical authored initial facts changed")
        require(not analysis.validation_report.findings, "valid source gained findings")

        alpha = next(path for path in first.bindings.paths
                     if path.choice.path == ("AlphaChoice",) and path.path_index == 0)
        require(alpha.source_condition == "hero_ready", "source condition was not retained")
        require(alpha.condition.name == "ready", "condition binding resolved incorrectly")
        require(alpha.source_consequence == "mark_done",
                "source consequence was not retained")
        require(alpha.assignments[0].name == "done", "consequence binding resolved incorrectly")
        binding_text = repr(first.bindings)
        require("The Final Gate" not in binding_text and "Zeta:" not in binding_text,
                "prose entered executable binding semantics")

        require(NARRATIVE_BUILD_ARTIFACT_SCHEMA.endswith("/v2"),
                "current narrative schema is not frozen v2")
        require(first.artifact.content == repeated.artifact.content,
                "equivalent builds changed canonical bytes")
        require(first.artifact.fingerprint == repeated.artifact.fingerprint,
                "equivalent builds changed fingerprint")
        value = json.loads(first.artifact.content.decode("utf-8"))
        require(value["narrative"]["schema"] == NARRATIVE_BUILD_ARTIFACT_SCHEMA,
                "artifact narrative schema changed")
        require(
            tuple(item["identity"]["path"][-1]
                  for item in value["narrative"]["story"]["dialogues"])
            == AUTHORED_ORDER,
            "artifact dialogue array order changed",
        )
        require(value["narrative"]["story"]["scenes"][0]["title"]
                == "  The Final Gate  ", "artifact title changed")
        require(first.artifact.content.endswith(b"\n"), "artifact lost final LF")

        material = first.material
        require(material.story == story.identity, "material story changed")
        require(material.bindings == first.bindings, "material bindings changed")
        require(material.scene_records == story.scenes, "material scene/prose changed")
        require(material.dialogues == story.dialogues,
                "material dialogue/order changed")
        require(material.scenes == frozenset(item.identity for item in story.scenes),
                "material scene inventory changed")


def test_execution_session_presentation_and_interaction() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        bundle = build_bundle(temporary_root, "integrated")
        story = bundle.analysis.semantic_story
        session = create_session(bundle)
        require(session.artifact_fingerprint == bundle.artifact.fingerprint,
                "session artifact association changed")
        require(session.story == story.identity, "session story changed")
        require(session.state.current_scene.path == ("Start",), "starting scene changed")
        require(
            tuple((fact.subject.path[-1], fact.name, fact.value)
                  for fact in session.state.facts)
            == (("Guide", "mood", "calm"), ("Hero", "ready", "yes")),
            "canonical starting facts changed",
        )
        require(session.state.termination.status == "active", "session not active")
        require(session.state.progression == (story.scenes[0].identity,),
                "initial progression changed")
        require(session.state.choice_history == (), "initial history is not empty")
        serialized = narrative_session_bytes(session).decode("utf-8")
        require(not any(text in serialized for text in (
            "The Final Gate", "Variant-A", "Alpha exact text", "dialogues", "title", "body"
        )), "session serialization duplicated presentation material")

        presentation = narrative_session_presentation(bundle.material, session)
        require(presentation.story == story.identity, "presentation story changed")
        require(presentation.scene.path == ("Start",), "presentation scene changed")
        require(presentation.status == "active" and presentation.transition_count == 0,
                "presentation lifecycle state changed")
        require(presentation.title == "  The Final Gate  ", "presentation title changed")
        require("invoke Main" in presentation.body, "presentation body changed")
        require(
            tuple(item.identity.path[-1] for item in presentation.dialogues)
            == ("ZetaStart", "AlphaStart"),
            "current-scene filtering lost authored order",
        )
        rendered = render_narrative_presentation(presentation)
        require(rendered == render_narrative_session(bundle.material, session),
                "structured and text rendering disagree")
        require(rendered.index("dialogue:ZetaStart") < rendered.index("dialogue:AlphaStart"),
                "rendered authored order changed")
        require("UNRELATED-SCENE-TEXT" not in rendered and "dialogue:EndZeta" not in rendered,
                "unrelated-scene dialogue leaked")
        require("${fact}" in rendered and "invoke Main" in rendered,
                "authored prose was evaluated or omitted")

        menu = narrative_interactive_menu(bundle.material, session)
        require(
            tuple((item.number, item.choice.path[-1], item.path_index)
                  for item in menu)
            == ((1, "AlphaChoice", 0), (2, "AlphaChoice", 1),
                (3, "ZetaChoice", 0)),
            "choice/path ordering or menu mapping changed",
        )
        require(menu[0].request == NarrativeSessionStepRequest(
            NarrativeIdentity("choice", ("AlphaChoice",)), 0
        ), "menu alias did not map to the exact H request")

        direct = execute_narrative_request(
            bundle.bindings,
            selected_request(bundle, session),
        )
        require(direct.ok, "G one-shot transition failed")
        require(direct.final_state.current_scene.path == ("End",),
                "G destination changed")
        require(direct.diagnostics == (), "successful transition gained diagnostics")
        require(len(direct.trace) == 1 and len(direct.choice_evidence) == 1,
                "G trace/evidence changed")
        require(any(item.name == "done" and item.value == "yes"
                    for item in direct.final_state.facts),
                "G consequence was not applied")

        stepped = step_narrative_session(
            bundle.material,
            session,
            NarrativeSessionStepRequest(menu[0].choice, menu[0].path_index),
        )
        require(stepped.session is not None and stepped.execution_result == direct,
                "H/G/E/D step chain disagrees with one-shot execution")
        next_session = stepped.session
        require(next_session.state.progression[-1].path == ("End",),
                "session progression changed")
        require(next_session.state.choice_history == direct.final_state.choice_history,
                "session choice history changed")
        after = narrative_session_presentation(bundle.material, next_session)
        after_text = render_narrative_presentation(after)
        require(after.scene.path == ("End",) and after.transition_count == 1,
                "post-transition presentation state changed")
        require(after.title == "Arrival" and after.body == "The authored destination.",
                "post-transition authored prose changed")
        require(
            tuple(item.identity.path[-1] for item in after.dialogues)
            == ("EndZeta", "EndAlpha"),
            "destination dialogue authored order changed",
        )
        require("dialogue:ZetaStart" not in after_text,
                "old-scene dialogue survived transition")
        require("character:Hero:done=yes" in after_text,
                "updated fact was not presented")

        interaction_path = temporary_root / "interactive-session.json"
        write_narrative_session_atomic(session, interaction_path)
        events = []
        from tooling import narrative_interactive as interactive_module

        real_step = interactive_module.step_narrative_session
        real_write = interactive_module.write_narrative_session_atomic

        def recording_step(actual_material, actual_session, request):
            events.append(("step", request.choice.path[-1], request.path_index))
            return real_step(actual_material, actual_session, request)

        def recording_write(actual_session, path):
            events.append(("write", actual_session.state.current_scene.path[-1]))
            return real_write(actual_session, path)

        interaction_output = StringIO()
        with patch("tooling.narrative_interactive.step_narrative_session", recording_step), patch(
            "tooling.narrative_interactive.write_narrative_session_atomic", recording_write
        ):
            interacted = run_narrative_interactive_session(
                bundle.material,
                session,
                interaction_path,
                input_stream=StringIO("1\nquit\n"),
                output_stream=interaction_output,
            )
        require(events == [("step", "AlphaChoice", 0), ("write", "End")],
                f"interactive delegation/persistence order changed: {events!r}")
        require(interacted == next_session, "interactive state differs from H step")
        require(load_narrative_session(interaction_path) == interacted,
                "interactive success was not persisted")
        require("Scene: scene:Start" in interaction_output.getvalue()
                and "Scene: scene:End" in interaction_output.getvalue(),
                "interactive rendering did not reflect canonical states")

        terminated = terminate_narrative_session(
            bundle.material,
            next_session,
            NarrativeSessionTerminateRequest("explicit_outcome"),
        )
        require(terminated.state.termination.status == "terminated"
                and terminated.state.termination.reason == "explicit_outcome",
                "explicit H termination changed")
        try:
            terminated.state.current_scene = story.scenes[0].identity
        except FrozenInstanceError:
            pass
        else:
            raise AssertionError("terminated state is mutable")
        terminated_path = temporary_root / "terminated-session.json"
        write_narrative_session_atomic(terminated, terminated_path)
        require(load_narrative_session(terminated_path) == terminated,
                "terminated session persistence changed")
        terminated_text = render_narrative_session(bundle.material, terminated)
        require("Status: terminated" in terminated_text
                and "Termination reason: explicit_outcome" in terminated_text
                and "  (session terminated)" in terminated_text,
                "terminated J presentation changed")
        already_input = StringIO("1\n")
        with patch("tooling.narrative_interactive.step_narrative_session",
                   side_effect=AssertionError("terminated interaction stepped")), patch(
            "tooling.narrative_interactive.terminate_narrative_session",
            side_effect=AssertionError("terminated interaction re-terminated")
        ):
            returned = run_narrative_interactive_session(
                bundle.material,
                terminated,
                terminated_path,
                input_stream=already_input,
                output_stream=StringIO(),
            )
        require(returned == terminated and already_input.tell() == 0,
                "terminated interaction consumed choice input")

        original = narrative_session_bytes(session)
        for text in ("quit\n", ""):
            write_narrative_session_atomic(session, interaction_path)
            with patch("tooling.narrative_interactive.step_narrative_session",
                       side_effect=AssertionError("quit/EOF stepped")), patch(
                "tooling.narrative_interactive.terminate_narrative_session",
                side_effect=AssertionError("quit/EOF terminated")
            ), patch("tooling.narrative_interactive.write_narrative_session_atomic",
                     side_effect=AssertionError("quit/EOF wrote")):
                unchanged = run_narrative_interactive_session(
                    bundle.material,
                    session,
                    interaction_path,
                    input_stream=StringIO(text),
                    output_stream=StringIO(),
                )
            require(unchanged == session and interaction_path.read_bytes() == original,
                    "quit/EOF changed session, persistence, or outcome")


def test_compatibility_and_semantic_isolation() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        base = build_bundle(temporary_root, "base")
        story = base.analysis.semantic_story
        v1_path = make_v1(base, temporary_root / "historical-v1.json")
        v1 = load_narrative_session_material(v1_path)
        require(all(scene.title is None and scene.body is None
                    for scene in v1.scene_records), "v1 invented scene prose")
        require(all(dialogue.text is None for dialogue in v1.dialogues),
                "v1 invented dialogue prose")
        require(tuple(item.identity.path[-1] for item in v1.dialogues) == AUTHORED_ORDER,
                "v1 dialogue array order changed")
        v1_session = create_narrative_session(
            v1,
            NarrativeSessionCreateRequest(
                story.identity,
                story.scenes[0].identity,
                story.states[0].facts,
            ),
        )
        v1_text = render_narrative_session(v1, v1_session)
        expected_v1_text = (
            "ApexForge narrative session\n"
            "Story: story:FinalStory\n"
            "Scene: scene:Start\n"
            "Status: active\n"
            "Transitions: 0\n"
            "Facts:\n"
            "  character:Guide:mood=calm\n"
            "  character:Hero:ready=yes\n"
            "Choices:\n"
            '  1. choice:AlphaChoice path[0] "Continue" -> scene:End\n'
            '  2. choice:AlphaChoice path[1] "Detour" -> scene:Elsewhere\n'
            '  3. choice:ZetaChoice path[0] "Wait" -> scene:Elsewhere\n'
        )
        require(v1_text == expected_v1_text,
                "historical no-prose J rendering bytes changed")
        require("Title:" not in v1_text and "Body:" not in v1_text
                and "Dialogue:" not in v1_text,
                "no-prose rendering invented headings")
        v1_step = step_narrative_session(
            v1,
            v1_session,
            NarrativeSessionStepRequest(NarrativeIdentity("choice", ("AlphaChoice",)), 0),
        )
        require(v1_step.session is not None
                and v1_step.session.state.current_scene.path == ("End",),
                "v1 execution compatibility changed")
        require(base.material.scene_records == story.scenes
                and base.material.dialogues == story.dialogues,
                "v2 exact material reconstruction changed")

        prose_changed = build_bundle(temporary_root, "prose-changed", marker="Variant-B")
        require(base.artifact.content != prose_changed.artifact.content,
                "prose-only change did not change artifact bytes")
        require(base.artifact.fingerprint != prose_changed.artifact.fingerprint,
                "prose-only change did not change fingerprint")
        prose_sessions = tuple(create_session(item) for item in (base, prose_changed))
        prose_results = tuple(
            execute_narrative_request(item.bindings, selected_request(item, session))
            for item, session in zip((base, prose_changed), prose_sessions)
        )
        require(prose_results[0] == prose_results[1],
                "prose changed transition result/state/history/diagnostics")
        prose_terminated = tuple(
            terminate_narrative_session(
                item.material,
                step_narrative_session(
                    item.material,
                    session,
                    NarrativeSessionStepRequest(
                        NarrativeIdentity("choice", ("AlphaChoice",)), 0
                    ),
                ).session,
                NarrativeSessionTerminateRequest("explicit_outcome"),
            ).state.termination
            for item, session in zip((base, prose_changed), prose_sessions)
        )
        require(prose_terminated[0] == prose_terminated[1],
                "prose changed termination behavior")

        reordered = build_bundle(
            temporary_root,
            "reordered",
            dialogue_order=REORDERED,
        )
        require(base.artifact.content != reordered.artifact.content
                and base.artifact.fingerprint != reordered.artifact.fingerprint,
                "authored dialogue reorder did not change artifact identity")
        require(base.bindings == reordered.bindings,
                "dialogue order changed executable bindings/path mapping")
        order_sessions = tuple(create_session(item) for item in (base, reordered))
        order_presentations = tuple(
            narrative_session_presentation(item.material, session)
            for item, session in zip((base, reordered), order_sessions)
        )
        require(
            tuple(item.identity.path[-1] for item in order_presentations[0].dialogues)
            == ("ZetaStart", "AlphaStart")
            and tuple(item.identity.path[-1]
                      for item in order_presentations[1].dialogues)
            == ("AlphaStart", "ZetaStart"),
            "authored reorder did not change presentation order",
        )
        require(order_presentations[0].choices == order_presentations[1].choices,
                "dialogue order changed choice display/path ordering")
        order_results = tuple(
            execute_narrative_request(item.bindings, selected_request(item, session))
            for item, session in zip((base, reordered), order_sessions)
        )
        require(order_results[0] == order_results[1],
                "dialogue order changed execution result")


def test_environment_source_boundary_and_authority() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        with patch.dict(os.environ, {"APEXFORGE_M_IRRELEVANT": "one"}):
            first = build_bundle(temporary_root, "environment-one")
        with patch.dict(os.environ, {"APEXFORGE_M_IRRELEVANT": "two"}):
            second = build_bundle(temporary_root, "environment-two")
        sessions = tuple(create_session(item) for item in (first, second))
        presentations = tuple(
            narrative_session_presentation(item.material, session)
            for item, session in zip((first, second), sessions)
        )
        rendered = tuple(render_narrative_presentation(item) for item in presentations)
        results = tuple(
            execute_narrative_request(item.bindings, selected_request(item, session))
            for item, session in zip((first, second), sessions)
        )
        require(first.artifact.content == second.artifact.content
                and first.artifact.fingerprint == second.artifact.fingerprint,
                "irrelevant environment changed artifact determinism")
        require(presentations[0] == presentations[1] and rendered[0] == rendered[1],
                "irrelevant environment changed presentation")
        require(results[0] == results[1],
                "irrelevant environment changed execution")

        expected_render = rendered[0]
        expected_result = results[0]
        with patch("pathlib.Path.read_bytes", side_effect=AssertionError("source reopened")), patch(
            "pathlib.Path.read_text", side_effect=AssertionError("source reopened")
        ), patch("pathlib.Path.rglob", side_effect=AssertionError("project scanned")), patch(
            "pathlib.Path.glob", side_effect=AssertionError("project scanned")
        ):
            require(render_narrative_session(first.material, sessions[0]) == expected_render,
                    "material-only rendering changed")
            require(execute_narrative_request(
                first.material.bindings,
                selected_request(first, sessions[0]),
            ) == expected_result, "material-only execution changed")

    rendering_source = (root() / "apexforge/tooling/narrative_rendering.py").read_text(
        encoding="utf-8"
    )
    interaction_source = (root() / "apexforge/tooling/narrative_interactive.py").read_text(
        encoding="utf-8"
    )
    lowering_source = (root() / "apexforge/language/narrative_lowering.py").read_text(
        encoding="utf-8"
    )
    trees = (ast.parse(rendering_source), ast.parse(interaction_source))
    imports = {
        alias.name
        for tree in trees
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for tree in trees
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    forbidden_imports = {
        "random", "time", "socket", "requests", "urllib", "openai", "anthropic",
        "language.narrative_parser", "language.narrative_analysis",
    }
    require(not imports.intersection(forbidden_imports),
            "presentation/interaction acquired random, network, AI, or parser authority")
    calls = {
        node.func.id
        for tree in trees
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    require(not calls.intersection({"eval", "exec", "compile", "input", "open"}),
            "presentation/interaction gained executable prose or implicit input")
    require("source_condition" not in interaction_source
            and ".condition" not in interaction_source
            and ".assignments" not in interaction_source,
            "interaction inspects condition/consequence semantics")
    combined = (rendering_source + interaction_source + lowering_source).lower()
    require(not any(term in combined for term in (
        "openai", "anthropic", "llm", "recommendation engine",
        "semantic content scoring", "automatic speaker simulation",
        "random dialogue generation",
    )), "narrative presentation path gained autonomous narration")
    require("${" not in lowering_source and "interpol" not in lowering_source.lower(),
            "lowering gained prose interpolation")


def test_public_command_integration() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        bundle = build_bundle(temporary_root, "cli-narrative")
        project = root() / "examples/P11Validation"

        generic_artifact = temporary_root / "generic-build.json"
        stdout = StringIO()
        stderr = StringIO()
        code = cli_main(
            ("build", str(project), "--output", str(generic_artifact)),
            stdout=stdout,
            stderr=stderr,
        )
        require(code == EXIT_SUCCESS and generic_artifact.is_file() and stderr.getvalue() == "",
                "generic apexforge build failed")
        generic_value = json.loads(generic_artifact.read_text(encoding="utf-8"))
        require("narrative" not in generic_value,
                "generic build inferred narrative material")

        run_output = StringIO()
        run_error = StringIO()
        run_code = cli_main(
            ("run", str(project)),
            stdout=run_output,
            stderr=run_error,
        )
        require(run_code == EXIT_SUCCESS and run_error.getvalue() == "",
                "generic apexforge run failed")
        require("ApexForge run succeeded" in run_output.getvalue(),
                "generic run no longer executes the project entry directive")

        session = create_session(bundle)
        one_shot_request = selected_request(bundle, session)
        one_shot_path = temporary_root / "one-shot-request.json"
        write_json(one_shot_path, narrative_execution_request_payload(one_shot_request))
        one_shot_output = StringIO()
        one_shot_error = StringIO()
        code = cli_main(
            ("narrative", str(bundle.artifact_path), "--request", str(one_shot_path)),
            stdout=one_shot_output,
            stderr=one_shot_error,
        )
        expected = narrative_execution_result_bytes(
            execute_narrative_request(bundle.bindings, one_shot_request)
        ).decode("utf-8")
        require(code == EXIT_SUCCESS and one_shot_output.getvalue() == expected
                and one_shot_error.getvalue() == "",
                "public one-shot narrative command changed")

        story = bundle.analysis.semantic_story
        create_request_path = temporary_root / "create-request.json"
        write_json(create_request_path, {
            "schema": NARRATIVE_SESSION_CREATE_REQUEST_SCHEMA,
            "story": identity_payload(story.identity),
            "start_scene": identity_payload(story.scenes[0].identity),
            "facts": [
                {
                    "subject": identity_payload(fact.subject),
                    "name": fact.name,
                    "value": fact.value,
                }
                for fact in story.states[0].facts
            ],
        })
        created_path = temporary_root / "created-session.json"
        create_output = StringIO()
        code = cli_main((
            "narrative-session", "create", str(bundle.artifact_path),
            "--request", str(create_request_path), "--output", str(created_path),
        ), stdout=create_output, stderr=StringIO())
        require(code == EXIT_SUCCESS and load_narrative_session(created_path) == session,
                "public session create changed")

        step_request_path = temporary_root / "step-request.json"
        write_json(step_request_path, {
            "schema": NARRATIVE_SESSION_STEP_REQUEST_SCHEMA,
            "choice": identity_payload(NarrativeIdentity("choice", ("AlphaChoice",))),
            "path_index": 0,
        })
        stepped_path = temporary_root / "stepped-session.json"
        step_output = StringIO()
        code = cli_main((
            "narrative-session", "step", str(bundle.artifact_path), str(created_path),
            "--request", str(step_request_path), "--output", str(stepped_path),
        ), stdout=step_output, stderr=StringIO())
        require(code == EXIT_SUCCESS
                and load_narrative_session(stepped_path).state.current_scene.path == ("End",),
                "public session step changed")

        terminate_request_path = temporary_root / "terminate-request.json"
        write_json(terminate_request_path, {
            "schema": NARRATIVE_SESSION_TERMINATE_REQUEST_SCHEMA,
            "reason": "explicit_outcome",
        })
        terminated_path = temporary_root / "cli-terminated-session.json"
        code = cli_main((
            "narrative-session", "terminate", str(bundle.artifact_path), str(stepped_path),
            "--request", str(terminate_request_path), "--output", str(terminated_path),
        ), stdout=StringIO(), stderr=StringIO())
        require(code == EXIT_SUCCESS
                and load_narrative_session(terminated_path).state.termination.reason
                == "explicit_outcome", "public session terminate changed")

        interactive_path = temporary_root / "cli-interactive-session.json"
        write_narrative_session_atomic(session, interactive_path)
        interactive_output = StringIO()
        code = cli_main((
            "narrative-session", "interact", str(bundle.artifact_path),
            str(interactive_path),
        ), stdin=StringIO("1\nquit\n"), stdout=interactive_output, stderr=StringIO())
        require(code == EXIT_SUCCESS
                and load_narrative_session(interactive_path).state.current_scene.path == ("End",),
                "public interactive session command changed")
        require("Scene: scene:Start" in interactive_output.getvalue()
                and "Scene: scene:End" in interactive_output.getvalue(),
                "public interactive rendering changed")


def main() -> int:
    test_exact_freeze_ancestry_and_ownership()
    print("Exact L ancestry, M ownership, and protected fixtures: PASS")
    test_source_model_artifact_and_material()
    print("Source/model/bindings/artifact/material integration: PASS")
    test_execution_session_presentation_and_interaction()
    print("G/H/J/K/L/I/E/D execution and lifecycle integration: PASS")
    test_compatibility_and_semantic_isolation()
    print("No-prose, v1/v2, prose/order/choice isolation: PASS")
    test_environment_source_boundary_and_authority()
    print("Environment, source-reopening, inert prose, and no-autonomy boundaries: PASS")
    test_public_command_integration()
    print("Public build/run/narrative/session/interact commands: PASS")
    print("P11.6M final narrative integration and track-freeze smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
