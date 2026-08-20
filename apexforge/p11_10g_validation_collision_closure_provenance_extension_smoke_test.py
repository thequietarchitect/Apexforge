"""AFP-P11.10G semantic-decision validation smoke test."""

from __future__ import annotations

import dataclasses
import inspect
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "p11.10g-validation-collision-closure-provenance-extension"
PREDECESSOR_TAG = "afp-p11.10f-freeze"
ALLOWED = {
    "apexforge/p11_10g_validation_collision_closure_provenance_extension_smoke_test.py",
    "apexforge/semantic_decision/__init__.py",
    "apexforge/semantic_decision/validation.py",
    "docs/p11/P11_10G_VALIDATION_COLLISION_CLOSURE_PROVENANCE_AND_EXTENSION_CONTRACTS.md",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return completed.stdout.rstrip("\r\n")


def status_paths() -> set[str]:
    output = git("status", "--porcelain", "--untracked-files=all")
    if not output:
        return set()
    paths = set()
    for line in output.splitlines():
        require(len(line) >= 4, "malformed porcelain status line: " + repr(line))
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.add(path.replace("\\", "/"))
    return paths


def unchanged(path: str) -> bool:
    return not git("diff", "--name-only", PREDECESSOR_TAG, "--", path)


def require_value_error(callable_object, text: str) -> None:
    try:
        callable_object()
    except ValueError:
        return
    raise AssertionError(text)


def make_binding(sd, identity: str, state_id: str = "admissible"):
    condition = sd.AdvancedCondition(
        "condition:" + identity,
        "semantic.test",
        provenance=("condition:" + identity,),
    )
    if state_id == "admissible":
        evidence = (
            sd.ConditionEvidence(
                condition,
                True,
                facts=(("fact", identity),),
                provenance=("evidence:" + identity,),
            ),
        )
        evaluation = sd.evaluate_advanced_condition(condition, evidence=evidence)
    elif state_id == "inadmissible":
        evidence = (
            sd.ConditionEvidence(
                condition,
                False,
                facts=(("fact", identity),),
                provenance=("evidence:" + identity,),
            ),
        )
        evaluation = sd.evaluate_advanced_condition(condition, evidence=evidence)
    else:
        evidence = ()
        evaluation = sd.AdvancedConditionEvaluation(
            condition,
            evidence,
            state_id,
            condition.provenance,
        )
    candidate = sd.CandidateAlternative(
        identity,
        payload=("payload", identity),
        provenance=("candidate:" + identity,),
    )
    return sd.EvaluatedCandidate(candidate, evaluation)


def make_resolution(sd, bindings, policy):
    convergence_set = sd.construct_semantic_convergence_set(
        bindings,
        policy=policy,
    )
    return sd.apply_semantic_convergence_policy(convergence_set)


def paradox_fixture(sd):
    a = make_binding(sd, "candidate:a")
    b = make_binding(sd, "candidate:b")
    c = make_binding(sd, "candidate:c")
    policy = sd.ConvergencePolicy(
        "rank.explicit-order",
        parameters=(
            ("order", ("candidate:c", "candidate:a", "candidate:b")),
        ),
        provenance=("policy:rank",),
    )
    resolution = make_resolution(sd, (a, b, c), policy)
    alternatives = resolution.outcome.alternatives
    pairs = []
    for left_index in range(len(alternatives)):
        for right_index in range(left_index + 1, len(alternatives)):
            left = alternatives[left_index]
            right = alternatives[right_index]
            pairs.append(
                sd.ParadoxIncompatibilityEvidence(
                    left,
                    right,
                    True,
                    provenance=(
                        "pair:" + left.identity + ":" + right.identity,
                    ),
                )
            )
    evidence = sd.ParadoxElevationEvidence(
        resolution,
        tuple(pairs),
        True,
        provenance=("paradox:evidence",),
    )
    assessment = sd.assess_paradox_elevation(evidence)
    state = sd.elevate_paradox_assessment(assessment)
    return resolution, evidence, assessment, state


def main() -> None:
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong P11.10G branch")
    subprocess.run(
        ("git", "merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD"),
        cwd=ROOT,
        check=True,
    )
    print("Frozen P11.10F predecessor and exact branch ancestry: PASS")

    for path in (
        "apexforge/semantic_decision/model.py",
        "apexforge/semantic_decision/evaluation.py",
        "apexforge/semantic_decision/convergence.py",
        "apexforge/semantic_decision/resolution.py",
        "apexforge/semantic_decision/paradox.py",
        "apexforge/aether_air",
        "apexforge/air",
        "apexforge/language",
        "apexforge/runtime",
        "apexforge/quad_vector",
        "apexforge/semantic_lattice",
        "apexforge/authority",
        "apexforge/governance",
        "apexforge/causality",
    ):
        require(unchanged(path), "frozen predecessor owner changed: " + path)
    print("Frozen B-F semantic-decision and predecessor owners preserved: PASS")

    sys.path.insert(0, str(ROOT / "apexforge"))
    import semantic_decision as sd
    import semantic_decision.validation as validation

    expected_all = (
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
        "ConvergencePolicy",
        "EvaluatedCandidate",
        "SemanticConvergenceSet",
        "construct_semantic_convergence_set",
        "CORE_CONVERGENCE_POLICY_IDS",
        "RankedCandidate",
        "SemanticConvergenceResolution",
        "apply_semantic_convergence_policy",
        "ParadoxIncompatibilityEvidence",
        "ParadoxElevationEvidence",
        "ParadoxElevationAssessment",
        "ElevatedSemanticState",
        "assess_paradox_elevation",
        "elevate_paradox_assessment",
        "SemanticDecisionValidationReceipt",
        "ParadoxElevationValidationReceipt",
        "ElevatedSemanticStateValidationReceipt",
        "validate_semantic_convergence_resolution",
        "validate_paradox_elevation_assessment",
        "validate_elevated_semantic_state",
    )
    require(tuple(sd.__all__) == expected_all, "semantic_decision public surface changed")
    require(
        tuple(validation.__all__)
        == (
            "SemanticDecisionValidationReceipt",
            "ParadoxElevationValidationReceipt",
            "ElevatedSemanticStateValidationReceipt",
            "validate_semantic_convergence_resolution",
            "validate_paradox_elevation_assessment",
            "validate_elevated_semantic_state",
        ),
        "validation public surface changed",
    )
    print("Exact additive thirty-symbol semantic_decision public surface: PASS")

    require(
        tuple(
            field.name
            for field in dataclasses.fields(sd.SemanticDecisionValidationReceipt)
        )
        == (
            "resolution",
            "extension_admissibility_state_ids",
            "extension_outcome_kind_ids",
            "extension_policy_ids",
            "provenance",
            "checks",
        ),
        "SemanticDecisionValidationReceipt fields changed",
    )
    require(
        tuple(
            field.name
            for field in dataclasses.fields(sd.ParadoxElevationValidationReceipt)
        )
        == ("assessment", "resolution_receipt", "provenance", "checks"),
        "ParadoxElevationValidationReceipt fields changed",
    )
    require(
        tuple(
            field.name
            for field in dataclasses.fields(
                sd.ElevatedSemanticStateValidationReceipt
            )
        )
        == ("state", "assessment_receipt", "provenance", "checks"),
        "ElevatedSemanticStateValidationReceipt fields changed",
    )
    require(
        str(inspect.signature(sd.validate_semantic_convergence_resolution))
        == "(resolution: 'SemanticConvergenceResolution', *, extension_admissibility_state_ids: 'Tuple[str, ...]' = (), extension_outcome_kind_ids: 'Tuple[str, ...]' = (), extension_policy_ids: 'Tuple[str, ...]' = ()) -> 'SemanticDecisionValidationReceipt'",
        "ordinary validator signature changed",
    )
    print("Layered G receipt shapes and ordinary validation signature: PASS")

    a = make_binding(sd, "candidate:a")
    b = make_binding(sd, "candidate:b")
    c = make_binding(sd, "candidate:c")
    select_policy = sd.ConvergencePolicy(
        "select.explicit-order",
        parameters=(
            ("order", ("candidate:c", "candidate:a", "candidate:b")),
        ),
        provenance=("policy:select",),
    )
    resolution = make_resolution(sd, (a, b, c), select_policy)
    receipt = sd.validate_semantic_convergence_resolution(resolution)
    require(receipt.resolution is resolution, "ordinary receipt copied resolution")
    require(receipt.provenance == resolution.provenance, "ordinary receipt provenance changed")
    require(
        receipt.checks
        == (
            "extension-identifier-collision",
            "condition-evidence-closure",
            "condition-evidence-collision",
            "admissibility-state-closure",
            "candidate-identity-collision",
            "convergence-membership-closure",
            "policy-parameter-collision",
            "policy-extension-closure",
            "ranking-closure",
            "outcome-alternative-closure",
            "outcome-extension-closure",
            "policy-result-consistency",
            "provenance-integrity",
        ),
        "ordinary validation checks changed",
    )
    print("Valid B-E graph receives passive exact-object validation receipt: PASS")

    ext = make_binding(sd, "candidate:extension", "extension.reviewable")
    compose_policy = sd.ConvergencePolicy(
        "compose.all-admissible",
        provenance=("policy:compose",),
    )
    ext_resolution = make_resolution(sd, (a, b, ext), compose_policy)
    ext_receipt = sd.validate_semantic_convergence_resolution(
        ext_resolution,
        extension_admissibility_state_ids=("extension.reviewable",),
        extension_outcome_kind_ids=("outcome.future",),
    )
    require(
        ext_receipt.extension_admissibility_state_ids == ("extension.reviewable",)
        and ext_receipt.extension_outcome_kind_ids == ("outcome.future",),
        "extension identifiers were not preserved",
    )
    extension_policy = sd.ConvergencePolicy(
        "policy.future",
        provenance=("policy:future",),
    )
    extension_resolution = make_resolution(sd, (a, b), extension_policy)
    extension_receipt = sd.validate_semantic_convergence_resolution(
        extension_resolution,
        extension_policy_ids=("policy.future",),
    )
    require(
        extension_receipt.resolution.outcome.kind_id == "unresolved",
        "extension policy acquired invented operative semantics",
    )
    require_value_error(
        lambda: sd.validate_semantic_convergence_resolution(
            ext_resolution,
        ),
        "undeclared extension admissibility state was accepted",
    )
    require_value_error(
        lambda: sd.validate_semantic_convergence_resolution(
            resolution,
            extension_policy_ids=("select.explicit-order",),
        ),
        "core/extension policy collision was accepted",
    )
    print("Extension declaration, collision, and non-operative closure: PASS")

    bad_condition = sd.AdvancedCondition(
        "condition:bad",
        "semantic.test",
        provenance=("condition:bad",),
    )
    duplicate_fact_evidence = (
        sd.ConditionEvidence(
            bad_condition,
            True,
            facts=(("x", 1), ("x", 2)),
            provenance=("evidence:bad",),
        ),
    )
    bad_eval = sd.evaluate_advanced_condition(
        bad_condition,
        evidence=duplicate_fact_evidence,
    )
    bad_binding = sd.EvaluatedCandidate(
        sd.CandidateAlternative(
            "candidate:bad",
            provenance=("candidate:bad",),
        ),
        bad_eval,
    )
    bad_resolution = make_resolution(sd, (a, b, bad_binding), compose_policy)
    require_value_error(
        lambda: sd.validate_semantic_convergence_resolution(bad_resolution),
        "duplicate fact keys were accepted",
    )

    wrong_core_eval = sd.AdvancedConditionEvaluation(
        bad_condition,
        (),
        "admissible",
        bad_condition.provenance,
    )
    wrong_binding = sd.EvaluatedCandidate(
        sd.CandidateAlternative(
            "candidate:wrong-state",
            provenance=("candidate:wrong-state",),
        ),
        wrong_core_eval,
    )
    wrong_resolution = make_resolution(sd, (a, b, wrong_binding), compose_policy)
    require_value_error(
        lambda: sd.validate_semantic_convergence_resolution(wrong_resolution),
        "incorrect frozen C admissibility state was accepted",
    )
    print("Condition/evidence collision and frozen C state consistency: PASS")

    duplicate_identity_binding = sd.EvaluatedCandidate(
        sd.CandidateAlternative(
            "candidate:a",
            payload=("different",),
            provenance=("candidate:a:duplicate",),
        ),
        make_binding(sd, "condition-carrier").evaluation,
    )
    duplicate_identity_resolution = make_resolution(
        sd,
        (a, b, duplicate_identity_binding),
        compose_policy,
    )
    require_value_error(
        lambda: sd.validate_semantic_convergence_resolution(
            duplicate_identity_resolution
        ),
        "duplicate candidate identity was accepted",
    )

    wrong_members_set = sd.SemanticConvergenceSet(
        policy=compose_policy,
        candidates=(a, b),
        members=(a,),
        provenance=compose_policy.provenance
        + a.candidate.provenance
        + a.evaluation.provenance
        + b.candidate.provenance
        + b.evaluation.provenance,
    )
    wrong_members_resolution = sd.apply_semantic_convergence_policy(wrong_members_set)
    require_value_error(
        lambda: sd.validate_semantic_convergence_resolution(
            wrong_members_resolution
        ),
        "incorrect D membership closure was accepted",
    )

    duplicate_key_policy = sd.ConvergencePolicy(
        "select.explicit-order",
        parameters=(
            ("order", ("candidate:a", "candidate:b")),
            ("order", ("candidate:b", "candidate:a")),
        ),
        provenance=("policy:duplicate-key",),
    )
    duplicate_key_resolution = make_resolution(sd, (a, b), duplicate_key_policy)
    require_value_error(
        lambda: sd.validate_semantic_convergence_resolution(
            duplicate_key_resolution
        ),
        "duplicate policy parameter keys were accepted",
    )
    print("Candidate collision, D membership closure, and policy-key collision: PASS")

    expected = sd.apply_semantic_convergence_policy(resolution.convergence_set)
    wrong_outcome = sd.SemanticOutcome(
        "selected",
        alternatives=(a.candidate,),
        provenance=resolution.convergence_set.provenance,
    )
    inconsistent_resolution = sd.SemanticConvergenceResolution(
        resolution.convergence_set,
        resolution.ranking,
        wrong_outcome,
        resolution.provenance,
    )
    require(expected.outcome.alternatives[0] is c.candidate, "fixture selection changed")
    require_value_error(
        lambda: sd.validate_semantic_convergence_resolution(
            inconsistent_resolution
        ),
        "E policy/result inconsistency was accepted",
    )

    one_policy = sd.ConvergencePolicy(
        "select.explicit-order",
        parameters=(("order", ("candidate:a",)),),
        provenance=("policy:one",),
    )
    one_resolution = make_resolution(sd, (a,), one_policy)
    one_receipt = sd.validate_semantic_convergence_resolution(one_resolution)
    require(
        one_receipt.resolution.outcome.kind_id == "unresolved",
        "valid one-member E unresolved fallback was rejected",
    )
    print("E policy/result consistency and valid insufficient-cardinality fallback: PASS")

    duplicate_prov_binding = sd.EvaluatedCandidate(
        sd.CandidateAlternative(
            "candidate:duplicate-prov",
            provenance=("dup", "dup"),
        ),
        make_binding(sd, "duplicate-prov-eval").evaluation,
    )
    duplicate_prov_resolution = make_resolution(
        sd,
        (a, b, duplicate_prov_binding),
        compose_policy,
    )
    require_value_error(
        lambda: sd.validate_semantic_convergence_resolution(
            duplicate_prov_resolution
        ),
        "duplicate provenance was accepted",
    )
    print("Provenance integrity and deterministic lineage validation: PASS")

    paradox_resolution, paradox_evidence, assessment, state = paradox_fixture(sd)
    assessment_receipt = sd.validate_paradox_elevation_assessment(assessment)
    require(
        assessment_receipt.assessment is assessment,
        "Paradox validation receipt copied assessment",
    )
    require(
        assessment_receipt.resolution_receipt.resolution is paradox_resolution,
        "Paradox receipt lost exact E resolution lineage",
    )
    require(
        assessment_receipt.provenance == assessment.provenance,
        "Paradox receipt provenance changed",
    )
    print("Layered Paradox assessment validation preserves exact E receipt lineage: PASS")

    duplicate_pair_evidence = sd.ParadoxElevationEvidence(
        paradox_resolution,
        paradox_evidence.incompatibilities
        + (paradox_evidence.incompatibilities[0],),
        True,
        provenance=("paradox:duplicate-pair",),
    )
    duplicate_pair_assessment = sd.assess_paradox_elevation(
        duplicate_pair_evidence
    )
    require_value_error(
        lambda: sd.validate_paradox_elevation_assessment(
            duplicate_pair_assessment
        ),
        "duplicate unordered Paradox pair was accepted",
    )

    outsider = sd.CandidateAlternative(
        "candidate:outsider",
        provenance=("candidate:outsider",),
    )
    foreign_pair = sd.ParadoxIncompatibilityEvidence(
        paradox_resolution.outcome.alternatives[0],
        outsider,
        True,
        provenance=("pair:foreign",),
    )
    foreign_evidence = sd.ParadoxElevationEvidence(
        paradox_resolution,
        (foreign_pair,),
        True,
        provenance=("paradox:foreign",),
    )
    foreign_assessment = sd.assess_paradox_elevation(foreign_evidence)
    require_value_error(
        lambda: sd.validate_paradox_elevation_assessment(foreign_assessment),
        "foreign Paradox endpoint was accepted",
    )

    tampered_assessment = sd.ParadoxElevationAssessment(
        paradox_evidence,
        False,
        None,
        assessment.provenance,
    )
    require_value_error(
        lambda: sd.validate_paradox_elevation_assessment(tampered_assessment),
        "tampered F eligibility was accepted",
    )
    print("Paradox endpoint/pair collision and exact F assessment consistency: PASS")

    state_receipt = sd.validate_elevated_semantic_state(state)
    require(state_receipt.state is state, "elevated-state receipt copied state")
    require(
        state_receipt.assessment_receipt.assessment is assessment,
        "elevated receipt lost exact assessment lineage",
    )
    require(
        state_receipt.provenance == state.provenance,
        "elevated-state receipt provenance changed",
    )

    tampered_state = sd.ElevatedSemanticState(
        state.assessment,
        tuple(reversed(state.alternatives)),
        state.provenance,
    )
    require_value_error(
        lambda: sd.validate_elevated_semantic_state(tampered_state),
        "tampered elevated alternative order was accepted",
    )
    print("Elevated-state eligibility, exact alternative closure, and provenance: PASS")

    public_functions = tuple(
        name
        for name, value in vars(validation).items()
        if not name.startswith("_") and inspect.isfunction(value)
    )
    require(
        public_functions
        == (
            "validate_semantic_convergence_resolution",
            "validate_paradox_elevation_assessment",
            "validate_elevated_semantic_state",
        ),
        "unexpected public validation functions: " + repr(public_functions),
    )
    source = (
        ROOT / "apexforge/semantic_decision/validation.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "from runtime",
        "import runtime",
        "from authority",
        "import authority",
        "from governance",
        "import governance",
        "from causality",
        "import causality",
        "from quad_vector",
        "import quad_vector",
        "from aether_air",
        "import aether_air",
        "select_path",
        "resolve_quad_vector_synchronization",
    ):
        require(
            forbidden not in source,
            "forbidden execution/predecessor behavior entered G: " + forbidden,
        )
    print("Passive validation only; no runtime/predecessor execution authority: PASS")

    contract_path = (
        ROOT
        / "docs/p11/P11_10G_VALIDATION_COLLISION_CLOSURE_PROVENANCE_AND_EXTENSION_CONTRACTS.md"
    )
    contract_text = contract_path.read_text(encoding="utf-8")
    for phrase in (
        "G does not flatten the complete B-F graph into one monolithic receipt.",
        "Declaring an extension does not grant executable or operative semantics.",
        "G does not change an ineligible assessment into an eligible assessment.",
        "A zero- or one-member convergence set may therefore validate",
        "P11.10H owns downstream compatibility, reporting, tooling visibility, and traceability",
    ):
        require(phrase in contract_text, "G ownership contract missing: " + phrase)
    print("G layered-receipt, extension, and downstream ownership contract: PASS")

    observed = status_paths()
    require(
        not observed or observed == ALLOWED,
        "unexpected P11.10G artifacts: " + repr(sorted(observed)),
    )
    print("Repository no-op G boundary: PASS")


if __name__ == "__main__":
    main()
