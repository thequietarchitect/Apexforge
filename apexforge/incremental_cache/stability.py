"""Stability-layer immutable owner-product reuse.

P11.12E records and reuses the two canonical Stability products that already
exist at this roadmap boundary:

- air.model.VerifiedAIRProgram
- workflow.air_runner.RegistryExecutionPlan

The cache owns identity/reuse metadata only. Semantic verification remains owned
by RuntimeValidator; execution-plan construction remains owned by
build_registry_execution_plan. This module adds no general store, persistence,
ProjectBuilder integration, runtime execution, continuity-checkpoint surrogate,
optimized-artifact surrogate, or AETHER-AIR reclassification.
"""

from __future__ import annotations

from typing import Callable, Optional, Tuple, Type

from air.model import VerifiedAIRProgram
from incremental_cache.model import (
    CACHE_SCHEMA_VERSION,
    CacheDependency,
    CacheEntry,
    CacheFingerprint,
    CacheIdentity,
)
from incremental_cache.resonance import (
    resonance_dependencies_fingerprint,
    resonance_dependency,
    resonance_input_fingerprint,
)
from workflow.air_runner import RegistryExecutionPlan


_STABILITY_LAYER = "stability"

_TYPE_SPECS = (
    (
        VerifiedAIRProgram,
        "verified-air",
        "air.model",
    ),
    (
        RegistryExecutionPlan,
        "execution-plan",
        "workflow.air_runner",
    ),
)


def _type_name(value: object) -> str:
    selected = value if isinstance(value, type) else type(value)
    return "{}.{}".format(selected.__module__, selected.__qualname__)


def _type_spec(expected_type: Type[object]) -> tuple[str, str]:
    if not isinstance(expected_type, type):
        raise TypeError("expected_type must be a type")
    for selected_type, artifact_kind, owner in _TYPE_SPECS:
        if expected_type is selected_type:
            return artifact_kind, owner
    raise TypeError(
        "expected_type {} is not an allowed Stability product".format(
            _type_name(expected_type)
        )
    )


def stability_input_fingerprint(value: object) -> CacheFingerprint:
    """Fingerprint explicit Stability producer input/configuration evidence."""

    return resonance_input_fingerprint(value)


def stability_fingerprint(value: object) -> CacheFingerprint:
    """Fingerprint one allowed immutable Stability owner product."""

    selected_type = type(value)
    if not any(selected_type is spec[0] for spec in _TYPE_SPECS):
        raise TypeError(
            "value type {} is not an allowed Stability product".format(
                _type_name(value)
            )
        )
    return resonance_input_fingerprint(value)


def stability_dependency(entry: CacheEntry) -> CacheDependency:
    """Project one exact lower-layer entry into Stability dependency metadata."""

    return resonance_dependency(entry)


def stability_dependencies_fingerprint(
    dependencies: Tuple[CacheDependency, ...],
) -> CacheFingerprint:
    """Fingerprint one exact ordered Stability dependency vector."""

    return resonance_dependencies_fingerprint(dependencies)


def stability_identity(
    expected_type: Type[object],
    *,
    subject: str,
    input_fingerprint: CacheFingerprint,
    configuration_fingerprint: CacheFingerprint,
    dependencies: Tuple[CacheDependency, ...] = (),
) -> CacheIdentity:
    """Build one structured identity for an allowed Stability product."""

    artifact_kind, owner = _type_spec(expected_type)

    if type(subject) is not str:
        raise TypeError("subject must be exact str")
    if not subject or subject.strip() != subject:
        raise ValueError("subject must be non-empty trimmed text")
    if type(input_fingerprint) is not CacheFingerprint:
        raise TypeError(
            "input_fingerprint must be exact CacheFingerprint"
        )
    if type(configuration_fingerprint) is not CacheFingerprint:
        raise TypeError(
            "configuration_fingerprint must be exact CacheFingerprint"
        )
    if type(dependencies) is not tuple:
        raise TypeError("dependencies must be exact tuple")
    for dependency in dependencies:
        if type(dependency) is not CacheDependency:
            raise TypeError(
                "dependencies must contain exact CacheDependency values"
            )

    return CacheIdentity(
        schema_version=CACHE_SCHEMA_VERSION,
        layer_id=_STABILITY_LAYER,
        artifact_kind=artifact_kind,
        owner=owner,
        subject=subject,
        input_fingerprint=input_fingerprint,
        configuration_fingerprint=configuration_fingerprint,
        dependencies=dependencies,
    )


def reuse_or_produce_stability(
    expected_type: Type[object],
    *,
    subject: str,
    input_fingerprint: CacheFingerprint,
    configuration_fingerprint: CacheFingerprint,
    producer: Callable[[], object],
    dependencies: Tuple[CacheDependency, ...] = (),
    cached: Optional[CacheEntry] = None,
) -> CacheEntry:
    """Reuse one valid Stability entry or invoke its canonical owner producer."""

    identity = stability_identity(
        expected_type,
        subject=subject,
        input_fingerprint=input_fingerprint,
        configuration_fingerprint=configuration_fingerprint,
        dependencies=dependencies,
    )

    if not callable(producer):
        raise TypeError("producer must be callable")
    if cached is not None and type(cached) is not CacheEntry:
        raise TypeError("cached must be None or exact CacheEntry")

    if (
        cached is not None
        and cached.identity == identity
        and type(cached.value) is expected_type
    ):
        try:
            expected_fingerprint = stability_fingerprint(cached.value)
        except TypeError:
            expected_fingerprint = None
        if (
            expected_fingerprint is not None
            and cached.artifact_fingerprint == expected_fingerprint
        ):
            return cached

    value = producer()
    if type(value) is not expected_type:
        raise TypeError(
            "producer returned {}; expected exact {}".format(
                _type_name(value),
                _type_name(expected_type),
            )
        )

    return CacheEntry(
        identity=identity,
        artifact_fingerprint=stability_fingerprint(value),
        value=value,
    )


__all__ = (
    "stability_input_fingerprint",
    "stability_fingerprint",
    "stability_dependency",
    "stability_dependencies_fingerprint",
    "stability_identity",
    "reuse_or_produce_stability",
)