"""Passive deterministic validation over the frozen P11.5C narrative graph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from language.narrative_graph import NarrativeSemanticGraph
from language.narrative_model import NarrativeIdentity


__all__ = (
    "NarrativeValidationFinding",
    "NarrativeValidationReport",
    "validate_narrative_semantic_graph",
)


_CLASSIFICATIONS = (
    "duplicate_declaration",
    "referenced_only_identity",
    "conflicting_state_value",
    "temporal_cycle",
    "repeated_relation_evidence",
    "continuity_assertion_cluster",
    "perspective_cluster",
)

_INDEX_EVIDENCE_KEYS = frozenset(
    {
        "index",
        "constraint_index",
        "subject_index",
    }
)


def _require_identity(value: Any, field_name: str) -> NarrativeIdentity:
    if type(value) is not NarrativeIdentity:
        raise TypeError(f"{field_name} must be an exact NarrativeIdentity.")
    return value


def _require_identities(
    value: Any,
    field_name: str,
) -> tuple[NarrativeIdentity, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be an exact tuple.")
    if not value:
        raise ValueError(f"{field_name} must not be empty.")
    for item in value:
        _require_identity(item, f"{field_name} item")
    return value


def _require_indexes(value: Any, field_name: str) -> tuple[int, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be an exact tuple.")

    previous = -1
    for item in value:
        if type(item) is not int:
            raise TypeError(f"{field_name} items must be exact integers.")
        if item < 0:
            raise ValueError(f"{field_name} items must be non-negative.")
        if item <= previous:
            raise ValueError(
                f"{field_name} items must be strictly increasing."
            )
        previous = item
    return value


def _require_evidence(
    value: Any,
    field_name: str,
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be an exact tuple.")

    items: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise TypeError(
                f"{field_name} items must be exact two-item tuples."
            )
        key, fact = item
        if type(key) is not str or type(fact) is not str:
            raise TypeError(
                f"{field_name} keys and values must be exact strings."
            )
        if not key or key != key.strip():
            raise ValueError(
                f"{field_name} keys must be non-empty and trimmed."
            )
        if key in seen:
            raise ValueError(f"{field_name} keys must be unique.")
        seen.add(key)
        items.append((key, fact))

    return tuple(sorted(items, key=lambda item: item[0]))


@dataclass(frozen=True)
class NarrativeValidationFinding:
    """One passive classification of ordered graph evidence."""

    classification: str
    identities: tuple[NarrativeIdentity, ...]
    node_indexes: tuple[int, ...] = ()
    edge_indexes: tuple[int, ...] = ()
    evidence: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if type(self.classification) is not str:
            raise TypeError(
                "NarrativeValidationFinding.classification must be an exact str."
            )
        if self.classification not in _CLASSIFICATIONS:
            raise ValueError(
                "unsupported narrative validation classification "
                f"{self.classification!r}."
            )
        _require_identities(
            self.identities,
            "NarrativeValidationFinding.identities",
        )
        _require_indexes(
            self.node_indexes,
            "NarrativeValidationFinding.node_indexes",
        )
        _require_indexes(
            self.edge_indexes,
            "NarrativeValidationFinding.edge_indexes",
        )
        if not self.node_indexes and not self.edge_indexes:
            raise ValueError(
                "NarrativeValidationFinding requires node or edge evidence."
            )
        object.__setattr__(
            self,
            "evidence",
            _require_evidence(
                self.evidence,
                "NarrativeValidationFinding.evidence",
            ),
        )


@dataclass(frozen=True)
class NarrativeValidationReport:
    """Immutable ordered validation evidence for one narrative graph."""

    story: NarrativeIdentity
    findings: tuple[NarrativeValidationFinding, ...]

    def __post_init__(self) -> None:
        _require_identity(self.story, "NarrativeValidationReport.story")
        if self.story.kind != "story":
            raise ValueError(
                "NarrativeValidationReport.story must have narrative kind 'story'."
            )
        if type(self.findings) is not tuple:
            raise TypeError(
                "NarrativeValidationReport.findings must be an exact tuple."
            )
        if any(
            type(finding) is not NarrativeValidationFinding
            for finding in self.findings
        ):
            raise TypeError(
                "NarrativeValidationReport.findings must contain exact "
                "NarrativeValidationFinding values."
            )


def _ordered_unique_identities(
    identities: list[NarrativeIdentity],
) -> tuple[NarrativeIdentity, ...]:
    result: list[NarrativeIdentity] = []
    seen: set[NarrativeIdentity] = set()
    for identity in identities:
        if identity in seen:
            continue
        seen.add(identity)
        result.append(identity)
    return tuple(result)


def _semantic_repeat_evidence(
    evidence: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        item
        for item in evidence
        if item[0] not in _INDEX_EVIDENCE_KEYS
    )


def _temporal_cycle_findings(
    graph: NarrativeSemanticGraph,
) -> list[NarrativeValidationFinding]:
    precedes = [
        (index, edge)
        for index, edge in enumerate(graph.edges)
        if edge.relation == "precedes"
    ]
    if not precedes:
        return []

    vertex_order: list[NarrativeIdentity] = []
    vertex_seen: set[NarrativeIdentity] = set()
    adjacency: dict[NarrativeIdentity, list[NarrativeIdentity]] = {}

    for _, edge in precedes:
        for identity in (edge.source, edge.target):
            if identity not in vertex_seen:
                vertex_seen.add(identity)
                vertex_order.append(identity)
                adjacency[identity] = []
        adjacency[edge.source].append(edge.target)

    next_index = 0
    indexes: dict[NarrativeIdentity, int] = {}
    lowlinks: dict[NarrativeIdentity, int] = {}
    stack: list[NarrativeIdentity] = []
    on_stack: set[NarrativeIdentity] = set()
    components: list[list[NarrativeIdentity]] = []

    def visit(identity: NarrativeIdentity) -> None:
        nonlocal next_index
        indexes[identity] = next_index
        lowlinks[identity] = next_index
        next_index += 1
        stack.append(identity)
        on_stack.add(identity)

        for target in adjacency[identity]:
            if target not in indexes:
                visit(target)
                lowlinks[identity] = min(
                    lowlinks[identity],
                    lowlinks[target],
                )
            elif target in on_stack:
                lowlinks[identity] = min(
                    lowlinks[identity],
                    indexes[target],
                )

        if lowlinks[identity] != indexes[identity]:
            return

        component: list[NarrativeIdentity] = []
        while True:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == identity:
                break
        components.append(component)

    for identity in vertex_order:
        if identity not in indexes:
            visit(identity)

    position = {
        identity: index
        for index, identity in enumerate(vertex_order)
    }
    findings: list[tuple[int, NarrativeValidationFinding]] = []

    for component in components:
        members = set(component)
        internal_indexes = tuple(
            index
            for index, edge in precedes
            if edge.source in members and edge.target in members
        )
        self_loop = any(
            graph.edges[index].source == graph.edges[index].target
            for index in internal_indexes
        )
        if len(component) == 1 and not self_loop:
            continue

        ordered_members = tuple(
            sorted(component, key=lambda item: position[item])
        )
        finding = NarrativeValidationFinding(
            classification="temporal_cycle",
            identities=ordered_members,
            edge_indexes=internal_indexes,
            evidence=(
                ("edge_count", str(len(internal_indexes))),
                ("identity_count", str(len(ordered_members))),
            ),
        )
        findings.append((min(internal_indexes), finding))

    findings.sort(key=lambda item: item[0])
    return [finding for _, finding in findings]


def validate_narrative_semantic_graph(
    graph: NarrativeSemanticGraph,
) -> NarrativeValidationReport:
    """Classify passive evidence without mutating or interpreting the graph."""

    if type(graph) is not NarrativeSemanticGraph:
        raise TypeError(
            "validate_narrative_semantic_graph requires an exact "
            "NarrativeSemanticGraph."
        )

    findings: list[NarrativeValidationFinding] = []

    declared_groups: dict[NarrativeIdentity, list[int]] = {}
    declared_order: list[NarrativeIdentity] = []
    for index, node in enumerate(graph.nodes):
        if not node.declared:
            continue
        if node.identity not in declared_groups:
            declared_groups[node.identity] = []
            declared_order.append(node.identity)
        declared_groups[node.identity].append(index)

    for identity in declared_order:
        indexes = declared_groups[identity]
        if len(indexes) < 2:
            continue
        findings.append(
            NarrativeValidationFinding(
                classification="duplicate_declaration",
                identities=(identity,),
                node_indexes=tuple(indexes),
                evidence=(("count", str(len(indexes))),),
            )
        )

    for index, node in enumerate(graph.nodes):
        if node.declared:
            continue
        findings.append(
            NarrativeValidationFinding(
                classification="referenced_only_identity",
                identities=(node.identity,),
                node_indexes=(index,),
            )
        )

    state_groups: dict[
        tuple[NarrativeIdentity, str],
        list[int],
    ] = {}
    state_order: list[tuple[NarrativeIdentity, str]] = []
    for index, edge in enumerate(graph.edges):
        if edge.relation != "state_subject":
            continue
        evidence = dict(edge.evidence)
        name = evidence.get("name")
        value = evidence.get("value")
        if name is None or value is None:
            continue
        key = (edge.target, name)
        if key not in state_groups:
            state_groups[key] = []
            state_order.append(key)
        state_groups[key].append(index)

    for subject, name in state_order:
        edge_indexes = state_groups[(subject, name)]
        values: list[str] = []
        value_seen: set[str] = set()
        source_identities: list[NarrativeIdentity] = []
        for edge_index in edge_indexes:
            edge = graph.edges[edge_index]
            source_identities.append(edge.source)
            value = dict(edge.evidence)["value"]
            if value not in value_seen:
                value_seen.add(value)
                values.append(value)
        if len(values) < 2:
            continue
        findings.append(
            NarrativeValidationFinding(
                classification="conflicting_state_value",
                identities=_ordered_unique_identities(
                    [subject, *source_identities]
                ),
                edge_indexes=tuple(edge_indexes),
                evidence=(
                    ("name", name),
                    ("values", repr(tuple(values))),
                ),
            )
        )

    findings.extend(_temporal_cycle_findings(graph))

    repeat_groups: dict[
        tuple[
            str,
            NarrativeIdentity,
            NarrativeIdentity,
            tuple[tuple[str, str], ...],
        ],
        list[int],
    ] = {}
    repeat_order: list[
        tuple[
            str,
            NarrativeIdentity,
            NarrativeIdentity,
            tuple[tuple[str, str], ...],
        ]
    ] = []

    for index, edge in enumerate(graph.edges):
        if edge.relation == "contains":
            continue
        key = (
            edge.relation,
            edge.source,
            edge.target,
            _semantic_repeat_evidence(edge.evidence),
        )
        if key not in repeat_groups:
            repeat_groups[key] = []
            repeat_order.append(key)
        repeat_groups[key].append(index)

    for relation, source, target, semantic_evidence in repeat_order:
        edge_indexes = repeat_groups[
            (relation, source, target, semantic_evidence)
        ]
        if len(edge_indexes) < 2:
            continue
        findings.append(
            NarrativeValidationFinding(
                classification="repeated_relation_evidence",
                identities=(source, target),
                edge_indexes=tuple(edge_indexes),
                evidence=(
                    ("count", str(len(edge_indexes))),
                    ("relation", relation),
                    ("semantic_evidence", repr(semantic_evidence)),
                ),
            )
        )

    continuity_groups: dict[NarrativeIdentity, list[int]] = {}
    continuity_order: list[NarrativeIdentity] = []
    for index, edge in enumerate(graph.edges):
        if edge.relation != "continuity_subject":
            continue
        if edge.target not in continuity_groups:
            continuity_groups[edge.target] = []
            continuity_order.append(edge.target)
        continuity_groups[edge.target].append(index)

    for subject in continuity_order:
        edge_indexes = continuity_groups[subject]
        if len(edge_indexes) < 2:
            continue
        source_identities = [
            graph.edges[index].source
            for index in edge_indexes
        ]
        findings.append(
            NarrativeValidationFinding(
                classification="continuity_assertion_cluster",
                identities=_ordered_unique_identities(
                    [subject, *source_identities]
                ),
                edge_indexes=tuple(edge_indexes),
                evidence=(("count", str(len(edge_indexes))),),
            )
        )

    perspective_groups: dict[NarrativeIdentity, list[int]] = {}
    perspective_order: list[NarrativeIdentity] = []
    for index, edge in enumerate(graph.edges):
        if edge.relation != "viewpoint":
            continue
        if edge.target not in perspective_groups:
            perspective_groups[edge.target] = []
            perspective_order.append(edge.target)
        perspective_groups[edge.target].append(index)

    for viewpoint in perspective_order:
        edge_indexes = perspective_groups[viewpoint]
        if len(edge_indexes) < 2:
            continue
        source_identities = [
            graph.edges[index].source
            for index in edge_indexes
        ]
        findings.append(
            NarrativeValidationFinding(
                classification="perspective_cluster",
                identities=_ordered_unique_identities(
                    [viewpoint, *source_identities]
                ),
                edge_indexes=tuple(edge_indexes),
                evidence=(("count", str(len(edge_indexes))),),
            )
        )

    return NarrativeValidationReport(
        story=graph.story,
        findings=tuple(findings),
    )
