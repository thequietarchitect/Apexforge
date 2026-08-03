"""Executable current-behavior record for the P11.4C resolver audit.

P11.4C is audit-only.  This test proves that the published P11.4A/P11.4B
identity metadata remains passive while every existing lookup boundary keeps
its flat, unqualified behavior.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from io import StringIO
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from air.serialization import air_to_dict
import language.identities as identities_module
from language.identities import ProjectDeclaredIdentity, ProjectIdentityIndex
from language.project import (
    ProjectEntryPointError,
    ProjectLinkError,
    build_project,
)
from language_server.definition import definition
from language_server.diagnostics import offset_to_lsp_position
from language_server.integration import (
    CANONICAL_INTEGRATION_SHA256,
    integration_fingerprint,
    verify_frozen_feature_hashes,
)
from language_server.references import references
from language_server.rename import prepare_rename
from p11_3c_export_visibility_architecture_audit_smoke_test import (
    test_direct_transitive_and_legacy_visibility as accepted_visibility,
    test_parser_inventory_and_absent_export_features as accepted_absent_exports,
)
from p11_4b_declared_identity_metadata_smoke_test import execution_context
from tooling.build_artifact import construct_build_artifact
from tooling.cli import main as cli_main
from tooling.project_loader import load_project
from tooling.project_manifest import PROJECT_MANIFEST_SCHEMA
from tooling.visualstudio_intelligence import (
    CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256,
    audit_visualstudio_intelligence,
    visual_studio_intelligence_fingerprint,
)
from type_system.closure import collect_linked_specializations
from type_system.lowering import lower_linked_generics


PACKAGE_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_DIRECTORY.parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as error:
        return error
    raise AssertionError(message)


def diagnostic_of(error):
    diagnostics = tuple(getattr(error, "diagnostics", ()) or ())
    require(len(diagnostics) == 1, "expected one deterministic diagnostic")
    return diagnostics[0]


def repository_status() -> str:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v2", "--untracked-files=all"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    require(completed.stderr == "", "git status wrote unexpected stderr")
    return completed.stdout


def repository_bytecode_state() -> tuple[tuple[str, int, int], ...]:
    values: list[tuple[str, int, int]] = []
    for path in REPOSITORY_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in {".pyc", ".pyo"}:
            continue
        stat = path.stat()
        values.append(
            (
                path.relative_to(REPOSITORY_ROOT).as_posix(),
                stat.st_size,
                stat.st_mtime_ns,
            )
        )
    return tuple(sorted(values))


def recursive_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from recursive_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from recursive_keys(item)


def invoke_cli(arguments: tuple[str, ...]):
    stdout = StringIO()
    stderr = StringIO()
    code = cli_main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def test_passive_metadata_flat_ids_and_cross_kind_names() -> None:
    require(
        identities_module.__all__
        == ("ProjectDeclaredIdentity", "ProjectIdentityIndex")
        and tuple(item.name for item in fields(ProjectDeclaredIdentity))
        == (
            "kind",
            "declared_name",
            "current_air_id",
            "source_name",
            "module_name",
            "qualified_display_name",
            "span",
        )
        and tuple(item.name for item in fields(ProjectIdentityIndex))
        == ("identities",)
        and ProjectDeclaredIdentity.__dataclass_params__.frozen
        and ProjectIdentityIndex.__dataclass_params__.frozen,
        "the published P11.4B metadata model changed",
    )
    require(
        {
            "canonical_id",
            "qualified_lookup_name",
            "candidate",
            "binding",
            "visibility",
            "import_path",
            "generic_owner",
            "parent_identity",
        }.isdisjoint(item.name for item in fields(ProjectDeclaredIdentity)),
        "declared identity metadata acquired resolving fields",
    )

    project = build_project(
        {
            "root.apex": (
                "module App.Root\nimport Lib.Worker\n\n"
                "directive Root { cause flow { path primary @ 1 { invoke Worker } } }\n"
            ),
            "worker.apex": "module Lib.Worker\n\ndirective Worker {}\n",
        },
        entry="Root",
    )
    before_air = air_to_dict(project.program)
    root = project.identity_index.find_all("directive", "Root")
    require(
        len(root) == 1
        and root[0].declared_name == "Root"
        and root[0].current_air_id == "directive:Root"
        and root[0].module_name == "App.Root"
        and root[0].qualified_display_name == "App.Root.Root"
        and project.identity_index.find_qualified_display_name("App.Root.Root")
        == root,
        "declared identity metadata or display projection changed",
    )
    require_raises(
        FrozenInstanceError,
        lambda: setattr(root[0], "current_air_id", "directive:App.Root.Root"),
        "P11.4B metadata became mutable",
    )
    require_raises(
        ProjectEntryPointError,
        lambda: project.resolve_entry(root[0].qualified_display_name),
        "qualified_display_name became an entry lookup authority",
    )
    require(
        project.resolve_entry("Root") == project.resolve_entry("directive:Root")
        == "directive:Root"
        and tuple(item.id for item in project.program.directives)
        == ("directive:Worker", "directive:Root")
        and air_to_dict(project.program) == before_air,
        "flat AIR IDs, short/canonical entry lookup, or passive inspection changed",
    )

    cross_kind = build_project(
        {
            "directive.apex": "directive Same {}\n",
            "function.apex": "function Same() : int { return 1 }\n",
        },
        entry="Same",
    )
    require(
        tuple(item.id for item in cross_kind.program.directives)
        == ("directive:Same",)
        and tuple(item.id for item in cross_kind.program.functions)
        == ("function:Same",)
        and len(cross_kind.identity_index.find_all("directive", "Same")) == 1
        and len(cross_kind.identity_index.find_all("function", "Same")) == 1,
        "same-name cross-kind declarations stopped coexisting by AIR kind",
    )


def test_collisions_imports_exports_and_entries_are_unchanged() -> None:
    duplicate = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a.apex": "function Same() : int { return 1 }\n",
                "b.apex": "function Same() : int { return 2 }\n",
            }
        ),
        "same-kind duplicate declarations acquired candidate selection",
    )
    item = diagnostic_of(duplicate)
    require(
        item.stage == "link"
        and item.code == "APX-LINK-001"
        and item.air_id == "function:Same"
        and item.span.source_name == "a.apex"
        and tuple(span.source_name for span in item.related_spans) == ("b.apex",),
        "legacy duplicate failure phase, code, identity, or evidence changed",
    )

    cross_module = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a.apex": "module App.A\n\nfunction Same() : int { return 1 }\n",
                "b.apex": "module App.B\n\nfunction Same() : int { return 2 }\n",
            }
        ),
        "same-kind cross-module declarations stopped colliding globally",
    )
    item = diagnostic_of(cross_module)
    require(
        item.stage == "link"
        and item.code == "APX-LINK-001"
        and item.air_id == "function:Same"
        and item.span.source_name == "a.apex"
        and tuple(span.source_name for span in item.related_spans) == ("b.apex",),
        "cross-module collision behavior or deterministic evidence changed",
    )

    accepted_visibility()
    accepted_absent_exports()

    entries = build_project(
        {
            "alpha.apex": "module App.Alpha\n\ndirective Alpha {}\n",
            "beta.apex": "module App.Beta\n\ndirective Beta {}\n",
        }
    )
    require(
        entries.resolve_entry("Alpha") == "directive:Alpha"
        and entries.resolve_entry("directive:Beta") == "directive:Beta",
        "entry selection stopped using its existing unqualified forms",
    )
    for spelling in ("App.Alpha.Alpha", "App.Alpha::Alpha", "App.Alpha:Alpha"):
        require_raises(
            ProjectEntryPointError,
            lambda spelling=spelling: entries.resolve_entry(spelling),
            f"qualified entry spelling {spelling!r} was introduced",
        )


def test_generic_owner_lowering_and_runtime_lookup_are_unchanged() -> None:
    generic = build_project(
        {
            "generic.apex": (
                "module Lib.Generic\n\n"
                "function Identity<T : numeric>(value : T) : T { return value }\n"
            ),
            "use.apex": (
                "module App.Use\nimport Lib.Generic\n\n"
                "function Use(value : int) : int { return Identity<int>(Identity(value)) }\n"
            ),
        }
    )
    before_air = air_to_dict(generic.program)
    declaration = next(item for item in generic.program.functions if item.name == "Identity")
    closure = collect_linked_specializations(generic.program)
    lowered = lower_linked_generics(generic.program)
    binding = lowered.binding_for("Identity<int>")
    require(
        declaration.id == "function:Identity"
        and declaration.type_parameters[0].owner == "function:Identity"
        and closure.canonical_ids == lowered.canonical_ids == ("Identity<int>",)
        and binding is not None
        and binding.function_id.startswith("function:__apx_spec__Identity__int__")
        and generic.identity_index.find_all("function", "Identity")[0].current_air_id
        == "function:Identity"
        and generic.identity_index.find_current_air_id("Identity<int>") == ()
        and not any(
            "__apx_spec__" in identity.current_air_id
            for identity in generic.identity_index.identities
        )
        and air_to_dict(generic.program) == before_air,
        "generic owner, specialization, closure, lowering, or metadata exclusion changed",
    )

    runtime = build_project(
        {
            "root.apex": (
                "module App.Root\nimport App.Worker\n\n"
                "directive Root { cause run { path primary @ 1 { invoke Worker } } }\n"
            ),
            "worker.apex": (
                "module App.Worker\n\n"
                "directive Worker { state count = 1 cause work { path primary @ 1 { add count 2 } } }\n"
            ),
        },
        entry="Root",
    )
    before_runtime_air = air_to_dict(runtime.program)
    result = runtime.execute(
        execution_context(runtime, "Root", "Worker"),
        entry="Root",
    )
    require(
        result.ok
        and result.final_state.get_int("count") == 3
        and runtime.resolve_entry() == "directive:Root"
        and air_to_dict(runtime.program) == before_runtime_air,
        "runtime directive lookup, authority resource IDs, or execution changed",
    )


def test_artifact_cli_tooling_and_no_resolver_consumers() -> None:
    original_directory = Path.cwd().resolve()
    temporary_path: Path

    with TemporaryDirectory(prefix="apexforge-p11-4c-") as temporary:
        temporary_path = Path(temporary).resolve()
        try:
            temporary_path.relative_to(REPOSITORY_ROOT.resolve())
        except ValueError:
            pass
        else:
            raise AssertionError("temporary fixture was created inside the repository")

        source_root = temporary_path / "src"
        source_root.mkdir()
        (source_root / "main.apex").write_text(
            "module App.Main\n\ndirective Main {}\n",
            encoding="utf-8",
        )
        (temporary_path / "apexforge.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "name": "P11_4C_Resolver_Audit",
                    "sources": ["src/main.apex"],
                    "entry": "Main",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        output_path = temporary_path / "artifact.json"

        loaded = load_project(temporary_path)
        project = build_project(loaded.source_mapping(), entry=loaded.manifest.entry)
        before = construct_build_artifact(loaded, project)
        project.identity_index.find_qualified_display_name("App.Main.Main")
        after = construct_build_artifact(loaded, project)
        artifact = json.loads(after.content.decode("utf-8"))
        require(
            before.content == after.content
            and before.fingerprint == after.fingerprint
            and PROJECT_MANIFEST_SCHEMA == 1
            and set(artifact) == {"schema", "project", "air", "fingerprint"}
            and artifact["schema"] == "apexforge.build-artifact/v1"
            and {
                "identity_index",
                "candidate_index",
                "resolver",
                "declared_name",
                "current_air_id",
                "qualified_display_name",
                "qualified_lookup_name",
            }.isdisjoint(recursive_keys(artifact)),
            "artifact v1 or its fingerprint acquired resolver metadata",
        )

        check = invoke_cli(("check", str(temporary_path)))
        run = invoke_cli(("run", str(temporary_path)))
        build_cli = invoke_cli(
            ("build", str(temporary_path), "--output", str(output_path))
        )
        require(
            check
            == (
                0,
                "ApexForge check passed: P11_4C_Resolver_Audit (1 source(s)).\n",
                "",
            )
            and run
            == (
                0,
                "ApexForge run succeeded: P11_4C_Resolver_Audit\n"
                "Entry: directive:Main\n"
                "Runtime diagnostics: 0\n",
                "",
            )
            and build_cli[0] == 0
            and build_cli[2] == ""
            and build_cli[1].startswith(
                "ApexForge build succeeded: P11_4C_Resolver_Audit\n"
                "Schema: apexforge.build-artifact/v1\n"
                "Entry: directive:Main\n"
                "Sources: 1\nFingerprint: sha256:"
            )
            and build_cli[1].endswith("\nArtifact written.\n")
            and output_path.read_bytes() == before.content,
            "CLI entry, output, or artifact behavior changed",
        )

        uri = (source_root / "use.apex").resolve().as_uri()
        lsp_source = (
            "module App.Use\nimport Lib.Tool\n\n"
            "function Use() : int { return Tool() }\n"
        )
        call_offset = lsp_source.rindex("Tool")
        position = offset_to_lsp_position(lsp_source, call_offset)
        function_offset = lsp_source.index("Use()")
        require(
            definition(uri, lsp_source, position) is None
            and references(
                uri,
                lsp_source,
                position,
                {"includeDeclaration": True},
            )
            == ()
            and prepare_rename(
                uri,
                lsp_source,
                offset_to_lsp_position(lsp_source, function_offset),
            )
            is None,
            "LSP acquired cross-file/import resolution or callable rename behavior",
        )

        require(
            not tuple(temporary_path.glob(".*.tmp"))
            and Path.cwd().resolve() == original_directory,
            "temporary output residue or working-directory mutation detected",
        )

    require(
        not temporary_path.exists()
        and Path.cwd().resolve() == original_directory,
        "temporary fixture escaped its context manager",
    )

    require(
        verify_frozen_feature_hashes()
        and integration_fingerprint() == CANONICAL_INTEGRATION_SHA256
        == "c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897",
        "language-server definition/reference/rename or other frozen behavior changed",
    )
    extension_root = REPOSITORY_ROOT / "editors" / "visualstudio-apexforge"
    visual_studio = audit_visualstudio_intelligence(extension_root)
    require(
        visual_studio_intelligence_fingerprint()
        == CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256
        == "65f6ab0565276a59b1a71814acb0023da161a38661605b788e5f8b1e2753f82a"
        and visual_studio.intelligence_sha256
        == CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256
        and visual_studio.method_count == 9,
        "Visual Studio language intelligence behavior changed",
    )

    production_consumers = set()
    for path in PACKAGE_DIRECTORY.rglob("*.py"):
        if path.name.endswith("_smoke_test.py") or "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if any(
            marker in text
            for marker in (
                "identity_index",
                "ProjectIdentityIndex",
                "qualified_display_name",
            )
        ):
            production_consumers.add(
                path.relative_to(REPOSITORY_ROOT).as_posix()
            )
    require(
        production_consumers
        == {
            "apexforge/language/identities.py",
            "apexforge/language/project.py",
        },
        "a production path began consuming P11.4B identity metadata",
    )

    relevant_roots = (
        PACKAGE_DIRECTORY / "air",
        PACKAGE_DIRECTORY / "language",
        PACKAGE_DIRECTORY / "language_server",
        PACKAGE_DIRECTORY / "runtime",
        PACKAGE_DIRECTORY / "tooling",
        PACKAGE_DIRECTORY / "type_system",
    )
    forbidden = (
        "ProjectResolver",
        "ResolutionCandidate",
        "ResolvedBinding",
        "AmbiguitySet",
        "QualifiedLookupIdentity",
        "language.resolver",
        "language.resolution",
    )
    authorized_markers = {
        "apexforge/language/resolution_candidates.py": {
            "ResolutionCandidate",
        },
        "apexforge/language/project.py": {
            "ResolutionCandidate",
            "language.resolution",
        },
        "apexforge/language/resolution_queries.py": {
            "ResolutionCandidate",
            "ResolvedBinding",
            "language.resolution",
        },
        "apexforge/language/resolution_context.py": {
            "ResolutionCandidate",
            "ResolvedBinding",
            "language.resolution",
        },
    }
    observed_authorized_markers = set()
    for root in relevant_roots:
        for path in root.rglob("*.py"):
            relative = path.relative_to(REPOSITORY_ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            for marker in forbidden:
                if marker not in text:
                    continue
                require(
                    marker in authorized_markers.get(relative, set()),
                    f"production file {path.name} consumes a new resolver abstraction",
                )
                observed_authorized_markers.add((relative, marker))
    require(
        observed_authorized_markers
        == {
            (
                "apexforge/language/resolution_candidates.py",
                "ResolutionCandidate",
            ),
            ("apexforge/language/project.py", "ResolutionCandidate"),
            ("apexforge/language/project.py", "language.resolution"),
            (
                "apexforge/language/resolution_queries.py",
                "ResolutionCandidate",
            ),
            (
                "apexforge/language/resolution_queries.py",
                "ResolvedBinding",
            ),
            (
                "apexforge/language/resolution_queries.py",
                "language.resolution",
            ),
            (
                "apexforge/language/resolution_context.py",
                "ResolutionCandidate",
            ),
            (
                "apexforge/language/resolution_context.py",
                "ResolvedBinding",
            ),
            (
                "apexforge/language/resolution_context.py",
                "language.resolution",
            ),
        },
        "the reviewed P11.4D/P11.4E/P11.4F production boundary changed",
    )


def main() -> None:
    original_directory = Path.cwd().resolve()
    status_before = repository_status()
    bytecode_before = repository_bytecode_state()

    def forbidden_network(*_args, **_kwargs):
        raise AssertionError("P11.4C audit attempted network access")

    with patch("socket.create_connection", side_effect=forbidden_network), patch(
        "socket.socket", side_effect=forbidden_network
    ):
        test_passive_metadata_flat_ids_and_cross_kind_names()
        test_collisions_imports_exports_and_entries_are_unchanged()
        test_generic_owner_lowering_and_runtime_lookup_are_unchanged()
        test_artifact_cli_tooling_and_no_resolver_consumers()

    require(Path.cwd().resolve() == original_directory, "working directory changed")
    require(repository_status() == status_before, "running the audit changed repository status")
    require(
        repository_bytecode_state() == bytecode_before,
        "running the audit created, removed, or changed repository bytecode",
    )

    print("AFP-P11.4C resolver and qualification architecture audit smoke test passed.")
    print("Passive P11.4B metadata, display-only qualification, and flat AIR IDs: PASS")
    print("Collisions, imports/exports, visibility, and unqualified entries: PASS")
    print("Generic-owner lifecycle, lowering, and runtime lookup: PASS")
    print("Artifact v1, CLI, LSP, and Visual Studio compatibility: PASS")
    print("No resolver consumers, network, repository mutation, or bytecode mutation: PASS")


if __name__ == "__main__":
    main()
