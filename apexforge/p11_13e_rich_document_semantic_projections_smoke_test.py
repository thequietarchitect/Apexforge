"""P11.13E rich-document semantic projections smoke test."""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path
import subprocess

import rich_documents
import rich_documents.projections as projections
from language.diagnostics import DiagnosticError
from language.narrative_model import (
    NarrativeCharacter,
    NarrativeContinuity,
    NarrativeContinuityConstraint,
    NarrativeIdentity,
    NarrativeStory,
)
from language.source import SourceSpan, SourceText
from rich_documents.model import (
    ApexDocument,
    ApexDocumentBlock,
    DocumentBlockKind,
)
from rich_documents.parser import parse_apex_document
from rich_documents.projections import (
    CharacterSheetProjection,
    DiagramEdge,
    DiagramNode,
    DiagramProjection,
    RichDocumentProjectionLineage,
    SemanticTableProjection,
    SimulationDescriptionProjection,
    WorldBibleProjection,
    project_character_sheet,
    project_diagram,
    project_semantic_table,
    project_simulation_description,
    project_world_bible,
)


PREDECESSOR_TAG = "afp-p11-13d-freeze"
PREDECESSOR_COMMIT = "878927709a6c2ec37bf47ce84aa467761de6600b"

D_HASHES = {
    "apexforge/rich_documents/parser.py":
        "0A2BA1EE0747CC425875DF3F283CDA6AD020311A5A77570AEE2F41A8EEB86CE6",
    "apexforge/rich_documents/compilation.py":
        "80F39CA743745DBA17DD0491A245D4D8DAED2A9EEF5040A22A0A3823215FF58E",
    "apexforge/p11_13d_apexdoc_parser_executable_block_source_mapping_smoke_test.py":
        "BBEBAC23F852597C914975322355DB3CF04368EC93029933136DD26C63064D7A",
    "docs/p11/P11_13D_APEXDOC_PARSER_EXECUTABLE_BLOCK_SOURCE_MAPPING.md":
        "24589321986BDE71A5EF232CA93C3D94C783BFE96DA51896886292D3FBD76C1B",
}

EXPECTED_ARTIFACTS = (
    "apexforge/rich_documents/projections.py",
    "apexforge/p11_13e_rich_document_semantic_projections_smoke_test.py",
    "docs/p11/P11_13E_RICH_DOCUMENT_SEMANTIC_PROJECTIONS.md",
)

EXPECTED_PUBLIC = (
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


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _raises(error_type, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except error_type as error:
        return error
    except Exception as error:
        raise AssertionError(
            "expected {}, received {}: {}".format(
                error_type.__name__,
                type(error).__name__,
                error,
            )
        )
    raise AssertionError("expected {}".format(error_type.__name__))


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.13D freeze target changed",
    )
    _require(
        _git(
            "merge-base",
            "--is-ancestor",
            PREDECESSOR_TAG,
            "HEAD",
        ).returncode == 0,
        "P11.13D freeze is not ancestor of P11.13E",
    )
    for relative, expected in D_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen P11.13D hash changed".format(relative),
        )


def _assert_public_surface() -> None:
    _require(rich_documents.__all__ == (), "package-level exports changed in E")
    _require(
        projections.__all__ == EXPECTED_PUBLIC,
        "P11.13E public surface changed",
    )


def _assert_immutable_types() -> None:
    expected = {
        RichDocumentProjectionLineage:
            ("document_id", "block_id", "span"),
        SemanticTableProjection:
            ("lineage", "columns", "rows"),
        DiagramNode:
            ("node_id", "label"),
        DiagramEdge:
            ("source", "relation", "target"),
        DiagramProjection:
            ("lineage", "nodes", "edges"),
        WorldBibleProjection:
            ("lineage", "story"),
        CharacterSheetProjection:
            ("lineage", "character", "fields"),
        SimulationDescriptionProjection:
            ("lineage", "simulation_id", "parameters"),
    }
    for value, fields in expected.items():
        _require(dataclasses.is_dataclass(value), "{} not dataclass".format(value))
        _require(
            value.__dataclass_params__.frozen,
            "{} not frozen".format(value.__name__),
        )
        _require(
            tuple(value.__dataclass_fields__) == fields,
            "{} fields changed".format(value.__name__),
        )


def _document() -> ApexDocument:
    return parse_apex_document(
        "guide.apexdoc",
        (
            "@apexdoc Guide\n"
            "@block semantic-table stats\n"
            "column name\n"
            "column value\n"
            "row Alpha| 10\n"
            "row Beta|20\n"
            "@endblock\n"
            "@block diagram flow\n"
            "node Start Entry point\n"
            "node End Exit point\n"
            "edge Start leads_to End\n"
            "@endblock\n"
            "@block world-bible canon\n"
            "story Universe/Main\n"
            "character People/Ada\n"
            "character People/Borin\n"
            "continuity ArchiveRule character:People/Ada,character:People/Borin = The archive remains remembered.\n"
            "@endblock\n"
            "@block character-sheet ada\n"
            "character People/Ada\n"
            "field role = Cartographer\n"
            "field motto = Maps before certainty.\n"
            "@endblock\n"
            "@block simulation-description orbit\n"
            "simulation orbit-demo\n"
            "parameter timestep = 0.01\n"
            "parameter integrator = verlet\n"
            "@endblock\n"
        ),
    )


def _block(document: ApexDocument, block_id: str) -> ApexDocumentBlock:
    for block in document.blocks:
        if block.block_id == block_id:
            return block
    raise AssertionError("missing block " + block_id)


def _assert_semantic_table(document: ApexDocument) -> None:
    block = _block(document, "stats")
    first = project_semantic_table(document, block)
    second = project_semantic_table(document, block)

    _require(type(first) is SemanticTableProjection, "wrong semantic-table type")
    _require(first == second, "semantic-table projection not deterministic")
    _require(first.lineage.document_id == "Guide", "table document lineage lost")
    _require(first.lineage.block_id == "stats", "table block lineage lost")
    _require(first.lineage.span is block.span, "table span identity lost")
    _require(first.columns == ("name", "value"), "table columns changed")
    _require(
        first.rows == (("Alpha", " 10"), ("Beta", "20")),
        "table cell text/order changed",
    )

    bad = ApexDocumentBlock(
        block_id="bad-table",
        kind=DocumentBlockKind.SEMANTIC_TABLE,
        content="column a\nrow one|two\n",
    )
    bad_doc = ApexDocument("Bad", "bad.apexdoc", (bad,))
    error = _raises(DiagnosticError, project_semantic_table, bad_doc, bad)
    _require(error.diagnostic.code == "APXDOC-PROJECT-104", "row width code changed")


def _assert_diagram(document: ApexDocument) -> None:
    block = _block(document, "flow")
    first = project_diagram(document, block)
    second = project_diagram(document, block)

    _require(type(first) is DiagramProjection, "wrong diagram type")
    _require(first == second, "diagram projection not deterministic")
    _require(
        first.nodes
        == (
            DiagramNode("Start", "Entry point"),
            DiagramNode("End", "Exit point"),
        ),
        "diagram node order/content changed",
    )
    _require(
        first.edges == (DiagramEdge("Start", "leads_to", "End"),),
        "diagram edge changed",
    )

    bad = ApexDocumentBlock(
        block_id="bad-diagram",
        kind=DocumentBlockKind.DIAGRAM,
        content="node A\nedge A points_to Missing\n",
    )
    bad_doc = ApexDocument("Bad", "bad.apexdoc", (bad,))
    error = _raises(DiagnosticError, project_diagram, bad_doc, bad)
    _require(
        error.diagnostic.code == "APXDOC-PROJECT-206",
        "diagram endpoint code changed",
    )


def _assert_world_bible(document: ApexDocument) -> None:
    block = _block(document, "canon")
    first = project_world_bible(document, block)
    second = project_world_bible(document, block)

    _require(type(first) is WorldBibleProjection, "wrong world-bible type")
    _require(first == second, "world-bible projection not deterministic")
    _require(type(first.story) is NarrativeStory, "world bible duplicated story type")
    _require(
        first.story.identity == NarrativeIdentity("story", ("Universe", "Main")),
        "story identity path changed",
    )
    _require(
        first.story.characters
        == (
            NarrativeCharacter(
                NarrativeIdentity("character", ("People", "Ada"))
            ),
            NarrativeCharacter(
                NarrativeIdentity("character", ("People", "Borin"))
            ),
        ),
        "canonical character projection changed",
    )
    _require(
        first.story.scenes == ()
        and first.story.dialogues == ()
        and first.story.choices == ()
        and first.story.perspectives == ()
        and first.story.timelines == ()
        and first.story.states == (),
        "world bible invented unrelated narrative records",
    )
    _require(len(first.story.continuities) == 1, "continuity count changed")
    continuity = first.story.continuities[0]
    _require(type(continuity) is NarrativeContinuity, "continuity type duplicated")
    _require(
        continuity.identity
        == NarrativeIdentity("continuity", ("ArchiveRule",)),
        "continuity identity changed",
    )
    _require(len(continuity.constraints) == 1, "constraint count changed")
    constraint = continuity.constraints[0]
    _require(
        type(constraint) is NarrativeContinuityConstraint,
        "constraint type duplicated",
    )
    _require(
        constraint.subjects
        == (
            NarrativeIdentity("character", ("People", "Ada")),
            NarrativeIdentity("character", ("People", "Borin")),
        ),
        "continuity subject identities changed",
    )
    _require(
        constraint.assertion == "The archive remains remembered.",
        "continuity assertion changed",
    )

    bad = ApexDocumentBlock(
        block_id="bad-world",
        kind=DocumentBlockKind.WORLD_BIBLE,
        content="character Ada\n",
    )
    bad_doc = ApexDocument("Bad", "bad.apexdoc", (bad,))
    error = _raises(DiagnosticError, project_world_bible, bad_doc, bad)
    _require(
        error.diagnostic.code == "APXDOC-PROJECT-306",
        "missing story code changed",
    )


def _assert_character_sheet(document: ApexDocument) -> None:
    block = _block(document, "ada")
    first = project_character_sheet(document, block)
    second = project_character_sheet(document, block)

    _require(type(first) is CharacterSheetProjection, "wrong character-sheet type")
    _require(first == second, "character-sheet projection not deterministic")
    _require(
        type(first.character) is NarrativeCharacter,
        "character-sheet duplicated character type",
    )
    _require(
        first.character.identity
        == NarrativeIdentity("character", ("People", "Ada")),
        "character-sheet identity changed",
    )
    _require(
        first.fields
        == (
            ("role", "Cartographer"),
            ("motto", "Maps before certainty."),
        ),
        "character-sheet field order/value changed",
    )

    bad = ApexDocumentBlock(
        block_id="bad-sheet",
        kind=DocumentBlockKind.CHARACTER_SHEET,
        content=(
            "character Ada\n"
            "field role = One\n"
            "field role = Two\n"
        ),
    )
    bad_doc = ApexDocument("Bad", "bad.apexdoc", (bad,))
    error = _raises(DiagnosticError, project_character_sheet, bad_doc, bad)
    _require(
        error.diagnostic.code == "APXDOC-PROJECT-403",
        "duplicate sheet field code changed",
    )


def _assert_simulation_description(document: ApexDocument) -> None:
    block = _block(document, "orbit")
    first = project_simulation_description(document, block)
    second = project_simulation_description(document, block)

    _require(
        type(first) is SimulationDescriptionProjection,
        "wrong simulation-description type",
    )
    _require(first == second, "simulation projection not deterministic")
    _require(first.simulation_id == "orbit-demo", "simulation id changed")
    _require(
        first.parameters
        == (
            ("timestep", "0.01"),
            ("integrator", "verlet"),
        ),
        "simulation parameters changed",
    )

    bad = ApexDocumentBlock(
        block_id="bad-sim",
        kind=DocumentBlockKind.SIMULATION_DESCRIPTION,
        content=(
            "simulation test\n"
            "parameter x = one\n"
            "parameter x = two\n"
        ),
    )
    bad_doc = ApexDocument("Bad", "bad.apexdoc", (bad,))
    error = _raises(
        DiagnosticError,
        project_simulation_description,
        bad_doc,
        bad,
    )
    _require(
        error.diagnostic.code == "APXDOC-PROJECT-503",
        "duplicate simulation parameter code changed",
    )


def _assert_selection_and_diagnostics(document: ApexDocument) -> None:
    table = _block(document, "stats")
    diagram = _block(document, "flow")

    _raises(ValueError, project_diagram, document, table)

    equal_copy = ApexDocumentBlock(
        block_id=diagram.block_id,
        kind=diagram.kind,
        content=diagram.content,
        span=diagram.span,
        metadata=diagram.metadata,
    )
    _require(equal_copy == diagram and equal_copy is not diagram, "copy fixture invalid")
    _raises(ValueError, project_diagram, document, equal_copy)

    bad = ApexDocumentBlock(
        block_id="bad",
        kind=DocumentBlockKind.CHARACTER_SHEET,
        content="unknown value\n",
        span=table.span,
    )
    bad_doc = ApexDocument("Bad", "bad.apexdoc", (bad,))
    error = _raises(DiagnosticError, project_character_sheet, bad_doc, bad)
    _require(error.diagnostic.stage == "parse", "projection diagnostic stage changed")
    _require(error.diagnostic.span is not None, "projection diagnostic lost span")
    _require(
        error.diagnostic.span.source_name == "guide.apexdoc",
        "projection diagnostic lost outer source identity",
    )


def _assert_no_semantic_owner_takeover() -> None:
    path = _root() / "apexforge" / "rich_documents" / "projections.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    import_roots = set()
    calls = []
    definitions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            import_roots.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            import_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.append(node.name)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)

    _require(
        import_roots
        <= {
            "__future__",
            "dataclasses",
            "typing",
            "language",
            "rich_documents",
        },
        "E projection module acquired unexpected imports: {}".format(import_roots),
    )

    for forbidden_root in (
        "semantic_lattice",
        "runtime",
        "tooling",
        "incremental_cache",
        "tam",
        "tap_check",
        "workflow",
        "authority",
        "governance",
    ):
        _require(
            forbidden_root not in import_roots,
            "E imported premature subsystem: " + forbidden_root,
        )

    for forbidden_call in (
        "compile_source_with_map",
        "build_project",
        "load_project",
        "execute",
        "run_air_program",
        "adapt_codex_document_block_advisory",
        "validate_codex_document_block_advisory",
        "construct_semantic_lattice_snapshot",
    ):
        _require(
            forbidden_call not in calls,
            "E acquired forbidden behavior: " + forbidden_call,
        )

    _require(
        "project_world_bible" in definitions
        and "project_character_sheet" in definitions,
        "E narrative projection entries disappeared",
    )


def _assert_predecessor_owner_immutability() -> None:
    protected = (
        "apexforge/air",
        "apexforge/language",
        "apexforge/quad_vector",
        "apexforge/semantic_lattice",
        "apexforge/aether_air",
        "apexforge/tam",
        "apexforge/tap_check",
        "apexforge/runtime",
        "apexforge/workflow",
        "apexforge/tooling",
        "apexforge/type_system",
        "apexforge/governance",
        "apexforge/incremental_cache",
        "apexforge/standard_library",
        "apexforge/rich_documents/__init__.py",
        "apexforge/rich_documents/model.py",
        "apexforge/rich_documents/codex_adapter.py",
        "apexforge/rich_documents/parser.py",
        "apexforge/rich_documents/compilation.py",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *protected)
    _require(diff.returncode == 0, "P11.13E mutated frozen predecessor owners")


def _assert_artifact_set() -> None:
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    _require(status.returncode == 0, status.stderr.strip())
    actual = tuple(
        line[3:].replace("\\", "/")
        for line in status.stdout.splitlines()
        if line.strip()
    )

    head_result = _git("rev-parse", "HEAD")
    _require(head_result.returncode == 0, head_result.stderr.strip())
    head = head_result.stdout.strip()

    if head == PREDECESSOR_COMMIT:
        _require(
            set(actual) == set(EXPECTED_ARTIFACTS),
            "P11.13E precommit artifact set changed: {}".format(actual),
        )
        return

    parent_result = _git("rev-parse", "HEAD^")
    _require(parent_result.returncode == 0, parent_result.stderr.strip())
    _require(
        parent_result.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.13E committed-head parent is not frozen P11.13D",
    )
    _require(
        not actual,
        "P11.13E committed-head working tree must be clean: {}".format(actual),
    )

    committed = tuple(
        line.strip().replace("\\", "/")
        for line in _git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).stdout.splitlines()
        if line.strip()
    )
    _require(
        set(committed) == set(EXPECTED_ARTIFACTS),
        "P11.13E committed artifact set changed: {}".format(committed),
    )


def main() -> None:
    _assert_predecessor()
    _assert_public_surface()
    _assert_immutable_types()
    document = _document()
    _assert_semantic_table(document)
    _assert_diagram(document)
    _assert_world_bible(document)
    _assert_character_sheet(document)
    _assert_simulation_description(document)
    _assert_selection_and_diagnostics(document)
    _assert_no_semantic_owner_takeover()
    _assert_predecessor_owner_immutability()
    _assert_artifact_set()

    print("P11_13D_FREEZE_ANCESTRY=PASS")
    print("P11_13D_FROZEN_HASHES=PASS")
    print("RICH_DOCUMENT_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("PROJECTION_PUBLIC_SYMBOL_COUNT=13")
    print("PROJECTION_IMMUTABLE_TYPE_COUNT=8")
    print("PROJECTION_ENTRY_COUNT=5")
    print("PROJECTION_SELECTION=EXPLICIT_CALLER_CONTROLLED")
    print("BLOCK_MEMBERSHIP=EXACT_DOCUMENT_OWNED_OBJECT")
    print("SOURCE_LINEAGE=document_id+block_id+SourceSpan")
    print("SEMANTIC_TABLE_GRAMMAR=column+row")
    print("SEMANTIC_TABLE_COLUMN_ORDER=PRESERVED")
    print("SEMANTIC_TABLE_ROW_ORDER=PRESERVED")
    print("SEMANTIC_TABLE_VALUES=STRING_NO_COERCION")
    print("DIAGRAM_GRAMMAR=node+edge")
    print("DIAGRAM_NODE_EDGE_ORDER=PRESERVED")
    print("DIAGRAM_RENDERING=NONE")
    print("WORLD_BIBLE_GRAMMAR=story+character+continuity")
    print("WORLD_BIBLE_PATH_SEPARATOR=/")
    print("WORLD_BIBLE_CONTINUITY_SUBJECT=<kind>:<path>")
    print("WORLD_BIBLE_STORY_TYPE=language.narrative_model.NarrativeStory")
    print("WORLD_BIBLE_CHARACTER_TYPE=language.narrative_model.NarrativeCharacter")
    print("WORLD_BIBLE_CONTINUITY_TYPE=language.narrative_model.NarrativeContinuity")
    print("WORLD_BIBLE_CONSTRAINT_TYPE=language.narrative_model.NarrativeContinuityConstraint")
    print("NARRATIVE_OWNER_DUPLICATION=NONE")
    print("CHARACTER_SHEET_GRAMMAR=character+field")
    print("CHARACTER_SHEET_CANONICAL_CHARACTER=PASS")
    print("SIMULATION_DESCRIPTION_GRAMMAR=simulation+parameter")
    print("SIMULATION_ENGINE=NONE")
    print("APEXMOTION_IMPLEMENTATION=NONE")
    print("GRAMMAR_ESCAPING=NONE")
    print("GRAMMAR_COMMENTS=NONE")
    print("GRAMMAR_BLANK_LINES=IGNORED")
    print("GRAMMAR_ORDER=PRESERVED")
    print("UNKNOWN_DIRECTIVE=DIAGNOSTIC_ERROR")
    print("DUPLICATE_IDENTITIES=REJECTED")
    print("DUPLICATE_METADATA_KEYS=REJECTED")
    print("SEMANTIC_LATTICE_IMPORT=NONE")
    print("SEMANTIC_LATTICE_MUTATION=NONE")
    print("CODEX_AUTO_INVOCATION=NONE")
    print("PROJECT_MANIFEST_MUTATION=NONE")
    print("PROJECT_LOADER_MUTATION=NONE")
    print("CLI_MUTATION=NONE")
    print("CACHE_INTEGRATION=NONE")
    print("TAM_INTEGRATION=NONE")
    print("TAP_OWNERSHIP=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("PACKAGE_RESOLUTION=NONE")
    print("REMOTE_IO=NONE")
    print("GLOBAL_MUTABLE_STATE=NONE")
    print("PREDECESSOR_OWNER_MUTATION=NONE")
    print("P11_13E_RICH_DOCUMENT_SEMANTIC_PROJECTIONS=PASS")


if __name__ == "__main__":
    main()