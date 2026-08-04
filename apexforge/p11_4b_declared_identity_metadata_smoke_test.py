"""Focused production coverage for P11.4B declared identity metadata."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from io import StringIO
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from air.serialization import air_to_dict
from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
import language.identities as identities_module
from language.compiler import compile_source
from language.declarations import ProjectDeclarationOwnership
from language.identities import ProjectDeclaredIdentity, ProjectIdentityIndex
from language.modules import ProjectDocumentGraph
from language.project import (
    ProjectBuild,
    ProjectBuilder,
    ProjectCompilationError,
    ProjectLinkError,
    build_project,
)
from language.source import SourceText
from language_server.integration import (
    CANONICAL_INTEGRATION_SHA256,
    integration_fingerprint,
    verify_frozen_feature_hashes,
)
from p11_3c_export_visibility_architecture_audit_smoke_test import (
    test_direct_transitive_and_legacy_visibility as accepted_visibility,
)
from runtime.context import ExecutionContext
from runtime.state import StateSnapshot
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


def air_fingerprint(build: ProjectBuild) -> str:
    content = json.dumps(
        air_to_dict(build.program),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def execution_context(build: ProjectBuild, *names: str) -> ExecutionContext:
    return ExecutionContext(
        state=StateSnapshot.from_program_initials(build.program),
        authority=AuthorityEngine.from_grants(
            tuple(
                AuthorityGrant(
                    principal=f"principal:{name}",
                    capability=f"directive.invoke:{name}",
                    resource=f"directive:{name}",
                )
                for name in names
            )
        ),
    )


def test_public_model_validation_order_queries_and_immutability() -> None:
    require(
        identities_module.__all__
        == ("ProjectDeclaredIdentity", "ProjectIdentityIndex"),
        "language.identities exports an unintended public name",
    )
    require(
        tuple(item.name for item in fields(ProjectDeclaredIdentity))
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
        == ("identities",),
        "declared identity dataclass fields changed",
    )
    require(
        ProjectDeclaredIdentity.__dataclass_params__.frozen
        and ProjectIdentityIndex.__dataclass_params__.frozen,
        "declared identity metadata is mutable",
    )
    forbidden_fields = {
        "alias",
        "canonical_id",
        "owner",
        "parent_identity",
        "scope",
        "visibility",
        "entry",
        "specialization",
    }
    require(
        forbidden_fields.isdisjoint(
            item.name for item in fields(ProjectDeclaredIdentity)
        ),
        "the P11.4B record acquired unavailable or resolving metadata",
    )

    upper_text = SourceText("A.apex", "directive Alpha {}\n")
    lower_text = SourceText("a.apex", "function Alpha() { return 1 }\n")
    zed_text = SourceText("z.apex", "function Zed() { return 1 }\n")
    legacy = ProjectDeclaredIdentity(
        "directive",
        "Alpha",
        "directive:Alpha",
        "A.apex",
        None,
        "Alpha",
        upper_text.span(0, 18),
    )
    module_directive = ProjectDeclaredIdentity(
        "directive",
        "Alpha",
        "directive:Alpha",
        "A.apex",
        "App.Core",
        "App.Core.Alpha",
        upper_text.span(0, 18),
    )
    display_collision = ProjectDeclaredIdentity(
        "function",
        "Alpha",
        "function:Alpha",
        "a.apex",
        "App.Core",
        "App.Core.Alpha",
        lower_text.span(0, 29),
    )
    zed = ProjectDeclaredIdentity(
        "function",
        "Zed",
        "function:Zed",
        "z.apex",
        "Lib.Zed",
        "Lib.Zed.Zed",
        zed_text.span(0, 27),
    )
    index = ProjectIdentityIndex(
        [zed, display_collision, module_directive, legacy]
    )
    require(
        isinstance(index.identities, tuple)
        and index.identities
        == (legacy, module_directive, display_collision, zed),
        "canonical identity ordering or tuple normalization changed",
    )
    require(
        index.for_source("A.apex") == (legacy, module_directive)
        and index.for_module("App.Core")
        == (module_directive, display_collision)
        and index.find_all("directive", "Alpha")
        == (legacy, module_directive)
        and index.find_current_air_id("directive:Alpha")
        == (legacy, module_directive)
        and index.find_qualified_display_name("App.Core.Alpha")
        == (module_directive, display_collision),
        "identity queries lost canonical order or duplicate retention",
    )
    require(
        index.for_source("A.APEX") == ()
        and index.for_module("app.core") == ()
        and index.find_all("directive", "alpha") == ()
        and index.find_current_air_id("Directive:Alpha") == ()
        and index.find_qualified_display_name("app.core.Alpha") == ()
        and index.find_all("function", "Missing") == (),
        "identity query matching stopped being exact-case",
    )

    single_queries = (
        index.for_source,
        index.for_module,
        index.find_current_air_id,
        index.find_qualified_display_name,
    )
    for query in single_queries:
        require_raises(TypeError, lambda query=query: query(None), "non-string query accepted")
        require_raises(ValueError, lambda query=query: query(" \t"), "blank query accepted")
    require_raises(
        TypeError,
        lambda: index.find_all(None, "Alpha"),
        "non-string declaration kind query accepted",
    )
    require_raises(
        ValueError,
        lambda: index.find_all("workflow", "Alpha"),
        "unsupported declaration kind query accepted",
    )
    require_raises(
        TypeError,
        lambda: index.find_all("directive", None),
        "non-string declared-name query accepted",
    )
    require_raises(
        ValueError,
        lambda: index.find_all("directive", " "),
        "blank declared-name query accepted",
    )

    require_raises(
        FrozenInstanceError,
        lambda: setattr(legacy, "current_air_id", "directive:Changed"),
        "declared identity record is mutable",
    )
    require_raises(
        FrozenInstanceError,
        lambda: setattr(index, "identities", ()),
        "declared identity index is mutable",
    )
    require_raises(
        TypeError,
        lambda: ProjectIdentityIndex((object(),)),
        "non-identity collection member accepted",
    )

    valid_span = SourceText("valid.apex", "directive Valid {}\n").span(0, 18)
    invalid_constructors = (
        lambda: ProjectDeclaredIdentity(
            "workflow", "Valid", "workflow:Valid", "valid.apex", None, "Valid", valid_span
        ),
        lambda: ProjectDeclaredIdentity(
            "directive", "App.Valid", "directive:App.Valid", "valid.apex", None, "App.Valid", valid_span
        ),
        lambda: ProjectDeclaredIdentity(
            "directive", "Valid", "function:Valid", "valid.apex", None, "Valid", valid_span
        ),
        lambda: ProjectDeclaredIdentity(
            "directive", "Valid", "directive:Other", "valid.apex", None, "Valid", valid_span
        ),
        lambda: ProjectDeclaredIdentity(
            "directive", "Valid", "directive:Valid", " ", None, "Valid", valid_span
        ),
        lambda: ProjectDeclaredIdentity(
            "directive", "Valid", "directive:Valid", "valid.apex", "App..Core", "App..Core.Valid", valid_span
        ),
        lambda: ProjectDeclaredIdentity(
            "directive", "Valid", "directive:Valid", "valid.apex", None, "App.Valid", valid_span
        ),
        lambda: ProjectDeclaredIdentity(
            "directive", "Valid", "directive:Valid", "valid.apex", "App", "Valid", valid_span
        ),
        lambda: ProjectDeclaredIdentity(
            "directive", "Valid", "directive:Valid", "valid.apex", None, "Valid", object()
        ),
        lambda: ProjectDeclaredIdentity(
            "directive", "Valid", "directive:Valid", "other.apex", None, "Valid", valid_span
        ),
    )
    for constructor in invalid_constructors:
        require_raises(
            (TypeError, ValueError),
            constructor,
            "invalid declared identity metadata was accepted",
        )


def test_collection_determinism_families_and_project_compatibility() -> None:
    legacy_sources = {
        "30-rich.apex": (
            "directive Rich { state count = 0 event done "
            "cause flow { path primary @ 1 { emit done } } }\n"
        ),
        "20-function.apex": "function Echo(value : int) : int { return value }\n",
        "10-many.apex": "directive Zebra {}\ndirective Alpha {}\n",
    }
    legacy = build_project(legacy_sources, entry="Alpha")
    expected_legacy = (
        ("directive", "Alpha", "directive:Alpha", "10-many.apex", None, "Alpha"),
        ("directive", "Rich", "directive:Rich", "30-rich.apex", None, "Rich"),
        ("directive", "Zebra", "directive:Zebra", "10-many.apex", None, "Zebra"),
        ("function", "Echo", "function:Echo", "20-function.apex", None, "Echo"),
    )
    require(
        tuple(
            (
                item.kind,
                item.declared_name,
                item.current_air_id,
                item.source_name,
                item.module_name,
                item.qualified_display_name,
            )
            for item in legacy.identity_index.identities
        )
        == expected_legacy,
        "legacy declared identity collection or ordering changed",
    )
    require(
        len(legacy.identity_index.identities)
        == len(legacy.declaration_ownership.declarations)
        == len(legacy.program.directives) + len(legacy.program.functions)
        and {
            (identity.kind, identity.current_air_id, identity.source_name, identity.span)
            for identity in legacy.identity_index.identities
        }
        == {
            (owner.kind, owner.air_id, owner.source_name, owner.span)
            for owner in legacy.declaration_ownership.declarations
        },
        "identity and ownership metadata stopped being one-to-one",
    )
    require(
        not {
            "state:count",
            "event:done",
            "cause:flow",
            "path:primary",
        }.intersection(
            identity.current_air_id for identity in legacy.identity_index.identities
        ),
        "nested members entered the declared identity index",
    )

    module_sources = {
        "30-root.apex": "module App.Root\nimport App.Worker\n\ndirective Root {}\n",
        "20-worker.apex": "module App.Worker\n\nfunction Worker() : int { return 1 }\n",
        "10-leaf.apex": "module Lib.Leaf\n\ndirective Leaf {}\n",
    }
    first = build_project(module_sources, entry="Root")
    reversed_build = build_project(
        dict(reversed(tuple(module_sources.items()))),
        entry="Root",
    )
    repeated = build_project(module_sources, entry="Root")
    require(
        first.identity_index == reversed_build.identity_index == repeated.identity_index,
        "mapping insertion order or repeated collection changed identity metadata",
    )
    require(
        tuple(
            (
                item.current_air_id,
                item.module_name,
                item.qualified_display_name,
            )
            for item in first.identity_index.identities
        )
        == (
            ("directive:Leaf", "Lib.Leaf", "Lib.Leaf.Leaf"),
            ("directive:Root", "App.Root", "App.Root.Root"),
            ("function:Worker", "App.Worker", "App.Worker.Worker"),
        ),
        "module identity projection or exact display metadata changed",
    )
    require(
        {item.id for item in first.program.directives}
        == {"directive:Leaf", "directive:Root"}
        and tuple(item.id for item in first.program.functions)
        == ("function:Worker",)
        and tuple(
            identity.current_air_id for identity in first.identity_index.identities
        )
        == ("directive:Leaf", "directive:Root", "function:Worker"),
        "the metadata layer rewrote or requalified an AIR ID",
    )

    project_fields = fields(ProjectBuild)
    project_field_names = tuple(item.name for item in project_fields)
    document_graph_index = project_field_names.index("document_graph")
    identity_index_field = project_fields[
        project_field_names.index("identity_index")
    ]
    require(
        project_field_names[:document_graph_index]
        == (
            "source_units",
            "program",
            "verified",
            "source_map",
            "module_graph",
            "entry_directive",
        )
        and project_field_names[
            document_graph_index:document_graph_index + 3
        ]
        == ("document_graph", "declaration_ownership", "identity_index")
        and identity_index_field.compare is False,
        "ProjectBuild P11.4B metadata sequence or compatibility changed",
    )
    positional = ProjectBuild(
        first.source_units,
        first.program,
        first.verified,
        first.source_map,
        first.module_graph,
        first.entry_directive,
    )
    positional_with_existing_metadata = ProjectBuild(
        first.source_units,
        first.program,
        first.verified,
        first.source_map,
        first.module_graph,
        first.entry_directive,
        first.document_graph,
        first.declaration_ownership,
    )
    require(
        positional == first
        and positional.document_graph == ProjectDocumentGraph()
        and positional.declaration_ownership == ProjectDeclarationOwnership()
        and positional.identity_index == ProjectIdentityIndex()
        and positional_with_existing_metadata == first
        and positional_with_existing_metadata.identity_index == ProjectIdentityIndex(),
        "manual ProjectBuild positional or equality compatibility changed",
    )
    require_raises(
        TypeError,
        lambda: ProjectBuild(
            first.source_units,
            first.program,
            first.verified,
            first.source_map,
            first.module_graph,
            first.entry_directive,
            first.document_graph,
            first.declaration_ownership,
            object(),
        ),
        "ProjectBuild accepted a non-identity index",
    )

    bare_build = ProjectBuilder(compiler=lambda source: compile_source(source)).build(
        {"bare.apex": "directive Bare {}\n"}
    )
    require(
        bare_build.declaration_ownership == ProjectDeclarationOwnership()
        and bare_build.identity_index == ProjectIdentityIndex()
        and bare_build.program.directives[0].id == "directive:Bare",
        "a bare AIR compiler caused fabricated identity metadata or changed AIR",
    )


def test_air_generics_collisions_modules_and_runtime_are_unchanged() -> None:
    generic_sources = {
        "generic.apex": (
            "module Lib.Generic\n\n"
            "function Identity<T : numeric>(value : T) : T { return value }\n"
        ),
        "use.apex": (
            "module App.Use\nimport Lib.Generic\n\n"
            "function Use(value : int) : int { return Identity<int>(Identity(value)) }\n"
        ),
    }
    generic = build_project(generic_sources)
    before_air = air_to_dict(generic.program)
    before_fingerprint = air_fingerprint(generic)
    declaration = next(item for item in generic.program.functions if item.name == "Identity")
    closure = collect_linked_specializations(generic.program)
    lowered = lower_linked_generics(generic.program)
    identity_record = generic.identity_index.find_all("function", "Identity")
    after_air = air_to_dict(generic.program)
    require(
        len(identity_record) == 1
        and identity_record[0].current_air_id == declaration.id == "function:Identity"
        and declaration.type_parameters[0].owner == "function:Identity"
        and generic.identity_index.find_current_air_id("Identity<int>") == ()
        and not any(
            "__apx_spec__" in item.current_air_id
            for item in generic.identity_index.identities
        ),
        "generic declarations, specializations, or lowered targets entered the wrong identity layer",
    )
    require(
        closure.canonical_ids == lowered.canonical_ids == ("Identity<int>",)
        and lowered.lowered_target("Identity<int>") is not None
        and lowered.binding_for("Identity<int>").function_id.startswith(
            "function:__apx_spec__Identity__int__"
        )
        and before_air == after_air
        and before_fingerprint == air_fingerprint(generic),
        "generic specialization, closure, lowering, or source AIR changed",
    )

    cross_kind = build_project(
        {
            "directive.apex": "directive Same {}\n",
            "function.apex": "function Same() : int { return 1 }\n",
        },
        entry="Same",
    )
    require(
        cross_kind.identity_index.find_all("directive", "Same")[0].current_air_id
        == "directive:Same"
        and cross_kind.identity_index.find_all("function", "Same")[0].current_air_id
        == "function:Same",
        "cross-kind equal declared names stopped coexisting",
    )
    duplicate = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a.apex": "module App.A\n\nfunction Same() : int { return 1 }\n",
                "b.apex": "module App.B\n\nfunction Same() : int { return 2 }\n",
            }
        ),
        "duplicate declarations acquired new resolution behavior",
    )
    duplicate_diagnostic = diagnostic_of(duplicate)
    require(
        duplicate_diagnostic.stage == "link"
        and duplicate_diagnostic.code == "APX-LINK-001"
        and duplicate_diagnostic.air_id == "function:Same"
        and duplicate_diagnostic.span.source_name == "a.apex"
        and tuple(span.source_name for span in duplicate_diagnostic.related_spans)
        == ("b.apex",),
        "duplicate declaration phase, diagnostic, or AIR ID changed",
    )

    accepted_visibility()
    legacy_many = build_project(
        {"legacy.apex": "directive First {}\ndirective Second {}\n"},
        entry="First",
    )
    module_many = build_project(
        {
            "module.apex": (
                "module App.Main\n\n"
                "directive First {}\n"
                "directive Second {}\n"
            )
        },
        entry="First",
    )
    require(
        tuple(item.id for item in legacy_many.program.directives)
        == ("directive:First", "directive:Second")
        and tuple(item.id for item in module_many.program.directives)
        == ("directive:First", "directive:Second")
        and tuple(item.order for item in module_many.program.directives)
        == (0, 1)
        and module_many.resolve_entry() == "directive:First",
        "legacy or module-source declaration boundaries changed",
    )
    require(
        not module_many.module_graph.is_legacy
        and module_many.module_graph.source_order() == ("module.apex",)
        and module_many.identity_index.find_all("directive", "First")[0].current_air_id
        == "directive:First"
        and module_many.identity_index.find_all("directive", "Second")[0].current_air_id
        == "directive:Second",
        "module-source ownership or declared identity metadata changed",
    )

    runtime_build = build_project(
        {
            "runtime.apex": (
                "directive Runtime { state count = 1 event done "
                "cause flow { path primary @ 1 { add count 2 emit done } } }\n"
            )
        },
        entry="Runtime",
    )
    runtime_before = air_to_dict(runtime_build.program)
    runtime_build.identity_index.find_all("directive", "Runtime")
    result = runtime_build.execute(
        execution_context(runtime_build, "Runtime"),
        entry="Runtime",
    )
    require(
        result.ok
        and result.final_state.get_int("count") == 3
        and air_to_dict(runtime_build.program) == runtime_before
        and runtime_build.resolve_entry() == "directive:Runtime",
        "metadata inspection changed AIR, entry selection, or runtime behavior",
    )


def test_artifact_cli_tooling_and_temporary_isolation() -> None:
    original_directory = Path.cwd().resolve()
    temporary_path: Path

    with TemporaryDirectory(prefix="apexforge-p11-4b-") as temporary:
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
                    "name": "P11_4B_Declared_Identity",
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
        project = build_project(
            loaded.source_mapping(),
            entry=loaded.manifest.entry,
        )
        before = construct_build_artifact(loaded, project)
        project.identity_index.for_source("src/main.apex")
        project.identity_index.for_module("App.Main")
        project.identity_index.find_all("directive", "Main")
        project.identity_index.find_current_air_id("directive:Main")
        project.identity_index.find_qualified_display_name("App.Main.Main")
        after = construct_build_artifact(loaded, project)
        require(
            before.content == after.content
            and before.fingerprint == after.fingerprint,
            "identity metadata inspection changed artifact v1 bytes or fingerprint",
        )
        artifact = json.loads(after.content.decode("utf-8"))
        forbidden_keys = {
            "identity_index",
            "identities",
            "declared_name",
            "current_air_id",
            "qualified_display_name",
        }
        require(
            PROJECT_MANIFEST_SCHEMA == 1
            and set(artifact) == {"schema", "project", "air", "fingerprint"}
            and artifact["schema"] == "apexforge.build-artifact/v1"
            and forbidden_keys.isdisjoint(recursive_keys(artifact)),
            "manifest or artifact v1 acquired identity metadata",
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
                "ApexForge check passed: P11_4B_Declared_Identity (1 source(s)).\n",
                "",
            )
            and run
            == (
                0,
                "ApexForge run succeeded: P11_4B_Declared_Identity\n"
                "Entry: directive:Main\n"
                "Runtime diagnostics: 0\n",
                "",
            )
            and build_cli[0] == 0
            and build_cli[2] == ""
            and build_cli[1].startswith(
                "ApexForge build succeeded: P11_4B_Declared_Identity\n"
                "Schema: apexforge.build-artifact/v1\n"
                "Entry: directive:Main\n"
                "Sources: 1\nFingerprint: sha256:"
            )
            and build_cli[1].endswith("\nArtifact written.\n")
            and output_path.read_bytes() == before.content,
            "CLI output or artifact bytes changed",
        )

        require(
            verify_frozen_feature_hashes()
            and integration_fingerprint() == CANONICAL_INTEGRATION_SHA256
            == "c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897",
            "language-server code paths changed",
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
            "Visual Studio code paths changed",
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
            "identity_index" not in language_server_text
            and "ProjectIdentityIndex" not in language_server_text
            and "identity_index" not in visual_studio_text
            and "ProjectIdentityIndex" not in visual_studio_text,
            "language-server or Visual Studio tooling consumed identity metadata",
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
    original_directory = Path.cwd().resolve()
    status_before = repository_status()

    def forbidden_network(*_args, **_kwargs):
        raise AssertionError("P11.4B smoke test attempted network access")

    with patch("socket.create_connection", side_effect=forbidden_network), patch(
        "socket.socket", side_effect=forbidden_network
    ):
        test_public_model_validation_order_queries_and_immutability()
        test_collection_determinism_families_and_project_compatibility()
        test_air_generics_collisions_modules_and_runtime_are_unchanged()
        test_artifact_cli_tooling_and_temporary_isolation()

    require(Path.cwd().resolve() == original_directory, "working directory changed")
    require(repository_status() == status_before, "running the smoke test changed repository status")

    print("AFP-P11.4B declared identity metadata smoke test passed.")
    print("Public immutable model, validation, ordering, and read-only queries: PASS")
    print("Deterministic legacy/module collection and declaration families: PASS")
    print("AIR IDs, generics, collisions, modules, entry, and runtime: PASS")
    print("CLI, manifest, artifact v1, language server, and Visual Studio: PASS")
    print("Network, temporary fixture, working-directory, and repository safety: PASS")


if __name__ == "__main__":
    main()
