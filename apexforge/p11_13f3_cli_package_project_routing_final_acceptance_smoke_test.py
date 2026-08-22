"""P11.13F3 CLI package-project routing and final-F acceptance smoke test."""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import io
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from tooling import cli
from tooling.build_artifact import BUILD_ARTIFACT_SCHEMA_V3


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
F2_FREEZE_TAG = "afp-p11-13f2-freeze"
F2_FREEZE_COMMIT = "3c2ccb0af494fff546d879ad1ce07af34c5455c0"

FROZEN_F2_HASHES = {
    "apexforge/rich_documents/project_build.py":
        "31C7A3A3F1737ED326C0EACF9B1CA3E2B2F4AF41D56C88C9E5B3E3B21A29AB7F",
    "apexforge/tooling/build_artifact.py":
        "FBB3B49E85D549705AF5BD0ED0459063DCEAB4487A65E68BAF24E6DD6972B76B",
    "apexforge/p11_13f2_native_rich_document_project_build_artifact_smoke_test.py":
        "176A36F61717CD59A0AF19ECC6F9DA9A300782BB594942FAA1CAA5279BC42971",
    "docs/p11/P11_13F2_NATIVE_RICH_DOCUMENT_PROJECT_BUILD_ARTIFACT.md":
        "73ACD4AC0D43260AEE610A77461D809BB440F6E0C473F8281F2A3770365AFE59",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=str(REPOSITORY_ROOT),
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.rstrip()


def _assert_frozen_f2_baseline() -> None:
    require(
        git("cat-file", "-t", F2_FREEZE_TAG) == "tag",
        "F2 freeze tag is no longer annotated",
    )
    require(
        git("rev-parse", F2_FREEZE_TAG + "^{commit}") == F2_FREEZE_COMMIT,
        "F2 freeze tag moved",
    )
    require(
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", F2_FREEZE_COMMIT, "HEAD"),
            cwd=str(REPOSITORY_ROOT),
            check=False,
        ).returncode == 0,
        "F2 freeze is not an ancestor of F3",
    )

    for relative, expected in FROZEN_F2_HASHES.items():
        observed = hashlib.sha256(
            (REPOSITORY_ROOT / relative).read_bytes()
        ).hexdigest().upper()
        require(
            observed == expected,
            "frozen F2 owner changed: {}".format(relative),
        )


def _assert_frozen_owner_shapes() -> None:
    from tooling.build_artifact import CanonicalBuildArtifact
    from tooling.project_loader import LoadedProject
    from tooling.project_manifest import ProjectManifest

    require(
        tuple(field.name for field in dataclasses.fields(CanonicalBuildArtifact))
        == (
            "content",
            "entry",
            "fingerprint",
            "source_count",
            "narrative_artifact",
        ),
        "CanonicalBuildArtifact fields changed in F3",
    )
    require(
        tuple(field.name for field in dataclasses.fields(LoadedProject))
        == ("root", "manifest_path", "manifest", "sources", "project_kind"),
        "LoadedProject fields changed in F3",
    )
    require(
        tuple(field.name for field in dataclasses.fields(ProjectManifest))
        == ("name", "sources", "entry", "schema", "package"),
        "ProjectManifest fields changed in F3",
    )
    require(
        str(inspect.signature(cli._run_project))
        == "(path: 'str', *, stdout: 'TextIO') -> 'int'",
        "_run_project signature changed",
    )
    require(
        str(inspect.signature(cli._run_check))
        == (
            "(path: 'str', *, stdout: 'TextIO', "
            "builder: 'Optional[ProjectBuilder]', "
            "styler: 'Optional[Any]' = None) -> 'int'"
        ),
        "_run_check signature changed",
    )
    require(
        str(inspect.signature(cli._run_build))
        == (
            "(path: 'str', output_path: 'str', entry: 'Optional[str]', *, "
            "stdout: 'TextIO', builder: 'Optional[ProjectBuilder]' = None, "
            "styler: 'Optional[Any]' = None) -> 'int'"
        ),
        "_run_build signature changed",
    )


def _write_package_fixture(root: Path) -> bytes:
    exact = (
        b"@apexdoc Exec\n"
        b"@block apex run\n"
        b"directive Main {}\n"
        b"@endblock\n"
    )
    (root / "exec.apexdoc").write_bytes(exact)
    (root / "apexforge.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": "F3Package",
                "sources": ["exec.apexdoc"],
                "entry": None,
                "package": {
                    "id": "f3-package",
                    "tier": "domain",
                    "version": "1",
                    "documents": ["exec.apexdoc"],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return exact


def _invoke(arguments, *, builder=None):
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = cli.main(
        arguments,
        stdout=stdout,
        stderr=stderr,
        project_builder=builder,
    )
    return exit_code, stdout.getvalue(), stderr.getvalue()


def _assert_project_command_remains_presentation_compatible() -> None:
    with TemporaryDirectory(prefix="apexforge-p11-13f3-project-") as temporary:
        root = Path(temporary)
        _write_package_fixture(root)

        exit_code, stdout, stderr = _invoke(("project", str(root)))

        expected = (
            "Project: F3Package\n"
            "Manifest: {}\n"
            "Root: {}\n"
            "Entry: <none>\n"
            "Sources: 1\n"
            "  exec.apexdoc\n"
        ).format(
            root / "apexforge.json",
            root,
        )
        require(exit_code == cli.EXIT_SUCCESS, "package project command failed")
        require(stdout == expected, "project package presentation changed")
        require(stderr == "", "project package command wrote stderr")


def _assert_package_check_routes_to_f2_without_project_builder() -> None:
    with TemporaryDirectory(prefix="apexforge-p11-13f3-check-") as temporary:
        root = Path(temporary)
        _write_package_fixture(root)

        calls = []

        def forbidden_builder(sources, entry):
            calls.append((sources, entry))
            raise AssertionError(
                "ordinary ProjectBuilder was invoked for a package project"
            )

        exit_code, stdout, stderr = _invoke(
            ("check", str(root)),
            builder=forbidden_builder,
        )

        require(
            exit_code == cli.EXIT_SUCCESS,
            "package check did not route through frozen F2 rich-document build",
        )
        require(calls == [], "package check invoked ordinary ProjectBuilder")
        require(
            stdout == "ApexForge check passed: F3Package (1 source(s)).\n",
            "package check success presentation changed",
        )
        require(stderr == "", "successful package check wrote stderr")


def _assert_package_build_routes_to_v3_artifact() -> None:
    with TemporaryDirectory(prefix="apexforge-p11-13f3-build-") as temporary:
        root = Path(temporary)
        exact = _write_package_fixture(root)
        first = root / "first.json"
        second = root / "second.json"

        calls = []

        def forbidden_builder(sources, entry):
            calls.append((sources, entry))
            raise AssertionError(
                "ordinary ProjectBuilder was invoked for a package project"
            )

        exit_code, stdout, stderr = _invoke(
            ("build", str(root), "--output", str(first)),
            builder=forbidden_builder,
        )
        require(
            exit_code == cli.EXIT_SUCCESS,
            "package build did not route through frozen F2 rich-document artifact",
        )
        require(calls == [], "package build invoked ordinary ProjectBuilder")
        require(stderr == "", "successful package build wrote stderr")
        require(first.is_file(), "package build artifact was not written")

        first_bytes = first.read_bytes()
        value = json.loads(first_bytes.decode("utf-8"))
        require(
            value["schema"] == BUILD_ARTIFACT_SCHEMA_V3,
            "package build did not emit build-artifact/v3",
        )
        require(
            frozenset(value)
            == frozenset(
                ("fingerprint", "package", "project", "rich_documents", "schema")
            ),
            "package build v3 top-level shape changed",
        )
        require("air" not in value, "package build synthesized top-level AIR")
        require(
            "narrative" not in value,
            "package build synthesized narrative material",
        )
        require(
            value["package"]
            == {
                "id": "f3-package",
                "tier": "domain",
                "version": "1",
                "documents": ["exec.apexdoc"],
            },
            "package build metadata changed",
        )
        require(
            value["project"]["name"] == "F3Package"
            and value["project"]["entry"] is None
            and value["project"]["source_count"] == 1
            and value["project"]["sources"]
            == [
                {
                    "path": "exec.apexdoc",
                    "sha256": hashlib.sha256(exact).hexdigest(),
                }
            ],
            "package build project provenance changed",
        )

        executable = value["rich_documents"]["executable_blocks"]
        require(
            len(executable) == 1,
            "package build lost executable Apex block",
        )
        require(
            executable[0]["document_id"] == "Exec"
            and executable[0]["block_id"] == "run"
            and executable[0]["text"] == "directive Main {}\n",
            "package build executable source lineage changed",
        )
        require(
            tuple(
                item["id"]
                for item in executable[0]["air"]["directives"]
            )
            == ("directive:Main",),
            "package build lost canonical executable AIR",
        )
        require(
            executable[0]["source_map"],
            "package build lost executable source-map provenance",
        )

        expected_stdout = (
            "ApexForge build succeeded: F3Package\n"
            "Schema: apexforge.build-artifact/v3\n"
            "Entry: <none>\n"
            "Sources: 1\n"
            "Fingerprint: sha256:{}\n"
            "Artifact written.\n"
        ).format(value["fingerprint"]["value"])
        require(
            stdout == expected_stdout,
            "package build success presentation changed",
        )

        second_exit, second_stdout, second_stderr = _invoke(
            ("build", str(root), "--output", str(second)),
            builder=forbidden_builder,
        )
        require(second_exit == cli.EXIT_SUCCESS, "repeat package build failed")
        require(second_stderr == "", "repeat package build wrote stderr")
        require(
            second.read_bytes() == first_bytes,
            "package CLI build artifact bytes are not deterministic",
        )
        require(
            second_stdout == stdout,
            "package CLI build stdout is not deterministic",
        )


def _assert_f3_scope_boundaries() -> None:
    source = inspect.getsource(cli)
    require(
        "PROJECT_KIND_RICH_DOCUMENT" not in source,
        "F3 introduced a rich-document project kind",
    )
    require(
        "package registry" not in source.casefold()
        and "lockfile" not in source.casefold()
        and "package signing" not in source.casefold(),
        "P14 package-manager behavior leaked into F3",
    )


def main() -> None:
    _assert_frozen_f2_baseline()
    _assert_frozen_owner_shapes()
    _assert_project_command_remains_presentation_compatible()
    _assert_package_check_routes_to_f2_without_project_builder()
    _assert_package_build_routes_to_v3_artifact()
    _assert_f3_scope_boundaries()

    print("P11_13F2_FREEZE_BASELINE=" + F2_FREEZE_COMMIT)
    print("F3_PRIMARY_MUTATION_OWNER=tooling.cli")
    print("PACKAGE_ROUTE_DISCRIMINATOR=manifest.package")
    print("PROJECT_COMMAND_PRESENTATION=UNCHANGED")
    print("PACKAGE_CHECK_PROJECT_BUILDER_INVOCATIONS=NONE")
    print("PACKAGE_BUILD_PROJECT_BUILDER_INVOCATIONS=NONE")
    print("PACKAGE_BUILD_SCHEMA=" + BUILD_ARTIFACT_SCHEMA_V3)
    print("PACKAGE_BUILD_TOP_LEVEL_AIR=NONE")
    print("PACKAGE_BUILD_NARRATIVE_MATERIAL=NONE")
    print("PACKAGE_EXECUTABLE_CANONICAL_AIR=PASS")
    print("PACKAGE_EXECUTABLE_SOURCE_MAP_PROVENANCE=PASS")
    print("PACKAGE_BUILD_DETERMINISM=PASS")
    print("CLI_PROJECT_KIND_EXPANSION=NONE")
    print("LOADED_PROJECT_MUTATION=NONE")
    print("PROJECT_MANIFEST_SCHEMA_MUTATION=NONE")
    print("PROJECT_BUILDER_MUTATION=NONE")
    print("RUNTIME_EXECUTION=OUT_OF_SCOPE")
    print("CACHE_INTEGRATION=OUT_OF_SCOPE")
    print("TAM_TAP_INTEGRATION=OUT_OF_SCOPE")
    print("REMOTE_REGISTRY_SOLVER_LOCKFILE_SIGNING=NONE")
    print("P11_13F3_CLI_PACKAGE_PROJECT_ROUTING_FINAL_ACCEPTANCE=PASS")
    print("P11_13F3_EXIT=0")


if __name__ == "__main__":
    main()