"""P11.8A Parametric Semantic Lattice architecture audit smoke test."""

from pathlib import Path


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    from air.model import AIRDirective, AIRProgram
    from authority.model import AuthorityCheck, AuthorityGrant, Principal
    from language.narrative_graph import NarrativeSemanticGraph
    from language.narrative_model import (
        NarrativeCharacter,
        NarrativeContinuity,
        NarrativeIdentity,
        NarrativeScene,
    )
    from language.narrative_validation import NarrativeValidationReport
    from quad_vector.model import ResultantVector

    root = Path(__file__).resolve().parents[1]
    contract_path = (
        root
        / "docs"
        / "p11"
        / "P11_8A_PARAMETRIC_SEMANTIC_LATTICE_ARCHITECTURE_AUDIT.md"
    )
    require(contract_path.is_file(), "P11.8A architecture contract is missing")
    contract = contract_path.read_text(encoding="utf-8")

    required_contract_markers = (
        "Parametric Semantic Lattice Architecture & Compatibility Audit",
        "VARENIC-CREST-PULSE: APEXFORGE-P11 / TAM-v3 / QV-AETHER / STORY-SEMANTICS / APEXMOTION",
        "passive indexing, annotation, relationship, and traceability layer",
        "Priority ownership rule",
        "priority as passive lattice metadata",
        "Deterministic lattice ordering is a serialization/inspection invariant, not semantic priority.",
        "Convergence ownership rule",
        "P11.7 owns executable Quad-Vector synchronization and resultant resolution.",
        "P11.10 remains the roadmap stage for future advanced conditional, convergence, and Paradox Elevation semantics.",
        "Identity and reference boundary",
        "Determinism and evidence",
        "Codex remains optional/advisory",
        "P11.8B:** minimal immutable lattice model and metadata-axis taxonomy",
    )
    for marker in required_contract_markers:
        require(marker in contract, "P11.8A architecture marker missing: " + marker)

    owner_expectations = (
        (AIRDirective, "air.model"),
        (AIRProgram, "air.model"),
        (Principal, "authority.model"),
        (AuthorityCheck, "authority.model"),
        (AuthorityGrant, "authority.model"),
        (NarrativeIdentity, "language.narrative_model"),
        (NarrativeCharacter, "language.narrative_model"),
        (NarrativeScene, "language.narrative_model"),
        (NarrativeContinuity, "language.narrative_model"),
        (NarrativeSemanticGraph, "language.narrative_graph"),
        (NarrativeValidationReport, "language.narrative_validation"),
        (ResultantVector, "quad_vector.model"),
    )
    for symbol, owner in owner_expectations:
        require(
            symbol.__module__ == owner,
            f"{symbol.__name__} ownership moved from {owner}",
        )

    forbidden_owner_terms = (
        "lattice grants authority",
        "lattice resolves ambiguity",
        "lattice executes modules",
        "lattice validates narrative continuity",
        "priority metadata selects declarations",
        "lattice recomputes convergence",
    )
    lowered = contract.casefold()
    for term in forbidden_owner_terms:
        require(
            term.casefold() not in lowered,
            "P11.8A architecture accidentally grants forbidden ownership: " + term,
        )

    print("Existing AIR/authority/narrative/Quad-Vector ownership preservation: PASS")
    print("Passive semantic-lattice responsibility boundary: PASS")
    print("Non-operative priority metadata contract: PASS")
    print("P11.7 convergence/resultant ownership preservation: PASS")
    print("P11.10 future convergence-semantics boundary preservation: PASS")
    print("Canonical identity/reference non-replacement contract: PASS")
    print("Deterministic metadata ordering without semantic precedence: PASS")
    print("P11.8A runtime/loader/import/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
