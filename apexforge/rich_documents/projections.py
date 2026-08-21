"""P11.13E deterministic projections for structured rich-document blocks.

The projection layer is caller-controlled and non-operative. It parses only the
minimal structured text owned by each P11.13E rich-document block kind. It does
not mutate semantic-lattice, narrative, runtime, project, package, cache, TAM,
or TAP owners.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from language.diagnostics import BuildDiagnostic, DiagnosticError
from language.narrative_model import (
    NarrativeCharacter,
    NarrativeContinuity,
    NarrativeContinuityConstraint,
    NarrativeIdentity,
    NarrativeStory,
)
from language.source import SourcePosition, SourceSpan
from rich_documents.model import (
    ApexDocument,
    ApexDocumentBlock,
    DocumentBlockKind,
)


@dataclass(frozen=True)
class RichDocumentProjectionLineage:
    """Exact document/block lineage retained by every E projection."""

    document_id: str
    block_id: str
    span: Optional[SourceSpan]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("document_id", self.document_id),
            ("block_id", self.block_id),
        ):
            if type(value) is not str:
                raise TypeError(
                    "RichDocumentProjectionLineage.{} must be an exact str".format(
                        field_name
                    )
                )
            if not value or value != value.strip():
                raise ValueError(
                    "RichDocumentProjectionLineage.{} must be non-empty and "
                    "trimmed".format(field_name)
                )
        if self.span is not None and type(self.span) is not SourceSpan:
            raise TypeError(
                "RichDocumentProjectionLineage.span must be None or exact "
                "SourceSpan"
            )


@dataclass(frozen=True)
class SemanticTableProjection:
    lineage: RichDocumentProjectionLineage
    columns: Tuple[str, ...]
    rows: Tuple[Tuple[str, ...], ...]

    def __post_init__(self) -> None:
        _require_lineage(self.lineage, "SemanticTableProjection.lineage")
        _require_exact_tuple(self.columns, "SemanticTableProjection.columns")
        _require_exact_tuple(self.rows, "SemanticTableProjection.rows")
        if not self.columns:
            raise ValueError("SemanticTableProjection.columns must not be empty")
        if any(type(column) is not str or not column for column in self.columns):
            raise TypeError(
                "SemanticTableProjection.columns must contain non-empty exact str values"
            )
        if len(set(self.columns)) != len(self.columns):
            raise ValueError("duplicate semantic-table column")
        for row in self.rows:
            if type(row) is not tuple:
                raise TypeError(
                    "SemanticTableProjection.rows must contain exact tuples"
                )
            if any(type(cell) is not str for cell in row):
                raise TypeError(
                    "SemanticTableProjection row cells must be exact str values"
                )
            if len(row) != len(self.columns):
                raise ValueError(
                    "SemanticTableProjection row width must equal column count"
                )


@dataclass(frozen=True)
class DiagramNode:
    node_id: str
    label: Optional[str] = None

    def __post_init__(self) -> None:
        _require_token(self.node_id, "DiagramNode.node_id")
        if self.label is not None:
            if type(self.label) is not str:
                raise TypeError("DiagramNode.label must be None or exact str")
            if not self.label:
                raise ValueError("DiagramNode.label must not be empty")


@dataclass(frozen=True)
class DiagramEdge:
    source: str
    relation: str
    target: str

    def __post_init__(self) -> None:
        _require_token(self.source, "DiagramEdge.source")
        _require_token(self.relation, "DiagramEdge.relation")
        _require_token(self.target, "DiagramEdge.target")


@dataclass(frozen=True)
class DiagramProjection:
    lineage: RichDocumentProjectionLineage
    nodes: Tuple[DiagramNode, ...]
    edges: Tuple[DiagramEdge, ...]

    def __post_init__(self) -> None:
        _require_lineage(self.lineage, "DiagramProjection.lineage")
        _require_exact_tuple(self.nodes, "DiagramProjection.nodes")
        _require_exact_tuple(self.edges, "DiagramProjection.edges")
        if any(type(node) is not DiagramNode for node in self.nodes):
            raise TypeError("DiagramProjection.nodes must contain exact DiagramNode values")
        if any(type(edge) is not DiagramEdge for edge in self.edges):
            raise TypeError("DiagramProjection.edges must contain exact DiagramEdge values")
        ids = tuple(node.node_id for node in self.nodes)
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate diagram node")
        if len(set(self.edges)) != len(self.edges):
            raise ValueError("duplicate diagram edge")
        available = set(ids)
        for edge in self.edges:
            if edge.source not in available or edge.target not in available:
                raise ValueError("diagram edge endpoints must name declared nodes")


@dataclass(frozen=True)
class WorldBibleProjection:
    lineage: RichDocumentProjectionLineage
    story: NarrativeStory

    def __post_init__(self) -> None:
        _require_lineage(self.lineage, "WorldBibleProjection.lineage")
        if type(self.story) is not NarrativeStory:
            raise TypeError(
                "WorldBibleProjection.story must be an exact NarrativeStory"
            )


@dataclass(frozen=True)
class CharacterSheetProjection:
    lineage: RichDocumentProjectionLineage
    character: NarrativeCharacter
    fields: Tuple[Tuple[str, str], ...]

    def __post_init__(self) -> None:
        _require_lineage(self.lineage, "CharacterSheetProjection.lineage")
        if type(self.character) is not NarrativeCharacter:
            raise TypeError(
                "CharacterSheetProjection.character must be an exact NarrativeCharacter"
            )
        _validate_pairs(self.fields, "CharacterSheetProjection.fields")


@dataclass(frozen=True)
class SimulationDescriptionProjection:
    lineage: RichDocumentProjectionLineage
    simulation_id: str
    parameters: Tuple[Tuple[str, str], ...]

    def __post_init__(self) -> None:
        _require_lineage(self.lineage, "SimulationDescriptionProjection.lineage")
        _require_token(
            self.simulation_id,
            "SimulationDescriptionProjection.simulation_id",
        )
        _validate_pairs(
            self.parameters,
            "SimulationDescriptionProjection.parameters",
        )


@dataclass(frozen=True)
class _StructuredLine:
    start: int
    end: int
    body: str


def _require_exact_tuple(value: object, field_name: str) -> None:
    if type(value) is not tuple:
        raise TypeError("{} must be an exact tuple".format(field_name))


def _require_lineage(
    value: object,
    field_name: str,
) -> RichDocumentProjectionLineage:
    if type(value) is not RichDocumentProjectionLineage:
        raise TypeError(
            "{} must be an exact RichDocumentProjectionLineage".format(
                field_name
            )
        )
    return value


def _require_token(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise TypeError("{} must be an exact str".format(field_name))
    if not value or value != value.strip() or any(character.isspace() for character in value):
        raise ValueError(
            "{} must be a non-empty trimmed token".format(field_name)
        )
    return value


def _validate_pairs(
    value: object,
    field_name: str,
) -> Tuple[Tuple[str, str], ...]:
    _require_exact_tuple(value, field_name)
    keys = []
    for pair in value:
        if type(pair) is not tuple or len(pair) != 2:
            raise TypeError(
                "{} must contain exact (str, str) tuples".format(field_name)
            )
        key, item = pair
        _require_token(key, "{} key".format(field_name))
        if type(item) is not str:
            raise TypeError("{} values must be exact str values".format(field_name))
        if not item:
            raise ValueError("{} values must not be empty".format(field_name))
        keys.append(key)
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate {} key".format(field_name))
    return value


def _structured_lines(text: str) -> Tuple[_StructuredLine, ...]:
    result: List[_StructuredLine] = []
    offset = 0
    for raw in text.splitlines(keepends=True):
        if raw.endswith("\r\n"):
            body = raw[:-2]
        elif raw.endswith("\n") or raw.endswith("\r"):
            body = raw[:-1]
        else:
            body = raw
        result.append(
            _StructuredLine(
                start=offset,
                end=offset + len(body),
                body=body,
            )
        )
        offset += len(raw)
    return tuple(result)


def _position_in_block(
    block: ApexDocumentBlock,
    relative_offset: int,
) -> Optional[SourcePosition]:
    if block.span is None:
        return None

    prefix = block.content[:relative_offset]
    line_breaks = prefix.count("\n")
    if line_breaks == 0:
        column = block.span.start.column + relative_offset
    else:
        last_newline = prefix.rfind("\n")
        column = relative_offset - last_newline

    return SourcePosition(
        line=block.span.start.line + line_breaks,
        column=column,
        offset=block.span.start.offset + relative_offset,
    )


def _line_span(
    block: ApexDocumentBlock,
    line: _StructuredLine,
) -> Optional[SourceSpan]:
    if block.span is None:
        return None
    start = _position_in_block(block, line.start)
    end = _position_in_block(block, line.end)
    if start is None or end is None:
        return None
    return SourceSpan(
        source_name=block.span.source_name,
        start=start,
        end=end,
    )


def _projection_error(
    block: ApexDocumentBlock,
    line: Optional[_StructuredLine],
    *,
    code: str,
    message: str,
) -> None:
    span = block.span if line is None else _line_span(block, line)
    raise DiagnosticError(
        BuildDiagnostic(
            severity="error",
            code=code,
            message=message,
            stage="parse",
            span=span,
        )
    )


def _select_block(
    document: ApexDocument,
    block: ApexDocumentBlock,
    expected_kind: DocumentBlockKind,
) -> RichDocumentProjectionLineage:
    if type(document) is not ApexDocument:
        raise TypeError("document must be an exact ApexDocument")
    if type(block) is not ApexDocumentBlock:
        raise TypeError("block must be an exact ApexDocumentBlock")
    if not any(candidate is block for candidate in document.blocks):
        raise ValueError("block must be the exact object owned by document")
    if block.kind is not expected_kind:
        raise ValueError(
            "block kind {!r} does not match projection kind {!r}".format(
                block.kind.value,
                expected_kind.value,
            )
        )
    return RichDocumentProjectionLineage(
        document_id=document.document_id,
        block_id=block.block_id,
        span=block.span,
    )


def _meaningful_lines(block: ApexDocumentBlock) -> Tuple[_StructuredLine, ...]:
    return tuple(
        line for line in _structured_lines(block.content)
        if line.body.strip()
    )


def _split_assignment(
    block: ApexDocumentBlock,
    line: _StructuredLine,
    prefix: str,
    *,
    code: str,
) -> Tuple[str, str]:
    if not line.body.startswith(prefix):
        _projection_error(
            block,
            line,
            code=code,
            message="Expected {!r} structured line.".format(prefix.rstrip()),
        )
    remainder = line.body[len(prefix):]
    if " = " not in remainder:
        _projection_error(
            block,
            line,
            code=code,
            message="Expected exact ' = ' delimiter.",
        )
    key, value = remainder.split(" = ", 1)
    try:
        _require_token(key, "structured key")
    except (TypeError, ValueError) as error:
        _projection_error(
            block,
            line,
            code=code,
            message=str(error),
        )
    if value == "":
        _projection_error(
            block,
            line,
            code=code,
            message="Structured value must not be empty.",
        )
    return key, value


def _parse_identity_path(
    block: ApexDocumentBlock,
    line: _StructuredLine,
    value: str,
    *,
    code: str,
) -> Tuple[str, ...]:
    if not value:
        _projection_error(
            block,
            line,
            code=code,
            message="Narrative identity path must not be empty.",
        )
    segments = tuple(value.split("/"))
    if any(
        not segment
        or segment != segment.strip()
        for segment in segments
    ):
        _projection_error(
            block,
            line,
            code=code,
            message=(
                "Narrative identity path segments must be non-empty and trimmed."
            ),
        )
    return segments


def _parse_subject_reference(
    block: ApexDocumentBlock,
    line: _StructuredLine,
    text: str,
) -> NarrativeIdentity:
    if ":" not in text:
        _projection_error(
            block,
            line,
            code="APXDOC-PROJECT-303",
            message=(
                "World-bible continuity subject must be "
                "'<kind>:<path>'."
            ),
        )
    kind, path_text = text.split(":", 1)
    try:
        _require_token(kind, "continuity subject kind")
    except (TypeError, ValueError) as error:
        _projection_error(
            block,
            line,
            code="APXDOC-PROJECT-303",
            message=str(error),
        )
    path = _parse_identity_path(
        block,
        line,
        path_text,
        code="APXDOC-PROJECT-303",
    )
    try:
        return NarrativeIdentity(kind, path)
    except (TypeError, ValueError) as error:
        _projection_error(
            block,
            line,
            code="APXDOC-PROJECT-303",
            message=str(error),
        )
    raise AssertionError("unreachable")


def project_semantic_table(
    document: ApexDocument,
    block: ApexDocumentBlock,
) -> SemanticTableProjection:
    lineage = _select_block(
        document,
        block,
        DocumentBlockKind.SEMANTIC_TABLE,
    )
    columns: List[str] = []
    rows: List[Tuple[str, ...]] = []
    seen_row = False

    for line in _meaningful_lines(block):
        if line.body.startswith("column "):
            if seen_row:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-101",
                    message="semantic-table columns must precede rows",
                )
            column = line.body[len("column "):]
            try:
                _require_token(column, "semantic-table column")
            except (TypeError, ValueError) as error:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-101",
                    message=str(error),
                )
            if column in columns:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-102",
                    message="duplicate semantic-table column {!r}".format(column),
                )
            columns.append(column)
            continue

        if line.body.startswith("row "):
            seen_row = True
            cells = tuple(line.body[len("row "):].split("|"))
            if not columns:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-103",
                    message="semantic-table row requires declared columns",
                )
            if len(cells) != len(columns):
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-104",
                    message=(
                        "semantic-table row width {} does not match "
                        "column count {}".format(len(cells), len(columns))
                    ),
                )
            rows.append(cells)
            continue

        _projection_error(
            block,
            line,
            code="APXDOC-PROJECT-105",
            message="unknown semantic-table directive",
        )

    if not columns:
        _projection_error(
            block,
            None,
            code="APXDOC-PROJECT-106",
            message="semantic-table requires at least one column",
        )

    return SemanticTableProjection(
        lineage=lineage,
        columns=tuple(columns),
        rows=tuple(rows),
    )


def project_diagram(
    document: ApexDocument,
    block: ApexDocumentBlock,
) -> DiagramProjection:
    lineage = _select_block(document, block, DocumentBlockKind.DIAGRAM)
    nodes: List[DiagramNode] = []
    edges: List[DiagramEdge] = []
    node_ids = set()

    for line in _meaningful_lines(block):
        if line.body.startswith("node "):
            remainder = line.body[len("node "):]
            parts = remainder.split(" ", 1)
            node_id = parts[0]
            label = parts[1] if len(parts) == 2 else None
            try:
                node = DiagramNode(node_id=node_id, label=label)
            except (TypeError, ValueError) as error:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-201",
                    message=str(error),
                )
            if node.node_id in node_ids:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-202",
                    message="duplicate diagram node {!r}".format(node.node_id),
                )
            node_ids.add(node.node_id)
            nodes.append(node)
            continue

        if line.body.startswith("edge "):
            parts = line.body[len("edge "):].split(" ")
            if len(parts) != 3 or any(not part for part in parts):
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-203",
                    message=(
                        "diagram edge must be exactly "
                        "'edge <source> <relation> <target>'"
                    ),
                )
            try:
                edge = DiagramEdge(
                    source=parts[0],
                    relation=parts[1],
                    target=parts[2],
                )
            except (TypeError, ValueError) as error:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-203",
                    message=str(error),
                )
            if edge in edges:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-204",
                    message="duplicate diagram edge",
                )
            edges.append(edge)
            continue

        _projection_error(
            block,
            line,
            code="APXDOC-PROJECT-205",
            message="unknown diagram directive",
        )

    available = set(node.node_id for node in nodes)
    for edge in edges:
        if edge.source not in available or edge.target not in available:
            _projection_error(
                block,
                None,
                code="APXDOC-PROJECT-206",
                message="diagram edge endpoints must name declared nodes",
            )

    return DiagramProjection(
        lineage=lineage,
        nodes=tuple(nodes),
        edges=tuple(edges),
    )


def project_world_bible(
    document: ApexDocument,
    block: ApexDocumentBlock,
) -> WorldBibleProjection:
    lineage = _select_block(
        document,
        block,
        DocumentBlockKind.WORLD_BIBLE,
    )
    story_identity: Optional[NarrativeIdentity] = None
    characters: List[NarrativeCharacter] = []
    continuities: List[NarrativeContinuity] = []
    character_identities = set()
    continuity_identities = set()

    for line in _meaningful_lines(block):
        if line.body.startswith("story "):
            if story_identity is not None:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-301",
                    message="world-bible requires exactly one story identity",
                )
            path = _parse_identity_path(
                block,
                line,
                line.body[len("story "):],
                code="APXDOC-PROJECT-301",
            )
            story_identity = NarrativeIdentity("story", path)
            continue

        if line.body.startswith("character "):
            path = _parse_identity_path(
                block,
                line,
                line.body[len("character "):],
                code="APXDOC-PROJECT-302",
            )
            identity = NarrativeIdentity("character", path)
            if identity in character_identities:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-302",
                    message="duplicate world-bible character identity",
                )
            character_identities.add(identity)
            characters.append(NarrativeCharacter(identity))
            continue

        if line.body.startswith("continuity "):
            remainder = line.body[len("continuity "):]
            if " = " not in remainder:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-303",
                    message=(
                        "world-bible continuity requires exact ' = ' delimiter"
                    ),
                )
            left, assertion = remainder.split(" = ", 1)
            if assertion == "":
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-303",
                    message="world-bible continuity assertion must not be empty",
                )
            left_parts = left.split(" ", 1)
            if len(left_parts) != 2:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-303",
                    message=(
                        "world-bible continuity must be "
                        "'continuity <path> <kind>:<path>[,<kind>:<path>...] "
                        "= <assertion>'"
                    ),
                )
            continuity_path = _parse_identity_path(
                block,
                line,
                left_parts[0],
                code="APXDOC-PROJECT-303",
            )
            subject_texts = tuple(left_parts[1].split(","))
            if any(not item for item in subject_texts):
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-303",
                    message="continuity subject list must not contain empty items",
                )
            subjects = tuple(
                _parse_subject_reference(block, line, item)
                for item in subject_texts
            )
            identity = NarrativeIdentity("continuity", continuity_path)
            if identity in continuity_identities:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-304",
                    message="duplicate world-bible continuity identity",
                )
            continuity_identities.add(identity)
            try:
                constraint = NarrativeContinuityConstraint(
                    subjects,
                    assertion,
                )
                continuity = NarrativeContinuity(
                    identity,
                    (constraint,),
                )
            except (TypeError, ValueError) as error:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-303",
                    message=str(error),
                )
            continuities.append(continuity)
            continue

        _projection_error(
            block,
            line,
            code="APXDOC-PROJECT-305",
            message="unknown world-bible directive",
        )

    if story_identity is None:
        _projection_error(
            block,
            None,
            code="APXDOC-PROJECT-306",
            message="world-bible requires exactly one story identity",
        )

    story = NarrativeStory(
        identity=story_identity,
        characters=tuple(characters),
        scenes=(),
        dialogues=(),
        choices=(),
        perspectives=(),
        timelines=(),
        states=(),
        continuities=tuple(continuities),
    )
    return WorldBibleProjection(
        lineage=lineage,
        story=story,
    )


def project_character_sheet(
    document: ApexDocument,
    block: ApexDocumentBlock,
) -> CharacterSheetProjection:
    lineage = _select_block(
        document,
        block,
        DocumentBlockKind.CHARACTER_SHEET,
    )
    character: Optional[NarrativeCharacter] = None
    fields: List[Tuple[str, str]] = []
    keys = set()

    for line in _meaningful_lines(block):
        if line.body.startswith("character "):
            if character is not None:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-401",
                    message="character-sheet requires exactly one character identity",
                )
            path = _parse_identity_path(
                block,
                line,
                line.body[len("character "):],
                code="APXDOC-PROJECT-401",
            )
            character = NarrativeCharacter(
                NarrativeIdentity("character", path)
            )
            continue

        if line.body.startswith("field "):
            key, value = _split_assignment(
                block,
                line,
                "field ",
                code="APXDOC-PROJECT-402",
            )
            if key in keys:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-403",
                    message="duplicate character-sheet field {!r}".format(key),
                )
            keys.add(key)
            fields.append((key, value))
            continue

        _projection_error(
            block,
            line,
            code="APXDOC-PROJECT-404",
            message="unknown character-sheet directive",
        )

    if character is None:
        _projection_error(
            block,
            None,
            code="APXDOC-PROJECT-405",
            message="character-sheet requires exactly one character identity",
        )

    return CharacterSheetProjection(
        lineage=lineage,
        character=character,
        fields=tuple(fields),
    )


def project_simulation_description(
    document: ApexDocument,
    block: ApexDocumentBlock,
) -> SimulationDescriptionProjection:
    lineage = _select_block(
        document,
        block,
        DocumentBlockKind.SIMULATION_DESCRIPTION,
    )
    simulation_id: Optional[str] = None
    parameters: List[Tuple[str, str]] = []
    keys = set()

    for line in _meaningful_lines(block):
        if line.body.startswith("simulation "):
            if simulation_id is not None:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-501",
                    message=(
                        "simulation-description requires exactly one simulation id"
                    ),
                )
            candidate = line.body[len("simulation "):]
            try:
                simulation_id = _require_token(
                    candidate,
                    "simulation id",
                )
            except (TypeError, ValueError) as error:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-501",
                    message=str(error),
                )
            continue

        if line.body.startswith("parameter "):
            key, value = _split_assignment(
                block,
                line,
                "parameter ",
                code="APXDOC-PROJECT-502",
            )
            if key in keys:
                _projection_error(
                    block,
                    line,
                    code="APXDOC-PROJECT-503",
                    message="duplicate simulation parameter {!r}".format(key),
                )
            keys.add(key)
            parameters.append((key, value))
            continue

        _projection_error(
            block,
            line,
            code="APXDOC-PROJECT-504",
            message="unknown simulation-description directive",
        )

    if simulation_id is None:
        _projection_error(
            block,
            None,
            code="APXDOC-PROJECT-505",
            message=(
                "simulation-description requires exactly one simulation id"
            ),
        )

    return SimulationDescriptionProjection(
        lineage=lineage,
        simulation_id=simulation_id,
        parameters=tuple(parameters),
    )


__all__ = (
    "RichDocumentProjectionLineage",
    "SemanticTableProjection",
    "DiagramNode",
    "DiagramEdge",
    "DiagramProjection",
    "WorldBibleProjection",
    "CharacterSheetProjection",
    "SimulationDescriptionProjection",
    "project_semantic_table",
    "project_diagram",
    "project_world_bible",
    "project_character_sheet",
    "project_simulation_description",
)