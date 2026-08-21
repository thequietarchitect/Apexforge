"""Minimal immutable three-layer incremental-cache model.

P11.12B defines cache identity and entry data only. It does not perform cache
lookup, persistence, project building, semantic evaluation, or runtime work.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any, Tuple


CACHE_SCHEMA_VERSION = 1
CACHE_LAYER_IDS = ("capture", "resonance", "stability")
CACHE_FINGERPRINT_ALGORITHM = "sha256"

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def _require_text(value: object, owner: str) -> str:
    if type(value) is not str:
        raise TypeError("{} must be an exact str".format(owner))
    if not value or value.strip() != value:
        raise ValueError("{} must be non-empty trimmed text".format(owner))
    return value


def _require_sha256_hex(value: object, owner: str) -> str:
    selected = _require_text(value, owner)
    if _SHA256_HEX.fullmatch(selected) is None:
        raise ValueError(
            "{} must be exactly 64 lowercase SHA-256 hex characters".format(
                owner
            )
        )
    return selected


@dataclass(frozen=True)
class CacheFingerprint:
    """One canonical content or configuration fingerprint."""

    algorithm: str
    value: str

    def __post_init__(self) -> None:
        _require_text(self.algorithm, "CacheFingerprint.algorithm")
        if self.algorithm != CACHE_FINGERPRINT_ALGORITHM:
            raise ValueError(
                "CacheFingerprint.algorithm must be {!r}".format(
                    CACHE_FINGERPRINT_ALGORITHM
                )
            )
        _require_sha256_hex(self.value, "CacheFingerprint.value")


def cache_fingerprint(payload: bytes) -> CacheFingerprint:
    """Fingerprint exact bytes with the canonical P11.12 hash algorithm."""

    if type(payload) is not bytes:
        raise TypeError("cache_fingerprint payload must be exact bytes")
    return CacheFingerprint(
        algorithm=CACHE_FINGERPRINT_ALGORITHM,
        value=sha256(payload).hexdigest(),
    )


@dataclass(frozen=True)
class CacheDependency:
    """One ordered dependency on another canonical cache identity."""

    cache_key: str
    fingerprint: CacheFingerprint

    def __post_init__(self) -> None:
        _require_sha256_hex(self.cache_key, "CacheDependency.cache_key")
        if type(self.fingerprint) is not CacheFingerprint:
            raise TypeError(
                "CacheDependency.fingerprint must be exact CacheFingerprint"
            )


@dataclass(frozen=True)
class CacheIdentity:
    """Structured content-addressed identity for one owner-produced artifact."""

    schema_version: int
    layer_id: str
    artifact_kind: str
    owner: str
    subject: str
    input_fingerprint: CacheFingerprint
    configuration_fingerprint: CacheFingerprint
    dependencies: Tuple[CacheDependency, ...] = ()

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int:
            raise TypeError("CacheIdentity.schema_version must be exact int")
        if self.schema_version != CACHE_SCHEMA_VERSION:
            raise ValueError(
                "CacheIdentity.schema_version must equal CACHE_SCHEMA_VERSION"
            )
        _require_text(self.layer_id, "CacheIdentity.layer_id")
        if self.layer_id not in CACHE_LAYER_IDS:
            raise ValueError(
                "CacheIdentity.layer_id must be a canonical cache layer"
            )
        _require_text(self.artifact_kind, "CacheIdentity.artifact_kind")
        _require_text(self.owner, "CacheIdentity.owner")
        _require_text(self.subject, "CacheIdentity.subject")
        if type(self.input_fingerprint) is not CacheFingerprint:
            raise TypeError(
                "CacheIdentity.input_fingerprint must be exact CacheFingerprint"
            )
        if type(self.configuration_fingerprint) is not CacheFingerprint:
            raise TypeError(
                "CacheIdentity.configuration_fingerprint must be exact "
                "CacheFingerprint"
            )
        if type(self.dependencies) is not tuple:
            raise TypeError("CacheIdentity.dependencies must be an exact tuple")
        seen = set()
        for dependency in self.dependencies:
            if type(dependency) is not CacheDependency:
                raise TypeError(
                    "CacheIdentity.dependencies must contain exact "
                    "CacheDependency values"
                )
            if dependency.cache_key in seen:
                raise ValueError(
                    "CacheIdentity.dependencies must not duplicate cache keys"
                )
            seen.add(dependency.cache_key)


def cache_identity_key(identity: CacheIdentity) -> str:
    """Return the deterministic SHA-256 key for a structured cache identity."""

    if type(identity) is not CacheIdentity:
        raise TypeError("cache_identity_key identity must be exact CacheIdentity")

    payload = {
        "artifact_kind": identity.artifact_kind,
        "configuration_fingerprint": {
            "algorithm": identity.configuration_fingerprint.algorithm,
            "value": identity.configuration_fingerprint.value,
        },
        "dependencies": [
            {
                "cache_key": dependency.cache_key,
                "fingerprint": {
                    "algorithm": dependency.fingerprint.algorithm,
                    "value": dependency.fingerprint.value,
                },
            }
            for dependency in identity.dependencies
        ],
        "input_fingerprint": {
            "algorithm": identity.input_fingerprint.algorithm,
            "value": identity.input_fingerprint.value,
        },
        "layer_id": identity.layer_id,
        "owner": identity.owner,
        "schema_version": identity.schema_version,
        "subject": identity.subject,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


@dataclass(frozen=True)
class CacheEntry:
    """Immutable cache wrapper for one already owner-produced value."""

    identity: CacheIdentity
    artifact_fingerprint: CacheFingerprint
    value: Any

    def __post_init__(self) -> None:
        if type(self.identity) is not CacheIdentity:
            raise TypeError("CacheEntry.identity must be exact CacheIdentity")
        if type(self.artifact_fingerprint) is not CacheFingerprint:
            raise TypeError(
                "CacheEntry.artifact_fingerprint must be exact CacheFingerprint"
            )

    @property
    def cache_key(self) -> str:
        return cache_identity_key(self.identity)


__all__ = (
    "CACHE_SCHEMA_VERSION",
    "CACHE_LAYER_IDS",
    "CACHE_FINGERPRINT_ALGORITHM",
    "CacheFingerprint",
    "CacheDependency",
    "CacheIdentity",
    "CacheEntry",
    "cache_fingerprint",
    "cache_identity_key",
)