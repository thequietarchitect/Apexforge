"""P14.8 transport-independent read-only protocol over supplied immutable evidence."""
from dataclasses import dataclass, field
from hashlib import sha256
import json
from types import MappingProxyType

from tooling.package_manifest import (PackageManifest, PackageCoordinate, PackageContentIdentity,
    ExactVersion, PackageManifestError, parse_manifest)
from tooling.package_solver import ResolvedPackage, PackageUniverse
from tooling.package_lock import PackageLock
from tooling.package_trust import SignatureEnvelope, PackageTrustError

SCHEMA = "apexforge.registry/v1"
OPERATIONS = frozenset(("coordinate", "content", "versions", "blob", "catalog"))
MAX_JSON_BYTES = 16 * 1024 * 1024
ERRORS = frozenset(("INVALID_REQUEST", "UNSUPPORTED_PROTOCOL_VERSION", "UNKNOWN_OPERATION",
    "PACKAGE_NOT_FOUND", "CONTENT_NOT_FOUND", "BLOB_NOT_FOUND", "AMBIGUOUS_COORDINATE",
    "REGISTRY_RECORD_INVALID", "CONTENT_IDENTITY_MISMATCH", "BLOB_DIGEST_MISMATCH",
    "RESPONSE_SCHEMA_INVALID"))


class RegistryError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(ok, code):
    if not ok:
        raise RegistryError(code)


def _json(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _object(value, keys, code):
    _require(type(value) is dict and set(value) == set(keys), code)
    return value


def _parse(text, code):
    _require(type(text) is str, code)
    def pairs(items):
        result = {}
        for k, v in items:
            _require(k not in result, code)
            result[k] = v
        return result
    def reject(_):
        raise RegistryError(code)
    def integer(raw):
        _require(len(raw.lstrip("-")) <= 10, code)
        return int(raw)
    try:
        _require(len(text.encode("utf-8")) <= MAX_JSON_BYTES, code)
        return json.loads(text, object_pairs_hook=pairs, parse_constant=reject, parse_int=integer)
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, RegistryError):
            raise
        raise RegistryError(code) from exc


def _identity(value):
    v = _object(value, ("domain", "fingerprint"), "CONTENT_IDENTITY_MISMATCH")
    return PackageContentIdentity(v["fingerprint"], v["domain"])


def _key(record):
    c = record.manifest.coordinate
    return (c.namespace, c.name, c.version.major, c.version.minor, c.version.patch,
            c.schema, record.identity.fingerprint)


@dataclass(frozen=True)
class RegistryRecord:
    manifest: PackageManifest
    signature: SignatureEnvelope | None = None

    def __post_init__(self):
        _require(type(self.manifest) is PackageManifest and (self.signature is None or
                 type(self.signature) is SignatureEnvelope), "REGISTRY_RECORD_INVALID")
        object.__setattr__(self, "manifest", ResolvedPackage(self.manifest).manifest)

    @property
    def identity(self):
        return self.manifest.content_identity()

    def record(self):
        return {"coordinate": self.manifest.coordinate.record(), "content_identity": self.identity.record(),
            "manifest": self.manifest.canonical_record(),
            "signature": None if self.signature is None else self.signature.record(),
            "signature_status": "NOT_VERIFIED" if self.signature is not None else "UNSIGNED"}

    @classmethod
    def from_mapping(cls, value):
        v = _object(value, ("coordinate", "content_identity", "manifest", "signature", "signature_status"),
                    "REGISTRY_RECORD_INVALID")
        try:
            manifest = parse_manifest(_json(v["manifest"]))
            signature = None
            if v["signature"] is not None:
                s = _object(v["signature"], ("schema", "algorithm", "signer_fingerprint",
                    "payload_fingerprint", "signature_hex"), "REGISTRY_RECORD_INVALID")
                _require(type(s["signature_hex"]) is str and len(s["signature_hex"]) == 128,
                         "REGISTRY_RECORD_INVALID")
                data = bytes.fromhex(s["signature_hex"])
                _require(data.hex() == s["signature_hex"], "REGISTRY_RECORD_INVALID")
                signature = SignatureEnvelope(s["signer_fingerprint"], s["payload_fingerprint"], data,
                                               s["algorithm"], s["schema"])
            result = cls(manifest, signature)
            _require(PackageCoordinate.from_mapping(v["coordinate"]) == manifest.coordinate
                and _identity(v["content_identity"]) == result.identity, "CONTENT_IDENTITY_MISMATCH")
            _require(v == result.record(), "REGISTRY_RECORD_INVALID")
            return result
        except (PackageManifestError, PackageTrustError, ValueError) as exc:
            if isinstance(exc, RegistryError):
                raise
            raise RegistryError("REGISTRY_RECORD_INVALID") from exc


@dataclass(frozen=True)
class RegistryBlob:
    digest: str
    data: bytes

    def __post_init__(self):
        try:
            PackageContentIdentity(self.digest)  # Syntax reuse only; digest means raw member bytes.
        except PackageManifestError as exc:
            raise RegistryError("BLOB_DIGEST_MISMATCH") from exc
        _require(type(self.data) is bytes and sha256(self.data).hexdigest().upper() == self.digest,
                 "BLOB_DIGEST_MISMATCH")

    def record(self):
        return {"digest": self.digest, "data_hex": self.data.hex()}


@dataclass(frozen=True)
class RegistryRequest:
    operation: str
    selector_json: str
    schema: str = SCHEMA

    def __post_init__(self):
        _require(self.schema == SCHEMA, "UNSUPPORTED_PROTOCOL_VERSION")
        _require(type(self.operation) is str and self.operation in OPERATIONS, "UNKNOWN_OPERATION")
        try:
            s = _parse(self.selector_json, "INVALID_REQUEST")
            if self.operation == "coordinate":
                s = PackageCoordinate.from_mapping(s).record()
            elif self.operation == "content":
                s = _identity(s).record()
            elif self.operation == "versions":
                s = _object(s, ("namespace", "name"), "INVALID_REQUEST")
                PackageCoordinate(s["namespace"], s["name"], ExactVersion(0, 0, 0))
            elif self.operation == "blob":
                s = _object(s, ("digest",), "INVALID_REQUEST")
                PackageContentIdentity(s["digest"])
            else:
                s = _object(s, (), "INVALID_REQUEST")
            object.__setattr__(self, "selector_json", _json(s))
        except PackageManifestError as exc:
            raise RegistryError("INVALID_REQUEST") from exc

    def record(self):
        return {"schema": self.schema, "operation": self.operation, "selector": json.loads(self.selector_json)}

    def canonical_json(self):
        return _json(self.record())

    @classmethod
    def parse(cls, text):
        v = _object(_parse(text, "INVALID_REQUEST"), ("schema", "operation", "selector"), "INVALID_REQUEST")
        return cls(v["operation"], _json(v["selector"]), v["schema"])


@dataclass(frozen=True)
class RegistryResponse:
    operation: str
    code: str = "OK"
    records: tuple[RegistryRecord, ...] = ()
    versions: tuple[ExactVersion, ...] = ()
    blob: RegistryBlob | None = None

    def __post_init__(self):
        _require(type(self.operation) is str and self.operation in OPERATIONS and
            type(self.code) is str and self.code in ERRORS | {"OK"}, "RESPONSE_SCHEMA_INVALID")
        _require(type(self.records) is tuple and all(type(r) is RegistryRecord for r in self.records)
            and type(self.versions) is tuple and all(type(v) is ExactVersion for v in self.versions)
            and (self.blob is None or type(self.blob) is RegistryBlob), "RESPONSE_SCHEMA_INVALID")
        _require(len({r.identity for r in self.records}) == len(self.records)
            and len(set(self.versions)) == len(self.versions), "RESPONSE_SCHEMA_INVALID")
        if self.code == "OK":
            valid = ((self.operation in ("coordinate", "content") and len(self.records) == 1
                and not self.versions and self.blob is None) or
                (self.operation == "catalog" and not self.versions and self.blob is None) or
                (self.operation == "versions" and not self.records and self.blob is None) or
                (self.operation == "blob" and self.blob is not None and not self.records and not self.versions))
        elif self.code == "AMBIGUOUS_COORDINATE":
            valid = self.operation == "coordinate" and len(self.records) > 1 and not self.versions and self.blob is None
            valid = valid and len({r.manifest.coordinate for r in self.records}) == 1
        else:
            valid = not self.records and not self.versions and self.blob is None
        _require(valid, "RESPONSE_SCHEMA_INVALID")
        object.__setattr__(self, "records", tuple(sorted(self.records, key=_key)))
        object.__setattr__(self, "versions", tuple(sorted(self.versions, key=lambda v: (v.major, v.minor, v.patch))))

    def record(self):
        return {"schema": SCHEMA, "operation": self.operation, "code": self.code,
            "status": "OK" if self.code == "OK" else "ERROR", "records": [r.record() for r in self.records],
            "versions": [v.text() for v in self.versions], "blob": None if self.blob is None else self.blob.record()}

    def canonical_json(self):
        return _json(self.record())

    @classmethod
    def parse(cls, text):
        v = _object(_parse(text, "RESPONSE_SCHEMA_INVALID"),
            ("schema", "operation", "code", "status", "records", "versions", "blob"), "RESPONSE_SCHEMA_INVALID")
        _require(v["schema"] == SCHEMA and type(v["records"]) is list and type(v["versions"]) is list,
                 "RESPONSE_SCHEMA_INVALID")
        try:
            blob = None
            if v["blob"] is not None:
                b = _object(v["blob"], ("digest", "data_hex"), "RESPONSE_SCHEMA_INVALID")
                _require(type(b["data_hex"]) is str, "RESPONSE_SCHEMA_INVALID")
                data = bytes.fromhex(b["data_hex"])
                _require(data.hex() == b["data_hex"], "RESPONSE_SCHEMA_INVALID")
                blob = RegistryBlob(b["digest"], data)
            result = cls(v["operation"], v["code"], tuple(RegistryRecord.from_mapping(r) for r in v["records"]),
                tuple(ExactVersion.parse(x) for x in v["versions"]), blob)
            _require(v["status"] == result.record()["status"], "RESPONSE_SCHEMA_INVALID")
            return result
        except (PackageManifestError, ValueError) as exc:
            if isinstance(exc, RegistryError):
                raise
            raise RegistryError("RESPONSE_SCHEMA_INVALID") from exc


@dataclass(frozen=True)
class RegistryCandidateSnapshot:
    records: tuple[RegistryRecord, ...]

    def __post_init__(self):
        _require(type(self.records) is tuple and all(type(r) is RegistryRecord for r in self.records),
                 "REGISTRY_RECORD_INVALID")
        _require(len({r.identity for r in self.records}) == len(self.records), "REGISTRY_RECORD_INVALID")
        object.__setattr__(self, "records", tuple(sorted(self.records, key=_key)))

    def canonical_json(self):
        return _json({"schema": "apexforge.registry-candidates/v1", "protocol": SCHEMA,
                      "records": [r.record() for r in self.records]})

    def fingerprint(self):
        return sha256(("apexforge.registry-snapshot/v1\0" + self.canonical_json()).encode("utf-8")).hexdigest().upper()

    def to_universe(self):
        # Explicit caller conversion; P14.2 still rejects coordinate/content conflicts.
        return PackageUniverse(tuple(r.manifest for r in self.records))


def validate_response(request, response):
    """Client-side association check, separate from an internally valid response record."""
    _require(type(request) is RegistryRequest and type(response) is RegistryResponse
        and request.operation == response.operation, "RESPONSE_SCHEMA_INVALID")
    s = json.loads(request.selector_json)
    if response.records and request.operation == "coordinate":
        coordinate = PackageCoordinate.from_mapping(s)
        _require(all(r.manifest.coordinate == coordinate for r in response.records), "CONTENT_IDENTITY_MISMATCH")
    if response.records and request.operation == "content":
        _require(response.records[0].identity == _identity(s), "CONTENT_IDENTITY_MISMATCH")
    if response.blob is not None:
        _require(response.blob.digest == s["digest"], "BLOB_DIGEST_MISMATCH")
    return response


@dataclass(frozen=True)
class RegistryCatalog:
    records: tuple[RegistryRecord, ...]
    blobs: tuple[RegistryBlob, ...] = ()
    _content: object = field(init=False, repr=False, compare=False)
    _coordinates: object = field(init=False, repr=False, compare=False)
    _versions: object = field(init=False, repr=False, compare=False)
    _blobs: object = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        _require(type(self.records) is tuple and all(type(r) is RegistryRecord for r in self.records)
            and type(self.blobs) is tuple and all(type(b) is RegistryBlob for b in self.blobs), "REGISTRY_RECORD_INVALID")
        content, coordinates, versions, blobs = {}, {}, {}, {}
        for record in sorted(self.records, key=_key):
            _require(record.identity not in content or content[record.identity] == record, "REGISTRY_RECORD_INVALID")
            content[record.identity] = record
        for record in content.values():
            c = record.manifest.coordinate
            coordinates.setdefault(c, []).append(record)
            versions.setdefault((c.namespace, c.name), set()).add(c.version)
        for blob in self.blobs:
            _require(blob.digest not in blobs or blobs[blob.digest] == blob, "BLOB_DIGEST_MISMATCH")
            blobs[blob.digest] = blob
        object.__setattr__(self, "records", tuple(content.values()))
        object.__setattr__(self, "blobs", tuple(blobs[k] for k in sorted(blobs)))
        for name, value in (("_content", content), ("_coordinates", {c: tuple(r) for c, r in coordinates.items()}),
                ("_versions", {c: tuple(sorted(v, key=lambda x: (x.major, x.minor, x.patch))) for c, v in versions.items()}),
                ("_blobs", blobs)):
            object.__setattr__(self, name, MappingProxyType(value))

    def query(self, request):
        _require(type(request) is RegistryRequest, "INVALID_REQUEST")
        s = json.loads(request.selector_json)
        op = request.operation
        if op == "catalog":
            return RegistryResponse(op, records=self.records)
        if op == "coordinate":
            records = self._coordinates.get(PackageCoordinate.from_mapping(s), ())
            return RegistryResponse(op, "PACKAGE_NOT_FOUND" if not records else
                "OK" if len(records) == 1 else "AMBIGUOUS_COORDINATE", records)
        if op == "content":
            record = self._content.get(_identity(s))
            return RegistryResponse(op, "CONTENT_NOT_FOUND" if record is None else "OK",
                                    () if record is None else (record,))
        if op == "versions":
            versions = self._versions.get((s["namespace"], s["name"]), ())
            return RegistryResponse(op, "PACKAGE_NOT_FOUND" if not versions else "OK", versions=versions)
        blob = self._blobs.get(s["digest"])
        return RegistryResponse(op, "BLOB_NOT_FOUND" if blob is None else "OK", blob=blob)

    def snapshot(self):
        return RegistryCandidateSnapshot(self.records)

    def locked_records(self, lock):
        _require(type(lock) is PackageLock, "INVALID_REQUEST")
        result = []
        for node in lock.resolution.nodes:
            record = self._content.get(node.content_identity)
            _require(record is not None, "CONTENT_NOT_FOUND")
            _require(ResolvedPackage(record.manifest) == node, "CONTENT_IDENTITY_MISMATCH")
            result.append(record)
        return RegistryCandidateSnapshot(tuple(result))
