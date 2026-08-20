"""P11-TAM-A architecture and traceability ownership audit smoke test.

Audit-only: establishes Compiler TAM ownership boundaries without adding a TAM
runtime/model implementation or mutating frozen predecessor production code.
"""

from __future__ import annotations

from pathlib import Path
import subprocess


PREDECESSOR = "a9e677353a7c01dd760bc0a670790efc16a1c7ef"
TRACE_DOMAINS = (
    "source",
    "token",
    "declaration",
    "reference",
    "scope",
    "type",
    "authority",
    "narrative",
    "ownership",
    "transformation",
)

DEDICATED_TAM_CANDIDATES = (
    "apexforge/tam.py",
    "apexforge/tam",
    "apexforge/language/tam.py",
    "apexforge/language/token_analysis.py",
    "apexforge/language/compiler_tam.py",
)

FROZEN_OWNERS = (
    "apexforge/language/source.py",
    "apexforge/language/lexer.py",
    "apexforge/language/parser.py",
    "apexforge/language/compiler.py",
    "apexforge/language/declarations.py",
    "apexforge/language/identities.py",
    "apexforge/language/resolution_candidates.py",
    "apexforge/language/resolution_context.py",
    "apexforge/language/narrative_source.py",
    "apexforge/language/narrative_analysis.py",
    "apexforge/language/narrative_lowering.py",
    "apexforge/language/semantic_decision_source.py",
    "apexforge/language/semantic_decision_parser.py",
    "apexforge/language/semantic_decision_lowering.py",
    "apexforge/language/semantic_decision_analysis.py",
    "apexforge/language/semantic_decision_project_analysis.py",
    "apexforge/aether_air/records.py",
    "apexforge/aether_air/transformation.py",
    "apexforge/aether_air/projection.py",
    "apexforge/semantic_lattice/model.py",
    "apexforge/semantic_lattice/adapters.py",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (_root() / relative_path).read_text(encoding="utf-8")


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


def _assert_predecessor_and_branch() -> None:
    branch = _git("branch", "--show-current")
    _require(branch.returncode == 0, branch.stderr.strip())
    _require(
        branch.stdout.strip() == "p11-tam-a-architecture-traceability-audit",
        "unexpected TAM-A branch",
    )

    head = _git("rev-parse", "HEAD")
    _require(head.returncode == 0, head.stderr.strip())
    selected_head = head.stdout.strip()
    if selected_head != PREDECESSOR:
        parent = _git("rev-parse", "HEAD^")
        _require(parent.returncode == 0, parent.stderr.strip())
        _require(
            parent.stdout.strip() == PREDECESSOR,
            "TAM-A predecessor changed",
        )


def _assert_no_dedicated_tam_implementation() -> None:
    root = _root()
    existing = tuple(
        candidate
        for candidate in DEDICATED_TAM_CANDIDATES
        if (root / candidate).exists()
    )
    _require(existing == (), "dedicated TAM implementation unexpectedly exists")

    tracked = _git("ls-files")
    _require(tracked.returncode == 0, tracked.stderr.strip())
    tam_files = tuple(
        line.strip()
        for line in tracked.stdout.splitlines()
        if line.strip()
        and (
            "/tam/" in line.lower()
            or line.lower().endswith("/tam.py")
            or "token_analysis" in line.lower()
            or "compiler_tam" in line.lower()
        )
    )
    _require(tam_files == (), "tracked dedicated TAM implementation exists")


def _assert_passive_lattice_boundary() -> None:
    model = _read("apexforge/semantic_lattice/model.py")
    adapters = _read("apexforge/semantic_lattice/adapters.py")
    p11_8e = _read(
        "docs/p11/"
        "P11_8E_CANONICAL_PROJECTION_ADAPTERS_AND_OPTIONAL_CODEX_ADVISORY_ADAPTER.md"
    )
    p11_8h = _read(
        "docs/p11/"
        "P11_8H_FINAL_SEMANTIC_LATTICE_INTEGRATION_REGRESSION_AND_FREEZE.md"
    )

    _require('"tam.traceability"' in model, "canonical TAM lattice axis missing")
    _require(
        "without fabricating a TAM subject model" in adapters,
        "passive TAM projection boundary changed",
    )
    _require(
        "No canonical ApexForge TAM runtime/model type exists at this stage."
        in p11_8e,
        "P11.8E TAM absence boundary changed",
    )
    _require(
        "passive `tam.traceability` metadata, evidence, or provenance" in p11_8e,
        "P11.8E passive TAM projection boundary changed",
    )
    _require(
        "no canonical TAM runtime/model type is introduced by P11.8" in p11_8h,
        "P11.8H TAM boundary changed",
    )


def _assert_existing_provenance_owners() -> None:
    source = _read("apexforge/language/source.py")
    compiler = _read("apexforge/language/compiler.py")
    declarations = _read("apexforge/language/declarations.py")
    identities = _read("apexforge/language/identities.py")
    semantic_decision = _read(
        "apexforge/language/semantic_decision_lowering.py"
    )
    aether_records = _read("apexforge/aether_air/records.py")
    lattice_records = _read("apexforge/semantic_lattice/records.py")

    _require("class SourceSpan" in source, "SourceSpan owner missing")
    _require("class SourceMapEntry" in compiler, "SourceMapEntry owner missing")
    _require("class SourceMap" in compiler, "SourceMap owner missing")
    _require("air_id: str" in compiler, "SourceMapEntry AIR identity seam missing")
    _require("span: SourceSpan" in compiler, "SourceMapEntry span seam missing")
    _require(
        "class ProjectDeclarationOwner" in declarations,
        "declaration ownership seam missing",
    )
    _require(
        "class ProjectDeclaredIdentity" in identities,
        "declared identity seam missing",
    )
    _require(
        "def _provenance(span: SourceSpan)" in semantic_decision,
        "semantic-decision provenance seam missing",
    )
    _require(
        "provenance: Tuple[str, ...]" in aether_records,
        "AETHER-AIR provenance seam missing",
    )
    _require(
        "provenance: Tuple[str, ...]" in lattice_records,
        "semantic-lattice provenance seam missing",
    )


def _assert_transformation_seams() -> None:
    compiler = _read("apexforge/language/compiler.py")
    parser = _read("apexforge/language/parser.py")
    narrative_analysis = _read("apexforge/language/narrative_analysis.py")
    narrative_lowering = _read("apexforge/language/narrative_lowering.py")
    semantic_analysis = _read(
        "apexforge/language/semantic_decision_analysis.py"
    )
    semantic_lowering = _read(
        "apexforge/language/semantic_decision_lowering.py"
    )
    semantic_project = _read(
        "apexforge/language/semantic_decision_project_analysis.py"
    )

    required = (
        ("parse_source_unit", parser),
        ("compile_source_with_map", compiler),
        ("compile_source", compiler),
        ("analyze_narrative_source", narrative_analysis),
        ("lower_narrative_source", narrative_lowering),
        ("analyze_semantic_decision_source", semantic_analysis),
        ("lower_semantic_decision_source", semantic_lowering),
        ("analyze_semantic_decision_project_sources", semantic_project),
    )
    for name, text in required:
        _require(
            ("def " + name + "(") in text,
            "transformation seam missing: {}".format(name),
        )


def _assert_frozen_owner_immutability() -> None:
    completed = _git(
        "diff",
        "--exit-code",
        "afp-p11-src-h-freeze",
        "--",
        *FROZEN_OWNERS,
    )
    _require(
        completed.returncode == 0,
        "TAM-A mutated frozen provenance/semantic owner",
    )


def _assert_audit_document_contract() -> None:
    doc = _read(
        "docs/p11/P11_TAM_A_ARCHITECTURE_TRACEABILITY_OWNERSHIP_AUDIT.md"
    )

    required_phrases = (
        "observational, immutable, deterministic, and non-authoritative",
        "source",
        "token",
        "declaration",
        "reference",
        "scope",
        "type",
        "authority",
        "narrative",
        "ownership",
        "transformation",
        "`tam.traceability` remains a passive semantic-lattice axis",
        "TAM must not reconstruct compiler or semantic decisions",
        "TAP Check must consume canonical TAM evidence",
    )
    for phrase in required_phrases:
        _require(phrase in doc, "audit document contract missing: " + phrase)


def main() -> None:
    _assert_predecessor_and_branch()
    _assert_no_dedicated_tam_implementation()
    _assert_passive_lattice_boundary()
    _assert_existing_provenance_owners()
    _assert_transformation_seams()
    _assert_frozen_owner_immutability()
    _assert_audit_document_contract()

    print("P11_TAM_A_PREDECESSOR=PASS")
    print("DEDICATED_TAM_IMPLEMENTATION=NONE")
    print("TAM_TRACEABILITY_AXIS=PRESERVED_PASSIVE")
    print("SOURCE_SPAN_OWNER=PRESERVED")
    print("SOURCE_MAP_OWNER=PRESERVED")
    print("DECLARATION_OWNER=PRESERVED")
    print("IDENTITY_OWNER=PRESERVED")
    print("SEMANTIC_DECISION_PROVENANCE=PRESERVED")
    print("AETHER_AIR_PROVENANCE=PRESERVED")
    print("SEMANTIC_LATTICE_PROVENANCE=PRESERVED")
    print("TRANSFORMATION_SEAMS=IDENTIFIED")
    print("TRACE_DOMAINS=" + ",".join(TRACE_DOMAINS))
    print("TAM_AUTHORITY=OBSERVATIONAL_NONAUTHORITATIVE")
    print("FROZEN_OWNER_IMMUTABILITY=PASS")
    print("P11_TAM_A_ARCHITECTURE_OWNERSHIP_AUDIT=PASS")


if __name__ == "__main__":
    main()