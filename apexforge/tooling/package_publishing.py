"""P14.9 functional publication; caller identity authentication is an external precondition."""
from dataclasses import dataclass
from hashlib import sha256
import json
import re

from tooling.package_manifest import PackageManifest, PackageCoordinate, PackageContentIdentity, ExactVersion
from tooling.package_registry import RegistryCatalog, RegistryRecord, RegistryBlob
from tooling.package_trust import ContentMember, SignatureEnvelope, PackageTrustError, verify_integrity

SCHEMA = "apexforge.registry-publication/v1"


class PublicationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(condition, code):
    if not condition:
        raise PublicationError(code)


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _fingerprint(domain, value):
    return sha256((domain + "\0" + _json(value)).encode("utf-8")).hexdigest().upper()


@dataclass(frozen=True)
class PublisherPrincipal:
    identifier: str

    def __post_init__(self):
        _require(type(self.identifier) is str and re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", self.identifier),
                 "PUBLICATION_PRINCIPAL_INVALID")


@dataclass(frozen=True)
class PublicationGrant:
    publisher: PublisherPrincipal
    namespace: str

    def __post_init__(self):
        _require(type(self.publisher) is PublisherPrincipal, "PUBLICATION_POLICY_INVALID")
        try:
            PackageCoordinate(self.namespace, "validation", ExactVersion(0, 0, 0))
        except ValueError as exc:
            raise PublicationError("PUBLICATION_POLICY_INVALID") from exc

    def record(self):
        return {"publisher": self.publisher.identifier, "namespace": self.namespace}


@dataclass(frozen=True)
class PublicationPolicy:
    grants: tuple[PublicationGrant, ...]

    def __post_init__(self):
        _require(type(self.grants) is tuple and all(type(g) is PublicationGrant for g in self.grants),
                 "PUBLICATION_POLICY_INVALID")
        object.__setattr__(self, "grants", tuple(sorted(set(self.grants),
                           key=lambda g: (g.publisher.identifier, g.namespace))))

    def record(self):
        return {"schema": "apexforge.registry-publication-policy/v1", "grants": [g.record() for g in self.grants]}

    def fingerprint(self):
        return _fingerprint("apexforge.registry-publication-policy/v1", self.record())


@dataclass(frozen=True)
class PublicationRequest:
    publisher: PublisherPrincipal
    manifest: PackageManifest
    members: tuple[ContentMember, ...]
    expected_content: PackageContentIdentity
    signature: SignatureEnvelope | None = None
    schema: str = SCHEMA

    def __post_init__(self):
        _require(self.schema == SCHEMA, "PUBLICATION_SCHEMA_UNSUPPORTED")
        _require(type(self.publisher) is PublisherPrincipal, "PUBLICATION_PRINCIPAL_INVALID")
        _require(type(self.manifest) is PackageManifest and type(self.expected_content) is PackageContentIdentity
            and type(self.members) is tuple and all(type(m) is ContentMember for m in self.members)
            and (self.signature is None or type(self.signature) is SignatureEnvelope), "PUBLICATION_REQUEST_INVALID")
        object.__setattr__(self, "members", tuple(sorted(self.members, key=lambda m: m.path.value)))

    def record(self):
        return {"schema": self.schema, "publisher": self.publisher.identifier,
            "manifest": self.manifest.canonical_record(), "expected_content": self.expected_content.record(),
            "members": [{"path": m.path.value, "data_hex": m.data.hex()} for m in self.members],
            "signature": None if self.signature is None else self.signature.record()}

    def canonical_json(self):
        return _json(self.record())


def registry_state_fingerprint(catalog):
    """Full supplied state, including blobs; distinct from P14.8's record-only snapshot."""
    _require(type(catalog) is RegistryCatalog, "PUBLICATION_REQUEST_INVALID")
    return _fingerprint("apexforge.registry-publication-state/v1",
        {"records": [r.record() for r in catalog.records], "blobs": [b.record() for b in catalog.blobs]})


@dataclass(frozen=True)
class PublicationReceipt:
    canonical_json: str

    def record(self):
        return json.loads(self.canonical_json)

    def fingerprint(self):
        return _fingerprint("apexforge.registry-publication-receipt/v1", self.record())


@dataclass(frozen=True)
class PublicationResult:
    catalog: RegistryCatalog
    receipt: PublicationReceipt


def publish(catalog, request, policy):
    """Append exact content, or return an authorized identical retry without mutation."""
    _require(type(catalog) is RegistryCatalog and type(request) is PublicationRequest,
             "PUBLICATION_REQUEST_INVALID")
    try:
        integrity = verify_integrity(request.manifest, request.members)
    except PackageTrustError as exc:
        raise PublicationError("PUBLICATION_CONTENT_INTEGRITY_FAILED") from exc
    _require(integrity.valid, "PUBLICATION_CONTENT_INTEGRITY_FAILED")
    _require(request.expected_content == request.manifest.content_identity(),
             "PUBLICATION_CONTENT_IDENTITY_MISMATCH")
    _require(type(policy) is PublicationPolicy, "PUBLICATION_POLICY_INVALID")
    _require(PublicationGrant(request.publisher, request.manifest.coordinate.namespace) in policy.grants,
             "PUBLICATION_NAMESPACE_NOT_AUTHORIZED")
    existing = tuple(r for r in catalog.records if r.manifest.coordinate == request.manifest.coordinate)
    _require(not existing or (len(existing) == 1 and existing[0].identity == request.expected_content),
             "PUBLICATION_COORDINATE_CONTENT_CONFLICT")
    blobs = {b.digest: b for b in catalog.blobs}
    for member in request.members:
        digest = sha256(member.data).hexdigest().upper()
        if digest in blobs:
            _require(blobs[digest].data == member.data, "PUBLICATION_BLOB_CONFLICT")
        else:
            _require(not existing, "PUBLICATION_BLOB_CONFLICT")
            blobs[digest] = RegistryBlob(digest, member.data)
    if existing:
        result, status = catalog, "ALREADY_PRESENT"
    else:
        result = RegistryCatalog(catalog.records + (RegistryRecord(request.manifest, request.signature),),
                                 tuple(blobs.values()))
        status = "PUBLISHED_NEW"
    receipt = PublicationReceipt(_json({"schema": "apexforge.registry-publication-receipt/v1",
        "status": status, "publisher": request.publisher.identifier,
        "coordinate": request.manifest.coordinate.record(), "content_identity": request.expected_content.record(),
        "previous_state": registry_state_fingerprint(catalog), "resulting_state": registry_state_fingerprint(result),
        "policy_fingerprint": policy.fingerprint(), "authentication": "EXTERNAL_PRECONDITION",
        "signature_status": "NOT_VERIFIED" if (existing[0].signature if existing else request.signature) else "UNSIGNED",
        "provenance": [p.record() for p in request.manifest.provenance],
        "package_trust_granted": False, "runtime_authority_granted": False}))
    return PublicationResult(result, receipt)
