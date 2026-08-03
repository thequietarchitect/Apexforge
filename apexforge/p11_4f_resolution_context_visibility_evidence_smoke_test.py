"""Executable contract for P11.4F context and visibility evidence."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from air.serialization import air_to_dict
from language.project import ProjectLinkError, build_project
import language.resolution_context as context_module
from language.resolution_candidates import ProjectResolutionCandidateIndex
from language.resolution_context import (
    ProjectResolutionContext,
    ProjectVisibilityEvidence,
    collect_project_visibility_evidence,
)
from language.resolution_queries import ProjectResolutionQuery
from p11_4c_resolver_qualification_architecture_audit_smoke_test import diagnostic_of
from p11_4d_passive_resolver_candidate_index_smoke_test import (
    candidate_record,
    repository_bytecode_state,
    repository_status,
)
from p11_4e_structured_resolution_query_binding_smoke_test import (
    test_artifact_and_accepted_compatibility as accepted_compatibility,
    test_project_entry_duplicates_generics_and_air as accepted_project_contract,
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


def test_public_model_and_context_validation() -> None:
    require(
        context_module.__all__
        == (
            "ProjectResolutionContext",
            "ProjectVisibilityEvidence",
            "collect_project_visibility_evidence",
        ),
        "resolution context module exports an unintended public name",
    )
    require(
        tuple(item.name for item in fields(ProjectResolutionContext))
        == ("source_name", "module_segments", "imported_modules")
        and tuple(item.name for item in fields(ProjectVisibilityEvidence))
        == (
            "query",
            "context",
            "candidate",
            "same_source",
            "same_module",
            "imported_module",
            "legacy_candidate",
        ),
        "P11.4F public dataclass fields changed",
    )
    require(
        ProjectResolutionContext.__dataclass_params__.frozen
        and ProjectVisibilityEvidence.__dataclass_params__.frozen,
        "P11.4F public records are mutable",
    )
    source = (
        PACKAGE_DIRECTORY / "language" / "resolution_context.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    public_definitions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef))
        and not node.name.startswith("_")
    }
    require(
        public_definitions == set(context_module.__all__),
        "P11.4F defines an extra public production API",
    )

    legacy = ProjectResolutionContext("Legacy.apex", [])
    module = ProjectResolutionContext(
        "Src/Main.apex",
        ["App", "Main"],
        [
            ["Zeta"],
            ["Alpha", "Core"],
            ["Zeta"],
            ["App", "Main"],
        ],
    )
    require(
        legacy.source_name == "Legacy.apex"
        and legacy.module_segments == ()
        and legacy.imported_modules == ()
        and module.source_name == "Src/Main.apex"
        and module.module_segments == ("App", "Main")
        and module.imported_modules
        == (
            ("Alpha", "Core"),
            ("App", "Main"),
            ("Zeta",),
            ("Zeta",),
        ),
        "context normalization, ordering, duplicates, spelling, or case changed",
    )
    require_raises(
        FrozenInstanceError,
        lambda: setattr(module, "source_name", "other.apex"),
        "resolution context is mutable",
    )

    invalid_contexts = (
        lambda: ProjectResolutionContext(None, ()),
        lambda: ProjectResolutionContext("", ()),
        lambda: ProjectResolutionContext("bad\0source", ()),
        lambda: ProjectResolutionContext("source.apex", None),
        lambda: ProjectResolutionContext("source.apex", "App"),
        lambda: ProjectResolutionContext("source.apex", b"App"),
        lambda: ProjectResolutionContext("source.apex", ("App.Main",)),
        lambda: ProjectResolutionContext("source.apex", ("",)),
        lambda: ProjectResolutionContext("source.apex", ("bad-name",)),
        lambda: ProjectResolutionContext("source.apex", (1,)),
        lambda: ProjectResolutionContext("source.apex", (), None),
        lambda: ProjectResolutionContext("source.apex", (), "App"),
        lambda: ProjectResolutionContext("source.apex", (), b"App"),
        lambda: ProjectResolutionContext("source.apex", (), ((),)),
        lambda: ProjectResolutionContext("source.apex", (), ("App",)),
        lambda: ProjectResolutionContext("source.apex", (), (("App.Core",),)),
        lambda: ProjectResolutionContext("source.apex", (), (("bad-name",),)),
        lambda: ProjectResolutionContext("source.apex", (), ((1,),)),
    )
    for operation in invalid_contexts:
        require_raises(
            (TypeError, ValueError),
            operation,
            "malformed resolution context was accepted",
        )


def test_evidence_facts_query_modes_and_duplicates() -> None:
    legacy = candidate_record(
        "directive", "Name", "src/main.apex", None
    )
    current = candidate_record(
        "directive", "Name", "src/main.apex", "App.Main"
    )
    imported = candidate_record(
        "directive", "Name", "lib/core.apex", "Lib.Core"
    )
    unrelated = candidate_record(
        "directive", "Name", "other.apex", "Other.Core"
    )
    case_mismatch = candidate_record(
        "directive", "Name", "lib/lower.apex", "lib.Core"
    )
    function = candidate_record(
        "function", "Name", "function.apex", "App.Main"
    )
    index = ProjectResolutionCandidateIndex(
        (case_mismatch, unrelated, imported, function, current, legacy)
    )
    context = ProjectResolutionContext(
        "src/main.apex",
        ("App", "Main"),
        (
            ("Zeta",),
            ("Lib", "Core"),
            ("App", "Main"),
            ("Zeta",),
        ),
    )
    unqualified_query = ProjectResolutionQuery("directive", ("Name",))
    evidence = collect_project_visibility_evidence(
        index, unqualified_query, context
    )
    require(
        tuple(item.candidate for item in evidence)
        == (legacy, current, imported, unrelated, case_mismatch),
        "evidence collection changed canonical candidate ordering",
    )
    by_candidate = {item.candidate: item for item in evidence}
    require(
        by_candidate[legacy].same_source
        and not by_candidate[legacy].same_module
        and not by_candidate[legacy].imported_module
        and by_candidate[legacy].legacy_candidate,
        "legacy candidate facts changed",
    )
    require(
        by_candidate[current].same_source
        and by_candidate[current].same_module
        and by_candidate[current].imported_module
        and not by_candidate[current].legacy_candidate,
        "same-source, same-module, and imported-module overlap changed",
    )
    require(
        not by_candidate[imported].same_source
        and not by_candidate[imported].same_module
        and by_candidate[imported].imported_module
        and not by_candidate[imported].legacy_candidate,
        "exact imported-module evidence changed",
    )
    require(
        not by_candidate[unrelated].same_source
        and not by_candidate[unrelated].same_module
        and not by_candidate[unrelated].imported_module
        and not by_candidate[unrelated].legacy_candidate
        and not by_candidate[case_mismatch].imported_module,
        "unrelated or exact-case import evidence changed",
    )

    legacy_context = ProjectResolutionContext("src/main.apex", ())
    legacy_context_evidence = collect_project_visibility_evidence(
        index, unqualified_query, legacy_context
    )
    require(
        all(not item.same_module for item in legacy_context_evidence),
        "a legacy use-site context produced same-module evidence",
    )
    exact_legacy = collect_project_visibility_evidence(
        index,
        ProjectResolutionQuery("directive", ("Name",), ()),
        context,
    )
    exact_module = collect_project_visibility_evidence(
        index,
        ProjectResolutionQuery(
            "directive", ("Name",), ("Lib", "Core")
        ),
        context,
    )
    missing = collect_project_visibility_evidence(
        index,
        ProjectResolutionQuery(
            "directive", ("Missing",), ("Lib", "Core")
        ),
        context,
    )
    exact_function = collect_project_visibility_evidence(
        index,
        ProjectResolutionQuery("function", ("Name",)),
        context,
    )
    require(
        tuple(item.candidate for item in exact_legacy) == (legacy,)
        and tuple(item.candidate for item in exact_module) == (imported,)
        and missing == ()
        and tuple(item.candidate for item in exact_function) == (function,),
        "legacy, module, zero, unique, or cross-kind query reuse changed",
    )

    duplicate_index = ProjectResolutionCandidateIndex(
        (current, legacy, current)
    )
    duplicate_evidence = collect_project_visibility_evidence(
        duplicate_index, unqualified_query, context
    )
    require(
        tuple(item.candidate for item in duplicate_evidence)
        == (legacy, current, current)
        and duplicate_evidence[1] == duplicate_evidence[2]
        and len(duplicate_evidence) == 3,
        "ambiguous evidence collapsed, selected, or reordered duplicates",
    )
    banned_fields = {
        "visible",
        "accessible",
        "selected",
        "winner",
        "rank",
        "priority",
        "precedence",
    }
    require(
        banned_fields.isdisjoint(
            item.name for item in fields(ProjectVisibilityEvidence)
        )
        and len(evidence) == 5,
        "evidence acquired policy fields or filtered matching candidates",
    )


def test_direct_validation() -> None:
    candidate = candidate_record(
        "directive", "Name", "src/main.apex", "App.Main"
    )
    query = ProjectResolutionQuery(
        "directive", ("Name",), ("App", "Main")
    )
    context = ProjectResolutionContext(
        "src/main.apex",
        ("App", "Main"),
        (("App", "Main"),),
    )
    valid = ProjectVisibilityEvidence(
        query,
        context,
        candidate,
        True,
        True,
        True,
        False,
    )
    require(
        valid.candidate is candidate,
        "valid direct evidence construction changed",
    )
    invalid_values = (
        lambda: ProjectVisibilityEvidence(
            object(), context, candidate, True, True, True, False
        ),
        lambda: ProjectVisibilityEvidence(
            query, object(), candidate, True, True, True, False
        ),
        lambda: ProjectVisibilityEvidence(
            query, context, object(), True, True, True, False
        ),
        lambda: ProjectVisibilityEvidence(
            ProjectResolutionQuery("function", ("Name",)),
            context,
            candidate,
            True,
            True,
            True,
            False,
        ),
    )
    for operation in invalid_values:
        require_raises(
            (TypeError, ValueError),
            operation,
            "direct evidence accepted an invalid query, context, or candidate",
        )
    for offset in range(4):
        flags: list[object] = [True, True, True, False]
        flags[offset] = 1
        require_raises(
            TypeError,
            lambda flags=flags: ProjectVisibilityEvidence(
                query, context, candidate, *flags
            ),
            "direct evidence accepted a non-boolean flag",
        )
    expected = [True, True, True, False]
    for offset in range(4):
        flags = list(expected)
        flags[offset] = not flags[offset]
        require_raises(
            ValueError,
            lambda flags=flags: ProjectVisibilityEvidence(
                query, context, candidate, *flags
            ),
            "direct evidence accepted an incorrect derived flag",
        )

    index = ProjectResolutionCandidateIndex((candidate,))
    require_raises(
        TypeError,
        lambda: collect_project_visibility_evidence(object(), query, context),
        "collector accepted a non-index",
    )
    require_raises(
        TypeError,
        lambda: collect_project_visibility_evidence(index, object(), context),
        "collector accepted a non-query",
    )
    require_raises(
        TypeError,
        lambda: collect_project_visibility_evidence(index, query, object()),
        "collector accepted a non-context",
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
    main_evidence = collect_project_visibility_evidence(
        project.resolution_candidate_index,
        ProjectResolutionQuery("directive", ("Main",)),
        ProjectResolutionContext("main.apex", ("App", "Main")),
    )
    function_evidence = collect_project_visibility_evidence(
        project.resolution_candidate_index,
        ProjectResolutionQuery("function", ("Main",)),
        ProjectResolutionContext("function.apex", ("App", "Function")),
    )
    generic_evidence = collect_project_visibility_evidence(
        project.resolution_candidate_index,
        ProjectResolutionQuery(
            "function", ("Identity",), ("Lib", "Generic")
        ),
        ProjectResolutionContext(
            "use.apex", ("App", "Use"), (("Lib", "Generic"),)
        ),
    )
    synthetic_evidence = collect_project_visibility_evidence(
        project.resolution_candidate_index,
        ProjectResolutionQuery(
            "function", ("__apx_spec__Identity__int__",)
        ),
        ProjectResolutionContext("use.apex", ("App", "Use")),
    )
    closure = collect_linked_specializations(project.program)
    lowered = lower_linked_generics(project.program)
    require(
        len(main_evidence) == len(function_evidence) == len(generic_evidence) == 1
        and main_evidence[0].same_source
        and main_evidence[0].same_module
        and function_evidence[0].candidate.identity.kind == "function"
        and generic_evidence[0].imported_module
        and generic_evidence[0].candidate.identity.current_air_id
        == "function:Identity"
        and synthetic_evidence == ()
        and closure.canonical_ids == lowered.canonical_ids == ("Identity<int>",)
        and lowered.binding_for("Identity<int>").function_id.startswith(
            "function:__apx_spec__Identity__int__"
        )
        and project.resolve_entry() == "directive:Main"
        and project.resolve_entry("Main") == "directive:Main"
        and air_to_dict(project.program) == before_air,
        "project, entry, cross-kind, generic, lowering, or AIR boundary changed",
    )

    duplicate = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a.apex": "module App.A\n\ndirective Same {}\n",
                "b.apex": "module App.B\n\ndirective Same {}\n",
            }
        ),
        "duplicate build exposed context or evidence",
    )
    item = diagnostic_of(duplicate)
    require(
        item.stage == "link"
        and item.code == "APX-LINK-001"
        and item.air_id == "principal:Same",
        "duplicate-link behavior changed",
    )

    original_directory = Path.cwd().resolve()
    temporary_path: Path
    with TemporaryDirectory(prefix="apexforge-p11-4f-") as temporary:
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
                    "name": "P11_4F_Evidence",
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
        evidence = collect_project_visibility_evidence(
            loaded_project.resolution_candidate_index,
            ProjectResolutionQuery("directive", ("Main",)),
            ProjectResolutionContext(
                "src/main.apex", ("App", "Main")
            ),
        )
        after = construct_build_artifact(loaded, loaded_project)
        require(
            len(evidence) == 1
            and before.content == after.content
            and before.fingerprint == after.fingerprint
            and b"ProjectResolutionContext" not in after.content
            and b"ProjectVisibilityEvidence" not in after.content,
            "artifact v1 bytes or fingerprint acquired context evidence",
        )
        require(
            Path.cwd().resolve() == original_directory,
            "artifact evidence fixture changed the working directory",
        )
    require(
        not temporary_path.exists()
        and Path.cwd().resolve() == original_directory,
        "temporary fixture escaped its context manager",
    )

    accepted_project_contract()
    accepted_compatibility()


def test_exact_production_boundaries_and_no_diagnostics() -> None:
    p11_4f_files = set()
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
                "ProjectResolutionContext",
                "ProjectVisibilityEvidence",
                "collect_project_visibility_evidence",
            )
        ):
            p11_4f_files.add(relative)
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

    context_path = "apexforge/language/resolution_context.py"
    query_path = "apexforge/language/resolution_queries.py"
    p11_4d_owned = {
        "apexforge/language/resolution_candidates.py",
        "apexforge/language/project.py",
    }
    visibility_path = "apexforge/language/resolution_visibility.py"
    expected_candidate_files = p11_4d_owned | {
        query_path,
        context_path,
        visibility_path,
    }
    require(
        p11_4f_files == {context_path, visibility_path}
        and p11_4f_files - {visibility_path} == {context_path},
        "P11.4F ownership or its single P11.4G successor consumer changed",
    )
    require(
        p11_4e_contract_files == {query_path, context_path, visibility_path}
        and p11_4e_contract_files - {context_path, visibility_path}
        == {query_path},
        "P11.4E ownership or its reviewed successor consumers changed",
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
        and "collect_project_visibility_evidence" not in project_text
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
        raise AssertionError("P11.4F attempted network access")

    with patch("socket.create_connection", side_effect=forbidden_network), patch(
        "socket.socket", side_effect=forbidden_network
    ):
        test_public_model_and_context_validation()
        test_evidence_facts_query_modes_and_duplicates()
        test_direct_validation()
        test_project_generics_air_artifact_and_compatibility()
        test_exact_production_boundaries_and_no_diagnostics()

    require(Path.cwd().resolve() == original_directory, "working directory changed")
    require(repository_status() == status_before, "running the test changed Git status")
    require(
        repository_bytecode_state() == bytecode_before,
        "running the test changed repository bytecode state",
    )
    print("AFP-P11.4F resolution context and visibility evidence smoke test passed.")
    print("Public frozen context/evidence records and validation: PASS")
    print("Legacy, module, import, source, case, and overlap facts: PASS")
    print("Query modes, ambiguity order, and duplicate retention: PASS")
    print("Direct consistency, no policy fields, and no filtering: PASS")
    print("Project, entry, duplicate-link, generic, AIR, and artifact: PASS")
    print("CLI, runtime, LSP, VS Code, and Visual Studio compatibility: PASS")
    print("Production boundaries, diagnostics, network, Git, and bytecode: PASS")


if __name__ == "__main__":
    main()
