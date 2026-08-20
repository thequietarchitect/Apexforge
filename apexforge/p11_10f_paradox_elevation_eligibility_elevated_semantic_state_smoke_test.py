"""AFP-P11.10F Paradox Elevation eligibility smoke test."""

from __future__ import annotations

import dataclasses
import inspect
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "p11.10f-paradox-elevation-eligibility-elevated-semantic-state"
PREDECESSOR_TAG = "afp-p11.10e-freeze"
ALLOWED = {
    "apexforge/p11_10f_paradox_elevation_eligibility_elevated_semantic_state_smoke_test.py",
    "apexforge/semantic_decision/__init__.py",
    "apexforge/semantic_decision/paradox.py",
    "docs/p11/P11_10F_PARADOX_ELEVATION_ELIGIBILITY_AND_ELEVATED_SEMANTIC_STATE.md",
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


def make_binding(sd, identity: str):
    condition = sd.AdvancedCondition(
        "condition:" + identity,
        "semantic.test",
        provenance=("condition:" + identity,),
    )
    evaluation = sd.AdvancedConditionEvaluation(
        condition=condition,
        evidence=(),
        state_id="admissible",
        provenance=("evaluation:" + identity,),
    )
    candidate = sd.CandidateAlternative(
        identity,
        payload=("payload", identity),
        provenance=("candidate:" + identity,),
    )
    return sd.EvaluatedCandidate(candidate, evaluation)


def ranked_resolution(sd, bindings):
    order = tuple(item.candidate.identity for item in reversed(bindings))
    policy = sd.ConvergencePolicy(
        "rank.explicit-order",
        parameters=(("order", order),),
        provenance=("policy:rank",),
    )
    convergence_set = sd.construct_semantic_convergence_set(
        bindings,
        policy=policy,
    )
    return sd.apply_semantic_convergence_policy(convergence_set)


def incompatibilities(sd, alternatives):
    result = []
    for left_index in range(len(alternatives)):
        for right_index in range(left_index + 1, len(alternatives)):
            left = alternatives[left_index]
            right = alternatives[right_index]
            result.append(
                sd.ParadoxIncompatibilityEvidence(
                    left,
                    right,
                    True,
                    provenance=(
                        "incompatible:"
                        + left.identity
                        + ":"
                        + right.identity,
                    ),
                )
            )
    return tuple(result)


def main() -> None:
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong P11.10F branch")
    subprocess.run(
        ("git", "merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD"),
        cwd=ROOT,
        check=True,
    )
    print("Frozen P11.10E predecessor and exact branch ancestry: PASS")

    for path in (
        "apexforge/semantic_decision/model.py",
        "apexforge/semantic_decision/evaluation.py",
        "apexforge/semantic_decision/convergence.py",
        "apexforge/semantic_decision/resolution.py",
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
    print("Frozen B/C/D/E semantic-decision and predecessor owners preserved: PASS")

    sys.path.insert(0, str(ROOT / "apexforge"))
    import semantic_decision as sd
    import semantic_decision.paradox as paradox

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
    )
    require(tuple(sd.__all__) == expected_all, "semantic_decision public surface changed")
    require(
        tuple(paradox.__all__)
        == (
            "ParadoxIncompatibilityEvidence",
            "ParadoxElevationEvidence",
            "ParadoxElevationAssessment",
            "ElevatedSemanticState",
            "assess_paradox_elevation",
            "elevate_paradox_assessment",
        ),
        "paradox public surface changed",
    )
    print("Exact additive twenty-four-symbol semantic_decision public surface: PASS")

    require(
        tuple(
            field.name
            for field in dataclasses.fields(sd.ParadoxIncompatibilityEvidence)
        )
        == ("left", "right", "materially_incompatible", "provenance"),
        "ParadoxIncompatibilityEvidence fields changed",
    )
    require(
        tuple(field.name for field in dataclasses.fields(sd.ParadoxElevationEvidence))
        == (
            "resolution",
            "incompatibilities",
            "reduction_requires_information_loss",
            "provenance",
        ),
        "ParadoxElevationEvidence fields changed",
    )
    require(
        tuple(
            field.name
            for field in dataclasses.fields(sd.ParadoxElevationAssessment)
        )
        == ("evidence", "eligible", "candidate_outcome", "provenance"),
        "ParadoxElevationAssessment fields changed",
    )
    require(
        tuple(field.name for field in dataclasses.fields(sd.ElevatedSemanticState))
        == ("assessment", "alternatives", "provenance"),
        "ElevatedSemanticState fields changed",
    )
    require(
        str(inspect.signature(sd.assess_paradox_elevation))
        == "(evidence: 'ParadoxElevationEvidence') -> 'ParadoxElevationAssessment'",
        "assessment signature changed",
    )
    require(
        str(inspect.signature(sd.elevate_paradox_assessment))
        == "(assessment: 'ParadoxElevationAssessment') -> 'ElevatedSemanticState'",
        "elevation signature changed",
    )
    print("Frozen F record shapes and function signatures: PASS")

    a = make_binding(sd, "candidate:a")
    b = make_binding(sd, "candidate:b")
    c = make_binding(sd, "candidate:c")
    resolution = ranked_resolution(sd, (a, b, c))
    require(
        resolution.outcome.kind_id == "unresolved"
        and len(resolution.ranking) == 3,
        "fixture is not a successful unresolved ranked E resolution",
    )

    alternatives = resolution.outcome.alternatives
    pair_evidence = incompatibilities(sd, alternatives)
    evidence = sd.ParadoxElevationEvidence(
        resolution=resolution,
        incompatibilities=pair_evidence,
        reduction_requires_information_loss=True,
        provenance=("paradox:evidence",),
    )
    assessment = sd.assess_paradox_elevation(evidence)
    require(assessment.evidence is evidence, "assessment copied evidence")
    require(assessment.eligible is True, "complete paradox evidence was not eligible")
    require(
        type(assessment.candidate_outcome) is sd.SemanticOutcome
        and assessment.candidate_outcome.kind_id == "paradox.elevation_candidate",
        "eligible assessment did not create elevation-candidate outcome",
    )
    require(
        assessment.candidate_outcome.alternatives == alternatives
        and all(
            observed is expected
            for observed, expected in zip(
                assessment.candidate_outcome.alternatives,
                alternatives,
            )
        ),
        "eligible assessment copied or reordered candidates",
    )
    print("Complete explicit incompatibility plus information-loss eligibility: PASS")

    expected_provenance = (
        resolution.provenance
        + ("paradox:evidence",)
        + tuple(
            item
            for pair in pair_evidence
            for item in pair.provenance
        )
    )
    require(
        assessment.provenance == expected_provenance,
        "assessment provenance aggregation changed",
    )
    require(
        assessment.candidate_outcome.provenance == expected_provenance,
        "candidate-outcome provenance changed",
    )
    print("Exact E lineage and deterministic F provenance preservation: PASS")

    elevated = sd.elevate_paradox_assessment(assessment)
    require(elevated.assessment is assessment, "elevated state copied assessment")
    require(
        elevated.alternatives == alternatives
        and all(
            observed is expected
            for observed, expected in zip(elevated.alternatives, alternatives)
        ),
        "elevated state copied or reordered alternatives",
    )
    require(elevated.provenance == assessment.provenance, "elevated provenance changed")
    print("Immutable elevated semantic state preserves participating alternatives: PASS")

    missing = sd.ParadoxElevationEvidence(
        resolution,
        pair_evidence[:-1],
        True,
    )
    duplicate = sd.ParadoxElevationEvidence(
        resolution,
        pair_evidence + (pair_evidence[0],),
        True,
    )
    compatible_pair = sd.ParadoxElevationEvidence(
        resolution,
        (
            sd.ParadoxIncompatibilityEvidence(
                pair_evidence[0].left,
                pair_evidence[0].right,
                False,
            ),
        )
        + pair_evidence[1:],
        True,
    )
    no_loss = sd.ParadoxElevationEvidence(
        resolution,
        pair_evidence,
        False,
    )
    outside = make_binding(sd, "candidate:outside")
    outside_pair = sd.ParadoxElevationEvidence(
        resolution,
        pair_evidence[:-1]
        + (
            sd.ParadoxIncompatibilityEvidence(
                alternatives[1],
                outside.candidate,
                True,
            ),
        ),
        True,
    )
    for observed_evidence in (
        missing,
        duplicate,
        compatible_pair,
        no_loss,
        outside_pair,
    ):
        observed = sd.assess_paradox_elevation(observed_evidence)
        require(observed.eligible is False, "insufficient/invalid evidence became eligible")
        require(
            observed.candidate_outcome is None,
            "ineligible evidence created paradox.elevation_candidate",
        )
    print("Incomplete, duplicate, compatible, outside, and no-loss evidence remain ineligible: PASS")

    malformed_select_policy = sd.ConvergencePolicy(
        "select.explicit-order",
        parameters=(("order", ("candidate:a", "candidate:b")),),
    )
    malformed_set = sd.construct_semantic_convergence_set(
        (a, b, c),
        policy=malformed_select_policy,
    )
    malformed_resolution = sd.apply_semantic_convergence_policy(malformed_set)
    require(malformed_resolution.outcome.kind_id == "unresolved", "malformed E fixture changed")
    malformed_evidence = sd.ParadoxElevationEvidence(
        malformed_resolution,
        incompatibilities(sd, malformed_resolution.outcome.alternatives),
        True,
    )
    require(
        sd.assess_paradox_elevation(malformed_evidence).eligible is False,
        "malformed E unresolved fallback became Paradox Elevation",
    )

    unsupported_policy = sd.ConvergencePolicy("experimental.weighted")
    unsupported_set = sd.construct_semantic_convergence_set(
        (a, b, c),
        policy=unsupported_policy,
    )
    unsupported_resolution = sd.apply_semantic_convergence_policy(unsupported_set)
    unsupported_evidence = sd.ParadoxElevationEvidence(
        unsupported_resolution,
        incompatibilities(sd, unsupported_resolution.outcome.alternatives),
        True,
    )
    require(
        sd.assess_paradox_elevation(unsupported_evidence).eligible is False,
        "unsupported E unresolved fallback became Paradox Elevation",
    )
    print("Ordinary E unresolved fallback is not automatically Paradox Elevation: PASS")

    select_policy = sd.ConvergencePolicy(
        "select.explicit-order",
        parameters=(
            ("order", ("candidate:c", "candidate:b", "candidate:a")),
        ),
    )
    selected_set = sd.construct_semantic_convergence_set((a, b, c), policy=select_policy)
    selected_resolution = sd.apply_semantic_convergence_policy(selected_set)
    selected_evidence = sd.ParadoxElevationEvidence(
        selected_resolution,
        incompatibilities(sd, selected_resolution.outcome.alternatives),
        True,
    )
    require(
        sd.assess_paradox_elevation(selected_evidence).eligible is False,
        "selected ordinary convergence became Paradox Elevation",
    )
    print("Selected/composed ordinary convergence cannot enter elevation eligibility: PASS")

    ineligible_assessment = sd.assess_paradox_elevation(no_loss)
    try:
        sd.elevate_paradox_assessment(ineligible_assessment)
    except ValueError:
        pass
    else:
        raise AssertionError("ineligible assessment constructed elevated semantic state")
    print("Elevated-state construction requires positive eligibility: PASS")

    manually_labeled = sd.SemanticOutcome(
        "paradox.elevation_candidate",
        alternatives=alternatives,
    )
    require(
        manually_labeled.kind_id == "paradox.elevation_candidate",
        "B manual outcome fixture changed",
    )
    require(
        assessment.candidate_outcome is not manually_labeled,
        "manual B outcome unexpectedly became F eligibility proof",
    )
    print("Manual B paradox.elevation_candidate remains non-authoritative: PASS")

    source = (ROOT / "apexforge/semantic_decision/paradox.py").read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "from governance",
        "import governance",
        "classify_conflict",
        "PolicyConflict",
        "max_weight",
        "priority",
        "from runtime",
        "import runtime",
        "from authority",
        "import authority",
        "from quad_vector",
        "import quad_vector",
        "from aether_air",
        "import aether_air",
        ".payload",
    ):
        require(
            forbidden not in source,
            "forbidden inference/predecessor behavior entered F: " + forbidden,
        )
    public_functions = tuple(
        name
        for name, value in vars(paradox).items()
        if not name.startswith("_") and inspect.isfunction(value)
    )
    require(
        public_functions
        == ("assess_paradox_elevation", "elevate_paradox_assessment"),
        "unexpected public paradox functions: " + repr(public_functions),
    )
    print("No payload inference, governance reuse, runtime behavior, or hidden precedence: PASS")

    contract_path = (
        ROOT
        / "docs/p11/P11_10F_PARADOX_ELEVATION_ELIGIBILITY_AND_ELEVATED_SEMANTIC_STATE.md"
    )
    contract_text = contract_path.read_text(encoding="utf-8")
    for phrase in (
        "An E outcome being `unresolved` is necessary but not sufficient",
        "F does not silently elevate a paradoxical subset.",
        "P11.10G owns validation, collision, closure",
        "Paradox Elevation is not ordinary branch selection",
        "candidate payloads that appear contradictory",
    ):
        require(phrase in contract_text, "F ownership contract missing: " + phrase)
    print("F ownership and downstream validation boundary contract: PASS")

    observed = status_paths()
    require(
        not observed or observed == ALLOWED,
        "unexpected P11.10F artifacts: " + repr(sorted(observed)),
    )
    print("Repository no-op F boundary: PASS")


if __name__ == "__main__":
    main()
