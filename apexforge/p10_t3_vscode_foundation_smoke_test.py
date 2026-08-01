"""AFP-P10-T3.1 VS Code extension-foundation smoke test."""

from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

from tooling.vscode_extension import (
    CANONICAL_VSCODE_ENGINE,
    CANONICAL_VSCODE_FOUNDATION_SHA256,
    CANONICAL_VSCODE_LANGUAGE_ID,
    CANONICAL_VSCODE_PACKAGE_NAME,
    CANONICAL_VSCODE_PACKAGE_VERSION,
    CANONICAL_VSCODE_PUBLISHER,
    CANONICAL_VSCODE_SOURCE_EXTENSION,
    P10_T3_VSCODE_FOUNDATION_VERSION,
    VSCODE_EXTENSION_FOUNDATION_SCHEMA,
    VSCODE_EXTENSION_KIND,
    VSCodeExtensionError,
    audit_vscode_extension,
    foundation_fingerprint,
    main as vscode_main,
)


EXPECTED_FOUNDATION_SHA256 = "2a8478ea163312d211556f35f8c2fa99fd16eb93db81f829c33d8d688fb685e2"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_extension_error(operation, message: str) -> VSCodeExtensionError:
    try:
        operation()
    except VSCodeExtensionError as error:
        require(error.code == "APX-VSCODE-001", "VS Code error code changed")
        return error
    raise AssertionError(message)


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    require(
        P10_T3_VSCODE_FOUNDATION_VERSION == "10-T3.1",
        "T3.1 version changed",
    )
    require(VSCODE_EXTENSION_FOUNDATION_SCHEMA == 1, "schema changed")
    require(
        VSCODE_EXTENSION_KIND == "apexforge.vscode-foundation",
        "foundation kind changed",
    )
    require(CANONICAL_VSCODE_PACKAGE_NAME == "apexforge-language", "name changed")
    require(CANONICAL_VSCODE_PACKAGE_VERSION == "0.1.0", "version changed")
    require(CANONICAL_VSCODE_PUBLISHER == "gravitas-studios", "publisher changed")
    require(CANONICAL_VSCODE_ENGINE == "^1.85.0", "engine changed")
    require(CANONICAL_VSCODE_LANGUAGE_ID == "apexforge", "language id changed")
    require(CANONICAL_VSCODE_SOURCE_EXTENSION == ".apex", "extension changed")

    repository_root = Path(__file__).resolve().parent.parent
    extension_root = repository_root / "editors" / "vscode-apexforge"
    audit = audit_vscode_extension(
        extension_root,
        repository_root=repository_root,
    )
    require(audit.language_id == "apexforge", "audit language id changed")
    require(audit.source_extension == ".apex", "audit source extension changed")
    require(
        audit.foundation_sha256 == EXPECTED_FOUNDATION_SHA256,
        "audit foundation hash changed",
    )
    require(
        CANONICAL_VSCODE_FOUNDATION_SHA256 == EXPECTED_FOUNDATION_SHA256,
        "declared foundation hash changed",
    )

    package = json.loads((extension_root / "package.json").read_text(encoding="utf-8"))
    configuration = json.loads(
        (extension_root / "language-configuration.json").read_text(encoding="utf-8")
    )
    require(
        foundation_fingerprint(package, configuration) == EXPECTED_FOUNDATION_SHA256,
        "foundation projection is not deterministic",
    )
    require("comments" not in configuration, "unsupported comment syntax appeared")

    stdout = StringIO()
    stderr = StringIO()
    code = vscode_main(
        (str(extension_root), "--check"),
        stdout=stdout,
        stderr=stderr,
    )
    require(code == 0, "standalone foundation check failed")
    require(stderr.getvalue() == "", "successful foundation check wrote stderr")
    require(
        "AFP-P10-T3.1 VS Code extension foundation check passed.\n"
        in stdout.getvalue(),
        "standalone check omitted success heading",
    )
    require(
        f"Foundation SHA-256: {EXPECTED_FOUNDATION_SHA256}\n"
        in stdout.getvalue(),
        "standalone check omitted foundation hash",
    )

    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        copied_extension = temporary_root / "editors" / "vscode-apexforge"
        copied_extension.parent.mkdir(parents=True)
        copytree(extension_root, copied_extension)
        copied_spec = temporary_root / "spec"
        copytree(repository_root / "spec", copied_spec)

        bad_package = json.loads(
            (copied_extension / "package.json").read_text(encoding="utf-8")
        )
        bad_package["contributes"]["languages"][0]["extensions"] = [".APEX"]
        write_json(copied_extension / "package.json", bad_package)
        require_extension_error(
            lambda: audit_vscode_extension(
                copied_extension,
                repository_root=temporary_root,
            ),
            "uppercase extension unexpectedly passed",
        )

        write_json(copied_extension / "package.json", package)
        bad_configuration = dict(configuration)
        bad_configuration["comments"] = {"lineComment": "#"}
        write_json(
            copied_extension / "language-configuration.json",
            bad_configuration,
        )
        require_extension_error(
            lambda: audit_vscode_extension(
                copied_extension,
                repository_root=temporary_root,
            ),
            "unsupported comments unexpectedly passed",
        )

    print("AFP-P10-T3.1 VS Code extension foundation smoke test passed.")
    print("Canonical .apex file recognition: PASS")
    print("ApexForge language ID and aliases: PASS")
    print("Bracket and auto-closing configuration: PASS")
    print("Four-space indentation contract: PASS")
    print("No-comment grammar boundary: PASS")
    print("Frozen T2 contract synchronization: PASS")
    print("Deterministic foundation fingerprint: PASS")
    print("Standalone package validator: PASS")


if __name__ == "__main__":
    main()