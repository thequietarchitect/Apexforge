"""P15 narrative containers around frozen P11 semantics; passive evidence only."""
from dataclasses import dataclass, fields

from language import narrative_model as model
from language.narrative_graph import build_narrative_semantic_graph
from tooling import domain_platform as sdk
from tooling.package_manifest import PackageManifest, ExactVersion, CanonicalReference

OPERATIONS = ("narrative.state.describe", "narrative.graph.describe", "narrative.branch.describe")
PLATFORM = sdk.DomainPlatformIdentity("apexforge.narrative", "narrative")
_RECORD_TYPES = tuple(getattr(model, name) for name in model.__all__)


class NarrativeDomainError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise NarrativeDomainError(code)


def frozen_record(value):
    """Explicit P11 record projection. Semantic tuple order is preserved verbatim."""
    if type(value) in _RECORD_TYPES:
        return {field.name: frozen_record(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [frozen_record(item) for item in value]
    require(value is None or type(value) in (str, bool, int), "NARRATIVE_RECORD_INVALID")
    return value


def provenance(owner):
    try:
        sdk._refs(owner, "provenance", CanonicalReference, "NARRATIVE_PROVENANCE_INVALID")
    except sdk.DomainContractError as error:
        raise NarrativeDomainError("NARRATIVE_PROVENANCE_INVALID") from error


def name(value, code):
    try:
        sdk._name(value, code)
    except sdk.DomainContractError as error:
        raise NarrativeDomainError(code) from error


@dataclass(frozen=True)
class NarrativeEvent(sdk.CanonicalModel):
    """Domain event declaration; intentionally not a new P11 identity kind."""
    identifier: str
    scene: model.NarrativeIdentity
    participants: tuple
    ordinal: int
    provenance: tuple = ()
    DOMAIN = "apexforge.narrative.event/v1"

    def __post_init__(self):
        name(self.identifier, "NARRATIVE_EVENT_ID_INVALID")
        require(type(self.scene) is model.NarrativeIdentity and self.scene.kind == "scene",
            "NARRATIVE_EVENT_SCENE_INVALID")
        require(type(self.ordinal) is int and 0 <= self.ordinal <= 2 ** 63 - 1,
            "NARRATIVE_EVENT_ORDER_INVALID")
        require(type(self.participants) is tuple and all(type(p) is model.NarrativeIdentity and
            p.kind == "character" for p in self.participants), "NARRATIVE_EVENT_PARTICIPANT_INVALID")
        require(len(set(self.participants)) == len(self.participants), "NARRATIVE_EVENT_PARTICIPANT_DUPLICATE")
        object.__setattr__(self, "participants", tuple(sorted(self.participants, key=lambda p: (p.kind, p.path))))
        provenance(self)

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier, "scene": frozen_record(self.scene),
            "participants": frozen_record(self.participants), "ordinal": self.ordinal,
            "provenance": [p.record() for p in self.provenance],
            "assertion_status": "NARRATIVE_DECLARATION", "execution": "NOT_PERFORMED"}


@dataclass(frozen=True)
class NarrativeCausalRelation(sdk.CanonicalModel):
    source_event: str
    target_event: str
    provenance: tuple = ()
    DOMAIN = "apexforge.narrative.causal-relation/v1"

    def __post_init__(self):
        name(self.source_event, "NARRATIVE_CAUSAL_SOURCE_INVALID")
        name(self.target_event, "NARRATIVE_CAUSAL_TARGET_INVALID")
        provenance(self)

    def record(self):
        return {"schema": self.DOMAIN, "relation": "narrative-cause", "source": self.source_event,
            "target": self.target_event, "provenance": [p.record() for p in self.provenance],
            "external_causation_verified": False}


@dataclass(frozen=True)
class NarrativeSnapshot(sdk.CanonicalModel):
    story: model.NarrativeStory
    events: tuple = ()
    causal_relations: tuple = ()
    provenance: tuple = ()
    DOMAIN = "apexforge.narrative.state-graph/v1"

    def __post_init__(self):
        require(type(self.story) is model.NarrativeStory, "NARRATIVE_STORY_INVALID")
        graph = build_narrative_semantic_graph(self.story)
        identities = tuple(node.identity for node in graph.nodes if node.declared)
        require(len(set(identities)) == len(identities), "NARRATIVE_NODE_DUPLICATE")
        require(all(node.declared for node in graph.nodes), "NARRATIVE_REFERENCE_MISSING")
        # This domain container requires unambiguous alternatives and state facts.
        for choice in self.story.choices:
            labels = tuple(path.label for path in choice.paths)
            require(len(set(labels)) == len(labels), "NARRATIVE_CHOICE_ALTERNATIVE_DUPLICATE")
        for state in self.story.states:
            keys = tuple((fact.subject, fact.name) for fact in state.facts)
            require(len(set(keys)) == len(keys), "NARRATIVE_STATE_FACT_DUPLICATE")
        require(type(self.events) is tuple and all(type(e) is NarrativeEvent for e in self.events),
            "NARRATIVE_EVENT_INVALID")
        ids = tuple(e.identifier for e in self.events)
        require(len(set(ids)) == len(ids), "NARRATIVE_EVENT_DUPLICATE")
        require(len(set(e.ordinal for e in self.events)) == len(self.events), "NARRATIVE_EVENT_ORDER_DUPLICATE")
        declared = set(identities)
        require(all(e.scene in declared and all(p in declared for p in e.participants) for e in self.events),
            "NARRATIVE_EVENT_REFERENCE_MISSING")
        object.__setattr__(self, "events", tuple(sorted(self.events, key=lambda e: e.ordinal)))
        require(type(self.causal_relations) is tuple and all(type(e) is NarrativeCausalRelation
            for e in self.causal_relations), "NARRATIVE_CAUSAL_RELATION_INVALID")
        pairs = tuple((e.source_event, e.target_event) for e in self.causal_relations)
        require(len(set(pairs)) == len(pairs), "NARRATIVE_EDGE_DUPLICATE")
        require(all(source in ids and target in ids for source, target in pairs), "NARRATIVE_EDGE_REFERENCE_MISSING")
        object.__setattr__(self, "causal_relations", tuple(e for _, e in sorted(zip(pairs, self.causal_relations))))
        provenance(self)

    def record(self):
        graph = build_narrative_semantic_graph(self.story)
        return {"schema": self.DOMAIN, "story": frozen_record(self.story),
            "frozen_graph": {"story": frozen_record(graph.story),
                "nodes": [{"identity": frozen_record(n.identity), "declared": n.declared} for n in graph.nodes],
                "edges": [{"relation": e.relation, "source": frozen_record(e.source),
                    "target": frozen_record(e.target), "evidence": [list(pair) for pair in e.evidence]} for e in graph.edges]},
            "events": [e.record() for e in self.events],
            "causal_relations": [e.record() for e in self.causal_relations],
            "provenance": [p.record() for p in self.provenance],
            "assertion_status": "NARRATIVE_DECLARATION", "semantic_authority": "CANONICAL_AIR",
            "grants_authority": False, "external_fact_verified": False}


@dataclass(frozen=True)
class NarrativeBranch(sdk.CanonicalModel):
    identifier: str
    parent: NarrativeSnapshot
    choice: model.NarrativeIdentity
    alternative_index: int
    state: model.NarrativeIdentity
    provenance: tuple = ()
    DOMAIN = "apexforge.narrative.branch/v1"

    def __post_init__(self):
        name(self.identifier, "NARRATIVE_BRANCH_ID_INVALID")
        require(type(self.parent) is NarrativeSnapshot, "NARRATIVE_BRANCH_PARENT_INVALID")
        require(type(self.choice) is model.NarrativeIdentity, "NARRATIVE_BRANCH_CHOICE_INVALID")
        choices = tuple(c for c in self.parent.story.choices if c.identity == self.choice)
        require(len(choices) == 1, "NARRATIVE_BRANCH_CHOICE_MISSING")
        require(type(self.alternative_index) is int and 0 <= self.alternative_index < len(choices[0].paths),
            "NARRATIVE_BRANCH_ALTERNATIVE_MISSING")
        require(type(self.state) is model.NarrativeIdentity and any(s.identity == self.state
            for s in self.parent.story.states), "NARRATIVE_BRANCH_STATE_MISSING")
        provenance(self)

    def record(self):
        choice = next(c for c in self.parent.story.choices if c.identity == self.choice)
        return {"schema": self.DOMAIN, "id": self.identifier, "parent_fingerprint": self.parent.fingerprint(),
            "world": frozen_record(self.parent.story.identity), "choice": frozen_record(self.choice),
            "alternative_index": self.alternative_index,
            "alternative": frozen_record(choice.paths[self.alternative_index]), "state": frozen_record(self.state),
            "selection_origin": "CALLER_SUPPLIED", "history_replaced": False,
            "provenance": [p.record() for p in self.provenance], "grants_authority": False}


def narrative_platform(manifest):
    require(type(manifest) is PackageManifest, "NARRATIVE_PACKAGE_INVALID")
    return sdk.DomainPlatformDescriptor(PLATFORM, sdk.ImplementationPackage.from_manifest(manifest),
        ExactVersion(1, 0, 0), OPERATIONS, (sdk.DomainCapability("narrative.describe"),),
        provenance=manifest.provenance)


def narrative_artifact(descriptor, record, *, semantic_inputs=(), symbols=()):
    require(type(descriptor) is sdk.DomainPlatformDescriptor and descriptor.identity == PLATFORM and
        descriptor.contract_version == ExactVersion(1, 0, 0) and descriptor.operations == tuple(sorted(OPERATIONS)) and
        descriptor.capabilities == (sdk.DomainCapability("narrative.describe"),) and not descriptor.dependencies,
        "NARRATIVE_PLATFORM_BINDING_INVALID")
    require(type(record) in (NarrativeSnapshot, NarrativeBranch), "NARRATIVE_RECORD_INVALID")
    operation = "narrative.branch.describe" if type(record) is NarrativeBranch else "narrative.graph.describe"
    payload = record.canonical_json().encode("utf-8")
    return sdk.DomainArtifact.from_bytes(descriptor, operation, "model", payload,
        semantic_inputs=semantic_inputs, symbols=symbols, provenance=record.provenance)
