"""AFP-P11.10E deterministic convergence policy smoke test."""

from __future__ import annotations

import dataclasses
import inspect
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "p11.10e-deterministic-convergence-selection-composition-ranking"
PREDECESSOR_TAG = "afp-p11.10d-freeze"
ALLOWED = {
    "apexforge/p11_10e_deterministic_convergence_selection_composition_ranking_smoke_test.py",
    "apexforge/semantic_decision/__init__.py",
    "apexforge/semantic_decision/resolution.py",
    "docs/p11/P11_10E_DETERMINISTIC_CONVERGENCE_SELECTION_COMPOSITION_AND_RANKING.md",
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


def main() -> None:
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong P11.10E branch")
    subprocess.run(
        ("git", "merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD"),
        cwd=ROOT,
        check=True,
    )
    print("Frozen P11.10D predecessor and exact branch ancestry: PASS")

    for path in (
        "apexforge/semantic_decision/model.py",
        "apexforge/semantic_decision/evaluation.py",
        "apexforge/semantic_decision/convergence.py",
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
    print("Frozen B/C/D semantic-decision and predecessor owners preserved: PASS")

    sys.path.insert(0, str(ROOT / "apexforge"))
    import semantic_decision as sd
    import semantic_decision.resolution as resolution

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
    )
    require(tuple(sd.__all__) == expected_all, "semantic_decision public surface changed")
    require(
        tuple(resolution.__all__)
        == (
            "CORE_CONVERGENCE_POLICY_IDS",
            "RankedCandidate",
            "SemanticConvergenceResolution",
            "apply_semantic_convergence_policy",
        ),
        "resolution public surface changed",
    )
    print("Exact additive eighteen-symbol semantic_decision public surface: PASS")

    require(
        sd.CORE_CONVERGENCE_POLICY_IDS
        == (
            "select.explicit-order",
            "compose.all-admissible",
            "rank.explicit-order",
        ),
        "core convergence policy identifiers changed",
    )
    require(
        tuple(field.name for field in dataclasses.fields(sd.RankedCandidate))
        == ("candidate", "rank"),
        "RankedCandidate fields changed",
    )
    require(
        tuple(
            field.name
            for field in dataclasses.fields(sd.SemanticConvergenceResolution)
        )
        == ("convergence_set", "ranking", "outcome", "provenance"),
        "SemanticConvergenceResolution fields changed",
    )
    require(
        inspect.signature(sd.apply_semantic_convergence_policy)
        == inspect.Signature(
            parameters=(
                inspect.Parameter(
                    "convergence_set",
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation="SemanticConvergenceSet",
                ),
            ),
            return_annotation="SemanticConvergenceResolution",
        ),
        "policy application signature changed",
    )
    print("Exact three-policy vocabulary, E record shapes, and function signature: PASS")

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
    first_set = sd.construct_semantic_convergence_set(
        (a, b, c),
        policy=select_policy,
    )
    second_set = sd.construct_semantic_convergence_set(
        (b, c, a),
        policy=select_policy,
    )
    first = sd.apply_semantic_convergence_policy(first_set)
    second = sd.apply_semantic_convergence_policy(second_set)
    require(first.convergence_set is first_set, "convergence-set identity copied")
    require(second.convergence_set is second_set, "reordered convergence-set identity copied")
    require(
        tuple(item.candidate.identity for item in first.ranking)
        == ("candidate:c", "candidate:a", "candidate:b"),
        "explicit selection ranking changed",
    )
    require(
        tuple(item.rank for item in first.ranking) == (1, 2, 3),
        "selection ranks changed",
    )
    require(
        first.outcome.kind_id == "selected"
        and first.outcome.alternatives == (c.candidate,)
        and first.outcome.alternatives[0] is c.candidate,
        "explicit selection outcome changed",
    )
    require(
        tuple(item.candidate.identity for item in second.ranking)
        == ("candidate:c", "candidate:a", "candidate:b")
        and second.outcome.alternatives[0] is c.candidate,
        "D encounter order became selection precedence",
    )
    print("Deterministic explicit-order selection independent of D encounter order: PASS")

    compose_policy = sd.ConvergencePolicy(
        "compose.all-admissible",
        provenance=("policy:compose",),
    )
    compose_set = sd.construct_semantic_convergence_set(
        (b, a, c),
        policy=compose_policy,
    )
    composed = sd.apply_semantic_convergence_policy(compose_set)
    require(composed.ranking == (), "composition acquired ranking")
    require(composed.outcome.kind_id == "composed", "composition outcome kind changed")
    require(
        composed.outcome.alternatives
        == (b.candidate, a.candidate, c.candidate),
        "composition did not preserve D member order",
    )
    require(
        all(
            observed is expected
            for observed, expected in zip(
                composed.outcome.alternatives,
                (b.candidate, a.candidate, c.candidate),
            )
        ),
        "composition copied canonical candidates",
    )
    print("All-admissible composition without implicit ranking: PASS")

    rank_policy = sd.ConvergencePolicy(
        "rank.explicit-order",
        parameters=(
            ("order", ("candidate:b", "candidate:c", "candidate:a")),
        ),
        provenance=("policy:rank",),
    )
    rank_set = sd.construct_semantic_convergence_set(
        (a, c, b),
        policy=rank_policy,
    )
    ranked = sd.apply_semantic_convergence_policy(rank_set)
    require(
        tuple(item.candidate.identity for item in ranked.ranking)
        == ("candidate:b", "candidate:c", "candidate:a"),
        "explicit ranking changed",
    )
    require(
        ranked.outcome.kind_id == "unresolved",
        "ranking silently selected or composed an outcome",
    )
    require(
        ranked.outcome.alternatives == (a.candidate, c.candidate, b.candidate),
        "ranking changed unresolved trace order",
    )
    print("Explicit-order ranking without silent winner selection: PASS")

    malformed_policies = (
        sd.ConvergencePolicy("select.explicit-order"),
        sd.ConvergencePolicy(
            "select.explicit-order",
            parameters=(("order", ("candidate:a", "candidate:b")),),
        ),
        sd.ConvergencePolicy(
            "select.explicit-order",
            parameters=(
                ("order", ("candidate:a", "candidate:a", "candidate:c")),
            ),
        ),
        sd.ConvergencePolicy(
            "select.explicit-order",
            parameters=(
                ("order", ("candidate:a", "candidate:b", "candidate:x")),
            ),
        ),
        sd.ConvergencePolicy(
            "compose.all-admissible",
            parameters=(("unexpected", True),),
        ),
        sd.ConvergencePolicy("experimental.weighted"),
    )
    for policy in malformed_policies:
        convergence_set = sd.construct_semantic_convergence_set(
            (a, b, c),
            policy=policy,
        )
        observed = sd.apply_semantic_convergence_policy(convergence_set)
        require(observed.ranking == (), "unsupported/malformed policy created ranking")
        require(
            observed.outcome.kind_id == "unresolved",
            "unsupported/malformed policy created ordinary convergence result",
        )
        require(
            observed.outcome.alternatives
            == (a.candidate, b.candidate, c.candidate),
            "unresolved alternatives changed",
        )

    ambiguous_a = make_binding(sd, "candidate:duplicate")
    ambiguous_b = make_binding(sd, "candidate:duplicate")
    ambiguous_c = make_binding(sd, "candidate:c")
    ambiguous_policy = sd.ConvergencePolicy(
        "select.explicit-order",
        parameters=(
            ("order", ("candidate:duplicate", "candidate:c")),
        ),
    )
    ambiguous_set = sd.construct_semantic_convergence_set(
        (ambiguous_a, ambiguous_b, ambiguous_c),
        policy=ambiguous_policy,
    )
    ambiguous = sd.apply_semantic_convergence_policy(ambiguous_set)
    require(
        ambiguous.ranking == () and ambiguous.outcome.kind_id == "unresolved",
        "ambiguous member identity received hidden tie-breaker",
    )
    print("Malformed, unsupported, and ambiguous policies fail deterministically unresolved: PASS")

    zero = sd.construct_semantic_convergence_set((), policy=compose_policy)
    one = sd.construct_semantic_convergence_set((a,), policy=select_policy)
    for convergence_set in (zero, one):
        observed = sd.apply_semantic_convergence_policy(convergence_set)
        require(observed.ranking == (), "insufficient cardinality created ranking")
        require(observed.outcome.kind_id == "unresolved", "insufficient cardinality converged")
    print("Insufficient convergence cardinality remains unresolved: PASS")

    require(
        first.provenance is first_set.provenance
        or first.provenance == first_set.provenance,
        "resolution provenance changed",
    )
    require(
        first.outcome.provenance == first_set.provenance,
        "outcome provenance changed",
    )
    require(
        first.ranking[0].candidate is c.candidate,
        "ranked candidate identity copied",
    )
    print("Exact canonical candidate identity and D provenance preserved: PASS")

    source = (ROOT / "apexforge/semantic_decision/resolution.py").read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "max_weight",
        "paradox.elevation_candidate",
        "priority",
        "from runtime",
        "import runtime",
        "from authority",
        "import authority",
        "from governance",
        "import governance",
        "from quad_vector",
        "import quad_vector",
        "from aether_air",
        "import aether_air",
        "select_path",
        "resolve_quad_vector_synchronization",
    ):
        require(
            forbidden not in source,
            "forbidden predecessor/Paradox behavior entered E: " + forbidden,
        )
    print("No hidden predecessor precedence, runtime behavior, or Paradox Elevation: PASS")

    contract_path = (
        ROOT
        / "docs/p11/P11_10E_DETERMINISTIC_CONVERGENCE_SELECTION_COMPOSITION_AND_RANKING.md"
    )
    contract = contract_path.read_text(encoding="utf-8")
    for phrase in (
        "P11.10F owns Paradox Elevation eligibility",
        "P11.10G owns validation, collision, closure",
        "D candidate encounter order remains trace order and is not precedence.",
        "P11.10F must not reinterpret every unresolved E result as Paradox Elevation automatically.",
        "unsupported policy identity simply has no E-owned ordinary convergence semantics",
    ):
        require(phrase in contract, "E ownership contract missing: " + phrase)
    print("E ownership and downstream Paradox/validation boundary contract: PASS")

    observed = status_paths()
    require(
        not observed or observed == ALLOWED,
        "unexpected P11.10E artifacts: " + repr(sorted(observed)),
    )
    print("Repository no-op E boundary: PASS")


if __name__ == "__main__":
    main()
