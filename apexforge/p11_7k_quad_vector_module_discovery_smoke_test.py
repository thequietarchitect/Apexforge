"""P11.7K canonical Quad-Vector module-discovery red-gate smoke test."""

from dataclasses import FrozenInstanceError


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_error(error_type, callback, message: str) -> None:
    try:
        callback()
    except error_type:
        return
    raise AssertionError(message)


def main() -> None:
    from quad_vector.discovery import (
        QuadVectorDiscoveryCandidate,
        QuadVectorDiscoveryInventory,
        QuadVectorDiscoverySource,
        discover_quad_vector_modules,
    )

    require(
        tuple(item.value for item in QuadVectorDiscoverySource)
        == ("manifest", "directory", "explicit"),
        "canonical discovery source taxonomy changed",
    )

    candidates = (
        QuadVectorDiscoveryCandidate(
            source=QuadVectorDiscoverySource.EXPLICIT,
            source_identity="source:explicit:vector-emitter",
            descriptor_identity="descriptor:VectorEmitter",
            descriptor_reference="modules/vector_emitter.qvmodule",
            order=20,
        ),
        QuadVectorDiscoveryCandidate(
            source=QuadVectorDiscoverySource.MANIFEST,
            source_identity="source:manifest:quad-vector",
            descriptor_identity="descriptor:BaseVelocity",
            descriptor_reference="quad-vector.json#BaseVelocity",
            order=0,
        ),
        QuadVectorDiscoveryCandidate(
            source=QuadVectorDiscoverySource.DIRECTORY,
            source_identity="source:directory:rules",
            descriptor_identity="descriptor:BalanceWeight",
            descriptor_reference="rules/balance_weight.qvmodule",
            order=10,
        ),
    )

    inventory = discover_quad_vector_modules(candidates)

    require(
        type(inventory) is QuadVectorDiscoveryInventory,
        "discovery returned a non-canonical inventory",
    )
    require(
        tuple(item.descriptor_identity for item in inventory.candidates)
        == (
            "descriptor:BaseVelocity",
            "descriptor:BalanceWeight",
            "descriptor:VectorEmitter",
        ),
        "deterministic discovery ordering changed",
    )
    require(
        tuple(item.source for item in inventory.candidates)
        == (
            QuadVectorDiscoverySource.MANIFEST,
            QuadVectorDiscoverySource.DIRECTORY,
            QuadVectorDiscoverySource.EXPLICIT,
        ),
        "discovery source provenance changed",
    )
    require(
        tuple(item.source_identity for item in inventory.candidates)
        == (
            "source:manifest:quad-vector",
            "source:directory:rules",
            "source:explicit:vector-emitter",
        ),
        "discovery source identity changed",
    )
    require(
        tuple(item.descriptor_reference for item in inventory.candidates)
        == (
            "quad-vector.json#BaseVelocity",
            "rules/balance_weight.qvmodule",
            "modules/vector_emitter.qvmodule",
        ),
        "passive descriptor references changed",
    )

    duplicate = QuadVectorDiscoveryCandidate(
        source=QuadVectorDiscoverySource.EXPLICIT,
        source_identity="source:explicit:duplicate",
        descriptor_identity="descriptor:BaseVelocity",
        descriptor_reference="other/base_velocity.qvmodule",
        order=30,
    )
    expect_error(
        ValueError,
        lambda: discover_quad_vector_modules(candidates + (duplicate,)),
        "duplicate descriptor identity bypassed discovery validation",
    )
    expect_error(
        TypeError,
        lambda: discover_quad_vector_modules([candidates[0]]),
        "non-tuple discovery collection accepted",
    )
    expect_error(
        TypeError,
        lambda: discover_quad_vector_modules((object(),)),
        "non-canonical discovery candidate accepted",
    )
    expect_error(
        ValueError,
        lambda: QuadVectorDiscoveryCandidate(
            source=QuadVectorDiscoverySource.EXPLICIT,
            source_identity="source:explicit:invalid-order",
            descriptor_identity="descriptor:InvalidOrder",
            descriptor_reference="invalid.qvmodule",
            order=-1,
        ),
        "negative discovery order accepted",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(inventory, "candidates", ()),
        "discovery inventory became mutable",
    )
    expect_error(
        FrozenInstanceError,
        lambda: setattr(inventory.candidates[0], "descriptor_reference", "mutated"),
        "discovery candidate became mutable",
    )

    for item in (inventory,) + inventory.candidates:
        require(
            not hasattr(item, "parse")
            and not hasattr(item, "canonicalize")
            and not hasattr(item, "register")
            and not hasattr(item, "bind")
            and not hasattr(item, "execute")
            and not hasattr(item, "run")
            and not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex"),
            "P11.7K discovery snapshot gained parse/runtime/loader/Codex authority",
        )

    print("Canonical manifest/directory/explicit discovery source taxonomy: PASS")
    print("Deterministic passive discovery ordering: PASS")
    print("Discovery source identity/provenance preservation: PASS")
    print("Opaque descriptor-reference preservation: PASS")
    print("Discovery descriptor-identity collision validation: PASS")
    print("Exact discovery candidate/collection boundary: PASS")
    print("Immutable discovery inventory boundary: PASS")
    print("P11.7K parse/register/bind/execution/loader/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
