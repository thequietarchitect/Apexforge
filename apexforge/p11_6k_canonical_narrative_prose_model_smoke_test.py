"""P11.6K canonical narrative prose model focused smoke test."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from language.narrative_analysis import analyze_narrative_source
from language.narrative_model import (
    NarrativeDialogue,
    NarrativeIdentity,
    NarrativeScene,
    NarrativeStateFact,
)
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
from tooling.narrative_artifact import (
    NARRATIVE_BUILD_ARTIFACT_SCHEMA,
    NARRATIVE_BUILD_ARTIFACT_SCHEMA_V1,
    route_narrative_build_material,
)
from tooling.narrative_execution import (
    NarrativeExecutionRequest,
    execute_narrative_request,
)
from tooling.narrative_rendering import (
    NarrativeDialoguePresentation,
    narrative_session_presentation,
    render_narrative_session,
)
from tooling.narrative_session import (
    NarrativeSessionCreateRequest,
    NarrativeSessionStepRequest,
    NarrativeSessionTerminateRequest,
    create_narrative_session,
    load_narrative_session_material,
    narrative_session_bytes,
    step_narrative_session,
    terminate_narrative_session,
)
from tooling.project_loader import load_project


EXPECTED_BRANCH = "p11.6k-canonical-narrative-prose-model"
EXPECTED_PREDECESSOR = "a1683ce4f3e1fc16d8da0411fc516dd16478aef6"
EXPECTED_TAG = "afp-p11.6j-freeze"
THIS_FILE = "apexforge/p11_6k_canonical_narrative_prose_model_smoke_test.py"
DOC_FILE = "docs/p11/P11_6K_CANONICAL_NARRATIVE_PROSE_MODEL.md"
AUTHORIZED_PATHS = (
    "apexforge/language/narrative_model.py",
    "apexforge/language/narrative_source.py",
    "apexforge/language/narrative_parser.py",
    "apexforge/language/narrative_lowering.py",
    "apexforge/tooling/narrative_artifact.py",
    "apexforge/tooling/narrative_execution.py",
    "apexforge/tooling/narrative_session.py",
    "apexforge/tooling/narrative_rendering.py",
    "apexforge/tooling/__init__.py",
    THIS_FILE,
    DOC_FILE,
)
PROTECTED_FIXTURES = {
    "examples/P11Validation/apexforge.json": (
        "8154bdc7668b7ba7979557e27db8c97ea945b3ca8993d7b0230fb3c550463405"
    ),
    "examples/P11Validation/main.apex": (
        "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9"
    ),
}


def narrative_source(marker: str) -> str:
    return "\n".join(
        (
            "story ProseStory {",
            "    character Hero",
            "    character Guide",
            '    scene Start { title "  The Ω Gate  " body "First line\\nSecond\\tline" }',
            "    scene End",
            "    dialogue Zeta {",
            "        scene Start",
            "        speaker Guide",
            "        participants [Hero, Guide]",
            f'        text "{marker}: ${{fact}} if (...) invoke Main terminate choice Decide"',
            "    }",
            "    dialogue Alpha {",
            "        scene Start",
            "        speaker Hero",
            "        participants [Guide, Hero]",
            '        text "He said: \\"go\\"; path C:\\\\archive."',
            "    }",
            "    dialogue Elsewhere {",
            "        scene End",
            "        speaker Hero",
            "        participants [Hero]",
            '        text "UNRELATED-SCENE-TEXT"',
            "    }",
            "    choice Decide {",
            "        scene Start",
            '        path "Continue" {',
            "            destination End",
            "            condition hero_ready",
            "            consequence mark_done",
            "        }",
            "    }",
            "}",
        )
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(exc_type, operation, message: str):
    try:
        operation()
    except exc_type as exc:
        return exc
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


def build_material(temporary_root: Path, marker: str, name: str):
    analysis = analyze_narrative_source(
        narrative_source(marker),
        source_name="prose-story.apex",
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
    build = build_project(loaded.source_mapping(), entry=loaded.manifest.entry)
    narrative = route_narrative_build_material(analysis, bindings)
    artifact = construct_build_artifact(
        loaded,
        build,
        narrative_artifact=narrative,
    )
    artifact_path = temporary_root / f"{name}.json"
    write_build_artifact_atomic(artifact, artifact_path)
    material = load_narrative_session_material(artifact_path)
    return analysis, bindings, artifact, material, artifact_path


def test_baseline_ownership_and_protected_fixtures() -> None:
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong branch")
    require(git("rev-parse", "HEAD") == EXPECTED_PREDECESSOR, "wrong HEAD")
    require(
        git("rev-parse", EXPECTED_TAG + "^{}") == EXPECTED_PREDECESSOR,
        "P11.6J freeze tag does not identify the exact predecessor",
    )
    require(not git("diff", "--cached", "--name-only"), "files are staged")
    status_paths = {
        line[3:].replace("\\", "/")
        for line in git(
            "status", "--porcelain=v1", "--untracked-files=all"
        ).splitlines()
        if line
    }
    require(
        status_paths == set(AUTHORIZED_PATHS) | set(PROTECTED_FIXTURES),
        f"unexpected ownership set: {status_paths!r}",
    )
    changed = set(git("diff", "--name-only", "HEAD").splitlines())
    require(
        changed == set(AUTHORIZED_PATHS) - {THIS_FILE, DOC_FILE},
        f"tracked ownership differs: {changed!r}",
    )
    for relative_path, expected in PROTECTED_FIXTURES.items():
        observed = hashlib.sha256((root() / relative_path).read_bytes()).hexdigest()
        require(observed == expected, f"protected fixture changed: {relative_path}")
    require((root() / ".git").is_dir(), ".git is unavailable")


def test_model_source_and_exact_prose_contract() -> None:
    analysis = analyze_narrative_source(narrative_source("Variant-A"))
    story = analysis.semantic_story
    scene = story.scenes[0]
    dialogue = story.dialogues[0]
    require(scene.identity == NarrativeIdentity("scene", ("Start",)), "scene identity changed")
    require(scene.title == "  The Ω Gate  ", "title was not retained exactly")
    require(scene.body == "First line\nSecond\tline", "body escapes were not retained")
    require(story.scenes[1].title is None and story.scenes[1].body is None,
            "absent scene prose was fabricated")
    require(dialogue.identity == NarrativeIdentity("dialogue", ("Zeta",)),
            "dialogue identity changed")
    require(dialogue.scene == scene.identity, "dialogue scene changed")
    require(dialogue.speaker == NarrativeIdentity("character", ("Guide",)),
            "dialogue speaker changed")
    require(dialogue.participants == (
        NarrativeIdentity("character", ("Hero",)),
        NarrativeIdentity("character", ("Guide",)),
    ), "dialogue participants changed")
    require("${fact}" in dialogue.text and "terminate" in dialogue.text,
            "executable-looking prose was altered")
    require_raises(FrozenInstanceError, lambda: setattr(scene, "title", "changed"),
                   "scene prose record is mutable")
    require_raises(FrozenInstanceError, lambda: setattr(dialogue, "text", "changed"),
                   "dialogue prose record is mutable")
    require_raises(ValueError, lambda: NarrativeScene(scene.identity, ""),
                   "empty title duplicated absence")
    require_raises(ValueError, lambda: NarrativeScene(scene.identity, body="a\rb"),
                   "CR newline entered canonical prose")


def test_artifact_determinism_fingerprint_and_v1_compatibility() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        first = build_material(temporary_root, "Variant-A", "first")
        repeated = build_material(temporary_root, "Variant-A", "repeated")
        changed = build_material(temporary_root, "Variant-B", "changed")
        first_analysis, _, first_artifact, first_material, _ = first
        repeated_analysis, _, repeated_artifact, repeated_material, _ = repeated
        changed_analysis, _, changed_artifact, changed_material, changed_path = changed
        require(first_analysis.semantic_story == repeated_analysis.semantic_story,
                "equivalent source produced different parsed models")
        require(first_artifact.content == repeated_artifact.content,
                "equivalent prose produced different canonical bytes")
        require(first_artifact.fingerprint == repeated_artifact.fingerprint,
                "equivalent prose produced different fingerprints")
        require(first_material == repeated_material, "equivalent material changed")
        require(first_artifact.content != changed_artifact.content,
                "prose-only change did not change artifact bytes")
        require(first_artifact.fingerprint != changed_artifact.fingerprint,
                "prose-only change did not change artifact fingerprint")
        require(first_analysis.semantic_story.identity == changed_analysis.semantic_story.identity,
                "prose changed story identity")
        require(tuple(scene.identity for scene in first_analysis.semantic_story.scenes)
                == tuple(scene.identity for scene in changed_analysis.semantic_story.scenes),
                "prose changed scene identities")
        require(first[1] == changed[1], "prose changed executable bindings")
        require(changed_material.scene_records == changed_analysis.semantic_story.scenes,
                "scene prose did not survive material loading")
        require(changed_material.dialogues == changed_analysis.semantic_story.dialogues,
                "dialogue prose did not survive material loading")
        value = json.loads(changed_path.read_text(encoding="utf-8"))
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
        historical_path = temporary_root / "historical-v1.json"
        historical_path.write_bytes(canonical_json_bytes(value))
        historical = load_narrative_session_material(historical_path)
        require(all(scene.title is None and scene.body is None
                    for scene in historical.scene_records),
                "historical v1 artifact invented scene prose")
        require(all(dialogue.text is None for dialogue in historical.dialogues),
                "historical v1 artifact invented dialogue prose")
        require(NARRATIVE_BUILD_ARTIFACT_SCHEMA.endswith("/v2"),
                "K writer did not use the versioned prose schema")


def test_renderer_current_scene_ordering_and_no_prose_compatibility() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        analysis, _, _, material, _ = build_material(
            temporary_root, "Variant-A", "render"
        )
        story = analysis.semantic_story
        session = create_narrative_session(
            material,
            NarrativeSessionCreateRequest(story.identity, story.scenes[0].identity),
        )
        presentation = narrative_session_presentation(material, session)
        require(presentation.title == "  The Ω Gate  ", "title was not projected")
        require(presentation.body == "First line\nSecond\tline", "body was not projected")
        require(all(type(item) is NarrativeDialoguePresentation
                    for item in presentation.dialogues),
                "dialogue presentation records are not immutable exact values")
        require(tuple(item.identity.path for item in presentation.dialogues)
                == (("Alpha",), ("Zeta",)), "dialogue ordering is not canonical")
        text = render_narrative_session(material, session)
        require("Title:\n  The Ω Gate  \n" in text, "exact title was not rendered")
        require("Body:\nFirst line\nSecond\tline\n" in text, "exact body was not rendered")
        require(text.index("dialogue:Alpha") < text.index("dialogue:Zeta"),
                "rendered dialogue ordering changed")
        require("UNRELATED-SCENE-TEXT" not in text,
                "unrelated-scene dialogue leaked into rendering")
        with patch("pathlib.Path.read_bytes", side_effect=AssertionError("source reopened")), patch(
            "pathlib.Path.read_text", side_effect=AssertionError("source reopened")
        ), patch("pathlib.Path.rglob", side_effect=AssertionError("filesystem scanned")):
            require(render_narrative_session(material, session) == text,
                    "material-only rendering changed")

        from p11_6i_interactive_narrative_session_ux_smoke_test import make_material
        _, _, old_material, old_session, _, _ = make_material(temporary_root, "NoProse")
        expected = (
            "ApexForge narrative session\n"
            "Story: story:InteractiveStory\n"
            "Scene: scene:Start\n"
            "Status: active\n"
            "Transitions: 0\n"
            "Facts:\n"
            "  (none)\n"
            "Choices:\n"
            '  1. choice:Alpha path[0] "Continue" -> scene:Middle\n'
            '  2. choice:Alpha path[1] "Finish now" -> scene:End\n'
            '  3. choice:Zeta path[0] "Blocked" -> scene:End\n'
        )
        require(render_narrative_session(old_material, old_session) == expected,
                "historical no-prose J bytes changed")


def test_semantic_execution_and_session_isolation() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        candidates = (
            build_material(temporary_root, "Variant-A", "semantic-a"),
            build_material(temporary_root, "Variant-B", "semantic-b"),
        )
        sessions = []
        results = []
        direct_results = []
        for analysis, bindings, _, material, _ in candidates:
            story = analysis.semantic_story
            hero = NarrativeIdentity("character", ("Hero",))
            session = create_narrative_session(
                material,
                NarrativeSessionCreateRequest(
                    story.identity,
                    story.scenes[0].identity,
                    (NarrativeStateFact(hero, "ready", "yes"),),
                ),
            )
            direct_results.append(
                execute_narrative_request(
                    bindings,
                    NarrativeExecutionRequest(session.state, story.choices[0].identity, 0),
                )
            )
            stepped = step_narrative_session(
                material,
                session,
                NarrativeSessionStepRequest(story.choices[0].identity, 0),
            )
            require(stepped.session is not None, "explicit transition failed")
            sessions.append((session, stepped.session, material))
            results.append(stepped.execution_result)
        require(direct_results[0] == direct_results[1],
                "prose changed P11.6G one-shot execution")
        require(results[0] == results[1], "prose changed transition result/diagnostics")
        require(sessions[0][1].state == sessions[1][1].state,
                "prose changed scene, facts, progression, history, or termination")
        for initial, stepped, material in sessions:
            serialized = narrative_session_bytes(initial).decode("utf-8")
            require("The Ω Gate" not in serialized and "Variant-" not in serialized,
                    "session serialization duplicated prose")
            terminated = terminate_narrative_session(
                material,
                stepped,
                NarrativeSessionTerminateRequest("explicit_outcome"),
            )
            require(terminated.state.termination.is_terminated,
                    "explicit H termination changed")


def test_no_executable_or_autonomous_narration_authority() -> None:
    rendering_path = root() / "apexforge/tooling/narrative_rendering.py"
    source = rendering_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    forbidden = {
        "random", "subprocess", "socket", "requests",
        "language.narrative_parser", "language.narrative_analysis",
        "runtime.narrative_transition",
    }
    require(not imports.intersection(forbidden),
            "renderer acquired parsing, transition, random, process, or network authority")
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    require(not called.intersection({"eval", "exec", "compile", "input", "open"}),
            "renderer executes or sources prose")
    lower_source = (root() / "apexforge/language/narrative_lowering.py").read_text(
        encoding="utf-8"
    )
    require("${" not in lower_source and "interpol" not in lower_source.lower(),
            "lowering contains interpolation machinery")
    combined = source.lower() + lower_source.lower()
    require(not any(term in combined for term in ("llm", "recommendation", "speaker simulation")),
            "K contains autonomous narration machinery")


def main() -> int:
    test_baseline_ownership_and_protected_fixtures()
    test_model_source_and_exact_prose_contract()
    test_artifact_determinism_fingerprint_and_v1_compatibility()
    test_renderer_current_scene_ordering_and_no_prose_compatibility()
    test_semantic_execution_and_session_isolation()
    test_no_executable_or_autonomous_narration_authority()
    print("P11.6K canonical narrative prose model smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
