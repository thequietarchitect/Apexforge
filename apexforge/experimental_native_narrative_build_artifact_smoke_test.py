"""Experimental native narrative build-artifact smoke test."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from language.narrative_analysis import analyze_narrative_source
from language.project import build_project
from runtime.narrative_binding import bind_narrative_story
from tooling.build_artifact import (
    BUILD_ARTIFACT_SCHEMA,
    BUILD_ARTIFACT_SCHEMA_V2,
    canonical_json_bytes,
    construct_build_artifact,
    construct_narrative_build_artifact,
    write_build_artifact_atomic,
)
from tooling.narrative_artifact import (
    NARRATIVE_BUILD_ARTIFACT_SCHEMA,
    route_narrative_build_material,
)
from tooling.narrative_execution import load_narrative_execution_material
from tooling.narrative_session import load_narrative_session_material
from tooling.project_loader import load_project


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_project(root: Path, *, name: str, source: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "story.apex").write_text(source, encoding="utf-8")
    (root / "apexforge.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": name,
                "sources": ["story.apex"],
                "entry": name,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


def main() -> None:
    source = """story NativeStory {
    character Traveler
    scene Start {
        body "Native narrative artifact."
    }
    timeline Main {
        scenes [Start]
    }
}
"""

    with TemporaryDirectory() as directory:
        root = Path(directory)
        narrative_root = root / "narrative"
        write_project(narrative_root, name="NativeStory", source=source)

        loaded = load_project(narrative_root)
        analysis = analyze_narrative_source(source, source_name="story.apex")
        bindings = bind_narrative_story(analysis.semantic_story)
        narrative = route_narrative_build_material(
            analysis,
            bindings,
            source_name="story.apex",
        )
        artifact = construct_narrative_build_artifact(loaded, narrative)
        value = json.loads(artifact.content.decode("utf-8"))

        require(
            value["schema"] == BUILD_ARTIFACT_SCHEMA_V2 == "apexforge.build-artifact/v2",
            "native narrative top-level schema changed",
        )
        require("air" not in value, "native narrative artifact still contains AIR")
        require(
            frozenset(value) == frozenset(("fingerprint", "narrative", "project", "schema")),
            "native narrative top-level shape changed",
        )
        require(
            value["project"]["entry"] == "story:NativeStory",
            "native narrative project entry identity changed",
        )
        require(
            value["project"]["name"] == "NativeStory"
            and value["project"]["source_count"] == 1
            and value["project"]["sources"][0]["path"] == "story.apex",
            "native narrative project metadata changed",
        )
        require(
            value["narrative"]["schema"] == NARRATIVE_BUILD_ARTIFACT_SCHEMA,
            "nested narrative schema changed",
        )

        payload = dict(value)
        fingerprint = payload.pop("fingerprint")
        expected = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
        require(
            fingerprint == {"algorithm": "sha256", "value": expected},
            "native narrative fingerprint changed",
        )
        require(
            artifact.entry == "story:NativeStory"
            and artifact.narrative_artifact == narrative,
            "native narrative in-memory metadata changed",
        )

        artifact_path = root / "native-build.json"
        write_build_artifact_atomic(artifact, artifact_path)
        require(
            load_narrative_execution_material(artifact_path) == bindings,
            "execution loader rejected native narrative artifact",
        )
        material = load_narrative_session_material(artifact_path)
        require(
            material.story == analysis.semantic_story.identity
            and material.artifact_fingerprint == expected,
            "session loader rejected native narrative artifact",
        )

        air_root = root / "air"
        air_root.mkdir()
        (air_root / "main.apex").write_text("directive Main {}", encoding="utf-8")
        (air_root / "apexforge.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "name": "AirProject",
                    "sources": ["main.apex"],
                    "entry": "Main",
                },
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        air_loaded = load_project(air_root)
        air_build = build_project(air_loaded.source_mapping(), entry="Main")
        air_artifact = construct_build_artifact(air_loaded, air_build)
        air_value = json.loads(air_artifact.content.decode("utf-8"))
        require(
            air_value["schema"] == BUILD_ARTIFACT_SCHEMA == "apexforge.build-artifact/v1",
            "ordinary AIR top-level schema changed",
        )
        require(
            "air" in air_value and "narrative" not in air_value,
            "ordinary AIR artifact shape changed",
        )

    print("Native narrative top-level artifact: PASS")
    print("Native narrative execution loader compatibility: PASS")
    print("Native narrative session loader compatibility: PASS")
    print("AIR build-artifact v1 compatibility: PASS")
    print("Experimental native narrative build artifact: PASS")


if __name__ == "__main__":
    main()
