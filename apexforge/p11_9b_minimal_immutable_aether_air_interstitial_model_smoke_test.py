"""P11.9B minimal immutable AETHER-AIR 2.0 interstitial-model smoke test."""

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
    from aether_air.model import (
        CORE_AETHER_BEHAVIOR_KINDS,
        AetherAirRepresentation,
        AetherBehaviorIntent,
        AetherBehaviorKind,
        AetherIntentParameter,
    )

    ids = tuple(kind.canonical_id for kind in CORE_AETHER_BEHAVIOR_KINDS)
    require(ids == (
        "behavior.intent",
        "transformation.intent",
        "constraint.intent",
        "projection.intent",
    ), "core AETHER-AIR behavior-kind taxonomy changed")
    print("Canonical extensible four-kind AETHER-AIR taxonomy: PASS")

    extra = AetherBehaviorKind("domain.experimental")
    kinds = CORE_AETHER_BEHAVIOR_KINDS + (extra,)
    require(kinds[-1] is extra, "behavior-kind extension lost identity")
    print("Open behavior-kind extension boundary: PASS")

    parameter = AetherIntentParameter("mode", ("preserve", "defer"))
    behavior = AetherBehaviorIntent(
        "behavior.intent",
        "preserve canonical behavioral intent",
        parameters=(parameter,),
    )
    representation = AetherAirRepresentation(behaviors=(behavior,))
    require(
        representation.behaviors[0] is behavior
        and behavior.parameters[0] is parameter,
        "representation changed supplied identity/order",
    )
    print("Immutable interstitial encounter-order preservation: PASS")

    raises(
        FrozenInstanceError,
        lambda: setattr(extra, "canonical_id", "changed"),
        "behavior kind became mutable",
    )
    raises(
        FrozenInstanceError,
        lambda: setattr(parameter, "key", "changed"),
        "intent parameter became mutable",
    )
    raises(
        FrozenInstanceError,
        lambda: setattr(behavior, "intent", "changed"),
        "behavior intent became mutable",
    )
    raises(
        FrozenInstanceError,
        lambda: setattr(representation, "behaviors", ()),
        "AETHER-AIR representation became mutable",
    )
    print("Frozen kind/parameter/intent/representation boundary: PASS")

    raises(
        TypeError,
        lambda: AetherIntentParameter("bad", ["mutable"]),
        "mutable list accepted as intent parameter value",
    )
    raises(
        TypeError,
        lambda: AetherIntentParameter("bad", {"rank": 1}),
        "mutable mapping accepted as intent parameter value",
    )
    raises(
        TypeError,
        lambda: AetherBehaviorIntent(
            "behavior.intent",
            "bad container",
            parameters=[parameter],
        ),
        "mutable parameter container accepted",
    )
    raises(
        TypeError,
        lambda: AetherAirRepresentation(behaviors=[behavior]),
        "mutable behavior container accepted",
    )
    print("Recursively immutable intent-value/container contract: PASS")

    for owner in (behavior, representation):
        for name in (
            "execute",
            "run",
            "evaluate",
            "branch",
            "select",
            "resolve",
            "rank",
            "grant",
            "deny",
            "synchronize",
            "converge",
            "normalize",
            "transform",
            "project",
            "lower",
            "compile",
            "emit",
            "generate",
            "construct",
            "load",
        ):
            require(
                not hasattr(owner, name),
                "operative behavior leaked into AETHER-AIR model: " + name,
            )
    print("Behavioral intent remains non-executing data: PASS")

    parameter_fields = tuple(AetherIntentParameter.__dataclass_fields__)
    behavior_fields = tuple(AetherBehaviorIntent.__dataclass_fields__)
    representation_fields = tuple(AetherAirRepresentation.__dataclass_fields__)
    require(
        parameter_fields == ("key", "value"),
        "P11.9B intent-parameter surface expanded",
    )
    require(
        behavior_fields == ("kind_id", "intent", "parameters"),
        "P11.9B behavior-intent surface expanded",
    )
    require(
        representation_fields == ("behaviors",),
        "P11.9B representation surface expanded",
    )
    print("P11.9C/D/E/G ownership boundaries preserved: PASS")

    require(
        tuple(item.key for item in behavior.parameters) == ("mode",)
        and tuple(item.kind_id for item in representation.behaviors)
        == ("behavior.intent",),
        "AETHER-AIR deterministic encounter order changed",
    )
    print("Deterministic ordering without semantic precedence: PASS")


if __name__ == "__main__":
    main()
