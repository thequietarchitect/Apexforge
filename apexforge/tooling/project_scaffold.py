"""AFP-P10-T1.3 deterministic ApexForge project scaffolding.

The scaffold uses ``.apex`` as the default template filename selected for the
CLI workflow. Source loading remains extension-neutral until AFP-P10-T2 freezes
the canonical source-extension and grammar contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Union

from tooling.project_loader import LoadedProject, load_project
from tooling.project_manifest import (
    PROJECT_MANIFEST_NAME,
    ProjectManifest,
    ProjectManifestError,
)


P10_T1_SCAFFOLD_VERSION = "10-T1.3"
DEFAULT_PROJECT_ENTRY = "Main"
DEFAULT_PROJECT_SOURCE = "src/main.apex"
DEFAULT_PROJECT_SOURCE_TEXT = """directive Main {
    event ready

    cause start {
        path primary @ 10 {
            message \"ready\"
            emit ready
        }
    }
}
"""


@dataclass(frozen=True)
class ScaffoldedProject:
    """Paths and loaded snapshot for one newly created ApexForge project."""

    root: Path
    manifest_path: Path
    source_path: Path
    loaded: LoadedProject

    def __post_init__(self) -> None:
        if not isinstance(self.root, Path):
            raise TypeError("ScaffoldedProject.root must be pathlib.Path.")
        if not isinstance(self.manifest_path, Path):
            raise TypeError(
                "ScaffoldedProject.manifest_path must be pathlib.Path."
            )
        if not isinstance(self.source_path, Path):
            raise TypeError("ScaffoldedProject.source_path must be pathlib.Path.")
        if not isinstance(self.loaded, LoadedProject):
            raise TypeError("ScaffoldedProject.loaded must be LoadedProject.")


def _scaffold_error(message: str, *, path: Path) -> ProjectManifestError:
    return ProjectManifestError(
        code="APX-TOOL-009",
        message=message,
        manifest_path=path,
    )


def _write_utf8_lf(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def create_project_scaffold(
    name: str,
    destination: Union[str, Path] = ".",
) -> ScaffoldedProject:
    """Create one non-overwriting project under ``destination/name``.

    The project is validated through the frozen T1.1 manifest and loader
    contracts before the completed scaffold is returned.
    """

    manifest = ProjectManifest(
        name=name,
        sources=(DEFAULT_PROJECT_SOURCE,),
        entry=DEFAULT_PROJECT_ENTRY,
    )

    parent = Path(destination).resolve()
    root = parent / manifest.name
    manifest_path = root / PROJECT_MANIFEST_NAME
    source_path = root.joinpath(*DEFAULT_PROJECT_SOURCE.split("/"))

    if root.exists():
        raise _scaffold_error(
            f"Project destination already exists: {root}.",
            path=manifest_path,
        )

    created_root = False
    try:
        parent.mkdir(parents=True, exist_ok=True)
        if not parent.is_dir():
            raise _scaffold_error(
                f"Project parent is not a directory: {parent}.",
                path=manifest_path,
            )

        root.mkdir()
        created_root = True
        source_path.parent.mkdir(parents=True)

        _write_utf8_lf(manifest_path, manifest.canonical_json())
        _write_utf8_lf(source_path, DEFAULT_PROJECT_SOURCE_TEXT)

        loaded = load_project(root)
    except ProjectManifestError:
        if created_root:
            shutil.rmtree(root, ignore_errors=True)
        raise
    except OSError as exc:
        if created_root:
            shutil.rmtree(root, ignore_errors=True)
        raise _scaffold_error(
            f"Unable to create ApexForge project: {exc}.",
            path=manifest_path,
        ) from exc
    except Exception:
        if created_root:
            shutil.rmtree(root, ignore_errors=True)
        raise

    return ScaffoldedProject(
        root=root,
        manifest_path=manifest_path,
        source_path=source_path,
        loaded=loaded,
    )


__all__ = (
    "DEFAULT_PROJECT_ENTRY",
    "DEFAULT_PROJECT_SOURCE",
    "DEFAULT_PROJECT_SOURCE_TEXT",
    "P10_T1_SCAFFOLD_VERSION",
    "ScaffoldedProject",
    "create_project_scaffold",
)