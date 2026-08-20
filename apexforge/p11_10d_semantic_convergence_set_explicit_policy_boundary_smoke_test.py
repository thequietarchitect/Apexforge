"""AFP-P11.10D semantic convergence-set and explicit policy boundary smoke test."""

from __future__ import annotations

import dataclasses
import inspect
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "p11.10d-semantic-convergence-set-explicit-policy-boundary"
PREDECESSOR_TAG = "afp-p11.10c-freeze"
ALLOWED = {
    "apexforge/p11_10d_semantic_convergence_set_explicit_policy_boundary_smoke_test.py",
    "apexforge/semantic_decision/__init__.py",
    "apexforge/semantic_decision/convergence.py",
    "docs/p11/P11_10D_SEMANTIC_CONVERGENCE_SET_AND_EXPLICIT_POLICY_BOUNDARY.md",
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


def main() -> None:
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong P11.10D branch")
    subprocess.run(
        ("git", "merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD"),
        cwd=ROOT,
        check=True,
    )
    print("Frozen P11.10C predecessor and exact branch ancestry: PASS")

    for path in (
        "apexforge/semantic_decision/model.py",
        "apexforge/semantic_decision/evaluation.py",
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
    print("Frozen B/C model-evaluation and predecessor owners preserved: PASS")

    sys.path.insert(0, str(ROOT / "apexforge"))
    import semantic_decision as sd
    import semantic_decision.convergence as conv

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
    )
    require(tuple(sd.__all__) == expected_all, "semantic_decision public surface changed")
    require(
        tuple(conv.__all__)
        == (
            "ConvergencePolicy",
            "EvaluatedCandidate",
            "SemanticConvergenceSet",
            "construct_semantic_convergence_set",
        ),
        "convergence public surface changed",
    )
    print("Exact additive fourteen-symbol semantic_decision public surface: PASS")

    require(
        tuple(field.name for field in dataclasses.fields(sd.ConvergencePolicy))
        == ("identity", "parameters", "provenance"),
        "ConvergencePolicy fields changed",
    )
    require(
        tuple(field.name for field in dataclasses.fields(sd.EvaluatedCandidate))
        == ("candidate", "evaluation"),
        "EvaluatedCandidate fields changed",
    )
    require(
        tuple(field.name for field in dataclasses.fields(sd.SemanticConvergenceSet))
        == ("policy", "candidates", "members", "provenance"),
        "SemanticConvergenceSet fields changed",
    )
    require(
        inspect.signature(sd.construct_semantic_convergence_set)
        == inspect.Signature(
            parameters=(
                inspect.Parameter(
                    "candidates",
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation="Tuple[EvaluatedCandidate, ...]",
                ),
                inspect.Parameter(
                    "policy",
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation="ConvergencePolicy",
                ),
            ),
            return_annotation="SemanticConvergenceSet",
        ),
        "constructor signature changed",
    )
    print("Frozen D record shapes and constructor signature: PASS")

    condition_a = sd.AdvancedCondition(
        "condition:a",
        "semantic.test",
        provenance=("condition:a",),
    )
    condition_b = sd.AdvancedCondition(
        "condition:b",
        "semantic.test",
        provenance=("condition:b",),
    )
    condition_c = sd.AdvancedCondition(
        "condition:c",
        "semantic.test",
        provenance=("condition:c",),
    )
    condition_d = sd.AdvancedCondition(
        "condition:d",
        "semantic.test",
        provenance=("condition:d",),
    )
    evaluations = (
        sd.AdvancedConditionEvaluation(
            condition_a, (), "admissible", ("evaluation:a",)
        ),
        sd.AdvancedConditionEvaluation(
            condition_b, (), "indeterminate", ("evaluation:b",)
        ),
        sd.AdvancedConditionEvaluation(
            condition_c, (), "inadmissible", ("evaluation:c",)
        ),
        sd.AdvancedConditionEvaluation(
            condition_d, (), "admissible", ("evaluation:d",)
        ),
    )
    candidate_objects = tuple(
        sd.CandidateAlternative(
            f"candidate:{letter}",
            payload=(letter,),
            provenance=(f"candidate:{letter}",),
        )
        for letter in ("a", "b", "c", "d")
    )
    bindings = tuple(
        sd.EvaluatedCandidate(candidate, evaluation)
        for candidate, evaluation in zip(candidate_objects, evaluations)
    )
    for index, binding in enumerate(bindings):
        require(binding.candidate is candidate_objects[index], "candidate identity copied")
        require(binding.evaluation is evaluations[index], "evaluation identity copied")
    print("Exact B/C predecessor object identity preserved: PASS")

    policy = sd.ConvergencePolicy(
        "custom.experimental-policy",
        parameters=(("mode", ("trace", 1)),),
        provenance=("policy:explicit",),
    )
    require(policy.identity == "custom.experimental-policy", "policy identity changed")
    require(
        policy.parameters == (("mode", ("trace", 1)),),
        "policy parameters changed",
    )
    open_policy = sd.ConvergencePolicy("another.open.policy")
    require(open_policy.identity == "another.open.policy", "policy taxonomy became closed")
    print("Explicit open passive convergence-policy boundary: PASS")

    result = sd.construct_semantic_convergence_set(bindings, policy=policy)
    require(result.policy is policy, "policy identity copied")
    require(result.candidates is bindings, "candidate tuple identity changed")
    require(
        result.members == (bindings[0], bindings[3]),
        "admissible convergence-member subset changed",
    )
    require(result.members[0] is bindings[0] and result.members[1] is bindings[3], "member identity copied")
    print("Complete candidate trace and admissible-member subset construction: PASS")

    expected_provenance = (
        "policy:explicit",
        "candidate:a",
        "evaluation:a",
        "candidate:b",
        "evaluation:b",
        "candidate:c",
        "evaluation:c",
        "candidate:d",
        "evaluation:d",
    )
    require(result.provenance == expected_provenance, "provenance aggregation changed")
    require(
        tuple(item.candidate.identity for item in result.candidates)
        == ("candidate:a", "candidate:b", "candidate:c", "candidate:d"),
        "candidate encounter order changed",
    )
    print("Encounter order and deterministic provenance preservation: PASS")

    empty = sd.construct_semantic_convergence_set((), policy=policy)
    require(empty.members == (), "zero-member structure rejected or altered")
    one_binding = (bindings[0],)
    one = sd.construct_semantic_convergence_set(one_binding, policy=policy)
    require(one.candidates is one_binding and one.members == one_binding, "one-member structure changed")
    duplicate_bindings = (bindings[0], bindings[0])
    duplicate = sd.construct_semantic_convergence_set(duplicate_bindings, policy=policy)
    require(
        duplicate.members == duplicate_bindings,
        "later-owned duplicate validation entered D",
    )
    print("Later-owned cardinality, collision, and closure validation absent: PASS")

    public_functions = tuple(
        name
        for name, value in vars(conv).items()
        if not name.startswith("_") and inspect.isfunction(value)
    )
    require(
        public_functions == ("construct_semantic_convergence_set",),
        "unexpected public convergence functions: " + repr(public_functions),
    )
    source = (ROOT / "apexforge/semantic_decision/convergence.py").read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "select_path",
        "max_weight",
        "SemanticOutcome(",
        "paradox.elevation_candidate",
        "CandidateAlternative(",
        "evaluate_advanced_condition(",
        "import runtime",
        "from runtime",
        "import authority",
        "from authority",
        "import governance",
        "from governance",
        "import quad_vector",
        "from quad_vector",
        "import aether_air",
        "from aether_air",
    ):
        require(forbidden not in source, "forbidden operative boundary entered D: " + forbidden)
    print("No selection/ranking/composition/runtime/Paradox or causal-policy reuse: PASS")

    contract_path = ROOT / "docs/p11/P11_10D_SEMANTIC_CONVERGENCE_SET_AND_EXPLICIT_POLICY_BOUNDARY.md"
    contract = contract_path.read_text(encoding="utf-8")
    for phrase in (
        "P11.10E owns deterministic convergence selection, composition, and ranking",
        "P11.10F owns Paradox Elevation eligibility",
        "P11.10G owns validation, collision, closure",
        "Encounter order is trace order only. It is never convergence precedence.",
        "A zero-member or one-member `SemanticConvergenceSet` is structurally permitted",
    ):
        require(phrase in contract, "D ownership contract missing: " + phrase)
    print("D ownership and downstream convergence boundary contract: PASS")

    observed = status_paths()
    require(
        not observed or observed == ALLOWED,
        "unexpected P11.10D artifacts: " + repr(sorted(observed)),
    )
    print("Repository no-op D boundary: PASS")


if __name__ == "__main__":
    main()
