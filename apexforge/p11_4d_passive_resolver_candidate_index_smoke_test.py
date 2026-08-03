"""Executable contract for the P11.4D passive resolver candidate index."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from io import StringIO
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from air.serialization import air_to_dict
from language.compiler import compile_source
from language.declarations import ProjectDeclarationOwner, ProjectDeclarationOwnership
from language.identities import ProjectDeclaredIdentity, ProjectIdentityIndex
from language.project import ProjectBuild, ProjectLinkError, ProjectBuilder, build_project
import language.resolution_candidates as candidate_module
from language.resolution_candidates import (
    ProjectQualification,
    ProjectResolutionCandidate,
    ProjectResolutionCandidateIndex,
)
from language.source import SourceText
from p11_4b_declared_identity_metadata_smoke_test import execution_context
from p11_4c_resolver_qualification_architecture_audit_smoke_test import (
    diagnostic_of,
    test_artifact_cli_tooling_and_no_resolver_consumers as accepted_external_compatibility,
    test_collisions_imports_exports_and_entries_are_unchanged as accepted_lookup_boundaries,
    test_generic_owner_lowering_and_runtime_lookup_are_unchanged as accepted_generic_runtime,
)
from tooling.build_artifact import construct_build_artifact
from tooling.cli import P10_T1_CLI_VERSION, main as cli_main
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
    values: list[tuple[str, int, int]] = []
    for path in REPOSITORY_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in {".pyc", ".pyo"}:
            continue
        stat = path.stat()
        values.append(
            (
                path.relative_to(REPOSITORY_ROOT).as_posix(),
                stat.st_size,
                stat.st_mtime_ns,
            )
        )
    return tuple(sorted(values))


def invoke_cli(arguments: tuple[str, ...]):
    stdout = StringIO()
    stderr = StringIO()
    code = cli_main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def candidate_record(
    kind: str,
    declared_name: str,
    source_name: str,
    module_name: str | None,
    *,
    start: int = 0,
) -> ProjectResolutionCandidate:
    text = SourceText(source_name, (" " * start) + declared_name + "\n")
    span = text.span(start, start + len(declared_name))
    air_id = f"{kind}:{declared_name}"
    identity = ProjectDeclaredIdentity(
        kind=kind,
        declared_name=declared_name,
        current_air_id=air_id,
        source_name=source_name,
        module_name=module_name,
        qualified_display_name=(
            declared_name
            if module_name is None
            else f"{module_name}.{declared_name}"
        ),
        span=span,
    )
    owner = ProjectDeclarationOwner(
        kind=kind,
        air_id=air_id,
        source_name=source_name,
        module_name=module_name,
        span=span,
    )
    return ProjectResolutionCandidate(
        identity=identity,
        owner=owner,
        qualification=ProjectQualification(
            kind=kind,
            module_segments=(
                () if module_name is None else tuple(module_name.split("."))
            ),
            declaration_path=(declared_name,),
            legacy=module_name is None,
        ),
    )


def test_public_models_validation_and_immutability() -> None:
    require(
        candidate_module.__all__
        == (
            "ProjectQualification",
            "ProjectResolutionCandidate",
            "ProjectResolutionCandidateIndex",
        ),
        "resolution candidate module exports an unintended public name",
    )
    require(
        tuple(item.name for item in fields(ProjectQualification))
        == ("kind", "module_segments", "declaration_path", "legacy")
        and tuple(item.name for item in fields(ProjectResolutionCandidate))
        == ("identity", "owner", "qualification")
        and tuple(item.name for item in fields(ProjectResolutionCandidateIndex))
        == ("candidates",),
        "public P11.4D dataclass fields changed",
    )
    require(
        ProjectQualification.__dataclass_params__.frozen
        and ProjectResolutionCandidate.__dataclass_params__.frozen
        and ProjectResolutionCandidateIndex.__dataclass_params__.frozen,
        "P11.4D metadata is mutable",
    )

    legacy = candidate_record("directive", "Legacy", "legacy.apex", None)
    module = candidate_record("function", "Work", "work.apex", "App.Core")
    require(
        legacy.qualification
        == ProjectQualification("directive", (), ("Legacy",), True)
        and module.qualification
        == ProjectQualification(
            "function", ("App", "Core"), ("Work",), False
        )
        and legacy.identity.qualified_display_name == "Legacy"
        and module.identity.qualified_display_name == "App.Core.Work",
        "legacy or module-owned structured qualification changed",
    )
    require_raises(
        FrozenInstanceError,
        lambda: setattr(legacy.qualification, "legacy", False),
        "qualification is mutable",
    )
    require_raises(
        FrozenInstanceError,
        lambda: setattr(legacy, "owner", module.owner),
        "candidate is mutable",
    )
    require_raises(
        FrozenInstanceError,
        lambda: setattr(ProjectResolutionCandidateIndex(), "candidates", ()),
        "candidate index is mutable",
    )

    invalid_qualifications = (
        lambda: ProjectQualification("workflow", (), ("Name",), True),
        lambda: ProjectQualification("directive", ("App",), ("Name",), True),
        lambda: ProjectQualification("directive", (), ("Name",), False),
        lambda: ProjectQualification("directive", (), (), True),
        lambda: ProjectQualification("directive", (), ("One", "Two"), True),
        lambda: ProjectQualification("directive", ("App", ""), ("Name",), False),
        lambda: ProjectQualification("directive", ("bad-name",), ("Name",), False),
        lambda: ProjectQualification("directive", "App", ("Name",), False),
        lambda: ProjectQualification("directive", (), "Name", True),
        lambda: ProjectQualification("directive", (), ("Name",), 1),
    )
    for operation in invalid_qualifications:
        require_raises(
            (TypeError, ValueError),
            operation,
            "malformed structured qualification was accepted",
        )

    base = candidate_record("directive", "Base", "base.apex", "App.Base")
    other_span = SourceText("base.apex", " directive Base\n").span(1, 5)
    mismatches = (
        lambda: ProjectResolutionCandidate(object(), base.owner, base.qualification),
        lambda: ProjectResolutionCandidate(base.identity, object(), base.qualification),
        lambda: ProjectResolutionCandidate(base.identity, base.owner, object()),
        lambda: ProjectResolutionCandidate(
            base.identity,
            ProjectDeclarationOwner(
                "function", "function:Base", "base.apex", "App.Base", base.owner.span
            ),
            base.qualification,
        ),
        lambda: ProjectResolutionCandidate(
            base.identity,
            ProjectDeclarationOwner(
                "directive", "directive:Other", "base.apex", "App.Base", base.owner.span
            ),
            base.qualification,
        ),
        lambda: ProjectResolutionCandidate(
            base.identity,
            ProjectDeclarationOwner(
                "directive",
                "directive:Base",
                "other.apex",
                "App.Base",
                SourceText("other.apex", "Base\n").span(0, 4),
            ),
            base.qualification,
        ),
        lambda: ProjectResolutionCandidate(
            base.identity,
            ProjectDeclarationOwner(
                "directive", "directive:Base", "base.apex", "App.Other", base.owner.span
            ),
            base.qualification,
        ),
        lambda: ProjectResolutionCandidate(
            base.identity,
            ProjectDeclarationOwner(
                "directive", "directive:Base", "base.apex", "App.Base", other_span
            ),
            base.qualification,
        ),
        lambda: ProjectResolutionCandidate(
            base.identity,
            base.owner,
            ProjectQualification(
                "directive", ("App", "Base"), ("Other",), False
            ),
        ),
    )
    for operation in mismatches:
        require_raises(
            (TypeError, ValueError),
            operation,
            "mismatched candidate facts were accepted",
        )


def test_order_queries_duplicates_and_no_selection() -> None:
    legacy = candidate_record("directive", "Same", "z.apex", None)
    upper = candidate_record("directive", "Same", "A.apex", "App.Core")
    lower = candidate_record("directive", "Same", "a.apex", "App.Core")
    beta = candidate_record("directive", "Beta", "beta.apex", "App.Core")
    function = candidate_record("function", "Same", "function.apex", "App.Core")
    shuffled = (function, lower, beta, legacy, upper)
    index = ProjectResolutionCandidateIndex(shuffled)
    require(
        isinstance(index.candidates, tuple)
        and index.candidates == (legacy, beta, upper, lower, function),
        "candidate evidence ordering is not canonical",
    )
    require(
        ProjectResolutionCandidateIndex(tuple(reversed(shuffled))) == index,
        "candidate ordering depends on input order",
    )
    require(
        index.find_all("directive", "Same") == (legacy, upper, lower)
        and index.find_all("function", "Same") == (function,)
        and index.find_current_air_id("directive:Same")
        == (legacy, upper, lower)
        and index.find_qualification(upper.qualification) == (upper, lower)
        and index.find_all("directive", "same") == ()
        and index.find_current_air_id("Directive:Same") == (),
        "factual filters changed case or failed to return every match",
    )
    duplicate_index = ProjectResolutionCandidateIndex((upper, upper, lower))
    require(
        duplicate_index.candidates == (upper, upper, lower)
        and duplicate_index.find_all("directive", "Same")
        == (upper, upper, lower),
        "the passive representation discarded duplicate candidate facts",
    )
    require_raises(
        TypeError,
        lambda: ProjectResolutionCandidateIndex((object(),)),
        "candidate index accepted a non-candidate value",
    )
    require_raises(
        TypeError,
        lambda: index.find_qualification(object()),
        "structured-qualification query accepted another type",
    )
    for name in vars(ProjectResolutionCandidateIndex):
        if name.startswith("_"):
            continue
        require(
            not any(
                marker in name.casefold()
                for marker in (
                    "resolve",
                    "bind",
                    "select",
                    "choose",
                    "winner",
                    "best",
                    "visible",
                    "accessible",
                    "ambiguity",
                )
            ),
            f"candidate index acquired semantic operation {name!r}",
        )


def test_successful_build_integration_and_existing_failures() -> None:
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
    candidates = project.resolution_candidate_index.candidates
    require(
        len(candidates)
        == len(project.identity_index.identities)
        == len(project.declaration_ownership.declarations)
        == 2,
        "successful build metadata is not one-to-one",
    )
    for candidate in candidates:
        require(
            any(candidate.identity is item for item in project.identity_index.identities)
            and any(
                candidate.owner is item
                for item in project.declaration_ownership.declarations
            ),
            "candidate copied identity or ownership facts",
        )
    require(
        len(project.resolution_candidate_index.find_all("directive", "Same")) == 1
        and len(project.resolution_candidate_index.find_all("function", "Same")) == 1
        and project.resolve_entry("Same") == "directive:Same"
        and project.resolution_candidate_index.find_qualification(
            ProjectQualification(
                "directive", ("App", "Directive"), ("Same",), False
            )
        )[0].identity.qualified_display_name == "App.Directive.Same",
        "cross-kind separation, display metadata, or entry behavior changed",
    )

    legacy = build_project(
        {
            "legacy-directive.apex": "directive Legacy {}\n",
            "legacy-function.apex": (
                "function Echo(value : int) : int { return value }\n"
            ),
        }
    )
    require(
        len(legacy.resolution_candidate_index.candidates) == 2
        and all(
            candidate.qualification.legacy
            and candidate.qualification.module_segments == ()
            and candidate.owner.module_name is None
            for candidate in legacy.resolution_candidate_index.candidates
        ),
        "legacy candidates acquired synthetic module qualification",
    )

    project_fields = fields(ProjectBuild)
    require(
        project_fields[-1].name == "resolution_candidate_index"
        and project_fields[-1].default_factory is ProjectResolutionCandidateIndex
        and project_fields[-1].compare is False,
        "ProjectBuild candidate index was not appended compatibly",
    )
    positional = ProjectBuild(
        project.source_units,
        project.program,
        project.verified,
        project.source_map,
        project.module_graph,
        project.entry_directive,
        project.document_graph,
        project.declaration_ownership,
        project.identity_index,
    )
    require(
        positional == project
        and positional.resolution_candidate_index
        == ProjectResolutionCandidateIndex(),
        "existing positional ProjectBuild construction changed",
    )
    require_raises(
        TypeError,
        lambda: ProjectBuild(
            project.source_units,
            project.program,
            project.verified,
            project.source_map,
            project.module_graph,
            project.entry_directive,
            project.document_graph,
            project.declaration_ownership,
            project.identity_index,
            object(),
        ),
        "ProjectBuild accepted a non-candidate index",
    )

    bare = ProjectBuilder(compiler=lambda source: compile_source(source)).build(
        {"bare.apex": "directive Bare {}\n"}
    )
    require(
        bare.declaration_ownership == ProjectDeclarationOwnership()
        and bare.identity_index == ProjectIdentityIndex()
        and bare.resolution_candidate_index == ProjectResolutionCandidateIndex(),
        "a compiler without source-map metadata fabricated candidates",
    )

    duplicate = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a.apex": "module App.A\n\nfunction Same() : int { return 1 }\n",
                "b.apex": "module App.B\n\nfunction Same() : int { return 2 }\n",
            }
        ),
        "same-kind duplicate build exposed candidate selection",
    )
    item = diagnostic_of(duplicate)
    require(
        item.stage == "link"
        and item.code == "APX-LINK-001"
        and item.air_id == "function:Same",
        "duplicate failure stage, code, or identity changed",
    )


def test_generics_air_artifact_cli_runtime_and_tooling() -> None:
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
    before_air = air_to_dict(generic.program)
    identity_candidates = generic.resolution_candidate_index.find_all(
        "function", "Identity"
    )
    closure = collect_linked_specializations(generic.program)
    lowered = lower_linked_generics(generic.program)
    require(
        len(identity_candidates) == 1
        and identity_candidates[0].identity.current_air_id == "function:Identity"
        and generic.resolution_candidate_index.find_current_air_id(
            "Identity<int>"
        )
        == ()
        and not any(
            "__apx_spec__" in candidate.identity.current_air_id
            for candidate in generic.resolution_candidate_index.candidates
        )
        and closure.canonical_ids == lowered.canonical_ids == ("Identity<int>",)
        and lowered.binding_for("Identity<int>").function_id.startswith(
            "function:__apx_spec__Identity__int__"
        )
        and air_to_dict(generic.program) == before_air,
        "generic candidates changed specialization, lowering, or AIR",
    )

    original_directory = Path.cwd().resolve()
    temporary_path: Path
    with TemporaryDirectory(prefix="apexforge-p11-4d-") as temporary:
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
                    "name": "P11_4D_Candidates",
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
        require(
            len(project.resolution_candidate_index.find_all("directive", "Main"))
            == 1,
            "artifact fixture omitted its passive candidate",
        )
        after = construct_build_artifact(loaded, project)
        require(
            before.content == after.content
            and before.fingerprint == after.fingerprint
            and b"resolution_candidate_index" not in after.content
            and b"ProjectResolutionCandidate" not in after.content,
            "artifact v1 bytes or fingerprint acquired candidate metadata",
        )

        check = invoke_cli(("check", str(temporary_path)))
        run = invoke_cli(("run", str(temporary_path)))
        build_cli = invoke_cli(
            ("build", str(temporary_path), "--output", str(output_path))
        )
        version = invoke_cli(("--version",))
        require(
            check
            == (
                0,
                "ApexForge check passed: P11_4D_Candidates (1 source(s)).\n",
                "",
            )
            and run
            == (
                0,
                "ApexForge run succeeded: P11_4D_Candidates\n"
                "Entry: directive:Main\nRuntime diagnostics: 0\n",
                "",
            )
            and build_cli[0] == 0
            and build_cli[2] == ""
            and output_path.read_bytes() == before.content
            and version == (0, f"ApexForge CLI {P10_T1_CLI_VERSION}\n", ""),
            "CLI check, run, build, or version boundary changed",
        )
        runtime = project.execute(
            execution_context(project, "Main"),
            entry="Main",
        )
        require(
            runtime.ok
            and project.resolve_entry() == "directive:Main"
            and air_to_dict(project.program) == air_to_dict(project.verified.program),
            "runtime or entry behavior changed",
        )
        require(
            Path.cwd().resolve() == original_directory,
            "compatibility fixture changed the working directory",
        )

    require(
        not temporary_path.exists()
        and Path.cwd().resolve() == original_directory,
        "temporary fixture escaped its context manager",
    )

    accepted_lookup_boundaries()
    accepted_generic_runtime()
    accepted_external_compatibility()


def test_production_boundary_is_exact() -> None:
    observed = set()
    markers = (
        "ProjectQualification",
        "ProjectResolutionCandidate",
        "resolution_candidate_index",
    )
    for path in PACKAGE_DIRECTORY.rglob("*.py"):
        if path.name.endswith("_smoke_test.py") or "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in markers):
            observed.add(path.relative_to(REPOSITORY_ROOT).as_posix())
        require(
            "APX-RESOLVE-" not in text,
            f"production file {path.name} introduced a resolver diagnostic",
        )
    require(
        observed
        == {
            "apexforge/language/resolution_candidates.py",
            "apexforge/language/project.py",
            "apexforge/language/resolution_queries.py",
            "apexforge/language/resolution_context.py",
            "apexforge/language/resolution_visibility.py",
        },
        "a production consumer exists outside the reviewed successor boundary",
    )
    p11_4d_owned = {
        "apexforge/language/resolution_candidates.py",
        "apexforge/language/project.py",
    }
    successor_consumers = observed - p11_4d_owned
    require(
        p11_4d_owned.issubset(observed)
        and successor_consumers
        == {
            "apexforge/language/resolution_queries.py",
            "apexforge/language/resolution_context.py",
            "apexforge/language/resolution_visibility.py",
        },
        "P11.4D ownership or its reviewed successor consumers changed",
    )


def main() -> None:
    original_directory = Path.cwd().resolve()
    status_before = repository_status()
    bytecode_before = repository_bytecode_state()

    def forbidden_network(*_args, **_kwargs):
        raise AssertionError("P11.4D attempted network access")

    with patch("socket.create_connection", side_effect=forbidden_network), patch(
        "socket.socket", side_effect=forbidden_network
    ):
        test_public_models_validation_and_immutability()
        test_order_queries_duplicates_and_no_selection()
        test_successful_build_integration_and_existing_failures()
        test_generics_air_artifact_cli_runtime_and_tooling()
        test_production_boundary_is_exact()

    require(Path.cwd().resolve() == original_directory, "working directory changed")
    require(repository_status() == status_before, "running the test changed Git status")
    require(
        repository_bytecode_state() == bytecode_before,
        "running the test changed repository bytecode state",
    )
    print("AFP-P11.4D passive resolver candidate index smoke test passed.")
    print("Public immutable records and exact fact validation: PASS")
    print("Deterministic duplicate-capable factual index and queries: PASS")
    print("Successful-build integration and existing collision boundary: PASS")
    print("AIR, generics, artifact v1, CLI, runtime, LSP, and Visual Studio: PASS")
    print("Production boundary, network, fixture, Git, and bytecode safety: PASS")


if __name__ == "__main__":
    main()
