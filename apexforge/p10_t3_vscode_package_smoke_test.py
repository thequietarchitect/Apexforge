"""AFP-P10-T3.3 VS Code VSIX packaging and local-install smoke test."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from shutil import copytree
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from tooling.vscode_package import (
    CANONICAL_VSCODE_EXTENSION_ID,
    CANONICAL_VSCODE_PACKAGE_SHA256,
    CANONICAL_VSIX_FILENAME,
    MINIMUM_NODE_MAJOR,
    P10_T3_VSCODE_PACKAGE_VERSION,
    VSCODE_PACKAGE_KIND,
    VSCODE_PACKAGE_SCHEMA,
    VSCODE_VSCE_VERSION,
    VSCodePackageError,
    audit_vscode_package_source,
    audit_vscode_vsix,
    check_vscode_installation,
    install_vscode_extension,
    main as package_main,
    package_vscode_extension,
    packaging_fingerprint,
    parse_installed_extensions,
    vsce_package_command,
)


EXPECTED_PACKAGE_SHA256 = (
    "75a39c44354d4f647ab46cb6aba42adf00f5396c7563b1433ff2d93d66e9498c"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_package_error(operation, message: str) -> VSCodePackageError:
    try:
        operation()
    except VSCodePackageError as error:
        require(error.code == "APX-VSCODE-003", "package error code changed")
        return error
    raise AssertionError(message)


def _content_types() -> str:
    return """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="md" ContentType="text/markdown" />
  <Default Extension="xml" ContentType="text/xml" />
</Types>
"""


def _manifest() -> str:
    return """<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="en-US" Id="apexforge-language" Version="0.1.0" Publisher="gravitas-studios" />
    <DisplayName>ApexForge Language</DisplayName>
    <Description xml:space="preserve">ApexForge language support.</Description>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.85.0" />
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code" />
  </Installation>
  <Dependencies />
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
  </Assets>
</PackageManifest>
"""


def write_synthetic_vsix(
    extension_root: Path,
    destination: Path,
    *,
    omit: str = "",
    corrupt: str = "",
    extra_name: str = "",
) -> None:
    payload = {
        "extension/package.json": extension_root / "package.json",
        "extension/language-configuration.json": (
            extension_root / "language-configuration.json"
        ),
        "extension/readme.md": extension_root / "README.md",
        "extension/changelog.md": extension_root / "CHANGELOG.md",
        "extension/syntaxes/apexforge.tmLanguage.json": (
            extension_root / "syntaxes" / "apexforge.tmLanguage.json"
        ),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        if omit.casefold() != "[content_types].xml":
            archive.writestr("[Content_Types].xml", _content_types())
        if omit.casefold() != "extension.vsixmanifest":
            archive.writestr("extension.vsixmanifest", _manifest())
        for archive_name, source_path in payload.items():
            if archive_name.casefold() == omit.casefold():
                continue
            data = source_path.read_bytes()
            if archive_name.casefold() == corrupt.casefold():
                data += b"\ncorrupt"
            archive.writestr(archive_name, data)
        if extra_name:
            archive.writestr(extra_name, b"unexpected")


def main() -> None:
    require(
        P10_T3_VSCODE_PACKAGE_VERSION == "10-T3.3",
        "T3.3 version changed",
    )
    require(VSCODE_PACKAGE_SCHEMA == 1, "T3.3 schema changed")
    require(
        VSCODE_PACKAGE_KIND == "apexforge.vscode-package",
        "T3.3 kind changed",
    )
    require(VSCODE_VSCE_VERSION == "3.9.1", "pinned vsce version changed")
    require(MINIMUM_NODE_MAJOR == 20, "minimum Node.js major changed")
    require(
        CANONICAL_VSCODE_EXTENSION_ID
        == "gravitas-studios.apexforge-language",
        "extension ID changed",
    )
    require(
        CANONICAL_VSIX_FILENAME == "apexforge-language-0.1.0.vsix",
        "canonical VSIX filename changed",
    )

    repository_root = Path(__file__).resolve().parent.parent
    extension_root = repository_root / "editors" / "vscode-apexforge"

    observed = audit_vscode_package_source(
        extension_root,
        repository_root=repository_root,
    )
    require(observed == EXPECTED_PACKAGE_SHA256, "source audit hash changed")
    require(
        packaging_fingerprint(extension_root) == EXPECTED_PACKAGE_SHA256,
        "packaging fingerprint is not deterministic",
    )
    require(
        CANONICAL_VSCODE_PACKAGE_SHA256 == EXPECTED_PACKAGE_SHA256,
        "declared packaging hash changed",
    )

    command = vsce_package_command(
        "npx",
        Path("dist") / CANONICAL_VSIX_FILENAME,
    )
    require(command[0] == "npx", "npx command changed")
    require(command[1] == "--yes", "noninteractive npx flag changed")
    require(
        command[2] == "@vscode/vsce@3.9.1",
        "pinned official packager changed",
    )
    require("--no-dependencies" in command, "dependency exclusion omitted")
    require("--allow-missing-repository" in command, "repository override omitted")
    require("--skip-license" in command, "local-package license override omitted")
    require("--no-rewrite-relative-links" in command, "README byte preservation omitted")

    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        copied_extension = temporary_root / "editors" / "vscode-apexforge"
        copied_extension.parent.mkdir(parents=True)
        copytree(extension_root, copied_extension)
        copytree(repository_root / "spec", temporary_root / "spec")

        vsix = temporary_root / CANONICAL_VSIX_FILENAME
        write_synthetic_vsix(copied_extension, vsix)
        audit = audit_vscode_vsix(
            copied_extension,
            vsix,
            repository_root=temporary_root,
        )
        require(audit.extension_id == CANONICAL_VSCODE_EXTENSION_ID, "VSIX ID changed")
        require(audit.package_version == "0.1.0", "VSIX version changed")
        require(audit.archive_file_count == 7, "VSIX file count changed")
        require(audit.payload_sha256 == EXPECTED_PACKAGE_SHA256, "payload hash changed")
        require(len(audit.vsix_sha256) == 64, "VSIX artifact hash missing")

        bad_vsix = temporary_root / "missing.vsix"
        write_synthetic_vsix(
            copied_extension,
            bad_vsix,
            omit="extension/syntaxes/apexforge.tmLanguage.json",
        )
        require_package_error(
            lambda: audit_vscode_vsix(
                copied_extension,
                bad_vsix,
                repository_root=temporary_root,
            ),
            "missing syntax payload unexpectedly passed",
        )

        bad_vsix = temporary_root / "corrupt.vsix"
        write_synthetic_vsix(
            copied_extension,
            bad_vsix,
            corrupt="extension/package.json",
        )
        require_package_error(
            lambda: audit_vscode_vsix(
                copied_extension,
                bad_vsix,
                repository_root=temporary_root,
            ),
            "corrupted package payload unexpectedly passed",
        )

        bad_vsix = temporary_root / "node-modules.vsix"
        write_synthetic_vsix(
            copied_extension,
            bad_vsix,
            extra_name="extension/node_modules/hidden.js",
        )
        require_package_error(
            lambda: audit_vscode_vsix(
                copied_extension,
                bad_vsix,
                repository_root=temporary_root,
            ),
            "node_modules payload unexpectedly passed",
        )

        bad_vsix = temporary_root / "traversal.vsix"
        write_synthetic_vsix(
            copied_extension,
            bad_vsix,
            extra_name="../outside.txt",
        )
        require_package_error(
            lambda: audit_vscode_vsix(
                copied_extension,
                bad_vsix,
                repository_root=temporary_root,
            ),
            "path traversal unexpectedly passed",
        )

        copied_ignore = copied_extension / ".vscodeignore"
        copied_ignore.write_text(copied_ignore.read_text() + "dist/**\n")
        require_package_error(
            lambda: audit_vscode_package_source(
                copied_extension,
                repository_root=temporary_root,
            ),
            "ignore-policy drift unexpectedly passed",
        )
        copied_ignore.write_text(
            ".vscode/**\n.git/**\nnode_modules/**\npackage-lock.json\n*.vsix\n",
            encoding="utf-8",
        )

        runner_calls: list[tuple[str, ...]] = []

        def package_runner(command, **kwargs):
            normalized = tuple(str(item) for item in command)
            runner_calls.append(normalized)
            if normalized[1:] == ("--version",):
                return subprocess.CompletedProcess(normalized, 0, "v22.16.0\n", "")
            if normalized[1] == "--yes":
                destination = Path(normalized[-1])
                write_synthetic_vsix(copied_extension, destination)
                return subprocess.CompletedProcess(normalized, 0, "packaged\n", "")
            raise AssertionError(f"unexpected package command: {normalized!r}")

        packaged_path = temporary_root / "built" / CANONICAL_VSIX_FILENAME
        packaged = package_vscode_extension(
            copied_extension,
            packaged_path,
            repository_root=temporary_root,
            runner=package_runner,
            node_command="node",
            npx_command="npx",
        )
        require(packaged.vsix_path == packaged_path.resolve(), "packaged path changed")
        require(len(runner_calls) == 2, "packaging command count changed")

        install_calls: list[tuple[str, ...]] = []

        def code_runner(command, **kwargs):
            normalized = tuple(str(item) for item in command)
            install_calls.append(normalized)
            if "--install-extension" in normalized:
                return subprocess.CompletedProcess(normalized, 0, "installed\n", "")
            if "--list-extensions" in normalized:
                stdout = (
                    "someone.other@2.0.0\n"
                    "gravitas-studios.apexforge-language@0.1.0\n"
                )
                return subprocess.CompletedProcess(normalized, 0, stdout, "")
            raise AssertionError(f"unexpected code command: {normalized!r}")

        installed = install_vscode_extension(
            copied_extension,
            packaged_path,
            repository_root=temporary_root,
            code_command="code",
            runner=code_runner,
        )
        require(installed.package_version == "0.1.0", "installed version changed")
        require(len(install_calls) == 2, "install verification count changed")
        require("--force" in install_calls[0], "forced local update omitted")

        checked = check_vscode_installation(
            code_command="code",
            runner=code_runner,
        )
        require(checked.extension_id == CANONICAL_VSCODE_EXTENSION_ID, "installed ID changed")

        parsed = parse_installed_extensions(
            "GRAVITAS-STUDIOS.APEXFORGE-LANGUAGE@0.1.0\n"
        )
        require(
            parsed[CANONICAL_VSCODE_EXTENSION_ID] == "0.1.0",
            "installed-list case normalization changed",
        )

        stdout = StringIO()
        stderr = StringIO()
        exit_code = package_main(
            (str(copied_extension), "--check-vsix", str(packaged_path)),
            stdout=stdout,
            stderr=stderr,
        )
        require(exit_code == 0, "standalone VSIX check failed")
        require(stderr.getvalue() == "", "successful VSIX check wrote stderr")
        require(
            "AFP-P10-T3.3 VS Code VSIX audit passed.\n" in stdout.getvalue(),
            "standalone audit omitted success heading",
        )
        require(
            f"Payload SHA-256: {EXPECTED_PACKAGE_SHA256}\n" in stdout.getvalue(),
            "standalone audit omitted payload hash",
        )

    print("AFP-P10-T3.3 VS Code packaging and local-install smoke test passed.")
    print("Frozen T3.1/T3.2 contract preservation: PASS")
    print("Pinned official @vscode/vsce command: PASS")
    print("Deterministic source-payload fingerprint: PASS")
    print("VSIX archive safety and inventory: PASS")
    print("Embedded package and manifest identity: PASS")
    print("Canonical payload byte equality: PASS")
    print("Forbidden build-artifact exclusion: PASS")
    print("Local install command and version verification: PASS")
    print("Standalone VSIX audit: PASS")


if __name__ == "__main__":
    main()
