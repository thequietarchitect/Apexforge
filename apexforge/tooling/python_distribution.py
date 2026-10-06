"""P16.5 bounded Python archive evidence and offline setuptools packaging.

Archives are inspected as data, never extracted or imported. Local builds use
caller-supplied source bytes in a disposable tree and the frozen backend only.
"""
from dataclasses import dataclass, field
from hashlib import sha256
from io import BytesIO, StringIO
from email.parser import Parser
import base64
import configparser
import csv
import gzip
import os
import math
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
import zipfile
try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None
from tooling.domain_platform import CanonicalModel
from tooling import release_architecture as release
from tooling import release_build as build
from tooling import release_manifest as manifest
from tooling.package_manifest import PackagePath, CanonicalReference

MAX_ARCHIVE = 16 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_MEMBER = 8 * 1024 * 1024
MAX_METADATA = 256 * 1024
MAX_MEMBERS = 8192
PROJECT_DIGEST = "68934BACB869FCACB4B90F7E37173C891DEBECBE9A0F7FAAF24F2CAF95D9044E"
FORBIDDEN = (".git", "__pycache__", ".vs", ".venv", "venv", ".pytest_cache", ".mypy_cache", "build", "dist")


class PythonDistributionError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code):
    if not ok:
        raise PythonDistributionError(code)


def digest(data):
    require(type(data) is bytes and len(data) <= MAX_TOTAL, "PYTHON_BYTES_INVALID")
    return sha256(data).hexdigest().upper()


def safe_path(value):
    require(type(value) is str and len(value) <= 512 and "\\" not in value and ":" not in value,
            "PYTHON_ARCHIVE_PATH_INVALID")
    try:
        PackagePath(value)
    except ValueError as error:
        raise PythonDistributionError("PYTHON_ARCHIVE_PATH_INVALID") from error
    return value


def clean_path(value, allow_egg=False):
    safe_path(value)
    parts = value.split("/")
    require(not any(p.lower() in FORBIDDEN or p.lower().endswith((".pyc", ".pyo", ".whl", ".tar.gz", ".pypirc"))
                    or (p.lower().endswith(".egg-info") and not allow_egg) for p in parts), "PYTHON_PACKAGE_RESIDUE")
    require(not any(p.lower() in (".env", ".aws", ".ssh", "credentials", "secrets") for p in parts),
            "PYTHON_PACKAGE_RESIDUE")


def compatible_paths(files):
    require(type(files) is dict and len(files) <= MAX_MEMBERS and all(type(name) is str for name in files),
            "PYTHON_ARCHIVE_ENTRY_INVALID")
    logical = {name.casefold() for name in files}
    for name in logical:
        parts = name.split("/")
        require(not any("/".join(parts[:i]) in logical for i in range(1, len(parts))),
                "PYTHON_ARCHIVE_ENTRY_INVALID")


@dataclass(frozen=True)
class PythonProjectMetadata(CanonicalModel):
    pyproject: bytes = field(repr=False)
    DOMAIN = "apexforge.python-project-metadata/v1"

    def __post_init__(self):
        require(type(self.pyproject) is bytes and len(self.pyproject) <= MAX_METADATA and digest(self.pyproject) == PROJECT_DIGEST,
                "PYTHON_PROJECT_METADATA_MISMATCH")
        require(tomllib is not None, "PYTHON_METADATA_ENVIRONMENT_DEPENDENCY")
        try:
            tomllib.loads(self.pyproject.decode("utf-8"))
        except (UnicodeError, ValueError) as error:
            raise PythonDistributionError("PYTHON_PROJECT_METADATA_INVALID") from error

    def record(self):
        data = tomllib.loads(self.pyproject.decode("utf-8"))
        return {"pyproject_digest": digest(self.pyproject), "project": data["project"],
                "build_system": data["build-system"], "setuptools": data["tool"]["setuptools"],
                "readme": data["project"].get("readme"), "license": data["project"].get("license"),
                "optional_dependencies": data["project"].get("optional-dependencies"),
                "package_data": data["tool"]["setuptools"].get("package-data"), "repository_derived": True}


@dataclass(frozen=True)
class PythonDistributionIdentity(CanonicalModel):
    release: release.ReleaseIdentity
    name: str
    version: str
    metadata: PythonProjectMetadata
    DOMAIN = "apexforge.python-distribution-identity/v1"

    def __post_init__(self):
        require(type(self.release) is release.ReleaseIdentity and self.release.baseline == release.P15_BASELINE,
                "PYTHON_RELEASE_BINDING_INVALID")
        require(type(self.metadata) is PythonProjectMetadata, "PYTHON_PROJECT_METADATA_INVALID")
        project = self.metadata.record()["project"]
        require(type(self.name) is str and self.name == re.sub(r"[-_.]+", "-", project["name"]).lower() and
                type(self.version) is str and self.version == project["version"], "PYTHON_IDENTITY_METADATA_MISMATCH")

    def record(self):
        return {"release": self.release.record(), "name": self.name, "python_version": self.version,
                "metadata": self.metadata.fingerprint(), "packaging_contract": self.DOMAIN,
                "release_version_distinct": True, "authority": False, "trust": False}


def text(data):
    require(type(data) is bytes and len(data) <= MAX_METADATA, "PYTHON_METADATA_SIZE_INVALID")
    try:
        value = data.decode("utf-8")
    except UnicodeError as error:
        raise PythonDistributionError("PYTHON_METADATA_TEXT_INVALID") from error
    require("\x00" not in value, "PYTHON_METADATA_TEXT_INVALID")
    return value


def core_metadata(data, identity):
    require(type(identity) is PythonDistributionIdentity, "PYTHON_METADATA_BINDING_INVALID")
    message = Parser().parsestr(text(data))
    require(not message.defects, "PYTHON_METADATA_INVALID")
    expected = {"Name": identity.metadata.record()["project"]["name"], "Version": identity.version,
                "Requires-Python": identity.metadata.record()["project"]["requires-python"],
                "Summary": identity.metadata.record()["project"]["description"]}
    for key, value in expected.items():
        require(message.get_all(key) == [value], "PYTHON_METADATA_MISMATCH")
    require(message.get_all("Metadata-Version") is not None and len(message.get_all("Metadata-Version")) == 1 and
            message["Metadata-Version"] in ("2.1", "2.2", "2.3", "2.4"), "PYTHON_METADATA_INVALID")
    require(not message.get_all("Requires-Dist") and not message.get_all("Provides-Extra"), "PYTHON_METADATA_MISMATCH")
    return tuple(sorted(expected.items()))


def wheel_members(data):
    require(type(data) is bytes and len(data) <= MAX_ARCHIVE, "PYTHON_ARCHIVE_SIZE_INVALID")
    result, timestamps, seen, total = {}, [], set(), 0
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            infos = archive.infolist()
            require(len(infos) <= MAX_MEMBERS, "PYTHON_ARCHIVE_COUNT_INVALID")
            for info in infos:
                name = safe_path(info.filename.rstrip("/") if info.is_dir() else info.filename)
                require(name.casefold() not in seen, "PYTHON_ARCHIVE_DUPLICATE")
                seen.add(name.casefold())
                clean_path(name)
                require(not info.flag_bits & 1 and not stat.S_ISLNK(info.external_attr >> 16), "PYTHON_ARCHIVE_ENTRY_INVALID")
                mode = stat.S_IFMT(info.external_attr >> 16)
                require(mode in (0, stat.S_IFREG, stat.S_IFDIR), "PYTHON_ARCHIVE_ENTRY_INVALID")
                require(0 <= info.file_size <= MAX_MEMBER, "PYTHON_ARCHIVE_SIZE_INVALID")
                total += info.file_size
                require(total <= MAX_TOTAL, "PYTHON_ARCHIVE_SIZE_INVALID")
                if not info.is_dir():
                    result[name] = archive.read(info)
                    timestamps.append((name, tuple(info.date_time)))
    except (zipfile.BadZipFile, RuntimeError, OSError, NotImplementedError) as error:
        raise PythonDistributionError("PYTHON_WHEEL_INVALID") from error
    compatible_paths(result)
    return result, tuple(sorted(timestamps))


def sdist_members(data, root):
    require(type(data) is bytes and len(data) <= MAX_ARCHIVE, "PYTHON_ARCHIVE_SIZE_INVALID")
    require(type(root) is str and "/" not in root, "PYTHON_SDIST_ROOT_INVALID")
    safe_path(root)
    result, timestamps, seen, total = {}, [], set(), 0
    try:
        # Bound decompression before tar/PAX parsing, including extended headers.
        limit = MAX_TOTAL + MAX_MEMBERS * 1024
        with gzip.GzipFile(fileobj=BytesIO(data)) as compressed:
            raw = compressed.read(limit + 1)
        require(len(raw) <= limit, "PYTHON_ARCHIVE_SIZE_INVALID")
        with tarfile.open(fileobj=BytesIO(raw), mode="r:") as archive:
            for index, member in enumerate(archive):
                require(index < MAX_MEMBERS, "PYTHON_ARCHIVE_COUNT_INVALID")
                name = safe_path(member.name.rstrip("/") if member.isdir() else member.name)
                require(name == root or name.startswith(root + "/"), "PYTHON_SDIST_ROOT_INVALID")
                require(name.casefold() not in seen, "PYTHON_ARCHIVE_DUPLICATE")
                seen.add(name.casefold())
                clean_path(name, allow_egg=True)
                require(member.isfile() or member.isdir(), "PYTHON_ARCHIVE_ENTRY_INVALID")
                require(type(member.mtime) in (int, float) and math.isfinite(member.mtime) and 0 <= member.mtime <= 2**63,
                        "PYTHON_ARCHIVE_METADATA_INVALID")
                require(sum(len(k) + len(v) for k, v in member.pax_headers.items()) <= MAX_METADATA,
                        "PYTHON_METADATA_SIZE_INVALID")
                require(type(member.size) is int and 0 <= member.size <= MAX_MEMBER, "PYTHON_ARCHIVE_SIZE_INVALID")
                total += member.size
                require(total <= MAX_TOTAL, "PYTHON_ARCHIVE_SIZE_INVALID")
                if member.isfile():
                    payload = archive.extractfile(member).read(member.size + 1)
                    require(len(payload) == member.size, "PYTHON_SDIST_INVALID")
                    relative = name[len(root) + 1:]
                    require(bool(relative), "PYTHON_SDIST_ROOT_INVALID")
                    result[relative] = payload
                    timestamps.append((relative, member.mtime))
    except (tarfile.TarError, OSError, EOFError, ValueError) as error:
        if type(error) is PythonDistributionError:
            raise
        raise PythonDistributionError("PYTHON_SDIST_INVALID") from error
    compatible_paths(result)
    return result, tuple(sorted(timestamps))


def wheel_record(members, record_path):
    require(type(members) is dict and len(members) <= MAX_MEMBERS and type(record_path) is str and
            all(type(k) is str and type(v) is bytes and len(v) <= MAX_MEMBER for k, v in members.items()), "PYTHON_WHEEL_RECORD_INVALID")
    require(sum(len(v) for v in members.values()) <= MAX_TOTAL, "PYTHON_WHEEL_RECORD_INVALID")
    safe_path(record_path)
    require(record_path in members, "PYTHON_WHEEL_RECORD_MISSING")
    try:
        rows = list(csv.reader(StringIO(text(members[record_path])), strict=True))
    except csv.Error as error:
        raise PythonDistributionError("PYTHON_WHEEL_RECORD_INVALID") from error
    require(len(rows) <= MAX_MEMBERS, "PYTHON_WHEEL_RECORD_INVALID")
    seen = set()
    for row in rows:
        require(len(row) == 3, "PYTHON_WHEEL_RECORD_INVALID")
        name, declared, length = row
        safe_path(name)
        require(name in members and name not in seen, "PYTHON_WHEEL_RECORD_INVALID")
        seen.add(name)
        if name == record_path:
            require(declared == "" and length == "", "PYTHON_WHEEL_RECORD_INVALID")
        else:
            expected = base64.urlsafe_b64encode(sha256(members[name]).digest()).rstrip(b"=").decode("ascii")
            require(declared == "sha256=" + expected and length == str(len(members[name])), "PYTHON_WHEEL_RECORD_MISMATCH")
    require(seen == set(members), "PYTHON_WHEEL_RECORD_INVALID")


@dataclass(frozen=True)
class PythonPackageEvidence(CanonicalModel):
    identity: PythonDistributionIdentity
    descriptor: release.ReleaseArtifactDescriptor
    data: bytes = field(repr=False)
    expected_sources: tuple = ()
    _inventory: tuple = field(init=False, repr=False)
    _timestamps: tuple = field(init=False, repr=False)
    DOMAIN = "apexforge.python-package-evidence/v1"

    def __post_init__(self):
        require(type(self.identity) is PythonDistributionIdentity and type(self.descriptor) is release.ReleaseArtifactDescriptor,
                "PYTHON_PACKAGE_BINDING_INVALID")
        descriptor = self.descriptor
        require(descriptor.release == self.identity.release and descriptor.target == release.ReleaseTarget("python") and
                descriptor.role == "PYTHON_DISTRIBUTION" and descriptor.surface_version == self.identity.version and
                descriptor.availability != "UNAVAILABLE", "PYTHON_PACKAGE_BINDING_INVALID")
        stem = self.identity.name.replace("-", "_") + "-" + self.identity.version
        if descriptor.format == "wheel":
            require(descriptor.filename == stem + "-py3-none-any.whl", "PYTHON_WHEEL_FILENAME_MISMATCH")
            members, timestamps = wheel_members(self.data)
            info = stem + ".dist-info/"
            require({info + "METADATA", info + "WHEEL", info + "RECORD", info + "entry_points.txt"} <= set(members), "PYTHON_WHEEL_METADATA_MISSING")
            require(all(p.startswith(info) for p in members if ".dist-info/" in p), "PYTHON_WHEEL_METADATA_MISMATCH")
            core_metadata(members[info + "METADATA"], self.identity)
            wheel = Parser().parsestr(text(members[info + "WHEEL"]))
            require(wheel.get_all("Wheel-Version") == ["1.0"] and wheel.get_all("Root-Is-Purelib") == ["true"] and
                    wheel.get_all("Tag") == ["py3-none-any"], "PYTHON_WHEEL_TAG_MISMATCH")
            config = configparser.ConfigParser(interpolation=None, strict=True)
            try:
                config.read_string(text(members[info + "entry_points.txt"]))
            except configparser.Error as error:
                raise PythonDistributionError("PYTHON_ENTRY_POINTS_MISMATCH") from error
            require(config.sections() == ["console_scripts"] and dict(config["console_scripts"]) == {"apexforge": "tooling.cli:main"},
                    "PYTHON_ENTRY_POINTS_MISMATCH")
            wheel_record(members, info + "RECORD")
            require({"tooling/__init__.py", "tooling/cli.py"} <= set(members), "PYTHON_PACKAGE_SOURCE_MISSING")
        else:
            require(descriptor.format == "sdist" and descriptor.filename in
                    (stem + ".tar.gz", self.identity.name + "-" + self.identity.version + ".tar.gz"), "PYTHON_SDIST_FILENAME_MISMATCH")
            root = descriptor.filename[:-7]
            members, timestamps = sdist_members(self.data, root)
            require({"PKG-INFO", "pyproject.toml", "apexforge/tooling/__init__.py", "apexforge/tooling/cli.py"} <= set(members),
                    "PYTHON_PACKAGE_SOURCE_MISSING")
            core_metadata(members["PKG-INFO"], self.identity)
            require(members["pyproject.toml"] == self.identity.metadata.pyproject, "PYTHON_PROJECT_METADATA_MISMATCH")
        require(type(self.expected_sources) is tuple and len(self.expected_sources) <= MAX_MEMBERS,
                "PYTHON_SOURCE_EXPECTATION_INVALID")
        expected = {}
        for item in self.expected_sources:
            require(type(item) is tuple and len(item) == 2 and type(item[1]) is str and
                    re.fullmatch(r"[0-9A-F]{64}", item[1]) is not None, "PYTHON_SOURCE_EXPECTATION_INVALID")
            safe_path(item[0])
            require(item[0] not in expected, "PYTHON_SOURCE_EXPECTATION_INVALID")
            expected[item[0]] = item[1]
        if expected:
            actual = {name: digest(value) for name, value in members.items() if name.endswith(".py")}
            require(actual == expected, "PYTHON_PACKAGE_SOURCE_MISMATCH")
        object.__setattr__(self, "expected_sources", tuple(sorted(expected.items())))
        object.__setattr__(self, "_inventory", tuple(sorted((name, len(payload), digest(payload)) for name, payload in members.items())))
        object.__setattr__(self, "_timestamps", timestamps)

    def content_record(self):
        return {"identity": self.identity.fingerprint(), "descriptor": self.descriptor.fingerprint(),
                "inventory": self._inventory, "expected_sources": self.expected_sources}

    def record(self):
        return {**self.content_record(), "length": len(self.data), "digest": digest(self.data),
                "timestamps": self._timestamps, "authority": False, "trusted": False, "authenticated": False,
                "installed": False, "published": False, "compatibility": "NOT_ESTABLISHED",
                "crypto": "CRYPTO_PROVIDER_UNAVAILABLE", "semantic_authority": "CANONICAL_AIR"}


@dataclass(frozen=True)
class PythonReproducibilityEvidence(CanonicalModel):
    first: PythonPackageEvidence
    second: PythonPackageEvidence
    DOMAIN = "apexforge.python-package-reproducibility/v1"

    def __post_init__(self):
        require(type(self.first) is PythonPackageEvidence and type(self.second) is PythonPackageEvidence,
                "PYTHON_REPRODUCIBILITY_INVALID")

    def record(self):
        content = self.first.content_record() == self.second.content_record()
        raw = self.first.data == self.second.data
        return {"first": self.first.fingerprint(), "second": self.second.fingerprint(),
                "content": "PASS" if content else "MISMATCH", "raw_bytes": "PASS" if content and raw else "MISMATCH",
                "timestamp_metadata_equal": self.first._timestamps == self.second._timestamps,
                "finding": None if content and raw else "PYTHON_PACKAGE_BYTE_REPRODUCIBILITY_GAP" if content else "PYTHON_PACKAGE_REPRODUCIBILITY_GAP",
                "authenticated": False, "trusted": False}


def generic_evidence(package):
    """Adapt actual inspected bytes through P16.3 COPY_BYTES without redefining it."""
    require(type(package) is PythonPackageEvidence, "PYTHON_PACKAGE_BINDING_INVALID")
    require(len(package.data) <= build.MAX_BYTES, "PYTHON_GENERIC_BUILD_SIZE_UNSUPPORTED")
    provenance = package.descriptor.provenance
    provenance = provenance + (CanonicalReference(package.identity.DOMAIN, "source", package.identity.fingerprint()),)
    supplied = build.ReleaseBuildInput(package.identity.release, PackagePath("python-artifact"), "EXISTING_ARTIFACT",
                    package.data, build.digest(package.data),
                    source=CanonicalReference(package.DOMAIN, "artifact", package.fingerprint()), provenance=provenance)
    recipe = build.ReleaseBuildRecipe("python-packaging-evidence", package.identity.release, "COPY_BYTES",
                    build.ReleaseBuildEnvironment("python-artifact-adapter", "p16.python-packaging"), (supplied,),
                    (build.ReleaseBuildOutputSlot(package.descriptor, supplied.identity),), provenance)
    artifact = build.ReleaseBuildArtifact(recipe, package.descriptor.identity, package.data, build.digest(package.data))
    return artifact, manifest.checksum_for(artifact)


def build_local(metadata, sources, kind):
    """Offline frozen setuptools backend in a disposable supplied-source projection.

    Returns bytes only when a real build produced an output. Missing frontend or
    wheel dependencies are classified, never installed. No arbitrary argv API.
    """
    require(type(metadata) is PythonProjectMetadata and type(kind) is str and kind in ("wheel", "sdist"), "PYTHON_BUILD_REQUEST_INVALID")
    require(type(sources) is tuple and len(sources) <= MAX_MEMBERS, "PYTHON_BUILD_SOURCE_INVALID")
    members, total, logical = {}, 0, set()
    for item in sources:
        require(type(item) is tuple and len(item) == 2 and type(item[0]) is str and type(item[1]) is bytes, "PYTHON_BUILD_SOURCE_INVALID")
        name, data = item
        try:
            clean_path(name)
        except PythonDistributionError as error:
            raise PythonDistributionError("PYTHON_BUILD_SOURCE_INVALID") from error
        require(name.casefold() not in logical and name.casefold() not in ("setup.py", "setup.cfg") and len(data) <= MAX_MEMBER,
                "PYTHON_BUILD_SOURCE_INVALID")
        logical.add(name.casefold())
        total += len(data)
        require(total <= MAX_TOTAL, "PYTHON_BUILD_SOURCE_INVALID")
        members[name] = data
    compatible_paths(members)
    require(members.get("pyproject.toml") == metadata.pyproject, "PYTHON_PROJECT_METADATA_MISMATCH")
    # Constant trusted script; build kind chooses between two fixed backend hooks.
    script = ("from setuptools.build_meta import build_wheel; build_wheel('../output')" if kind == "wheel" else
              "from setuptools.build_meta import build_sdist; build_sdist('../output')")
    with tempfile.TemporaryDirectory(prefix="apexforge-python-") as temp:
        root = Path(temp) / "source"
        output = Path(temp) / "output"
        root.mkdir()
        output.mkdir()
        home = Path(temp) / "home"
        scratch = Path(temp) / "scratch"
        home.mkdir()
        scratch.mkdir()
        for name, data in members.items():
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        try:
            environment = {"PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PYTHONDONTWRITEBYTECODE": "1"}
            environment.update({"HOME": str(home), "USERPROFILE": str(home), "TEMP": str(scratch), "TMP": str(scratch)})
            if os.name == "nt":
                # Windows DLL/Winsock initialization requires this non-secret loader setting.
                require("SystemRoot" in os.environ, "PYTHON_BUILD_ENVIRONMENT_DEPENDENCY")
                environment["SystemRoot"] = os.environ["SystemRoot"]
            process = subprocess.run([sys.executable, "-I", "-B", "-c", script], cwd=root,
                         env=environment,
                         capture_output=True, timeout=120, check=False, shell=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise PythonDistributionError("PYTHON_BUILD_ENVIRONMENT_DEPENDENCY") from error
        if process.returncode:
            reason = process.stderr.decode("utf-8", errors="replace")
            code = "PYTHON_BUILD_ENVIRONMENT_DEPENDENCY" if ("bdist_wheel" in reason or "No module named" in reason) else "PYTHON_BUILD_BACKEND_FAILED"
            raise PythonDistributionError(code)
        files = tuple(output.iterdir())  # Explicit output directory, not source discovery.
        require(len(files) == 1 and not files[0].is_symlink() and files[0].is_file() and files[0].stat().st_size <= MAX_ARCHIVE,
                "PYTHON_BUILD_OUTPUT_INVALID")
        name, data = files[0].name, files[0].read_bytes()
        require(name.endswith(".whl" if kind == "wheel" else ".tar.gz"), "PYTHON_BUILD_OUTPUT_INVALID")
        return name, data
