"""P11.6L canonical narrative content ordering focused smoke test."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from language.narrative_analysis import analyze_narrative_source
from language.narrative_model import (
    NarrativeDialogue,
    NarrativeIdentity,
    NarrativeScene,
    NarrativeStateFact,
)
from language.project import build_project
from runtime.narrative_binding import (
    NarrativeConsequenceBinding,
    NarrativeFactAssignment,
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
from tooling.narrative_interactive import narrative_interactive_menu
from tooling.narrative_rendering import (
    narrative_session_presentation,
    render_narrative_presentation,
    render_narrative_session,
)
from tooling.narrative_session import (
    NarrativeSessionCreateRequest,
    NarrativeSessionStepRequest,
    create_narrative_session,
    load_narrative_session_material,
    narrative_session_bytes,
    step_narrative_session,
)
from tooling.project_loader import load_project


EXPECTED_BRANCH = "p11.6l-canonical-narrative-content-ordering"
EXPECTED_PREDECESSOR = "628022283b75ee97d4545bc8324da968e7fab68f"
EXPECTED_TAG = "afp-p11.6k-freeze"
THIS_FILE = (
    "apexforge/p11_6l_canonical_narrative_content_ordering_smoke_test.py"
)
DOC_FILE = "docs/p11/P11_6L_CANONICAL_NARRATIVE_CONTENT_ORDERING.md"
RENDERER_FILE = "apexforge/tooling/narrative_rendering.py"
K_SMOKE = "apexforge/p11_6k_canonical_narrative_prose_model_smoke_test.py"
AUTHORIZED_PATHS = (RENDERER_FILE, THIS_FILE, DOC_FILE)
PROTECTED_FIXTURES = {
    "examples/P11Validation/apexforge.json": (
        "8154bdc7668b7ba7979557e27db8c97ea945b3ca8993d7b0230fb3c550463405"
    ),
    "examples/P11Validation/main.apex": (
        "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9"
    ),
}


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


def dialogue_block(name: str) -> tuple[str, ...]:
    records = {
        "Zeta": (
            "    dialogue Zeta {",
            "        scene Start",
            "        speaker Guide",
            "        participants [Hero, Guide]",
            '        text "  Zeta Ω first\\nsecond\\tline  "',
            "    }",
        ),
        "Elsewhere": (
            "    dialogue Elsewhere {",
            "        scene End",
            "        speaker Hero",
            "        participants [Hero]",
            '        text "UNRELATED-SCENE-TEXT"',
            "    }",
        ),
        "Alpha": (
            "    dialogue Alpha {",
            "        scene Start",
            "        speaker Hero",
            "        participants [Guide, Hero]",
            '        text "Alpha exact text"',
            "    }",
        ),
        "Middle": (
            "    dialogue Middle {",
            "        scene Start",
            "        speaker Guide",
            "        participants [Guide]",
            '        text "Middle exact text"',
            "    }",
        ),
    }
    return records[name]


def narrative_source(dialogue_order: tuple[str, ...]) -> str:
    declarations = (
        "story OrderedStory {",
        "    character Hero",
        "    character Guide",
        '    scene Start { title "  Authored Title  " body "Body first\\nBody second" }',
        "    scene MiddleScene",
        "    scene End",
    )
    choices = (
        "    choice ZetaChoice {",
        "        scene Start",
        '        path "Finish" { destination End }',
        "    }",
        "    choice AlphaChoice {",
        "        scene Start",
        '        path "Continue" {',
        "            destination MiddleScene",
        "            consequence mark_done",
        "        }",
        "    }",
        "}",
    )
    dialogue_lines = tuple(
        line
        for name in dialogue_order
        for line in dialogue_block(name)
    )
    return "\n".join(declarations + dialogue_lines + choices)


def build_material(
    temporary_root: Path,
    dialogue_order: tuple[str, ...],
    output_name: str,
):
    analysis = analyze_narrative_source(
        narrative_source(dialogue_order),
        source_name="ordered-story.apex",
    )
    story = analysis.semantic_story
    hero = NarrativeIdentity("character", ("Hero",))
    bindings = bind_narrative_story(
        story,
        consequence_bindings=(
            NarrativeConsequenceBinding(
                "mark_done",
                (NarrativeFactAssignment(hero, "done", "yes"),),
            ),
        ),
    )
    loaded = load_project(root() / "examples/P11Validation")
    build = build_project(loaded.source_mapping(), entry=loaded.manifest.entry)
    narrative = route_narrative_build_material(
        analysis,
        bindings,
        source_name="ordered-story.apex",
    )
    artifact = construct_build_artifact(
        loaded,
        build,
        narrative_artifact=narrative,
    )
    artifact_path = temporary_root / f"{output_name}.json"
    write_build_artifact_atomic(artifact, artifact_path)
    material = load_narrative_session_material(artifact_path)
    return analysis, bindings, artifact, material, artifact_path


def identity_names(records) -> tuple[str, ...]:
    return tuple(record.identity.path[-1] for record in records)


def artifact_dialogue_names(artifact) -> tuple[str, ...]:
    value = json.loads(artifact.content.decode("utf-8"))
    return tuple(
        record["identity"]["path"][-1]
        for record in value["narrative"]["story"]["dialogues"]
    )


def test_baseline_ownership_and_protected_state() -> None:
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong branch")
    require(git("rev-parse", "HEAD") == EXPECTED_PREDECESSOR, "wrong HEAD")
    require(
        git("rev-parse", EXPECTED_TAG + "^{}") == EXPECTED_PREDECESSOR,
        "P11.6K freeze tag does not identify the exact predecessor",
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
    require(
        set(git("diff", "--name-only", "HEAD").splitlines()) == {RENDERER_FILE},
        "tracked ownership differs from the exact L renderer change",
    )
    require((root() / ".git").is_dir(), ".git is unavailable")
    require((root() / K_SMOKE).is_file(), "P11.6K focused smoke is unavailable")
    require(
        (root() / K_SMOKE).read_bytes()
        == subprocess.run(
            ("git", "show", f"HEAD:{K_SMOKE}"),
            cwd=root(),
            check=True,
            stdout=subprocess.PIPE,
        ).stdout,
        "frozen P11.6K smoke bytes changed",
    )
    for relative_path, expected_hash in PROTECTED_FIXTURES.items():
        observed = hashlib.sha256((root() / relative_path).read_bytes()).hexdigest()
        require(observed == expected_hash, f"protected fixture changed: {relative_path}")


def test_existing_order_artifact_material_and_rendering() -> None:
    authored = ("Zeta", "Elsewhere", "Alpha", "Middle")
    with TemporaryDirectory() as temporary_name:
        analysis, _, artifact, material, _ = build_material(
            Path(temporary_name), authored, "authored"
        )
        source_names = tuple(
            dialogue.name.text
            for dialogue in analysis.source_document.story.dialogues
        )
        require(source_names == authored, "source AST tuple lost declaration order")
        require(
            identity_names(analysis.semantic_story.dialogues) == authored,
            "lowering lost authored dialogue order",
        )
        require(
            artifact_dialogue_names(artifact) == authored,
            "artifact dialogue array lost authored order",
        )
        require(
            identity_names(material.dialogues) == authored,
            "material tuple lost artifact array order",
        )

        story = analysis.semantic_story
        session = create_narrative_session(
            material,
            NarrativeSessionCreateRequest(story.identity, story.scenes[0].identity),
        )
        presentation = narrative_session_presentation(material, session)
        current_order = identity_names(presentation.dialogues)
        require(
            current_order == ("Zeta", "Alpha", "Middle"),
            "current-scene filtering did not preserve surviving authored order",
        )
        require(presentation.title == "  Authored Title  ", "scene title changed")
        require(presentation.body == "Body first\nBody second", "scene body changed")
        require(
            tuple(item.text for item in presentation.dialogues)
            == (
                "  Zeta Ω first\nsecond\tline  ",
                "Alpha exact text",
                "Middle exact text",
            ),
            "dialogue text or UTF-8/whitespace content changed",
        )
        rendered = render_narrative_session(material, session)
        require("UNRELATED-SCENE-TEXT" not in rendered, "other-scene dialogue leaked")
        require(
            rendered.index("dialogue:Zeta")
            < rendered.index("dialogue:Alpha")
            < rendered.index("dialogue:Middle"),
            "rendering did not use authored dialogue order",
        )


def test_determinism_order_sensitive_artifact_and_semantic_isolation() -> None:
    first_order = ("Zeta", "Elsewhere", "Alpha", "Middle")
    reordered = ("Middle", "Elsewhere", "Alpha", "Zeta")
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        first = build_material(temporary_root, first_order, "first")
        repeated = build_material(temporary_root, first_order, "repeated")
        changed = build_material(temporary_root, reordered, "reordered")

        first_analysis, first_bindings, first_artifact, first_material, _ = first
        repeated_analysis, _, repeated_artifact, repeated_material, _ = repeated
        changed_analysis, changed_bindings, changed_artifact, changed_material, _ = changed

        require(first_analysis.semantic_story == repeated_analysis.semantic_story,
                "identical source changed semantic model")
        require(first_artifact.content == repeated_artifact.content,
                "identical source changed canonical artifact bytes")
        require(first_artifact.fingerprint == repeated_artifact.fingerprint,
                "identical source changed artifact fingerprint")
        require(first_material == repeated_material,
                "identical artifact changed session material")
        require(first_artifact.content != changed_artifact.content,
                "authored reorder did not change canonical artifact bytes")
        require(first_artifact.fingerprint != changed_artifact.fingerprint,
                "authored reorder did not change artifact fingerprint")

        first_dialogues = {
            dialogue.identity: (dialogue.scene, dialogue.speaker,
                                dialogue.participants, dialogue.text)
            for dialogue in first_analysis.semantic_story.dialogues
        }
        changed_dialogues = {
            dialogue.identity: (dialogue.scene, dialogue.speaker,
                                dialogue.participants, dialogue.text)
            for dialogue in changed_analysis.semantic_story.dialogues
        }
        require(first_dialogues == changed_dialogues,
                "authored reorder changed dialogue identity or content")
        require(first_analysis.semantic_story.identity == changed_analysis.semantic_story.identity,
                "authored reorder changed story identity")
        require(identity_names(first_analysis.semantic_story.scenes)
                == identity_names(changed_analysis.semantic_story.scenes),
                "authored reorder changed scene identities")
        require(first_bindings == changed_bindings,
                "passive dialogue order changed executable bindings")

        sessions = []
        direct_results = []
        step_results = []
        presentations = []
        rendered = []
        for analysis, bindings, _, material, _ in (first, changed):
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
            alpha_choice = NarrativeIdentity("choice", ("AlphaChoice",))
            direct_results.append(
                execute_narrative_request(
                    bindings,
                    NarrativeExecutionRequest(session.state, alpha_choice, 0),
                )
            )
            stepped = step_narrative_session(
                material,
                session,
                NarrativeSessionStepRequest(alpha_choice, 0),
            )
            require(stepped.session is not None, "explicit L isolation step failed")
            sessions.append(stepped.session)
            step_results.append(stepped.execution_result)
            presentation = narrative_session_presentation(material, session)
            presentations.append(presentation)
            rendered.append(render_narrative_presentation(presentation))
            serialized = narrative_session_bytes(session).decode("utf-8")
            require("Zeta Ω" not in serialized and "Alpha exact text" not in serialized,
                    "session serialization duplicated presentation ordering data")

        require(direct_results[0] == direct_results[1],
                "dialogue order changed one-shot execution result or diagnostics")
        require(step_results[0] == step_results[1],
                "dialogue order changed lifecycle execution result or diagnostics")
        require(sessions[0].state == sessions[1].state,
                "dialogue order changed destination, facts, progression, history, or termination")
        require(sessions[0].state.current_scene.path == ("MiddleScene",),
                "explicit destination changed")
        require(any(fact.name == "done" and fact.value == "yes"
                    for fact in sessions[0].state.facts),
                "explicit consequence did not preserve facts")
        require(presentations[0] != presentations[1],
                "different authored order did not change presentation")
        require(rendered[0] != rendered[1],
                "different authored order did not change rendered bytes")

        repeated_session = create_narrative_session(
            repeated_material,
            NarrativeSessionCreateRequest(
                repeated_analysis.semantic_story.identity,
                repeated_analysis.semantic_story.scenes[0].identity,
            ),
        )
        repeated_presentation = narrative_session_presentation(
            repeated_material, repeated_session
        )
        require(
            repeated_presentation
            == narrative_session_presentation(repeated_material, repeated_session),
            "repeated presentation changed",
        )
        require(
            render_narrative_presentation(repeated_presentation).encode("utf-8")
            == render_narrative_session(repeated_material, repeated_session).encode("utf-8"),
            "repeated rendered UTF-8 bytes changed",
        )


def test_schema_v1_v2_and_j_i_compatibility() -> None:
    authored = ("Zeta", "Elsewhere", "Alpha", "Middle")
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        analysis, _, artifact, material, artifact_path = build_material(
            temporary_root, authored, "v2"
        )
        require(NARRATIVE_BUILD_ARTIFACT_SCHEMA.endswith("/v2"),
                "L unnecessarily advanced the narrative artifact schema")
        require(identity_names(material.dialogues) == authored,
                "K v2 dialogue array order did not load")

        value = json.loads(artifact_path.read_text(encoding="utf-8"))
        value["narrative"]["schema"] = NARRATIVE_BUILD_ARTIFACT_SCHEMA_V1
        value["narrative"]["story"]["scenes"] = [
            {"identity": record["identity"]}
            for record in value["narrative"]["story"]["scenes"]
        ]
        for record in value["narrative"]["story"]["dialogues"]:
            del record["text"]
        del value["fingerprint"]
        fingerprint = hashlib.sha256(canonical_json_bytes(value)).hexdigest()
        value["fingerprint"] = {"algorithm": "sha256", "value": fingerprint}
        v1_path = temporary_root / "historical-v1.json"
        v1_path.write_bytes(canonical_json_bytes(value))
        v1_material = load_narrative_session_material(v1_path)
        require(identity_names(v1_material.dialogues) == authored,
                "historical v1 dialogue array order did not load")
        require(all(dialogue.text is None for dialogue in v1_material.dialogues),
                "historical v1 loading invented dialogue prose")

        story = analysis.semantic_story
        session = create_narrative_session(
            material,
            NarrativeSessionCreateRequest(story.identity, story.scenes[0].identity),
        )
        menu = narrative_interactive_menu(material, session)
        menu_contract = tuple(
            (item.number, item.choice.path[-1], item.path_index, item.path_label)
            for item in menu
        )
        require(
            menu_contract
            == ((1, "AlphaChoice", 0, "Continue"),
                (2, "ZetaChoice", 0, "Finish")),
            "P11.6I selection mapping or choice display ordering changed",
        )
        require(tuple(path.path_index for path in material.bindings.paths) == (0, 0),
                "path-index meaning changed")

        from p11_6i_interactive_narrative_session_ux_smoke_test import make_material

        _, _, old_material, old_session, _, _ = make_material(
            temporary_root, "NoProseL"
        )
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
                "historical no-prose P11.6J bytes changed")
        require(artifact.content.endswith(b"\n"), "canonical artifact lost final LF")


def test_no_semantic_sorting_schema_growth_or_autonomy() -> None:
    renderer_path = root() / RENDERER_FILE
    source = renderer_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    presenter = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "narrative_session_presentation"
    )
    dialogue_assignments = [
        node
        for node in ast.walk(presenter)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "dialogues"
                for target in node.targets)
    ]
    require(len(dialogue_assignments) == 1,
            "dialogue presentation projection is not singular and explicit")
    dialogue_calls = {
        node.func.id
        for node in ast.walk(dialogue_assignments[0].value)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    require(not dialogue_calls.intersection({"sorted", "sort", "enumerate"}),
            "dialogue presentation infers a sort or manufactured ordinal")
    require("_dialogue_key" not in source,
            "K dialogue identity sorting remains in the renderer")

    forbidden_fields = {"order", "ordinal", "sequence", "priority", "weight", "rank"}
    require(not forbidden_fields.intersection(NarrativeDialogue.__dataclass_fields__),
            "NarrativeDialogue gained speculative ordering metadata")
    require(not forbidden_fields.intersection(NarrativeScene.__dataclass_fields__),
            "NarrativeScene gained speculative ordering metadata")

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
    forbidden_imports = {
        "random", "time", "subprocess", "socket", "requests", "urllib",
        "openai", "anthropic",
    }
    require(not imports.intersection(forbidden_imports),
            "renderer acquired random, time, process, network, or AI authority")
    lower_source = source.lower()
    require(not any(term in lower_source for term in (
        "recommendation", "relevance score", "semantic score",
        "dialogue generation", "llm",
    )), "renderer acquired recommendation, scoring, or generation machinery")


def main() -> int:
    test_baseline_ownership_and_protected_state()
    test_existing_order_artifact_material_and_rendering()
    test_determinism_order_sensitive_artifact_and_semantic_isolation()
    test_schema_v1_v2_and_j_i_compatibility()
    test_no_semantic_sorting_schema_growth_or_autonomy()
    print("P11.6L canonical narrative content ordering smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
