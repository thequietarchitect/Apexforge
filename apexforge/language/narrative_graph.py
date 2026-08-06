"""Passive deterministic Narrative Semantic Graph construction for P11.5C-B.

This module projects immutable P11.5B narrative records into immutable graph
evidence. It does not parse source text, validate continuity, emit diagnostics,
produce external output, run stories, or integrate with AIR.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from language.narrative_model import (
    NarrativeChoice,
    NarrativeContinuity,
    NarrativeDialogue,
    NarrativeIdentity,
    NarrativePerspective,
    NarrativeState,
    NarrativeStory,
    NarrativeTimeline,
)


__all__ = (
    "NarrativeGraphNode",
    "NarrativeGraphEdge",
    "NarrativeSemanticGraph",
    "build_narrative_semantic_graph",
)


_RELATIONS = frozenset(
    {
        "contains",
        "occurs_in",
        "spoken_by",
        "participant",
        "leads_to",
        "viewpoint",
        "timeline_scene",
        "precedes",
        "state_subject",
        "continuity_subject",
    }
)


def _require_identity(value: Any, field_name: str) -> NarrativeIdentity:
    if type(value) is not NarrativeIdentity:
        raise TypeError(f"{field_name} must be an exact NarrativeIdentity.")
    return value


def _require_exact_bool(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be an exact bool.")
    return value


def _require_relation(value: Any) -> str:
    if type(value) is not str:
        raise TypeError("NarrativeGraphEdge.relation must be an exact str.")
    if value not in _RELATIONS:
        raise ValueError(f"unsupported narrative graph relation {value!r}.")
    return value


def _require_evidence(value: Any) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise TypeError("NarrativeGraphEdge.evidence must be an exact tuple.")

    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise TypeError(
                "NarrativeGraphEdge.evidence items must be exact two-item tuples."
            )
        key, fact = item
        if type(key) is not str or type(fact) is not str:
            raise TypeError(
                "NarrativeGraphEdge.evidence keys and values must be exact strings."
            )
        if not key or key != key.strip():
            raise ValueError(
                "NarrativeGraphEdge.evidence keys must be non-empty and trimmed."
            )
        if key in seen:
            raise ValueError("NarrativeGraphEdge.evidence keys must be unique.")
        seen.add(key)
        normalized.append((key, fact))

    return tuple(sorted(normalized, key=lambda item: item[0]))


def _identity_text(identity: NarrativeIdentity) -> str:
    return f"{identity.kind}:{'/'.join(identity.path)}"


@dataclass(frozen=True)
class NarrativeGraphNode:
    """One declared or referenced narrative identity occurrence."""

    identity: NarrativeIdentity
    declared: bool

    def __post_init__(self) -> None:
        _require_identity(self.identity, "NarrativeGraphNode.identity")
        _require_exact_bool(self.declared, "NarrativeGraphNode.declared")


@dataclass(frozen=True)
class NarrativeGraphEdge:
    """One ordered narrative relationship with passive string evidence."""

    relation: str
    source: NarrativeIdentity
    target: NarrativeIdentity
    evidence: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "relation", _require_relation(self.relation))
        _require_identity(self.source, "NarrativeGraphEdge.source")
        _require_identity(self.target, "NarrativeGraphEdge.target")
        object.__setattr__(self, "evidence", _require_evidence(self.evidence))


@dataclass(frozen=True)
class NarrativeSemanticGraph:
    """Immutable ordered graph evidence projected from one NarrativeStory."""

    story: NarrativeIdentity
    nodes: tuple[NarrativeGraphNode, ...]
    edges: tuple[NarrativeGraphEdge, ...]

    def __post_init__(self) -> None:
        _require_identity(self.story, "NarrativeSemanticGraph.story")
        if self.story.kind != "story":
            raise ValueError(
                "NarrativeSemanticGraph.story must have narrative kind 'story'."
            )
        if type(self.nodes) is not tuple:
            raise TypeError("NarrativeSemanticGraph.nodes must be an exact tuple.")
        if type(self.edges) is not tuple:
            raise TypeError("NarrativeSemanticGraph.edges must be an exact tuple.")
        if not self.nodes:
            raise ValueError("NarrativeSemanticGraph.nodes must not be empty.")
        if any(type(node) is not NarrativeGraphNode for node in self.nodes):
            raise TypeError(
                "NarrativeSemanticGraph.nodes must contain exact "
                "NarrativeGraphNode values."
            )
        if any(type(edge) is not NarrativeGraphEdge for edge in self.edges):
            raise TypeError(
                "NarrativeSemanticGraph.edges must contain exact "
                "NarrativeGraphEdge values."
            )
        if self.nodes[0] != NarrativeGraphNode(self.story, True):
            raise ValueError(
                "NarrativeSemanticGraph must begin with its declared story node."
            )

        identities = {node.identity for node in self.nodes}
        for edge in self.edges:
            if edge.source not in identities or edge.target not in identities:
                raise ValueError(
                    "NarrativeSemanticGraph edge endpoints must exist as nodes."
                )


def build_narrative_semantic_graph(
    story: NarrativeStory,
) -> NarrativeSemanticGraph:
    """Project one exact NarrativeStory into deterministic graph evidence.

    Declared node occurrences retain P11.5B collection order and duplicates.
    Referenced-only identities are appended once in first-encounter order.
    Edge ordering follows a fixed record-family traversal and source tuple order.
    """

    if type(story) is not NarrativeStory:
        raise TypeError(
            "build_narrative_semantic_graph requires an exact NarrativeStory."
        )

    declared_records = (
        *story.characters,
        *story.scenes,
        *story.dialogues,
        *story.choices,
        *story.perspectives,
        *story.timelines,
        *story.states,
        *story.continuities,
    )
    declared_identities = {record.identity for record in declared_records}
    declared_identities.add(story.identity)

    nodes: list[NarrativeGraphNode] = [NarrativeGraphNode(story.identity, True)]
    nodes.extend(
        NarrativeGraphNode(record.identity, True) for record in declared_records
    )

    edges: list[NarrativeGraphEdge] = []
    referenced_only: list[NarrativeIdentity] = []
    referenced_seen: set[NarrativeIdentity] = set()

    def note(identity: NarrativeIdentity) -> None:
        _require_identity(identity, "graph reference")
        if identity in declared_identities or identity in referenced_seen:
            return
        referenced_seen.add(identity)
        referenced_only.append(identity)

    def add(
        relation: str,
        source: NarrativeIdentity,
        target: NarrativeIdentity,
        evidence: tuple[tuple[str, str], ...] = (),
    ) -> None:
        note(source)
        note(target)
        edges.append(
            NarrativeGraphEdge(
                relation=relation,
                source=source,
                target=target,
                evidence=evidence,
            )
        )

    for record in declared_records:
        add("contains", story.identity, record.identity)

    for dialogue in story.dialogues:
        if type(dialogue) is not NarrativeDialogue:
            raise TypeError("NarrativeStory.dialogues contains a malformed record.")
        add("occurs_in", dialogue.identity, dialogue.scene)
        add("spoken_by", dialogue.identity, dialogue.speaker)
        for index, participant in enumerate(dialogue.participants):
            add(
                "participant",
                dialogue.identity,
                participant,
                (("index", str(index)),),
            )

    for choice in story.choices:
        if type(choice) is not NarrativeChoice:
            raise TypeError("NarrativeStory.choices contains a malformed record.")
        add("occurs_in", choice.identity, choice.scene)
        for index, path in enumerate(choice.paths):
            evidence = [("index", str(index)), ("label", path.label)]
            if path.condition is not None:
                evidence.append(("condition", path.condition))
            if path.consequence is not None:
                evidence.append(("consequence", path.consequence))
            add(
                "leads_to",
                choice.identity,
                path.destination,
                tuple(evidence),
            )

    for perspective in story.perspectives:
        if type(perspective) is not NarrativePerspective:
            raise TypeError(
                "NarrativeStory.perspectives contains a malformed record."
            )
        if perspective.viewpoint is not None:
            add("viewpoint", perspective.identity, perspective.viewpoint)

    for timeline in story.timelines:
        if type(timeline) is not NarrativeTimeline:
            raise TypeError("NarrativeStory.timelines contains a malformed record.")
        for index, scene in enumerate(timeline.scenes):
            add(
                "timeline_scene",
                timeline.identity,
                scene,
                (("index", str(index)),),
            )
        for index, (before, after) in enumerate(
            zip(timeline.scenes, timeline.scenes[1:])
        ):
            add(
                "precedes",
                before,
                after,
                (
                    ("index", str(index)),
                    ("timeline", _identity_text(timeline.identity)),
                ),
            )

    for state in story.states:
        if type(state) is not NarrativeState:
            raise TypeError("NarrativeStory.states contains a malformed record.")
        for index, fact in enumerate(state.facts):
            add(
                "state_subject",
                state.identity,
                fact.subject,
                (
                    ("index", str(index)),
                    ("name", fact.name),
                    ("value", fact.value),
                ),
            )

    for continuity in story.continuities:
        if type(continuity) is not NarrativeContinuity:
            raise TypeError(
                "NarrativeStory.continuities contains a malformed record."
            )
        for constraint_index, constraint in enumerate(continuity.constraints):
            for subject_index, subject in enumerate(constraint.subjects):
                add(
                    "continuity_subject",
                    continuity.identity,
                    subject,
                    (
                        ("assertion", constraint.assertion),
                        ("constraint_index", str(constraint_index)),
                        ("subject_index", str(subject_index)),
                    ),
                )

    nodes.extend(
        NarrativeGraphNode(identity, False) for identity in referenced_only
    )

    return NarrativeSemanticGraph(
        story=story.identity,
        nodes=tuple(nodes),
        edges=tuple(edges),
    )
