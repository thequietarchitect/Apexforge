from air.model import AIRAuthority
from authority.registry import (
    AuthorityRegistry,
    AuthorityInheritanceError,
)


def test_normal_inheritance():
    registry = AuthorityRegistry()

    registry.register(
        AIRAuthority(
            id="authority:Sentinel",
            name="Sentinel",
            capabilities=("Observe",),
        )
    )

    registry.register(
        AIRAuthority(
            id="authority:AEGIS",
            name="AEGIS",
            capabilities=("Protect",),
            inherits=("Sentinel",),
        )
    )

    resolved = registry.resolve_capabilities("AEGIS")

    assert resolved == {"Observe", "Protect"}

    print("PASS: normal inheritance resolved correctly")


def test_cycle_detection():
    registry = AuthorityRegistry()

    registry.register(
        AIRAuthority(
            id="authority:A",
            name="A",
            capabilities=(),
            inherits=("B",),
        )
    )

    registry.register(
        AIRAuthority(
            id="authority:B",
            name="B",
            capabilities=(),
            inherits=("A",),
        )
    )

    try:
        registry.resolve_capabilities("A")
        raise AssertionError("Expected AuthorityInheritanceError")
    except AuthorityInheritanceError as error:
        assert "cycle" in str(error).lower()
        assert "A" in str(error)

    print("PASS: inheritance cycle detected correctly")


if __name__ == "__main__":
    test_normal_inheritance()
    test_cycle_detection()

    print("ALL AUTHORITY INHERITANCE TESTS PASSED")
