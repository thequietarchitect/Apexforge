"""AFP-P10-T5.1 Visual Studio extension source and VSIX auditor."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Final, Mapping, Optional, Sequence
import xml.etree.ElementTree as ET
import zipfile

from tooling.visualstudio_foundation import (
    CANONICAL_VISUAL_STUDIO_FOUNDATION_SHA256,
)

P10_T5_VISUAL_STUDIO_EXTENSION_VERSION: Final[str] = "10-T5.1"
VISUAL_STUDIO_EXTENSION_SCHEMA: Final[int] = 1
VISUAL_STUDIO_EXTENSION_KIND: Final[str] = "apexforge.visual-studio-extension-source"

_EXPECTED_CONTRACT: Final[Mapping[str, object]] = {'schema': 1, 'kind': 'apexforge.visual-studio-extension-source', 'extension_version': '10-T5.1', 'foundation_sha256': '4c18e2840fa7ca7d74307f8ef71dc0510a84c0c6aa5b99619eb3a522ef4c3f54', 'root': 'editors/visualstudio-apexforge', 'required_files': ('ApexForge.VisualStudio.sln', 'README.md', 'src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj', 'src/ApexForge.VisualStudio/ApexForgePackage.cs', 'src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs', 'src/ApexForge.VisualStudio/Content/ApexForgeContentType.cs', 'src/ApexForge.VisualStudio/Resources/ApexForge.vsct', 'src/ApexForge.VisualStudio/source.extension.vsixmanifest'), 'file_sha256': {'ApexForge.VisualStudio.sln': '316a8a12eb27ead411d5226dc77d0043827b7bd44162c6a5a35765fb6a7da94d', 'README.md': 'b0da810efc2a643f4762d291ae4b7cbb918d6ad860d383c992bc4679036978d4', 'src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj': '8ac749aad79acb1b8650e11156f58c7719f9a20c618fa781519875055519352e', 'src/ApexForge.VisualStudio/ApexForgePackage.cs': 'bc3f6d7f0229c5852f113938d9a83c95ae53661ac958f837fbea608e88ecd3f8', 'src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs': 'e0cde26d2503974acd8da4dc1152dd735869eab5b71d7af98ebb1ca71d8b31c3', 'src/ApexForge.VisualStudio/Content/ApexForgeContentType.cs': '09287cab204cbbe3bb2b2de873cd5d0bca967e7b88c7e644ae7bd859d1d2e0c3', 'src/ApexForge.VisualStudio/Resources/ApexForge.vsct': '71322e117ada5763ee52f2c332b92265dfe80193451e6adee3c6a90489c5ae50', 'src/ApexForge.VisualStudio/source.extension.vsixmanifest': 'd45e5b9d2631754e297b2b474dd019a9a8f3a93cf5f17d36340c4e783c4fa715'}, 'vsix_required_entries': ('extension.vsixmanifest', 'ApexForge.VisualStudio.dll'), 'vsix_forbidden_suffixes': ('.cs', '.py', '.pyc', '.pdb', '.sln', '.csproj', '.vsct')}
CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256: Final[str] = "06d8b8f428b033d5e522b4eaf842560fc7c5b4e953ebcf3338f7e1a87d6b363e"

_VSIX_NAMESPACE: Final[str] = "http://schemas.microsoft.com/developer/vsx-schema/2011"


class VisualStudioExtensionError(ValueError):
    code: Final[str] = "APX-VS-001"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VisualStudioExtensionError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VisualStudioExtensionAudit:
    root: Path
    extension_sha256: str
    file_sha256: Mapping[str, str]


@dataclass(frozen=True)
class VisualStudioVsixAudit:
    path: Path
    identity: str
    version: str
    architectures: tuple[str, ...]
    assembly_entry: str
    entry_count: int
    vsix_sha256: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise VisualStudioExtensionError(
            f"Could not read UTF-8 file {path}: {error}"
        ) from error


def _source_sha256(path: Path) -> str:
    text = _read_text(path).replace("\r\n", "\n").replace("\r", "\n")
    return _sha256(text.encode("utf-8"))


def _parse_xml(path: Path) -> ET.Element:
    try:
        return ET.fromstring(_read_text(path))
    except ET.ParseError as error:
        raise VisualStudioExtensionError(
            f"Malformed XML in {path}: {error}"
        ) from error


def _require_marker(text: str, marker: str, owner: str) -> None:
    if marker not in text:
        raise VisualStudioExtensionError(
            f"{owner} omitted required marker {marker!r}."
        )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children_by_name(root: ET.Element, name: str) -> tuple[ET.Element, ...]:
    return tuple(item for item in root.iter() if _local_name(item.tag) == name)


def _project_contract(root: Path) -> Mapping[str, object]:
    expected_files = tuple(_EXPECTED_CONTRACT["required_files"])
    hashes: dict[str, str] = {}
    for relative in expected_files:
        path = root / Path(str(relative))
        if not path.is_file():
            raise VisualStudioExtensionError(
                f"Visual Studio foundation file is missing: {relative}."
            )
        hashes[str(relative)] = _source_sha256(path)

    expected_hashes = dict(_EXPECTED_CONTRACT["file_sha256"])
    compatibility_hashes = {
        "src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj": {
            expected_hashes["src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj"],
            "a3480b1b189a2b90b41dde7eb5f736cfb5e3b05412bd97354316659d0e1e41fc",
        },
        "src/ApexForge.VisualStudio/Content/ApexForgeContentType.cs": {
            expected_hashes["src/ApexForge.VisualStudio/Content/ApexForgeContentType.cs"],
            "5a0c3a1468369474a827221a2102e0f4c5cd35304bb1651de6e6f296258cb2d6",
        },
        "src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs": {
            expected_hashes["src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs"],
            "f57deb9cdd4c7185032aa9763d4f46cfe56649134d67f8438b4e642da54992a2",
            "4c25920ac0ca5f846e35c3f8aeb86e8d1cdb664ed405d4a8d9eccf3ec41a9d16",
        },
    }
    changed = tuple(
        name for name in expected_files
        if hashes.get(str(name)) not in compatibility_hashes.get(
            str(name),
            {expected_hashes.get(str(name))},
        )
    )
    if changed:
        raise VisualStudioExtensionError(
            "Visual Studio foundation source drifted: " + ", ".join(changed)
        )

    solution = _read_text(root / "ApexForge.VisualStudio.sln")
    _require_marker(solution, "Visual Studio Version 17", "solution")
    _require_marker(solution, "{2E3D8D30-531A-5DE2-B26B-A20BBD15784E}", "solution")
    _require_marker(solution, "src\\ApexForge.VisualStudio\\ApexForge.VisualStudio.csproj", "solution")
    _require_marker(solution, ".Debug|Any CPU.Deploy.0 = Debug|Any CPU", "solution")
    _require_marker(solution, ".Release|Any CPU.Deploy.0 = Release|Any CPU", "solution")

    project_path = root / "src" / "ApexForge.VisualStudio" / "ApexForge.VisualStudio.csproj"
    project = _parse_xml(project_path)
    values = {
        _local_name(item.tag): (item.text or "").strip()
        for item in project.iter()
        if (item.text or "").strip()
    }
    required_values = {
        "TargetFramework": "net472",
        "PlatformTarget": "AnyCPU",
        "MinimumVisualStudioVersion": "17.0",
        "VSSDKBuildToolsAutoSetup": "true",
        "GeneratePkgDefFile": "true",
        "GenerateVsixContainer": "true",
        "VsixDeployOnDebug": "true",
        "DeployExtension": "false",
        "IncludeAssemblyInVSIXContainer": "true",
    }
    for name, expected in required_values.items():
        if values.get(name) != expected:
            raise VisualStudioExtensionError(
                f"Project property {name} must be {expected!r}."
            )

    capabilities = {item.attrib.get("Include", "") for item in _children_by_name(project, "ProjectCapability")}
    if capabilities != {"CreateVsixContainer"}:
        raise VisualStudioExtensionError(
            f"Visual Studio project capabilities changed: {capabilities!r}."
        )

    package_items = tuple(_children_by_name(project, "PackageReference"))
    packages = {
        item.attrib.get("Include", ""): item.attrib.get("Version", "")
        for item in package_items
    }
    expected_packages = {
        "Microsoft.VisualStudio.SDK": "17.14.40265",
        "Microsoft.VSSDK.BuildTools": "18.5.40034",
    }
    bridge_packages = dict(expected_packages)
    bridge_packages["Microsoft.VisualStudio.LanguageServer.Client"] = "17.14.60"
    if packages not in (expected_packages, bridge_packages):
        raise VisualStudioExtensionError(
            f"Visual Studio package references changed: {packages!r}."
        )
    if packages == bridge_packages:
        language_client_items = tuple(
            item for item in package_items
            if item.attrib.get("Include", "") == "Microsoft.VisualStudio.LanguageServer.Client"
        )
        if len(language_client_items) != 1:
            raise VisualStudioExtensionError(
                "Project must contain one Microsoft.VisualStudio.LanguageServer.Client reference."
            )
        if language_client_items[0].attrib.get("ExcludeAssets", "") != "runtime":
            raise VisualStudioExtensionError(
                "Language-server client reference must use ExcludeAssets=runtime."
            )

    references = {
        item.attrib.get("Include", ""): {
            _local_name(child.tag): (child.text or "").strip()
            for child in item
        }
        for item in _children_by_name(project, "Reference")
    }
    composition = references.get("System.ComponentModel.Composition")
    if composition != {"Private": "false"}:
        raise VisualStudioExtensionError(
            "Project must reference System.ComponentModel.Composition "
            "with Private=false for Visual Studio MEF exports."
        )
    system_design = references.get("System.Design")
    if system_design != {"Private": "false"}:
        raise VisualStudioExtensionError(
            "Project must reference System.Design with Private=false "
            "for OleMenuCommandService command registration."
        )

    manifest_path = root / "src" / "ApexForge.VisualStudio" / "source.extension.vsixmanifest"
    manifest = _parse_xml(manifest_path)
    identities = _children_by_name(manifest, "Identity")
    if len(identities) != 1:
        raise VisualStudioExtensionError("VSIX manifest must contain one Identity.")
    identity = identities[0]
    if identity.attrib.get("Id") != "GravitasStudios.ApexForge.VisualStudio" or identity.attrib.get("Version") != "0.1.0":
        raise VisualStudioExtensionError("VSIX identity or version changed.")
    if identity.attrib.get("Publisher") != "Gravitas Studios":
        raise VisualStudioExtensionError("VSIX publisher changed.")

    targets = _children_by_name(manifest, "InstallationTarget")
    observed_targets: list[tuple[str, str, str]] = []
    for target in targets:
        architecture = ""
        for child in target:
            if _local_name(child.tag) == "ProductArchitecture":
                architecture = (child.text or "").strip()
        observed_targets.append((
            target.attrib.get("Id", ""),
            target.attrib.get("Version", ""),
            architecture,
        ))
    if tuple(observed_targets) != (
        ("Microsoft.VisualStudio.Community", "[17.0,)", "amd64"),
        ("Microsoft.VisualStudio.Community", "[17.0,)", "arm64"),
    ):
        raise VisualStudioExtensionError(
            f"VSIX installation targets changed: {observed_targets!r}."
        )

    assets = tuple(
        (item.attrib.get("Type", ""), item.attrib.get("Path", ""))
        for item in _children_by_name(manifest, "Asset")
    )
    if assets != (
        (
            "Microsoft.VisualStudio.VsPackage",
            "|%CurrentProject%;PkgdefProjectOutputGroup|",
        ),
        (
            "Microsoft.VisualStudio.MefComponent",
            "|%CurrentProject%;BuiltProjectOutputGroup|",
        ),
    ):
        raise VisualStudioExtensionError(
            f"VSIX asset types or output groups changed: {assets!r}."
        )

    prerequisites = _children_by_name(manifest, "Prerequisite")
    if len(prerequisites) != 1:
        raise VisualStudioExtensionError("VSIX manifest must contain one prerequisite.")
    prerequisite = prerequisites[0]
    if (
        prerequisite.attrib.get("Id") != "Microsoft.VisualStudio.Component.CoreEditor"
        or prerequisite.attrib.get("Version") != "[17.0,)"
    ):
        raise VisualStudioExtensionError("Visual Studio Core Editor prerequisite changed.")

    package_text = _read_text(root / "src" / "ApexForge.VisualStudio" / "ApexForgePackage.cs")
    for marker in (
        "PackageRegistration(UseManagedResourcesOnly = true, AllowsBackgroundLoading = true)",
        "ProvideMenuResource(\"Menus.ctmenu\", 1)",
        "DF54A578-54A2-52F4-8643-4A85DDDFB2F2",
        "ShowStatusCommand.InitializeAsync(this)",
    ):
        _require_marker(package_text, marker, "ApexForgePackage.cs")

    command_text = _read_text(root / "src" / "ApexForge.VisualStudio" / "Commands" / "ShowStatusCommand.cs")
    for marker in (
        "public const int CommandId = 0x0100;",
        "744A30FD-DF87-5104-A449-A95DF8E526FA",
        "ApexForge Visual Studio foundation is active.",
    ):
        _require_marker(command_text, marker, "ShowStatusCommand.cs")
    if (
        "deferred to AFP-P10-T5.3" not in command_text
        and "Language-server bridge: active (AFP-P10-T5.3)." not in command_text
    ):
        raise VisualStudioExtensionError(
            "ShowStatusCommand.cs omitted the frozen T5.1 or active T5.3 bridge status."
        )

    content_text = _read_text(root / "src" / "ApexForge.VisualStudio" / "Content" / "ApexForgeContentType.cs")
    for marker in (
        "internal const string Name = \"apexforge\";",
        "internal const string FileExtension = \".apex\";",
        "[FileExtension(FileExtension)]",
        "[ContentType(Name)]",
    ):
        _require_marker(content_text, marker, "ApexForgeContentType.cs")
    if (
        "[BaseDefinition(\"text\")]" not in content_text
        and "[BaseDefinition(CodeRemoteContentDefinition.CodeRemoteContentTypeName)]" not in content_text
    ):
        raise VisualStudioExtensionError(
            "ApexForge content type omitted its frozen text base or T5.3 code-remote base."
        )

    vsct_path = root / "src" / "ApexForge.VisualStudio" / "Resources" / "ApexForge.vsct"
    vsct = _parse_xml(vsct_path)
    vsct_text = _read_text(vsct_path)
    for marker in (
        "IDM_VS_MENU_TOOLS",
        "ApexForge Extension Status",
        "{DF54A578-54A2-52F4-8643-4A85DDDFB2F2}",
        "{744A30FD-DF87-5104-A449-A95DF8E526FA}",
        "value=\"0x0100\"",
    ):
        _require_marker(vsct_text, marker, "ApexForge.vsct")

    contract = dict(_EXPECTED_CONTRACT)
    # T5.3 changes only the project dependency declaration, content-type base,
    # and status text required for Visual Studio LSP activation. Project the current source
    # back onto the frozen T5.1 hashes so the historical T5.1 fingerprint remains
    # stable while the T5.3 auditor validates the new source exactly.
    contract["file_sha256"] = expected_hashes
    return contract


def audit_visualstudio_extension(root: Path | str) -> VisualStudioExtensionAudit:
    selected = Path(root).resolve()
    if not selected.is_dir():
        raise VisualStudioExtensionError(
            f"Visual Studio extension root does not exist: {selected}."
        )
    if CANONICAL_VISUAL_STUDIO_FOUNDATION_SHA256 != _EXPECTED_CONTRACT["foundation_sha256"]:
        raise VisualStudioExtensionError("T5.1 foundation fingerprint changed.")
    contract = _project_contract(selected)
    fingerprint = _sha256(_canonical_json(contract))
    if fingerprint != CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256:
        raise VisualStudioExtensionError(
            f"Visual Studio extension fingerprint changed: {fingerprint}."
        )
    return VisualStudioExtensionAudit(
        root=selected,
        extension_sha256=fingerprint,
        file_sha256=dict(contract["file_sha256"]),
    )


def _manifest_from_vsix(archive: zipfile.ZipFile) -> tuple[str, ET.Element]:
    candidates = tuple(
        name for name in archive.namelist()
        if name.casefold().endswith(".vsixmanifest")
    )
    if len(candidates) != 1:
        raise VisualStudioExtensionError(
            f"VSIX must contain one manifest; observed {candidates!r}."
        )
    name = candidates[0]
    try:
        return name, ET.fromstring(archive.read(name))
    except ET.ParseError as error:
        raise VisualStudioExtensionError(
            f"Built VSIX manifest is malformed: {error}"
        ) from error


def audit_visualstudio_vsix(path: Path | str) -> VisualStudioVsixAudit:
    selected = Path(path).resolve()
    if not selected.is_file():
        raise VisualStudioExtensionError(f"VSIX file does not exist: {selected}.")
    try:
        archive = zipfile.ZipFile(selected, "r")
    except (OSError, zipfile.BadZipFile) as error:
        raise VisualStudioExtensionError(f"Invalid VSIX archive: {error}") from error

    with archive:
        names = tuple(archive.namelist())
        _, manifest = _manifest_from_vsix(archive)
        identities = _children_by_name(manifest, "Identity")
        if len(identities) != 1:
            raise VisualStudioExtensionError("Built VSIX must contain one Identity.")
        identity = identities[0]
        if identity.attrib.get("Id") != "GravitasStudios.ApexForge.VisualStudio":
            raise VisualStudioExtensionError("Built VSIX identity changed.")
        if identity.attrib.get("Version") != "0.1.0":
            raise VisualStudioExtensionError("Built VSIX version changed.")

        architectures: list[str] = []
        for target in _children_by_name(manifest, "InstallationTarget"):
            for child in target:
                if _local_name(child.tag) == "ProductArchitecture":
                    architectures.append((child.text or "").strip())
        if tuple(architectures) != ("amd64", "arm64"):
            raise VisualStudioExtensionError(
                f"Built VSIX architectures changed: {architectures!r}."
            )

        assembly_candidates = tuple(
            name for name in names
            if name.replace("\\", "/").rsplit("/", 1)[-1].casefold()
            == "apexforge.visualstudio.dll"
        )
        if len(assembly_candidates) != 1:
            raise VisualStudioExtensionError(
                "Built VSIX must contain exactly one ApexForge.VisualStudio.dll."
            )

        forbidden = tuple(
            name for name in names
            if name.casefold().endswith(tuple(_EXPECTED_CONTRACT["vsix_forbidden_suffixes"]))
        )
        if forbidden:
            raise VisualStudioExtensionError(
                "Built VSIX contains source/debug files: " + ", ".join(forbidden)
            )

        return VisualStudioVsixAudit(
            path=selected,
            identity=identity.attrib.get("Id", ""),
            version=identity.attrib.get("Version", ""),
            architectures=tuple(architectures),
            assembly_entry=assembly_candidates[0],
            entry_count=len(names),
            vsix_sha256=_sha256(selected.read_bytes()),
        )


def visual_studio_extension_contract() -> Mapping[str, object]:
    return _EXPECTED_CONTRACT


def visual_studio_extension_fingerprint() -> str:
    return _sha256(_canonical_json(visual_studio_extension_contract()))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="apexforge-visualstudio-extension",
        description="Audit the AFP-P10-T5.1 Visual Studio extension foundation.",
    )
    parser.add_argument("root", nargs="?", help="Visual Studio extension source root")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true", help="audit extension source")
    modes.add_argument("--contract", action="store_true", help="print source contract fingerprint")
    modes.add_argument("--check-vsix", metavar="PATH", help="audit a built VSIX archive")
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    try:
        if arguments.contract:
            print(visual_studio_extension_fingerprint())
            return 0
        if arguments.check_vsix:
            audit = audit_visualstudio_vsix(arguments.check_vsix)
            print(f"AFP-P10-T5.1 built VSIX audit passed: {audit.path}")
            print(f"VSIX SHA-256: {audit.vsix_sha256}")
            return 0
        if not arguments.root:
            parser.error("root is required with --check")
        audit = audit_visualstudio_extension(arguments.root)
        print(f"AFP-P10-T5.1 Visual Studio extension audit passed: {audit.root}")
        print(f"Visual Studio extension SHA-256: {audit.extension_sha256}")
        return 0
    except VisualStudioExtensionError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
