"""P14.6 supplied-byte integrity and passive signing/trust boundary.

No vetted asymmetric crypto provider is present in the tested environment.
Ed25519 envelopes are structural only; signature verification never reports VALID.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
import re

from tooling.package_manifest import PackageManifest, PackagePath
from tooling.package_lock import PackageLock

PAYLOAD_SCHEMA = "apexforge.package-signature-payload/v1"
SIGNATURE_SCHEMA = "apexforge.package-signature/v1"
ALGORITHM = "ed25519"


class PackageTrustError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(ok, code):
    if not ok:
        raise PackageTrustError(code)


def _json(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _digest(domain, data):
    return sha256(domain.encode("ascii") + b"\0" + data).hexdigest().upper()


def _hash(value):
    _require(type(value) is str and re.fullmatch(r"[A-F0-9]{64}", value) is not None,
             "SIGNATURE_MALFORMED")


def signing_payload(manifest):
    _require(type(manifest) is PackageManifest, "PACKAGE_MANIFEST_INVALID")
    # Content identity already commits to coordinate, member digests, declarations and provenance.
    return _json({"schema": PAYLOAD_SCHEMA, "coordinate": manifest.coordinate.record(),
                  "content_identity": manifest.content_identity().record()}).encode("utf-8")


def payload_fingerprint(manifest):
    return _digest("apexforge.package-signing-payload-fingerprint/v1", signing_payload(manifest))


def key_fingerprint(public_key):
    _require(type(public_key) is bytes and len(public_key) == 32, "PUBLIC_KEY_MALFORMED")
    # Canonical Ed25519 raw public-key representation, not a username or namespace.
    return _digest("apexforge.package-signing-key/v1", public_key)


@dataclass(frozen=True)
class ContentMember:
    path: PackagePath
    data: bytes

    def __post_init__(self):
        _require(type(self.path) is PackagePath and type(self.data) is bytes, "CONTENT_MEMBER_INVALID")


@dataclass(frozen=True)
class IntegrityResult:
    content_fingerprint: str
    diagnostics: tuple[tuple[str, str], ...]

    def __post_init__(self):
        _hash(self.content_fingerprint)
        _require(type(self.diagnostics) is tuple and all(type(d) is tuple and len(d) == 2
            and d[0] in ("CONTENT_MISSING", "CONTENT_UNEXPECTED", "CONTENT_DIGEST_MISMATCH")
            and type(d[1]) is str for d in self.diagnostics), "INTEGRITY_RESULT_INVALID")

    @property
    def valid(self):
        return not self.diagnostics

    def record(self):
        return {"content_fingerprint": self.content_fingerprint, "status": "VALID" if self.valid else "INVALID",
                "diagnostics": [{"code": code, "path": path} for code, path in self.diagnostics]}


def verify_integrity(manifest, members):
    _require(type(manifest) is PackageManifest and type(members) is tuple
        and all(type(m) is ContentMember for m in members), "INTEGRITY_INPUT_INVALID")
    paths = [m.path.value for m in members]
    _require(len({p.casefold() for p in paths}) == len(paths), "CONTENT_MEMBER_DUPLICATE")
    supplied = {m.path.value: m.data for m in members}
    expected = {m.path.value: m.digest for m in manifest.content}
    diagnostics = []
    for path in sorted(set(expected) | set(supplied)):
        if path not in supplied:
            diagnostics.append(("CONTENT_MISSING", path))
        elif path not in expected:
            diagnostics.append(("CONTENT_UNEXPECTED", path))
        elif sha256(supplied[path]).hexdigest().upper() != expected[path]:
            diagnostics.append(("CONTENT_DIGEST_MISMATCH", path))
    return IntegrityResult(manifest.content_identity().fingerprint, tuple(diagnostics))


@dataclass(frozen=True)
class SignatureEnvelope:
    signer_fingerprint: str
    payload_fingerprint: str
    signature: bytes
    algorithm: str = ALGORITHM
    schema: str = SIGNATURE_SCHEMA

    def __post_init__(self):
        _require(self.schema == SIGNATURE_SCHEMA, "SIGNATURE_SCHEMA_UNSUPPORTED")
        _require(self.algorithm == ALGORITHM, "SIGNATURE_ALGORITHM_UNSUPPORTED")
        _hash(self.signer_fingerprint)
        _hash(self.payload_fingerprint)
        _require(type(self.signature) is bytes and len(self.signature) == 64, "SIGNATURE_MALFORMED")

    def record(self):
        return {"schema": self.schema, "algorithm": self.algorithm, "signer_fingerprint": self.signer_fingerprint,
            "payload_fingerprint": self.payload_fingerprint, "signature_hex": self.signature.hex()}


@dataclass(frozen=True)
class TrustAnchor:
    public_key: bytes

    def __post_init__(self):
        key_fingerprint(self.public_key)

    @property
    def fingerprint(self):
        return key_fingerprint(self.public_key)


@dataclass(frozen=True)
class NamespaceTrustRule:
    signer_fingerprint: str
    namespace: str

    def __post_init__(self):
        _hash(self.signer_fingerprint)
        _require(type(self.namespace) is str and len(self.namespace) <= 255 and
            re.fullmatch(r"[a-z_][a-z0-9_]{0,63}(?:\.[a-z_][a-z0-9_]{0,63})*", self.namespace) is not None,
            "TRUST_SCOPE_INVALID")


@dataclass(frozen=True)
class TrustPolicy:
    anchors: tuple[TrustAnchor, ...] = ()
    rules: tuple[NamespaceTrustRule, ...] = ()
    require_signature: bool = True
    require_scope_trust: bool = True

    def __post_init__(self):
        _require(type(self.anchors) is tuple and all(type(a) is TrustAnchor for a in self.anchors)
            and type(self.rules) is tuple and all(type(r) is NamespaceTrustRule for r in self.rules)
            and type(self.require_signature) is bool and type(self.require_scope_trust) is bool,
            "TRUST_POLICY_INVALID")
        _require(not self.require_scope_trust or self.require_signature, "TRUST_POLICY_CONFLICT")
        anchors = tuple(sorted(set(self.anchors), key=lambda a: a.fingerprint))
        _require(len({a.fingerprint for a in anchors}) == len(anchors), "TRUST_ANCHOR_CONFLICT")
        _require(all(r.signer_fingerprint in {a.fingerprint for a in anchors} for r in self.rules),
                 "TRUST_RULE_ANCHOR_MISSING")
        object.__setattr__(self, "anchors", anchors)
        object.__setattr__(self, "rules", tuple(sorted(set(self.rules), key=lambda r: (r.namespace, r.signer_fingerprint))))

    def record(self):
        return {"schema": "apexforge.package-trust-policy/v1", "anchors": [a.fingerprint for a in self.anchors],
            "rules": [{"signer_fingerprint": r.signer_fingerprint, "namespace": r.namespace} for r in self.rules],
            "require_signature": self.require_signature, "require_scope_trust": self.require_scope_trust}

    def fingerprint(self):
        return _digest("apexforge.package-trust-policy-fingerprint/v1", _json(self.record()).encode("utf-8"))


@dataclass(frozen=True)
class VerificationEvidence:
    canonical_json: str

    def __post_init__(self):
        _require(type(self.canonical_json) is str, "VERIFICATION_EVIDENCE_INVALID")

    def record(self):
        return json.loads(self.canonical_json)


def verify_package(manifest, members, envelope=None, public_key=None, policy=None, lock=None):
    """Independent verification states; no asymmetric validity is fabricated."""
    integrity = verify_integrity(manifest, members)
    _require(envelope is None or type(envelope) is SignatureEnvelope, "SIGNATURE_MALFORMED")
    _require(policy is None or type(policy) is TrustPolicy, "TRUST_POLICY_INVALID")
    _require(lock is None or type(lock) is PackageLock, "LOCK_INVALID")
    key_id = None if public_key is None else key_fingerprint(public_key)
    payload_status = "NOT_APPLICABLE" if envelope is None else (
        "VALID" if envelope.payload_fingerprint == payload_fingerprint(manifest) else "SIGNING_PAYLOAD_MISMATCH")
    if envelope is None:
        signature_status = "UNSIGNED"
    elif payload_status != "VALID":
        signature_status = "NOT_VERIFIED"
    elif key_id != envelope.signer_fingerprint:
        signature_status = "SIGNER_KEY_FINGERPRINT_MISMATCH"
    else:
        signature_status = "CRYPTO_PROVIDER_UNAVAILABLE"
    signer_trust = "NOT_EVALUATED" if policy is None or key_id is None else (
        "SIGNER_TRUSTED" if key_id in {a.fingerprint for a in policy.anchors} else "SIGNER_UNTRUSTED")
    scope_trust = "NOT_EVALUATED" if signer_trust != "SIGNER_TRUSTED" else (
        "TRUSTED_FOR_PACKAGE_SCOPE" if NamespaceTrustRule(key_id, manifest.coordinate.namespace) in policy.rules
        else "TRUST_SCOPE_MISMATCH")
    lock_status = "NOT_APPLICABLE" if lock is None else (
        "MATCH" if any(n.coordinate == manifest.coordinate and n.content_identity == manifest.content_identity()
                       for n in lock.resolution.nodes) else "LOCK_CONTENT_MISMATCH")
    # No implicit acceptance policy. Signed material cannot bypass unavailable crypto.
    accepted = None if policy is None else (integrity.valid and lock_status != "LOCK_CONTENT_MISMATCH"
        and (signature_status == "VALID" or (signature_status == "UNSIGNED" and not policy.require_signature))
        and (not policy.require_scope_trust or scope_trust == "TRUSTED_FOR_PACKAGE_SCOPE"))
    record = {"schema": "apexforge.package-verification/v1", "coordinate": manifest.coordinate.record(),
        "content_identity": manifest.content_identity().record(), "integrity": integrity.record(),
        "signing_payload": payload_status, "signature": signature_status,
        "envelope": None if envelope is None else envelope.record(), "public_key_fingerprint": key_id,
        "signer_trust": signer_trust, "scope_trust": scope_trust, "lock": lock_status,
        "lock_fingerprint": None if lock is None else lock.fingerprint(),
        "policy_fingerprint": None if policy is None else policy.fingerprint(), "accepted": accepted,
        "provenance": [r.record() for r in manifest.provenance],
        "provenance_status": "REFERENCE_COMMITTED_CLAIM_UNVERIFIED", "non_identity_metadata": "UNSIGNED",
        "grants_runtime_authority": False}
    return VerificationEvidence(_json(record))
