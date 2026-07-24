"""
ApexForge Principal Execution Integration Test.

Tests:
1. A principal possessing the required authority can execute.
2. A principal lacking the required authority is blocked before execution.
"""

from workflow.directive_engine import (
    DirectiveExecutionEngine,
    TestDirectiveRegistry,
)

from workflow.registry import PrincipalRegistry

from authority.validator import (
    PrincipalAuthorizationError,
)

from air.model import (
    AIRProgram,
    AIRPrincipal,
    DirectiveAuthority,
    PrincipalAuthority,
)


class TestAuthorityRegistry:
    """
    Minimal authority registry for this integration test.

    Sentinel and Auditor are both recognized authorities. This allows
    the test to reach principal authorization instead of failing during
    authority-reference validation.
    """

    def __init__(self) -> None:
        self._authorities = {
            "Sentinel": object(),
            "Auditor": object(),
        }

    def get(self, name: str):
        return self._authorities.get(name)

    def contains(self, name: str) -> bool:
        return name in self._authorities

    def has_capability(
        self,
        authority_name: str,
        capability: str,
    ) -> bool:
        return True


def make_principal(
    authority_name: str,
    ) -> AIRPrincipal:
        return AIRPrincipal(
            name="Lyra",
            authorities=(
                PrincipalAuthority(
                    name=authority_name,
            ),
        ),
    )

def make_program(
    principal: AIRPrincipal,
) -> AIRProgram:
    """
    Creates a minimal executable AIR program requiring Sentinel.
    """

    return AIRProgram(
        version="0.2",
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        authorities=(
            DirectiveAuthority(
                name="Sentinel",
            ),
        ),
        principals=(
            principal,
        ),
    )


def authorized_test() -> None:
    print("=== Authorized Principal Test ===")

    principal = make_principal(
        authority_name="Sentinel",
    )

    program = make_program(principal)

    directive_registry = TestDirectiveRegistry()
    authority_registry = TestAuthorityRegistry()
    principal_registry = PrincipalRegistry()

    directive_registry.register(
        "Investigate",
        program,
    )

    principal_registry.register(principal)

    engine = DirectiveExecutionEngine()

    execution_result = engine.execute(
        registry=directive_registry,
        authority_registry=authority_registry,
        principal_registry=principal_registry,
        principal_name="Lyra",
        root="Investigate",
    )

    if execution_result.root != "Investigate":
        raise AssertionError(
            "Execution result contains the wrong root directive."
        )

    if len(execution_result.results) != 1:
        raise AssertionError(
            "Expected exactly one directive execution result, "
            f"but received {len(execution_result.results)}."
        )

    executed_name, _ = execution_result.results[0]

    if executed_name != "Investigate":
        raise AssertionError(
            f"Expected Investigate to execute, "
            f"but received {executed_name}."
        )

    print(
        "PASS: Lyra possessed Sentinel authority and "
        "the directive executed."
    )


def unauthorized_test() -> None:
    print("\n=== Unauthorized Principal Test ===")

    principal = make_principal(
        authority_name="Auditor",
    )

    program = make_program(principal)

    directive_registry = TestDirectiveRegistry()
    authority_registry = TestAuthorityRegistry()
    principal_registry = PrincipalRegistry()

    directive_registry.register(
        "Investigate",
        program,
    )

    principal_registry.register(principal)

    engine = DirectiveExecutionEngine()

    try:
        engine.execute(
            registry=directive_registry,
            authority_registry=authority_registry,
            principal_registry=principal_registry,
            principal_name="Lyra",
            root="Investigate",
        )

    except PrincipalAuthorizationError as error:
        error_message = str(error)

        if "Sentinel" not in error_message:
            raise AssertionError(
                "Authorization failed, but the error did not "
                "identify the missing Sentinel authority."
            )

        print(
            "PASS: Lyra lacked Sentinel authority and "
            "execution was blocked."
        )

        print(
            f"Authorization message: {error_message}"
        )

        return

    raise AssertionError(
        "Unauthorized principal was allowed to execute."
    )


def run_tests() -> None:
    print(
        "ApexForge Principal Authority Pipeline\n"
    )

    authorized_test()
    unauthorized_test()

    print(
        "\nALL PRINCIPAL EXECUTION INTEGRATION TESTS PASSED"
    )


if __name__ == "__main__":
    run_tests()