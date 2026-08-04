"""Focused production coverage for the P11.3B project document graph."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from language.modules import (
    ProjectDocument,
    ProjectDocumentGraph,
    ResolvedImportEdge,
)
from language.project import (
    ProjectBuild,
    ProjectEntryPointError,
    ProjectModuleError,
    build_project,
)
from language_server.diagnostics import analyze_document
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


def span_text(span, sources: dict[str, str]) -> str:
    if span is None:
        return ""
    source = sources[span.source_name]
    return source[span.start.offset:span.end.offset]


def invoke_cli(arguments: tuple[str, ...]):
    stdout = StringIO()
    stderr = StringIO()
    code = cli_main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def test_legacy_projection_and_project_build_compatibility() -> None:
    sources = {
        "20-function.apex": (
            "function Identity(value : int) : int { return value }\n"
        ),
        "10-directives.apex": (
            "directive First {}\n"
            "directive Second {}\n"
        ),
    }
    build = build_project(sources)
    graph = build.document_graph

    require(isinstance(graph, ProjectDocumentGraph), "document graph is not public")
    require(graph.is_legacy, "legacy document graph was marked as module mode")
    require(build.module_graph.is_legacy, "legacy ModuleGraph behavior changed")
    require(
        graph.canonical_source_order()
        == ("10-directives.apex", "20-function.apex")
        == graph.dependency_first_source_order(),
        "legacy canonical and dependency source orders diverged",
    )
    require(
        tuple(document.source_name for document in graph.documents)
        == graph.canonical_source_order(),
        "legacy graph did not represent every physical source once",
    )
    require(
        all(
            document.module_name is None
            and document.module_span is None
            and document.imports == ()
            for document in graph.documents
        ),
        "legacy graph invented module metadata",
    )
    require(graph.resolved_import_edges == (), "legacy graph invented import edges")
    require(
        tuple(item.id for item in build.program.directives)
        == ("directive:First", "directive:Second"),
        "P11.2B headerless multi-directive support changed",
    )

    positional = ProjectBuild(
        build.source_units,
        build.program,
        build.verified,
        build.source_map,
        build.module_graph,
        build.entry_directive,
    )
    require(
        positional == build and positional.document_graph == ProjectDocumentGraph(),
        "existing positional construction or equality compatibility changed",
    )


def module_sources() -> dict[str, str]:
    return {
        "40-root.apex": (
            "module App.Root\n"
            "import App.Middle\n"
            "import Lib.Shared\n"
            "import Lib.Leaf\n\n"
            "directive Root {}\n"
        ),
        "30-middle.apex": (
            "module App.Middle\n"
            "import Lib.Leaf\n\n"
            "directive Middle {}\n"
        ),
        "20-shared.apex": "module Lib.Shared\n\ndirective Shared {}\n",
        "10-leaf.apex": "module Lib.Leaf\n\ndirective Leaf {}\n",
    }


def test_module_projection_edges_queries_and_immutability() -> None:
    sources = module_sources()
    first = build_project(sources, entry="Root")
    second = build_project(
        dict(reversed(tuple(sources.items()))),
        entry="Root",
    )
    graph = first.document_graph

    require(graph == second.document_graph, "mapping order changed the document graph")
    require(
        graph.canonical_source_order()
        == tuple(unit.name for unit in first.source_units)
        == (
            "10-leaf.apex",
            "20-shared.apex",
            "30-middle.apex",
            "40-root.apex",
        ),
        "canonical physical source order changed",
    )
    require(
        first.module_graph.order
        == ("Lib.Leaf", "App.Middle", "Lib.Shared", "App.Root")
        and first.module_graph.source_order()
        == (
            "10-leaf.apex",
            "30-middle.apex",
            "20-shared.apex",
            "40-root.apex",
        )
        == graph.dependency_first_source_order(),
        "document dependency order stopped projecting ModuleGraph source order",
    )
    require(
        tuple(item.name for item in first.module_graph.modules)
        == ("App.Middle", "App.Root", "Lib.Leaf", "Lib.Shared")
        and first.module_graph.direct_imports("App.Root")
        == ("App.Middle", "Lib.Shared", "Lib.Leaf"),
        "existing ModuleGraph values changed",
    )

    root = graph.find("40-root.apex")
    require(isinstance(root, ProjectDocument), "document lookup failed")
    require(
        root.module_name == "App.Root"
        and root.module_span is not None
        and span_text(root.module_span, sources) == "App.Root"
        and tuple(item.name for item in root.imports)
        == ("App.Middle", "Lib.Shared", "Lib.Leaf")
        and tuple(span_text(item.span, sources) for item in root.imports)
        == ("App.Middle", "Lib.Shared", "Lib.Leaf"),
        "module/import spelling, order, or spans changed",
    )

    edge_projection = tuple(
        (
            edge.importer_source_name,
            edge.imported_module_name,
            edge.target_source_name,
            span_text(edge.import_span, sources),
        )
        for edge in graph.resolved_import_edges
    )
    require(
        edge_projection
        == (
            ("30-middle.apex", "Lib.Leaf", "10-leaf.apex", "Lib.Leaf"),
            ("40-root.apex", "App.Middle", "30-middle.apex", "App.Middle"),
            ("40-root.apex", "Lib.Shared", "20-shared.apex", "Lib.Shared"),
            ("40-root.apex", "Lib.Leaf", "10-leaf.apex", "Lib.Leaf"),
        ),
        "resolved edge ownership, target, spelling, span, or order changed",
    )
    require(
        tuple(
            item.source_name
            for item in graph.direct_document_dependencies("40-root.apex")
        )
        == ("30-middle.apex", "20-shared.apex", "10-leaf.apex"),
        "direct dependencies stopped preserving import declaration order",
    )
    require(
        tuple(
            item.source_name
            for item in graph.transitive_document_dependencies("40-root.apex")
        )
        == ("10-leaf.apex", "30-middle.apex", "20-shared.apex"),
        "transitive dependencies are not unique dependency-first documents",
    )
    require(
        graph.find("missing.apex") is None
        and graph.direct_document_dependencies("missing.apex") == ()
        and graph.transitive_document_dependencies("missing.apex") == ()
        and graph.find(" 40-root.apex ") is root
        and graph.find("40-ROOT.apex") is None,
        "unknown, trimmed, or exact-case lookup behavior changed",
    )
    require_raises(TypeError, lambda: graph.find(1), "non-string lookup was accepted")
    require_raises(ValueError, lambda: graph.find(" "), "blank lookup was accepted")
    require_raises(
        FrozenInstanceError,
        lambda: setattr(root, "module_name", "Changed"),
        "document records are mutable",
    )
    require_raises(
        FrozenInstanceError,
        lambda: setattr(graph.resolved_import_edges[0], "target_source_name", "x"),
        "resolved import edges are mutable",
    )


def test_module_diagnostics_and_one_declaration_boundary() -> None:
    scenarios = (
        (
            "APX-MODULE-001",
            {"bad.apex": "module app.main extra\ndirective Main {}\n"},
            "well-formed",
            "bad.apex",
            1,
            "module app.main extra",
            (),
        ),
        (
            "APX-MODULE-002",
            {"bad.apex": "module app.one\nmodule app.two\ndirective Main {}\n"},
            "only one module",
            "bad.apex",
            2,
            "app.two",
            ("app.one",),
        ),
        (
            "APX-MODULE-003",
            {"bad.apex": "import app.one\nmodule app.main\ndirective Main {}\n"},
            "preceding module",
            "bad.apex",
            1,
            "app.one",
            (),
        ),
        (
            "APX-MODULE-004",
            {
                "bad.apex": (
                    "module app.main\nimport app.one\nimport app.one\ndirective Main {}\n"
                )
            },
            "Duplicate import",
            "bad.apex",
            3,
            "app.one",
            ("app.one",),
        ),
        (
            "APX-MODULE-005",
            {
                "legacy.apex": "directive Legacy {}\n",
                "module.apex": "module app.main\n\ndirective Main {}\n",
            },
            "Every source unit",
            "legacy.apex",
            1,
            "",
            (),
        ),
        (
            "APX-MODULE-006",
            {
                "bad.apex": (
                    "module app.main\nimport app.missing\n\ndirective Main {}\n"
                )
            },
            "undefined module",
            "bad.apex",
            2,
            "app.missing",
            (),
        ),
        (
            "APX-MODULE-007",
            {
                "a.apex": "module cycle.a\nimport cycle.b\n\ndirective A {}\n",
                "b.apex": "module cycle.b\nimport cycle.a\n\ndirective B {}\n",
            },
            "cycle detected",
            "a.apex",
            2,
            "cycle.b",
            ("cycle.a",),
        ),
        (
            "APX-MODULE-008",
            {
                "a-root.apex": (
                    "module app.root\n\n"
                    "directive Root { cause flow { path p @ 1 { invoke Leaf } } }\n"
                ),
                "b-leaf.apex": "module app.leaf\n\ndirective Leaf {}\n",
            },
            "without directly importing",
            "a-root.apex",
            3,
            "invoke Leaf",
            (),
        ),
        (
            "APX-MODULE-009",
            {
                "a.apex": "module App.Shared\n\ndirective A {}\n",
                "b.apex": "module app.shared\n\ndirective B {}\n",
            },
            "Duplicate module declaration",
            "b.apex",
            1,
            "app.shared",
            ("App.Shared",),
        ),
    )

    for code, sources, category, source_name, line, primary, related in scenarios:
        error = require_raises(
            ProjectModuleError,
            lambda sources=sources: build_project(sources),
            f"{code} scenario was accepted",
        )
        item = diagnostic_of(error)
        require(
            item.stage == "module"
            and item.code == code
            and category in item.message
            and item.span is not None
            and item.span.source_name == source_name
            and item.span.start.line == line
            and span_text(item.span, sources) == primary
            and tuple(span_text(span, sources) for span in item.related_spans)
            == related
            and (
                item.air_id.startswith("invoke:")
                if code == "APX-MODULE-008"
                else item.air_id == ""
            ),
            f"{code} observable diagnostic behavior changed",
        )

    still_002 = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "bad.apex": (
                    "module app.first\n"
                    "import app.dependency\n"
                    "module app.second\n"
                    "directive Main {}\n"
                )
            }
        ),
        "the unreachable module-after-import branch changed",
    )
    require(
        diagnostic_of(still_002).code == "APX-MODULE-002",
        "the unreachable APX-MODULE-003 branch became observable",
    )

    # P11.2E intentionally routes masked module sources through the canonical
    # heterogeneous compiler instead of retaining P11.2B's legacy-only gate.
    module_multi = build_project(
        {
            "multi.apex": (
                "module app.multi\n\n"
                "directive First {}\n"
                "directive Second {}\n"
            )
        },
        entry="First",
    )
    require(
        tuple(item.id for item in module_multi.program.directives)
        == ("directive:First", "directive:Second")
        and module_multi.entry_directive == "directive:First",
        "P11.2E module-source promotion lost declarations or entry selection",
    )


def test_visibility_generics_entries_and_scope_boundaries() -> None:
    transitive_sources = {
        "root.apex": (
            "module app.root\nimport app.middle\n\n"
            "directive Root { cause flow { path p @ 1 { invoke Leaf } } }\n"
        ),
        "middle.apex": "module app.middle\nimport app.leaf\n\ndirective Middle {}\n",
        "leaf.apex": "module app.leaf\n\ndirective Leaf {}\n",
    }
    transitive = require_raises(
        ProjectModuleError,
        lambda: build_project(transitive_sources),
        "transitive document dependency granted directive visibility",
    )
    require(
        diagnostic_of(transitive).code == "APX-MODULE-008",
        "direct-import-only visibility changed",
    )

    identity = (
        "module library.identity\n\n"
        "function Identity<T : numeric>(value : T) : T { return value }\n"
    )
    user = (
        "module application.user\nimport library.identity\n\n"
        "function Use(value : int) : int { return Identity<int>(value) }\n"
    )
    generic = build_project({"user.apex": user, "identity.apex": identity})
    require(
        generic.document_graph.dependency_first_source_order()
        == generic.module_graph.source_order()
        and collect_linked_specializations(generic.program).canonical_ids
        == ("Identity<int>",)
        and lower_linked_generics(generic.program).canonical_ids
        == ("Identity<int>",),
        "document graph access changed generic closure or lowering",
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
        "entry selection changed",
    )
    require_raises(
        ProjectEntryPointError,
        entries.resolve_entry,
        "multi-directive entry fallback changed",
    )
    require_raises(
        ProjectEntryPointError,
        lambda: entries.resolve_entry("app.a.Alpha"),
        "module-qualified entry syntax was introduced",
    )

    graph_fields = {
        item.name for item in fields(ProjectDocumentGraph)
    }
    document_fields = {
        item.name for item in fields(ProjectDocument)
    }
    edge_fields = {
        item.name for item in fields(ResolvedImportEdge)
    }
    require(
        graph_fields
        == {"documents", "resolved_import_edges", "canonical_order", "dependency_order"}
        and document_fields
        == {"source_name", "module_name", "module_span", "imports"}
        and edge_fields
        == {
            "importer_source_name",
            "imported_module_name",
            "target_source_name",
            "import_span",
        },
        "document graph acquired an out-of-scope overlay model",
    )
    forbidden = (
        "export",
        "visibility",
        "namespace",
        "alias",
        "qualified",
        "air",
        "artifact",
        "lsp",
    )
    all_fields = graph_fields | document_fields | edge_fields
    require(
        not any(term in name for term in forbidden for name in all_fields),
        "document graph contains a forbidden P11.3C-or-later field",
    )


def test_cli_artifact_lsp_and_temporary_isolation() -> None:
    original_directory = Path.cwd().resolve()
    temporary_path: Path

    with TemporaryDirectory(prefix="apexforge-p11-3b-") as temporary:
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
            "module app.main\nimport app.worker\n\ndirective Main {}\n",
            encoding="utf-8",
        )
        (source_root / "20-worker.apex").write_text(
            "module app.worker\n\ndirective Worker {}\n",
            encoding="utf-8",
        )
        (temporary_path / "apexforge.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "name": "P11_3B_Document_Graph",
                    "sources": ["src/20-worker.apex", "src/10-main.apex"],
                    "entry": "Main",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        first_output = temporary_path / "first.json"
        second_output = temporary_path / "second.json"

        def forbidden_network(*_args, **_kwargs):
            raise AssertionError("P11.3B smoke test attempted network access")

        with patch("socket.create_connection", side_effect=forbidden_network), patch(
            "socket.socket", side_effect=forbidden_network
        ):
            check = invoke_cli(("check", str(temporary_path)))
            run = invoke_cli(("run", str(temporary_path)))
            first_cli = invoke_cli(
                ("build", str(temporary_path), "--output", str(first_output))
            )
            second_cli = invoke_cli(
                ("build", str(temporary_path), "--output", str(second_output))
            )

        require(
            check
            == (
                0,
                "ApexForge check passed: P11_3B_Document_Graph (2 source(s)).\n",
                "",
            ),
            "CLI check output changed",
        )
        require(
            run
            == (
                0,
                "ApexForge run succeeded: P11_3B_Document_Graph\n"
                "Entry: directive:Main\n"
                "Runtime diagnostics: 0\n",
                "",
            ),
            "CLI run output changed",
        )
        require(
            first_cli == second_cli
            and first_cli[0] == 0
            and first_cli[2] == ""
            and first_output.read_bytes() == second_output.read_bytes(),
            "CLI build output or artifact bytes changed nondeterministically",
        )

        loaded = load_project(temporary_path)
        build = build_project(
            loaded.source_mapping(),
            entry=loaded.manifest.entry,
        )
        before = construct_build_artifact(loaded, build)
        require(
            build.document_graph.canonical_source_order()
            == ("src/10-main.apex", "src/20-worker.apex")
            and build.document_graph.dependency_first_source_order()
            == ("src/20-worker.apex", "src/10-main.apex"),
            "loaded document graph source orders changed",
        )
        build.document_graph.transitive_document_dependencies("src/10-main.apex")
        after = construct_build_artifact(loaded, build)
        require(
            before.content == after.content
            and before.fingerprint == after.fingerprint,
            "document graph access changed artifact v1 bytes or fingerprint",
        )
        artifact = json.loads(after.content.decode("utf-8"))
        require(
            set(artifact) == {"schema", "project", "air", "fingerprint"}
            and "document_graph" not in artifact
            and "modules" not in artifact
            and "exports" not in artifact,
            "artifact v1 acquired project document-graph metadata",
        )

        missing_import_source = (
            "module app.local\nimport app.missing\n\ndirective Local {}\n"
        )
        require(
            analyze_document(
                "file:///workspace/local.apex",
                missing_import_source,
            )
            == (),
            "language server acquired cross-file module resolution",
        )
        require(
            not tuple(temporary_path.glob(".*.tmp"))
            and Path.cwd().resolve() == original_directory,
            "temporary artifact residue or working-directory mutation detected",
        )

    require(
        not temporary_path.exists()
        and Path.cwd().resolve() == original_directory,
        "temporary fixture escaped its context manager",
    )


def main() -> None:
    test_legacy_projection_and_project_build_compatibility()
    test_module_projection_edges_queries_and_immutability()
    test_module_diagnostics_and_one_declaration_boundary()
    test_visibility_generics_entries_and_scope_boundaries()
    test_cli_artifact_lsp_and_temporary_isolation()

    print("AFP-P11.3B project document-graph smoke test passed.")
    print("Legacy and module document coverage: PASS")
    print("Module/import spelling, spans, and resolved edges: PASS")
    print("Canonical, dependency, direct, and transitive ordering: PASS")
    print("ModuleGraph, diagnostics, and P11.2B compatibility: PASS")
    print("Visibility, generics, entries, and scope boundaries: PASS")
    print("CLI, artifact v1, language server, and isolation: PASS")


if __name__ == "__main__":
    main()
