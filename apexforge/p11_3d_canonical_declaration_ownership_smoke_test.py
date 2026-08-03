"""Focused production coverage for the P11.3D declaration ownership index."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from io import StringIO
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

import language.declarations as declarations_module
from language.declarations import (
    ProjectDeclarationOwner,
    ProjectDeclarationOwnership,
)
from language.modules import (
    ModuleGraph,
    ProjectDocument,
    ProjectDocumentGraph,
    ResolvedImportEdge,
)
from language.project import (
    ProjectBuild,
    ProjectEntryPointError,
    ProjectLinkError,
    ProjectModuleError,
    build_project,
)
from language.source import SourceText
from language_server.definition import definition
from language_server.diagnostics import analyze_document
from language_server.references import references
from language_server.rename import prepare_rename, rename
from p11_3c_export_visibility_architecture_audit_smoke_test import (
    test_module_diagnostic_contract_and_preempted_branch,
)
from tooling.build_artifact import construct_build_artifact
from tooling.cli import main as cli_main
from tooling.project_loader import load_project
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
        [
            "git",
            "status",
            "--porcelain=v2",
            "--untracked-files=all",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    require(completed.stderr == "", "git status wrote unexpected stderr")
    return completed.stdout


def invoke_cli(arguments: tuple[str, ...]):
    stdout = StringIO()
    stderr = StringIO()
    code = cli_main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def recursive_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from recursive_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from recursive_keys(item)


def test_public_model_shape_validation_order_and_queries() -> None:
    require(
        declarations_module.__all__
        == ("ProjectDeclarationOwner", "ProjectDeclarationOwnership"),
        "language.declarations exports an unintended public name",
    )
    require(
        tuple(item.name for item in fields(ProjectDeclarationOwner))
        == ("kind", "air_id", "source_name", "module_name", "span")
        and tuple(item.name for item in fields(ProjectDeclarationOwnership))
        == ("declarations",),
        "declaration ownership dataclass fields changed",
    )
    require(
        ProjectDeclarationOwner.__dataclass_params__.frozen
        and ProjectDeclarationOwnership.__dataclass_params__.frozen,
        "declaration ownership records are not frozen",
    )
    forbidden = {
        "export",
        "exported",
        "visibility",
        "public",
        "private",
        "alias",
        "namespace",
        "qualified_identity",
        "reference_edge",
        "artifact",
    }
    require(
        forbidden.isdisjoint(item.name for item in fields(ProjectDeclarationOwner))
        and forbidden.isdisjoint(
            item.name for item in fields(ProjectDeclarationOwnership)
        ),
        "ownership model acquired export, visibility, or reference metadata",
    )

    a_text = SourceText("A.apex", "directive Alpha {}\n")
    lower_text = SourceText("a.apex", "directive Alpha {}\n")
    z_text = SourceText("z.apex", "function Zed() { return 1 }\n")
    first = ProjectDeclarationOwner(
        "directive",
        "directive:Alpha",
        "A.apex",
        "App.A",
        a_text.span(0, 18),
    )
    second = ProjectDeclarationOwner(
        "directive",
        "directive:Alpha",
        "a.apex",
        None,
        lower_text.span(0, 18),
    )
    function = ProjectDeclarationOwner(
        "function",
        "function:Zed",
        "z.apex",
        "Lib.Zed",
        z_text.span(0, 27),
    )
    duplicate_module_tie = ProjectDeclarationOwner(
        "directive",
        "directive:Alpha",
        "A.apex",
        None,
        a_text.span(0, 18),
    )
    ownership = ProjectDeclarationOwnership(
        (function, second, first, duplicate_module_tie)
    )
    require(
        ownership.declarations
        == (duplicate_module_tie, first, second, function),
        "canonical owner ordering or optional-module tie-breaker changed",
    )
    require(
        ownership.find_all("directive:Alpha")
        == (duplicate_module_tie, first, second)
        and ownership.for_source("A.apex") == (duplicate_module_tie, first)
        and ownership.for_module("App.A") == (first,)
        and ownership.find_all("directive:Missing") == ()
        and ownership.for_source("missing.apex") == ()
        and ownership.for_module("Missing.Module") == (),
        "owner queries lost canonical order, duplicates, or empty results",
    )
    require(
        ownership.for_source("a.apex") == (second,)
        and ownership.for_source("A.APEX") == ()
        and ownership.for_module("app.a") == ()
        and ownership.find_all("Directive:Alpha") == (),
        "owner query matching stopped being exact-case",
    )

    for query in (
        ownership.for_source,
        ownership.for_module,
        ownership.find_all,
    ):
        require_raises(TypeError, lambda query=query: query(None), "non-string query accepted")
        require_raises(ValueError, lambda query=query: query(" \t"), "blank query accepted")

    require_raises(
        FrozenInstanceError,
        lambda: setattr(first, "air_id", "directive:Changed"),
        "owner record is mutable",
    )
    require_raises(
        FrozenInstanceError,
        lambda: setattr(ownership, "declarations", ()),
        "owner collection is mutable",
    )
    require_raises(
        TypeError,
        lambda: ProjectDeclarationOwnership((object(),)),
        "non-owner collection member accepted",
    )

    valid_span = SourceText("valid.apex", "directive Valid {}\n").span(0, 18)
    invalid_constructors = (
        lambda: ProjectDeclarationOwner("workflow", "workflow:W", "valid.apex", None, valid_span),
        lambda: ProjectDeclarationOwner("directive", "function:Valid", "valid.apex", None, valid_span),
        lambda: ProjectDeclarationOwner("function", "directive:Valid", "valid.apex", None, valid_span),
        lambda: ProjectDeclarationOwner("directive", "", "valid.apex", None, valid_span),
        lambda: ProjectDeclarationOwner("directive", "directive:", "valid.apex", None, valid_span),
        lambda: ProjectDeclarationOwner("directive", "directive:App.Valid", "valid.apex", None, valid_span),
        lambda: ProjectDeclarationOwner("directive", "directive:Valid", " ", None, valid_span),
        lambda: ProjectDeclarationOwner("directive", "directive:Valid", "valid.apex", " ", valid_span),
        lambda: ProjectDeclarationOwner("directive", "directive:Valid", "valid.apex", None, object()),
        lambda: ProjectDeclarationOwner(
            "directive",
            "directive:Valid",
            "other.apex",
            None,
            valid_span,
        ),
    )
    for constructor in invalid_constructors:
        require_raises(
            (TypeError, ValueError),
            constructor,
            "invalid declaration owner was accepted",
        )


def test_legacy_projection_and_project_build_compatibility() -> None:
    sources = {
        "30-nested.apex": (
            "directive Mid {\n"
            "    state count = 1\n"
            "    event done\n"
            "    cause flow { path primary @ 1 { emit done } }\n"
            "}\n"
        ),
        "20-function.apex": "function Echo(value : int) : int { return value }\n",
        "10-many.apex": "directive Zebra {}\ndirective Alpha {}\n",
    }
    build = build_project(sources, entry="Alpha")
    owners = build.declaration_ownership.declarations
    require(
        tuple((item.kind, item.air_id, item.source_name, item.module_name) for item in owners)
        == (
            ("directive", "directive:Alpha", "10-many.apex", None),
            ("directive", "directive:Mid", "30-nested.apex", None),
            ("directive", "directive:Zebra", "10-many.apex", None),
            ("function", "function:Echo", "20-function.apex", None),
        ),
        "legacy ownership projection or canonical ordering changed",
    )
    expected_entries = {
        (entry.kind, entry.air_id, entry.span.source_name, entry.span)
        for entry in build.source_map.entries
        if entry.kind in {"directive", "function"}
    }
    require(
        {
            (owner.kind, owner.air_id, owner.source_name, owner.span)
            for owner in owners
        }
        == expected_entries
        and len(owners)
        == len(build.program.directives) + len(build.program.functions),
        "legacy owner count, AIR IDs, physical sources, or top-level spans changed",
    )
    require(
        not {
            "state:count",
            "event:done",
            "cause:flow",
            "path:primary",
        }.intersection(owner.air_id for owner in owners),
        "nested directive members became declaration owners",
    )
    require(
        build.declaration_ownership.for_source("10-many.apex")
        == (owners[0], owners[2])
        and build.declaration_ownership.for_module("legacy") == ()
        and build.declaration_ownership.find_all("function:Echo") == (owners[3],),
        "legacy query projection changed",
    )

    project_fields = fields(ProjectBuild)
    require(
        tuple(item.name for item in project_fields[-2:])
        == ("document_graph", "declaration_ownership")
        and project_fields[-1].compare is False,
        "ProjectBuild ownership field was not appended with compare=False",
    )
    positional = ProjectBuild(
        build.source_units,
        build.program,
        build.verified,
        build.source_map,
        build.module_graph,
        build.entry_directive,
    )
    positional_with_document_graph = ProjectBuild(
        build.source_units,
        build.program,
        build.verified,
        build.source_map,
        build.module_graph,
        build.entry_directive,
        build.document_graph,
    )
    require(
        positional == build
        and positional.document_graph == ProjectDocumentGraph()
        and positional.declaration_ownership == ProjectDeclarationOwnership(),
        "manual positional ProjectBuild compatibility changed",
    )
    require(
        positional_with_document_graph == build
        and positional_with_document_graph.document_graph == build.document_graph
        and positional_with_document_graph.declaration_ownership
        == ProjectDeclarationOwnership(),
        "P11.3B positional ProjectBuild compatibility changed",
    )


def test_module_projection_visibility_and_graph_boundaries() -> None:
    sources = {
        "30-root.apex": (
            "module App.Root\n"
            "import App.Middle\n\n"
            "directive Root {}\n"
        ),
        "20-middle.apex": (
            "module App.Middle\n"
            "import Lib.Leaf\n\n"
            "function Middle(value : int) : int { return value }\n"
        ),
        "10-leaf.apex": "module Lib.Leaf\n\ndirective Leaf {}\n",
    }
    first = build_project(sources, entry="Root")
    second = build_project(dict(reversed(tuple(sources.items()))), entry="Root")
    require(
        first.declaration_ownership == second.declaration_ownership,
        "mapping insertion order changed canonical declaration ownership",
    )
    require(
        tuple(
            (owner.kind, owner.air_id, owner.source_name, owner.module_name)
            for owner in first.declaration_ownership.declarations
        )
        == (
            ("directive", "directive:Leaf", "10-leaf.apex", "Lib.Leaf"),
            ("directive", "directive:Root", "30-root.apex", "App.Root"),
            ("function", "function:Middle", "20-middle.apex", "App.Middle"),
        ),
        "module owner source/module spelling or canonical order changed",
    )
    require(
        all(
            owner.span
            == first.source_map.find(kind=owner.kind, air_id=owner.air_id)[0].span
            for owner in first.declaration_ownership.declarations
        )
        and first.declaration_ownership.for_module("Lib.Leaf")[0].source_name
        == "10-leaf.apex"
        and tuple(
            document.source_name
            for document in first.document_graph.transitive_document_dependencies(
                "30-root.apex"
            )
        )
        == ("10-leaf.apex", "20-middle.apex"),
        "module owner spans, queries, or dependency projection changed",
    )

    transitive = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "root.apex": (
                    "module app.root\nimport app.middle\n\n"
                    "directive Root { cause flow { path p @ 1 { invoke Leaf } } }\n"
                ),
                "middle.apex": (
                    "module app.middle\nimport app.leaf\n\ndirective Middle {}\n"
                ),
                "leaf.apex": "module app.leaf\n\ndirective Leaf {}\n",
            }
        ),
        "ownership/dependency metadata granted transitive visibility",
    )
    require(
        diagnostic_of(transitive).code == "APX-MODULE-008",
        "transitive visibility diagnostic changed",
    )

    direct = build_project(
        {
            "root.apex": (
                "module app.root\nimport app.worker\nimport app.helper\n\n"
                "directive Root {\n"
                "state count : int = Helper(1)\n"
                "cause flow { path p @ 1 { invoke Worker } }\n"
                "}\n"
            ),
            "worker.apex": "module app.worker\n\ndirective Worker {}\n",
            "helper.apex": (
                "module app.helper\n\n"
                "function Helper(value : int) : int { return value }\n"
            ),
        },
        entry="Root",
    )
    legacy = build_project(
        {
            "root.apex": (
                "directive Root { state count : int = Helper(1) "
                "cause flow { path p @ 1 { invoke Worker } } }\n"
            ),
            "worker.apex": "directive Worker {}\n",
            "helper.apex": "function Helper(value : int) : int { return value }\n",
        },
        entry="Root",
    )
    require(
        direct.resolve_entry() == legacy.resolve_entry() == "directive:Root"
        and legacy.module_graph.is_legacy,
        "direct-import or legacy global visibility changed",
    )

    require(
        tuple(item.name for item in fields(ModuleGraph)) == ("modules", "order")
        and tuple(item.name for item in fields(ProjectDocument))
        == ("source_name", "module_name", "module_span", "imports")
        and tuple(item.name for item in fields(ResolvedImportEdge))
        == (
            "importer_source_name",
            "imported_module_name",
            "target_source_name",
            "import_span",
        )
        and tuple(item.name for item in fields(ProjectDocumentGraph))
        == (
            "documents",
            "resolved_import_edges",
            "canonical_order",
            "dependency_order",
        ),
        "ModuleGraph or ProjectDocumentGraph acquired declaration metadata",
    )


def test_duplicates_generics_entries_and_diagnostics() -> None:
    a_span = SourceText("a.apex", "function Same() { return 1 }\n").span(0, 28)
    b_span = SourceText("b.apex", "function Same() { return 2 }\n").span(0, 28)
    duplicate_owners = ProjectDeclarationOwnership(
        (
            ProjectDeclarationOwner(
                "function", "function:Same", "b.apex", "lib.b", b_span
            ),
            ProjectDeclarationOwner(
                "function", "function:Same", "a.apex", "lib.a", a_span
            ),
        )
    )
    require(
        tuple(owner.source_name for owner in duplicate_owners.find_all("function:Same"))
        == ("a.apex", "b.apex"),
        "duplicate owners were overwritten or returned out of canonical order",
    )

    duplicate_error = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a.apex": (
                    "module lib.a\n\nfunction Same(value : int) : int { return value }\n"
                ),
                "b.apex": (
                    "module lib.b\n\nfunction Same(value : int) : int { return value }\n"
                ),
            }
        ),
        "duplicate project declaration bypassed the linker",
    )
    item = diagnostic_of(duplicate_error)
    require(
        item.severity == "error"
        and item.stage == "link"
        and item.code == "APX-LINK-001"
        and item.air_id == "function:Same"
        and item.span is not None
        and item.span.source_name == "a.apex"
        and tuple(span.source_name for span in item.related_spans) == ("b.apex",),
        "ownership metadata replaced or altered APX-LINK-001",
    )

    generic = build_project(
        {
            "identity.apex": (
                "module Lib.Generic\n\n"
                "function Identity<T : numeric>(value : T) : T { return value }\n"
            ),
            "user.apex": (
                "module App.User\nimport Lib.Generic\n\n"
                "function Use(value : int) : int { return Identity(value) }\n"
            ),
        }
    )
    identity = generic.program.functions[0]
    closure = collect_linked_specializations(generic.program)
    lowered = lower_linked_generics(generic.program)
    require(
        generic.declaration_ownership.find_all("function:Identity")
        == generic.declaration_ownership.for_module("Lib.Generic")
        and len(generic.declaration_ownership.find_all("function:Identity")) == 1
        and not any("<" in owner.air_id for owner in generic.declaration_ownership.declarations)
        and identity.type_parameters[0].owner == "function:Identity"
        and closure.canonical_ids == lowered.canonical_ids == ("Identity<int>",)
        and lowered.lowered_target("Identity<int>") is not None,
        "generic ownership, inference, closure, specialization, or lowering changed",
    )

    entries = build_project(
        {
            "a.apex": "module app.a\n\ndirective Alpha {}\n",
            "b.apex": "module app.b\n\ndirective Beta {}\n",
        }
    )
    require(
        entries.resolve_entry("Alpha") == "directive:Alpha"
        and entries.resolve_entry("directive:Beta") == "directive:Beta",
        "short or canonical directive entries changed",
    )
    require_raises(
        ProjectEntryPointError,
        lambda: entries.resolve_entry("app.a.Alpha"),
        "module-qualified entry syntax was introduced",
    )

    # Reuse the accepted P11.3C exact APX-MODULE-001..009 and preemption record.
    test_module_diagnostic_contract_and_preempted_branch()


def test_cli_artifact_language_server_and_isolation() -> None:
    original_directory = Path.cwd().resolve()
    temporary_path: Path

    with TemporaryDirectory(prefix="apexforge-p11-3d-") as temporary:
        temporary_path = Path(temporary).resolve()
        try:
            temporary_path.relative_to(REPOSITORY_ROOT.resolve())
        except ValueError:
            pass
        else:
            raise AssertionError("temporary fixture was created inside the repository")

        source_root = temporary_path / "src"
        source_root.mkdir()
        (source_root / "10-main.apex").write_text(
            "module App.Main\nimport App.Worker\n\ndirective Main {}\n",
            encoding="utf-8",
        )
        (source_root / "20-worker.apex").write_text(
            "module App.Worker\n\ndirective Worker {}\n",
            encoding="utf-8",
        )
        (temporary_path / "apexforge.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "name": "P11_3D_Declaration_Ownership",
                    "sources": ["src/20-worker.apex", "src/10-main.apex"],
                    "entry": "Main",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        output_path = temporary_path / "artifact.json"

        def forbidden_network(*_args, **_kwargs):
            raise AssertionError("P11.3D smoke test attempted network access")

        with patch("socket.create_connection", side_effect=forbidden_network), patch(
            "socket.socket", side_effect=forbidden_network
        ):
            check = invoke_cli(("check", str(temporary_path)))
            run = invoke_cli(("run", str(temporary_path)))
            build_cli = invoke_cli(
                ("build", str(temporary_path), "--output", str(output_path))
            )

        require(
            check
            == (
                0,
                "ApexForge check passed: P11_3D_Declaration_Ownership (2 source(s)).\n",
                "",
            )
            and run
            == (
                0,
                "ApexForge run succeeded: P11_3D_Declaration_Ownership\n"
                "Entry: directive:Main\n"
                "Runtime diagnostics: 0\n",
                "",
            )
            and build_cli[0] == 0
            and build_cli[2] == ""
            and build_cli[1].startswith(
                "ApexForge build succeeded: P11_3D_Declaration_Ownership\n"
                "Schema: apexforge.build-artifact/v1\n"
                "Entry: directive:Main\n"
                "Sources: 2\nFingerprint: sha256:"
            )
            and build_cli[1].endswith("\nArtifact written.\n"),
            "CLI check, run, or build output changed",
        )

        loaded = load_project(temporary_path)
        project = build_project(
            loaded.source_mapping(),
            entry=loaded.manifest.entry,
        )
        before = construct_build_artifact(loaded, project)
        project.declaration_ownership.for_source("src/10-main.apex")
        project.declaration_ownership.for_module("App.Worker")
        project.declaration_ownership.find_all("directive:Main")
        after = construct_build_artifact(loaded, project)
        require(
            output_path.read_bytes() == before.content == after.content
            and before.fingerprint == after.fingerprint,
            "ownership access changed artifact v1 bytes or fingerprint",
        )
        artifact = json.loads(after.content.decode("utf-8"))
        forbidden_keys = {
            "declaration_ownership",
            "declarations",
            "exports",
            "export",
            "visibility",
            "qualified_identity",
            "module_graph",
            "document_graph",
        }
        require(
            set(artifact) == {"schema", "project", "air", "fingerprint"}
            and artifact["schema"] == "apexforge.build-artifact/v1"
            and forbidden_keys.isdisjoint(recursive_keys(artifact)),
            "artifact v1 acquired declaration, export, visibility, or graph metadata",
        )

        uri = "file:///workspace/main.apex"
        source = (
            "module App.Main\n"
            "import App.Missing\n\n"
            "directive Main {}\n"
        )
        import_offset = source.index("App.Missing")
        import_position = {
            "line": source[:import_offset].count("\n"),
            "character": len(source[:import_offset].rsplit("\n", 1)[-1]),
        }
        require(
            analyze_document(uri, source) == ()
            and definition(uri, source, import_position) is None
            and references(
                uri,
                source,
                import_position,
                {"includeDeclaration": True},
            )
            == ()
            and prepare_rename(uri, source, import_position) is None
            and rename(uri, source, import_position, "Other") is None,
            "language server consumed ownership metadata or gained cross-file resolution",
        )
        export_source = "module App.Main\nexport Main\n\ndirective Main {}\n"
        export_diagnostics = analyze_document(uri, export_source)
        require(
            len(export_diagnostics) == 1
            and export_diagnostics[0]["code"] == "APX-PARSE-002",
            "language server acquired export awareness",
        )

        language_server_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((PACKAGE_DIRECTORY / "language_server").glob("*.py"))
        )
        visual_studio_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((PACKAGE_DIRECTORY / "tooling").glob("visualstudio*.py"))
        )
        require(
            "declaration_ownership" not in language_server_text
            and "declaration_ownership" not in visual_studio_text,
            "language-server or Visual Studio tooling consumes the ownership index",
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


def main() -> None:
    status_before = repository_status()

    test_public_model_shape_validation_order_and_queries()
    test_legacy_projection_and_project_build_compatibility()
    test_module_projection_visibility_and_graph_boundaries()
    test_duplicates_generics_entries_and_diagnostics()
    test_cli_artifact_language_server_and_isolation()

    require(
        repository_status() == status_before,
        "running the P11.3D smoke test changed repository status",
    )

    print("AFP-P11.3D canonical declaration ownership smoke test passed.")
    print("Public immutable model, validation, ordering, and queries: PASS")
    print("Legacy and module declaration ownership projection: PASS")
    print("Duplicate retention, linker authority, and generics: PASS")
    print("ProjectBuild, graph, visibility, entry, and diagnostics boundaries: PASS")
    print("CLI, artifact v1, language server, and isolation: PASS")
    print("Repository status preservation: PASS")


if __name__ == "__main__":
    main()
