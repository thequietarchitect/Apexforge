"""Smoke test for deterministic ApexForge AIR program linking."""

from __future__ import annotations

from dataclasses import replace

from air.linker import (
    AIRProgramLinker,
    DuplicateLinkDefinitionError,
    EmptyLinkError,
    IncompatibleAIRVersionError,
    link_programs,
)
from air.model import AIRProgram
from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from language.compiler import compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.context import ExecutionContext
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot


CALLER_SOURCE = """
directive Caller {
    state caller_count = 1
    event caller_done

    cause CallerFlow {
        path primary @ 10 {
            add caller_count 1
            invoke Callee
            add caller_count 1
            emit caller_done
        }
    }
}
"""


CALLEE_SOURCE = """
directive Callee {
    state callee_count = 5
    event callee_done

    cause CalleeFlow {
        path primary @ 10 {
            add callee_count 2
            emit callee_done
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


def require_raises(
    expected_type: type[BaseException],
    function,
    message: str,
) -> None:
    try:
        function()
    except expected_type:
        return

    raise AssertionError(message)


def compile_program(
    source: str,
) -> AIRProgram:
    program = compile_source(source)

    require(
        isinstance(program, AIRProgram),
        "compile_source must return AIRProgram for directive source",
    )

    return program


def main() -> None:
    caller = compile_program(CALLER_SOURCE)
    callee = compile_program(CALLEE_SOURCE)

    # Both separately compiled directives begin at local order zero.
    require(
        caller.directives[0].order == 0,
        "caller must begin with local directive order zero",
    )
    require(
        callee.directives[0].order == 0,
        "callee must begin with local directive order zero",
    )

    linked = link_programs(
        caller,
        callee,
    )

    require(
        tuple(
            directive.id
            for directive in linked.directives
        ) == (
            "directive:Caller",
            "directive:Callee",
        ),
        "linked directive order is not deterministic",
    )
    require(
        tuple(
            directive.order
            for directive in linked.directives
        ) == (
            0,
            1,
        ),
        "linker did not assign unique global directive orders",
    )
    require(
        len(linked.states) == 2,
        "linker did not preserve both state declarations",
    )
    require(
        len(linked.causal_decisions) == 2,
        "linker did not preserve both causal decisions",
    )

    # The caller's invocation is unresolved in its isolated compilation unit,
    # but becomes valid after the callee unit is linked.
    verified = RuntimeValidator().validate(
        linked
    )

    context = ExecutionContext(
        state=StateSnapshot.from_program_initials(
            linked
        ),
        authority=AuthorityEngine.from_grants(
            (
                AuthorityGrant(
                    principal="principal:Caller",
                    capability="directive.invoke:Caller",
                    resource="directive:Caller",
                ),
                AuthorityGrant(
                    principal="principal:Callee",
                    capability="directive.invoke:Callee",
                    resource="directive:Callee",
                ),
            )
        ),
    )

    result = RuntimeEngine().execute(
        verified,
        context,
        entry_directives=(
            "Caller",
        ),
    )

    require(
        result.ok,
        f"linked program execution failed: {result.diagnostics!r}",
    )
    require(
        result.final_state.get_int(
            "caller_count"
        ) == 3,
        "caller did not continue after nested invocation",
    )
    require(
        result.final_state.get_int(
            "callee_count"
        ) == 7,
        "callee did not execute against the linked state",
    )
    require(
        tuple(
            event.event
            for event in result.delta.events
        ) == (
            "event:callee_done",
            "event:caller_done",
        ),
        "linked nested event order is not deterministic",
    )

    require_raises(
        DuplicateLinkDefinitionError,
        lambda: AIRProgramLinker().link(
            (
                caller,
                caller,
            )
        ),
        "linker must reject duplicate global definitions",
    )

    incompatible = replace(
        callee,
        version="999.0",
    )
    require_raises(
        IncompatibleAIRVersionError,
        lambda: link_programs(
            caller,
            incompatible,
        ),
        "linker must reject incompatible AIR versions",
    )

    require_raises(
        EmptyLinkError,
        lambda: AIRProgramLinker().link(()),
        "linker must reject an empty link set",
    )

    print(
        "AIR program linker smoke test passed."
    )
    print(
        "Cross-directive resolution: PASS"
    )
    print(
        "Global directive ordering: PASS"
    )
    print(
        "Linked runtime execution: PASS"
    )
    print(
        "Duplicate collision rejection: PASS"
    )
    print(
        "Version mismatch rejection: PASS"
    )


if __name__ == "__main__":
    main()