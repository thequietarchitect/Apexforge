from air.model import (
    AIRPrincipal,
    AIRProgram,
    DirectiveAuthority,
    PrincipalAuthority,
)

from authority.validator import (
    PrincipalAuthorizationError,
)


def make_program(
    required_authority: str,
) -> AIRProgram:
    return AIRProgram(
        version="1.0",
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        authorities=(
            DirectiveAuthority(
                name=required_authority,
            ),
        ),
        principals=(),
    )


def test_authorized_principal() -> None:
    program = make_program(
        required_authority="Sentinel",
    )

    principal = AIRPrincipal(
        name="Lyra",
        authorities=(
            PrincipalAuthority(
                name="Sentinel",
            ),
        ),
    )

    PrincipalAuthorizationError.authorize_principal(
        principal,
        program,
    )

    print(
        "PASS: Lyra was authorized "
        "with Sentinel authority."
    )


def test_unauthorized_principal() -> None:
    program = make_program(
        required_authority="Sentinel",
    )

    principal = AIRPrincipal(
        name="Lyra",
        authorities=(
            PrincipalAuthority(
                name="Auditor",
            ),
        ),
    )

    try:
       PrincipalAuthorizationError.authorize_principal(
            principal,
            program,
        )

    except PrincipalAuthorizationError as exc:
        print(
            "PASS: Unauthorized principal "
            "was rejected."
        )
        print(exc)
        return

    raise AssertionError(
        "Expected PrincipalAuthorizationError, "
        "but authorization succeeded."
    )


if __name__ == "__main__":
    test_authorized_principal()
    test_unauthorized_principal()