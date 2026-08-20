"""AFP-P11.10B minimal immutable semantic-decision model smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
import inspect
from pathlib import Path
import subprocess

from semantic_decision import (
    CORE_SEMANTIC_OUTCOME_KINDS,
    AdvancedCondition,
    CandidateAlternative,
    SemanticOutcome,
    SemanticOutcomeKind,
)
import semantic_decision
import semantic_decision.model as model


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "p11.10b-minimal-immutable-advanced-conditional-candidate-outcome-model"
PREDECESSOR_TAG = "afp-p11.10a-freeze"
PREDECESSOR_SHORT = "bec53e8"

CONTRACT = ROOT / "docs" / "p11" / "P11_10B_MINIMAL_IMMUTABLE_ADVANCED_CONDITIONAL_CANDIDATE_ALTERNATIVE_AND_OUTCOME_MODEL.md"
SMOKE = ROOT / "apexforge" / "p11_10b_minimal_immutable_advanced_conditional_candidate_outcome_model_smoke_test.py"
PACKAGE_INIT = ROOT / "apexforge" / "semantic_decision" / "__init__.py"
PACKAGE_MODEL = ROOT / "apexforge" / "semantic_decision" / "model.py"

ALLOWED = {
    CONTRACT.relative_to(ROOT).as_posix(),
    SMOKE.relative_to(ROOT).as_posix(),
    PACKAGE_INIT.relative_to(ROOT).as_posix(),
    PACKAGE_MODEL.relative_to(ROOT).as_posix(),
}

EXPECTED_PUBLIC = (
    "AdvancedCondition",
    "CandidateAlternative",
    "SemanticOutcomeKind",
    "SemanticOutcome",
    "CORE_SEMANTIC_OUTCOME_KINDS",
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
    return completed.stdout.strip()


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

    require(git("branch", "--show-current") == EXPECTED_BRANCH, "unexpected P11.10B branch")
    predecessor = git("rev-list", "-n", "1", PREDECESSOR_TAG)
    require(predecessor.startswith(PREDECESSOR_SHORT), "P11.10A freeze tag moved")
    ancestry = subprocess.run(
        ("git", "merge-base", "--is-ancestor", predecessor, "HEAD"),
        cwd=str(ROOT),
        check=False,
    )
    require(ancestry.returncode == 0, "P11.10B does not descend from frozen P11.10A")
    print("Frozen P11.10A predecessor and exact branch ancestry: PASS")

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
        "P11.10B modified a frozen predecessor production surface",
    )
    print("Frozen predecessor production ownership surfaces preserved: PASS")

    require(PACKAGE_INIT.is_file(), "semantic_decision package initializer missing")
    require(PACKAGE_MODEL.is_file(), "semantic_decision model missing")
    require(CONTRACT.is_file(), "P11.10B contract missing")
    require(tuple(semantic_decision.__all__) == EXPECTED_PUBLIC, "unexpected package public surface")
    require(tuple(model.__all__) == EXPECTED_PUBLIC, "unexpected model public surface")
    for name in EXPECTED_PUBLIC:
        require(
            getattr(semantic_decision, name) is getattr(model, name),
            "package export identity mismatch: " + name,
        )
    print("Exact five-symbol semantic_decision public surface: PASS")

    expected_fields = {
        AdvancedCondition: ("identity", "condition_kind", "payload", "provenance"),
        CandidateAlternative: ("identity", "payload", "provenance"),
        SemanticOutcomeKind: ("canonical_id",),
        SemanticOutcome: ("kind_id", "alternatives", "payload", "provenance"),
    }
    for record_type, shape in expected_fields.items():
        require(is_dataclass(record_type), record_type.__name__ + " must be a dataclass")
        require(
            tuple(item.name for item in fields(record_type)) == shape,
            record_type.__name__ + " field shape changed",
        )

    condition = AdvancedCondition(
        identity="condition:alpha",
        condition_kind="evidence.threshold",
        payload=("signal", 3, True, None),
        provenance=("source:alpha",),
    )
    candidate_a = CandidateAlternative(
        identity="alternative:a",
        payload=("payload", 1),
        provenance=("source:a",),
    )
    candidate_b = CandidateAlternative(
        identity="alternative:b",
        payload=("payload", 2),
        provenance=("source:b",),
    )
    kind = SemanticOutcomeKind("extension.example")
    outcome = SemanticOutcome(
        kind_id="selected",
        alternatives=(candidate_a, candidate_b),
        payload=("decision",),
        provenance=("source:decision",),
    )
    assert_frozen(condition, "identity")
    assert_frozen(candidate_a, "identity")
    assert_frozen(kind, "canonical_id")
    assert_frozen(outcome, "kind_id")
    require(
        outcome.alternatives[0] is candidate_a and outcome.alternatives[1] is candidate_b,
        "candidate object identity/order not preserved",
    )
    print("Frozen exact record shapes and candidate identity preservation: PASS")

    require(
        tuple(item.canonical_id for item in CORE_SEMANTIC_OUTCOME_KINDS)
        == ("selected", "composed", "unresolved", "paradox.elevation_candidate"),
        "core semantic outcome taxonomy changed",
    )
    require(
        all(type(item) is SemanticOutcomeKind for item in CORE_SEMANTIC_OUTCOME_KINDS),
        "core taxonomy contains non-canonical kind values",
    )
    print("Exact four-kind semantic outcome taxonomy: PASS")

    custom_condition = AdvancedCondition(
        identity="condition:open",
        condition_kind="future.condition.kind",
    )
    custom_outcome = SemanticOutcome(kind_id="future.outcome.kind")
    require(
        custom_condition.condition_kind == "future.condition.kind",
        "condition kind was reinterpreted",
    )
    require(custom_outcome.kind_id == "future.outcome.kind", "outcome kind was closed prematurely")
    print("Open passive condition-kind and outcome-kind identifier boundary: PASS")

    for constructor in (
        lambda: AdvancedCondition("c", "k", payload=[]),
        lambda: CandidateAlternative("a", payload={}),
        lambda: SemanticOutcome("selected", payload=set()),
        lambda: AdvancedCondition("c", "k", provenance=["p"]),
        lambda: CandidateAlternative("a", provenance=(" ",)),
        lambda: SemanticOutcome("selected", alternatives=[candidate_a]),
        lambda: SemanticOutcome("selected", alternatives=(object(),)),
    ):
        try:
            constructor()
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("mutable or non-canonical B structure was accepted")
    print("Recursive immutability and exact tuple/type boundaries: PASS")

    empty_selected = SemanticOutcome(kind_id="selected")
    duplicate_selected = SemanticOutcome(
        kind_id="selected",
        alternatives=(candidate_a, candidate_a),
    )
    elevation_candidate = SemanticOutcome(
        kind_id="paradox.elevation_candidate",
        alternatives=(candidate_a, candidate_b),
    )
    require(empty_selected.alternatives == (), "B unexpectedly synthesized selected alternatives")
    require(
        duplicate_selected.alternatives == (candidate_a, candidate_a),
        "B unexpectedly deduplicated alternatives",
    )
    require(
        elevation_candidate.kind_id == "paradox.elevation_candidate",
        "B elevation-candidate category changed",
    )
    print("Later-owned cardinality/collision/admissibility/elevation validation absent: PASS")

    public_functions = tuple(
        name
        for name, value in vars(model).items()
        if not name.startswith("_") and inspect.isfunction(value)
    )
    require(
        public_functions == (),
        "operative public model functions entered P11.10B: " + repr(public_functions),
    )
    print("No evaluation/convergence/ranking/Paradox-Elevation operative behavior: PASS")

    contract_text = CONTRACT.read_text(encoding="utf-8")
    markers = (
        "B is data vocabulary only",
        "P11.10C owns canonical condition evidence",
        "P11.10D owns semantic convergence-set construction",
        "P11.10E owns deterministic convergence selection",
        "P11.10F owns Paradox Elevation eligibility",
        "P11.10G owns validation, collision, closure, provenance, and extension contracts",
        "A structurally valid B record can still be semantically invalid",
    )
    for marker in markers:
        require(marker in contract_text, "missing P11.10B ownership marker: " + repr(marker))
    print("Later-slice ownership and data-first boundary documented: PASS")

    status_lines = tuple(line for line in status().splitlines() if line)
    paths = set()
    for line in status_lines:
        require(line[:2] == "??", "tracked/staged mutation entered P11.10B smoke: " + line)
        paths.add(line[3:].replace("\\", "/"))
    require(not paths or paths == ALLOWED, "unexpected P11.10B artifacts: " + repr(sorted(paths)))

    after = status()
    require(before == after, "P11.10B smoke mutated repository status")
    print("Repository no-op B boundary: PASS")


if __name__ == "__main__":
    main()