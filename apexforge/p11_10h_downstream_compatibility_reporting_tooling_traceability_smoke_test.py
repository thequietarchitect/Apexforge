"""AFP-P11.10H downstream compatibility, reporting, and traceability smoke test."""

from __future__ import annotations

import dataclasses
import inspect
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "p11.10h-downstream-compatibility-reporting-tooling-traceability"
PREDECESSOR_TAG = "afp-p11.10g-freeze"
ALLOWED = {
    "apexforge/p11_10h_downstream_compatibility_reporting_tooling_traceability_smoke_test.py",
    "apexforge/semantic_decision/__init__.py",
    "apexforge/semantic_decision/projection.py",
    "apexforge/semantic_decision/reporting.py",
    "docs/p11/P11_10H_DOWNSTREAM_COMPATIBILITY_REPORTING_TOOLING_VISIBILITY_AND_TRACEABILITY.md",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_type_error(callable_object, message: str) -> None:
    try:
        callable_object()
    except TypeError:
        return
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


def status_paths() -> set:
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
    evidence = (
        sd.ConditionEvidence(
            condition,
            True,
            facts=(("fact", identity),),
            provenance=("evidence:" + identity,),
        ),
    )
    evaluation = sd.evaluate_advanced_condition(condition, evidence=evidence)
    candidate = sd.CandidateAlternative(
        identity,
        payload=("payload", identity),
        provenance=("candidate:" + identity,),
    )
    return sd.EvaluatedCandidate(candidate, evaluation)


def fixture(sd):
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
    convergence_set = sd.construct_semantic_convergence_set(
        (a, b, c),
        policy=policy,
    )
    resolution = sd.apply_semantic_convergence_policy(convergence_set)
    resolution_receipt = sd.validate_semantic_convergence_resolution(resolution)

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
    paradox_evidence = sd.ParadoxElevationEvidence(
        resolution,
        tuple(pairs),
        True,
        provenance=("paradox:evidence",),
    )
    assessment = sd.assess_paradox_elevation(paradox_evidence)
    assessment_receipt = sd.validate_paradox_elevation_assessment(assessment)
    state = sd.elevate_paradox_assessment(assessment)
    state_receipt = sd.validate_elevated_semantic_state(state)
    return resolution_receipt, assessment_receipt, state_receipt


def main() -> None:
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong P11.10H branch")
    subprocess.run(
        ("git", "merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD"),
        cwd=ROOT,
        check=True,
    )
    print("Frozen P11.10G predecessor and exact branch ancestry: PASS")

    for path in (
        "apexforge/semantic_decision/model.py",
        "apexforge/semantic_decision/evaluation.py",
        "apexforge/semantic_decision/convergence.py",
        "apexforge/semantic_decision/resolution.py",
        "apexforge/semantic_decision/paradox.py",
        "apexforge/semantic_decision/validation.py",
        "apexforge/aether_air",
        "apexforge/air",
        "apexforge/language",
        "apexforge/runtime",
        "apexforge/quad_vector",
        "apexforge/semantic_lattice",
        "apexforge/authority",
        "apexforge/governance",
        "apexforge/causality",
        "apexforge/tooling",
        "apexforge/tools",
    ):
        require(unchanged(path), "frozen predecessor owner changed: " + path)
    print("Frozen B-G semantic-decision and historical tooling owners preserved: PASS")

    sys.path.insert(0, str(ROOT / "apexforge"))
    import semantic_decision as sd
    import semantic_decision.projection as projection
    import semantic_decision.reporting as reporting

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
        "SemanticDecisionDownstreamProjection",
        "project_validated_semantic_decision",
        "render_semantic_decision_downstream_projection_report",
    )
    require(tuple(sd.__all__) == expected_all, "semantic_decision public surface changed")
    require(
        tuple(projection.__all__)
        == (
            "SemanticDecisionDownstreamProjection",
            "project_validated_semantic_decision",
        ),
        "projection public surface changed",
    )
    require(
        tuple(reporting.__all__)
        == ("render_semantic_decision_downstream_projection_report",),
        "reporting public surface changed",
    )
    print("Exact additive thirty-three-symbol semantic_decision public surface: PASS")

    require(
        tuple(
            field.name
            for field in dataclasses.fields(sd.SemanticDecisionDownstreamProjection)
        )
        == ("validation", "consumer", "provenance"),
        "SemanticDecisionDownstreamProjection fields changed",
    )
    require(
        "consumer: 'str'" in str(inspect.signature(sd.project_validated_semantic_decision))
        and "provenance: 'Tuple[str, ...]' = ()"
        in str(inspect.signature(sd.project_validated_semantic_decision))
        and str(inspect.signature(sd.project_validated_semantic_decision)).endswith(
            "-> 'SemanticDecisionDownstreamProjection'"
        ),
        "projection function signature changed",
    )
    require(
        str(inspect.signature(sd.render_semantic_decision_downstream_projection_report))
        == "(projection: '_SemanticDecisionDownstreamProjection') -> 'str'",
        "reporter signature changed",
    )
    print("Frozen H projection shape and projection/report signatures: PASS")

    resolution_receipt, assessment_receipt, state_receipt = fixture(sd)

    projections = tuple(
        sd.project_validated_semantic_decision(
            receipt,
            consumer="tooling.semantic-decision",
            provenance=("projection:trace",),
        )
        for receipt in (
            resolution_receipt,
            assessment_receipt,
            state_receipt,
        )
    )
    for receipt, observed in zip(
        (resolution_receipt, assessment_receipt, state_receipt),
        projections,
    ):
        require(observed.validation is receipt, "projection copied validation receipt")
        require(
            observed.consumer == "tooling.semantic-decision",
            "projection consumer changed",
        )
        require(
            observed.provenance == ("projection:trace",),
            "projection provenance changed",
        )
    print("One exact projection preserves all three G receipt families: PASS")

    changed_consumer = sd.project_validated_semantic_decision(
        resolution_receipt,
        consumer="diagnostics.semantic-decision",
        provenance=("projection:trace",),
    )
    require(
        changed_consumer.validation is resolution_receipt,
        "consumer change altered semantic receipt identity",
    )
    require(
        changed_consumer.consumer != projections[0].consumer,
        "consumer fixture did not change",
    )
    print("Consumer and projection provenance remain observational metadata: PASS")

    for invalid in (
        object(),
        resolution_receipt.resolution,
        assessment_receipt.assessment,
        state_receipt.state,
    ):
        require_type_error(
            lambda invalid=invalid: sd.project_validated_semantic_decision(
                invalid,
                consumer="tooling.semantic-decision",
            ),
            "projection accepted a non-G-receipt object",
        )
    print("Explicit G-receipt-only downstream projection boundary: PASS")

    reports = tuple(
        sd.render_semantic_decision_downstream_projection_report(item)
        for item in projections
    )
    for report in reports:
        require(type(report) is str, "report is not an exact str")
        require(not report.endswith("\n"), "report gained a trailing newline")
        require(
            report.startswith(
                "APEXFORGE SEMANTIC DECISION DOWNSTREAM PROJECTION REPORT\n"
            ),
            "report heading changed",
        )
        require(
            report.endswith("END SEMANTIC DECISION DOWNSTREAM PROJECTION REPORT"),
            "report end marker changed",
        )
        require(
            sd.render_semantic_decision_downstream_projection_report(
                projections[reports.index(report)]
            )
            == report,
            "report is not deterministic",
        )
    require(
        "VALIDATION TYPE\nsemantic-decision-resolution" in reports[0]
        and "POLICY\nrank.explicit-order" in reports[0]
        and "OUTCOME KIND\nunresolved" in reports[0]
        and "VALIDATION CHECKS" in reports[0],
        "ordinary semantic-decision traceability report changed",
    )
    require(
        "VALIDATION TYPE\nparadox-elevation-assessment" in reports[1]
        and "PARADOX ELIGIBLE\ntrue" in reports[1]
        and "REDUCTION REQUIRES INFORMATION LOSS\ntrue" in reports[1]
        and "INCOMPATIBILITY EVIDENCE" in reports[1]
        and "RESOLUTION RECEIPT\nVALIDATION TYPE\nsemantic-decision-resolution"
        in reports[1],
        "Paradox nested-receipt traceability report changed",
    )
    require(
        "VALIDATION TYPE\nelevated-semantic-state" in reports[2]
        and "ELEVATED ALTERNATIVES" in reports[2]
        and "ASSESSMENT RECEIPT\nVALIDATION TYPE\nparadox-elevation-assessment"
        in reports[2]
        and "RESOLUTION RECEIPT\nVALIDATION TYPE\nsemantic-decision-resolution"
        in reports[2],
        "elevated nested-receipt traceability report changed",
    )
    print("Deterministic ordinary, Paradox, and elevated traceability reports: PASS")

    require_type_error(
        lambda: sd.render_semantic_decision_downstream_projection_report(
            resolution_receipt
        ),
        "reporter accepted a raw G receipt",
    )
    require_type_error(
        lambda: sd.render_semantic_decision_downstream_projection_report(object()),
        "reporter accepted an arbitrary object",
    )
    print("Reporter requires explicit H projection boundary: PASS")

    projection_functions = tuple(
        name
        for name, value in vars(projection).items()
        if not name.startswith("_") and inspect.isfunction(value)
    )
    projection_classes = tuple(
        name
        for name, value in vars(projection).items()
        if not name.startswith("_") and inspect.isclass(value)
    )
    reporting_functions = tuple(
        name
        for name, value in vars(reporting).items()
        if not name.startswith("_") and inspect.isfunction(value)
    )
    require(
        projection_functions == ("project_validated_semantic_decision",),
        "unexpected public projection functions: " + repr(projection_functions),
    )
    require(
        projection_classes == ("SemanticDecisionDownstreamProjection",),
        "unexpected public projection classes: " + repr(projection_classes),
    )
    require(
        reporting_functions
        == ("render_semantic_decision_downstream_projection_report",),
        "unexpected public reporting functions: " + repr(reporting_functions),
    )

    reporting_source = (
        ROOT / "apexforge/semantic_decision/reporting.py"
    ).read_text(encoding="utf-8")
    projection_source = (
        ROOT / "apexforge/semantic_decision/projection.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "validate_semantic_convergence_resolution",
        "validate_paradox_elevation_assessment",
        "validate_elevated_semantic_state",
        "evaluate_advanced_condition",
        "construct_semantic_convergence_set",
        "apply_semantic_convergence_policy",
        "assess_paradox_elevation",
        "elevate_paradox_assessment",
        "project_validated_semantic_decision",
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
    ):
        require(
            forbidden not in reporting_source,
            "reporting acquired semantic/revalidation behavior: " + forbidden,
        )
    for forbidden in (
        "validate_semantic_convergence_resolution",
        "validate_paradox_elevation_assessment",
        "validate_elevated_semantic_state",
        "evaluate_advanced_condition",
        "construct_semantic_convergence_set",
        "apply_semantic_convergence_policy",
        "assess_paradox_elevation",
        "elevate_paradox_assessment",
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
    ):
        require(
            forbidden not in projection_source,
            "projection acquired semantic/revalidation behavior: " + forbidden,
        )
    print("Pure projection/reporting with no B-G revalidation or semantic execution: PASS")

    contract_path = (
        ROOT
        / "docs/p11/P11_10H_DOWNSTREAM_COMPATIBILITY_REPORTING_TOOLING_VISIBILITY_AND_TRACEABILITY.md"
    )
    contract_text = contract_path.read_text(encoding="utf-8")
    for phrase in (
        "H does not flatten G's layered receipt graph.",
        "A consumer label does not:",
        "Reporting consumes the already-created H projection.",
        "Tooling visibility is observational availability, not automatic integration",
        "P11.10I owns final integration, regression, and freeze.",
    ):
        require(phrase in contract_text, "H ownership contract missing: " + phrase)
    print("H downstream, tooling-visibility, and final-integration boundary contract: PASS")

    observed = status_paths()
    require(
        not observed or observed == ALLOWED,
        "unexpected P11.10H artifacts: " + repr(sorted(observed)),
    )
    print("Repository no-op H boundary: PASS")


if __name__ == "__main__":
    main()
