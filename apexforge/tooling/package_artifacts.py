"""P14.11 supplied artifact bundles; no compilation, installation or execution."""
from dataclasses import dataclass
from hashlib import sha256
import json
import math

from tooling.package_manifest import (PackageManifest, PackageContentIdentity, PackagePath,
    CanonicalReference, SymbolReference)
from tooling.package_lock import PackageLock
from interoperability.build_artifact import inspect_build_artifact_interchange
from interoperability.build_artifact_integrity import verify_build_artifact_interchange_fingerprint
from native_backend.native_execution_contract import PROFILE

SCHEMA = "apexforge.package-artifacts/v1"
MANAGED_TARGET = "apexforge-managed"
MANAGED_PROFILE = "apexforge.build-artifact/v1"
NATIVE_TARGET = "win-x64"


class PackageArtifactError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(ok, code):
    if not ok:
        raise PackageArtifactError(code)


def _json(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _digest(data):
    return sha256(data).hexdigest().upper()


def _fingerprint(domain, record):
    return _digest((domain + "\0" + _json(record)).encode("utf-8"))


def _hash(value):
    try:
        PackageContentIdentity(value)  # Syntax only; domains retain distinct meanings.
    except ValueError as exc:
        raise PackageArtifactError("ARTIFACT_DIGEST_INVALID") from exc


def _parse_record(data):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "BUILD_EVIDENCE_INVALID")
            result[key] = value
        return result
    def integer(raw):
        _require(len(raw.lstrip("-")) <= 128, "BUILD_EVIDENCE_INVALID")
        return int(raw)
    def floating(raw):
        value = float(raw)
        _require(math.isfinite(value), "BUILD_EVIDENCE_INVALID")
        return value
    def reject(_):
        raise PackageArtifactError("BUILD_EVIDENCE_INVALID")
    try:
        _require(type(data) is bytes, "BUILD_EVIDENCE_INVALID")
        _require(len(data) <= 16 * 1024 * 1024, "BUILD_EVIDENCE_INVALID")
        record = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_int=integer,
                            parse_float=floating, parse_constant=reject)
        _require(type(record) is dict, "BUILD_EVIDENCE_INVALID")
        return record
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, PackageArtifactError):
            raise
        raise PackageArtifactError("BUILD_EVIDENCE_INVALID") from exc


@dataclass(frozen=True)
class ArtifactDescriptor:
    package: PackageContentIdentity
    kind: str
    path: PackagePath
    digest: str
    target: str
    profile: str
    build: CanonicalReference
    air: CanonicalReference
    source: CanonicalReference | None = None
    provenance: tuple[CanonicalReference, ...] = ()
    entrypoint: SymbolReference | None = None
    debug_metadata: CanonicalReference | None = None
    schema: str = SCHEMA

    def __post_init__(self):
        _require(self.schema == SCHEMA, "ARTIFACT_SCHEMA_UNSUPPORTED")
        _require(type(self.package) is PackageContentIdentity and type(self.path) is PackagePath,
                 "ARTIFACT_PACKAGE_BINDING_INVALID")
        _hash(self.digest)
        _require(type(self.kind) is str and self.kind in ("MANAGED", "NATIVE"), "ARTIFACT_KIND_UNSUPPORTED")
        expected = (MANAGED_TARGET, MANAGED_PROFILE) if self.kind == "MANAGED" else (NATIVE_TARGET, PROFILE)
        _require((self.target, self.profile) == expected, "UNSUPPORTED_TARGET")
        _require(type(self.build) is CanonicalReference and self.build.kind in ("artifact", "build-receipt")
            and type(self.air) is CanonicalReference and self.air.kind == "air", "ARTIFACT_BUILD_BINDING_INVALID")
        _require(self.source is None or type(self.source) is CanonicalReference and self.source.kind == "source",
                 "ARTIFACT_SOURCE_REFERENCE_INVALID")
        _require(type(self.provenance) is tuple and all(type(p) is CanonicalReference for p in self.provenance),
                 "ARTIFACT_PROVENANCE_INVALID")
        _require(self.entrypoint is None or type(self.entrypoint) is SymbolReference and
                 self.entrypoint.kind == "directive" and self.entrypoint.air_fingerprint == self.air.fingerprint,
                 "ARTIFACT_ENTRYPOINT_INVALID")
        _require(self.debug_metadata is None or type(self.debug_metadata) is CanonicalReference and
                 self.debug_metadata.kind in ("source-mapping", "native-mapping"), "ARTIFACT_DEBUG_REFERENCE_INVALID")
        object.__setattr__(self, "provenance", tuple(sorted(set(self.provenance), key=lambda p: _json(p.record()))))

    def record(self):
        return {"schema": self.schema, "package_content": self.package.record(), "kind": self.kind,
            "logical_path": self.path.value, "digest": self.digest, "target": self.target, "profile": self.profile,
            "role": "build-envelope" if self.kind == "MANAGED" else "native-image", "build": self.build.record(),
            "air": self.air.record(), "source": None if self.source is None else self.source.record(),
            "provenance": [p.record() for p in self.provenance],
            "entrypoint": None if self.entrypoint is None else self.entrypoint.record(),
            "debug_metadata": None if self.debug_metadata is None else self.debug_metadata.record()}

    def fingerprint(self):
        return _fingerprint("apexforge.package-artifact-descriptor/v1", self.record())


@dataclass(frozen=True)
class ArtifactPayload:
    digest: str
    data: bytes

    def __post_init__(self):
        _hash(self.digest)
        _require(type(self.data) is bytes and _digest(self.data) == self.digest, "ARTIFACT_PAYLOAD_DIGEST_MISMATCH")


def describe_managed(manifest, path, build_bytes, *, entrypoint=None, debug_metadata=None):
    """Admit an existing v1 AIR build envelope, verifying its frozen P11 fingerprint."""
    _require(type(manifest) is PackageManifest, "ARTIFACT_PACKAGE_BINDING_INVALID")
    record = _parse_record(build_bytes)
    _require(record.get("schema") == MANAGED_PROFILE and type(record.get("air")) is dict,
             "MANAGED_REPRESENTATION_UNSUPPORTED")
    try:
        fingerprint = verify_build_artifact_interchange_fingerprint(inspect_build_artifact_interchange(build_bytes))
    except (ValueError, TypeError) as exc:
        raise PackageArtifactError("BUILD_FINGERPRINT_MISMATCH") from exc
    if entrypoint is not None:
        _require(type(entrypoint) is SymbolReference and type(record.get("project")) is dict
            and record["project"].get("entry") == entrypoint.identity, "ARTIFACT_ENTRYPOINT_INVALID")
    air_bytes = json.dumps(record["air"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return ArtifactDescriptor(manifest.content_identity(), "MANAGED", path, _digest(build_bytes),
        MANAGED_TARGET, MANAGED_PROFILE, CanonicalReference(MANAGED_PROFILE, "artifact", fingerprint.upper()),
        CanonicalReference("apexforge.air-transport/v1", "air", _digest(air_bytes)),
        provenance=manifest.provenance, entrypoint=entrypoint, debug_metadata=debug_metadata)


def describe_native(manifest, path, image_bytes, receipt_bytes, receipt_fingerprint, *, target, profile,
                    entrypoint=None, debug_metadata=None):
    """Retain supplied P12 receipt linkage; this is not backend ticket issuance validation."""
    _require(type(manifest) is PackageManifest, "ARTIFACT_PACKAGE_BINDING_INVALID")
    _require((target, profile) == (NATIVE_TARGET, PROFILE), "UNSUPPORTED_TARGET")
    _require(type(image_bytes) is bytes, "ARTIFACT_PAYLOAD_DIGEST_MISMATCH")
    _hash(receipt_fingerprint)
    record = _parse_record(receipt_bytes)
    _require(set(record) == {"profile", "air", "routing", "entry", "owner_air", "states", "source",
                           "toolchain", "options", "image"}, "BUILD_EVIDENCE_INVALID")
    _require(_json(record).encode("utf-8") == receipt_bytes and _digest(receipt_bytes) == receipt_fingerprint,
             "BUILD_FINGERPRINT_MISMATCH")
    _require(record["profile"] == PROFILE and record["air"] == record["owner_air"], "ARTIFACT_BUILD_BINDING_INVALID")
    for field in ("air", "routing", "source", "image"):
        _hash(record[field])
    _require(record["image"] == _digest(image_bytes), "ARTIFACT_PAYLOAD_DIGEST_MISMATCH")
    _require(type(record["states"]) is list and all(type(s) is str for s in record["states"])
        and type(record["entry"]) is str and type(record["toolchain"]) is dict
        and type(record["options"]) is list and all(type(o) is str for o in record["options"]), "BUILD_EVIDENCE_INVALID")
    for value in record["toolchain"].values():
        _hash(value)
    if entrypoint is not None:
        _require(type(entrypoint) is SymbolReference and entrypoint.identity == record["entry"],
                 "ARTIFACT_ENTRYPOINT_INVALID")
    return ArtifactDescriptor(manifest.content_identity(), "NATIVE", path, record["image"], target, profile,
        CanonicalReference("apexforge.native-build-receipt/v1", "build-receipt", receipt_fingerprint),
        CanonicalReference("apexforge.air-transport/v1", "air", record["air"]),
        CanonicalReference("apexforge.native-generated-source/v1", "source", record["source"]),
        manifest.provenance, entrypoint, debug_metadata)


@dataclass(frozen=True)
class ArtifactBundle:
    package: PackageContentIdentity
    descriptors: tuple[ArtifactDescriptor, ...]
    payloads: tuple[ArtifactPayload, ...]

    def __post_init__(self):
        _require(type(self.package) is PackageContentIdentity and type(self.descriptors) is tuple and self.descriptors
            and all(type(d) is ArtifactDescriptor and d.package == self.package for d in self.descriptors),
                 "ARTIFACT_PACKAGE_BINDING_INVALID")
        _require(len({d.path.value.casefold() for d in self.descriptors}) == len(self.descriptors),
                 "ARTIFACT_PATH_DUPLICATE")
        paths = {d.path.value.casefold() for d in self.descriptors}
        _require(not any("/".join(p.split("/")[:i]) in paths for p in paths for i in range(1,len(p.split("/")))),
                 "ARTIFACT_PATH_CONFLICT")
        _require(type(self.payloads) is tuple and all(type(p) is ArtifactPayload for p in self.payloads),
                 "ARTIFACT_PAYLOAD_INVALID")
        _require(len({p.digest for p in self.payloads}) == len(self.payloads), "ARTIFACT_PAYLOAD_DUPLICATE")
        _require({d.digest for d in self.descriptors} == {p.digest for p in self.payloads}, "ARTIFACT_PAYLOAD_SET_MISMATCH")
        # Recheck supplied bytes, including adversarially corrupted otherwise-frozen fixtures.
        _require(all(_digest(p.data) == p.digest for p in self.payloads), "ARTIFACT_PAYLOAD_DIGEST_MISMATCH")
        object.__setattr__(self, "descriptors", tuple(sorted(self.descriptors, key=lambda d: _json(d.record()))))
        object.__setattr__(self, "payloads", tuple(sorted(self.payloads, key=lambda p: p.digest)))

    @property
    def kind(self):
        kinds = {d.kind for d in self.descriptors}
        return "HYBRID" if len(kinds) == 2 else next(iter(kinds))

    def canonical_record(self):
        return {"schema": SCHEMA, "package_content": self.package.record(), "kind": self.kind,
            "semantic_authority": "CANONICAL_AIR", "artifacts": [d.record() for d in self.descriptors]}

    def canonical_json(self):
        return _json(self.canonical_record())

    def fingerprint(self):
        return _fingerprint(SCHEMA, self.canonical_record())

    def bundle_record(self):
        return {"manifest": self.canonical_record(), "payloads": [
            {"digest": p.digest, "data_hex": p.data.hex()} for p in self.payloads]}

    def validate_lock(self, lock):
        _require(type(lock) is PackageLock and any(n.content_identity == self.package for n in lock.resolution.nodes),
                 "ARTIFACT_LOCK_CONTENT_MISMATCH")
        return self

    def select(self, kind, target=None, profile=None):
        _require(type(kind) is str and kind in ("MANAGED", "NATIVE", "ANY"), "ARTIFACT_KIND_UNSUPPORTED")
        if kind != "ANY" or target is not None or profile is not None:
            allowed = {(MANAGED_TARGET, MANAGED_PROFILE), (NATIVE_TARGET, PROFILE)}
            _require((target, profile) in allowed, "UNSUPPORTED_TARGET")
        candidates = tuple(d for d in self.descriptors if (kind == "ANY" or d.kind == kind)
            and (target is None or d.target == target) and (profile is None or d.profile == profile))
        _require(bool(candidates), "NO_SUPPORTED_VARIANT")
        _require(len(candidates) == 1, "AMBIGUOUS_VARIANT")
        return candidates[0]
