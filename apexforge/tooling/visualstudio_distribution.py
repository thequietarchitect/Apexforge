"""P16.7 exact frozen-source Visual Studio release evidence.

The frozen project and T5 auditors own packaging/editor semantics. Archives are
data only. The optional local probe uses only fixed dotnet build argv, no restore,
and a disposable source projection; it never installs or activates an extension.
"""
from dataclasses import dataclass, field
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET
from zipfile import ZipFile, BadZipFile
from tooling.domain_platform import CanonicalModel
from tooling import release_architecture as r, release_build as b
from tooling import visualstudio_packaging as owner, visualstudio_integration as integration
from tooling.package_manifest import PackagePath, CanonicalReference

PROJECT = "src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj"
MANIFEST = "src/ApexForge.VisualStudio/source.extension.vsixmanifest"
SOURCE_FILES = (
    ".gitignore", "ApexForge.VisualStudio.sln", "README.md", "VISUAL_STUDIO_INTEGRATION.md",
    "VISUAL_STUDIO_LANGUAGE_FEATURES.md", "VISUAL_STUDIO_PACKAGING.md", PROJECT,
    "src/ApexForge.VisualStudio/ApexForgePackage.cs",
    "src/ApexForge.VisualStudio/Classification/ApexForgeClassificationFormats.cs",
    "src/ApexForge.VisualStudio/Classification/ApexForgeClassificationNames.cs",
    "src/ApexForge.VisualStudio/Classification/ApexForgeClassificationTypes.cs",
    "src/ApexForge.VisualStudio/Classification/ApexForgeClassifier.cs",
    "src/ApexForge.VisualStudio/Classification/ApexForgeClassifierProvider.cs",
    "src/ApexForge.VisualStudio/Commands/OpenLanguageServerLogCommand.cs",
    "src/ApexForge.VisualStudio/Commands/RestartLanguageServerCommand.cs",
    "src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs",
    "src/ApexForge.VisualStudio/Content/ApexForgeContentType.cs",
    "src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageClient.cs",
    "src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageServerLocator.cs",
    "src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageServerTrace.cs",
    "src/ApexForge.VisualStudio/Resources/ApexForge.vsct", MANIFEST)
FROZEN_SOURCE_LEDGER = "9EDF0D0A9E950BDEA07113338E547345AD57CB0EFA7BF5B7BC2DC26C854D5F6F"
MAX_BYTES = b.MAX_BYTES
MAX_MEMBER = MAX_BYTES
MAX_TOTAL = 4 * MAX_BYTES
MAX_ENTRIES = 1024


class VisualStudioDistributionError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(value, code):
    if not value:
        raise VisualStudioDistributionError(code)


def digest(data):
    return sha256(data).hexdigest().upper()


def xml(data):
    require(type(data) is bytes and len(data) <= 128 * 1024 and b"\0" not in data and b"<!DOCTYPE" not in data.upper()
            and b"<!ENTITY" not in data.upper(), "VISUAL_STUDIO_XML_INVALID")
    try:
        text = data.decode("utf-8-sig")
        root = ET.fromstring(text)
        stack, count = [(root, 0)], 0
        while stack:
            item, depth = stack.pop()
            count += 1
            require(depth <= 16 and count <= 4096, "VISUAL_STUDIO_XML_INVALID")
            stack.extend((child, depth + 1) for child in item)
        return root
    except (ET.ParseError, UnicodeError, ValueError) as error:
        if isinstance(error, VisualStudioDistributionError):
            raise
        raise VisualStudioDistributionError("VISUAL_STUDIO_XML_INVALID") from error


def xml_projection(element):
    # Called only after bounded depth validation. No host-dependent XML formatting.
    return {"tag": element.tag, "attributes": dict(sorted(element.attrib.items())),
            "text": (element.text or "").strip(), "children": [xml_projection(c) for c in element]}


def manifest_metadata(root):
    return {name: [xml_projection(e) for e in owner._children_by_name(root, name)]
            for name in ("Metadata", "Installation", "Dependencies", "Prerequisites")}


def materialize(source, destination):
    for name, payload in source.files:
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


@dataclass(frozen=True)
class VisualStudioDistributionIdentity(CanonicalModel):
    release: r.ReleaseIdentity
    files: tuple = field(repr=False)
    DOMAIN = "apexforge.visual-studio-distribution-identity/v1"

    def __post_init__(self):
        require(type(self.release) is r.ReleaseIdentity and self.release.baseline == r.P15_BASELINE,
                "VISUAL_STUDIO_RELEASE_BINDING_INVALID")
        require(type(self.files) is tuple and len(self.files) == len(SOURCE_FILES)
                and all(type(row) is tuple and len(row) == 2 and type(row[0]) is str
                        and type(row[1]) is bytes and len(row[1]) <= MAX_MEMBER for row in self.files),
                "VISUAL_STUDIO_SOURCE_INVALID")
        require({name for name, _ in self.files} == set(SOURCE_FILES), "VISUAL_STUDIO_SOURCE_INVALID")
        files = tuple(sorted(self.files))
        ledger = [(name, digest(payload)) for name, payload in files]
        require(digest(json.dumps(ledger, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
                == FROZEN_SOURCE_LEDGER, "VISUAL_STUDIO_FROZEN_SOURCE_MISMATCH")
        object.__setattr__(self, "files", files)
        with TemporaryDirectory(prefix="apexforge-vs-source-") as temporary:
            materialize(self, Path(temporary))
            try:
                integration.audit_visualstudio_integration_source(temporary)
            except integration.VisualStudioIntegrationError as error:
                raise VisualStudioDistributionError("VISUAL_STUDIO_FROZEN_OWNER_REJECTED") from error

    def record(self):
        sources = dict(self.files)
        manifest = xml(sources[MANIFEST])
        return {"release": self.release.record(), "extension_id": "GravitasStudios.ApexForge.VisualStudio",
                "extension_version": "0.1.0", "version_domain": "VISUAL_STUDIO_EXTENSION",
                "source_ledger": FROZEN_SOURCE_LEDGER,
                "source": [{"path": n, "sha256": digest(v), "length": len(v)} for n, v in self.files],
                "source_manifest": xml_projection(manifest), "project": xml_projection(xml(sources[PROJECT])),
                "packaging_owner": owner.CANONICAL_VISUAL_STUDIO_PACKAGING_SHA256,
                "integration_owner": integration.CANONICAL_VISUAL_STUDIO_INTEGRATION_SHA256,
                "publisher_authenticated": False, "semantic_authority": "CANONICAL_AIR"}


def inventory(data):
    require(type(data) is bytes and 0 < len(data) <= MAX_BYTES, "VISUAL_STUDIO_ARCHIVE_SIZE_INVALID")
    rows, seen, files, total = [], set(), set(), 0
    try:
        with ZipFile(BytesIO(data)) as archive:
            infos = archive.infolist()
            require(0 < len(infos) <= MAX_ENTRIES, "VISUAL_STUDIO_ARCHIVE_SIZE_INVALID")
            for info in infos:
                name = info.orig_filename
                parts = name.rstrip("/").split("/")
                require(name and not name.startswith("/") and ":" not in name and "\\" not in name
                        and all(p not in ("", ".", "..") for p in parts)
                        and all(ord(c) >= 32 for c in name), "VISUAL_STUDIO_ARCHIVE_PATH_INVALID")
                key = name.rstrip("/").casefold()
                require(key not in seen, "VISUAL_STUDIO_ARCHIVE_DUPLICATE")
                require(not any(key.startswith(f + "/") for f in files)
                        and not (not info.is_dir() and any(n.startswith(key + "/") for n in seen)),
                        "VISUAL_STUDIO_ARCHIVE_PATH_INVALID")
                seen.add(key)
                if not info.is_dir():
                    files.add(key)
                require(not info.flag_bits & 1 and stat.S_IFMT(info.external_attr >> 16) in
                        (0, stat.S_IFDIR, stat.S_IFREG), "VISUAL_STUDIO_ARCHIVE_LINK_INVALID")
                total += info.file_size
                require(info.file_size <= MAX_MEMBER and total <= MAX_TOTAL, "VISUAL_STUDIO_ARCHIVE_SIZE_INVALID")
                require(not any(p.casefold() in owner._FORBIDDEN_SEGMENTS or p.casefold() in
                                ("dist", "build", "test-results", "temp") for p in parts)
                        and not key.endswith(owner._FORBIDDEN_SUFFIXES + (".pypirc",)), "VISUAL_STUDIO_ARCHIVE_RESIDUE")
                payload = archive.read(info)
                require(len(payload) == info.file_size, "VISUAL_STUDIO_ARCHIVE_INVALID")
                if key.endswith((".xml", ".vsixmanifest")):
                    xml(payload)
                rows.append((name, len(payload), digest(payload), tuple(info.date_time), info.is_dir()))
            order = tuple(i.filename for i in infos)
    except (BadZipFile, OSError, RuntimeError, NotImplementedError, UnicodeError) as error:
        raise VisualStudioDistributionError("VISUAL_STUDIO_ARCHIVE_INVALID") from error
    return tuple(sorted(rows)), order


@dataclass(frozen=True)
class VisualStudioVSIXEvidence(CanonicalModel):
    identity: VisualStudioDistributionIdentity
    descriptor: r.ReleaseArtifactDescriptor
    data: bytes = field(repr=False)
    built_assembly: bytes = field(repr=False)
    declared_assembly_digest: str
    _audit: tuple = field(init=False, repr=False)
    DOMAIN = "apexforge.visual-studio-vsix-evidence/v1"

    def __post_init__(self):
        require(type(self.identity) is VisualStudioDistributionIdentity and type(self.descriptor) is r.ReleaseArtifactDescriptor,
                "VISUAL_STUDIO_RELEASE_BINDING_INVALID")
        d = self.descriptor
        require(d.release == self.identity.release and d.target == r.ReleaseTarget("visual-studio")
                and d.surface_version == "0.1.0" and d.availability != "UNAVAILABLE",
                "VISUAL_STUDIO_RELEASE_BINDING_INVALID")
        require(type(self.built_assembly) is bytes and 0 < len(self.built_assembly) <= MAX_MEMBER
                and type(self.declared_assembly_digest) is str and re.fullmatch(r"[0-9A-F]{64}", self.declared_assembly_digest)
                and digest(self.built_assembly) == self.declared_assembly_digest, "VISUAL_STUDIO_ASSEMBLY_DIGEST_MISMATCH")
        inventory(self.data)
        with TemporaryDirectory(prefix="apexforge-vs-vsix-") as temporary:
            path = Path(temporary) / "owner.vsix"
            path.write_bytes(self.data)
            try:
                audit = integration.audit_visualstudio_integration_vsix(path)
                hardened = owner.audit_visualstudio_vsix_hardening(path)
            except (integration.VisualStudioIntegrationError, owner.VisualStudioPackagingError) as error:
                raise VisualStudioDistributionError("VISUAL_STUDIO_FROZEN_OWNER_REJECTED") from error
            with ZipFile(BytesIO(self.data)) as archive:
                require(archive.read(hardened.assembly_entry) == self.built_assembly
                        and audit.assembly_sha256.upper() == self.declared_assembly_digest,
                        "VISUAL_STUDIO_ASSEMBLY_CONTINUITY_MISMATCH")
                packaged = xml(archive.read(hardened.manifest_entry))
                source = xml(dict(self.identity.files)[MANIFEST])
                require(manifest_metadata(packaged) == manifest_metadata(source), "VISUAL_STUDIO_MANIFEST_CONTINUITY_MISMATCH")
                # Owner's assets must resolve to the payload it reported.
                index = {i.filename: i for i in archive.infolist() if not i.is_dir()}
                require(all(asset.attrib["Path"] in index for asset in owner._children_by_name(packaged, "Asset")),
                        "VISUAL_STUDIO_ASSET_UNRESOLVED")
            object.__setattr__(self, "_audit", (audit.normalized_payload_sha256.upper(), hardened.manifest_sha256.upper(),
                                              hardened.assembly_entry, hardened.package_definition_entry))

    def record(self):
        rows, order = inventory(self.data)
        return {"identity": self.identity.record(), "descriptor": self.descriptor.record(),
                "sha256": digest(self.data), "length": len(self.data),
                "inventory": [{"path": n, "length": size, "sha256": h, "timestamp": list(t), "directory": directory}
                              for n, size, h, t, directory in rows], "archive_order": list(order),
                "normalized_owner_payload": self._audit[0], "manifest_sha256": self._audit[1],
                "assembly_entry": self._audit[2], "pkgdef_entry": self._audit[3],
                "assembly_sha256": self.declared_assembly_digest, "assembly_continuity": True,
                "build_evidence": "EXPLICIT_SUPPLIED_BUILD_OUTPUT_BYTES", "installed_copy": "NOT_EVALUATED",
                "authenticated": False, "signed": False, "grants_authority": False, "grants_trust": False,
                "grants_compatibility": False, "installed": False, "published": False, "executed": False,
                "crypto": "CRYPTO_PROVIDER_UNAVAILABLE"}

    def build_artifact(self):
        ref = CanonicalReference(self.DOMAIN, "source", self.fingerprint())
        inp = b.ReleaseBuildInput(self.identity.release, PackagePath(self.descriptor.filename), "EXISTING_ARTIFACT",
                                  self.data, digest(self.data), ref, (ref,))
        recipe = b.ReleaseBuildRecipe("visual-studio-release-evidence", self.identity.release, "COPY_BYTES",
                  b.ReleaseBuildEnvironment("visual-studio-inspected-bytes", "tooling.visualstudio_packaging"),
                  (inp,), (b.ReleaseBuildOutputSlot(self.descriptor, inp.identity),), (ref,))
        return b.ReleaseBuildArtifact(recipe, self.descriptor.identity, self.data, digest(self.data))


def compare_packages(left, right):
    require(type(left) is VisualStudioVSIXEvidence and type(right) is VisualStudioVSIXEvidence, "VISUAL_STUDIO_EVIDENCE_INVALID")
    context = left.identity == right.identity and left.descriptor == right.descriptor
    return {"context_equal": context,
            "member_content_equal": context and left._audit[0] == right._audit[0],
            "assembly_equal": context and left.built_assembly == right.built_assembly,
            "raw_bytes_equal": context and left.data == right.data, "authenticated": False}


@dataclass(frozen=True)
class LocalVisualStudioBuildResult:
    status: str
    finding: str
    evidence: VisualStudioVSIXEvidence | None = None
    tool_diagnostic: str = field(default="", repr=False)

    def __post_init__(self):
        require(type(self.tool_diagnostic) is str and len(self.tool_diagnostic) <= 32768,
                "VISUAL_STUDIO_BUILD_RESULT_INVALID")
        require((self.status == "BUILT" and self.finding == "VISUAL_STUDIO_LOCAL_BUILD" and type(self.evidence) is VisualStudioVSIXEvidence)
                or (self.status == "UNAVAILABLE" and self.finding == "VISUAL_STUDIO_PACKAGE_ENVIRONMENT_DEPENDENCY" and self.evidence is None),
                "VISUAL_STUDIO_BUILD_RESULT_INVALID")


def local_build(identity, descriptor):
    """Fixed project-only no-restore probe. Never acquire missing dependencies.

    Diagnostics are operational, not canonical. Missing assets/framework tools
    remain unavailable; callers may supply genuine separately-produced outputs.
    """
    require(type(identity) is VisualStudioDistributionIdentity and type(descriptor) is r.ReleaseArtifactDescriptor
            and descriptor.release == identity.release and descriptor.target == r.ReleaseTarget("visual-studio")
            and descriptor.surface_version == "0.1.0" and descriptor.availability != "UNAVAILABLE",
            "VISUAL_STUDIO_RELEASE_BINDING_INVALID")
    executable = shutil.which("dotnet")
    if executable is None:
        return LocalVisualStudioBuildResult("UNAVAILABLE", "VISUAL_STUDIO_PACKAGE_ENVIRONMENT_DEPENDENCY")
    with TemporaryDirectory(prefix="apexforge-vs-build-") as temporary:
        root = Path(temporary)
        materialize(identity, root / "source")
        output = root / "output"
        # Keep first-run writes and caches disposable. Do not enumerate secrets.
        environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "PATH") if key in os.environ}
        environment.update({"DOTNET_CLI_HOME": str(root / "home"), "TEMP": str(root / "temp"),
                            "TMP": str(root / "temp"), "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
                            "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1", "DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE": "true"})
        environment["DOTNET_GENERATE_ASPNET_CERTIFICATE"] = "false"
        (root / "temp").mkdir()
        argv = (executable, "build", PROJECT, "--no-restore", "--configuration", "Release", "--output", str(output),
                "--verbosity", "quiet", "--nologo", "-warnaserror", "-p:DeployExtension=false",
                "-p:UseSharedCompilation=false", "-nodeReuse:false")
        try:
            completed = subprocess.run(argv, cwd=root / "source", env=environment, shell=False,
                                       capture_output=True, text=True, timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return LocalVisualStudioBuildResult("UNAVAILABLE", "VISUAL_STUDIO_PACKAGE_ENVIRONMENT_DEPENDENCY")
        if completed.returncode != 0:
            diagnostics = (completed.stdout + completed.stderr)[-32768:]
            require(re.search(r"\b(?:NETSDK1004|MSB3644|MSB4019|MSB4062|MSB4801)\b", diagnostics) is not None,
                    "VISUAL_STUDIO_BUILD_REJECTED")
            return LocalVisualStudioBuildResult("UNAVAILABLE", "VISUAL_STUDIO_PACKAGE_ENVIRONMENT_DEPENDENCY",
                                               tool_diagnostic=diagnostics)
        vsix, dll = output / "ApexForge.VisualStudio.vsix", output / "ApexForge.VisualStudio.dll"
        if not vsix.is_file() or not dll.is_file():
            return LocalVisualStudioBuildResult("UNAVAILABLE", "VISUAL_STUDIO_PACKAGE_ENVIRONMENT_DEPENDENCY")
        require(not vsix.is_symlink() and not dll.is_symlink() and 0 < vsix.stat().st_size <= MAX_BYTES
                and 0 < dll.stat().st_size <= MAX_MEMBER, "VISUAL_STUDIO_BUILD_OUTPUT_INVALID")
        assembly = dll.read_bytes()
        evidence = VisualStudioVSIXEvidence(identity, descriptor, vsix.read_bytes(), assembly, digest(assembly))
        return LocalVisualStudioBuildResult("BUILT", "VISUAL_STUDIO_LOCAL_BUILD", evidence)


def local_cached_build(identity, descriptor):
    """Full framework MSBuild using only existing cache and an empty local feed.

    Fixed installed-tool locations are operational evidence, never identity.
    No public sources, inherited NuGet configuration, credentials, or installers.
    The frozen csproj remains the only packager/build definition.
    """
    require(type(identity) is VisualStudioDistributionIdentity and type(descriptor) is r.ReleaseArtifactDescriptor
            and descriptor.release == identity.release and descriptor.target == r.ReleaseTarget("visual-studio")
            and descriptor.surface_version == "0.1.0" and descriptor.availability != "UNAVAILABLE",
            "VISUAL_STUDIO_RELEASE_BINDING_INVALID")
    program_files, profile = os.environ.get("ProgramFiles", ""), os.environ.get("USERPROFILE", "")
    if not Path(program_files).is_absolute() or not Path(profile).is_absolute():
        return LocalVisualStudioBuildResult("UNAVAILABLE", "VISUAL_STUDIO_PACKAGE_ENVIRONMENT_DEPENDENCY")
    candidates = tuple(Path(program_files) / "Microsoft Visual Studio" / version / "Community" /
                       "MSBuild/Current/Bin/MSBuild.exe" for version in ("18", "2022"))
    executable = next((path for path in candidates if path.is_file()), None)
    cache = Path(profile) / ".nuget/packages"
    if executable is None or not cache.is_dir():
        return LocalVisualStudioBuildResult("UNAVAILABLE", "VISUAL_STUDIO_PACKAGE_ENVIRONMENT_DEPENDENCY")
    with TemporaryDirectory(prefix="apexforge-vs-cached-build-") as temporary:
        root = Path(temporary)
        materialize(identity, root / "source")
        for folder in ("empty-feed", "temp", "home", "appdata", "localappdata", "output"):
            (root / folder).mkdir()
        config = ET.Element("configuration")
        sources = ET.SubElement(config, "packageSources")
        ET.SubElement(sources, "clear")
        ET.SubElement(sources, "add", key="offline", value=str(root / "empty-feed"))
        options = ET.SubElement(config, "config")
        ET.SubElement(options, "add", key="globalPackagesFolder", value=str(cache))
        config_path = root / "NuGet.Config"
        config_path.write_bytes(ET.tostring(config, encoding="utf-8", xml_declaration=True))
        environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "PATH", "ProgramFiles", "ProgramFiles(x86)") if key in os.environ}
        environment.update({"USERPROFILE": str(root / "home"), "APPDATA": str(root / "appdata"),
                            "LOCALAPPDATA": str(root / "localappdata"), "DOTNET_CLI_HOME": str(root / "home"),
                            "TEMP": str(root / "temp"), "TMP": str(root / "temp"),
                            "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_GENERATE_ASPNET_CERTIFICATE": "false"})
        common = (str(executable), PROJECT, "-nologo", "-verbosity:quiet", "-warnaserror", "-p:NuGetAudit=false",
                  "-p:UseSharedCompilation=false", "-nodeReuse:false")
        commands = (
            common + ("-t:Restore", "-p:RestoreConfigFile=" + str(config_path),
                      "-p:RestoreSources=" + str(root / "empty-feed"), "-p:RestorePackagesPath=" + str(cache)),
            common + ("-t:Rebuild", "-p:Configuration=Release", "-p:DeployExtension=false",
                      "-p:OutputPath=" + str(root / "output") + "/", "-p:AppendTargetFrameworkToOutputPath=false"))
        for argv in commands:
            try:
                completed = subprocess.run(argv, cwd=root / "source", env=environment, shell=False,
                                           capture_output=True, text=True, timeout=120, check=False)
            except (OSError, subprocess.TimeoutExpired):
                return LocalVisualStudioBuildResult("UNAVAILABLE", "VISUAL_STUDIO_PACKAGE_ENVIRONMENT_DEPENDENCY")
            if completed.returncode != 0:
                diagnostics = (completed.stdout + completed.stderr)[-32768:]
                require(re.search(r"\b(?:NU1101|NU1102|NETSDK1004|MSB3644|MSB4019|MSB4062|MSB4801)\b", diagnostics) is not None,
                        "VISUAL_STUDIO_BUILD_REJECTED")
                return LocalVisualStudioBuildResult("UNAVAILABLE", "VISUAL_STUDIO_PACKAGE_ENVIRONMENT_DEPENDENCY", tool_diagnostic=diagnostics)
        vsix, dll = root / "output/ApexForge.VisualStudio.vsix", root / "output/ApexForge.VisualStudio.dll"
        if not vsix.is_file() or not dll.is_file():
            return LocalVisualStudioBuildResult("UNAVAILABLE", "VISUAL_STUDIO_PACKAGE_ENVIRONMENT_DEPENDENCY")
        require(not vsix.is_symlink() and not dll.is_symlink() and 0 < vsix.stat().st_size <= MAX_BYTES
                and 0 < dll.stat().st_size <= MAX_MEMBER, "VISUAL_STUDIO_BUILD_OUTPUT_INVALID")
        assembly = dll.read_bytes()
        evidence = VisualStudioVSIXEvidence(identity, descriptor, vsix.read_bytes(), assembly, digest(assembly))
        return LocalVisualStudioBuildResult("BUILT", "VISUAL_STUDIO_LOCAL_BUILD", evidence)
