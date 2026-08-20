"""AFP-P11.10I final integration, regression, and freeze smoke test."""

from __future__ import annotations

import dataclasses
import inspect
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "p11.10i-final-integration-regression-freeze"
PREDECESSOR_TAG = "afp-p11.10h-freeze"

FREEZE_TAGS = (
    "afp-p11.10a-freeze",
    "afp-p11.10b-freeze",
    "afp-p11.10c-freeze",
    "afp-p11.10d-freeze",
    "afp-p11.10e-freeze",
    "afp-p11.10f-freeze",
    "afp-p11.10g-freeze",
    "afp-p11.10h-freeze",
)

ALLOWED = {
    "apexforge/p11_10i_final_integration_regression_freeze_smoke_test.py",
    "docs/p11/P11_10I_FINAL_INTEGRATION_REGRESSION_AND_FREEZE.md",
}

EXPECTED_PUBLIC_SURFACE = (
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

EXPECTED_FIELDS = {
    "AdvancedCondition": ("identity", "condition_kind", "payload", "provenance"),
    "CandidateAlternative": ("identity", "payload", "provenance"),
    "SemanticOutcome": ("kind_id", "alternatives", "payload", "provenance"),
    "ConditionEvidence": ("condition", "result", "facts", "provenance"),
    "AdvancedConditionEvaluation": ("condition", "evidence", "state_id", "provenance"),
    "ConvergencePolicy": ("identity", "parameters", "provenance"),
    "EvaluatedCandidate": ("candidate", "evaluation"),
    "SemanticConvergenceSet": ("policy", "candidates", "members", "provenance"),
    "RankedCandidate": ("candidate", "rank"),
    "SemanticConvergenceResolution": ("convergence_set", "ranking", "outcome", "provenance"),
    "ParadoxIncompatibilityEvidence": (
        "left",
        "right",
        "materially_incompatible",
        "provenance",
    ),
    "ParadoxElevationEvidence": (
        "resolution",
        "incompatibilities",
        "reduction_requires_information_loss",
        "provenance",
    ),
    "ParadoxElevationAssessment": (
        "evidence",
        "eligible",
        "candidate_outcome",
        "provenance",
    ),
    "ElevatedSemanticState": ("assessment", "alternatives", "provenance"),
    "SemanticDecisionValidationReceipt": (
        "resolution",
        "extension_admissibility_state_ids",
        "extension_outcome_kind_ids",
        "extension_policy_ids",
        "provenance",
        "checks",
    ),
    "ParadoxElevationValidationReceipt": (
        "assessment",
        "resolution_receipt",
        "provenance",
        "checks",
    ),
    "ElevatedSemanticStateValidationReceipt": (
        "state",
        "assessment_receipt",
        "provenance",
        "checks",
    ),
    "SemanticDecisionDownstreamProjection": (
        "validation",
        "consumer",
        "provenance",
    ),
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


def git_exit(*args: str) -> int:
    completed = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode


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


def make_binding(sd, identity: str):
    condition = sd.AdvancedCondition(
        "condition:" + identity,
        "semantic.integration",
        payload=("condition-payload", identity),
        provenance=("condition:" + identity,),
    )
    evidence = (
        sd.ConditionEvidence(
            condition,
            True,
            facts=(("identity", identity),),
            provenance=("evidence:" + identity,),
        ),
    )
    evaluation = sd.evaluate_advanced_condition(
        condition,
        evidence=evidence,
    )
    candidate = sd.CandidateAlternative(
        identity,
        payload=("candidate-payload", identity),
        provenance=("candidate:" + identity,),
    )
    binding = sd.EvaluatedCandidate(candidate, evaluation)
    return condition, evidence, evaluation, candidate, binding


def main() -> None:
    require(
        git("branch", "--show-current") == EXPECTED_BRANCH,
        "wrong P11.10I branch",
    )
    require(
        git_exit("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD") == 0,
        "P11.10I does not descend from frozen P11.10H",
    )
    print("Frozen P11.10H predecessor and exact I branch ancestry: PASS")

    for left, right in zip(FREEZE_TAGS, FREEZE_TAGS[1:]):
        require(
            git_exit("merge-base", "--is-ancestor", left, right) == 0,
            f"broken P11.10 freeze ancestry: {left} -> {right}",
        )
    print("Continuous P11.10A-H freeze-tag ancestry: PASS")

    production_delta = git(
        "diff",
        "--name-only",
        PREDECESSOR_TAG,
        "--",
        "apexforge/semantic_decision",
    )
    require(
        production_delta == "",
        "P11.10I modified frozen semantic_decision production: "
        + repr(production_delta),
    )
    print("Audit-only I boundary with zero semantic_decision production delta: PASS")

    historical_delta = git(
        "diff",
        "--name-only",
        PREDECESSOR_TAG,
        "--",
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
    )
    require(
        historical_delta == "",
        "P11.10I modified historical predecessor/tooling owner: "
        + repr(historical_delta),
    )
    print("Historical predecessor, runtime, and tooling owners preserved: PASS")

    sys.path.insert(0, str(ROOT / "apexforge"))
    import semantic_decision as sd

    require(
        tuple(sd.__all__) == EXPECTED_PUBLIC_SURFACE,
        "integrated P11.10 public surface changed",
    )
    for name, expected in EXPECTED_FIELDS.items():
        observed = tuple(
            field.name for field in dataclasses.fields(getattr(sd, name))
        )
        require(observed == expected, f"{name} field shape changed: {observed!r}")

    require(
        tuple(item.canonical_id for item in sd.CORE_SEMANTIC_OUTCOME_KINDS)
        == (
            "selected",
            "composed",
            "unresolved",
            "paradox.elevation_candidate",
        ),
        "core semantic outcome taxonomy changed",
    )
    require(
        tuple(item.canonical_id for item in sd.CORE_ADMISSIBILITY_STATES)
        == ("admissible", "inadmissible", "indeterminate"),
        "core admissibility taxonomy changed",
    )
    require(
        tuple(sd.CORE_CONVERGENCE_POLICY_IDS)
        == (
            "select.explicit-order",
            "compose.all-admissible",
            "rank.explicit-order",
        ),
        "core convergence policy taxonomy changed",
    )
    print("Exact thirty-three-symbol API, record shapes, and core taxonomies: PASS")

    signatures = {
        "evaluate_advanced_condition": str(
            inspect.signature(sd.evaluate_advanced_condition)
        ),
        "construct_semantic_convergence_set": str(
            inspect.signature(sd.construct_semantic_convergence_set)
        ),
        "apply_semantic_convergence_policy": str(
            inspect.signature(sd.apply_semantic_convergence_policy)
        ),
        "assess_paradox_elevation": str(
            inspect.signature(sd.assess_paradox_elevation)
        ),
        "elevate_paradox_assessment": str(
            inspect.signature(sd.elevate_paradox_assessment)
        ),
        "validate_semantic_convergence_resolution": str(
            inspect.signature(sd.validate_semantic_convergence_resolution)
        ),
        "validate_paradox_elevation_assessment": str(
            inspect.signature(sd.validate_paradox_elevation_assessment)
        ),
        "validate_elevated_semantic_state": str(
            inspect.signature(sd.validate_elevated_semantic_state)
        ),
        "project_validated_semantic_decision": str(
            inspect.signature(sd.project_validated_semantic_decision)
        ),
        "render_semantic_decision_downstream_projection_report": str(
            inspect.signature(
                sd.render_semantic_decision_downstream_projection_report
            )
        ),
    }
    require(
        signatures["evaluate_advanced_condition"]
        == "(condition: 'AdvancedCondition', *, evidence: 'Tuple[ConditionEvidence, ...]' = ()) -> 'AdvancedConditionEvaluation'",
        "C evaluator signature changed",
    )
    require(
        signatures["construct_semantic_convergence_set"]
        == "(candidates: 'Tuple[EvaluatedCandidate, ...]', *, policy: 'ConvergencePolicy') -> 'SemanticConvergenceSet'",
        "D constructor signature changed",
    )
    require(
        signatures["apply_semantic_convergence_policy"]
        == "(convergence_set: 'SemanticConvergenceSet') -> 'SemanticConvergenceResolution'",
        "E resolver signature changed",
    )
    require(
        signatures["assess_paradox_elevation"]
        == "(evidence: 'ParadoxElevationEvidence') -> 'ParadoxElevationAssessment'",
        "F assessor signature changed",
    )
    require(
        signatures["elevate_paradox_assessment"]
        == "(assessment: 'ParadoxElevationAssessment') -> 'ElevatedSemanticState'",
        "F elevation signature changed",
    )
    require(
        signatures["validate_semantic_convergence_resolution"]
        == "(resolution: 'SemanticConvergenceResolution', *, extension_admissibility_state_ids: 'Tuple[str, ...]' = (), extension_outcome_kind_ids: 'Tuple[str, ...]' = (), extension_policy_ids: 'Tuple[str, ...]' = ()) -> 'SemanticDecisionValidationReceipt'",
        "G resolution-validator signature changed",
    )
    require(
        signatures["validate_paradox_elevation_assessment"]
        == "(assessment: 'ParadoxElevationAssessment', *, extension_admissibility_state_ids: 'Tuple[str, ...]' = (), extension_outcome_kind_ids: 'Tuple[str, ...]' = (), extension_policy_ids: 'Tuple[str, ...]' = ()) -> 'ParadoxElevationValidationReceipt'",
        "G assessment-validator signature changed",
    )
    require(
        signatures["validate_elevated_semantic_state"]
        == "(state: 'ElevatedSemanticState', *, extension_admissibility_state_ids: 'Tuple[str, ...]' = (), extension_outcome_kind_ids: 'Tuple[str, ...]' = (), extension_policy_ids: 'Tuple[str, ...]' = ()) -> 'ElevatedSemanticStateValidationReceipt'",
        "G state-validator signature changed",
    )
    require(
        "consumer: 'str'" in signatures["project_validated_semantic_decision"]
        and "provenance: 'Tuple[str, ...]' = ()"
        in signatures["project_validated_semantic_decision"]
        and signatures["project_validated_semantic_decision"].endswith(
            "-> 'SemanticDecisionDownstreamProjection'"
        ),
        "H projection signature changed",
    )
    require(
        signatures["render_semantic_decision_downstream_projection_report"]
        == "(projection: '_SemanticDecisionDownstreamProjection') -> 'str'",
        "H reporter signature changed",
    )
    print("Frozen C-H callable signatures: PASS")

    a_condition, a_evidence, a_eval, a_candidate, a_binding = make_binding(
        sd, "candidate:a"
    )
    b_condition, b_evidence, b_eval, b_candidate, b_binding = make_binding(
        sd, "candidate:b"
    )
    c_condition, c_evidence, c_eval, c_candidate, c_binding = make_binding(
        sd, "candidate:c"
    )

    require(a_evidence[0].condition is a_condition, "C evidence lost condition identity")
    require(a_binding.evaluation is a_eval, "D binding lost evaluation identity")
    require(a_binding.candidate is a_candidate, "D binding lost candidate identity")
    require(
        a_eval.state_id == b_eval.state_id == c_eval.state_id == "admissible",
        "C admissibility integration changed",
    )
    print("B->C exact condition/evidence/candidate identity lineage: PASS")

    policy = sd.ConvergencePolicy(
        "rank.explicit-order",
        parameters=(
            ("order", ("candidate:c", "candidate:a", "candidate:b")),
        ),
        provenance=("policy:integration-rank",),
    )
    convergence_set = sd.construct_semantic_convergence_set(
        (a_binding, b_binding, c_binding),
        policy=policy,
    )
    require(
        convergence_set.candidates
        == (a_binding, b_binding, c_binding)
        and all(
            observed is expected
            for observed, expected in zip(
                convergence_set.candidates,
                (a_binding, b_binding, c_binding),
            )
        ),
        "D candidate lineage changed",
    )
    require(
        all(
            observed is expected
            for observed, expected in zip(
                convergence_set.members,
                (a_binding, b_binding, c_binding),
            )
        ),
        "D admissible member identity/order changed",
    )

    resolution = sd.apply_semantic_convergence_policy(convergence_set)
    require(
        resolution.convergence_set is convergence_set,
        "E resolution copied convergence set",
    )
    require(resolution.outcome.kind_id == "unresolved", "rank policy outcome changed")
    require(
        tuple(item.candidate for item in resolution.ranking)
        == (c_candidate, a_candidate, b_candidate)
        and all(
            observed is expected
            for observed, expected in zip(
                tuple(item.candidate for item in resolution.ranking),
                (c_candidate, a_candidate, b_candidate),
            )
        ),
        "E explicit ranking identity/order changed",
    )
    require(
        all(
            observed is expected
            for observed, expected in zip(
                resolution.outcome.alternatives,
                (a_candidate, b_candidate, c_candidate),
            )
        ),
        "E unresolved alternatives lost D member trace order",
    )
    print("D->E convergence, ranking, and unresolved identity lineage: PASS")

    alternatives = resolution.outcome.alternatives
    incompatibilities = (
        sd.ParadoxIncompatibilityEvidence(
            alternatives[0],
            alternatives[1],
            True,
            provenance=("pair:a:b",),
        ),
        sd.ParadoxIncompatibilityEvidence(
            alternatives[0],
            alternatives[2],
            True,
            provenance=("pair:a:c",),
        ),
        sd.ParadoxIncompatibilityEvidence(
            alternatives[1],
            alternatives[2],
            True,
            provenance=("pair:b:c",),
        ),
    )
    paradox_evidence = sd.ParadoxElevationEvidence(
        resolution,
        incompatibilities,
        True,
        provenance=("paradox:integration",),
    )
    assessment = sd.assess_paradox_elevation(paradox_evidence)
    require(assessment.evidence is paradox_evidence, "F assessment copied evidence")
    require(assessment.eligible is True, "integrated F Paradox eligibility changed")
    require(
        assessment.candidate_outcome is not None
        and assessment.candidate_outcome.kind_id
        == "paradox.elevation_candidate",
        "integrated F candidate outcome changed",
    )
    require(
        all(
            observed is expected
            for observed, expected in zip(
                assessment.candidate_outcome.alternatives,
                alternatives,
            )
        ),
        "F candidate outcome lost E alternative identity",
    )

    state = sd.elevate_paradox_assessment(assessment)
    require(state.assessment is assessment, "F elevated state copied assessment")
    require(
        all(
            observed is expected
            for observed, expected in zip(state.alternatives, alternatives)
        ),
        "F elevated state lost candidate identity",
    )
    print("E->F Paradox eligibility and elevated-state identity lineage: PASS")

    resolution_receipt = sd.validate_semantic_convergence_resolution(resolution)
    assessment_receipt = sd.validate_paradox_elevation_assessment(assessment)
    state_receipt = sd.validate_elevated_semantic_state(state)

    require(
        resolution_receipt.resolution is resolution,
        "G ordinary receipt copied E resolution",
    )
    require(
        assessment_receipt.assessment is assessment,
        "G Paradox receipt copied F assessment",
    )
    require(
        assessment_receipt.resolution_receipt.resolution is resolution,
        "G Paradox receipt lost nested E resolution",
    )
    require(
        state_receipt.state is state,
        "G elevated receipt copied F state",
    )
    require(
        state_receipt.assessment_receipt.assessment is assessment,
        "G elevated receipt lost nested F assessment",
    )
    require(
        state_receipt.assessment_receipt.resolution_receipt.resolution
        is resolution,
        "G elevated receipt lost nested E resolution",
    )
    print("F->G layered validation receipt identity lineage: PASS")

    ordinary_projection = sd.project_validated_semantic_decision(
        resolution_receipt,
        consumer="integration.audit",
        provenance=("projection:ordinary",),
    )
    paradox_projection = sd.project_validated_semantic_decision(
        assessment_receipt,
        consumer="integration.audit",
        provenance=("projection:paradox",),
    )
    elevated_projection = sd.project_validated_semantic_decision(
        state_receipt,
        consumer="integration.audit",
        provenance=("projection:elevated",),
    )

    require(
        ordinary_projection.validation is resolution_receipt,
        "H ordinary projection copied G receipt",
    )
    require(
        paradox_projection.validation is assessment_receipt,
        "H Paradox projection copied G receipt",
    )
    require(
        elevated_projection.validation is state_receipt,
        "H elevated projection copied G receipt",
    )
    print("G->H exact validation-receipt projection lineage: PASS")

    ordinary_report = sd.render_semantic_decision_downstream_projection_report(
        ordinary_projection
    )
    paradox_report = sd.render_semantic_decision_downstream_projection_report(
        paradox_projection
    )
    elevated_report = sd.render_semantic_decision_downstream_projection_report(
        elevated_projection
    )

    for projection, report in (
        (ordinary_projection, ordinary_report),
        (paradox_projection, paradox_report),
        (elevated_projection, elevated_report),
    ):
        require(type(report) is str, "H report is not exact str")
        require(not report.endswith("\n"), "H report gained trailing newline")
        require(
            sd.render_semantic_decision_downstream_projection_report(projection)
            == report,
            "H report is not deterministic",
        )

    require(
        "VALIDATION TYPE\nsemantic-decision-resolution" in ordinary_report
        and "OUTCOME KIND\nunresolved" in ordinary_report,
        "ordinary integrated report lost E/G traceability",
    )
    require(
        "VALIDATION TYPE\nparadox-elevation-assessment" in paradox_report
        and "PARADOX ELIGIBLE\ntrue" in paradox_report
        and "RESOLUTION RECEIPT\nVALIDATION TYPE\nsemantic-decision-resolution"
        in paradox_report,
        "Paradox integrated report lost nested lineage",
    )
    require(
        "VALIDATION TYPE\nelevated-semantic-state" in elevated_report
        and "ASSESSMENT RECEIPT\nVALIDATION TYPE\nparadox-elevation-assessment"
        in elevated_report
        and "RESOLUTION RECEIPT\nVALIDATION TYPE\nsemantic-decision-resolution"
        in elevated_report,
        "elevated integrated report lost nested lineage",
    )
    print("Integrated B->H deterministic semantic traceability report: PASS")

    source_files = (
        "model.py",
        "evaluation.py",
        "convergence.py",
        "resolution.py",
        "paradox.py",
        "validation.py",
        "projection.py",
        "reporting.py",
    )
    semantic_root = ROOT / "apexforge" / "semantic_decision"
    for filename in source_files:
        source = (semantic_root / filename).read_text(encoding="utf-8")
        if filename in ("projection.py", "reporting.py"):
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
            ):
                require(
                    forbidden not in source,
                    f"{filename} gained forbidden predecessor execution import: {forbidden}",
                )
    print("Integrated ownership remains isolated from runtime/governance/Quad-Vector/AETHER execution: PASS")

    expected_smokes = tuple(
        f"apexforge/p11_10{letter}_{suffix}"
        for letter, suffix in (
            ("a", "advanced_conditionals_convergence_paradox_elevation_architecture_audit_smoke_test.py"),
            ("b", "minimal_immutable_advanced_conditional_candidate_outcome_model_smoke_test.py"),
            ("c", "condition_evidence_admissibility_higher_order_evaluation_smoke_test.py"),
            ("d", "semantic_convergence_set_explicit_policy_boundary_smoke_test.py"),
            ("e", "deterministic_convergence_selection_composition_ranking_smoke_test.py"),
            ("f", "paradox_elevation_eligibility_elevated_semantic_state_smoke_test.py"),
            ("g", "validation_collision_closure_provenance_extension_smoke_test.py"),
            ("h", "downstream_compatibility_reporting_tooling_traceability_smoke_test.py"),
        )
    )
    for path in expected_smokes:
        require((ROOT / path).is_file(), "missing frozen slice smoke: " + path)

    expected_docs = (
        "docs/p11/P11_10A_ADVANCED_CONDITIONALS_CONVERGENCE_AND_PARADOX_ELEVATION_ARCHITECTURE_AUDIT.md",
        "docs/p11/P11_10B_MINIMAL_IMMUTABLE_ADVANCED_CONDITIONAL_CANDIDATE_ALTERNATIVE_AND_OUTCOME_MODEL.md",
        "docs/p11/P11_10C_CANONICAL_CONDITION_EVIDENCE_ADMISSIBILITY_AND_HIGHER_ORDER_EVALUATION.md",
        "docs/p11/P11_10D_SEMANTIC_CONVERGENCE_SET_AND_EXPLICIT_POLICY_BOUNDARY.md",
        "docs/p11/P11_10E_DETERMINISTIC_CONVERGENCE_SELECTION_COMPOSITION_AND_RANKING.md",
        "docs/p11/P11_10F_PARADOX_ELEVATION_ELIGIBILITY_AND_ELEVATED_SEMANTIC_STATE.md",
        "docs/p11/P11_10G_VALIDATION_COLLISION_CLOSURE_PROVENANCE_AND_EXTENSION_CONTRACTS.md",
        "docs/p11/P11_10H_DOWNSTREAM_COMPATIBILITY_REPORTING_TOOLING_VISIBILITY_AND_TRACEABILITY.md",
    )
    for path in expected_docs:
        require((ROOT / path).is_file(), "missing frozen slice contract: " + path)
    print("Complete P11.10A-H smoke/contract artifact chain: PASS")

    contract_path = (
        ROOT
        / "docs/p11/P11_10I_FINAL_INTEGRATION_REGRESSION_AND_FREEZE.md"
    )
    contract = contract_path.read_text(encoding="utf-8")
    for phrase in (
        "P11.10I is audit-only.",
        "P11.10I adds no semantic-decision production behavior.",
        "The complete frozen A-H ancestry chain must remain continuous.",
        "B -> C -> D -> E -> F -> G -> H",
        "P11.10 is complete only after this I gate freezes.",
    ):
        require(phrase in contract, "I freeze contract missing: " + phrase)
    print("Final P11.10I audit-only and completion contract: PASS")

    observed = status_paths()
    require(
        not observed or observed == ALLOWED,
        "unexpected P11.10I artifacts: " + repr(sorted(observed)),
    )
    print("Repository no-op I boundary: PASS")


if __name__ == "__main__":
    main()
