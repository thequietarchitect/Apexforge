"""P11.3A audit coverage for the frozen module/import architecture.

This test records behavior that exists before P11.3B. It intentionally adds no
export, visibility, namespace, qualified-identity, or document-graph behavior.
"""

from __future__ import annotations

import hashlib
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from air.serialization import air_to_dict
from language.modules import ModuleError, parse_module_source
from language.project import (
    ProjectCompilationError,
    ProjectEntryPointError,
    ProjectLinkError,
    ProjectModuleError,
    build_project,
)
from language_server.definition import definition
from language_server.diagnostics import analyze_document
from language_server.formatting import format_document
from language_server.hover import hover
from language_server.references import references
from language_server.rename import prepare_rename, rename
from language_server.symbols import document_symbols
from language_server.workspace_symbols import workspace_symbols
from tooling.build_artifact import canonical_json_bytes
from tooling.cli import main as cli_main
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


def lsp_position(text: str, needle: str, *, occurrence: int = 1):
    start = -1
    for _ in range(occurrence):
        start = text.index(needle, start + 1)
    prefix = text[:start]
    return {
        "line": prefix.count("\n"),
        "character": len(prefix.rsplit("\n", 1)[-1]),
    }


def invoke_cli(arguments: tuple[str, ...]):
    stdout = StringIO()
    stderr = StringIO()
    code = cli_main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def test_module_parsing_normalization_order_and_spans() -> None:
    source = (
        "  module App.Main;\r\n"
        "\r\n"
        "import App.Zeta\r\n"
        "import App.Alpha;\r\n"
        "\r\n"
        "directive Main {}\r\n"
    )
    parsed = parse_module_source(" headers.apex ", source)

    require(parsed.source_name == "headers.apex", "source-name trimming changed")
    require(parsed.module_name == "App.Main", "module spelling or case changed")
    require(
        tuple(item.name for item in parsed.imports)
        == ("App.Zeta", "App.Alpha"),
        "source-order imports were normalized or reordered",
    )
    require(
        parsed.module_span is not None
        and parsed.module_span.start.line == 1
        and parsed.module_span.start.column == 10
        and parsed.module_span.end.column == 18,
        "module-name source span changed",
    )
    require(
        tuple(
            (
                item.span.start.line,
                item.span.start.column,
                item.span.end.column,
            )
            for item in parsed.imports
        )
        == ((3, 8, 16), (4, 8, 17)),
        "import-name source spans changed",
    )
    require(
        len(parsed.masked_source) == len(source)
        and parsed.masked_source.count("\r\n") == source.count("\r\n")
        and "module" not in parsed.masked_source
        and "import" not in parsed.masked_source,
        "header masking stopped preserving offsets and line endings",
    )

    duplicate = require_raises(
        ModuleError,
        lambda: parse_module_source(
            "duplicate-import.apex",
            "module app.main\nimport app.shared\nimport app.shared\n\ndirective Main {}\n",
        ),
        "an exact duplicate import was accepted",
    )
    item = diagnostic_of(duplicate)
    require(
        item.stage == "module"
        and item.code == "APX-MODULE-004"
        and item.span is not None
        and item.span.start.line == 3
        and item.span.start.column == 8
        and len(item.related_spans) == 1
        and item.related_spans[0].start.line == 2,
        "duplicate-import diagnostic or related span changed",
    )


def test_graph_order_direct_transitive_and_failures() -> None:
    sources = {
        "40-main.apex": (
            "module app.main\n"
            "import app.util\n"
            "import app.feature\n\n"
            "directive Main {}\n"
        ),
        "30-feature.apex": (
            "module app.feature\nimport app.core\n\ndirective Feature {}\n"
        ),
        "20-util.apex": (
            "module app.util\nimport app.core\n\ndirective Util {}\n"
        ),
        "10-core.apex": "module app.core\n\ndirective Core {}\n",
    }
    first = build_project(sources, entry="Main")
    second = build_project(dict(reversed(tuple(sources.items()))), entry="Main")

    require(
        first.module_graph.order
        == ("app.core", "app.feature", "app.util", "app.main"),
        "dependency-first topological order changed",
    )
    require(
        first.module_graph.source_order()
        == (
            "10-core.apex",
            "30-feature.apex",
            "20-util.apex",
            "40-main.apex",
        ),
        "module-to-source graph order changed",
    )
    require(
        tuple(item.name for item in first.module_graph.modules)
        == ("app.core", "app.feature", "app.main", "app.util"),
        "canonical module-record order changed",
    )
    require(
        first.module_graph.direct_imports("app.main")
        == ("app.util", "app.feature"),
        "direct imports stopped preserving header order",
    )
    require(
        tuple(item.id for item in first.program.directives)
        == (
            "directive:Core",
            "directive:Feature",
            "directive:Util",
            "directive:Main",
        )
        and air_to_dict(first.program) == air_to_dict(second.program),
        "module ordering or mapping insertion determinism changed linked AIR",
    )

    missing = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "missing.apex": (
                    "module app.missing_user\n"
                    "import app.absent\n\n"
                    "directive MissingUser {}\n"
                )
            }
        ),
        "a missing imported module was accepted",
    )
    item = diagnostic_of(missing)
    require(
        item.stage == "module"
        and item.code == "APX-MODULE-006"
        and item.span is not None
        and item.span.source_name == "missing.apex"
        and item.span.start.line == 2
        and item.span.start.column == 8
        and item.related_spans == (),
        "missing-import diagnostic changed",
    )

    cycle = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "A.apex": "module cycle.a\nimport cycle.b\n\ndirective A {}\n",
                "B.apex": "module cycle.b\nimport cycle.c\n\ndirective B {}\n",
                "C.apex": "module cycle.c\nimport cycle.a\n\ndirective C {}\n",
            }
        ),
        "a module cycle was accepted",
    )
    item = diagnostic_of(cycle)
    require(
        item.stage == "module"
        and item.code == "APX-MODULE-007"
        and item.message
        == "Module import cycle detected: cycle.a -> cycle.b -> cycle.c -> cycle.a."
        and item.span is not None
        and item.span.source_name == "A.apex"
        and tuple(span.source_name for span in item.related_spans)
        == ("B.apex", "C.apex"),
        "cycle path, primary edge, or related edges changed",
    )

    self_import = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "self.apex": (
                    "module app.self\nimport app.self\n\ndirective Self {}\n"
                )
            }
        ),
        "a self-import was accepted",
    )
    require(
        diagnostic_of(self_import).code == "APX-MODULE-007"
        and "app.self -> app.self" in diagnostic_of(self_import).message,
        "self-import stopped using the cycle diagnostic",
    )

    duplicate = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "a-first.apex": "module App.Shared\n\ndirective First {}\n",
                "b-second.apex": "module app.shared\n\ndirective Second {}\n",
            }
        ),
        "case-folded duplicate module names were accepted",
    )
    item = diagnostic_of(duplicate)
    require(
        item.stage == "module"
        and item.code == "APX-MODULE-009"
        and item.span is not None
        and item.span.source_name == "b-second.apex"
        and len(item.related_spans) == 1
        and item.related_spans[0].source_name == "a-first.apex",
        "case-folded duplicate-module diagnostic changed",
    )

    mixed = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "module.apex": "module app.module\n\ndirective Module {}\n",
                "legacy.apex": "directive Legacy {}\n",
            }
        ),
        "mixed legacy/module mode was accepted",
    )
    item = diagnostic_of(mixed)
    require(
        item.stage == "module"
        and item.code == "APX-MODULE-005"
        and item.span is not None
        and item.span.source_name == "legacy.apex"
        and item.span.start.offset == item.span.end.offset == 0,
        "mixed-mode zero-width source diagnostic changed",
    )

    case_mismatch = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "a.apex": (
                    "module App.A\nimport app.b\n\ndirective A {}\n"
                ),
                "b.apex": "module App.B\n\ndirective B {}\n",
            }
        ),
        "case-mismatched import unexpectedly resolved",
    )
    require(
        diagnostic_of(case_mismatch).code == "APX-MODULE-006",
        "imports stopped resolving by exact case-preserved module spelling",
    )


def test_module_source_boundary_and_p11_2b_compatibility() -> None:
    headerless = build_project(
        {
            "legacy.apex": (
                "directive First {}\n"
                "directive Second {}\n"
            )
        }
    )
    require(
        headerless.module_graph.is_legacy
        and tuple(item.id for item in headerless.program.directives)
        == ("directive:First", "directive:Second"),
        "P11.2B headerless multi-directive compatibility changed",
    )

    module_multi = require_raises(
        ProjectCompilationError,
        lambda: build_project(
            {
                "module-multi.apex": (
                    "module app.multi\n\n"
                    "directive First {}\n"
                    "directive Second {}\n"
                )
            }
        ),
        "P11.2B multi-directive parsing entered module mode",
    )
    item = diagnostic_of(module_multi)
    require(
        item.stage == "parse"
        and item.code == "APX-PARSE-001"
        and item.span is not None
        and item.span.source_name == "module-multi.apex"
        and item.span.start.line == 4,
        "module-mode one-declaration boundary changed",
    )


def test_resolution_generics_visibility_and_entries() -> None:
    worker = "module library.worker\n\ndirective Worker {}\n"
    caller = (
        "module application.caller\n"
        "import library.worker\n\n"
        "directive Caller {\n"
        "    cause flow { path primary @ 1 { invoke Worker } }\n"
        "}\n"
    )
    direct = build_project(
        {"caller.apex": caller, "worker.apex": worker},
        entry="Caller",
    )
    require(
        direct.resolve_entry() == "directive:Caller"
        and direct.program.causal_decisions[0].paths[0].invocations[0].target
        == "Worker",
        "directly imported directive or short AIR target changed",
    )

    no_directive_import = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "caller.apex": caller.replace("import library.worker\n", ""),
                "worker.apex": worker,
            }
        ),
        "a known cross-module directive was visible without a direct import",
    )
    item = diagnostic_of(no_directive_import)
    require(
        item.stage == "module"
        and item.code == "APX-MODULE-008"
        and item.air_id.startswith("invoke:")
        and item.span is not None
        and item.span.source_name == "caller.apex",
        "directive visibility diagnostic changed",
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
        "a transitive-only directive became visible",
    )
    require(
        diagnostic_of(transitive).code == "APX-MODULE-008"
        and "without directly importing it" in diagnostic_of(transitive).message,
        "transitive imports stopped being ordering-only for visibility",
    )

    identity = (
        "module library.identity\n\n"
        "function Identity<T : numeric>(value : T) : T { return value }\n"
    )
    user = (
        "module application.user\n"
        "import library.identity\n\n"
        "function UseIdentity(value : int) : int {\n"
        "    return Identity<int>(value)\n"
        "}\n"
    )
    generic = build_project(
        {"user.apex": user, "identity.apex": identity}
    )
    require(
        tuple(item.id for item in generic.program.functions)
        == ("function:Identity", "function:UseIdentity")
        and generic.program.functions[1].return_expression.target == "Identity",
        "directly imported generic function resolution changed",
    )
    require(
        collect_linked_specializations(generic.program).canonical_ids
        == ("Identity<int>",)
        and lower_linked_generics(generic.program).canonical_ids
        == ("Identity<int>",),
        "module projects changed linked generic closure or lowering",
    )

    no_function_import = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "user.apex": user.replace("import library.identity\n", ""),
                "identity.apex": identity,
            }
        ),
        "a known cross-module function was visible without a direct import",
    )
    item = diagnostic_of(no_function_import)
    require(
        item.stage == "module"
        and item.code == "APX-MODULE-008"
        and item.air_id.startswith("function_call:")
        and item.span is not None
        and item.span.source_name == "user.apex",
        "function visibility diagnostic changed",
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
        "short or canonical entry selection changed in module mode",
    )
    require_raises(
        ProjectEntryPointError,
        entries.resolve_entry,
        "ambiguous global module-project entry fallback was accepted",
    )
    require_raises(
        ProjectEntryPointError,
        lambda: entries.resolve_entry("app.a.Alpha"),
        "a module-qualified entry reference was invented",
    )

    duplicate_global = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a.apex": "module app.a\n\nfunction Same(value) { return value }\n",
                "b.apex": "module app.b\n\nfunction Same(value) { return value }\n",
            }
        ),
        "duplicate global short function identities became ambiguous",
    )
    item = diagnostic_of(duplicate_global)
    require(
        item.stage == "link"
        and item.code == "APX-LINK-001"
        and item.air_id == "function:Same"
        and item.span is not None
        and len(item.related_spans) == 1,
        "duplicate global declaration diagnostic changed in module mode",
    )


def test_language_server_module_import_recognition() -> None:
    uri = "file:///workspace/main.apex"
    source = (
        "module app.main;\n"
        "import app.worker;\n\n"
        "directive Main {\n"
        "state count=1\n"
        "}\n"
    )
    require(analyze_document(uri, source) == (), "valid module headers gained LSP diagnostics")

    symbols = document_symbols(uri, source)
    require(
        len(symbols) == 1
        and symbols[0]["name"] == "app.main"
        and symbols[0]["detail"] == "module"
        and tuple(child["detail"] for child in symbols[0]["children"])
        == ("import", "directive"),
        "document symbols stopped projecting module/import hierarchy",
    )

    import_hover = hover(uri, source, lsp_position(source, "app.worker"))
    require(
        import_hover is not None
        and "import app.worker" in import_hover["contents"]["value"]
        and "Direct module import." in import_hover["contents"]["value"],
        "syntax-level import hover changed",
    )

    module_position = lsp_position(source, "app.main")
    import_position = lsp_position(source, "app.worker")
    module_definition = definition(uri, source, module_position)
    require(
        module_definition is not None
        and module_definition["uri"] == uri
        and definition(uri, source, import_position) is None,
        "same-document module definition or unresolved import behavior changed",
    )
    require(
        len(references(uri, source, module_position, {"includeDeclaration": True}))
        == 1
        and prepare_rename(uri, source, module_position) is None
        and rename(uri, source, module_position, "renamed") is None,
        "module references or protected rename boundary changed",
    )

    edits = format_document(
        uri,
        source,
        {"tabSize": 4, "insertSpaces": True},
    )
    require(
        len(edits) == 1
        and edits[0]["newText"].startswith(
            "module app.main\nimport app.worker\n\n"
        )
        and ";" not in edits[0]["newText"].split("\n\n", 1)[0],
        "module/import formatting normalization changed",
    )


def test_cli_artifact_workspace_symbols_and_isolation() -> None:
    original_directory = Path.cwd().resolve()
    temporary_path: Path

    with TemporaryDirectory(prefix="apexforge-p11-3a-") as temporary:
        temporary_path = Path(temporary).resolve()
        try:
            temporary_path.relative_to(REPOSITORY_ROOT.resolve())
        except ValueError:
            pass
        else:
            raise AssertionError("temporary fixture was created inside the repository")

        source_root = temporary_path / "src"
        source_root.mkdir()
        main_source = (
            "module app.main\n"
            "import app.worker\n\n"
            "directive Main { state main_count = 1 }\n"
        ).encode("utf-8")
        worker_source = (
            "module app.worker\n\n"
            "directive Worker { state worker_count = 2 }\n"
        ).encode("utf-8")
        (source_root / "10-main.apex").write_bytes(main_source)
        (source_root / "20-worker.apex").write_bytes(worker_source)
        (temporary_path / "apexforge.json").write_bytes(
            (
                json.dumps(
                    {
                        "schema": 1,
                        "name": "P11_3A_Module_Audit",
                        "sources": [
                            "src/20-worker.apex",
                            "src/10-main.apex",
                        ],
                        "entry": "Main",
                    },
                    indent=2,
                )
                + "\n"
            ).encode("utf-8")
        )

        first_output = temporary_path / "first.json"
        second_output = temporary_path / "second.json"

        def forbidden_network(*_args, **_kwargs):
            raise AssertionError("audit smoke test attempted network access")

        with patch("socket.create_connection", side_effect=forbidden_network), patch(
            "socket.socket", side_effect=forbidden_network
        ):
            check_code, check_out, check_err = invoke_cli(
                ("check", str(temporary_path))
            )
            run_code, run_out, run_err = invoke_cli(
                ("run", str(temporary_path))
            )
            first_code, first_out, first_err = invoke_cli(
                (
                    "build",
                    str(temporary_path),
                    "--output",
                    str(first_output),
                )
            )
            second_code, second_out, second_err = invoke_cli(
                (
                    "build",
                    str(temporary_path),
                    "--output",
                    str(second_output),
                )
            )
            indexed = workspace_symbols(temporary_path.as_uri(), "app")

        require(
            check_code == 0
            and check_out
            == "ApexForge check passed: P11_3A_Module_Audit (2 source(s)).\n"
            and check_err == "",
            "CLI check changed for a module project",
        )
        require(
            run_code == 0
            and "Entry: directive:Main\n" in run_out
            and run_err == "",
            "CLI run changed for a module project",
        )
        require(
            first_code == second_code == 0
            and first_out == second_out
            and first_err == second_err == ""
            and first_output.read_bytes() == second_output.read_bytes(),
            "CLI build or module-project artifact bytes were nondeterministic",
        )

        artifact = json.loads(first_output.read_text(encoding="utf-8"))
        require(
            set(artifact) == {"schema", "project", "air", "fingerprint"}
            and artifact["schema"] == "apexforge.build-artifact/v1"
            and artifact["project"]["entry"] == "directive:Main"
            and tuple(item["path"] for item in artifact["project"]["sources"])
            == ("src/10-main.apex", "src/20-worker.apex")
            and tuple(item["id"] for item in artifact["air"]["directives"])
            == ("directive:Worker", "directive:Main"),
            "artifact v1 source order or dependency-ordered AIR changed",
        )
        require(
            tuple(item["sha256"] for item in artifact["project"]["sources"])
            == (
                hashlib.sha256(main_source).hexdigest(),
                hashlib.sha256(worker_source).hexdigest(),
            ),
            "artifact source hashes stopped using exact loaded bytes",
        )
        payload = {
            "air": artifact["air"],
            "project": artifact["project"],
            "schema": artifact["schema"],
        }
        require(
            artifact["fingerprint"]
            == {
                "algorithm": "sha256",
                "value": hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
            }
            and "modules" not in artifact
            and "module_graph" not in artifact
            and "exports" not in artifact,
            "artifact fingerprint or v1 no-module-metadata boundary changed",
        )
        require(
            {item["name"] for item in indexed if item.get("kind") == 2}
            >= {"app.main", "app.worker"},
            "workspace symbols stopped indexing module declarations",
        )
        require(
            not tuple(temporary_path.glob(".*.tmp"))
            and Path.cwd().resolve() == original_directory,
            "temporary artifact residue or working-directory mutation detected",
        )

    require(
        not temporary_path.exists()
        and Path.cwd().resolve() == original_directory,
        "temporary fixture escaped its isolated lifetime",
    )


def main() -> None:
    test_module_parsing_normalization_order_and_spans()
    test_graph_order_direct_transitive_and_failures()
    test_module_source_boundary_and_p11_2b_compatibility()
    test_resolution_generics_visibility_and_entries()
    test_language_server_module_import_recognition()
    test_cli_artifact_workspace_symbols_and_isolation()

    print("AFP-P11.3A module architecture audit smoke test passed.")
    print("Module parsing, normalization, ordering, and spans: PASS")
    print("Graph order, imports, cycles, duplicates, and mixed mode: PASS")
    print("P11.2B legacy/module asymmetry: PASS")
    print("Directive, function, generic, and entry behavior: PASS")
    print("CLI check/run/build and deterministic artifact v1: PASS")
    print("Language-server module/import recognition: PASS")
    print("Repository, network, and temporary-fixture isolation: PASS")


if __name__ == "__main__":
    main()
