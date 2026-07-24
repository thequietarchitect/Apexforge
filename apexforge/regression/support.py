from __future__ import annotations


class AllowAllAuthority:
    """Test authority that permits every runtime authority check."""

    def allows(self, check) -> bool:
        return True


class DenyAllAuthority:
    """Test authority that denies every runtime authority check."""

    def allows(self, check) -> bool:
        return False


class TestState:
    """
    Minimal state implementation for pipeline integration tests.

    RuntimeEngine requires the state object to provide apply(delta).
    """

    def __init__(self) -> None:
        self.applied_deltas = []

    def apply(self, delta):
        self.applied_deltas.append(delta)
        return self