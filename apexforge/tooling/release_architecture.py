"""P16.1 passive release declarations; no acquisition, build or distribution."""
from dataclasses import dataclass
from tooling.domain_platform import CanonicalModel
from tooling.package_manifest import PackageCoordinate, PackageContentIdentity, PackagePath, CanonicalReference
from native_backend.native_execution_contract import PROFILE
import re

P15_COMMIT = "c9c5ca186c9d942ce336ac1ebfe1287b16953200"
P15_TAG = "afp-p15.14-freeze"
P15_TAG_OBJECT = "d7761c04e4422bfb91d9582275a60912874678f4"
P15_PARENT = "0731e9c00b2858079007dbafdb0e052f497fb24c"
TARGETS = ("python", "vscode", "visual-studio", "native-win-x64")
AVAILABILITY = ("SUPPORTED", "PLANNED", "UNAVAILABLE")
CHANNELS = ("DEVELOPMENT", "RELEASE_CANDIDATE", "STABLE")
# role, format, packaging owner, production slice, declared support scope
SURFACES = (
    ("python", "PYTHON_DISTRIBUTION", ("wheel", "sdist"), "pyproject.toml", "P16.5", "Python >=3.9 metadata; OS release qualification deferred"),
    ("vscode", "VSCODE_EXTENSION", ("vsix",), "tooling.vscode_package", "P16.6", "VS Code ^1.85.0; no native platform promise"),
    ("visual-studio", "VISUAL_STUDIO_EXTENSION", ("vsix",), "tooling.visualstudio_packaging", "P16.7", "Visual Studio 17+ Community; amd64/arm64 extension targets"),
    ("native-win-x64", "NATIVE_COMPONENT", ("dll", "exe"), "tooling.package_artifacts", "P16.8", PROFILE),
)
ROLES = tuple(row[1] for row in SURFACES)
MAX_ITEMS = 1024


class ReleaseArchitectureError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code):
    if not ok:
        raise ReleaseArchitectureError(code)


def text(value, code):
    require(type(value) is str and len(value) <= 128 and
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value, re.ASCII) is not None, code)


def ordered(values, cls, code):
    require(type(values) is tuple and len(values) <= MAX_ITEMS and all(type(v) is cls for v in values), code)
    keys = tuple(v.canonical_json() if isinstance(v, CanonicalModel) else
                 repr(tuple(sorted(v.record().items()))) for v in values)
    require(len(set(keys)) == len(keys), code)
    return tuple(v for _, v in sorted(zip(keys, values), key=lambda pair: pair[0]))


@dataclass(frozen=True)
class FrozenSourceBaseline(CanonicalModel):
    commit: str
    tag: str
    tag_object: str
    parent: str
    DOMAIN = "apexforge.release-source-baseline/v1"

    def __post_init__(self):
        for value in (self.commit, self.tag_object, self.parent):
            require(type(value) is str and re.fullmatch(r"[0-9a-f]{40}", value) is not None, "RELEASE_BASELINE_INVALID")
        text(self.tag, "RELEASE_BASELINE_INVALID")

    def record(self):
        return {"commit": self.commit, "tag": self.tag, "tag_object": self.tag_object, "parent": self.parent,
                "evidence": "CALLER_SUPPLIED_REFERENCE", "authenticated": False}


P15_BASELINE = FrozenSourceBaseline(P15_COMMIT, P15_TAG, P15_TAG_OBJECT, P15_PARENT)


@dataclass(frozen=True)
class ReleaseIdentity(CanonicalModel):
    identifier: str
    version: str
    channel: str
    baseline: FrozenSourceBaseline
    DOMAIN = "apexforge.release-identity/v1"

    def __post_init__(self):
        text(self.identifier, "RELEASE_IDENTITY_INVALID")
        text(self.version, "RELEASE_VERSION_REQUIRED")
        require(type(self.channel) is str and self.channel in CHANNELS, "RELEASE_CHANNEL_INVALID")
        require(type(self.baseline) is FrozenSourceBaseline, "RELEASE_BASELINE_INVALID")

    def record(self):
        return {"id": self.identifier, "declared_version": self.version, "channel": self.channel,
                "baseline": self.baseline.record(), "version_policy": "DEFER_TO_P16_2",
                "channel_grants_trust": False}


@dataclass(frozen=True)
class ReleaseTarget(CanonicalModel):
    identifier: str
    native_profile: str = ""
    DOMAIN = "apexforge.release-target/v1"

    def __post_init__(self):
        require(type(self.identifier) is str and self.identifier in TARGETS, "RELEASE_TARGET_UNSUPPORTED")
        require(type(self.native_profile) is str and self.native_profile ==
                (PROFILE if self.identifier == "native-win-x64" else ""), "RELEASE_NATIVE_PROFILE_INVALID")

    def record(self):
        row = next(row for row in SURFACES if row[0] == self.identifier)
        return {"id": self.identifier, "support_scope": row[5], "native_profile": self.native_profile,
                "whole_language_native_support": False}


@dataclass(frozen=True)
class ReleaseArtifactIdentity(CanonicalModel):
    identifier: str
    DOMAIN = "apexforge.release-artifact-identity/v1"

    def __post_init__(self):
        text(self.identifier, "RELEASE_ARTIFACT_ID_INVALID")

    def record(self):
        return {"id": self.identifier}


@dataclass(frozen=True)
class ReleaseArtifactDescriptor(CanonicalModel):
    release: ReleaseIdentity
    identity: ReleaseArtifactIdentity
    target: ReleaseTarget
    role: str
    format: str
    filename: str
    surface_version: str
    availability: str
    package_coordinate: PackageCoordinate | None = None
    package_content: PackageContentIdentity | None = None
    references: tuple = ()
    provenance: tuple = ()
    DOMAIN = "apexforge.release-artifact-descriptor/v1"

    def __post_init__(self):
        require(type(self.release) is ReleaseIdentity and type(self.identity) is ReleaseArtifactIdentity
                and type(self.target) is ReleaseTarget, "RELEASE_DESCRIPTOR_INVALID")
        row = next(row for row in SURFACES if row[0] == self.target.identifier)
        require(type(self.role) is str and self.role == row[1] and type(self.format) is str
                and self.format in row[2], "RELEASE_ARTIFACT_ROLE_FORMAT_INVALID")
        require(type(self.filename) is str and "/" not in self.filename, "RELEASE_FILENAME_INVALID")
        try:
            PackagePath(self.filename)
        except ValueError as error:
            raise ReleaseArchitectureError("RELEASE_FILENAME_INVALID") from error
        require(self.filename.endswith("." + ({"wheel": "whl", "sdist": "tar.gz"}.get(self.format, self.format))),
                "RELEASE_FILENAME_INVALID")
        text(self.surface_version, "RELEASE_SURFACE_VERSION_INVALID")
        require(type(self.availability) is str and self.availability in AVAILABILITY, "RELEASE_AVAILABILITY_INVALID")
        require((self.package_coordinate is None and self.package_content is None) or
                (type(self.package_coordinate) is PackageCoordinate and type(self.package_content) is PackageContentIdentity),
                "RELEASE_PACKAGE_BINDING_INVALID")
        object.__setattr__(self, "references", ordered(self.references, ReleaseArtifactIdentity, "RELEASE_REFERENCE_INVALID"))
        require(self.identity not in self.references, "RELEASE_REFERENCE_INVALID")
        object.__setattr__(self, "provenance", ordered(self.provenance, CanonicalReference, "RELEASE_PROVENANCE_INVALID"))

    def record(self):
        row = next(row for row in SURFACES if row[0] == self.target.identifier)
        return {"release": self.release.record(), "artifact": self.identity.record(), "target": self.target.record(),
                "role": self.role, "format": self.format, "declared_filename": self.filename,
                "surface_version": self.surface_version, "availability": self.availability,
                "packaging_owner": row[3], "production_slice": row[4],
                "package_coordinate": None if self.package_coordinate is None else self.package_coordinate.record(),
                "package_content": None if self.package_content is None else self.package_content.record(),
                "references": [v.record() for v in self.references], "provenance": [v.record() for v in self.provenance],
                "artifact_bytes_exist": "NOT_ESTABLISHED", "checksum": "REQUIRED_AFTER_ARTIFACT_ASSEMBLY",
                "signing": "CRYPTO_PROVIDER_UNAVAILABLE", "signing_owner": "P16.11",
                "authentication": "NOT_ESTABLISHED", "grants_authority": False, "grants_trust": False,
                "semantic_authority": "CANONICAL_AIR"}


@dataclass(frozen=True)
class ReleaseArtifactMatrix(CanonicalModel):
    release: ReleaseIdentity
    artifacts: tuple
    DOMAIN = "apexforge.release-artifact-matrix/v1"

    def __post_init__(self):
        require(type(self.release) is ReleaseIdentity, "RELEASE_IDENTITY_INVALID")
        artifacts = ordered(self.artifacts, ReleaseArtifactDescriptor, "RELEASE_MATRIX_INVALID")
        require(bool(artifacts), "RELEASE_MATRIX_EMPTY")
        require(all(a.release == self.release for a in artifacts), "RELEASE_MATRIX_BASELINE_MISMATCH")
        ids = {a.identity for a in artifacts}
        require(len(ids) == len(artifacts), "RELEASE_ARTIFACT_DUPLICATE")
        require(all(r in ids for a in artifacts for r in a.references), "RELEASE_REFERENCE_DANGLING")
        filenames = {(a.target, a.filename) for a in artifacts}
        require(len(filenames) == len(artifacts), "RELEASE_FILENAME_DUPLICATE")
        object.__setattr__(self, "artifacts", artifacts)

    def record(self):
        return {"release": self.release.record(), "artifacts": [a.record() for a in self.artifacts],
                "relationship_semantics": "REFERENCE_ONLY", "execution": "NOT_PERFORMED",
                "publication": "NOT_PERFORMED", "installation": "NOT_PERFORMED"}
