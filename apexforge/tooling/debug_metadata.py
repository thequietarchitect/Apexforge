"""Compiler/tooling-owned observational metadata identities (P12.6-3).

No source-map file format, source correspondence inference, admission, emission,
or execution. Canonical forms below are in-memory fingerprint preimages only.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Union

from air.model import VerifiedAIRProgram
from language.compiler import SourceMap, SourceMapEntry
from language.source import SourcePosition, SourceSpan, SourceText
from apexforge.native_backend.lowering_input import build_verified_air_lowering_input
from apexforge.native_backend.execution_plan_binding import bind_registry_execution_plan

OWNER = "COMPILER_TOOLING_SIDECAR"
SCHEMA = "apexforge.metadata-identity/v1"


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _digest(value):
    # Not an interchange format or a source-map serializer.
    return sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                             allow_nan=False).encode("utf-8")).hexdigest().upper()


def _hash(value):
    _require(type(value) is str and re.fullmatch(r"[0-9A-F]{64}", value) is not None,
             "exact uppercase SHA-256 required")


def _index(value):
    _require(type(value) is int and value >= 0, "nonnegative occurrence index required")


def _id(value):
    _require(type(value) is str and bool(value) and value == value.strip(), "exact AIR ID required")


def _tuple(value, item_type):
    _require(type(value) is tuple and all(type(x) is item_type for x in value),
             "immutable exact-value tuple required")


@dataclass(frozen=True)
class SourceIdentity:
    logical_name: str
    content_fingerprint: str

    def __post_init__(self):
        name = self.logical_name
        _require(type(name) is str and bool(name) and name == name.strip(), "logical source name required")
        _require(not any(ord(c) < 32 or c in "\\:" for c in name), "nonportable source name")
        _require(all(part not in ("", ".", "..") for part in name.split("/")), "project-relative source required")
        _hash(self.content_fingerprint)

    @classmethod
    def from_bytes(cls, logical_name, content):
        _require(type(content) is bytes, "governed UTF-8 bytes required")
        content.decode("utf-8")  # exact snapshot; no newline/BOM normalization
        return cls(logical_name, sha256(content).hexdigest().upper())

    def canonical_identity(self):
        return (SCHEMA, "source", self.logical_name, self.content_fingerprint, "utf-8")

    def fingerprint(self):
        return _digest(self.canonical_identity())

    def validate_content(self, content):
        _require(self == self.from_bytes(self.logical_name, content), "stale source fingerprint")


@dataclass(frozen=True)
class StateLocator:
    state_index: int
    state_id: str

    def __post_init__(self):
        _index(self.state_index)
        _id(self.state_id)

    def canonical_identity(self):
        return ("state-initialization", self.state_index, self.state_id)

    def validate(self, program):
        _require(self.state_index < len(program.states), "missing state occurrence")
        _require(sum(s.id == self.state_id for s in program.states) == 1, "missing/ambiguous state ID")
        _require(program.states[self.state_index].id == self.state_id, "state occurrence mismatch")


@dataclass(frozen=True)
class AssignmentLocator:
    directive_index: int
    directive_id: str
    decision_occurrence: int
    decision_id: str
    path_index: int
    path_id: str
    assignment_index: int

    def __post_init__(self):
        for value in (self.directive_index, self.decision_occurrence, self.path_index, self.assignment_index):
            _index(value)
        for value in (self.directive_id, self.decision_id, self.path_id):
            _id(value)

    def canonical_identity(self):
        return ("assignment", self.directive_index, self.directive_id, self.decision_occurrence,
                self.decision_id, self.path_index, self.path_id, self.assignment_index)

    def validate(self, program):
        # Check explicit canonical references; never resolve a source name or select a path.
        _require(self.directive_index < len(program.directives), "missing directive occurrence")
        _require(sum(d.id == self.directive_id for d in program.directives) == 1,
                 "missing/ambiguous directive ID")
        directive = program.directives[self.directive_index]
        _require(directive.id == self.directive_id, "directive occurrence mismatch")
        _require(self.decision_occurrence < len(directive.causal_decisions), "missing decision occurrence")
        _require(directive.causal_decisions[self.decision_occurrence] == self.decision_id,
                 "decision occurrence mismatch")
        matches = tuple(d for d in program.causal_decisions if d.id == self.decision_id)
        _require(len(matches) == 1, "missing/ambiguous canonical decision reference")
        paths = matches[0].paths
        _require(self.path_index < len(paths), "missing path occurrence")
        _require(sum(p.id == self.path_id for p in paths) == 1, "missing/ambiguous path ID")
        path = paths[self.path_index]
        _require(path.id == self.path_id, "path occurrence mismatch")
        _require(self.assignment_index < len(path.assignments), "missing assignment occurrence")


Locator = Union[StateLocator, AssignmentLocator]


@dataclass(frozen=True)
class AIRMetadataIdentity:
    air_fingerprint: str
    locator: Locator

    def __post_init__(self):
        _hash(self.air_fingerprint)
        _require(type(self.locator) in (StateLocator, AssignmentLocator), "unsupported structural correspondence")

    def canonical_identity(self):
        return (SCHEMA, "air-reference", self.air_fingerprint, self.locator.canonical_identity())

    def fingerprint(self):
        return _digest(self.canonical_identity())

    def validate(self, verified):
        _require(type(verified) is VerifiedAIRProgram, "canonical verified AIR required")
        current = build_verified_air_lowering_input(verified)
        _require(current.transport_fingerprint == self.air_fingerprint, "stale AIR fingerprint")
        self.locator.validate(current.program)


@dataclass(frozen=True)
class OperationReference:
    ordinal: int
    identity: AIRMetadataIdentity

    def __post_init__(self):
        _index(self.ordinal)
        _require(type(self.identity) is AIRMetadataIdentity, "AIR metadata identity required")

    def canonical_identity(self):
        return (SCHEMA, "operation", self.ordinal, self.identity.canonical_identity())

    @property
    def operation_id(self):
        return "af-meta-op:" + _digest(self.canonical_identity())


@dataclass(frozen=True)
class EvidenceReference:
    """Explicit producer-supplied reference, NOT an inferred source mapping."""
    operation_id: str
    source_index: int
    source_map_index: int

    def __post_init__(self):
        _require(type(self.operation_id) is str and self.operation_id.startswith("af-meta-op:"),
                 "operation ID required")
        _hash(self.operation_id[len("af-meta-op:"):])
        _index(self.source_index)
        _index(self.source_map_index)


def _entry_identity(entry):
    _require(type(entry) is SourceMapEntry, "exact compiler evidence required")
    for value in (entry.air_id, entry.kind, entry.reference):
        _require(type(value) is str and not any(ord(c) < 32 for c in value), "exact evidence string required")
        _require(not value.startswith("/") and "\\" not in value and
                 re.match(r"^[A-Za-z]:", value) is None, "host-path evidence contamination")
    span = entry.span
    _require(type(span) is SourceSpan, "canonical span required")
    _require(type(span.start) is SourcePosition and type(span.end) is SourcePosition, "canonical positions required")
    return (entry.air_id, entry.kind, entry.reference, span.source_name,
            (span.start.line, span.start.column, span.start.offset),
            (span.end.line, span.end.column, span.end.offset))


@dataclass(frozen=True)
class MetadataSidecar:
    sources: tuple[SourceIdentity, ...]
    air_fingerprint: str
    source_map: SourceMap
    operations: tuple[OperationReference, ...]
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self):
        _tuple(self.sources, SourceIdentity)
        _tuple(self.operations, OperationReference)
        _tuple(self.evidence, EvidenceReference)
        _hash(self.air_fingerprint)
        _require(type(self.source_map) is SourceMap, "existing compiler SourceMap required")
        names = tuple(s.logical_name for s in self.sources)
        _require(len(set(n.casefold() for n in names)) == len(names), "ambiguous source identity")
        _require(names == tuple(sorted(names, key=lambda n: (n.casefold(), n))), "noncanonical source order")
        _require(tuple(op.ordinal for op in self.operations) == tuple(range(len(self.operations))),
                 "operation order/occurrence mismatch")
        ids = tuple(op.operation_id for op in self.operations)
        _require(len(set(ids)) == len(ids), "duplicate operation ID")
        _require(len(set(op.identity for op in self.operations)) == len(self.operations),
                 "duplicate structural operation")
        _require(all(op.identity.air_fingerprint == self.air_fingerprint for op in self.operations),
                 "operation AIR mismatch")
        for entry in self.source_map.entries:
            _entry_identity(entry)
            _require(entry.span.source_name in names, "ungoverned source-map span")
            _require(type(entry.kind) is str and type(entry.reference) is str, "exact evidence strings required")
        for ref in self.evidence:
            _require(ref.operation_id in ids, "missing operation ID")
            _require(ref.source_index < len(self.sources) and ref.source_map_index < len(self.source_map.entries),
                     "missing evidence occurrence")
            _require(self.source_map.entries[ref.source_map_index].span.source_name ==
                     self.sources[ref.source_index].logical_name, "source/evidence mismatch")
        keys = tuple((r.operation_id, r.source_index, r.source_map_index) for r in self.evidence)
        _require(len(set(keys)) == len(keys) and keys == tuple(sorted(keys)), "noncanonical/duplicate evidence order")

    def canonical_identity(self):
        return (SCHEMA, OWNER, tuple(s.canonical_identity() for s in self.sources), self.air_fingerprint,
                tuple(_entry_identity(e) for e in self.source_map.entries),
                tuple(op.canonical_identity() for op in self.operations),
                tuple((r.operation_id, r.source_index, r.source_map_index) for r in self.evidence))

    def fingerprint(self):
        return _digest(self.canonical_identity())

    def validate(self, verified, source_contents, required_operations):
        # External expected occurrence list prevents a partial sidecar claiming full coverage.
        _require(type(source_contents) is tuple and len(source_contents) == len(self.sources), "source snapshots required")
        _require(type(required_operations) is tuple and all(type(x) is AIRMetadataIdentity for x in required_operations),
                 "explicit required operations required")
        _require(type(verified) is VerifiedAIRProgram, "canonical verified AIR required")
        current = build_verified_air_lowering_input(verified)
        _require(current.transport_fingerprint == self.air_fingerprint, "stale AIR fingerprint")
        _require(tuple(op.identity for op in self.operations) == required_operations, "missing/reordered required operation")
        for source, content in zip(self.sources, source_contents):
            source.validate_content(content)
            text = SourceText(source.logical_name, content.decode("utf-8"))
            for entry in self.source_map.entries:
                if entry.span.source_name == source.logical_name:
                    span = entry.span
                    _require(text.span(span.start.offset, span.end.offset) == span, "malformed source span")
        for op in self.operations:
            op.identity.validate(verified)


@dataclass(frozen=True)
class MetadataAssociation:
    """External provenance reference; never added to RegistryExecutionPlan."""
    sidecar_fingerprint: str
    air_fingerprint: str
    routing_fingerprint: str
    entry_directive: str
    owner_fingerprints: tuple[tuple[str, str], ...]

    def __post_init__(self):
        for value in (self.sidecar_fingerprint, self.air_fingerprint, self.routing_fingerprint):
            _hash(value)
        _id(self.entry_directive)
        _require(type(self.owner_fingerprints) is tuple, "immutable owner references required")
        for pair in self.owner_fingerprints:
            _require(type(pair) is tuple and len(pair) == 2, "owner reference pair required")
            _id(pair[0])
            _hash(pair[1])
        keys = tuple(pair[0] for pair in self.owner_fingerprints)
        _require(keys == tuple(sorted(set(keys))), "ambiguous/noncanonical owner references")

    @classmethod
    def for_plan(cls, sidecar, verified, plan, source_contents, required_operations):
        sidecar.validate(verified, source_contents, required_operations)
        lowering = build_verified_air_lowering_input(verified)
        binding = bind_registry_execution_plan(lowering, plan)
        _require(sum(d.id == binding.entry_directive for d in plan.program.directives) == 1,
                 "missing/ambiguous entry reference")
        for key in binding.directive_owner_ids:
            _require(sum(d.id.casefold() == key for d in plan.program.directives) == 1,
                     "missing/ambiguous routed directive")
            _require(sum(d.id.casefold() == key for d in plan.directive_owners[key].directives) == 1,
                     "missing/ambiguous owner directive")
        owners = tuple((key, build_verified_air_lowering_input(VerifiedAIRProgram(plan.directive_owners[key])).transport_fingerprint)
                       for key in binding.directive_owner_ids)
        _require(binding.entry_directive.casefold() in dict(owners), "missing entry owner")
        return cls(sidecar.fingerprint(), lowering.transport_fingerprint, binding.routing_fingerprint,
                   binding.entry_directive, owners)

    def validate(self, sidecar, verified, plan, source_contents, required_operations):
        expected = self.for_plan(sidecar, verified, plan, source_contents, required_operations)
        _require(self == expected, "mismatched metadata/provenance association")

    def fingerprint(self):
        return _digest((SCHEMA, "plan-association", self.sidecar_fingerprint, self.air_fingerprint,
                        self.routing_fingerprint, self.entry_directive, self.owner_fingerprints))
