"""Canonical descriptor parsing for the P11.7 Quad-Vector Engine.

P11.7L parses caller-supplied JSON text associated with an already discovered
opaque descriptor candidate. Parsing preserves candidate identity and JSON field
order while recursively freezing values into immutable tuples. This layer does
not validate module semantics, canonicalize declarations, register, bind,
execute, import, or load implementations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Tuple

from .discovery import QuadVectorDiscoveryCandidate


class _JSONObjectPairs(tuple):
    """Internal marker preserving JSON-object identity and pair order."""


def _object_pairs(pairs):
    seen = set()
    ordered = []
    for key, value in pairs:
        if key in seen:
            raise ValueError("descriptor JSON object keys must be unique")
        seen.add(key)
        ordered.append((key, value))
    return _JSONObjectPairs(ordered)


def _freeze_json(value: Any) -> Any:
    if type(value) is _JSONObjectPairs:
        return tuple((key, _freeze_json(item)) for key, item in value)
    if type(value) is list:
        return tuple(_freeze_json(item) for item in value)
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise TypeError("descriptor JSON contains an unsupported value")


@dataclass(frozen=True)
class QuadVectorParsedDescriptor:
    """Immutable syntactic snapshot for one discovered descriptor."""

    candidate: QuadVectorDiscoveryCandidate
    fields: Tuple[Tuple[str, Any], ...]

    def __post_init__(self) -> None:
        if type(self.candidate) is not QuadVectorDiscoveryCandidate:
            raise TypeError(
                "candidate must be an exact QuadVectorDiscoveryCandidate"
            )
        if type(self.fields) is not tuple:
            raise TypeError("fields must be a tuple")
        keys = []
        for item in self.fields:
            if type(item) is not tuple or len(item) != 2:
                raise TypeError("fields must contain exact two-item tuples")
            key = item[0]
            if type(key) is not str:
                raise TypeError("descriptor field keys must be strings")
            keys.append(key)
        if len(set(keys)) != len(keys):
            raise ValueError("descriptor field keys must be unique")


def parse_quad_vector_descriptor(
    candidate: QuadVectorDiscoveryCandidate,
    descriptor_text: str,
) -> QuadVectorParsedDescriptor:
    """Parse caller-supplied JSON without advancing into semantic processing."""

    if type(candidate) is not QuadVectorDiscoveryCandidate:
        raise TypeError(
            "candidate must be an exact QuadVectorDiscoveryCandidate"
        )
    if type(descriptor_text) is not str:
        raise TypeError("descriptor_text must be a string")

    try:
        document = json.loads(
            descriptor_text,
            object_pairs_hook=_object_pairs,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("descriptor_text must contain valid unique-key JSON") from exc

    if type(document) is not _JSONObjectPairs:
        raise ValueError("descriptor document must be a JSON object")

    fields = tuple((key, _freeze_json(value)) for key, value in document)
    return QuadVectorParsedDescriptor(candidate=candidate, fields=fields)


__all__ = (
    "QuadVectorParsedDescriptor",
    "parse_quad_vector_descriptor",
)
