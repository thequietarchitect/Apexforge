"""AFP-P11.10C condition evidence/admissibility/evaluation smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
import inspect
from pathlib import Path
import subprocess

import semantic_decision
import semantic_decision.evaluation as evaluation
from semantic_decision import (
    CORE_ADMISSIBILITY_STATES,
    CORE_SEMANTIC_OUTCOME_KINDS,
    AdmissibilityState,
    AdvancedCondition,
    AdvancedConditionEvaluation,
    CandidateAlternative,
    ConditionEvidence,
    SemanticOutcome,
    SemanticOutcomeKind,
    evaluate_advanced_condition,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "p11.10c-condition-evidence-admissibility-higher-order-evaluation"
PREDECESSOR_TAG = "afp-p11.10b-freeze"
PREDECESSOR_SHORT = "c690cff"

CONTRACT = ROOT / "docs" / "p11" / "P11_10C_CANONICAL_CONDITION_EVIDENCE_ADMISSIBILITY_AND_HIGHER_ORDER_EVALUATION.md"
SMOKE = ROOT / "apexforge" / "p11_10c_condition_evidence_admissibility_higher_order_evaluation_smoke_test.py"
EVALUATION = ROOT / "apexforge" / "semantic_decision" / "evaluation.py"
PACKAGE_INIT = ROOT / "apexforge" / "semantic_decision" / "__init__.py"

ALLOWED = {
    CONTRACT.relative_to(ROOT).as_posix(),
    SMOKE.relative_to(ROOT).as_posix(),
    EVALUATION.relative_to(ROOT).as_posix(),
    PACKAGE_INIT.relative_to(ROOT).as_posix(),
}

EXPECTED_PUBLIC = (
    "AdvancedCondition",
    "CandidateAlternative",
    "SemanticOutcomeKind",
    "SemanticOutcome",
    "CORE_SEMANTIC_OUTCOME_KINDS",
    "ConditionEvidence",
    "AdmissibilityState",
    "CORE_ADMISSIBILITY_STATES",
    "AdvancedConditionEvaluation",
    "evaluate_advanced_condition",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git",) + arguments,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "git command failed: " + " ".join(arguments) + "\n" + completed.stderr.strip()
        )
    return completed.stdout.rstrip()


def status() -> str:
    return git("status", "--porcelain=v1", "--untracked-files=all")


def unchanged(*paths: str) -> bool:
    return not git("diff", "--name-only", PREDECESSOR_TAG, "--", *paths)


def assert_frozen(instance: object, field_name: str) -> None:
    try:
        setattr(instance, field_name, getattr(instance, field_name))
    except FrozenInstanceError:
        return
    raise AssertionError(type(instance).__name__ + " is not frozen")


def main() -> None:
    before = status()

    require(git("branch", "--show-current") == EXPECTED_BRANCH, "unexpected P11.10C branch")
    predecessor = git("rev-list", "-n", "1", PREDECESSOR_TAG)
    require(predecessor.startswith(PREDECESSOR_SHORT), "P11.10B freeze tag moved")
    ancestry = subprocess.run(
        ("git", "merge-base", "--is-ancestor", predecessor, "HEAD"),
        cwd=str(ROOT),
        check=False,
    )
    require(ancestry.returncode == 0, "P11.10C does not descend from frozen P11.10B")
    print("Frozen P11.10B predecessor and exact branch ancestry: PASS")

    require(
        unchanged("apexforge/semantic_decision/model.py"),
        "P11.10C modified frozen P11.10B model.py",
    )
    require(
        unchanged(
            "apexforge/aether_air",
            "apexforge/air",
            "apexforge/language",
            "apexforge/runtime",
            "apexforge/quad_vector",
            "apexforge/semantic_lattice",
            "apexforge/authority",
            "apexforge/governance",
        ),
        "P11.10C modified a predecessor production owner",
    )
    print("Frozen B model and predecessor production owners preserved: PASS")

    require(EVALUATION.is_file(), "semantic_decision evaluation module missing")
    require(CONTRACT.is_file(), "P11.10C contract missing")
    require(tuple(semantic_decision.__all__) == EXPECTED_PUBLIC, "unexpected package public surface")
    require(tuple(evaluation.__all__) == EXPECTED_PUBLIC[5:], "unexpected C module public surface")
    print("Exact additive ten-symbol semantic_decision public surface: PASS")

    expected_fields = {
        ConditionEvidence: ("condition", "result", "facts", "provenance"),
        AdmissibilityState: ("canonical_id",),
        AdvancedConditionEvaluation: ("condition", "evidence", "state_id", "provenance"),
    }
    for record_type, shape in expected_fields.items():
        require(is_dataclass(record_type), record_type.__name__ + " must be a dataclass")
        require(
            tuple(item.name for item in fields(record_type)) == shape,
            record_type.__name__ + " field shape changed",
        )

    condition = AdvancedCondition(
        identity="condition:alpha",
        condition_kind="evidence.aggregate",
        payload=("passive",),
        provenance=("condition-source",),
    )
    yes = ConditionEvidence(
        condition=condition,
        result=True,
        facts=(("signal", 1),),
        provenance=("evidence-yes",),
    )
    no = ConditionEvidence(
        condition=condition,
        result=False,
        facts=(("signal", 0),),
        provenance=("evidence-no",),
    )
    unknown = ConditionEvidence(
        condition=condition,
        result=None,
        facts=(("signal", None),),
        provenance=("evidence-unknown",),
    )
    direct = AdvancedConditionEvaluation(
        condition=condition,
        evidence=(yes,),
        state_id="extension.state",
        provenance=("direct",),
    )
    assert_frozen(yes, "result")
    assert_frozen(AdmissibilityState("extension.state"), "canonical_id")
    assert_frozen(direct, "state_id")
    require(direct.condition is condition and direct.evidence[0] is yes, "C record identity changed")
    print("Frozen C record shapes and exact predecessor object identity: PASS")

    require(
        tuple(item.canonical_id for item in CORE_ADMISSIBILITY_STATES)
        == ("admissible", "inadmissible", "indeterminate"),
        "core admissibility taxonomy changed",
    )
    require(
        all(type(item) is AdmissibilityState for item in CORE_ADMISSIBILITY_STATES),
        "core admissibility taxonomy contains non-canonical values",
    )
    require(AdmissibilityState("future.state").canonical_id == "future.state", "state ids closed early")
    print("Exact three-state admissibility taxonomy with open structural identifiers: PASS")

    cases = (
        ((), "indeterminate"),
        ((yes,), "admissible"),
        ((no,), "inadmissible"),
        ((yes, no), "indeterminate"),
        ((yes, unknown), "indeterminate"),
    )
    for evidence_items, expected in cases:
        result = evaluate_advanced_condition(condition, evidence=evidence_items)
        require(result.condition is condition, "evaluation copied/replaced condition")
        require(result.evidence is evidence_items, "evaluation copied/reordered evidence tuple")
        require(result.state_id == expected, "canonical C evaluation rule changed")
    print("Deterministic five-case higher-order evaluation rule: PASS")

    result = evaluate_advanced_condition(condition, evidence=(yes, no))
    require(result.evidence[0] is yes and result.evidence[1] is no, "evidence identity/order changed")
    require(
        result.provenance == ("condition-source", "evidence-yes", "evidence-no"),
        "evaluation provenance aggregation changed",
    )
    require(
        result.state_id == "indeterminate",
        "mixed evidence became selected/converged/elevated",
    )
    print("Evidence encounter order, provenance, and mixed-result indeterminacy: PASS")

    equal_but_distinct = AdvancedCondition(
        identity=condition.identity,
        condition_kind=condition.condition_kind,
        payload=condition.payload,
        provenance=condition.provenance,
    )
    foreign = ConditionEvidence(condition=equal_but_distinct, result=True)
    try:
        evaluate_advanced_condition(condition, evidence=(foreign,))
    except ValueError:
        pass
    else:
        raise AssertionError("equal-but-distinct condition evidence was accepted")

    for constructor in (
        lambda: ConditionEvidence(condition=condition, result=1),
        lambda: ConditionEvidence(condition=condition, result=True, facts=[]),
        lambda: ConditionEvidence(condition=condition, result=True, facts=(("k", []),)),
        lambda: ConditionEvidence(condition=condition, result=True, provenance=["p"]),
        lambda: AdvancedConditionEvaluation(condition, [yes], "admissible"),
    ):
        try:
            constructor()
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("non-canonical C input structure was accepted")
    print("Exact evidence identity and immutable input boundaries: PASS")

    source = EVALUATION.read_text(encoding="utf-8")
    forbidden = (
        "runtime.",
        "air.",
        "narrative_",
        "quad_vector",
        "aether_air",
        "authority",
        "governance",
        "CandidateAlternative(",
        "SemanticOutcome(",
        "CORE_SEMANTIC_OUTCOME_KINDS",
        "paradox.elevation_candidate",
    )
    for token in forbidden:
        require(token not in source, "forbidden C ownership token entered evaluation.py: " + token)

    public_functions = tuple(
        name
        for name, value in vars(evaluation).items()
        if not name.startswith("_") and inspect.isfunction(value)
    )
    require(
        public_functions == ("evaluate_advanced_condition",),
        "unexpected public C functions: " + repr(public_functions),
    )
    print("No runtime/candidate/convergence/ranking/Paradox-Elevation behavior: PASS")

    contract_text = CONTRACT.read_text(encoding="utf-8")
    markers = (
        "Higher-order evaluation in C means deterministic classification over explicit already-canonical evidence",
        "Mixed evidence is `indeterminate`; it is not Paradox Elevation",
        "P11.10D owns semantic convergence-set construction",
        "P11.10E owns deterministic convergence selection",
        "P11.10F owns Paradox Elevation eligibility",
        "Equal-but-distinct condition objects are rejected",
    )
    for marker in markers:
        require(marker in contract_text, "missing P11.10C ownership marker: " + repr(marker))
    print("C ownership and downstream boundary contract: PASS")

    status_lines = tuple(line for line in status().splitlines() if line)
    observed = {}
    for line in status_lines:
        path = line[3:].replace("\\", "/")
        observed[path] = line[:2]
    if observed:
        require(set(observed) == ALLOWED, "unexpected P11.10C artifacts: " + repr(sorted(observed)))
        require(
            observed[PACKAGE_INIT.relative_to(ROOT).as_posix()] == " M",
            "P11.10C package initializer must be the only tracked pre-commit modification",
        )
        for path in ALLOWED - {PACKAGE_INIT.relative_to(ROOT).as_posix()}:
            require(observed[path] == "??", "unexpected pre-commit status for " + path)

    after = status()
    require(before == after, "P11.10C smoke mutated repository status")
    print("Repository no-op C boundary: PASS")


if __name__ == "__main__":
    main()
