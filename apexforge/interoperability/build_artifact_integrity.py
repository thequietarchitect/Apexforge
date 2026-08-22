"""Passive build-artifact fingerprint integrity verification for P11.15D."""

from __future__ import annotations

import hashlib
import json

from tooling.build_artifact import (
    BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
    canonical_json_bytes,
)

from .build_artifact import BuildArtifactInterchange


def verify_build_artifact_interchange_fingerprint(
    interchange: BuildArtifactInterchange,
) -> str:
    """Verify one inspected build artifact's declared canonical fingerprint."""

    if type(interchange) is not BuildArtifactInterchange:
        raise TypeError(
            "verify_build_artifact_interchange_fingerprint requires an exact "
            "BuildArtifactInterchange"
        )

    text = interchange.content.decode("utf-8")
    value = json.loads(text)

    if type(value) is not dict:
        raise ValueError(
            "build artifact integrity content must contain a JSON object"
        )

    schema = value.get("schema")
    if type(schema) is not str or schema != interchange.schema:
        raise ValueError(
            "build artifact interchange schema/content mismatch"
        )

    fingerprint = value.get("fingerprint")
    if (
        type(fingerprint) is not dict
        or frozenset(fingerprint) != frozenset(("algorithm", "value"))
    ):
        raise ValueError(
            "build artifact fingerprint shape mismatch"
        )

    if (
        fingerprint["algorithm"] != BUILD_ARTIFACT_FINGERPRINT_ALGORITHM
        or type(fingerprint["value"]) is not str
    ):
        raise ValueError(
            "build artifact fingerprint shape mismatch"
        )

    payload = dict(value)
    del payload["fingerprint"]

    expected = hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()

    if fingerprint["value"] != expected:
        raise ValueError(
            "build artifact fingerprint mismatch"
        )

    return fingerprint["value"]


__all__ = (
    "verify_build_artifact_interchange_fingerprint",
)