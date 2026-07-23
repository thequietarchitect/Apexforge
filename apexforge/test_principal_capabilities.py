"""
Tests principal capability authorization in ApexForge.
"""

from authority.validator import (
    PrincipalCapabilityAuthorizationError,
)

from air.model import (
    AIRPrincipal,
    AIRProgram,
    DirectiveAuthority,
    Principal,
    PrincipalAuthority,
)


class TestRequirement:
    def __init__(
        self,
        capability: str,
    ) -> None:
        self.capability = capability


class TestAuthorityRegistry:
    def __init__(self) -> None:
        self._capabilities = {
            "Sentinel": {
                "Observe",
                "Protect",
            },
            "Auditor": {
                "Inspect",
            },
        }

    def has_capability(
        self,
        authority_name: str,
        capability_name: str,
    ) -> bool:
        return capability_name in self._capabilities.get(
            authority_name,
            set(),
        )


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
    required_capability: str,
) -> AIRProgram:
    return AIRProgram(
        version="USE_YOUR_SUPPORTED_AIR_VERSION",
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(
            TestRequirement(
                capability=required_capability,
            ),
        ),
        authorities=(
            DirectiveAuthority(
                name="Sentinel",
            ),
        ),
        principals=(),
    )


def authorized_capability_test() -> None:
    print("=== Authorized Capability Test ===")

    principal = make_principal(
        authority_name="Sentinel",
    )

    program = make_program(
        required_capability="Observe",
    )

    authority_registry = TestAuthorityRegistry()

    PrincipalCapabilityAuthorizationError.authorize_principal_capabilities(
        principal,
        program,
        authority_registry,
    )

    print(
        "PASS: Sentinel granted the required "
        "Observe capability."
    )


def unauthorized_capability_test() -> None:
    print("\n=== Unauthorized Capability Test ===")

    principal = make_principal(
        authority_name="Sentinel",
    )

    program = make_program(
        required_capability="Erase",
    )

    authority_registry = TestAuthorityRegistry()

    try:
        PrincipalCapabilityAuthorizationError.authorize_principal_capabilities(
            principal,
            program,
            authority_registry,
        )

    except PrincipalCapabilityAuthorizationError as error:
        if "Erase" not in str(error):
            raise AssertionError(
                "The error did not identify the missing "
                "Erase capability."
            )

        print(
            "PASS: Sentinel lacked Erase and "
            "authorization was rejected."
        )

        print(
            f"Authorization message: {error}"
        )

        return

    raise AssertionError(
        "Principal was authorized without the "
        "required Erase capability."
    )


def unrelated_authority_test() -> None:
    print("\n=== Unrelated Authority Test ===")

    principal = make_principal(
        authority_name="Auditor",
    )

    program = make_program(
        required_capability="Inspect",
    )

    authority_registry = TestAuthorityRegistry()

    try:
        PrincipalCapabilityAuthorizationError.authorize_principal_capabilities(
            principal,
            program,
            authority_registry,
        )

    except PrincipalCapabilityAuthorizationError:
        print(
            "PASS: Auditor could not satisfy a directive "
            "restricted to Sentinel."
        )

        return

    raise AssertionError(
        "An unrelated authority satisfied the directive."
    )


def no_requirements_test() -> None:
    print("\n=== No Capability Requirements Test ===")

    principal = make_principal(
        authority_name="Sentinel",
    )

    program = AIRProgram(
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
        principals=(),
    )

    authority_registry = TestAuthorityRegistry()

    PrincipalCapabilityAuthorizationError.authorize_principal_capabilities(
        principal,
        program,
        authority_registry,
    )

    print(
        "PASS: A directive with no capability "
        "requirements required no capability check."
    )


def run_tests() -> None:
    print(
        "ApexForge Principal Capability Authorization\n"
    )

    authorized_capability_test()
    unauthorized_capability_test()
    unrelated_authority_test()
    no_requirements_test()

    print(
        "\nALL PRINCIPAL CAPABILITY TESTS PASSED"
    )


if __name__ == "__main__":
    run_tests()