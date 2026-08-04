"""Read-only coverage for the P11.3C export and visibility audit.

This test records existing behavior only. It introduces no export syntax,
visibility rule, namespace, qualified identity, diagnostic, or production
model.
"""

from __future__ import annotations

from dataclasses import fields
from io import StringIO
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

import language.parser as parser_module
from language.grammar import GRAMMAR_KEYWORD_TOKENS, MODULE_HEADER_KEYWORDS, TOP_LEVEL_DECLARATIONS
from language.lexer import KEYWORDS
from language.modules import (
    ModuleGraph,
    ProjectDocument,
    ProjectDocumentGraph,
    ResolvedImportEdge,
)
from language.parser import (
    AuthorityNode,
    DirectiveNode,
    FunctionNode,
    PrincipalNode,
    RoleNode,
    WorkflowNode,
    parse,
)
from language.project import (
    ProjectBuild,
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


def test_parser_inventory_and_absent_export_features() -> None:
    require(
        TOP_LEVEL_DECLARATIONS
        == (
            "function",
            "directive",
            "workflow",
            "authority",
            "principal",
            "role",
        ),
        "top-level declaration inventory changed",
    )
    require(
        MODULE_HEADER_KEYWORDS == ("module", "import")
        and not {"export", "public", "private"}.intersection(KEYWORDS)
        and not {"export", "public", "private"}.intersection(
            GRAMMAR_KEYWORD_TOKENS
        ),
        "an export or visibility keyword was introduced",
    )
    require(
        not hasattr(parser_module, "IdentityNode")
        and not hasattr(parser_module, "ExportNode")
        and not hasattr(parser_module, "VisibilityNode"),
        "a separate identity, export, or visibility parser declaration appeared",
    )

    declarations = (
        ("function F(value) { return value }", FunctionNode),
        ("directive D {}", DirectiveNode),
        ("workflow W {}", WorkflowNode),
        ("authority A {}", AuthorityNode),
        ("principal P {}", PrincipalNode),
        ("role R {}", RoleNode),
    )
    for source, expected_type in declarations:
        require(
            isinstance(parse(source), expected_type),
            f"{expected_type.__name__} parser mapping changed",
        )

    generic = parse(
        "function Identity<T : numeric>(value : T) : T { return value }"
    )
    require(
        isinstance(generic, FunctionNode)
        and len(generic.type_parameters) == 1
        and generic.type_parameters[0].name == "T"
        and generic.type_parameters[0].apex_type.owner == "function:Identity",
        "generic declarations stopped being owned function declarations",
    )

    for modifier in ("export", "public", "private"):
        error = require_raises(
            ProjectCompilationError,
            lambda modifier=modifier: build_project(
                {
                    "main.apex": (
                        "module app.main\n"
                        f"{modifier} directive Main {{}}\n"
                    )
                }
            ),
            f"{modifier!r} was accepted as a declaration feature",
        )
        item = diagnostic_of(error)
        require(
            item.stage == "parse"
            and item.code == "APX-PARSE-002"
            and item.span is not None
            and item.span.source_name == "main.apex"
            and item.span.start.line == 2,
            f"{modifier!r} stopped being an ordinary unrecognized identifier",
        )

    export_list = require_raises(
        ProjectCompilationError,
        lambda: build_project(
            {
                "main.apex": (
                    "module app.main\n"
                    "export Main\n\n"
                    "directive Main {}\n"
                )
            }
        ),
        "an export list was accepted",
    )
    require(
        diagnostic_of(export_list).code == "APX-PARSE-002",
        "export-list-looking text became a recognized export feature",
    )


def test_lowering_ownership_flat_ids_and_unsupported_forms() -> None:
    sources = {
        "directive.apex": (
            "module app.directive\n\n"
            "directive Main {\n"
            "    state count = 1\n"
            "    event done\n"
            "    cause flow { path primary @ 1 { emit done } }\n"
            "}\n"
        ),
        "function.apex": (
            "module app.function\n\n"
            "function Identity(value : int) : int { return value }\n"
        ),
    }
    build = build_project(sources, entry="Main")
    require(
        tuple(item.id for item in build.program.directives) == ("directive:Main",)
        and tuple(item.id for item in build.program.functions)
        == ("function:Identity",)
        and tuple(item.id for item in build.program.states) == ("state:count",)
        and tuple(item.id for item in build.program.events) == ("event:done",)
        and tuple(item.id for item in build.program.causal_decisions)
        == ("cause:flow",)
        and build.program.causal_decisions[0].paths[0].id == "path:primary",
        "linked AIR identities stopped being globally short and unqualified",
    )
    require(
        tuple(
            (entry.kind, entry.air_id, entry.span.source_name)
            for entry in build.source_map.entries
            if entry.kind in {"directive", "function"}
        )
        == (
            ("directive", "directive:Main", "directive.apex"),
            ("function", "function:Identity", "function.apex"),
        ),
        "source-map declaration ownership evidence changed",
    )

    promoted = (
        (
            "workflow.apex",
            "module app.workflow\n\nworkflow Flow {}\n",
            "workflows",
            "id",
            "workflow:Flow",
        ),
        (
            "authority.apex",
            "module app.authority\n\nauthority Guard {}\n",
            "authorities",
            "id",
            "authority:Guard",
        ),
        (
            "principal.apex",
            "module app.principal\n\nprincipal Actor {}\n",
            "principals",
            "id",
            "principal:Actor",
        ),
        (
            "role.apex",
            "module app.role\n\nrole Operator {}\n",
            "roles",
            "name",
            "Operator",
        ),
    )
    for source_name, source, collection_name, identity_field, expected in promoted:
        promoted_build = build_project({source_name: source})
        declarations = getattr(
            promoted_build.program,
            collection_name,
        )

        require(
            len(declarations) == 1
            and getattr(declarations[0], identity_field) == expected,
            f"{source_name} canonical project AIR lowering changed",
        )
        require(
            not promoted_build.module_graph.is_legacy
            and promoted_build.module_graph.source_order()
            == (source_name,),
            f"{source_name} module ownership changed",
        )

    flat_duplicate = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a.apex": "module app.a\n\ndirective A { state shared = 1 }\n",
                "b.apex": "module app.b\n\ndirective B { state shared = 2 }\n",
            }
        ),
        "equal state names in different modules stopped colliding globally",
    )
    item = diagnostic_of(flat_duplicate)
    require(
        item.stage == "link"
        and item.code == "APX-LINK-001"
        and item.air_id == "state:shared",
        "flat state collision behavior changed",
    )


def test_direct_transitive_and_legacy_visibility() -> None:
    direct_sources = {
        "root.apex": (
            "module app.root\n"
            "import lib.worker\n"
            "import lib.helper\n\n"
            "directive Root {\n"
            "    state value : int = Helper(1)\n"
            "    cause flow { path primary @ 1 { invoke Worker } }\n"
            "}\n"
        ),
        "worker.apex": "module lib.worker\n\ndirective Worker {}\n",
        "helper.apex": (
            "module lib.helper\n\n"
            "function Helper(value : int) : int { return value }\n"
        ),
    }
    direct = build_project(direct_sources, entry="Root")
    require(
        direct.resolve_entry() == "directive:Root"
        and tuple(item.id for item in direct.program.directives)
        == ("directive:Worker", "directive:Root")
        and tuple(item.id for item in direct.program.functions)
        == ("function:Helper",),
        "direct imports stopped granting directive/function visibility",
    )

    for target_kind in ("directive", "function"):
        root_body = (
            "directive Root { cause flow { path p @ 1 { invoke Leaf } } }\n"
            if target_kind == "directive"
            else "function Root(value : int) : int { return Leaf(value) }\n"
        )
        leaf_body = (
            "directive Leaf {}\n"
            if target_kind == "directive"
            else "function Leaf(value : int) : int { return value }\n"
        )
        transitive_sources = {
            "root.apex": "module app.root\nimport app.middle\n\n" + root_body,
            "middle.apex": "module app.middle\nimport app.leaf\n\ndirective Middle {}\n",
            "leaf.apex": "module app.leaf\n\n" + leaf_body,
        }
        error = require_raises(
            ProjectModuleError,
            lambda transitive_sources=transitive_sources: build_project(
                transitive_sources
            ),
            f"transitive dependency granted {target_kind} visibility",
        )
        item = diagnostic_of(error)
        require(
            item.stage == "module"
            and item.code == "APX-MODULE-008"
            and item.span is not None
            and item.span.source_name == "root.apex"
            and item.air_id.startswith(
                "invoke:" if target_kind == "directive" else "function_call:"
            ),
            f"transitive {target_kind} visibility diagnostic changed",
        )

    transitive_graph = build_project(
        {
            "root.apex": "module app.root\nimport app.middle\n\ndirective Root {}\n",
            "middle.apex": "module app.middle\nimport app.leaf\n\ndirective Middle {}\n",
            "leaf.apex": "module app.leaf\n\ndirective Leaf {}\n",
        },
        entry="Root",
    )
    require(
        tuple(
            item.source_name
            for item in transitive_graph.document_graph.transitive_document_dependencies(
                "root.apex"
            )
        )
        == ("leaf.apex", "middle.apex"),
        "transitive document dependency query changed",
    )

    legacy = build_project(
        {
            "root.apex": (
                "directive Root {\n"
                "    state value : int = Helper(1)\n"
                "    cause flow { path primary @ 1 { invoke Worker } }\n"
                "}\n"
            ),
            "worker.apex": "directive Worker {}\n",
            "helper.apex": (
                "function Helper(value : int) : int { return value }\n"
            ),
        },
        entry="Root",
    )
    require(
        legacy.module_graph.is_legacy
        and legacy.document_graph.is_legacy
        and legacy.resolve_entry() == "directive:Root"
        and tuple(item.id for item in legacy.program.functions)
        == ("function:Helper",),
        "legacy/headerless project-wide visibility changed",
    )


def test_collisions_generics_and_entry_identity() -> None:
    duplicate = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "root.apex": (
                    "module app.root\nimport lib.a\nimport lib.b\n\n"
                    "directive Root {}\n"
                ),
                "a.apex": (
                    "module lib.a\n\n"
                    "function Same(value : int) : int { return value }\n"
                ),
                "b.apex": (
                    "module lib.b\n\n"
                    "function Same(value : int) : int { return value }\n"
                ),
            }
        ),
        "equal imported short names formed a supported ambiguity set",
    )
    item = diagnostic_of(duplicate)
    require(
        item.stage == "link"
        and item.code == "APX-LINK-001"
        and item.air_id == "function:Same"
        and item.span is not None
        and len(item.related_spans) == 1,
        "same-kind global duplicate behavior changed",
    )

    generic = build_project(
        {
            "generic.apex": (
                "module lib.generic\n\n"
                "function Identity<T : numeric>(value : T) : T { return value }\n"
            ),
            "user.apex": (
                "module app.user\nimport lib.generic\n\n"
                "function Use(value : int) : int { return Identity(value) }\n"
            ),
        }
    )
    declaration = generic.program.functions[0]
    closure = collect_linked_specializations(generic.program)
    lowered = lower_linked_generics(generic.program)
    require(
        declaration.id == "function:Identity"
        and len(declaration.type_parameters) == 1
        and declaration.type_parameters[0].owner == "function:Identity"
        and closure.canonical_ids == ("Identity<int>",)
        and lowered.canonical_ids == ("Identity<int>",)
        and lowered.lowered_target("Identity<int>") is not None,
        "generic declaration, inference, specialization, closure, or lowering changed",
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
        "short/canonical entry resolution changed",
    )
    require_raises(
        ProjectEntryPointError,
        entries.resolve_entry,
        "multiple directives stopped requiring an explicit entry",
    )
    for spelling in ("app.a.Alpha", "app.a::Alpha", "app.a:Alpha"):
        require_raises(
            ProjectEntryPointError,
            lambda spelling=spelling: entries.resolve_entry(spelling),
            f"module-qualified entry spelling {spelling!r} was introduced",
        )


def test_document_and_module_graph_boundaries() -> None:
    build = build_project(
        {
            "root.apex": "module app.root\nimport app.leaf\n\ndirective Root {}\n",
            "leaf.apex": "module app.leaf\n\ndirective Leaf {}\n",
        },
        entry="Root",
    )
    graph_fields = {item.name for item in fields(ProjectDocumentGraph)}
    document_fields = {item.name for item in fields(ProjectDocument)}
    edge_fields = {item.name for item in fields(ResolvedImportEdge)}
    module_fields = {item.name for item in fields(ModuleGraph)}
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
        }
        and module_fields == {"modules", "order"},
        "ProjectDocumentGraph or ModuleGraph public shape changed",
    )
    forbidden = (
        "declaration",
        "export",
        "visibility",
        "reference",
        "namespace",
        "qualified",
    )
    require(
        not any(
            term in name
            for term in forbidden
            for name in graph_fields | document_fields | edge_fields | module_fields
        ),
        "a physical/dependency graph acquired semantic visibility nodes",
    )
    require(
        build.module_graph.order == ("app.leaf", "app.root")
        and build.module_graph.direct_imports("app.root") == ("app.leaf",)
        and build.document_graph.canonical_source_order()
        == ("leaf.apex", "root.apex")
        and build.document_graph.dependency_first_source_order()
        == ("leaf.apex", "root.apex"),
        "module or document graph ordering changed",
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
        "manual ProjectBuild empty document-graph compatibility changed",
    )


def test_module_diagnostic_contract_and_preempted_branch() -> None:
    scenarios = (
        (
            "APX-MODULE-001",
            {"bad.apex": "module app.main extra\ndirective Main {}\n"},
            "bad.apex",
            1,
            "module app.main extra",
            (),
            "",
        ),
        (
            "APX-MODULE-002",
            {"bad.apex": "module app.one\nmodule app.two\ndirective Main {}\n"},
            "bad.apex",
            2,
            "app.two",
            ("app.one",),
            "",
        ),
        (
            "APX-MODULE-003",
            {"bad.apex": "import app.one\nmodule app.main\ndirective Main {}\n"},
            "bad.apex",
            1,
            "app.one",
            (),
            "",
        ),
        (
            "APX-MODULE-004",
            {
                "bad.apex": (
                    "module app.main\nimport app.one\nimport app.one\n"
                    "directive Main {}\n"
                )
            },
            "bad.apex",
            3,
            "app.one",
            ("app.one",),
            "",
        ),
        (
            "APX-MODULE-005",
            {
                "legacy.apex": "directive Legacy {}\n",
                "module.apex": "module app.main\n\ndirective Main {}\n",
            },
            "legacy.apex",
            1,
            "",
            (),
            "",
        ),
        (
            "APX-MODULE-006",
            {
                "bad.apex": (
                    "module app.main\nimport app.missing\n\ndirective Main {}\n"
                )
            },
            "bad.apex",
            2,
            "app.missing",
            (),
            "",
        ),
        (
            "APX-MODULE-007",
            {
                "a.apex": "module cycle.a\nimport cycle.b\n\ndirective A {}\n",
                "b.apex": "module cycle.b\nimport cycle.a\n\ndirective B {}\n",
            },
            "a.apex",
            2,
            "cycle.b",
            ("cycle.a",),
            "",
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
            "a-root.apex",
            3,
            "invoke Leaf",
            (),
            "invoke:",
        ),
        (
            "APX-MODULE-009",
            {
                "a.apex": "module App.Shared\n\ndirective A {}\n",
                "b.apex": "module app.shared\n\ndirective B {}\n",
            },
            "b.apex",
            1,
            "app.shared",
            ("App.Shared",),
            "",
        ),
    )

    for code, sources, source_name, line, primary, related, air_prefix in scenarios:
        error = require_raises(
            ProjectModuleError,
            lambda sources=sources: build_project(sources),
            f"{code} scenario was accepted",
        )
        item = diagnostic_of(error)
        require(
            item.severity == "error"
            and item.stage == "module"
            and item.code == code
            and item.span is not None
            and item.span.source_name == source_name
            and item.span.start.line == line
            and span_text(item.span, sources) == primary
            and tuple(span_text(span, sources) for span in item.related_spans)
            == related
            and (
                item.air_id.startswith(air_prefix)
                if air_prefix
                else item.air_id == ""
            ),
            f"{code} stage, span, related span, or air_id changed",
        )

    preempted = require_raises(
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
        "module-after-import branch was accepted",
    )
    require(
        diagnostic_of(preempted).code == "APX-MODULE-002",
        "the preempted module-after-import APX-MODULE-003 branch was repaired",
    )


def test_cli_artifact_language_server_and_temporary_isolation() -> None:
    original_directory = Path.cwd().resolve()
    temporary_path: Path

    with TemporaryDirectory(prefix="apexforge-p11-3c-") as temporary:
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
                    "name": "P11_3C_Export_Visibility_Audit",
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
            raise AssertionError("P11.3C audit smoke test attempted network access")

        with patch("socket.create_connection", side_effect=forbidden_network), patch(
            "socket.socket", side_effect=forbidden_network
        ):
            check = invoke_cli(("check", str(temporary_path)))
            run = invoke_cli(("run", str(temporary_path)))
            build_cli = invoke_cli(
                ("build", str(temporary_path), "--output", str(output_path))
            )
            indexed = workspace_symbols(temporary_path.as_uri(), "app")

        require(
            check
            == (
                0,
                "ApexForge check passed: P11_3C_Export_Visibility_Audit (2 source(s)).\n",
                "",
            ),
            "CLI check output changed",
        )
        require(
            run
            == (
                0,
                "ApexForge run succeeded: P11_3C_Export_Visibility_Audit\n"
                "Entry: directive:Main\n"
                "Runtime diagnostics: 0\n",
                "",
            ),
            "CLI run output changed",
        )
        require(
            build_cli[0] == 0
            and build_cli[2] == ""
            and build_cli[1].startswith(
                "ApexForge build succeeded: P11_3C_Export_Visibility_Audit\n"
                "Schema: apexforge.build-artifact/v1\n"
                "Entry: directive:Main\n"
                "Sources: 2\nFingerprint: sha256:"
            )
            and build_cli[1].endswith("\nArtifact written.\n"),
            "CLI build output changed",
        )

        loaded = load_project(temporary_path)
        project = build_project(
            loaded.source_mapping(),
            entry=loaded.manifest.entry,
        )
        before = construct_build_artifact(loaded, project)
        project.document_graph.direct_document_dependencies("src/10-main.apex")
        project.document_graph.transitive_document_dependencies("src/10-main.apex")
        after = construct_build_artifact(loaded, project)
        require(
            output_path.read_bytes() == before.content == after.content
            and before.fingerprint == after.fingerprint,
            "document graph access or CLI changed artifact bytes/fingerprint",
        )
        artifact = json.loads(after.content.decode("utf-8"))
        forbidden_keys = {
            "export",
            "exports",
            "visibility",
            "module",
            "modules",
            "module_graph",
            "qualified",
            "qualification",
            "document_graph",
        }

        def keys(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    yield key
                    yield from keys(item)
            elif isinstance(value, list):
                for item in value:
                    yield from keys(item)

        require(
            set(artifact) == {"schema", "project", "air", "fingerprint"}
            and artifact["schema"] == "apexforge.build-artifact/v1"
            and not forbidden_keys.intersection(keys(artifact)),
            "artifact v1 acquired export, visibility, qualification, module, or graph fields",
        )

        uri = "file:///workspace/main.apex"
        source = (
            "module app.main;\n"
            "import app.missing;\n\n"
            "directive Main { state count = 1 }\n"
        )
        require(
            analyze_document(uri, source) == (),
            "language server acquired project-aware missing-import diagnostics",
        )
        symbols = document_symbols(uri, source)
        require(
            len(symbols) == 1
            and symbols[0]["name"] == "app.main"
            and tuple(child["detail"] for child in symbols[0]["children"])
            == ("import", "directive"),
            "document symbols stopped being syntax-oriented",
        )
        import_position = lsp_position(source, "app.missing")
        module_position = lsp_position(source, "app.main")
        import_hover = hover(uri, source, import_position)
        require(
            import_hover is not None
            and "Direct module import." in import_hover["contents"]["value"]
            and definition(uri, source, import_position) is None
            and len(
                references(
                    uri,
                    source,
                    module_position,
                    {"includeDeclaration": True},
                )
            )
            == 1
            and prepare_rename(uri, source, module_position) is None
            and rename(uri, source, module_position, "renamed") is None,
            "hover/definition/references/rename crossed the document boundary",
        )
        edits = format_document(
            uri,
            source,
            {"tabSize": 4, "insertSpaces": True},
        )
        require(
            len(edits) == 1
            and edits[0]["newText"].startswith(
                "module app.main\nimport app.missing\n\n"
            ),
            "module/import syntax formatting changed",
        )
        export_source = "module app.main\nexport Main\n\ndirective Main {}\n"
        export_diagnostics = analyze_document(uri, export_source)
        require(
            len(export_diagnostics) == 1
            and export_diagnostics[0]["code"] == "APX-PARSE-002"
            and document_symbols(uri, export_source) == ()
            and format_document(
                uri,
                export_source,
                {"tabSize": 4, "insertSpaces": True},
            )
            == (),
            "language server acquired export awareness",
        )
        require(
            {item["name"] for item in indexed if item.get("kind") == 2}
            >= {"app.main", "app.worker"},
            "workspace symbols stopped independently indexing modules",
        )
        require(
            not tuple(temporary_path.glob(".*.tmp"))
            and Path.cwd().resolve() == original_directory,
            "temporary output residue or working-directory mutation detected",
        )

    require(
        not temporary_path.exists() and Path.cwd().resolve() == original_directory,
        "temporary fixture escaped its context manager",
    )


def main() -> None:
    status_before = repository_status()

    test_parser_inventory_and_absent_export_features()
    test_lowering_ownership_flat_ids_and_unsupported_forms()
    test_direct_transitive_and_legacy_visibility()
    test_collisions_generics_and_entry_identity()
    test_document_and_module_graph_boundaries()
    test_module_diagnostic_contract_and_preempted_branch()
    test_cli_artifact_language_server_and_temporary_isolation()

    require(
        repository_status() == status_before,
        "running the P11.3C audit smoke test changed repository status",
    )

    print("AFP-P11.3C export and visibility architecture audit smoke test passed.")
    print("Parser and declaration inventory; absent export syntax: PASS")
    print("Lowering, ownership evidence, and flat identities: PASS")
    print("Direct, transitive, and legacy visibility: PASS")
    print("Collisions, generics, and entry identity: PASS")
    print("ProjectDocumentGraph and ModuleGraph boundaries: PASS")
    print("APX-MODULE-001 through APX-MODULE-009 preservation: PASS")
    print("CLI, artifact v1, language server, and isolation: PASS")
    print("Repository status preservation: PASS")


if __name__ == "__main__":
    main()
