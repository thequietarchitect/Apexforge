"""Executable contract for P11.4H contextual outcome classification."""

from __future__ import annotations

import ast
from dataclasses import fields
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from air.serialization import air_to_dict
from language.project import ProjectLinkError, build_project
from language.resolution_candidates import (
    ProjectResolutionCandidate,
    ProjectResolutionCandidateIndex,
)
from language.resolution_context import ProjectResolutionContext
import language.resolution_outcomes as outcome_module
from language.resolution_outcomes import resolve_project_contextual_query
from language.resolution_queries import (
    ProjectAmbiguousResolution,
    ProjectResolutionQuery,
    ProjectResolvedBinding,
    ProjectUnresolvedResolution,
    resolve_project_query,
)
from language.resolution_visibility import filter_project_visible_candidates
from p11_4c_resolver_qualification_architecture_audit_smoke_test import diagnostic_of
from p11_4d_passive_resolver_candidate_index_smoke_test import (
    candidate_record,
    repository_bytecode_state,
    repository_status,
)
from p11_4g_visibility_policy_contextual_candidate_filtering_smoke_test import (
    test_project_generics_air_artifact_and_compatibility as accepted_compatibility,
)
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


def test_public_api_and_mandatory_reuse() -> None:
    require(
        outcome_module.__all__ == ("resolve_project_contextual_query",),
        "contextual outcome module exports an unintended public name",
    )
    source = (
        PACKAGE_DIRECTORY / "language" / "resolution_outcomes.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    public_classes = {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    }
    public_assignments = set()
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and not target.id.startswith("_"):
                public_assignments.add(target.id)
    require(
        public_functions == {"resolve_project_contextual_query"}
        and not public_classes
        and not public_assignments,
        "P11.4H defines an extra function, class, alias, or constant",
    )
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    call_names = [
        node.func.id for node in calls if isinstance(node.func, ast.Name)
    ]
    require(
        call_names.count("filter_project_visible_candidates") == 1
        and call_names.count("ProjectResolutionCandidateIndex") == 1
        and call_names.count("resolve_project_query") == 1,
        "mandatory filter/index/classifier architecture changed",
    )
    forbidden_constructors = {
        "ProjectUnresolvedResolution",
        "ProjectResolvedBinding",
        "ProjectAmbiguousResolution",
    }
    require(
        forbidden_constructors.isdisjoint(call_names),
        "P11.4H directly constructs a frozen outcome",
    )
    require(
        "_candidate_matches_query" not in source
        and "same_source" not in source
        and "same_module" not in source
        and "imported_module" not in source
        and "legacy_context" not in source
        and "visibility_basis" not in source,
        "P11.4H copied query matching or visibility policy",
    )

    candidate = candidate_record(
        "directive", "Name", "main.apex", "App.Main"
    )
    index = ProjectResolutionCandidateIndex((candidate,))
    query = ProjectResolutionQuery("directive", ("Name",))
    context = ProjectResolutionContext("main.apex", ("App", "Main"))
    sentinel = object()
    filter_calls = []
    resolution_calls = []

    def fake_filter(received_index, received_query, received_context):
        filter_calls.append((received_index, received_query, received_context))
        return (candidate, candidate)

    def fake_resolve(received_index, received_query):
        resolution_calls.append((received_index, received_query))
        return sentinel

    with patch.object(
        outcome_module,
        "filter_project_visible_candidates",
        side_effect=fake_filter,
    ), patch.object(
        outcome_module,
        "resolve_project_query",
        side_effect=fake_resolve,
    ):
        result = resolve_project_contextual_query(index, query, context)

    require(
        result is sentinel
        and filter_calls == [(index, query, context)]
        and len(resolution_calls) == 1
        and type(resolution_calls[0][0]) is ProjectResolutionCandidateIndex
        and resolution_calls[0][0].candidates == (candidate, candidate)
        and resolution_calls[0][1] is query,
        "P11.4H did not preserve exact inputs, filtered tuple, or query identity",
    )


def test_input_validation() -> None:
    candidate = candidate_record(
        "directive", "Name", "main.apex", "App.Main"
    )
    index = ProjectResolutionCandidateIndex((candidate,))
    query = ProjectResolutionQuery("directive", ("Name",))
    context = ProjectResolutionContext("main.apex", ("App", "Main"))
    with patch.object(outcome_module, "filter_project_visible_candidates") as call:
        invalid = (
            lambda: resolve_project_contextual_query(object(), query, context),
            lambda: resolve_project_contextual_query(index, object(), context),
            lambda: resolve_project_contextual_query(index, query, object()),
        )
        for operation in invalid:
            require_raises(
                TypeError,
                operation,
                "contextual classifier accepted an invalid input",
            )
        require(
            call.call_count == 0,
            "invalid contextual inputs reached filtering",
        )


def test_classification_order_duplicates_and_query_modes() -> None:
    legacy = candidate_record("directive", "Name", "legacy.apex", None)
    current = candidate_record(
        "directive", "Name", "current.apex", "App.Main"
    )
    imported = candidate_record(
        "directive", "Name", "lib.apex", "Lib.Core"
    )
    unrelated = candidate_record(
        "directive", "Name", "other.apex", "Other.Hidden"
    )
    same_source = candidate_record(
        "directive", "Name", "caller.apex", "Zed.Remote"
    )
    function = candidate_record(
        "function", "Name", "function.apex", "App.Main"
    )
    context = ProjectResolutionContext(
        "caller.apex",
        ("App", "Main"),
        (("Lib", "Core"),),
    )
    query = ProjectResolutionQuery("directive", ("Name",))

    no_match_query = ProjectResolutionQuery("directive", ("Missing",))
    no_match = resolve_project_contextual_query(
        ProjectResolutionCandidateIndex((current,)),
        no_match_query,
        context,
    )
    invisible = resolve_project_contextual_query(
        ProjectResolutionCandidateIndex((legacy,)), query, context
    )
    raw_zero_index = ProjectResolutionCandidateIndex((legacy, unrelated))
    reduced_zero = resolve_project_contextual_query(
        raw_zero_index, query, context
    )
    raw_one_index = ProjectResolutionCandidateIndex((current, unrelated))
    reduced_one = resolve_project_contextual_query(raw_one_index, query, context)
    raw_many_index = ProjectResolutionCandidateIndex(
        (same_source, unrelated, imported, current, legacy)
    )
    filtered_many = filter_project_visible_candidates(
        raw_many_index, query, context
    )
    remains_many = resolve_project_contextual_query(
        raw_many_index, query, context
    )

    require(
        isinstance(no_match, ProjectUnresolvedResolution)
        and no_match.query is no_match_query
        and isinstance(invisible, ProjectUnresolvedResolution)
        and invisible.query is query
        and isinstance(reduced_zero, ProjectUnresolvedResolution)
        and tuple(item.name for item in fields(ProjectUnresolvedResolution))
        == ("query",),
        "zero-match and zero-visible unresolved classification diverged",
    )
    require(
        isinstance(resolve_project_query(raw_zero_index, query), ProjectAmbiguousResolution)
        and isinstance(reduced_zero, ProjectUnresolvedResolution)
        and isinstance(resolve_project_query(raw_one_index, query), ProjectAmbiguousResolution)
        and isinstance(reduced_one, ProjectResolvedBinding)
        and reduced_one.query is query
        and reduced_one.candidate is current,
        "raw ambiguity did not reduce to zero or one by visible tuple count",
    )
    require(
        filtered_many == (current, imported, same_source)
        and isinstance(remains_many, ProjectAmbiguousResolution)
        and remains_many.query is query
        and remains_many.candidates == filtered_many,
        "multiple visible candidates changed order or ambiguity contents",
    )

    duplicate_index = ProjectResolutionCandidateIndex((current, current, unrelated))
    filtered_duplicates = filter_project_visible_candidates(
        duplicate_index, query, context
    )
    duplicate_outcome = resolve_project_contextual_query(
        duplicate_index, query, context
    )
    require(
        filtered_duplicates == (current, current)
        and isinstance(duplicate_outcome, ProjectAmbiguousResolution)
        and duplicate_outcome.candidates == filtered_duplicates
        and duplicate_outcome.candidates[0] is duplicate_outcome.candidates[1],
        "duplicate visible candidates collapsed before ambiguity classification",
    )

    legacy_query = ProjectResolutionQuery("directive", ("Name",), ())
    legacy_context = ProjectResolutionContext("caller.apex", ())
    exact_legacy = resolve_project_contextual_query(
        ProjectResolutionCandidateIndex((legacy, current)),
        legacy_query,
        legacy_context,
    )
    hidden_legacy = resolve_project_contextual_query(
        ProjectResolutionCandidateIndex((legacy, current)),
        legacy_query,
        context,
    )
    module_query = ProjectResolutionQuery(
        "directive", ("Name",), ("Lib", "Core")
    )
    exact_module = resolve_project_contextual_query(
        raw_many_index, module_query, context
    )
    hidden_module = resolve_project_contextual_query(
        ProjectResolutionCandidateIndex((unrelated,)),
        ProjectResolutionQuery(
            "directive", ("Name",), ("Other", "Hidden")
        ),
        context,
    )
    function_outcome = resolve_project_contextual_query(
        ProjectResolutionCandidateIndex((current, function)),
        ProjectResolutionQuery("function", ("Name",)),
        ProjectResolutionContext("function.apex", ("App", "Main")),
    )
    require(
        isinstance(exact_legacy, ProjectResolvedBinding)
        and exact_legacy.candidate is legacy
        and isinstance(hidden_legacy, ProjectUnresolvedResolution)
        and isinstance(exact_module, ProjectResolvedBinding)
        and exact_module.candidate is imported
        and isinstance(hidden_module, ProjectUnresolvedResolution)
        and isinstance(function_outcome, ProjectResolvedBinding)
        and function_outcome.candidate is function,
        "legacy, module, visibility, or kind query reuse changed",
    )
    require(
        isinstance(
            resolve_project_contextual_query(
                raw_many_index,
                ProjectResolutionQuery("directive", ("name",)),
                context,
            ),
            ProjectUnresolvedResolution,
        )
        and isinstance(
            resolve_project_contextual_query(
                raw_many_index,
                ProjectResolutionQuery(
                    "directive", ("Name",), ("lib", "Core")
                ),
                context,
            ),
            ProjectUnresolvedResolution,
        ),
        "exact spelling or case query semantics changed",
    )

    outcome_types = (
        ProjectUnresolvedResolution,
        ProjectResolvedBinding,
        ProjectAmbiguousResolution,
    )
    for outcome in (
        no_match,
        invisible,
        reduced_zero,
        reduced_one,
        remains_many,
        duplicate_outcome,
        exact_legacy,
        hidden_legacy,
        exact_module,
        hidden_module,
        function_outcome,
    ):
        require(
            type(outcome) in outcome_types,
            "contextual classification returned a new outcome type",
        )
        outcome_fields = {item.name for item in fields(type(outcome))}
        require(
            outcome_fields.isdisjoint(
                {
                    "context",
                    "evidence",
                    "visibility",
                    "visibility_basis",
                    "accessible",
                    "selected",
                    "winner",
                    "rank",
                    "priority",
                    "precedence",
                    "score",
                    "weight",
                    "reason",
                    "hidden_candidates",
                }
            ),
            "a frozen outcome acquired contextual or policy metadata",
        )


def test_project_generics_air_artifact_and_compatibility() -> None:
    project = build_project(
        {
            "main.apex": "module App.Main\n\ndirective Main {}\n",
            "function.apex": (
                "module App.Function\n\n"
                "function Main() : int { return 1 }\n"
            ),
            "generic.apex": (
                "module Lib.Generic\n\n"
                "function Identity<T : numeric>(value : T) : T { return value }\n"
            ),
            "use.apex": (
                "module App.Use\nimport Lib.Generic\n\n"
                "function Use(value : int) : int { return Identity<int>(value) }\n"
            ),
        },
        entry="Main",
    )
    before_air = air_to_dict(project.program)
    directive_query = ProjectResolutionQuery("directive", ("Main",))
    directive = resolve_project_contextual_query(
        project.resolution_candidate_index,
        directive_query,
        ProjectResolutionContext("main.apex", ("App", "Main")),
    )
    function = resolve_project_contextual_query(
        project.resolution_candidate_index,
        ProjectResolutionQuery("function", ("Main",)),
        ProjectResolutionContext("function.apex", ("App", "Function")),
    )
    generic = resolve_project_contextual_query(
        project.resolution_candidate_index,
        ProjectResolutionQuery(
            "function", ("Identity",), ("Lib", "Generic")
        ),
        ProjectResolutionContext(
            "use.apex", ("App", "Use"), (("Lib", "Generic"),)
        ),
    )
    synthetic = resolve_project_contextual_query(
        project.resolution_candidate_index,
        ProjectResolutionQuery(
            "function", ("__apx_spec__Identity__int__",)
        ),
        ProjectResolutionContext("use.apex", ("App", "Use")),
    )
    closure = collect_linked_specializations(project.program)
    lowered = lower_linked_generics(project.program)
    require(
        isinstance(directive, ProjectResolvedBinding)
        and directive.query is directive_query
        and directive.candidate.identity.kind == "directive"
        and isinstance(function, ProjectResolvedBinding)
        and function.candidate.identity.kind == "function"
        and isinstance(generic, ProjectResolvedBinding)
        and generic.candidate.identity.current_air_id == "function:Identity"
        and isinstance(synthetic, ProjectUnresolvedResolution)
        and closure.canonical_ids == lowered.canonical_ids == ("Identity<int>",)
        and lowered.binding_for("Identity<int>").function_id.startswith(
            "function:__apx_spec__Identity__int__"
        )
        and project.resolve_entry() == "directive:Main"
        and project.resolve_entry("Main") == "directive:Main"
        and air_to_dict(project.program) == before_air,
        "project, entry, cross-kind, generic, lowering, or AIR changed",
    )

    duplicate = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a.apex": "module App.A\n\nfunction Same() : int { return 1 }\n",
                "b.apex": "module App.B\n\nfunction Same() : int { return 2 }\n",
            }
        ),
        "duplicate build exposed a contextual outcome",
    )
    item = diagnostic_of(duplicate)
    require(
        item.stage == "link"
        and item.code == "APX-LINK-001"
        and item.air_id == "function:Same",
        "duplicate-link behavior changed",
    )

    original_directory = Path.cwd().resolve()
    temporary_path: Path
    with TemporaryDirectory(prefix="apexforge-p11-4h-") as temporary:
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
            "module App.Main\n\ndirective Main {}\n", encoding="utf-8"
        )
        (temporary_path / "apexforge.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "name": "P11_4H_Outcomes",
                    "sources": ["src/main.apex"],
                    "entry": "Main",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        loaded = load_project(temporary_path)
        loaded_project = build_project(
            loaded.source_mapping(), entry=loaded.manifest.entry
        )
        before = construct_build_artifact(loaded, loaded_project)
        outcome = resolve_project_contextual_query(
            loaded_project.resolution_candidate_index,
            ProjectResolutionQuery("directive", ("Main",)),
            ProjectResolutionContext("src/main.apex", ("App", "Main")),
        )
        after = construct_build_artifact(loaded, loaded_project)
        require(
            isinstance(outcome, ProjectResolvedBinding)
            and before.content == after.content
            and before.fingerprint == after.fingerprint
            and b"resolve_project_contextual_query" not in after.content,
            "artifact v1 acquired contextual outcome metadata",
        )
        require(
            Path.cwd().resolve() == original_directory,
            "artifact outcome fixture changed the working directory",
        )
    require(
        not temporary_path.exists()
        and Path.cwd().resolve() == original_directory,
        "temporary fixture escaped its context manager",
    )

    accepted_compatibility()


def test_exact_production_boundaries_and_no_diagnostics() -> None:
    p11_4h_files = set()
    p11_4g_contract_files = set()
    p11_4f_contract_files = set()
    p11_4e_contract_files = set()
    candidate_files = set()
    for path in PACKAGE_DIRECTORY.rglob("*.py"):
        if path.name.endswith("_smoke_test.py") or "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        if "resolve_project_contextual_query" in text:
            p11_4h_files.add(relative)
        if any(
            marker in text
            for marker in (
                "ProjectVisibilityDecision",
                "evaluate_project_visibility",
                "filter_project_visible_candidates",
            )
        ):
            p11_4g_contract_files.add(relative)
        if any(
            marker in text
            for marker in (
                "ProjectResolutionContext",
                "ProjectVisibilityEvidence",
                "collect_project_visibility_evidence",
            )
        ):
            p11_4f_contract_files.add(relative)
        if any(
            marker in text
            for marker in (
                "ProjectResolutionQuery",
                "ProjectResolvedBinding",
                "resolve_project_query",
            )
        ):
            p11_4e_contract_files.add(relative)
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

    outcome_path = "apexforge/language/resolution_outcomes.py"
    visibility_path = "apexforge/language/resolution_visibility.py"
    context_path = "apexforge/language/resolution_context.py"
    query_path = "apexforge/language/resolution_queries.py"
    p11_4d_owned = {
        "apexforge/language/resolution_candidates.py",
        "apexforge/language/project.py",
    }
    expected_candidates = p11_4d_owned | {
        query_path,
        context_path,
        visibility_path,
        outcome_path,
    }
    require(
        p11_4h_files == {outcome_path},
        "P11.4H acquired another production file",
    )
    require(
        p11_4g_contract_files == {visibility_path, outcome_path}
        and p11_4g_contract_files - {outcome_path} == {visibility_path},
        "P11.4G ownership or its one P11.4H consumer changed",
    )
    require(
        p11_4f_contract_files == {context_path, visibility_path, outcome_path}
        and p11_4f_contract_files - {visibility_path, outcome_path}
        == {context_path},
        "P11.4F ownership or reviewed consumers changed",
    )
    require(
        p11_4e_contract_files
        == {query_path, context_path, visibility_path, outcome_path}
        and p11_4e_contract_files - {context_path, visibility_path, outcome_path}
        == {query_path},
        "P11.4E ownership or reviewed consumers changed",
    )
    require(
        candidate_files == expected_candidates
        and candidate_files
        - {query_path, context_path, visibility_path, outcome_path}
        == p11_4d_owned,
        "candidate-model ownership or reviewed consumer set changed",
    )
    project_text = (PACKAGE_DIRECTORY / "language" / "project.py").read_text(
        encoding="utf-8"
    )
    require(
        "resolve_project_contextual_query" not in project_text
        and "filter_project_visible_candidates" not in project_text
        and "ProjectResolutionContext" not in project_text,
        "ProjectBuild or ProjectBuilder acquired contextual resolution",
    )


def main() -> None:
    original_directory = Path.cwd().resolve()
    status_before = repository_status()
    bytecode_before = repository_bytecode_state()

    def forbidden_network(*_args, **_kwargs):
        raise AssertionError("P11.4H attempted network access")

    with patch("socket.create_connection", side_effect=forbidden_network), patch(
        "socket.socket", side_effect=forbidden_network
    ):
        test_public_api_and_mandatory_reuse()
        test_input_validation()
        test_classification_order_duplicates_and_query_modes()
        test_project_generics_air_artifact_and_compatibility()
        test_exact_production_boundaries_and_no_diagnostics()

    require(Path.cwd().resolve() == original_directory, "working directory changed")
    require(repository_status() == status_before, "running the test changed Git status")
    require(
        repository_bytecode_state() == bytecode_before,
        "running the test changed repository bytecode state",
    )
    print("AFP-P11.4H contextual outcome classification smoke test passed.")
    print("Exact one-function API and mandatory frozen-operation reuse: PASS")
    print("Input validation and no direct outcome construction: PASS")
    print("Unresolved, resolved, ambiguous, order, and duplicates: PASS")
    print("Query modes, exact query identity, and frozen outcomes: PASS")
    print("Project, entry, duplicate-link, generic, AIR, and artifact: PASS")
    print("CLI, runtime, LSP, VS Code, and Visual Studio compatibility: PASS")
    print("Production boundaries, diagnostics, network, Git, and bytecode: PASS")


if __name__ == "__main__":
    main()
