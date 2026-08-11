"""P11.7A Quad-Vector Engine architecture red-gate smoke test."""

from __future__ import annotations

from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    contract = root / "P11_7A_QUAD_VECTOR_ENGINE_ARCHITECTURE.md"
    text = contract.read_text(encoding="utf-8")

    required_contract = (
        "Quad-Vector Field Matrix",
        "Hyper-Conductive Stator",
        "Hyper-Conductive Rotor Ring",
        "Adaptive Field Control Core",
        "Active Thermal Balance",
        "Four independent canonical lanes: +X, -X, +Y, -Y.",
        "function",
        "conditional",
        "resolver",
        "weighting_rule",
        "vector_operator",
        "synchronizer",
        "Discover",
        "Validate",
        "Register",
        "Bind",
        "Execute",
        "Discovery MUST NOT execute a module.",
        "The engine core MUST execute canonical components without knowing which specific components exist.",
        "Codex integration is optional and advisory.",
        "Codex MUST NOT receive privileged insertion into the running engine",
        "immutable ResultantVector",
    )
    for marker in required_contract:
        require(marker in text, f"P11.7A architecture contract lost marker: {marker!r}")

    print("Motor-derived Quad-Vector architecture contract: PASS")
    print("Canonical modular component bus contract: PASS")
    print("Codex optional/advisory boundary contract: PASS")

    # Red gate: the passive canonical model does not exist yet.
    from quad_vector.model import (
        QuadVectorLane,
        QuadVectorResourceBudget,
        ResultantVector,
    )

    require(
        tuple(member.value for member in QuadVectorLane)
        == ("+X", "-X", "+Y", "-Y"),
        "canonical Quad-Vector lane order changed",
    )
    require(QuadVectorResourceBudget is not None, "resource-budget model missing")
    require(ResultantVector is not None, "resultant-vector model missing")
    print("Passive Quad-Vector canonical model: PASS")
    print("P11.7A Quad-Vector architecture red gate: PASS")


if __name__ == "__main__":
    main()
