"""Executable contract for the P11.5B minimal narrative semantic model."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, MISSING, fields, is_dataclass, replace
import hashlib
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from language.grammar import GRAMMAR_KEYWORD_TOKENS, TOP_LEVEL_DECLARATIONS
from language.lexer import KEYWORDS
import language.narrative_model as narrative_module
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
from p11_4d_passive_resolver_candidate_index_smoke_test import (
    repository_bytecode_state,
    repository_status,
)
from p11_5a_narrative_semantic_foundation_architecture_audit_smoke_test import (
    test_temporary_fixture_and_accepted_compatibility as accepted_compatibility,
)


PACKAGE_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_DIRECTORY.parent
MODEL_PATH = PACKAGE_DIRECTORY / "language" / "narrative_model.py"
DOCUMENT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "p11"
    / "P11_5B_MINIMAL_NARRATIVE_SEMANTIC_MODEL_CONTRACT.md"
)
P11_4H_COMMIT = "c6570766703d00bba4e1aff7d712a0d271c9ecc1"
P11_5A_COMMIT = "3349617a689eb0d9c9849dc604f749d7951d62a0"
P11_5A_TAG = "afp-p11.5a-freeze"
P11_5A_TAG_OBJECT = "983be9ef48d9f09cecb125810ab420e7c388eada"
P11_5A_DOCUMENT = (
    REPOSITORY_ROOT
    / "docs"
    / "p11"
    / "P11_5A_NARRATIVE_SEMANTIC_FOUNDATION_ARCHITECTURE_AUDIT.md"
)
P11_5A_DOCUMENT_SHA256 = (
    "556090dbd5b6844f537d0cfb6f6a3b3fea7acdb770857aeb6e0b0c7e4230db46"
)
P11_5A_OWNED_PATHS = {
    "apexforge/p11_5a_narrative_semantic_foundation_architecture_audit_smoke_test.py",
    "docs/p11/P11_5A_NARRATIVE_SEMANTIC_FOUNDATION_ARCHITECTURE_AUDIT.md",
}
P11_5B_OWNED_PATHS = {
    "apexforge/language/narrative_model.py",
    "apexforge/p11_5b_minimal_narrative_semantic_model_smoke_test.py",
    "docs/p11/P11_5B_MINIMAL_NARRATIVE_SEMANTIC_MODEL_CONTRACT.md",
}
P11_5B_WORKING_PATHS = P11_5B_OWNED_PATHS | {
    "apexforge/p11_5a_narrative_semantic_foundation_architecture_audit_smoke_test.py"
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as error:
        return error
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


def paths_since(commit: str) -> set[str]:
    paths: set[str] = set()
    for arguments in (
        ("diff", "--name-only", f"{commit}..HEAD"),
        ("diff", "--name-only"),
        ("diff", "--cached", "--name-only"),
        ("ls-files", "--others", "--exclude-standard"),
    ):
        paths.update(git_lines(*arguments))
    return paths


def production_python_files() -> tuple[Path, ...]:
    return tuple(
        sorted(
            path
            for path in PACKAGE_DIRECTORY.rglob("*.py")
            if not path.name.endswith("_smoke_test.py") and "tests" not in path.parts
        )
    )


def identity(kind: str, *path: str) -> NarrativeIdentity:
    return NarrativeIdentity(kind, path)


def test_frozen_baseline_and_exact_ownership(document: str) -> None:
    normalized = " ".join(document.split())
    require(P11_5A_COMMIT in document, "document omits exact P11.5A commit")
    require(P11_5A_TAG in document, "document omits exact P11.5A tag")
    require(P11_5A_TAG_OBJECT in document, "document omits exact P11.5A tag object")
    require(
        "P11.5A remains the frozen predecessor" in normalized,
        "document does not preserve P11.5A as predecessor",
    )
    require(
        git_lines("cat-file", "-t", P11_5A_TAG) == ("tag",)
        and git_lines("rev-parse", P11_5A_TAG) == (P11_5A_TAG_OBJECT,)
        and git_lines("rev-list", "-n", "1", P11_5A_TAG) == (P11_5A_COMMIT,),
        "P11.5A freeze identity changed",
    )
    require(
        paths_since(P11_5A_COMMIT) == P11_5B_WORKING_PATHS,
        "P11.5B working change set is not the exact four reviewed paths",
    )
    require(
        paths_since(P11_4H_COMMIT) == P11_5A_OWNED_PATHS | P11_5B_OWNED_PATHS,
        "complete branch delta is not the exact five reviewed paths",
    )
    require(
        hashlib.sha256(P11_5A_DOCUMENT.read_bytes()).hexdigest()
        == P11_5A_DOCUMENT_SHA256,
        "frozen P11.5A documentation changed",
    )
    require(
        MODEL_PATH.exists() and DOCUMENT_PATH.exists(),
        "a P11.5B-owned file is missing",
    )


def test_public_api_fields_and_frozen_records() -> None:
    expected_exports = (
        "NarrativeIdentity",
        "NarrativeCharacter",
        "NarrativeScene",
        "NarrativeDialogue",
        "NarrativeChoicePath",
        "NarrativeChoice",
        "NarrativePerspective",
        "NarrativeTimeline",
        "NarrativeStateFact",
        "NarrativeState",
        "NarrativeContinuityConstraint",
        "NarrativeContinuity",
        "NarrativeStory",
    )
    require(narrative_module.__all__ == expected_exports, "public exports changed")
    source = MODEL_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    public_classes = {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    }
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    require(public_classes == set(expected_exports), "public record class set changed")
    require(not public_functions, "narrative model exposes a public function")
    forbidden_surface = (
        "Builder",
        "Validator",
        "Resolver",
        "Serializer",
        "Registry",
        "Cache",
    )
    require(
        all(token not in name for name in public_classes for token in forbidden_surface),
        "narrative model exposes an operational public type",
    )

    expected_fields = {
        NarrativeIdentity: ("kind", "path"),
        NarrativeCharacter: ("identity",),
        NarrativeScene: ("identity",),
        NarrativeDialogue: ("identity", "scene", "speaker", "participants"),
        NarrativeChoicePath: ("label", "destination", "condition", "consequence"),
        NarrativeChoice: ("identity", "scene", "paths"),
        NarrativePerspective: ("identity", "viewpoint"),
        NarrativeTimeline: ("identity", "scenes"),
        NarrativeStateFact: ("subject", "name", "value"),
        NarrativeState: ("identity", "facts"),
        NarrativeContinuityConstraint: ("subjects", "assertion"),
        NarrativeContinuity: ("identity", "constraints"),
        NarrativeStory: (
            "identity",
            "characters",
            "scenes",
            "dialogues",
            "choices",
            "perspectives",
            "timelines",
            "states",
            "continuities",
        ),
    }
    for record_type, names in expected_fields.items():
        record_fields = fields(record_type)
        require(
            is_dataclass(record_type)
            and record_type.__dataclass_params__.frozen
            and tuple(item.name for item in record_fields) == names,
            f"{record_type.__name__} dataclass contract changed",
        )
        require(
            all(
                item.default is MISSING or item.default is None
                for item in record_fields
            )
            and all(item.default_factory is MISSING for item in record_fields),
            f"{record_type.__name__} acquired a mutable or generated default",
        )
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name not in public_classes:
            continue
        method_names = {
            item.name
            for item in node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        require(
            method_names <= {"__post_init__"},
            f"{node.name} acquired custom equality, ordering, or behavior",
        )


def test_identity_validation_and_preservation() -> None:
    kinds = (
        "story",
        "character",
        "scene",
        "dialogue",
        "choice",
        "perspective",
        "timeline",
        "narrative_state",
        "continuity",
    )
    values = tuple(NarrativeIdentity(kind, ("Root", kind)) for kind in kinds)
    require(
        tuple(value.kind for value in values) == kinds,
        "supported identity-kind vocabulary changed",
    )
    require_raises(ValueError, lambda: NarrativeIdentity("unknown", ("Name",)), "unsupported kind accepted")
    require_raises(TypeError, lambda: NarrativeIdentity(1, ("Name",)), "non-string kind accepted")
    require_raises(TypeError, lambda: NarrativeIdentity("story", ["Name"]), "list path accepted")
    require_raises(ValueError, lambda: NarrativeIdentity("story", ()), "empty path accepted")
    require_raises(ValueError, lambda: NarrativeIdentity("story", ("",)), "empty segment accepted")
    require_raises(ValueError, lambda: NarrativeIdentity("story", ("  ",)), "blank segment accepted")
    require_raises(ValueError, lambda: NarrativeIdentity("story", (" Name",)), "leading whitespace accepted")
    require_raises(ValueError, lambda: NarrativeIdentity("story", ("Name ",)), "trailing whitespace accepted")

    class TextSubclass(str):
        pass

    class TupleSubclass(tuple):
        pass

    require_raises(TypeError, lambda: NarrativeIdentity(TextSubclass("story"), ("Name",)), "kind subclass accepted")
    require_raises(TypeError, lambda: NarrativeIdentity("story", TupleSubclass(("Name",))), "tuple subclass accepted")
    require_raises(TypeError, lambda: NarrativeIdentity("story", (TextSubclass("Name"),)), "segment subclass accepted")
    exact = NarrativeIdentity("character", ("Zed", "alpha", "MiXeD"))
    require(
        exact.path == ("Zed", "alpha", "MiXeD")
        and exact.path[0] == "Zed"
        and exact.path[-1] == "MiXeD",
        "identity spelling, case, or segment order changed",
    )
    require(
        tuple(item.name for item in fields(NarrativeIdentity)) == ("kind", "path"),
        "identity acquired a generated ID field",
    )


def test_record_specific_validation() -> None:
    story_id = identity("story", "Story")
    character_id = identity("character", "Character")
    scene_id = identity("scene", "Scene")
    dialogue_id = identity("dialogue", "Dialogue")
    choice_id = identity("choice", "Choice")
    perspective_id = identity("perspective", "Perspective")
    timeline_id = identity("timeline", "Timeline")
    state_id = identity("narrative_state", "State")
    continuity_id = identity("continuity", "Continuity")

    NarrativeCharacter(character_id)
    NarrativeScene(scene_id)
    for record_type, wrong in (
        (NarrativeCharacter, scene_id),
        (NarrativeScene, character_id),
    ):
        require_raises((TypeError, ValueError), lambda record_type=record_type, wrong=wrong: record_type(wrong), "kind-specific identity accepted wrong value")

    dialogue = NarrativeDialogue(dialogue_id, scene_id, character_id, (character_id,))
    require_raises(ValueError, lambda: NarrativeDialogue(scene_id, scene_id, character_id, (character_id,)), "dialogue identity kind ignored")
    require_raises(ValueError, lambda: NarrativeDialogue(dialogue_id, character_id, character_id, (character_id,)), "dialogue scene kind ignored")
    require_raises(ValueError, lambda: NarrativeDialogue(dialogue_id, scene_id, scene_id, (character_id,)), "dialogue speaker kind ignored")
    require_raises(TypeError, lambda: NarrativeDialogue(dialogue_id, scene_id, character_id, [character_id]), "dialogue participant list accepted")
    require_raises(ValueError, lambda: NarrativeDialogue(dialogue_id, scene_id, character_id, ()), "empty dialogue participants accepted")
    require_raises(ValueError, lambda: NarrativeDialogue(dialogue_id, scene_id, character_id, (scene_id,)), "non-character participant accepted")

    path = NarrativeChoicePath("Continue", scene_id, "ready", "revealed")
    require_raises(ValueError, lambda: NarrativeChoicePath("", scene_id), "blank choice label accepted")
    require_raises(ValueError, lambda: NarrativeChoicePath(" Continue", scene_id), "untrimmed choice label accepted")
    require_raises(ValueError, lambda: NarrativeChoicePath("Continue", character_id), "non-scene destination accepted")
    for condition, consequence in (("", None), (" ready", None), (None, ""), (None, "done ")):
        require_raises(ValueError, lambda condition=condition, consequence=consequence: NarrativeChoicePath("Continue", scene_id, condition, consequence), "invalid optional choice text accepted")
    require_raises(TypeError, lambda: NarrativeChoicePath("Continue", scene_id, 1), "non-string condition accepted")

    NarrativeChoice(choice_id, scene_id, (path,))
    require_raises(ValueError, lambda: NarrativeChoice(scene_id, scene_id, (path,)), "choice identity kind ignored")
    require_raises(ValueError, lambda: NarrativeChoice(choice_id, character_id, (path,)), "choice scene kind ignored")
    require_raises(TypeError, lambda: NarrativeChoice(choice_id, scene_id, [path]), "choice path list accepted")
    require_raises(ValueError, lambda: NarrativeChoice(choice_id, scene_id, ()), "empty choice paths accepted")
    require_raises(TypeError, lambda: NarrativeChoice(choice_id, scene_id, (object(),)), "malformed choice path accepted")

    NarrativePerspective(perspective_id)
    NarrativePerspective(perspective_id, character_id)
    require_raises(ValueError, lambda: NarrativePerspective(scene_id), "perspective identity kind ignored")
    require_raises(ValueError, lambda: NarrativePerspective(perspective_id, scene_id), "non-character viewpoint accepted")
    require_raises(TypeError, lambda: NarrativePerspective(perspective_id, object()), "malformed viewpoint accepted")

    NarrativeTimeline(timeline_id, ())
    NarrativeTimeline(timeline_id, (scene_id,))
    require_raises(ValueError, lambda: NarrativeTimeline(scene_id, ()), "timeline identity kind ignored")
    require_raises(TypeError, lambda: NarrativeTimeline(timeline_id, [scene_id]), "timeline scene list accepted")
    require_raises(ValueError, lambda: NarrativeTimeline(timeline_id, (character_id,)), "timeline non-scene accepted")

    fact = NarrativeStateFact(character_id, "Mood", "Calm")
    require_raises(TypeError, lambda: NarrativeStateFact(object(), "Mood", "Calm"), "malformed state subject accepted")
    for name, value in (("", "Calm"), (" Mood", "Calm"), ("Mood", ""), ("Mood", "Calm ")):
        require_raises(ValueError, lambda name=name, value=value: NarrativeStateFact(character_id, name, value), "invalid state fact text accepted")
    require_raises(TypeError, lambda: NarrativeStateFact(character_id, 1, "Calm"), "non-string fact name accepted")
    NarrativeState(state_id, ())
    NarrativeState(state_id, (fact,))
    require_raises(ValueError, lambda: NarrativeState(scene_id, ()), "state identity kind ignored")
    require_raises(TypeError, lambda: NarrativeState(state_id, [fact]), "state fact list accepted")
    require_raises(TypeError, lambda: NarrativeState(state_id, (object(),)), "malformed state fact accepted")

    constraint = NarrativeContinuityConstraint((character_id,), "Mood remains known")
    require_raises(TypeError, lambda: NarrativeContinuityConstraint([character_id], "Known"), "constraint subject list accepted")
    require_raises(ValueError, lambda: NarrativeContinuityConstraint((), "Known"), "empty constraint subjects accepted")
    require_raises(TypeError, lambda: NarrativeContinuityConstraint((object(),), "Known"), "malformed constraint subject accepted")
    require_raises(ValueError, lambda: NarrativeContinuityConstraint((character_id,), " "), "blank assertion accepted")
    NarrativeContinuity(continuity_id, ())
    NarrativeContinuity(continuity_id, (constraint,))
    require_raises(ValueError, lambda: NarrativeContinuity(scene_id, ()), "continuity identity kind ignored")
    require_raises(TypeError, lambda: NarrativeContinuity(continuity_id, [constraint]), "constraint list accepted")
    require_raises(TypeError, lambda: NarrativeContinuity(continuity_id, (object(),)), "malformed constraint accepted")

    empty_story = NarrativeStory(story_id, (), (), (), (), (), (), (), ())
    require(empty_story.identity is story_id, "empty passive story rejected")
    require_raises(ValueError, lambda: NarrativeStory(scene_id, (), (), (), (), (), (), (), ()), "story identity kind ignored")
    valid_collections = {
        "characters": (NarrativeCharacter(character_id),),
        "scenes": (NarrativeScene(scene_id),),
        "dialogues": (dialogue,),
        "choices": (NarrativeChoice(choice_id, scene_id, (path,)),),
        "perspectives": (NarrativePerspective(perspective_id),),
        "timelines": (NarrativeTimeline(timeline_id, (scene_id,)),),
        "states": (NarrativeState(state_id, (fact,)),),
        "continuities": (NarrativeContinuity(continuity_id, (constraint,)),),
    }
    NarrativeStory(story_id, **valid_collections)
    for name, values in valid_collections.items():
        malformed = dict(valid_collections)
        malformed[name] = list(values)
        require_raises(TypeError, lambda malformed=malformed: NarrativeStory(story_id, **malformed), f"story accepted list for {name}")
        malformed = dict(valid_collections)
        malformed[name] = (object(),)
        require_raises(TypeError, lambda malformed=malformed: NarrativeStory(story_id, **malformed), f"story accepted wrong record for {name}")


def test_immutability_exact_types_order_and_duplicates() -> None:
    story_id = identity("story", "Story")
    character_z = identity("character", "Zed")
    character_a = identity("character", "Alpha")
    scene_z = identity("scene", "Zed")
    scene_a = identity("scene", "Alpha")
    dialogue_id = identity("dialogue", "Dialogue")
    choice_id = identity("choice", "Choice")
    perspective_id = identity("perspective", "Perspective")
    timeline_id = identity("timeline", "Timeline")
    state_id = identity("narrative_state", "State")
    continuity_id = identity("continuity", "Continuity")
    character = NarrativeCharacter(character_z)
    scene = NarrativeScene(scene_z)
    dialogue = NarrativeDialogue(dialogue_id, scene_z, character_z, (character_z, character_z))
    path = NarrativeChoicePath("Path", scene_a, "condition", "consequence")
    choice = NarrativeChoice(choice_id, scene_z, (path, path))
    perspective = NarrativePerspective(perspective_id, character_z)
    timeline = NarrativeTimeline(timeline_id, (scene_z, scene_a, scene_z))
    fact = NarrativeStateFact(character_z, "Mood", "Calm")
    state = NarrativeState(state_id, (fact, fact))
    constraint = NarrativeContinuityConstraint((character_z, character_z), "Stable")
    continuity = NarrativeContinuity(continuity_id, (constraint, constraint))
    story = NarrativeStory(
        story_id,
        (character, character, NarrativeCharacter(character_a)),
        (scene, scene, NarrativeScene(scene_a)),
        (dialogue,),
        (choice, choice),
        (perspective,),
        (timeline,),
        (state,),
        (continuity,),
    )
    records = (
        story_id,
        character,
        scene,
        dialogue,
        path,
        choice,
        perspective,
        timeline,
        fact,
        state,
        constraint,
        continuity,
        story,
    )
    for record in records:
        first_field = fields(type(record))[0].name
        require_raises(FrozenInstanceError, lambda record=record, first_field=first_field: setattr(record, first_field, getattr(record, first_field)), f"{type(record).__name__} allowed mutation")
        require(replace(record) == record and hash(replace(record)) == hash(record), f"{type(record).__name__} lost structural equality or hashing")
    require(
        dialogue.identity is dialogue_id
        and dialogue.scene is scene_z
        and dialogue.speaker is character_z
        and dialogue.participants == (character_z, character_z)
        and dialogue.participants[0] is dialogue.participants[1],
        "dialogue references or duplicate participants changed",
    )
    require(choice.paths == (path, path) and choice.paths[0] is choice.paths[1], "duplicate choice paths changed")
    require(timeline.scenes == (scene_z, scene_a, scene_z), "timeline order or duplicate scenes changed")
    require(state.facts == (fact, fact) and state.facts[0] is state.facts[1], "duplicate state facts changed")
    require(continuity.constraints == (constraint, constraint), "duplicate continuity constraints changed")
    require(
        tuple(item.identity.path[-1] for item in story.characters) == ("Zed", "Zed", "Alpha")
        and tuple(item.identity.path[-1] for item in story.scenes) == ("Zed", "Zed", "Alpha")
        and story.choices == (choice, choice),
        "story sorted or deduplicated caller tuples",
    )

    class IdentitySubclass(NarrativeIdentity):
        pass

    class CharacterSubclass(NarrativeCharacter):
        pass

    identity_subclass = IdentitySubclass("character", ("Subclass",))
    character_subclass = CharacterSubclass(character_z)
    require_raises(TypeError, lambda: NarrativeCharacter(identity_subclass), "identity subclass accepted")
    require_raises(TypeError, lambda: NarrativeDialogue(dialogue_id, scene_z, identity_subclass, (character_z,)), "nested identity subclass accepted")
    require_raises(TypeError, lambda: NarrativeStory(story_id, (character_subclass,), (), (), (), (), (), (), ()), "record subclass accepted")


def test_structural_only_unresolved_contradictory_boundary() -> None:
    story_id = identity("story", "Story")
    missing_scene = identity("scene", "MissingScene")
    missing_character = identity("character", "MissingCharacter")
    dialogue = NarrativeDialogue(
        identity("dialogue", "UnresolvedDialogue"),
        missing_scene,
        missing_character,
        (missing_character,),
    )
    path = NarrativeChoicePath("Absent destination", missing_scene, "never", "none")
    choice = NarrativeChoice(identity("choice", "Unreachable"), missing_scene, (path,))
    timeline = NarrativeTimeline(identity("timeline", "Impossible"), (missing_scene, missing_scene))
    fact_true = NarrativeStateFact(missing_character, "Known", "true")
    fact_false = NarrativeStateFact(missing_character, "Known", "false")
    state = NarrativeState(identity("narrative_state", "Contradiction"), (fact_true, fact_false))
    yes = NarrativeContinuityConstraint((missing_character,), "Identity is present")
    no = NarrativeContinuityConstraint((missing_character,), "Identity is absent")
    continuity = NarrativeContinuity(identity("continuity", "Contradiction"), (yes, no))
    duplicate_character = NarrativeCharacter(missing_character)
    story = NarrativeStory(
        story_id,
        (duplicate_character, duplicate_character),
        (),
        (dialogue,),
        (choice,),
        (),
        (timeline,),
        (state,),
        (continuity,),
    )
    require(
        story.scenes == ()
        and story.dialogues[0].scene is missing_scene
        and story.dialogues[0].speaker is missing_character
        and story.choices[0].paths[0].destination is missing_scene
        and story.timelines[0].scenes == (missing_scene, missing_scene)
        and story.characters[0] is story.characters[1]
        and story.states[0].facts == (fact_true, fact_false)
        and story.continuities[0].constraints == (yes, no),
        "structural model rejected or rewrote unresolved or contradictory facts",
    )


def test_production_protection_and_no_integration() -> None:
    narrative_keywords = {"story", "character", "scene", "dialogue", "choice"}
    require(
        narrative_keywords.isdisjoint(KEYWORDS)
        and narrative_keywords.isdisjoint(GRAMMAR_KEYWORD_TOKENS)
        and narrative_keywords.isdisjoint(TOP_LEVEL_DECLARATIONS),
        "storytelling syntax or grammar declaration exists",
    )
    parser_text = (PACKAGE_DIRECTORY / "language" / "parser.py").read_text(encoding="utf-8")
    require(all(f"parse_{item}" not in parser_text for item in narrative_keywords), "storytelling parser path exists")

    graph_markers = (
        "NarrativeSemanticGraph",
        "NarrativeGraph",
        "NarrativeNode",
        "NarrativeEdge",
        "NarrativeGraphBuilder",
        "build_narrative_graph",
    )
    diagnostic_markers = ("APX-NARRATIVE-", "APX-STORY-", "APX-CONTINUITY-")
    model_text = MODEL_PATH.read_text(encoding="utf-8")
    require(all(marker not in model_text for marker in graph_markers), "graph declaration or builder exists")
    require(all(marker not in model_text for marker in diagnostic_markers), "narrative diagnostic exists")
    require("BuildDiagnostic" not in model_text, "narrative model imports diagnostic machinery")

    consumer_files: set[str] = set()
    narrative_declaration_files: set[str] = set()
    all_production_text = []
    for path in production_python_files():
        text = path.read_text(encoding="utf-8")
        all_production_text.append(text)
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        if "NarrativeIdentity" in text or "language.narrative_model" in text:
            consumer_files.add(relative)
        tree = ast.parse(text, filename=str(path))
        if any(isinstance(node, ast.ClassDef) and node.name == "NarrativeIdentity" for node in ast.walk(tree)):
            narrative_declaration_files.add(relative)
    expected = {"apexforge/language/narrative_model.py"}
    combined = "\n".join(all_production_text)
    require(consumer_files == expected and narrative_declaration_files == expected, "narrative model escaped its one-file production boundary")
    require(all(marker not in combined for marker in graph_markers), "graph type exists in production")
    require(all(marker not in combined for marker in diagnostic_markers), "narrative diagnostic code exists")

    init_path = PACKAGE_DIRECTORY / "language" / "__init__.py"
    baseline_init = subprocess.run(
        ["git", "show", f"{P11_5A_COMMIT}:apexforge/language/__init__.py"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    ).stdout
    require(init_path.read_bytes() == baseline_init, "language.__init__ changed or re-exported narrative records")
    require(
        paths_since(P11_5A_COMMIT) == P11_5B_WORKING_PATHS,
        "syntax, project, AIR, artifact, runtime, CLI, or tooling path changed",
    )


def test_temporary_fixture_compatibility_and_safety() -> None:
    original_directory = Path.cwd().resolve()
    temporary_path: Path
    with TemporaryDirectory(prefix="apexforge-p11-5b-") as temporary:
        temporary_path = Path(temporary).resolve()
        try:
            temporary_path.relative_to(REPOSITORY_ROOT.resolve())
        except ValueError:
            pass
        else:
            raise AssertionError("temporary fixture was created in the repository")
        require(Path.cwd().resolve() == original_directory, "temporary fixture changed cwd")
    require(not temporary_path.exists(), "temporary fixture escaped its context manager")
    accepted_compatibility()


def main() -> None:
    original_directory = Path.cwd().resolve()
    status_before = repository_status()
    bytecode_before = repository_bytecode_state()
    document = DOCUMENT_PATH.read_text(encoding="utf-8")

    def forbidden_network(*_args, **_kwargs):
        raise AssertionError("P11.5B attempted network access")

    with patch("socket.create_connection", side_effect=forbidden_network), patch(
        "socket.socket", side_effect=forbidden_network
    ):
        test_frozen_baseline_and_exact_ownership(document)
        test_public_api_fields_and_frozen_records()
        test_identity_validation_and_preservation()
        test_record_specific_validation()
        test_immutability_exact_types_order_and_duplicates()
        test_structural_only_unresolved_contradictory_boundary()
        test_production_protection_and_no_integration()
        test_temporary_fixture_compatibility_and_safety()

    require(Path.cwd().resolve() == original_directory, "working directory changed")
    require(repository_status() == status_before, "running the test changed Git status")
    require(repository_bytecode_state() == bytecode_before, "running the test changed bytecode state")
    print("AFP-P11.5B minimal narrative semantic model smoke test passed.")
    print("Frozen P11.5A baseline and exact ownership deltas: PASS")
    print("Exact thirteen-record public API, fields, and frozen dataclasses: PASS")
    print("Strict identity and record-specific structural validation: PASS")
    print("Exact references, order, duplicates, equality, hashing, and immutability: PASS")
    print("Unresolved references and contradictions remain passive facts: PASS")
    print("No syntax, graph, diagnostics, serialization, or integration: PASS")
    print("P11.5A/P11.4H compatibility reuse and repository safety: PASS")


if __name__ == "__main__":
    main()
