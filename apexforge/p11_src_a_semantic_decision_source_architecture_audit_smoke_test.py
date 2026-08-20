"""P11-SRC-A semantic-decision source architecture audit.

Audit-only gate. This slice must not introduce source parser/lowering production
files or alter frozen P11.10 semantic-decision ownership.
"""

from pathlib import Path

from language.lexer import KEYWORDS
from language.narrative_lowering import lower_narrative_source
from language.narrative_parser import parse_narrative_source
from language.parser import SourceUnitNode
from language.project import ProjectBuild
import semantic_decision as semantic_decision


PROPOSED_SOURCE_WORDS = (
    "decision",
    "candidate",
    "converge",
    "using",
    "incompatible",
    "paradox",
    "elevate",
)

REQUIRED_P11_10_EXPORTS = (
    "AdvancedCondition",
    "CandidateAlternative",
    "ConvergencePolicy",
    "SemanticConvergenceSet",
    "SemanticConvergenceResolution",
    "ParadoxElevationAssessment",
    "ElevatedSemanticState",
    "evaluate_advanced_condition",
    "construct_semantic_convergence_set",
    "apply_semantic_convergence_policy",
    "assess_paradox_elevation",
    "elevate_paradox_assessment",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> None:
    root = _repo_root()

    assert all(word not in KEYWORDS for word in PROPOSED_SOURCE_WORDS), (
        "P11-SRC proposed structural words must remain unclaimed at the "
        "architecture-audit boundary."
    )

    source_unit_declarations = str(SourceUnitNode.__annotations__["declarations"])
    assert "Decision" not in source_unit_declarations
    assert "semantic" not in source_unit_declarations.lower()

    project_build_annotations = " ".join(
        str(value) for value in ProjectBuild.__annotations__.values()
    )
    assert "SemanticDecision" not in project_build_annotations

    assert callable(parse_narrative_source)
    assert callable(lower_narrative_source)

    for name in REQUIRED_P11_10_EXPORTS:
        assert hasattr(semantic_decision, name), (
            "Frozen P11.10 semantic_decision public surface is missing "
            f"required owner {name!r}."
        )

    assert tuple(item.canonical_id for item in semantic_decision.CORE_SEMANTIC_OUTCOME_KINDS) == (
        "selected",
        "composed",
        "unresolved",
        "paradox.elevation_candidate",
    )
    assert tuple(item.canonical_id for item in semantic_decision.CORE_ADMISSIBILITY_STATES) == (
        "admissible",
        "inadmissible",
        "indeterminate",
    )
    assert semantic_decision.CORE_CONVERGENCE_POLICY_IDS == (
        "select.explicit-order",
        "compose.all-admissible",
        "rank.explicit-order",
    )

    for relative in (
        "apexforge/language/semantic_decision_source.py",
        "apexforge/language/semantic_decision_parser.py",
        "apexforge/language/semantic_decision_lowering.py",
    ):
        assert not (root / relative).exists(), (
            "P11-SRC-A is audit-only; production source bridge appeared early: "
            + relative
        )

    print("P11_SRC_A_ARCHITECTURE_AUDIT=PASS")
    print("SOURCE_WORD_OWNERSHIP=FREE")
    print("AIR_SOURCE_UNIT_OWNERSHIP=UNCHANGED")
    print("PROJECT_BUILD_OWNERSHIP=UNCHANGED")
    print("NARRATIVE_PARALLEL_SEAM=CONFIRMED")
    print("P11_10_SEMANTIC_OWNERSHIP=PRESERVED")
    print("PRODUCTION_MUTATION=NONE")


if __name__ == "__main__":
    main()
