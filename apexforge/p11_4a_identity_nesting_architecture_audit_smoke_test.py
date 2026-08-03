"""Executable current-behavior record for the P11.4A identity/nesting audit.

This audit test changes no production behavior.  It composes the accepted
P11.2/P11.3 executable records and adds focused identity, generic, nesting,
scope, entry, artifact, language-server, and Visual Studio assertions.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
import hashlib
from pathlib import Path
import subprocess
from unittest.mock import patch

from air.expressions import AIRCallExpression
from air.serialization import air_to_dict
from language.compiler import compile_source_with_map
from language.grammar import TOP_LEVEL_DECLARATIONS
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
    ProjectBuildError,
    ProjectCompilationError,
    ProjectEntryPointError,
    ProjectLinkError,
    ProjectModuleError,
    ProjectValidationError,
    build_project,
)
from language_server.integration import (
    CANONICAL_INTEGRATION_SHA256,
    integration_fingerprint,
    verify_frozen_feature_hashes,
)
from p11_2a_declaration_model_audit_smoke_test import (
    test_duplicates_collisions_and_diagnostics as accepted_declaration_collisions,
    test_one_source_boundary_and_invalid_nesting as accepted_nesting_boundary,
    test_other_frozen_top_level_forms as accepted_parsed_only_forms,
)
from p11_2b_multi_directive_source_unit_smoke_test import (
    test_parser_shape_order_comments_and_single_compatibility as accepted_legacy_sequence,
    test_source_aware_rejections as accepted_source_unit_rejections,
)
from p11_3c_export_visibility_architecture_audit_smoke_test import (
    test_cli_artifact_language_server_and_temporary_isolation as accepted_cli_artifact_lsp,
    test_collisions_generics_and_entry_identity as accepted_module_identity,
    test_direct_transitive_and_legacy_visibility as accepted_visibility,
    test_document_and_module_graph_boundaries as accepted_graph_boundaries,
    test_lowering_ownership_flat_ids_and_unsupported_forms as accepted_flat_ids,
    test_module_diagnostic_contract_and_preempted_branch as accepted_module_diagnostics,
    test_parser_inventory_and_absent_export_features as accepted_parser_inventory,
)
from p11_3d_canonical_declaration_ownership_smoke_test import (
    test_cli_artifact_language_server_and_isolation as accepted_ownership_compatibility,
    test_legacy_projection_and_project_build_compatibility as accepted_legacy_ownership,
    test_module_projection_visibility_and_graph_boundaries as accepted_module_ownership,
    test_public_model_shape_validation_order_and_queries as accepted_ownership_model,
)
from tooling.project_manifest import PROJECT_MANIFEST_SCHEMA, ProjectManifest
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
    records: list[tuple[str, int, int]] = []
    for path in REPOSITORY_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in {".pyc", ".pyo"}:
            continue
        details = path.stat()
        records.append(
            (
                path.relative_to(REPOSITORY_ROOT).as_posix(),
                details.st_size,
                details.st_mtime_ns,
            )
        )
    return tuple(sorted(records))


def recursive_call_targets(value: object):
    if isinstance(value, AIRCallExpression):
        yield value.target
    if is_dataclass(value):
        for field in fields(value):
            yield from recursive_call_targets(getattr(value, field.name))
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from recursive_call_targets(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from recursive_call_targets(item)


def test_current_declaration_and_identity_inventory() -> None:
    accepted_parser_inventory()
    accepted_flat_ids()
    accepted_ownership_model()
    accepted_legacy_ownership()

    require(
        TOP_LEVEL_DECLARATIONS
        == ("function", "directive", "workflow", "authority", "principal", "role"),
        "the exact top-level declaration inventory changed",
    )
    samples = (
        ("function F() { return 1 }", FunctionNode),
        ("directive D {}", DirectiveNode),
        ("workflow W {}", WorkflowNode),
        ("authority A {}", AuthorityNode),
        ("principal P {}", PrincipalNode),
        ("role R {}", RoleNode),
    )
    for source, node_type in samples:
        require(isinstance(parse(source), node_type), f"{node_type.__name__} mapping changed")

    require(
        not hasattr(__import__("language.parser", fromlist=["IdentityNode"]), "IdentityNode"),
        "identity became a separate declaration family",
    )

    rich = compile_source_with_map(
        "directive Rich {\n"
        " state count : int = 0\n"
        " event done\n"
        " cause flow {\n"
        "  path primary @ 1 {\n"
        "   when true { when false { add count 1 } otherwise { emit done } }\n"
        "   otherwise { set count = 2 }\n"
        "  }\n"
        " }\n"
        "}\n",
        source_name="rich.apex",
    )
    identities = {(entry.kind, entry.air_id) for entry in rich.source_map.entries}
    require(
        {
            ("directive", "directive:Rich"),
            ("principal", "principal:Rich"),
            ("authority_check", "auth:Rich"),
            ("state", "state:count"),
            ("event", "event:done"),
            ("causal_decision", "cause:flow"),
            ("causal_path", "path:primary"),
        }.issubset(identities),
        "directive/member canonical or source-map identities changed",
    )
    require(
        any(kind == "conditional_action" and air_id.startswith("when:Rich:flow:primary")
            for kind, air_id in identities),
        "nested action sidecar identity changed",
    )

    generic = compile_source_with_map(
        "function Identity<T : numeric>(value : T) : T {\n"
        " when true { let inner = value return inner }\n"
        " otherwise { return value }\n"
        "}\n",
        source_name="identity.apex",
    )
    generic_entries = {(item.kind, item.air_id, item.reference) for item in generic.source_map.entries}
    require(
        ("function", "function:Identity", "Identity") in generic_entries
        and ("function_type_parameter", "type_parameter:Identity:0", "T") in generic_entries
        and ("function_parameter", "parameter:Identity:0", "value") in generic_entries
        and any(item[0] == "function_local" and item[1].startswith("local:Identity:")
                for item in generic_entries),
        "function lexical/source-map identity inventory changed",
    )


def test_collisions_modules_visibility_and_entries() -> None:
    accepted_declaration_collisions()
    accepted_visibility()
    accepted_module_identity()
    accepted_graph_boundaries()
    accepted_module_diagnostics()
    accepted_module_ownership()

    cross_kind = build_project(
        {
            "directive.apex": "directive Same {}\n",
            "function.apex": "function Same() : int { return 1 }\n",
        },
        entry="Same",
    )
    require(
        tuple(item.id for item in cross_kind.program.directives) == ("directive:Same",)
        and tuple(item.id for item in cross_kind.program.functions) == ("function:Same",),
        "cross-kind equal short names stopped coexisting",
    )

    for member, source_fragment, expected_id in (
        ("state", "state shared = 1", "state:shared"),
        ("event", "event shared", "event:shared"),
        ("cause", "cause shared { path p @ 1 {} }", "cause:shared"),
    ):
        error = require_raises(
            ProjectLinkError,
            lambda source_fragment=source_fragment: build_project(
                {
                    "a.apex": f"directive A {{ {source_fragment} }}\n",
                    "b.apex": f"directive B {{ {source_fragment} }}\n",
                }
            ),
            f"duplicate {member} stopped colliding globally",
        )
        item = diagnostic_of(error)
        require(
            item.stage == "link" and item.code == "APX-LINK-001" and item.air_id == expected_id,
            f"duplicate {member} diagnostic identity changed",
        )

    path_duplicate = require_raises(
        ProjectValidationError,
        lambda: build_project(
            {"paths.apex": "directive Paths { cause flow { path p @ 1 {} path p @ 2 {} } }"}
        ),
        "duplicate cause-local path was accepted",
    )
    require(
        diagnostic_of(path_duplicate).stage == "validate"
        and diagnostic_of(path_duplicate).code == "APX-VALIDATE-999",
        "duplicate path validation fallback changed",
    )
    distinct_cause_paths = build_project(
        {
            "paths.apex": (
                "directive Paths { cause left { path shared @ 1 {} } "
                "cause right { path shared @ 1 {} } }"
            )
        }
    )
    require(
        tuple(path.id for cause in distinct_cause_paths.program.causal_decisions for path in cause.paths)
        == ("path:shared", "path:shared"),
        "path identity stopped being cause-local in the AIR shape",
    )

    entries = build_project(
        {
            "a.apex": "module App.A\n\ndirective Alpha {}\n",
            "b.apex": "module App.B\n\ndirective alpha {}\n",
        }
    )
    require(
        entries.resolve_entry("Alpha") == "directive:Alpha"
        and entries.resolve_entry("directive:alpha") == "directive:alpha",
        "entry identity stopped being exact-case",
    )
    require_raises(
        ProjectEntryPointError,
        lambda: entries.resolve_entry("ALPHA"),
        "entry lookup became case-insensitive",
    )

    unsupported = (
        ("alias.apex", "module App\nimport Lib as Local\n\ndirective Main {}", ProjectModuleError),
        ("namespace.apex", "namespace App { directive Main {} }", ProjectCompilationError),
        ("qualified-invoke.apex", "directive Main { cause c { path p @ 1 { invoke Lib.Worker } } }", ProjectCompilationError),
        ("qualified-call.apex", "function Main() { return Lib.Worker() }", ProjectCompilationError),
    )
    for source_name, source, error_type in unsupported:
        require_raises(
            error_type,
            lambda source_name=source_name, source=source: build_project({source_name: source}),
            f"unsupported identity syntax in {source_name} was accepted",
        )


def test_generic_identity_lifecycle() -> None:
    project = build_project(
        {
            "generic.apex": (
                "module Lib.Generic\n\n"
                "function Identity<T : numeric>(value : T) : T { return value }\n"
            ),
            "use.apex": (
                "module App.Use\nimport Lib.Generic\n\n"
                "function Use(value : int) : int {\n"
                " let inferred = Identity(value)\n"
                " return Identity<int>(inferred)\n"
                "}\n"
            ),
        }
    )
    declaration = next(item for item in project.program.functions if item.name == "Identity")
    manifest = collect_linked_specializations(project.program)
    lowered = lower_linked_generics(project.program)
    digest = hashlib.sha256(b"Identity<int>").hexdigest()[:10]
    expected_name = f"__apx_spec__Identity__int__{digest}"
    expected_id = f"function:{expected_name}"

    require(
        declaration.id == "function:Identity"
        and declaration.type_parameters[0].owner == "function:Identity"
        and manifest.canonical_ids == ("Identity<int>",)
        and lowered.canonical_ids == ("Identity<int>",),
        "generic declaration/key/closure identity changed",
    )
    binding = lowered.binding_for("Identity<int>")
    require(
        binding is not None
        and binding.function_name == expected_name
        and binding.function_id == expected_id
        and lowered.lowered_target("Identity<int>") == expected_name,
        "lowered generic target identity changed",
    )
    require(
        "function:Identity" in {item.id for item in lowered.functions}
        and expected_id in {item.id for item in lowered.specialized_functions}
        and expected_name in set(recursive_call_targets(lowered.program)),
        "generic traceability or runtime dispatch target changed",
    )
    serialized = air_to_dict(project.program)
    require(
        {item["id"] for item in serialized["functions"]}
        == {"function:Identity", "function:Use"}
        and all("__apx_spec__" not in item["id"] for item in serialized["functions"]),
        "ordinary project artifact AIR unexpectedly contains explicit lowering output",
    )
    require(
        project.declaration_ownership.find_all("function:Identity")
        == project.declaration_ownership.for_module("Lib.Generic")
        and project.declaration_ownership.find_all("Identity<int>") == ()
        and project.declaration_ownership.find_all(expected_id) == (),
        "specialization/lowered identities entered declaration ownership",
    )

    duplicate_generic = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a.apex": "function Identity<T>(value : T) : T { return value }",
                "b.apex": "function Identity<U>(value : U) : U { return value }",
            }
        ),
        "equal generic declaration names formed an overload set",
    )
    require(
        diagnostic_of(duplicate_generic).code == "APX-LINK-001"
        and diagnostic_of(duplicate_generic).air_id == "function:Identity",
        "generic declaration collision identity changed",
    )


def test_nesting_and_scope_inventory() -> None:
    accepted_nesting_boundary()
    accepted_parsed_only_forms()
    accepted_legacy_sequence()
    accepted_source_unit_rejections()

    legal = build_project(
        {
            "function.apex": (
                "function Choose(flag : bool) : int {\n"
                " when flag {\n"
                "  when true { let value = 1 return value } otherwise { return 2 }\n"
                " } otherwise { let value = 3 return value }\n"
                "}\n"
            ),
            "directive.apex": (
                "directive Nested {\n"
                " state count = 0\n event done\n"
                " cause flow { path main @ 1 {\n"
                "  when true { when false { add count 1 } otherwise { emit done } }\n"
                "  otherwise { set count = 2 }\n"
                " } }\n"
                "}\n"
            ),
        },
        entry="Nested",
    )
    require(
        legal.resolve_entry() == "directive:Nested"
        and len(legal.program.functions[0].body) == 1
        and len(legal.program.causal_decisions[0].paths[0].actions) == 1,
        "legal member or conditional nesting changed",
    )

    rejected = (
        ("directive-in-directive.apex", "directive Outer { directive Inner {} }", "APX-PARSE-003"),
        ("function-in-function.apex", "function Outer() { function Inner() { return 1 } return 1 }", "APX-PARSE-007"),
        ("function-in-directive.apex", "directive Outer { function Inner() { return 1 } }", "APX-PARSE-003"),
        ("directive-in-function.apex", "function Outer() { directive Inner {} return 1 }", "APX-PARSE-007"),
        ("workflow-in-workflow.apex", "workflow Outer { workflow Inner {} }", "APX-PARSE-001"),
        ("authority-in-authority.apex", "authority Outer { authority Inner {} }", "APX-PARSE-001"),
        ("principal-in-principal.apex", "principal Outer { principal Inner {} }", "APX-PARSE-003"),
        ("role-in-role.apex", "role Outer { role Inner {} }", "APX-PARSE-001"),
        ("generic-in-function.apex", "function Outer() { function Inner<T>(x : T) : T { return x } return 1 }", "APX-PARSE-007"),
    )
    for source_name, source, code in rejected:
        error = require_raises(
            ProjectCompilationError,
            lambda source_name=source_name, source=source: build_project({source_name: source}),
            f"unsupported nesting in {source_name} was accepted",
        )
        item = diagnostic_of(error)
        require(
            item.stage == "parse" and item.code == code and item.span.source_name == source_name,
            f"unsupported nesting diagnostic changed for {source_name}",
        )

    for keyword, body in (
        ("state", "state count = 1"),
        ("event", "event done"),
        ("cause", "cause flow { path p @ 1 {} }"),
        ("path", "path p @ 1 {}"),
    ):
        error = require_raises(
            ProjectCompilationError,
            lambda keyword=keyword, body=body: build_project({f"{keyword}.apex": body}),
            f"{keyword} became an independent top-level declaration",
        )
        require(
            diagnostic_of(error).stage == "parse" and diagnostic_of(error).code == "APX-PARSE-002",
            f"top-level {keyword} rejection changed",
        )

    for source_name, source in (
        ("module-inside.apex", "directive Main {\nmodule Inner\n}"),
        ("import-inside.apex", "function Main() {\nimport Lib\nreturn 1\n}"),
    ):
        error = require_raises(
            ProjectModuleError,
            lambda source_name=source_name, source=source: build_project({source_name: source}),
            f"header syntax inside a declaration was accepted in {source_name}",
        )
        require(diagnostic_of(error).code == "APX-MODULE-001", "late header diagnostic changed")

    duplicate_parameter = require_raises(
        ProjectCompilationError,
        lambda: build_project({"parameter.apex": "function F(x, x) { return x }"}),
        "duplicate parameter was accepted",
    )
    duplicate_local = require_raises(
        ProjectCompilationError,
        lambda: build_project({"local.apex": "function F() { let x = 1 let x = 2 return x }"}),
        "duplicate local was accepted",
    )
    shadow = require_raises(
        ProjectCompilationError,
        lambda: build_project({"shadow.apex": "function F(x) { let x = 1 return x }"}),
        "parameter shadowing was accepted",
    )
    forward = require_raises(
        ProjectValidationError,
        lambda: build_project({"forward.apex": "function F() { let x = y let y = 1 return x }"}),
        "forward local reference was accepted",
    )
    require(
        diagnostic_of(duplicate_parameter).code == "APX-COMPILE-008"
        and diagnostic_of(duplicate_local).code == "APX-COMPILE-009"
        and diagnostic_of(shadow).code == "APX-COMPILE-010"
        and diagnostic_of(forward).code == "APX-VALIDATE-006",
        "parameter/local scope diagnostic stages changed",
    )

    branch_reuse = build_project(
        {
            "branch.apex": (
                "function F(flag : bool) : int { "
                "when flag { let x = 1 return x } "
                "otherwise { let x = 2 return x } }"
            )
        }
    )
    require(branch_reuse.program.functions[0].id == "function:F", "sibling branch scopes changed")
    branch_escape = require_raises(
        ProjectCompilationError,
        lambda: build_project(
            {"escape.apex": "function F(flag : bool) : int { when flag { let x = 1 } return x }"}
        ),
        "branch local escaped into the containing function",
    )
    require(diagnostic_of(branch_escape).code == "APX-TYPE-001", "branch escape diagnostic changed")

    duplicate_type = require_raises(
        ProjectCompilationError,
        lambda: build_project({"type.apex": "function F<T,T>(x : T) : T { return x }"}),
        "duplicate generic type parameter was accepted",
    )
    builtin_shadow = require_raises(
        ProjectCompilationError,
        lambda: build_project({"builtin.apex": "function F<int>(x : int) : int { return x }"}),
        "generic type parameter shadowed a built-in type",
    )
    require(
        diagnostic_of(duplicate_type).code == "APX-PARSE-009"
        and diagnostic_of(builtin_shadow).code == "APX-PARSE-010",
        "generic type-parameter scope diagnostics changed",
    )

    legacy = build_project({"legacy.apex": "directive First {}\ndirective Second {}\n"}, entry="First")
    require(
        tuple(item.id for item in legacy.program.directives)
        == ("directive:First", "directive:Second"),
        "P11.2B sequential legacy directives changed",
    )
    module_many = require_raises(
        ProjectCompilationError,
        lambda: build_project(
            {"module.apex": "module App.Main\n\ndirective First {}\ndirective Second {}\n"}
        ),
        "module source accepted more than one ordinary declaration",
    )
    require(diagnostic_of(module_many).code == "APX-PARSE-001", "module source cardinality changed")


def test_external_compatibility_and_repository_boundaries() -> None:
    accepted_cli_artifact_lsp()
    accepted_ownership_compatibility()

    manifest = ProjectManifest("IdentityAudit", ("src/main.apex",), "directive:Main")
    require(
        PROJECT_MANIFEST_SCHEMA == 1
        and tuple(manifest.to_mapping()) == ("schema", "name", "sources", "entry"),
        "manifest schema 1 shape changed",
    )
    require(
        verify_frozen_feature_hashes()
        and integration_fingerprint() == CANONICAL_INTEGRATION_SHA256
        == "c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897",
        "frozen language-server behavior changed",
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
        "Visual Studio diagnostics/intelligence integration changed",
    )


def main() -> None:
    original_directory = Path.cwd().resolve()
    status_before = repository_status()
    bytecode_before = repository_bytecode_state()

    def forbidden_network(*_args, **_kwargs):
        raise AssertionError("P11.4A audit attempted network access")

    with patch("socket.create_connection", side_effect=forbidden_network), patch(
        "socket.socket", side_effect=forbidden_network
    ):
        test_current_declaration_and_identity_inventory()
        test_collisions_modules_visibility_and_entries()
        test_generic_identity_lifecycle()
        test_nesting_and_scope_inventory()
        test_external_compatibility_and_repository_boundaries()

    require(Path.cwd().resolve() == original_directory, "working directory changed")
    require(repository_status() == status_before, "running the audit changed repository status")
    require(
        repository_bytecode_state() == bytecode_before,
        "running the audit created, removed, or changed repository bytecode",
    )

    print("AFP-P11.4A identity and nesting architecture audit smoke test passed.")
    print("Declaration and identity-layer inventory: PASS")
    print("Ownership, modules, visibility, collisions, entries, and diagnostics: PASS")
    print("Generic declaration, specialization, closure, lowering, and dispatch: PASS")
    print("Nesting, lexical scope, P11.2B, and module-source boundaries: PASS")
    print("CLI, manifest, artifact v1, runtime, LSP, and Visual Studio: PASS")
    print("Network, temporary fixture, working-directory, and repository safety: PASS")


if __name__ == "__main__":
    main()
