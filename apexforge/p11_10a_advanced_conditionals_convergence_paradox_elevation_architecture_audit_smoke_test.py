"""AFP-P11.10A advanced conditionals, convergence, and Paradox Elevation architecture audit."""

from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "p11.10a-advanced-conditionals-convergence-paradox-elevation-architecture-audit"
PREDECESSOR_TAG = "afp-p11.9i-freeze"
PREDECESSOR_SHORT = "06a6d71"

CONTRACT = ROOT / "docs" / "p11" / "P11_10A_ADVANCED_CONDITIONALS_CONVERGENCE_AND_PARADOX_ELEVATION_ARCHITECTURE_AUDIT.md"
SMOKE = ROOT / "apexforge" / "p11_10a_advanced_conditionals_convergence_paradox_elevation_architecture_audit_smoke_test.py"

ALLOWED = {
    CONTRACT.relative_to(ROOT).as_posix(),
    SMOKE.relative_to(ROOT).as_posix(),
}

AETHER = (
    "apexforge/aether_air/__init__.py",
    "apexforge/aether_air/construction.py",
    "apexforge/aether_air/model.py",
    "apexforge/aether_air/projection.py",
    "apexforge/aether_air/records.py",
    "apexforge/aether_air/reporting.py",
    "apexforge/aether_air/transformation.py",
    "apexforge/aether_air/validation.py",
)

CONDITIONAL_OWNERS = (
    "apexforge/air/functions.py",
    "apexforge/air/model.py",
    "apexforge/language/parser.py",
    "apexforge/language/compiler.py",
    "apexforge/language/validation/runtime_validator.py",
    "apexforge/runtime/engine.py",
    "apexforge/language/narrative_model.py",
    "apexforge/language/narrative_parser.py",
    "apexforge/runtime/narrative_binding.py",
    "apexforge/runtime/narrative_execution.py",
    "apexforge/runtime/narrative_transition.py",
)

QUAD_VECTOR = (
    "apexforge/quad_vector/resolver.py",
    "apexforge/quad_vector/synchronizer.py",
    "apexforge/quad_vector/model.py",
    "apexforge/quad_vector/orchestration.py",
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


def unchanged(*paths: str) -> bool:
    return not git("diff", "--name-only", PREDECESSOR_TAG, "--", *paths)


def main() -> None:
    before = git("status", "--porcelain=v1")

    require(git("branch", "--show-current") == EXPECTED_BRANCH, "unexpected P11.10A branch")
    predecessor = git("rev-list", "-n", "1", PREDECESSOR_TAG)
    require(predecessor.startswith(PREDECESSOR_SHORT), "P11.9I freeze tag moved")
    ancestry = subprocess.run(
        ("git", "merge-base", "--is-ancestor", predecessor, "HEAD"),
        cwd=str(ROOT),
        check=False,
    )
    require(ancestry.returncode == 0, "P11.10A does not descend from frozen P11.9I")
    print("Frozen P11.9I predecessor and exact branch ancestry: PASS")

    require(unchanged(*AETHER), "P11.10A modified frozen AETHER-AIR production")
    require(unchanged(*CONDITIONAL_OWNERS), "P11.10A modified an existing conditional owner")
    require(unchanged(*QUAD_VECTOR), "P11.10A modified frozen Quad-Vector owners")
    print("Frozen AETHER-AIR, conditional, and Quad-Vector surfaces preserved: PASS")

    air_functions = (ROOT / "apexforge" / "air" / "functions.py").read_text(encoding="utf-8")
    air_model = (ROOT / "apexforge" / "air" / "model.py").read_text(encoding="utf-8")
    parser = (ROOT / "apexforge" / "language" / "parser.py").read_text(encoding="utf-8")
    require(
        "class AIRFunctionWhen" in air_functions
        and "otherwise_actions" in air_functions
        and "class AIRWhenAction" in air_model
        and "class FunctionWhenNode" in parser
        and "class WhenActionNode" in parser,
        "existing ordinary conditional boundary disappeared",
    )
    print("Existing AIR/language ordinary conditional ownership preserved: PASS")

    resolver = (ROOT / "apexforge" / "quad_vector" / "resolver.py").read_text(encoding="utf-8")
    synchronizer = (ROOT / "apexforge" / "quad_vector" / "synchronizer.py").read_text(encoding="utf-8")
    require(
        "Deterministic Rotor-Ring convergence" in resolver
        and "resolve_quad_vector_synchronization" in resolver
        and "ResultantVector" in resolver
        and "synchronize_quad_vector_field_matrix" in synchronizer,
        "frozen Quad-Vector convergence/resultant boundary disappeared",
    )
    print("Frozen Quad-Vector synchronization and ResultantVector ownership preserved: PASS")

    paradox_production = []
    for path in (ROOT / "apexforge").rglob("*.py"):
        if path.name.startswith("p11_"):
            continue
        lowered = path.read_text(encoding="utf-8").casefold()
        if "paradox_elevation" in lowered or "paradoxelevation" in lowered or "paradox elevation" in lowered:
            paradox_production.append(path.relative_to(ROOT).as_posix())
    require(
        not paradox_production,
        "predecessor production already owns Paradox Elevation: " + repr(paradox_production),
    )
    print("No predecessor production Paradox Elevation implementation: PASS")

    text = CONTRACT.read_text(encoding="utf-8")
    markers = (
        "higher-order semantic decision boundary",
        "not a second implementation of ordinary AIR or narrative branch execution",
        "semantic alternatives",
        "not vector arithmetic convergence",
        "A convergence policy must be explicit",
        "does not recompute Quad-Vector synchronization or a `ResultantVector`",
        "remain canonically admissible, materially incompatible",
        "contradiction or incompatibility becomes represented semantic state",
        "Deterministic ordering is not semantic precedence",
        "does not acquire authority to override",
        "P11.10B",
        "P11.10I",
    )
    for marker in markers:
        require(marker in text, f"missing P11.10A contract marker: {marker!r}")
    print("Advanced-conditional higher-order semantic boundary: PASS")
    print("Semantic convergence distinct from Quad-Vector resultant resolution: PASS")
    print("Explicit convergence-policy and non-implicit-precedence boundary: PASS")
    print("Paradox Elevation irreducible-state preservation boundary: PASS")
    print("Authority/runtime/backend/AETHER ownership exclusions: PASS")

    status_lines = tuple(line for line in git("status", "--porcelain=v1").splitlines() if line)
    paths = set()
    for line in status_lines:
        require(line[:2] == "??", "tracked/staged mutation entered P11.10A audit: " + line)
        paths.add(line[3:].replace("\\", "/"))
    require(not paths or paths == ALLOWED, "unexpected P11.10A audit artifacts: " + repr(sorted(paths)))

    after = git("status", "--porcelain=v1")
    require(before == after, "P11.10A audit mutated repository status")
    print("Repository no-op audit-only boundary: PASS")


if __name__ == "__main__":
    main()
