"""Focused canonical-ID coverage for AIRVerifier."""

from air.expressions import AIRIntegerLiteral
from air.model import AIRDirective, AIRProgram, StateDefinition
from air.types import AIR_VERSION
from air.verify import AIRVerifier
from authority.model import AuthorityCheck, Principal


def program_with(
    *principals,
    states=(),
    authority_checks=(),
    directives=(),
):
    return AIRProgram(
        version=AIR_VERSION,
        states=states,
        events=(),
        authority_checks=authority_checks,
        causal_decisions=(),
        directives=directives,
        requirements=(),
        principals=principals,
    )


# Canonical Principal values verify without legacy .name access.
canonical = AIRVerifier().verify(
    program_with(
        Principal(
            id="principal:Operator",
            display_name="Operator",
        )
    )
)
assert canonical.ok


# Canonical IDs, not display names, own principal uniqueness.
duplicate = AIRVerifier().verify(
    program_with(
        Principal(
            id="principal:Shared",
            display_name="First",
        ),
        Principal(
            id="principal:Shared",
            display_name="Second",
        ),
    )
)
duplicate_diagnostics = tuple(
    item
    for item in duplicate.diagnostics
    if item.code == "AIR000"
)
assert len(duplicate_diagnostics) == 1
assert duplicate_diagnostics[0].message == (
    "duplicate principal id: principal:Shared"
)
assert duplicate_diagnostics[0].node_id == "principal:Shared"


# Equal human-readable names do not collapse distinct canonical IDs.
same_display = AIRVerifier().verify(
    program_with(
        Principal(
            id="principal:First",
            display_name="Shared",
        ),
        Principal(
            id="principal:Second",
            display_name="Shared",
        ),
    )
)
assert same_display.ok


# Canonical states verify without requiring a legacy .name.
canonical_state = AIRVerifier().verify(
    program_with(
        states=(
            StateDefinition(
                id="state:Ready",
                initial=AIRIntegerLiteral(0),
            ),
        )
    )
)
assert canonical_state.ok


# Distinct state objects with the same canonical ID collide.
state_first = StateDefinition(
    id="state:Shared",
    initial=AIRIntegerLiteral(0),
)
state_second = StateDefinition(
    id="state:Shared",
    initial=AIRIntegerLiteral(1),
)
assert state_first is not state_second

duplicate_state = AIRVerifier().verify(
    program_with(
        states=(state_first, state_second),
    )
)
state_diagnostics = tuple(
    item
    for item in duplicate_state.diagnostics
    if item.code == "AIR000"
)
assert len(state_diagnostics) == 1
assert state_diagnostics[0].message == (
    "duplicate state id: state:Shared"
)
assert state_diagnostics[0].node_id == "state:Shared"


# Existing directive duplicate-ID diagnostics remain unchanged.
principal = Principal(
    id="principal:Root",
    display_name="Root",
)
directive_first = AIRDirective(
    id="directive:Main",
    name="Main",
    principal=principal.id,
    authority_checks=(),
    causal_decisions=(),
)
directive_second = AIRDirective(
    id="directive:Main",
    name="Main",
    principal=principal.id,
    authority_checks=(),
    causal_decisions=(),
)
assert directive_first is not directive_second

other_declaration = AIRVerifier().verify(
    program_with(
        principal,
        directives=(directive_first, directive_second),
    )
)
other_diagnostics = tuple(
    item
    for item in other_declaration.diagnostics
    if item.code == "AIR000"
)
assert len(other_diagnostics) == 1
assert other_diagnostics[0].message == (
    "duplicate directive id: directive:Main"
)
assert other_diagnostics[0].node_id == "directive:Main"


# AuthorityCheck verifies through canonical ID without requiring .name.
check_first = AuthorityCheck(
    id="auth:Shared",
    principal=principal.id,
    capability="directive.invoke:Main",
    resource="directive:Main",
)
check_second = AuthorityCheck(
    id="auth:Shared",
    principal=principal.id,
    capability="directive.invoke:Other",
    resource="directive:Other",
)
assert check_first is not check_second

duplicate_check = AIRVerifier().verify(
    program_with(
        principal,
        authority_checks=(check_first, check_second),
    )
)
check_diagnostics = tuple(
    item
    for item in duplicate_check.diagnostics
    if item.code == "AIR000"
)
assert len(check_diagnostics) == 1
assert check_diagnostics[0].message == (
    "duplicate authority_check id: auth:Shared"
)
assert check_diagnostics[0].node_id == "auth:Shared"


print("AIR verifier canonical-ID smoke test passed.")
