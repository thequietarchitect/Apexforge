"""P11.8B minimal immutable lattice-model smoke test."""

from dataclasses import FrozenInstanceError


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def raises(exc_type, fn, message):
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(message)


def main():
    from semantic_lattice.model import (
        CORE_SEMANTIC_LATTICE_AXES,
        ParametricSemanticLattice,
        SemanticLatticeAxis,
        SemanticLatticeParameter,
    )

    ids = tuple(axis.canonical_id for axis in CORE_SEMANTIC_LATTICE_AXES)
    require(ids == (
        "structural.declaration",
        "narrative.identity_relation",
        "authority.integrity",
        "priority",
        "continuity",
        "convergence",
        "causal.provenance",
        "tam.traceability",
    ), "core axis taxonomy changed")
    print("Canonical extensible eight-axis taxonomy: PASS")

    extra = SemanticLatticeAxis("domain.experimental")
    axes = CORE_SEMANTIC_LATTICE_AXES + (extra,)
    require(axes[-1] is extra, "axis extension lost identity")
    print("Open metadata-axis extension boundary: PASS")

    parameter = SemanticLatticeParameter("continuity", "status", ("observed", "stable"))
    lattice = ParametricSemanticLattice(axes=axes, parameters=(parameter,))
    require(lattice.axes is axes and lattice.parameters[0] is parameter, "snapshot changed supplied identity/order")
    print("Immutable snapshot encounter-order preservation: PASS")

    raises(FrozenInstanceError, lambda: setattr(extra, "canonical_id", "changed"), "axis became mutable")
    raises(FrozenInstanceError, lambda: setattr(parameter, "key", "changed"), "parameter became mutable")
    raises(FrozenInstanceError, lambda: setattr(lattice, "parameters", ()), "snapshot became mutable")
    print("Frozen axis/parameter/snapshot boundary: PASS")

    raises(TypeError, lambda: SemanticLatticeParameter("priority", "bad", ["mutable"]), "mutable list accepted")
    raises(TypeError, lambda: SemanticLatticeParameter("priority", "bad", {"rank": 1}), "mutable mapping accepted")
    raises(TypeError, lambda: ParametricSemanticLattice(axes=list(axes)), "mutable axes container accepted")
    print("Recursively immutable metadata-value contract: PASS")

    passive = ParametricSemanticLattice(parameters=(
        SemanticLatticeParameter("priority", "observed", 7),
        SemanticLatticeParameter("convergence", "resultant_ref", ("quad.resultant", 10, 4)),
    ))
    for name in ("execute", "run", "bind", "resolve", "select", "rank", "grant", "deny", "synchronize", "load"):
        require(not hasattr(passive, name), "operative behavior leaked into lattice: " + name)
    print("Priority/convergence metadata remains non-operative: PASS")

    fields = SemanticLatticeParameter.__dataclass_fields__
    require("subject" not in fields and "relation" not in fields and "evidence" not in fields, "P11.8C boundary was preempted")
    print("P11.8C subject/relationship/evidence boundary preserved: PASS")

    require(tuple(item.axis_id for item in passive.parameters) == ("priority", "convergence"), "metadata order changed")
    print("Deterministic ordering without semantic precedence: PASS")

if __name__ == "__main__":
    main()
