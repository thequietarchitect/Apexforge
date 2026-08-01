"""AFP-P10-T1.1 project-manifest and source-loading smoke test."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tooling import (
    P10_T1_TOOLING_VERSION,
    PROJECT_MANIFEST_NAME,
    ProjectManifest,
    ProjectManifestError,
    find_project_manifest,
    load_project,
    load_project_manifest,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_error(operation, code: str) -> ProjectManifestError:
    try:
        operation()
    except ProjectManifestError as error:
        require(
            error.code == code,
            f"expected {code}, received {error.code}",
        )
        return error
    raise AssertionError(f"operation unexpectedly succeeded; expected {code}")


def write_manifest(root: Path, value) -> Path:
    path = root / PROJECT_MANIFEST_NAME
    path.write_text(
        json.dumps(value, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> None:
    require(
        P10_T1_TOOLING_VERSION == "10-T1.1",
        "tooling version changed",
    )

    manifest = ProjectManifest(
        name="Demo_Project",
        sources=(
            r"src\zeta.future",
            "src/Main.apx",
        ),
        entry="Main",
    )
    require(
        manifest.sources == ("src/Main.apx", "src/zeta.future"),
        "source paths were not normalized and sorted canonically",
    )
    require(
        manifest.entry == "Main",
        "entry normalization changed",
    )
    require(
        '"schema": 1' in manifest.canonical_json(),
        "canonical JSON omitted schema",
    )

    require_error(
        lambda: ProjectManifest(
            name="bad name",
            sources=("src/main.apx",),
        ),
        "APX-TOOL-004",
    )
    require_error(
        lambda: ProjectManifest(
            name="Demo",
            sources=("../outside.apx",),
        ),
        "APX-TOOL-005",
    )
    require_error(
        lambda: ProjectManifest(
            name="Demo",
            sources=("src/Main.apx", "SRC/main.apx"),
        ),
        "APX-TOOL-005",
    )

    with TemporaryDirectory() as temporary:
        root = Path(temporary) / "demo"
        nested = root / "src" / "nested"
        nested.mkdir(parents=True)

        (root / "src" / "Main.apx").write_text(
            'directive Main { message "ready" }\n',
            encoding="utf-8",
        )
        (root / "src" / "zeta.future").write_text(
            "function Identity(value : int) : int { return value }\n",
            encoding="utf-8",
        )

        manifest_path = write_manifest(
            root,
            {
                "schema": 1,
                "name": "Demo",
                "sources": [
                    "src/zeta.future",
                    "src/Main.apx",
                ],
                "entry": "Main",
            },
        )

        found = find_project_manifest(nested)
        require(
            found == manifest_path.resolve(),
            "ancestor manifest discovery failed",
        )

        loaded_manifest = load_project_manifest(manifest_path)
        require(
            loaded_manifest.sources
            == ("src/Main.apx", "src/zeta.future"),
            "manifest loading lost canonical source order",
        )

        loaded = load_project(nested)
        require(
            loaded.root == root.resolve(),
            "project root resolution changed",
        )
        require(
            tuple(source.name for source in loaded.sources)
            == loaded.manifest.sources,
            "source snapshot order diverged from manifest",
        )
        require(
            tuple(loaded.source_mapping())
            == ("src/Main.apx", "src/zeta.future"),
            "read-only source mapping order changed",
        )
        require(
            "directive Main" in loaded.source_mapping()["src/Main.apx"],
            "source snapshot omitted source text",
        )

        write_manifest(
            root,
            {
                "schema": 1,
                "name": "Demo",
                "sources": ["src/missing.apx"],
            },
        )
        require_error(
            lambda: load_project(root),
            "APX-TOOL-006",
        )

        write_manifest(
            root,
            {
                "schema": 1,
                "name": "Demo",
                "sources": ["src/Main.apx"],
                "unexpected": True,
            },
        )
        require_error(
            lambda: load_project_manifest(manifest_path),
            "APX-TOOL-003",
        )

    print("AFP-P10-T1.1 project packaging foundation smoke test passed.")
    print("Dependency-free JSON manifest: PASS")
    print("Canonical source ordering: PASS")
    print("Cross-platform path normalization: PASS")
    print("Extension-neutral source declaration: PASS")
    print("Ancestor project discovery: PASS")
    print("UTF-8 source snapshot: PASS")
    print("Read-only ProjectBuilder mapping: PASS")
    print("Traversal and duplicate rejection: PASS")
    print("Missing-source diagnostics: PASS")
    print("Unknown-field diagnostics: PASS")


if __name__ == "__main__":
    main()