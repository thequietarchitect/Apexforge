"""P11.9A AETHER-AIR 2.0 and interstitial-behavior architecture audit smoke test."""

from __future__ import annotations

from pathlib import Path
import subprocess


EXPECTED_BRANCH = "p11.9a-aether-air-2-interstitial-architecture-audit"
P11_8_FREEZE = "afp-p11.8h-freeze"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).strip()


def main() -> None:
    from air.model import AIRDirective, AIRProgram
    from authority.model import AuthorityCheck, AuthorityGrant, Principal
    from language.narrative_graph import NarrativeSemanticGraph
    from language.narrative_model import NarrativeIdentity
    from language.narrative_validation import NarrativeValidationReport
    from quad_vector.model import ResultantVector

    root = Path(__file__).resolve().parents[1]
    contract_path = (
        root
        / "docs"
        / "p11"
        / "P11_9A_AETHER_AIR_2_INTERSTITIAL_BEHAVIOR_ARCHITECTURE_AUDIT.md"
    )
    require(contract_path.is_file(), "P11.9A architecture contract is missing")
    contract = contract_path.read_text(encoding="utf-8")

    required_contract_markers = (
        "AETHER-AIR 2.0 and Interstitial Behavior Architecture & Compatibility Audit",
        "VARENIC-CREST-PULSE: APEXFORGE-P11 / TAM-v3 / QV-AETHER / STORY-SEMANTICS / APEXMOTION",
        "explicit interstitial semantic layer",
        "Interstitial behavior definition",
        "non-executing canonical description of behavioral intent",
        "Frozen ownership matrix",
        "P11.8 predecessor boundary",
        "P11.8H is a frozen predecessor contract.",
        "explicit canonical inputs",
        "Identity and reference boundary",
        "Determinism and provenance",
        "P11.10 ownership boundary",
        "P11.10 remains the exclusive roadmap owner for future advanced conditionals, convergence, and Paradox Elevation semantics.",
        "Codex remains optional/advisory",
        "P11.9B:** minimal immutable AETHER-AIR interstitial model and behavior-kind taxonomy",
    )
    for marker in required_contract_markers:
        require(marker in contract, "P11.9A architecture marker missing: " + marker)

    owner_expectations = (
        (AIRDirective, "air.model"),
        (AIRProgram, "air.model"),
        (Principal, "authority.model"),
        (AuthorityCheck, "authority.model"),
        (AuthorityGrant, "authority.model"),
        (NarrativeIdentity, "language.narrative_model"),
        (NarrativeSemanticGraph, "language.narrative_graph"),
        (NarrativeValidationReport, "language.narrative_validation"),
        (ResultantVector, "quad_vector.model"),
    )
    for symbol, owner in owner_expectations:
        require(
            symbol.__module__ == owner,
            f"{symbol.__name__} ownership moved from {owner}",
        )

    require(
        git(root, "branch", "--show-current") == EXPECTED_BRANCH,
        "unexpected P11.9A branch",
    )
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", P11_8_FREEZE, "HEAD"],
            cwd=root,
            check=False,
        ).returncode
        == 0,
        "P11.9A does not descend from the frozen P11.8H checkpoint",
    )
    require(
        subprocess.run(
            ["git", "diff", "--quiet", P11_8_FREEZE, "--", "apexforge/semantic_lattice"],
            cwd=root,
            check=False,
        ).returncode
        == 0,
        "P11.9A changed the frozen P11.8 semantic-lattice production surface",
    )

    forbidden_owner_terms = (
        "aether-air executes runtime effects",
        "aether-air grants authority",
        "aether-air resolves declaration precedence",
        "aether-air recomputes convergence",
        "aether-air mutates lattice snapshots",
        "aether-air owns paradox elevation",
        "interstitial behavior executes modules",
    )
    lowered = contract.casefold()
    for term in forbidden_owner_terms:
        require(
            term.casefold() not in lowered,
            "P11.9A architecture accidentally grants forbidden ownership: " + term,
        )

    print("Frozen P11.8H predecessor ancestry: PASS")
    print("Frozen P11.8 semantic-lattice production surface preservation: PASS")
    print("Existing AIR/authority/narrative/Quad-Vector ownership preservation: PASS")
    print("AETHER-AIR interstitial non-execution boundary: PASS")
    print("Explicit canonical-input and identity-preservation contract: PASS")
    print("Deterministic provenance without resolver precedence: PASS")
    print("P11.10 advanced-conditionals/convergence/Paradox-Elevation ownership: PASS")
    print("P11.9A runtime/backend/loader/serialization/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
