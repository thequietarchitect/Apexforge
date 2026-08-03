"""Executable contract for P11.4E structured queries and binding outcomes."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from air.serialization import air_to_dict
from language.project import ProjectLinkError, build_project
import language.resolution_queries as query_module
from language.resolution_candidates import ProjectResolutionCandidateIndex
from language.resolution_queries import (
    ProjectAmbiguousResolution,
    ProjectResolutionQuery,
    ProjectResolvedBinding,
    ProjectUnresolvedResolution,
    resolve_project_query,
)
from p11_4d_passive_resolver_candidate_index_smoke_test import (
    candidate_record,
    repository_bytecode_state,
    repository_status,
    test_generics_air_artifact_cli_runtime_and_tooling as accepted_compatibility,
)
from p11_4c_resolver_qualification_architecture_audit_smoke_test import diagnostic_of
from tooling.build_artifact import construct_build_artifact
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


def test_public_models_and_query_validation() -> None:
    require(
        query_module.__all__
        == (
            "ProjectResolutionQuery",
            "ProjectResolvedBinding",
            "ProjectUnresolvedResolution",
            "ProjectAmbiguousResolution",
            "resolve_project_query",
        ),
        "resolution query module exports an unintended public name",
    )
    require(
        tuple(item.name for item in fields(ProjectResolutionQuery))
        == ("kind", "declaration_path", "module_segments")
        and tuple(item.name for item in fields(ProjectResolvedBinding))
        == ("query", "candidate")
        and tuple(item.name for item in fields(ProjectUnresolvedResolution))
        == ("query",)
        and tuple(item.name for item in fields(ProjectAmbiguousResolution))
        == ("query", "candidates"),
        "P11.4E public dataclass fields changed",
    )
    require(
        ProjectResolutionQuery.__dataclass_params__.frozen
        and ProjectResolvedBinding.__dataclass_params__.frozen
        and ProjectUnresolvedResolution.__dataclass_params__.frozen
        and ProjectAmbiguousResolution.__dataclass_params__.frozen,
        "P11.4E public records are mutable",
    )

    unqualified = ProjectResolutionQuery("directive", ["Name"])
    legacy = ProjectResolutionQuery("directive", ["Name"], [])
    module = ProjectResolutionQuery(
        "directive", ["Name"], ["App", "Core"]
    )
    require(
        unqualified.declaration_path == ("Name",)
        and unqualified.module_segments is None
        and legacy.module_segments == ()
        and module.module_segments == ("App", "Core"),
        "query tuple normalization or module modes changed",
    )
    require_raises(
        FrozenInstanceError,
        lambda: setattr(unqualified, "kind", "function"),
        "resolution query is mutable",
    )

    invalid_queries = (
        lambda: ProjectResolutionQuery(None, ("Name",)),
        lambda: ProjectResolutionQuery("workflow", ("Name",)),
        lambda: ProjectResolutionQuery("directive", "Name"),
        lambda: ProjectResolutionQuery("directive", ()),
        lambda: ProjectResolutionQuery("directive", ("One", "Two")),
        lambda: ProjectResolutionQuery("directive", ("bad-name",)),
        lambda: ProjectResolutionQuery("directive", (1,)),
        lambda: ProjectResolutionQuery("directive", ("Name",), "App.Core"),
        lambda: ProjectResolutionQuery(
            "directive", ("Name",), ("App", "", "Core")
        ),
        lambda: ProjectResolutionQuery(
            "directive", ("Name",), ("bad-name",)
        ),
        lambda: ProjectResolutionQuery("directive", ("Name",), (1,)),
    )
    for operation in invalid_queries:
        require_raises(
            (TypeError, ValueError),
            operation,
            "malformed structured query was accepted",
        )


def test_query_modes_outcomes_case_and_display_boundary() -> None:
    legacy = candidate_record("directive", "Name", "legacy.apex", None)
    core = candidate_record("directive", "Name", "core.apex", "App.Core")
    other = candidate_record("directive", "Name", "other.apex", "App.Other")
    function = candidate_record(
        "function", "Name", "function.apex", "App.Core"
    )
    index = ProjectResolutionCandidateIndex((other, function, legacy, core))

    unqualified_query = ProjectResolutionQuery("directive", ("Name",))
    legacy_query = ProjectResolutionQuery("directive", ("Name",), ())
    core_query = ProjectResolutionQuery(
        "directive", ("Name",), ("App", "Core")
    )
    missing_query = ProjectResolutionQuery(
        "directive", ("Name",), ("App", "Missing")
    )
    function_query = ProjectResolutionQuery("function", ("Name",))

    unqualified = resolve_project_query(index, unqualified_query)
    exact_legacy = resolve_project_query(index, legacy_query)
    exact_core = resolve_project_query(index, core_query)
    missing = resolve_project_query(index, missing_query)
    exact_function = resolve_project_query(index, function_query)
    require(
        isinstance(unqualified, ProjectAmbiguousResolution)
        and unqualified.candidates == (legacy, core, other)
        and isinstance(exact_legacy, ProjectResolvedBinding)
        and exact_legacy.candidate is legacy
        and isinstance(exact_core, ProjectResolvedBinding)
        and exact_core.candidate is core
        and isinstance(missing, ProjectUnresolvedResolution)
        and isinstance(exact_function, ProjectResolvedBinding)
        and exact_function.candidate is function,
        "unqualified, legacy, module, or cross-kind outcome changed",
    )
    require(
        isinstance(
            resolve_project_query(
                index,
                ProjectResolutionQuery("directive", ("name",)),
            ),
            ProjectUnresolvedResolution,
        )
        and isinstance(
            resolve_project_query(
                index,
                ProjectResolutionQuery(
                    "directive", ("Name",), ("app", "Core")
                ),
            ),
            ProjectUnresolvedResolution,
        ),
        "query matching stopped being exact-case",
    )
    require_raises(
        ValueError,
        lambda: ProjectResolutionQuery(
            "directive", (core.identity.qualified_display_name,)
        ),
        "qualified display text became a query authority",
    )
    require_raises(
        ValueError,
        lambda: ProjectResolutionQuery("directive", ("Name",), ("App.Core",)),
        "a dotted module source string was accepted",
    )


def test_ambiguity_duplicates_and_direct_validation() -> None:
    legacy = candidate_record("directive", "Same", "legacy.apex", None)
    upper = candidate_record("directive", "Same", "A.apex", "App.Core")
    lower = candidate_record("directive", "Same", "a.apex", "App.Core")
    query = ProjectResolutionQuery("directive", ("Same",))
    duplicate_index = ProjectResolutionCandidateIndex(
        (lower, upper, legacy, upper)
    )
    outcome = resolve_project_query(duplicate_index, query)
    require(
        isinstance(outcome, ProjectAmbiguousResolution)
        and outcome.candidates == (legacy, upper, upper, lower)
        and tuple(item.name for item in fields(ProjectAmbiguousResolution))
        == ("query", "candidates")
        and not hasattr(outcome, "winner")
        and not hasattr(outcome, "candidate"),
        "ambiguity ordering, duplicate retention, or no-winner contract changed",
    )
    direct = ProjectAmbiguousResolution(
        query,
        (lower, legacy, upper, upper),
    )
    require(
        direct.candidates == outcome.candidates,
        "direct ambiguity construction is not canonical or duplicate-capable",
    )

    core_query = ProjectResolutionQuery(
        "directive", ("Same",), ("App", "Core")
    )
    require(
        ProjectResolvedBinding(core_query, upper).candidate is upper,
        "direct matching binding construction changed",
    )
    invalid_results = (
        lambda: ProjectResolvedBinding(object(), upper),
        lambda: ProjectResolvedBinding(core_query, object()),
        lambda: ProjectResolvedBinding(
            ProjectResolutionQuery("directive", ("Same",), ()),
            upper,
        ),
        lambda: ProjectUnresolvedResolution(object()),
        lambda: ProjectAmbiguousResolution(object(), (upper, lower)),
        lambda: ProjectAmbiguousResolution(query, (upper,)),
        lambda: ProjectAmbiguousResolution(query, (upper, object())),
        lambda: ProjectAmbiguousResolution(
            ProjectResolutionQuery("function", ("Same",)),
            (upper, lower),
        ),
    )
    for operation in invalid_results:
        require_raises(
            (TypeError, ValueError),
            operation,
            "inconsistent direct outcome construction was accepted",
        )
    require_raises(
        TypeError,
        lambda: resolve_project_query(object(), query),
        "query function accepted a non-index",
    )
    require_raises(
        TypeError,
        lambda: resolve_project_query(duplicate_index, object()),
        "query function accepted a non-query",
    )


def test_project_entry_duplicates_generics_and_air() -> None:
    project = build_project(
        {
            "directive.apex": "module App.Directive\n\ndirective Same {}\n",
            "function.apex": (
                "module App.Function\n\n"
                "function Same() : int { return 1 }\n"
            ),
        },
        entry="Same",
    )
    before_air = air_to_dict(project.program)
    directive = resolve_project_query(
        project.resolution_candidate_index,
        ProjectResolutionQuery(
            "directive", ("Same",), ("App", "Directive")
        ),
    )
    function = resolve_project_query(
        project.resolution_candidate_index,
        ProjectResolutionQuery("function", ("Same",)),
    )
    require(
        isinstance(directive, ProjectResolvedBinding)
        and directive.candidate.identity.current_air_id == "directive:Same"
        and isinstance(function, ProjectResolvedBinding)
        and function.candidate.identity.current_air_id == "function:Same"
        and project.resolve_entry() == "directive:Same"
        and project.resolve_entry("Same") == "directive:Same"
        and air_to_dict(project.program) == before_air,
        "explicit project query changed entry, cross-kind, or AIR behavior",
    )

    duplicate = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a.apex": "module App.A\n\nfunction Same() : int { return 1 }\n",
                "b.apex": "module App.B\n\nfunction Same() : int { return 2 }\n",
            }
        ),
        "duplicate build exposed a query result or binding",
    )
    item = diagnostic_of(duplicate)
    require(
        item.stage == "link"
        and item.code == "APX-LINK-001"
        and item.air_id == "function:Same",
        "duplicate-link behavior changed",
    )

    generic = build_project(
        {
            "generic.apex": (
                "module Lib.Generic\n\n"
                "function Identity<T : numeric>(value : T) : T { return value }\n"
            ),
            "use.apex": (
                "module App.Use\nimport Lib.Generic\n\n"
                "function Use(value : int) : int { return Identity<int>(value) }\n"
            ),
        }
    )
    generic_air = air_to_dict(generic.program)
    declared = resolve_project_query(
        generic.resolution_candidate_index,
        ProjectResolutionQuery(
            "function", ("Identity",), ("Lib", "Generic")
        ),
    )
    synthetic = resolve_project_query(
        generic.resolution_candidate_index,
        ProjectResolutionQuery(
            "function", ("__apx_spec__Identity__int__",)
        ),
    )
    closure = collect_linked_specializations(generic.program)
    lowered = lower_linked_generics(generic.program)
    require(
        isinstance(declared, ProjectResolvedBinding)
        and declared.candidate.identity.current_air_id == "function:Identity"
        and isinstance(synthetic, ProjectUnresolvedResolution)
        and closure.canonical_ids == lowered.canonical_ids == ("Identity<int>",)
        and lowered.binding_for("Identity<int>").function_id.startswith(
            "function:__apx_spec__Identity__int__"
        )
        and air_to_dict(generic.program) == generic_air,
        "generic query changed declaration, specialization, lowering, or AIR",
    )
    require_raises(
        ValueError,
        lambda: ProjectResolutionQuery("function", ("Identity<int>",)),
        "a specialization key became a declaration query path",
    )


def test_artifact_and_accepted_compatibility() -> None:
    original_directory = Path.cwd().resolve()
    temporary_path: Path
    with TemporaryDirectory(prefix="apexforge-p11-4e-") as temporary:
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
                    "name": "P11_4E_Query",
                    "sources": ["src/main.apex"],
                    "entry": "Main",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        loaded = load_project(temporary_path)
        project = build_project(
            loaded.source_mapping(),
            entry=loaded.manifest.entry,
        )
        before = construct_build_artifact(loaded, project)
        outcome = resolve_project_query(
            project.resolution_candidate_index,
            ProjectResolutionQuery(
                "directive", ("Main",), ("App", "Main")
            ),
        )
        after = construct_build_artifact(loaded, project)
        require(
            isinstance(outcome, ProjectResolvedBinding)
            and before.content == after.content
            and before.fingerprint == after.fingerprint
            and b"ProjectResolutionQuery" not in after.content
            and b"ProjectResolvedBinding" not in after.content,
            "artifact v1 bytes or fingerprint acquired query/binding metadata",
        )
        require(
            Path.cwd().resolve() == original_directory,
            "artifact query fixture changed the working directory",
        )

    require(
        not temporary_path.exists()
        and Path.cwd().resolve() == original_directory,
        "temporary fixture escaped its context manager",
    )
    accepted_compatibility()


def test_exact_production_boundaries_and_no_diagnostics() -> None:
    p11_4e_files = set()
    candidate_files = set()
    for path in PACKAGE_DIRECTORY.rglob("*.py"):
        if path.name.endswith("_smoke_test.py") or "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        if any(
            marker in text
            for marker in (
                "ProjectResolutionQuery",
                "ProjectResolvedBinding",
                "resolve_project_query",
            )
        ):
            p11_4e_files.add(relative)
        if any(
            marker in text
            for marker in (
                "ProjectQualification",
                "ProjectResolutionCandidate",
                "resolution_candidate_index",
            )
        ):
            candidate_files.add(relative)
        require(
            "APX-RESOLVE-" not in text,
            f"production file {path.name} introduced a resolver diagnostic",
        )
    p11_4e_owned = {"apexforge/language/resolution_queries.py"}
    p11_4e_successors = p11_4e_files - p11_4e_owned
    require(
        p11_4e_owned.issubset(p11_4e_files)
        and p11_4e_successors
        == {
            "apexforge/language/resolution_context.py",
            "apexforge/language/resolution_visibility.py",
        },
        "P11.4E ownership or its reviewed successor consumers changed",
    )
    require(
        candidate_files
        == {
            "apexforge/language/resolution_candidates.py",
            "apexforge/language/project.py",
            "apexforge/language/resolution_queries.py",
            "apexforge/language/resolution_context.py",
            "apexforge/language/resolution_visibility.py",
        }
        and candidate_files
        - {
            "apexforge/language/resolution_queries.py",
            "apexforge/language/resolution_context.py",
            "apexforge/language/resolution_visibility.py",
        }
        == {
            "apexforge/language/resolution_candidates.py",
            "apexforge/language/project.py",
        },
        "P11.4D ownership or its reviewed successor consumers changed",
    )
    project_text = (PACKAGE_DIRECTORY / "language" / "project.py").read_text(
        encoding="utf-8"
    )
    require(
        "resolve_project_query" not in project_text
        and "ProjectResolutionQuery" not in project_text
        and "ProjectResolutionContext" not in project_text
        and "collect_project_visibility_evidence" not in project_text
        and "ProjectVisibilityDecision" not in project_text
        and "evaluate_project_visibility" not in project_text
        and "filter_project_visible_candidates" not in project_text,
        "ProjectBuild or ProjectBuilder acquired automatic resolution integration",
    )


def main() -> None:
    original_directory = Path.cwd().resolve()
    status_before = repository_status()
    bytecode_before = repository_bytecode_state()

    def forbidden_network(*_args, **_kwargs):
        raise AssertionError("P11.4E attempted network access")

    with patch("socket.create_connection", side_effect=forbidden_network), patch(
        "socket.socket", side_effect=forbidden_network
    ):
        test_public_models_and_query_validation()
        test_query_modes_outcomes_case_and_display_boundary()
        test_ambiguity_duplicates_and_direct_validation()
        test_project_entry_duplicates_generics_and_air()
        test_artifact_and_accepted_compatibility()
        test_exact_production_boundaries_and_no_diagnostics()

    require(Path.cwd().resolve() == original_directory, "working directory changed")
    require(repository_status() == status_before, "running the test changed Git status")
    require(
        repository_bytecode_state() == bytecode_before,
        "running the test changed repository bytecode state",
    )
    print("AFP-P11.4E structured resolution query and binding smoke test passed.")
    print("Public frozen query and outcome records with exact validation: PASS")
    print("Unqualified, legacy, module, case, and display boundaries: PASS")
    print("Unique, unresolved, and duplicate-capable ambiguous outcomes: PASS")
    print("Project, entry, duplicate-link, generic, AIR, and artifact boundaries: PASS")
    print("CLI, runtime, LSP, VS Code, and Visual Studio compatibility: PASS")
    print("Production boundary, diagnostics, network, Git, and bytecode safety: PASS")


if __name__ == "__main__":
    main()
