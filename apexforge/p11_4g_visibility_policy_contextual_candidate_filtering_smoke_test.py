"""Executable contract for P11.4G fixed visibility and candidate filtering."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
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
from language.resolution_context import (
    ProjectResolutionContext,
    ProjectVisibilityEvidence,
    collect_project_visibility_evidence,
)
from language.resolution_queries import (
    ProjectAmbiguousResolution,
    ProjectResolutionQuery,
    ProjectResolvedBinding,
    ProjectUnresolvedResolution,
)
import language.resolution_visibility as visibility_module
from language.resolution_visibility import (
    ProjectVisibilityDecision,
    evaluate_project_visibility,
    filter_project_visible_candidates,
)
from p11_4c_resolver_qualification_architecture_audit_smoke_test import diagnostic_of
from p11_4d_passive_resolver_candidate_index_smoke_test import (
    candidate_record,
    repository_bytecode_state,
    repository_status,
)
from p11_4f_resolution_context_visibility_evidence_smoke_test import (
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


def evidence_for(
    candidate: ProjectResolutionCandidate,
    context: ProjectResolutionContext,
) -> ProjectVisibilityEvidence:
    query = ProjectResolutionQuery(
        candidate.qualification.kind,
        candidate.qualification.declaration_path,
    )
    records = collect_project_visibility_evidence(
        ProjectResolutionCandidateIndex((candidate,)),
        query,
        context,
    )
    require(len(records) == 1, "evidence helper did not retain its candidate")
    return records[0]


def test_public_model_and_fixed_policy_surface() -> None:
    require(
        visibility_module.__all__
        == (
            "ProjectVisibilityDecision",
            "evaluate_project_visibility",
            "filter_project_visible_candidates",
        ),
        "visibility module exports an unintended public name",
    )
    require(
        tuple(item.name for item in fields(ProjectVisibilityDecision))
        == ("evidence", "visible", "visibility_basis"),
        "visibility decision fields changed",
    )
    require(
        ProjectVisibilityDecision.__dataclass_params__.frozen,
        "visibility decision is mutable",
    )
    source = (
        PACKAGE_DIRECTORY / "language" / "resolution_visibility.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    public_definitions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef))
        and not node.name.startswith("_")
    }
    class_definitions = {
        node.name for node in tree.body if isinstance(node, ast.ClassDef)
    }
    require(
        public_definitions == set(visibility_module.__all__)
        and class_definitions == {"ProjectVisibilityDecision"},
        "P11.4G defines an extra API or configurable policy class",
    )
    require(
        visibility_module._VISIBILITY_BASIS_ORDER
        == (
            "same_source",
            "same_module",
            "imported_module",
            "legacy_context",
        )
        and "_VISIBILITY_BASIS_ORDER" not in visibility_module.__all__,
        "visibility vocabulary, canonical order, or private boundary changed",
    )


def test_basis_derivation_and_overlap() -> None:
    module_context = ProjectResolutionContext(
        "src/main.apex",
        ("App", "Main"),
        (("App", "Main"), ("Lib", "Core")),
    )
    legacy_context = ProjectResolutionContext("caller.apex", ())

    unrelated = evidence_for(
        candidate_record("directive", "Name", "other.apex", "Other.Core"),
        module_context,
    )
    same_source = evidence_for(
        candidate_record("directive", "Name", "src/main.apex", "Other.Core"),
        module_context,
    )
    same_module = evidence_for(
        candidate_record("directive", "Name", "other.apex", "App.Main"),
        ProjectResolutionContext("src/main.apex", ("App", "Main")),
    )
    imported = evidence_for(
        candidate_record("directive", "Name", "lib.apex", "Lib.Core"),
        module_context,
    )
    remote_legacy_from_legacy = evidence_for(
        candidate_record("directive", "Name", "legacy.apex", None),
        legacy_context,
    )
    remote_legacy_from_module = evidence_for(
        candidate_record("directive", "Name", "legacy.apex", None),
        module_context,
    )
    local_legacy_from_module = evidence_for(
        candidate_record("directive", "Name", "src/main.apex", None),
        module_context,
    )
    overlapping_module = evidence_for(
        candidate_record("directive", "Name", "src/main.apex", "App.Main"),
        module_context,
    )
    overlapping_legacy = evidence_for(
        candidate_record("directive", "Name", "caller.apex", None),
        legacy_context,
    )

    examples = (
        (unrelated, False, ()),
        (same_source, True, ("same_source",)),
        (same_module, True, ("same_module",)),
        (imported, True, ("imported_module",)),
        (remote_legacy_from_legacy, True, ("legacy_context",)),
        (remote_legacy_from_module, False, ()),
        (local_legacy_from_module, True, ("same_source",)),
        (
            overlapping_module,
            True,
            ("same_source", "same_module", "imported_module"),
        ),
        (
            overlapping_legacy,
            True,
            ("same_source", "legacy_context"),
        ),
    )
    observed_tokens = set()
    for evidence, expected_visible, expected_basis in examples:
        snapshot = (
            evidence.query,
            evidence.context,
            evidence.candidate,
            evidence.same_source,
            evidence.same_module,
            evidence.imported_module,
            evidence.legacy_candidate,
        )
        decision = evaluate_project_visibility(evidence)
        observed_tokens.update(decision.visibility_basis)
        require(
            decision.evidence is evidence
            and decision.visible is expected_visible
            and decision.visibility_basis == expected_basis
            and decision.visible == bool(decision.visibility_basis)
            and snapshot
            == (
                evidence.query,
                evidence.context,
                evidence.candidate,
                evidence.same_source,
                evidence.same_module,
                evidence.imported_module,
                evidence.legacy_candidate,
            ),
            "fixed visibility derivation or evidence immutability changed",
        )
    require(
        observed_tokens
        == {"same_source", "same_module", "imported_module", "legacy_context"},
        "visibility evaluation did not expose the exact frozen vocabulary",
    )
    banned = {
        "accessible",
        "selected",
        "winner",
        "rank",
        "priority",
        "precedence",
        "score",
        "weight",
    }
    require(
        banned.isdisjoint(item.name for item in fields(ProjectVisibilityDecision)),
        "visibility decision acquired ranking, precedence, or selection state",
    )


def test_decision_validation() -> None:
    context = ProjectResolutionContext(
        "src/main.apex",
        ("App", "Main"),
        (("App", "Main"),),
    )
    evidence = evidence_for(
        candidate_record("directive", "Name", "src/main.apex", "App.Main"),
        context,
    )
    expected = ("same_source", "same_module", "imported_module")
    valid = ProjectVisibilityDecision(evidence, True, list(expected))
    require(
        valid.visible
        and valid.visibility_basis == expected
        and isinstance(valid.visibility_basis, tuple),
        "valid direct decision did not normalize its basis tuple",
    )
    require_raises(
        FrozenInstanceError,
        lambda: setattr(valid, "visible", False),
        "visibility decision is mutable",
    )
    invalid = (
        lambda: ProjectVisibilityDecision(object(), True, expected),
        lambda: ProjectVisibilityDecision(evidence, 1, expected),
        lambda: ProjectVisibilityDecision(evidence, True, "same_source"),
        lambda: ProjectVisibilityDecision(evidence, True, b"same_source"),
        lambda: ProjectVisibilityDecision(evidence, True, (1,)),
        lambda: ProjectVisibilityDecision(evidence, True, ("implicit",)),
        lambda: ProjectVisibilityDecision(
            evidence, True, ("same_source", "same_source")
        ),
        lambda: ProjectVisibilityDecision(
            evidence,
            True,
            ("imported_module", "same_module", "same_source"),
        ),
        lambda: ProjectVisibilityDecision(
            evidence, True, ("same_source", "same_module")
        ),
        lambda: ProjectVisibilityDecision(
            evidence,
            True,
            ("same_source", "same_module", "imported_module", "legacy_context"),
        ),
        lambda: ProjectVisibilityDecision(evidence, False, expected),
    )
    for operation in invalid:
        require_raises(
            (TypeError, ValueError),
            operation,
            "inconsistent direct visibility decision was accepted",
        )
    unrelated = evidence_for(
        candidate_record("directive", "Name", "other.apex", "Other.Core"),
        context,
    )
    require_raises(
        ValueError,
        lambda: ProjectVisibilityDecision(unrelated, True, ()),
        "unrelated evidence was marked visible",
    )
    require_raises(
        TypeError,
        lambda: evaluate_project_visibility(object()),
        "visibility evaluator accepted a non-evidence value",
    )


def test_contextual_filtering_and_query_modes() -> None:
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
    index = ProjectResolutionCandidateIndex(
        (same_source, unrelated, imported, function, current, legacy)
    )
    context = ProjectResolutionContext(
        "caller.apex",
        ("App", "Main"),
        (("Lib", "Core"),),
    )
    query = ProjectResolutionQuery("directive", ("Name",))
    visible = filter_project_visible_candidates(index, query, context)
    require(
        visible == (current, imported, same_source)
        and type(visible) is tuple
        and all(type(item) is ProjectResolutionCandidate for item in visible)
        and not any(
            isinstance(
                item,
                (
                    ProjectVisibilityDecision,
                    ProjectResolvedBinding,
                    ProjectUnresolvedResolution,
                    ProjectAmbiguousResolution,
                ),
            )
            for item in visible
        ),
        "filtering changed canonical order or returned policy/outcome records",
    )
    require_raises(
        TypeError,
        lambda: filter_project_visible_candidates(object(), query, context),
        "filter accepted a non-index",
    )
    require_raises(
        TypeError,
        lambda: filter_project_visible_candidates(index, object(), context),
        "filter accepted a non-query",
    )
    require_raises(
        TypeError,
        lambda: filter_project_visible_candidates(index, query, object()),
        "filter accepted a non-context",
    )
    require(
        filter_project_visible_candidates(
            index,
            ProjectResolutionQuery("directive", ("Missing",)),
            context,
        )
        == (),
        "zero query matches did not filter to an empty tuple",
    )

    invisible_index = ProjectResolutionCandidateIndex((legacy, unrelated))
    require(
        filter_project_visible_candidates(invisible_index, query, context) == (),
        "query matches with zero visible candidates were retained",
    )
    one_visible = filter_project_visible_candidates(
        ProjectResolutionCandidateIndex((current, unrelated)), query, context
    )
    require(
        one_visible == (current,)
        and type(one_visible) is tuple
        and not isinstance(one_visible, ProjectResolvedBinding),
        "one visible candidate became a winner or binding",
    )
    duplicate_index = ProjectResolutionCandidateIndex(
        (unrelated, current, unrelated, current)
    )
    require(
        filter_project_visible_candidates(duplicate_index, query, context)
        == (current, current),
        "visible duplicates collapsed or invisible duplicates affected ordering",
    )

    legacy_query = ProjectResolutionQuery("directive", ("Name",), ())
    legacy_context = ProjectResolutionContext("caller.apex", ())
    require(
        filter_project_visible_candidates(index, legacy_query, legacy_context)
        == (legacy,)
        and filter_project_visible_candidates(index, legacy_query, context) == (),
        "exact legacy matching or legacy-context policy changed",
    )
    local_legacy_context = ProjectResolutionContext(
        "legacy.apex", ("App", "Main")
    )
    require(
        filter_project_visible_candidates(
            index, legacy_query, local_legacy_context
        )
        == (legacy,),
        "same-source legacy candidate was hidden in a module context",
    )
    exact_module = filter_project_visible_candidates(
        index,
        ProjectResolutionQuery(
            "directive", ("Name",), ("Lib", "Core")
        ),
        context,
    )
    exact_function = filter_project_visible_candidates(
        index,
        ProjectResolutionQuery("function", ("Name",)),
        context,
    )
    require(
        exact_module == (imported,)
        and exact_function == (function,)
        and filter_project_visible_candidates(
            index,
            ProjectResolutionQuery(
                "directive", ("Name",), ("lib", "Core")
            ),
            context,
        )
        == ()
        and filter_project_visible_candidates(
            index,
            ProjectResolutionQuery("directive", ("name",)),
            context,
        )
        == (),
        "module, kind, spelling, or exact-case query reuse changed",
    )
    require(
        len(collect_project_visibility_evidence(index, query, context)) == 5
        and len(visible) == 3
        and len(one_visible) == 1
        and filter_project_visible_candidates(invisible_index, query, context)
        == (),
        "ambiguous match sets did not reduce factually to zero, one, or many",
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
    directive = filter_project_visible_candidates(
        project.resolution_candidate_index,
        ProjectResolutionQuery("directive", ("Main",)),
        ProjectResolutionContext("main.apex", ("App", "Main")),
    )
    function = filter_project_visible_candidates(
        project.resolution_candidate_index,
        ProjectResolutionQuery("function", ("Main",)),
        ProjectResolutionContext("function.apex", ("App", "Function")),
    )
    generic = filter_project_visible_candidates(
        project.resolution_candidate_index,
        ProjectResolutionQuery(
            "function", ("Identity",), ("Lib", "Generic")
        ),
        ProjectResolutionContext(
            "use.apex", ("App", "Use"), (("Lib", "Generic"),)
        ),
    )
    synthetic = filter_project_visible_candidates(
        project.resolution_candidate_index,
        ProjectResolutionQuery(
            "function", ("__apx_spec__Identity__int__",)
        ),
        ProjectResolutionContext("use.apex", ("App", "Use")),
    )
    closure = collect_linked_specializations(project.program)
    lowered = lower_linked_generics(project.program)
    require(
        len(directive) == len(function) == len(generic) == 1
        and directive[0].identity.kind == "directive"
        and function[0].identity.kind == "function"
        and generic[0].identity.current_air_id == "function:Identity"
        and synthetic == ()
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
        "duplicate build exposed a filtered candidate tuple",
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
    with TemporaryDirectory(prefix="apexforge-p11-4g-") as temporary:
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
                    "name": "P11_4G_Visibility",
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
        filtered = filter_project_visible_candidates(
            loaded_project.resolution_candidate_index,
            ProjectResolutionQuery("directive", ("Main",)),
            ProjectResolutionContext("src/main.apex", ("App", "Main")),
        )
        decision = evaluate_project_visibility(
            collect_project_visibility_evidence(
                loaded_project.resolution_candidate_index,
                ProjectResolutionQuery("directive", ("Main",)),
                ProjectResolutionContext("src/main.apex", ("App", "Main")),
            )[0]
        )
        after = construct_build_artifact(loaded, loaded_project)
        require(
            len(filtered) == 1
            and decision.visible
            and before.content == after.content
            and before.fingerprint == after.fingerprint
            and b"ProjectVisibilityDecision" not in after.content,
            "artifact v1 acquired visibility policy metadata",
        )
        require(
            Path.cwd().resolve() == original_directory,
            "artifact visibility fixture changed the working directory",
        )
    require(
        not temporary_path.exists()
        and Path.cwd().resolve() == original_directory,
        "temporary fixture escaped its context manager",
    )

    accepted_compatibility()


def test_exact_production_boundaries_and_no_diagnostics() -> None:
    p11_4g_files = set()
    p11_4f_contract_files = set()
    p11_4e_contract_files = set()
    candidate_files = set()
    for path in PACKAGE_DIRECTORY.rglob("*.py"):
        if path.name.endswith("_smoke_test.py") or "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        if any(
            marker in text
            for marker in (
                "ProjectVisibilityDecision",
                "evaluate_project_visibility",
                "filter_project_visible_candidates",
            )
        ):
            p11_4g_files.add(relative)
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

    visibility_path = "apexforge/language/resolution_visibility.py"
    context_path = "apexforge/language/resolution_context.py"
    query_path = "apexforge/language/resolution_queries.py"
    p11_4d_owned = {
        "apexforge/language/resolution_candidates.py",
        "apexforge/language/project.py",
    }
    expected_candidate_files = p11_4d_owned | {
        query_path,
        context_path,
        visibility_path,
    }
    require(
        p11_4g_files == {visibility_path},
        "P11.4G acquired another production file",
    )
    require(
        p11_4f_contract_files == {context_path, visibility_path}
        and p11_4f_contract_files - {visibility_path} == {context_path},
        "P11.4F ownership or its single P11.4G consumer changed",
    )
    require(
        p11_4e_contract_files == {query_path, context_path, visibility_path}
        and p11_4e_contract_files - {context_path, visibility_path}
        == {query_path},
        "P11.4E ownership or its reviewed consumers changed",
    )
    require(
        candidate_files == expected_candidate_files
        and candidate_files - {query_path, context_path, visibility_path}
        == p11_4d_owned,
        "candidate-model ownership or reviewed consumer set changed",
    )
    project_text = (PACKAGE_DIRECTORY / "language" / "project.py").read_text(
        encoding="utf-8"
    )
    require(
        "ProjectResolutionContext" not in project_text
        and "ProjectVisibilityEvidence" not in project_text
        and "ProjectVisibilityDecision" not in project_text
        and "evaluate_project_visibility" not in project_text
        and "filter_project_visible_candidates" not in project_text,
        "ProjectBuild or ProjectBuilder acquired automatic visibility integration",
    )


def main() -> None:
    original_directory = Path.cwd().resolve()
    status_before = repository_status()
    bytecode_before = repository_bytecode_state()

    def forbidden_network(*_args, **_kwargs):
        raise AssertionError("P11.4G attempted network access")

    with patch("socket.create_connection", side_effect=forbidden_network), patch(
        "socket.socket", side_effect=forbidden_network
    ):
        test_public_model_and_fixed_policy_surface()
        test_basis_derivation_and_overlap()
        test_decision_validation()
        test_contextual_filtering_and_query_modes()
        test_project_generics_air_artifact_and_compatibility()
        test_exact_production_boundaries_and_no_diagnostics()

    require(Path.cwd().resolve() == original_directory, "working directory changed")
    require(repository_status() == status_before, "running the test changed Git status")
    require(
        repository_bytecode_state() == bytecode_before,
        "running the test changed repository bytecode state",
    )
    print("AFP-P11.4G visibility policy and filtering smoke test passed.")
    print("Public frozen decision model and fixed policy surface: PASS")
    print("Four-token basis derivation, overlap, and no precedence: PASS")
    print("Strict direct validation and evidence immutability: PASS")
    print("Zero, one, many, order, duplicate, and query-mode filtering: PASS")
    print("Project, entry, duplicate-link, generic, AIR, and artifact: PASS")
    print("CLI, runtime, LSP, VS Code, and Visual Studio compatibility: PASS")
    print("Production boundaries, diagnostics, network, Git, and bytecode: PASS")


if __name__ == "__main__":
    main()
