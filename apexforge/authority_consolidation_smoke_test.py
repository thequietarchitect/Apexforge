"""Focused smoke test for canonical authority ownership and execution."""

from __future__ import annotations

from air.model import (
    AuthorityCheck as AirAuthorityCheck,
    AuthorityGrant as AirAuthorityGrant,
    Principal as AirPrincipal,
)
from authority.engine import AuthorityEngine
from authority.model import (
    AuthorityCheck,
    AuthorityGrant,
    Principal,
)
from language.compiler import compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.context import ExecutionContext
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot

import sys
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
LEGACY_AIR_FILE = PROJECT_ROOT / "apexforge_air.py"


# Make both layouts importable:
# ApexForge/apexforge_air.py
# ApexForge/apexforge/air, runtime, causality, etc.
for import_path in (
    PROJECT_ROOT,
    PACKAGE_DIR,
):
    import_path_text = str(import_path)


SOURCE = """
directive Counter {
    state count = 2
    event updated

    cause start {
        path primary @ 1 {
            add count 1
            message "Count updated"
            emit updated
        }
    }
}
"""


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    require(
        AirPrincipal is Principal,
        "air.model.Principal must re-export authority.model.Principal",
    )
    require(
        AirAuthorityCheck is AuthorityCheck,
        "air.model.AuthorityCheck must re-export "
        "authority.model.AuthorityCheck",
    )
    require(
        AirAuthorityGrant is AuthorityGrant,
        "air.model.AuthorityGrant must re-export "
        "authority.model.AuthorityGrant",
    )

    exact_grant = AuthorityGrant(
        principal="principal:Counter",
        capability="directive.invoke:Counter",
        resource="directive:Counter",
    )

    engine = AuthorityEngine.from_grants(
        (exact_grant,)
    )

    require(
        engine.check(
            principal="principal:Counter",
            capability="directive.invoke:Counter",
            resource="directive:Counter",
        ),
        "matching grant must allow",
    )
    require(
        not engine.check(
            principal="principal:Other",
            capability="directive.invoke:Counter",
            resource="directive:Counter",
        ),
        "wrong principal must deny",
    )
    require(
        not engine.check(
            principal="principal:Counter",
            capability="directive.invoke:Other",
            resource="directive:Counter",
        ),
        "wrong capability must deny",
    )
    require(
        not engine.check(
            principal="principal:Counter",
            capability="directive.invoke:Counter",
            resource="directive:Other",
        ),
        "wrong resource must deny",
    )

    program = compile_source(SOURCE)
    verified = RuntimeValidator().validate(program)

    check = program.authority_checks[0]
    runtime_authority = AuthorityEngine.from_grants(
        (
            AuthorityGrant(
                principal=check.principal,
                capability=check.capability,
                resource=check.resource,
            ),
        )
    )

    initial_state = StateSnapshot.from_mapping(
        {
            "state:count": 2,
        }
    )

    allowed = RuntimeEngine().execute(
        verified,
        ExecutionContext(
            state=initial_state,
            authority=runtime_authority,
        ),
    )

    require(
        allowed.ok,
        f"authorized execution failed: {allowed.diagnostics}",
    )
    require(
        allowed.final_state.get_int("state:count") == 3,
        "authorized execution must apply the selected path",
    )
    require(
        len(allowed.delta.events) == 1,
        "authorized execution must emit one event",
    )

    denied = RuntimeEngine().execute(
        verified,
        ExecutionContext(
            state=initial_state,
            authority=AuthorityEngine(),
        ),
    )

    require(
        not denied.ok,
        "empty authority engine must deny execution",
    )
    require(
        denied.final_state.get_int("state:count") == 2,
        "denied execution must preserve the initial state",
    )
    require(
        denied.delta.is_empty,
        "denied execution must produce an empty delta",
    )

    print("Authority consolidation smoke test passed.")
    print("Canonical identities: PASS")
    print("Exact grant: PASS")
    print("Wrong principal/capability/resource denial: PASS")
    print("Authorized RuntimeEngine execution: PASS")
    print("Denied execution is transactional: PASS")


if __name__ == "__main__":
    main()