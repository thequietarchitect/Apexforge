"""Bounded native owner correspondence to generated C, not machine addresses."""
from __future__ import annotations

from dataclasses import dataclass
import json

from language.compiler import SourceMap
from language.source import SourceSpan, SourceText
from tooling.debug_metadata import (SourceIdentity, AIRMetadataIdentity, StateLocator, AssignmentLocator,
    OperationReference, MetadataSidecar, MetadataAssociation, _require, _digest, _hash)
from tooling.source_air_mapping import SourceAIRMapping
from .native_execution_contract import PROFILE, admit_native_profile
from .native_execution import _source, build_native, digest

SCHEMA = "apexforge.native-generated-source-mapping/v1"


@dataclass(frozen=True)
class GeneratedRegion:
    operation: OperationReference
    span: SourceSpan

    def __post_init__(self):
        _require(type(self.operation) is OperationReference and type(self.span) is SourceSpan,
                 "operation and canonical generated span required")
        _require(self.span.end.offset > self.span.start.offset, "empty/invalid generated region")


@dataclass(frozen=True)
class NativeSourceMapping:
    sidecar: MetadataSidecar
    association: MetadataAssociation
    source_mapping_fingerprint: str
    profile: str
    generated_source: SourceIdentity
    regions: tuple[GeneratedRegion, ...]

    def __post_init__(self):
        _require(type(self.sidecar) is MetadataSidecar and type(self.association) is MetadataAssociation,
                 "sidecar/provenance required")
        _require(self.profile == PROFILE, "wrong native mapping profile")
        if self.source_mapping_fingerprint != "UNMAPPED_SOURCE":
            _hash(self.source_mapping_fingerprint)
        _require(type(self.generated_source) is SourceIdentity and self.generated_source.logical_name == "program.c",
                 "governed generated-source identity required")
        _require(type(self.regions) is tuple and all(type(r) is GeneratedRegion for r in self.regions),
                 "immutable generated regions required")
        _require(tuple(r.operation for r in self.regions) == self.sidecar.operations,
                 "missing/duplicate/wrong operation correspondence")
        _require(self.association.sidecar_fingerprint == self.sidecar.fingerprint(), "substituted sidecar")
        for index, region in enumerate(self.regions):
            _require(region.span.source_name == self.generated_source.logical_name, "wrong generated source")
            if index:
                _require(self.regions[index-1].span.end.offset <= region.span.start.offset,
                         "duplicate/overlapping/out-of-order generated region")

    def canonical_form(self):
        return json.dumps((SCHEMA, self.sidecar.fingerprint(), self.association.fingerprint(),
            self.source_mapping_fingerprint, self.profile, self.generated_source.canonical_identity(),
            tuple((r.operation.canonical_identity(), r.span.source_name,
                   (r.span.start.line, r.span.start.column, r.span.start.offset),
                   (r.span.end.line, r.span.end.column, r.span.end.offset)) for r in self.regions)),
            ensure_ascii=False, separators=(",", ":"), allow_nan=False)

    def fingerprint(self):
        return _digest((SCHEMA, self.canonical_form()))

    def validate(self, verified, plan, generated_content, *, source_mapping=None, source_contents=()):
        self.generated_source.validate_content(generated_content)
        expected_content, expected = emit_native_source_mapping(
            verified, plan, source_mapping=source_mapping, source_contents=source_contents)
        _require(generated_content == expected_content and self == expected, "stale/substituted native source mapping")


def _admitted_operation_references(verified, plan):
    # Admission remains the ONLY semantic/profile authority. Observation follows its exact schedule.
    admission = admit_native_profile(verified, plan)
    p = verified.program
    identities = [AIRMetadataIdentity(admission.air_fingerprint, StateLocator(i, state.id))
                  for i, state in enumerate(p.states)]
    directive = p.directives[0]  # the admitted sole directive
    for occurrence, decision_id in enumerate(directive.causal_decisions):
        matches = tuple(d for d in p.causal_decisions if d.id == decision_id)
        _require(len(matches) == 1, "ambiguous admitted decision reference")
        path = matches[0].paths[0]  # sole path guaranteed by the unchanged profile; no selection
        for index in range(len(path.assignments)):
            locator = AssignmentLocator(0, directive.id, occurrence, decision_id, 0, path.id, index)
            identities.append(AIRMetadataIdentity(admission.air_fingerprint, locator))
    _require(len(identities) == len(admission.state_ids) + len(admission.stores), "missing admitted operation correspondence")
    return admission, tuple(OperationReference(i, identity) for i, identity in enumerate(identities))


def emit_native_source_mapping(verified, plan, *, source_mapping=None, source_contents=()):
    admission, operations = _admitted_operation_references(verified, plan)
    if source_mapping is None:
        _require(source_contents == (), "cannot infer missing source correspondence")
        # Hand-authored admitted AIR has no fabricated physical source spans.
        sidecar = MetadataSidecar((), admission.air_fingerprint, SourceMap(), operations)
        source_reference = "UNMAPPED_SOURCE"
    else:
        _require(type(source_mapping) is SourceAIRMapping, "explicit producer source correspondence required")
        sidecar = source_mapping.sidecar
        _require(sidecar.operations == operations, "wrong/missing source-to-admitted-operation correspondence")
        source_reference = source_mapping.fingerprint()
    required = tuple(op.identity for op in operations)
    association = MetadataAssociation.for_plan(sidecar, verified, plan, source_contents, required)
    raw_regions = []
    content = _source(admission, region_sink=raw_regions)
    _require(tuple(row[0] for row in raw_regions) == tuple(range(len(operations))), "missing emitter correspondence")
    source = SourceIdentity.from_bytes("program.c", content)
    text = SourceText(source.logical_name, content.decode("ascii"))
    regions = tuple(GeneratedRegion(operations[ordinal], text.span(start, end))
                    for ordinal, start, end in raw_regions)
    return content, NativeSourceMapping(sidecar, association, source_reference, PROFILE, source, regions)


@dataclass(frozen=True)
class MappedNativeArtifact:
    artifact: object
    mapping: NativeSourceMapping
    mapping_fingerprint: str
    receipt_fingerprint: str

    def validate(self, verified, plan, *, source_mapping=None, source_contents=()):
        content, expected = emit_native_source_mapping(verified, plan,
            source_mapping=source_mapping, source_contents=source_contents)
        _require(self.mapping == expected and self.mapping_fingerprint == expected.fingerprint(), "substituted artifact mapping")
        _require(self.receipt_fingerprint == self.artifact.receipt_fingerprint and
                 digest(self.artifact.receipt_json.encode("utf-8")) == self.receipt_fingerprint, "substituted receipt")
        receipt = json.loads(self.artifact.receipt_json)
        _require(receipt["profile"] == PROFILE and receipt["air"] == expected.sidecar.air_fingerprint and
                 receipt["routing"] == expected.association.routing_fingerprint and
                 receipt["source"] == digest(content), "wrong artifact/source provenance")
        _require(receipt["image"] == digest(self.artifact.image.read_bytes()), "substituted native image")
        # Canonical dispatch still owns ticket validation, image lock and execution.


def build_native_with_mapping(verified, plan, directory, *, source_mapping=None, source_contents=(), timeout=60):
    content, mapping = emit_native_source_mapping(verified, plan,
        source_mapping=source_mapping, source_contents=source_contents)
    artifact = build_native(verified, plan, directory, timeout=timeout)
    mapped = MappedNativeArtifact(artifact, mapping, mapping.fingerprint(), artifact.receipt_fingerprint)
    mapped.validate(verified, plan, source_mapping=source_mapping, source_contents=source_contents)
    return mapped
