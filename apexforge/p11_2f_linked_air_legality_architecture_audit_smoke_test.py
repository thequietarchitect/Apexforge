"""Architecture contract audit for P11.2F linked AIR legality."""

from __future__ import annotations

from pathlib import Path
import subprocess


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DOCUMENT = (
    REPOSITORY_ROOT
    / "docs"
    / "p11"
    / "P11_2F_LINKED_AIR_LEGALITY_AND_GOVERNANCE_BOUNDARY.md"
)
CONTINUITY_DOCUMENT = (
    REPOSITORY_ROOT
    / "docs"
    / "p11"
    / "P11_CONTINUITY_PULSE.md"
)
BASELINE_COMMIT = "bb1f3a3a33aabda0dc5ab5b37e0898fbbc636544"

AUDIT_OWNED_PATHS = {
    "apexforge/p11_2f_linked_air_legality_architecture_audit_smoke_test.py",
    "docs/p11/P11_2F_LINKED_AIR_LEGALITY_AND_GOVERNANCE_BOUNDARY.md",
}

PROTECTED_PATHS = {
    "apexforge/directives/gravitas.air.json",
    "apexforge/p11_5a_narrative_semantic_foundation_architecture_audit_smoke_test.py",
    "apexforge/p11_5b_minimal_narrative_semantic_model_smoke_test.py",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_lines(*arguments: str) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return tuple(
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    )


def test_baseline_and_owned_files() -> None:
    require(
        git_lines("cat-file", "-t", BASELINE_COMMIT) == ("commit",),
        "P11.2E baseline commit is unavailable",
    )
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(
        AUDIT_DOCUMENT.is_file() and Path(__file__).is_file(),
        "a P11.2F-A audit-owned file is missing",
    )
    require(
        AUDIT_OWNED_PATHS
        == {
            "apexforge/p11_2f_linked_air_legality_architecture_audit_smoke_test.py",
            "docs/p11/P11_2F_LINKED_AIR_LEGALITY_AND_GOVERNANCE_BOUNDARY.md",
        },
        "P11.2F-A ownership changed",
    )


def test_contract_vocabulary(document: str) -> None:
    normalized = " ".join(document.split())
    required_phrases = (
        "P11.2F Linked AIR Legality and Governance Boundary",
        "P11.2F introduces no new source syntax",
        "The linker must not apply a universal case-folding rule without evidence",
        "AIRVerifier owns linked-program structural legality",
        "A malformed symbol graph, missing target, duplicate declaration, or cyclic inheritance graph is a structural error",
        "Tap Check is observational and never activates directives",
        "routed through Concordat Court using WCCD and Gravitas Mode",
        "Structural errors and authorization denials remain non-overridable",
        "P11.2F-A — Architecture audit",
        "P11.2F-G — Integration and regression gate",
    )
    for phrase in required_phrases:
        require(
            phrase in normalized,
            f"P11.2F audit omits required contract phrase: {phrase}",
        )


def test_existing_architecture_boundaries() -> None:
    linker = (
        REPOSITORY_ROOT / "apexforge" / "air" / "linker.py"
    ).read_text(encoding="utf-8")
    verifier = (
        REPOSITORY_ROOT / "apexforge" / "air" / "verify.py"
    ).read_text(encoding="utf-8")
    workflow_compiler = (
        REPOSITORY_ROOT / "apexforge" / "workflow" / "compiler.py"
    ).read_text(encoding="utf-8")
    project_builder = (
        REPOSITORY_ROOT / "apexforge" / "language" / "project.py"
    ).read_text(encoding="utf-8")
    authority_registry = (
        REPOSITORY_ROOT / "apexforge" / "authority" / "registry.py"
    ).read_text(encoding="utf-8")
    directive_engine = (
        REPOSITORY_ROOT / "apexforge" / "workflow" / "directive_engine.py"
    ).read_text(encoding="utf-8")
    governance_conflicts = (
        REPOSITORY_ROOT / "apexforge" / "governance" / "conflicts.py"
    ).read_text(encoding="utf-8")

    require(
        "The linker combines compilation units only." in linker
        and "validator responsibilities after linking" in linker,
        "linker/validator ownership statement changed",
    )
    require(
        "class AIRVerifier:" in verifier
        and "return VerificationResult(program, tuple(sorted(diagnostics)))"
        in verifier,
        "AIRVerifier deterministic diagnostic boundary changed",
    )
    require(
        "AIRWorkflowInvocation(target=invocation.target)"
        in workflow_compiler,
        "workflow target deferral boundary changed",
    )
    require(
        "preserve_module_case_distinctions"
        in project_builder
        and "if not graph.is_legacy:"
        in project_builder,
        "module-project exact-case linker profile changed",
    )
    require(
        "class DuplicateAuthorityError" in authority_registry
        and "if key in self._authorities:" in authority_registry
        and "authority.name.casefold()" in authority_registry,
        "P11.2F-D duplicate-safe authority registry boundary changed",
    )
    require(
        '"AIR065"' in verifier
        and "directive_requirement_owners" in verifier,
        "P11.2F-E static requirement ownership boundary changed",
    )
    require(
        "class DirectiveRequirementOwnershipError" in directive_engine
        and "if owner.requirements and len(owner.directives) != 1"
        in directive_engine,
        "runtime requirement-ownership defense disappeared",
    )
    require(
        "class ConflictEvidence" in governance_conflicts
        and "class ConflictReferral" in governance_conflicts
        and "def route_conflict_evidence" in governance_conflicts
        and 'CONCORDAT_COURT = "Concordat Court"'
        in governance_conflicts
        and '"WCCD"' in governance_conflicts
        and '"Gravitas Mode"' in governance_conflicts
        and 'TAP_CHECK_MODE = "observational"'
        in governance_conflicts
        and "activates_directives: bool = False"
        in governance_conflicts,
        "P11.2F-F passive Concordat referral boundary changed",
    )
    require(
        all(
            token not in governance_conflicts
            for token in (
                "AIRVerifier",
                "RuntimeEngine",
                "AuthorityRegistry",
                "subprocess",
                "open(",
                "execute(",
            )
        ),
        "P11.2F-F governance evidence acquired active behavior",
    )


def test_continuity_and_protected_boundaries() -> None:
    continuity = CONTINUITY_DOCUMENT.read_text(encoding="utf-8")
    require(
        "Concordat TAM-v3 remains the governance authority." in continuity,
        "continuity contract omits Concordat TAM-v3",
    )
    require(
        "Tap Check never activates directives." in continuity,
        "continuity contract changed Tap Check activation semantics",
    )
    require(
        "Conflicts route through Concordat Court using WCCD and Gravitas Mode."
        in continuity,
        "continuity contract omits canonical conflict routing",
    )
    require(
        PROTECTED_PATHS
        == {
            "apexforge/directives/gravitas.air.json",
            "apexforge/p11_5a_narrative_semantic_foundation_architecture_audit_smoke_test.py",
            "apexforge/p11_5b_minimal_narrative_semantic_model_smoke_test.py",
        },
        "P11.2F protected path set changed",
    )


def main() -> None:
    document = AUDIT_DOCUMENT.read_text(encoding="utf-8")
    test_baseline_and_owned_files()
    test_contract_vocabulary(document)
    test_existing_architecture_boundaries()
    test_continuity_and_protected_boundaries()
    print("P11.2F linked AIR legality architecture audit smoke test passed.")


if __name__ == "__main__":
    main()
