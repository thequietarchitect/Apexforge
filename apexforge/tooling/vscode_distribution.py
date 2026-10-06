"""P16.6 release evidence around the frozen T3/T4 VSIX auditors.

No packager, dependency acquisition, extension activation, or publication API.
Inspection uses an explicitly supplied repository root and bounded supplied bytes.
"""
from dataclasses import dataclass, field
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
from zipfile import ZipFile, BadZipFile
from tooling.domain_platform import CanonicalModel
from tooling import release_architecture as r, release_build as b
from tooling import vscode_package as owner, vscode_lsp_activation as activation
from tooling.package_manifest import PackagePath, CanonicalReference

MAX_BYTES = b.MAX_BYTES
MAX_MEMBER = 512 * 1024
MAX_TOTAL = 4 * 1024 * 1024
MAX_MEMBERS = 1024
SOURCE_FILES = ("package.json", "language-configuration.json", "syntaxes/apexforge.tmLanguage.json",
                "README.md", "CHANGELOG.md", "extension.js", "runtime/lsp-client.js", "LANGUAGE_SERVER.md")
# Exact P15 Git blob projection, not platform checkout bytes or a new editor owner.
FROZEN_SOURCE_DIGESTS = (
    "393404F48C57C1D4887B27F6F6A796E606E40486365D8FD140337A97EF60CB80",
    "583DF5B35CA06C090A2AF590A08C47C1B822905B3B6430F267DE45A8CB7EBBF1",
    "80EC2C528EE37EC4C67DB6EBD40D2E8BBF8C48A872DA3CEDCAC3F90125A0808F",
    "990040AE71C7A4CB2AEEF40387D6D90587E42E3BA7F80F15C04A3C490E9861F1",
    "3791A395C77B073A4A01E101B6205BC052D19217609DFA024529106C5A516B29",
    "45E4B9D96A579A558055D24FDE05AE9806DAB1A70C0D2F3C42AD502CB5F98B3E",
    "853B5C026E65B9DB895C82AB322FCF267B41B57E87F2D819C1E1336C64D80145",
    "98FD6E92D7EA765FDC3CD280BEEB836C773E6453E70CA097BCD6CC6D75ED0F91")


class VSCodeDistributionError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(value, code):
    if not value:
        raise VSCodeDistributionError(code)


def digest(data):
    return sha256(data).hexdigest().upper()


def metadata(data):
    require(type(data) is bytes and len(data) <= 128 * 1024, "VSCODE_METADATA_INVALID")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "VSCODE_METADATA_INVALID")
            result[key] = value
        return result
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                           parse_constant=lambda _: require(False, "VSCODE_METADATA_INVALID"))
        require(type(value) is dict, "VSCODE_METADATA_INVALID")
        # Bounded input plus explicit iterative depth/count limit before canonicalization.
        stack, count = [(value, 0)], 0
        while stack:
            item, depth = stack.pop()
            count += 1
            require(depth <= 16 and count <= 4096, "VSCODE_METADATA_INVALID")
            require(type(item) is not float, "VSCODE_METADATA_INVALID")
            children = item.values() if type(item) is dict else item if type(item) is list else ()
            stack.extend((v, depth + 1) for v in children)
        return value
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, VSCodeDistributionError):
            raise
        raise VSCodeDistributionError("VSCODE_METADATA_INVALID") from error


@dataclass(frozen=True)
class VSCodeDistributionIdentity(CanonicalModel):
    release: r.ReleaseIdentity
    package_json: bytes = field(repr=False)
    DOMAIN = "apexforge.vscode-distribution-identity/v1"

    def __post_init__(self):
        require(type(self.release) is r.ReleaseIdentity and self.release.baseline == r.P15_BASELINE,
                "VSCODE_RELEASE_BINDING_INVALID")
        m = metadata(self.package_json)
        require(type(m.get("engines")) is dict, "VSCODE_METADATA_INVALID")
        require((m.get("name"), m.get("publisher"), m.get("version"), m["engines"].get("vscode")) ==
                ("apexforge-language", "gravitas-studios", "0.1.0", "^1.85.0"), "VSCODE_METADATA_MISMATCH")

    def record(self):
        return {"release": self.release.record(), "extension_id": owner.CANONICAL_VSCODE_EXTENSION_ID,
                "metadata": metadata(self.package_json), "manifest_digest": digest(self.package_json),
                "packaging_owner": "tooling.vscode_package", "activation_owner": "tooling.vscode_lsp_activation",
                "publisher_authenticated": False, "version_domain": "VSCODE_EXTENSION"}


def inventory(data):
    require(type(data) is bytes and 0 < len(data) <= MAX_BYTES, "VSCODE_ARCHIVE_SIZE_INVALID")
    rows, seen, total = [], set(), 0
    try:
        with ZipFile(BytesIO(data)) as archive:
            infos = archive.infolist()
            require(0 < len(infos) <= MAX_MEMBERS, "VSCODE_ARCHIVE_SIZE_INVALID")
            for info in infos:
                name = info.orig_filename
                parts = name.rstrip("/").split("/")
                require(name and not name.startswith("/") and "\\" not in name and ":" not in name
                        and all(p not in ("", ".", "..") for p in parts)
                        and all(ord(c) >= 32 for c in name), "VSCODE_ARCHIVE_PATH_INVALID")
                key = name.rstrip("/").casefold()
                require(key not in seen, "VSCODE_ARCHIVE_DUPLICATE")
                require(not any(key.startswith(p + "/") for p, _, _, _, directory in rows if not directory)
                        and not (not info.is_dir() and any(p.startswith(key + "/") for p in seen)),
                        "VSCODE_ARCHIVE_PATH_INVALID")
                seen.add(key)
                mode = info.external_attr >> 16
                require(stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR)
                        and not info.flag_bits & 1, "VSCODE_ARCHIVE_LINK_INVALID")
                require(info.file_size <= MAX_MEMBER, "VSCODE_ARCHIVE_SIZE_INVALID")
                total += info.file_size
                require(total <= MAX_TOTAL, "VSCODE_ARCHIVE_SIZE_INVALID")
                require(not any(p.casefold() in (".git", ".vscode", "__pycache__", "node_modules", "build", "dist")
                                for p in parts) and not key.endswith((".pyc", ".vsix", ".pypirc")),
                        "VSCODE_ARCHIVE_RESIDUE")
                payload = archive.read(info)
                require(len(payload) == info.file_size, "VSCODE_ARCHIVE_INVALID")
                if key.endswith(".json"):
                    metadata(payload)
                if key.endswith(".xml") or key == "extension.vsixmanifest":
                    require(len(payload) <= 128 * 1024 and b"<!DOCTYPE" not in payload.upper()
                            and b"<!ENTITY" not in payload.upper(), "VSCODE_XML_INVALID")
                rows.append((key, len(payload), digest(payload), tuple(info.date_time), info.is_dir()))
            # Metadata is explicit data only; never load extension.js or launch the server.
    except (BadZipFile, OSError, RuntimeError, NotImplementedError, UnicodeError) as error:
        raise VSCodeDistributionError("VSCODE_ARCHIVE_INVALID") from error
    return tuple(sorted(rows)), tuple(i.filename for i in infos)


@dataclass(frozen=True)
class VSIXReleaseEvidence(CanonicalModel):
    identity: VSCodeDistributionIdentity
    descriptor: r.ReleaseArtifactDescriptor
    data: bytes = field(repr=False)
    source_files: tuple = field(repr=False)
    DOMAIN = "apexforge.vscode-vsix-release-evidence/v1"

    def __post_init__(self):
        require(type(self.identity) is VSCodeDistributionIdentity and type(self.descriptor) is r.ReleaseArtifactDescriptor,
                "VSCODE_RELEASE_BINDING_INVALID")
        d = self.descriptor
        require(d.release == self.identity.release and d.target == r.ReleaseTarget("vscode")
                and d.surface_version == "0.1.0" and d.filename == owner.CANONICAL_VSIX_FILENAME
                and d.availability != "UNAVAILABLE", "VSCODE_RELEASE_BINDING_INVALID")
        require(type(self.source_files) is tuple and len(self.source_files) == len(SOURCE_FILES)
                and all(type(row) is tuple and len(row) == 2 and type(row[0]) is str
                        and type(row[1]) is bytes and len(row[1]) <= MAX_MEMBER for row in self.source_files),
                "VSCODE_SOURCE_INVALID")
        sources = dict(self.source_files)
        require(len(sources) == len(SOURCE_FILES) and set(sources) == set(SOURCE_FILES)
                and sources["package.json"] == self.identity.package_json, "VSCODE_SOURCE_INVALID")
        require(all(digest(sources[name]) == expected for name, expected in zip(SOURCE_FILES, FROZEN_SOURCE_DIGESTS)),
                "VSCODE_FROZEN_SOURCE_MISMATCH")
        inventory(self.data)
        with ZipFile(BytesIO(self.data)) as archive:
            index = {i.filename.casefold(): i for i in archive.infolist()}
            for name, payload in sources.items():
                key = "extension/" + name.casefold()
                require(key in index and archive.read(index[key]) == payload, "VSCODE_SOURCE_CONTINUITY_MISMATCH")
            require("[content_types].xml" in index and "extension.vsixmanifest" in index,
                    "VSCODE_ARCHIVE_STRUCTURE_INVALID")
            try:
                owner._validate_content_types(archive.read(index["[content_types].xml"]))
                owner._validate_vsix_manifest(archive.read(index["extension.vsixmanifest"]))
                owner._validate_embedded_package(metadata(self.identity.package_json))
            except owner.VSCodePackageError as error:
                raise VSCodeDistributionError("VSCODE_FROZEN_OWNER_REJECTED") from error
        object.__setattr__(self, "source_files", tuple(sorted(self.source_files)))

    def record(self):
        rows, order = inventory(self.data)
        return {"identity": self.identity.record(), "descriptor": self.descriptor.record(),
                "length": len(self.data), "sha256": digest(self.data),
                "inventory": [{"path": p, "length": n, "sha256": h, "timestamp": list(t), "directory": d}
                              for p, n, h, t, d in rows], "archive_order": list(order),
                "source": [{"path": p, "sha256": digest(v)} for p, v in self.source_files],
                "source_continuity": True, "authentication": "CRYPTO_PROVIDER_UNAVAILABLE",
                "owner_references": {"T3": owner.CANONICAL_VSCODE_PACKAGE_SHA256,
                                     "T4": activation.CANONICAL_VSCODE_LSP_ACTIVATION_SHA256},
                "grants_trust": False, "grants_authority": False, "grants_compatibility": False,
                "installed": False, "published": False, "executed": False}

    def build_artifact(self):
        ref = CanonicalReference(self.DOMAIN, "source", self.fingerprint())
        inp = b.ReleaseBuildInput(self.identity.release, PackagePath(self.descriptor.filename),
                                  "EXISTING_ARTIFACT", self.data, digest(self.data), ref, (ref,))
        recipe = b.ReleaseBuildRecipe("vscode-release-evidence", self.identity.release, "COPY_BYTES",
                 b.ReleaseBuildEnvironment("vscode-inspected-bytes", "tooling.vscode_package"),
                 (inp,), (b.ReleaseBuildOutputSlot(self.descriptor, inp.identity),), (ref,))
        return b.ReleaseBuildArtifact(recipe, self.descriptor.identity, self.data, digest(self.data))


def inspect_vsix(repository_root, descriptor, data, source_files=None):
    """Fixed-path read-only source inspection; bounded temporary VSIX, no discovery.

    Both frozen owner audits must pass. The temporary path never enters evidence.
    This accepts externally constructed bytes; it does not claim a local VSCE build.
    """
    require(type(descriptor) is r.ReleaseArtifactDescriptor, "VSCODE_RELEASE_BINDING_INVALID")
    inventory(data)  # Reject hostile input before legacy archive readers see it.
    root = Path(repository_root).resolve()
    source = root / "editors" / "vscode-apexforge"
    try:
        files = tuple((name, (source / name).read_bytes()) for name in SOURCE_FILES) if source_files is None else source_files
        identity = VSCodeDistributionIdentity(descriptor.release, dict(files)["package.json"])
        evidence = VSIXReleaseEvidence(identity, descriptor, data, files)
        with TemporaryDirectory(prefix="apexforge-vsix-inspection-") as temporary:
            # Explicit supplied source projection; preserve every byte. This also
            # allows exact frozen Git blob bytes rather than a CRLF checkout.
            projection = Path(temporary) / "source"
            for name, payload in evidence.source_files:
                target = projection / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            (projection / ".vscodeignore").write_bytes((source / ".vscodeignore").read_bytes())
            path = Path(temporary) / descriptor.filename
            path.write_bytes(data)
            owner.audit_vscode_vsix(projection, path, repository_root=root)
            activation.audit_vscode_lsp_vsix(projection, path)
        return evidence
    except (owner.VSCodePackageError, activation.VSCodeLSPActivationError, OSError) as error:
        raise VSCodeDistributionError("VSCODE_FROZEN_OWNER_REJECTED") from error


def compare_packages(left, right):
    require(type(left) is VSIXReleaseEvidence and type(right) is VSIXReleaseEvidence, "VSCODE_EVIDENCE_INVALID")
    same_context = left.identity == right.identity and left.descriptor == right.descriptor and left.source_files == right.source_files
    def content(value):
        return tuple((p, n, h, d) for p, n, h, _, d in inventory(value.data)[0])
    return {"context_equal": same_context,
            "member_content_equal": same_context and content(left) == content(right),
            "raw_bytes_equal": same_context and left.data == right.data,
            "authentication": False}
