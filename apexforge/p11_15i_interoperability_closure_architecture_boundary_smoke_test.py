"""P11.15I interoperability closure architecture boundary.

Architecture-only.  This stage closes P11.15 after the post-integration census
proved that no further concrete interoperability production pressure remains.
"""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APEX = ROOT / "apexforge"
sys.path.insert(0, str(APEX))

EXPECTED_H_FREEZE = "7c9b0c7d5d350a3c3c736a0d8c3e3d817d01d557"
EXPECTED_H_TAG = "afp-p11-15h-freeze"
EXPECTED_BRANCH = "p11-15i-interoperability-closure-architecture-boundary"

SESSION_PATH = APEX / "tooling" / "narrative_session.py"
EXECUTION_PATH = APEX / "tooling" / "narrative_execution.py"

EXPECTED_H_SESSION_BLOB = (
    "E5C41F8327DBD7A94A71FF6A6FB1B6D7A08AF9257C80B1ACC6450554E27890B3"
)
EXPECTED_F_EXECUTION_BLOB = (
    "80D31EB2AB98A71237230474AA5DDF1242BF4E25EC0EF0CF6327A02ED6A2F4A9"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str, binary: bool = False):
    proc = subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not binary,
        check=False,
    )
    if proc.returncode != 0:
        err = (
            proc.stderr.decode("utf-8", "replace")
            if binary
            else proc.stderr
        )
        raise AssertionError(
            "git failed: git {}\n{}".format(" ".join(args), err)
        )
    return proc.stdout


def production_python_files():
    for path in sorted(APEX.rglob("*.py")):
        name = path.name
        if "__pycache__" in path.parts:
            continue
        if re.match(r"p\d+_", name):
            continue
        if "smoke_test" in name:
            continue
        yield path, path.relative_to(ROOT).as_posix()


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def main() -> int:
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_H_FREEZE,
        "P11.15I must remain architecture-only on exact H freeze",
    )
    require(
        git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "unexpected P11.15I closure branch",
    )
    require(
        git("cat-file", "-t", EXPECTED_H_TAG).strip() == "tag",
        "P11.15H freeze tag must remain annotated",
    )
    require(
        git("rev-parse", EXPECTED_H_TAG + "^{commit}").strip()
        == EXPECTED_H_FREEZE,
        "P11.15H freeze tag target changed",
    )

    require(
        sha256(
            git(
                "show",
                "HEAD:apexforge/tooling/narrative_session.py",
                binary=True,
            )
        )
        == EXPECTED_H_SESSION_BLOB,
        "H narrative-session production blob changed during I closure",
    )
    require(
        sha256(
            git(
                "show",
                "HEAD:apexforge/tooling/narrative_execution.py",
                binary=True,
            )
        )
        == EXPECTED_F_EXECUTION_BLOB,
        "F narrative-execution production blob changed during I closure",
    )

    d_importers = []
    d_callers = []
    b_inspector_importers = []
    b_inspector_callers = []
    interchange_importers = []
    interchange_constructors = []
    duplicated_reader_verifiers = []
    generic_readers = []

    files = list(production_python_files())

    for path, rel in files:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))

        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = {alias.name for alias in node.names}
                if (
                    module == "interoperability.build_artifact_integrity"
                    and "verify_build_artifact_interchange_fingerprint" in names
                ):
                    d_importers.append(rel)
                if (
                    module == "interoperability.build_artifact"
                    and "inspect_build_artifact_interchange" in names
                ):
                    b_inspector_importers.append(rel)
                if (
                    module == "interoperability.build_artifact"
                    and "BuildArtifactInterchange" in names
                ):
                    interchange_importers.append(rel)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            else:
                continue

            if name == "verify_build_artifact_interchange_fingerprint":
                d_callers.append(rel)
            elif name == "inspect_build_artifact_interchange":
                b_inspector_callers.append(rel)
            elif name == "BuildArtifactInterchange":
                interchange_constructors.append(rel)

        if rel not in (
            "apexforge/tooling/build_artifact.py",
            "apexforge/interoperability/build_artifact_integrity.py",
        ):
            has_dup = (
                "BUILD_ARTIFACT_FINGERPRINT_ALGORITHM" in source
                and "canonical_json_bytes" in source
                and (
                    'del payload["fingerprint"]' in source
                    or (
                        "payload.pop(" in source
                        and "fingerprint" in source
                    )
                )
                and "sha256" in source
            )
            if has_dup:
                duplicated_reader_verifiers.append(rel)

        exact_outer_names = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
            and node.id in (
                "BUILD_ARTIFACT_SCHEMA",
                "BUILD_ARTIFACT_SCHEMA_V2",
                "BUILD_ARTIFACT_SCHEMA_V3",
            )
        }
        if exact_outer_names and (
            "json.loads(" in source
            or "json.load(" in source
            or ".read_bytes()" in source
            or ".read_text(" in source
        ):
            generic_readers.append(rel)

    d_importers = sorted(set(d_importers))
    d_callers = sorted(set(d_callers))
    b_inspector_importers = sorted(set(b_inspector_importers))
    b_inspector_callers = sorted(set(b_inspector_callers))
    interchange_importers = sorted(set(interchange_importers))
    interchange_constructors = sorted(set(interchange_constructors))
    duplicated_reader_verifiers = sorted(set(duplicated_reader_verifiers))
    generic_readers = sorted(set(generic_readers))

    expected_consumers = {
        "apexforge/tooling/narrative_execution.py",
        "apexforge/tooling/narrative_session.py",
    }
    interchange_owner = "apexforge/interoperability/build_artifact.py"
    downstream_constructors = sorted(
        set(interchange_constructors) - {interchange_owner}
    )

    require(set(d_importers) == expected_consumers, "D importers changed")
    require(set(d_callers) == expected_consumers, "D callers changed")
    require(
        set(interchange_importers) == expected_consumers,
        "interchange importers changed",
    )
    require(
        set(downstream_constructors) == expected_consumers,
        "downstream interchange constructors changed",
    )
    require(
        interchange_owner in interchange_constructors,
        "interchange owner construction disappeared",
    )
    require(
        not b_inspector_importers and not b_inspector_callers,
        "B inspector acquired production consumers",
    )
    require(
        not duplicated_reader_verifiers,
        "duplicated reader-side fingerprint verification remains",
    )

    allowed_readers = {
        "apexforge/interoperability/build_artifact.py",
        "apexforge/tooling/build_artifact.py",
        "apexforge/tooling/narrative_execution.py",
        "apexforge/tooling/narrative_session.py",
    }
    unexpected_readers = sorted(set(generic_readers) - allowed_readers)
    require(
        not unexpected_readers,
        "unexpected generic build-artifact reader pressure remains",
    )

    print("P11_15I_PRODUCTION_PYTHON_FILES={}".format(len(files)))
    print("P11_15I_SCOPE=ARCHITECTURE_ONLY_CLOSURE")
    print("P11_15I_PRODUCTION_FILES=0")
    print("P11_15I_CONCRETE_D_CONSUMERS=F_EXECUTION_H_SESSION_ONLY")
    print("P11_15I_INTERCHANGE_OWNER_CONSTRUCTION=EXPECTED")
    print("P11_15I_B_INSPECTOR_PRODUCTION_CONSUMERS=NONE")
    print("P11_15I_DUPLICATED_OUTER_FINGERPRINT_VERIFICATION=NONE")
    print("P11_15I_UNEXPECTED_GENERIC_BUILD_ARTIFACT_READERS=NONE")
    print("P11_15I_GENERIC_LOADER_RECONSTRUCTION=NOT_JUSTIFIED")
    print("P11_15I_SCHEMA_MIGRATION=NOT_JUSTIFIED")
    print("P11_15I_FILE_PATH_INTEROPERABILITY_LOADER=NOT_JUSTIFIED")
    print("P11_15I_NETWORK_RPC=NOT_JUSTIFIED")
    print("P11_15I_FFI_NATIVE_ABI=DEFER_TO_P12_OR_CONCRETE_CONSUMER")
    print("P11_15I_PACKAGE_REGISTRY_DISTRIBUTION=DEFERRED")
    print("P11_15I_INTEROPERABILITY_PRODUCTION_SCOPE=COMPLETE")
    print("P11_15I_FUTURE_J_K_ETC=NOT_JUSTIFIED_WITHOUT_NEW_EVIDENCE")
    print("P11_15I_SUCCESSOR=P11_16_FINAL_VERIFICATION")
    print("P11_15I_INTEROPERABILITY_CLOSURE_ARCHITECTURE_BOUNDARY=PASS")
    print("P11_15I_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())