"""Resonance-layer immutable owner-product reuse.

P11.12D records and reuses existing immutable Resonance products without
changing their semantic owners. This module owns cache metadata and integrity
fingerprints only. It introduces no general store, persistence, ProjectBuilder
integration, semantic evaluation, or runtime execution.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from decimal import Decimal
from enum import Enum
import json
import math
from pathlib import PurePath
from typing import Callable, Mapping, Optional, Tuple, Type

from incremental_cache.model import (
    CACHE_SCHEMA_VERSION,
    CacheDependency,
    CacheEntry,
    CacheFingerprint,
    CacheIdentity,
    cache_fingerprint,
)

from language.compiler import CompiledSource, SourceMap
from language.declarations import ProjectDeclarationOwnership
from language.identities import ProjectIdentityIndex
from language.modules import ModuleGraph, ProjectDocumentGraph
from language.narrative_graph import NarrativeSemanticGraph
from language.parser import SourceUnitNode
from language.resolution_candidates import ProjectResolutionCandidateIndex
from quad_vector import ResultantVector
from semantic_lattice.construction import SemanticLatticeSnapshot
from semantic_lattice.model import ParametricSemanticLattice
from tam import TraceMap


_RESONANCE_LAYER = "resonance"

_TYPE_SPECS = (
    (SourceUnitNode, "ast", "language.parser"),
    (ModuleGraph, "module-graph", "language.modules"),
    (ProjectDocumentGraph, "document-graph", "language.modules"),
    (CompiledSource, "compiled-source", "language.compiler"),
    (SourceMap, "source-map", "language.compiler"),
    (
        ProjectDeclarationOwnership,
        "declaration-ownership",
        "language.declarations",
    ),
    (ProjectIdentityIndex, "identity-index", "language.identities"),
    (
        ProjectResolutionCandidateIndex,
        "resolution-candidate-index",
        "language.resolution_candidates",
    ),
    (TraceMap, "trace-map", "tam"),
    (
        NarrativeSemanticGraph,
        "narrative-semantic-graph",
        "language.narrative_graph",
    ),
    (ResultantVector, "resultant-vector", "quad_vector"),
    (
        ParametricSemanticLattice,
        "parametric-semantic-lattice",
        "semantic_lattice.model",
    ),
    (
        SemanticLatticeSnapshot,
        "semantic-lattice-snapshot",
        "semantic_lattice.construction",
    ),
)


def _type_name(value: object) -> str:
    selected = value if isinstance(value, type) else type(value)
    return "{}.{}".format(selected.__module__, selected.__qualname__)


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def _canonical_data(value: object, seen: Optional[set[int]] = None) -> object:
    if seen is None:
        seen = set()

    if value is None or type(value) in (bool, int, str):
        return value

    if type(value) is float:
        if not math.isfinite(value):
            raise TypeError("non-finite float is not canonical Resonance data")
        return {"$float": repr(value)}

    if type(value) is bytes:
        return {"$bytes": value.hex()}

    if type(value) is Decimal:
        return {"$decimal": str(value)}

    if isinstance(value, PurePath):
        return {"$path": str(value)}

    if isinstance(value, Enum):
        return {
            "$enum": _type_name(value),
            "value": _canonical_data(value.value, seen),
        }

    if isinstance(value, type):
        return {"$type": _type_name(value)}

    identity = id(value)
    track = (
        is_dataclass(value)
        or type(value) in (tuple, list, dict, set, frozenset)
        or isinstance(value, Mapping)
        or hasattr(value, "__dict__")
        or hasattr(type(value), "__slots__")
    )
    if track:
        if identity in seen:
            raise TypeError("cyclic object is not canonical Resonance data")
        seen.add(identity)

    try:
        if is_dataclass(value) and not isinstance(value, type):
            return {
                "$dataclass": _type_name(value),
                "fields": [
                    [
                        field.name,
                        _canonical_data(getattr(value, field.name), seen),
                    ]
                    for field in fields(value)
                ],
            }

        if type(value) is tuple:
            return {
                "$tuple": [
                    _canonical_data(item, seen)
                    for item in value
                ]
            }

        if type(value) is list:
            return {
                "$list": [
                    _canonical_data(item, seen)
                    for item in value
                ]
            }

        if isinstance(value, Mapping):
            rows = []
            for key, item in value.items():
                encoded_key = _canonical_data(key, seen)
                encoded_value = _canonical_data(item, seen)
                rows.append(
                    (
                        _canonical_json_bytes(encoded_key),
                        encoded_key,
                        encoded_value,
                    )
                )
            rows.sort(key=lambda row: row[0])
            return {
                "$mapping": [
                    [key, item]
                    for _, key, item in rows
                ]
            }

        if type(value) in (set, frozenset):
            encoded = [
                _canonical_data(item, seen)
                for item in value
            ]
            encoded.sort(key=_canonical_json_bytes)
            return {
                "$set" if type(value) is set else "$frozenset":
                    encoded
            }

        if hasattr(value, "__dict__"):
            attributes = []
            for name, item in sorted(vars(value).items()):
                attributes.append(
                    [name, _canonical_data(item, seen)]
                )
            return {
                "$object": _type_name(value),
                "attributes": attributes,
            }

        slots = getattr(type(value), "__slots__", ())
        if type(slots) is str:
            slots = (slots,)
        if slots:
            attributes = []
            for name in sorted(slots):
                if hasattr(value, name):
                    attributes.append(
                        [name, _canonical_data(getattr(value, name), seen)]
                    )
            return {
                "$slotted": _type_name(value),
                "attributes": attributes,
            }
    finally:
        if track:
            seen.remove(identity)

    raise TypeError(
        "unsupported Resonance fingerprint value type {}".format(
            _type_name(value)
        )
    )


def resonance_input_fingerprint(value: object) -> CacheFingerprint:
    """Fingerprint one explicit owner input without interpreting its semantics."""

    return cache_fingerprint(
        _canonical_json_bytes(_canonical_data(value))
    )


def resonance_fingerprint(value: object) -> CacheFingerprint:
    """Fingerprint one allowed immutable Resonance owner product."""

    selected_type = type(value)
    if not any(selected_type is spec[0] for spec in _TYPE_SPECS):
        raise TypeError(
            "value type {} is not an allowed Resonance product".format(
                _type_name(value)
            )
        )
    return resonance_input_fingerprint(value)


def resonance_dependency(entry: CacheEntry) -> CacheDependency:
    """Project one exact cache entry into ordered dependency metadata."""

    if type(entry) is not CacheEntry:
        raise TypeError("entry must be exact CacheEntry")
    return CacheDependency(
        cache_key=entry.cache_key,
        fingerprint=entry.artifact_fingerprint,
    )


def resonance_dependencies_fingerprint(
    dependencies: Tuple[CacheDependency, ...],
) -> CacheFingerprint:
    """Fingerprint an exact ordered dependency vector."""

    if type(dependencies) is not tuple:
        raise TypeError("dependencies must be exact tuple")
    rows = []
    seen = set()
    for dependency in dependencies:
        if type(dependency) is not CacheDependency:
            raise TypeError(
                "dependencies must contain exact CacheDependency values"
            )
        if dependency.cache_key in seen:
            raise ValueError("dependencies must not repeat cache keys")
        seen.add(dependency.cache_key)
        rows.append(
            {
                "cache_key": dependency.cache_key,
                "fingerprint": {
                    "algorithm": dependency.fingerprint.algorithm,
                    "value": dependency.fingerprint.value,
                },
            }
        )
    return cache_fingerprint(_canonical_json_bytes(rows))


def _type_spec(expected_type: Type[object]) -> tuple[str, str]:
    if not isinstance(expected_type, type):
        raise TypeError("expected_type must be a type")
    for selected_type, artifact_kind, owner in _TYPE_SPECS:
        if expected_type is selected_type:
            return artifact_kind, owner
    raise TypeError(
        "expected_type {} is not an allowed Resonance product".format(
            _type_name(expected_type)
        )
    )


def resonance_identity(
    expected_type: Type[object],
    *,
    subject: str,
    input_fingerprint: CacheFingerprint,
    configuration_fingerprint: CacheFingerprint,
    dependencies: Tuple[CacheDependency, ...] = (),
) -> CacheIdentity:
    """Build one structured identity for an allowed Resonance product."""

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
        layer_id=_RESONANCE_LAYER,
        artifact_kind=artifact_kind,
        owner=owner,
        subject=subject,
        input_fingerprint=input_fingerprint,
        configuration_fingerprint=configuration_fingerprint,
        dependencies=dependencies,
    )


def reuse_or_produce_resonance(
    expected_type: Type[object],
    *,
    subject: str,
    input_fingerprint: CacheFingerprint,
    configuration_fingerprint: CacheFingerprint,
    producer: Callable[[], object],
    dependencies: Tuple[CacheDependency, ...] = (),
    cached: Optional[CacheEntry] = None,
) -> CacheEntry:
    """Reuse one valid Resonance entry or invoke its canonical owner producer."""

    identity = resonance_identity(
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
            expected_fingerprint = resonance_fingerprint(cached.value)
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
        artifact_fingerprint=resonance_fingerprint(value),
        value=value,
    )


__all__ = (
    "resonance_input_fingerprint",
    "resonance_fingerprint",
    "resonance_dependency",
    "resonance_dependencies_fingerprint",
    "resonance_identity",
    "reuse_or_produce_resonance",
)