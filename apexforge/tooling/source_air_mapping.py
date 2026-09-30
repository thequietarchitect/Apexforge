"""Producer-recorded SourceMap correspondence; no semantic reconstruction."""
from __future__ import annotations

from dataclasses import dataclass
import json

from language.compiler import CompiledSource, CompilerOperationEvidence
from tooling.debug_metadata import (SourceIdentity, StateLocator, AssignmentLocator, AIRMetadataIdentity,
    OperationReference, EvidenceReference, MetadataSidecar, _require, _digest, _index)
from apexforge.native_backend.lowering_input import build_verified_air_lowering_input

SCHEMA = "apexforge.source-air-correspondence/v1"


@dataclass(frozen=True)
class SourceCorrespondence:
    operation_id: str
    category: str
    source_map_index: int = -1

    def __post_init__(self):
        _require(type(self.operation_id) is str and self.operation_id.startswith("af-meta-op:"), "operation required")
        _require(self.category in ("SOURCE_BACKED", "UNMAPPED"), "unsupported source correspondence")
        if self.category == "SOURCE_BACKED":
            _index(self.source_map_index)
        else:
            _require(self.source_map_index == -1, "unmapped operation cannot claim a span")


@dataclass(frozen=True)
class StructuralLineage:
    label: str
    category: str
    source_map_index: int = -1
    originating_entry_index: int = -1

    def __post_init__(self):
        _require(self.category in ("SOURCE_BACKED", "COMPILER_SYNTHETIC", "GENERATED_CONTAINER", "METADATA_ONLY"),
                 "unsupported structural category")
        _require(type(self.label) is str and bool(self.label), "structural identity required")
        if self.category == "SOURCE_BACKED":
            _index(self.source_map_index)
        else:
            _require(self.source_map_index == -1, "synthetic/container/metadata object cannot claim a physical span")
        _require(type(self.originating_entry_index) is int and self.originating_entry_index >= -1,
                 "invalid lineage origin")


@dataclass(frozen=True)
class SourceAIRMapping:
    sidecar: MetadataSidecar
    correspondence: tuple[SourceCorrespondence, ...]
    lineage: tuple[StructuralLineage, ...]

    def __post_init__(self):
        _require(type(self.sidecar) is MetadataSidecar, "P12.6 sidecar required")
        _require(type(self.correspondence) is tuple and all(type(r) is SourceCorrespondence for r in self.correspondence),
                 "immutable correspondence required")
        _require(type(self.lineage) is tuple and all(type(r) is StructuralLineage for r in self.lineage),
                 "immutable lineage required")
        ids = tuple(r.operation_id for r in self.correspondence)
        _require(ids == tuple(op.operation_id for op in self.sidecar.operations), "missing/duplicate/reordered correspondence")
        for record in self.correspondence:
            if record.category == "SOURCE_BACKED":
                _require(record.source_map_index < len(self.sidecar.source_map.entries), "missing source entry")
                _require(any(e.operation_id == record.operation_id and e.source_map_index == record.source_map_index
                             for e in self.sidecar.evidence), "source correspondence lacks producer evidence")
        for record in self.lineage:
            _require(record.source_map_index < len(self.sidecar.source_map.entries) and
                     record.originating_entry_index < len(self.sidecar.source_map.entries), "missing structural lineage")

    def canonical_form(self):
        # In-memory fingerprint preimage only; no persistence/load API.
        return json.dumps((SCHEMA, self.sidecar.canonical_identity(),
            tuple((r.operation_id, r.category, r.source_map_index) for r in self.correspondence),
            tuple((r.label, r.category, r.source_map_index, r.originating_entry_index) for r in self.lineage)),
            ensure_ascii=False, separators=(",", ":"), allow_nan=False)

    def fingerprint(self):
        return _digest((SCHEMA, self.canonical_form()))

    def validate(self, compiled, producer_evidence, verified, source, content):
        expected = source_air_mapping(compiled, producer_evidence, verified, source, content)
        _require(self == expected, "stale/substituted source-to-AIR mapping")


def source_air_mapping(compiled, producer_evidence, verified, source, content):
    """Consume exact compiler observations, never infer an omitted correspondence.

    Single directive, original (unlinked/untransformed) compiler AIR only. A trusted
    producer output is a prerequisite, not a signed artifact or a semantic oracle.
    """
    _require(type(compiled) is CompiledSource and type(source) is SourceIdentity, "canonical producer inputs required")
    _require(type(producer_evidence) is tuple and all(type(e) is CompilerOperationEvidence for e in producer_evidence),
             "explicit compiler correspondence required; inference unsupported")
    source.validate_content(content)
    lowering = build_verified_air_lowering_input(verified)
    from air.model import VerifiedAIRProgram
    original = build_verified_air_lowering_input(VerifiedAIRProgram(compiled.program))
    _require(original.transport_json == lowering.transport_json, "stale compiler AIR correspondence")
    p = compiled.program
    _require(len(p.directives) == 1, "single directive producer required")
    expected_occurrences = tuple(("state", (i,)) for i in range(len(p.states))) + tuple(
        ("assignment", (di, pi, ai)) for di, decision in enumerate(p.causal_decisions)
        for pi, path in enumerate(decision.paths) for ai in range(len(path.assignments)))
    _require(tuple((e.kind, e.occurrence) for e in producer_evidence) == expected_occurrences,
             "missing/ambiguous producer operation correspondence")
    operations, references, records = [], [], []
    for ordinal, evidence in enumerate(producer_evidence):
        if evidence.kind == "state":
            index, = evidence.occurrence
            locator = StateLocator(index, p.states[index].id)
        else:
            di, pi, ai = evidence.occurrence
            decision, directive = p.causal_decisions[di], p.directives[0]
            _require(di < len(directive.causal_decisions) and directive.causal_decisions[di] == decision.id,
                     "unsupported transformed compiler order")
            locator = AssignmentLocator(0, directive.id, di, decision.id, pi, decision.paths[pi].id, ai)
        identity = AIRMetadataIdentity(lowering.transport_fingerprint, locator)
        identity.validate(verified)
        operation = OperationReference(ordinal, identity)
        operations.append(operation)
        if evidence.entry is None:
            records.append(SourceCorrespondence(operation.operation_id, "UNMAPPED"))
            continue
        # Exact recorded entry association, not matching literals/names or zipping spans to AIR.
        matches = tuple(i for i, entry in enumerate(compiled.source_map.entries) if entry == evidence.entry)
        _require(len(matches) == 1, "missing/ambiguous recorded SourceMap entry")
        index = matches[0]
        references.append(EvidenceReference(operation.operation_id, 0, index))
        records.append(SourceCorrespondence(operation.operation_id, "SOURCE_BACKED", index))
    references.sort(key=lambda e: (e.operation_id, e.source_index, e.source_map_index))
    sidecar = MetadataSidecar((source,), lowering.transport_fingerprint, compiled.source_map,
                             tuple(operations), tuple(references))
    sidecar.validate(verified, (content,), tuple(op.identity for op in operations))
    directive_entries = tuple(i for i, entry in enumerate(compiled.source_map.entries) if entry.kind == "directive")
    _require(len(directive_entries) <= 1, "ambiguous originating declaration")
    parent = directive_entries[0] if directive_entries else -1
    lineage = []
    for index, entry in enumerate(compiled.source_map.entries):
        if entry.kind in ("principal", "authority_check"):
            # Legacy SourceMap locations describe the originating declaration, not synthetic syntax.
            lineage.append(StructuralLineage(entry.air_id, "COMPILER_SYNTHETIC", originating_entry_index=parent))
        else:
            lineage.append(StructuralLineage(entry.air_id, "SOURCE_BACKED", index))
    lineage.extend((StructuralLineage("AIRProgram", "GENERATED_CONTAINER"),
                    StructuralLineage("MetadataSidecar", "METADATA_ONLY")))
    return SourceAIRMapping(sidecar, tuple(records), tuple(lineage))
