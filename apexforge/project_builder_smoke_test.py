"""Smoke test for the ApexForge multi-source project builder."""

from __future__ import annotations

from air.model import AIRProgram
from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from language.project import (
    ProjectCompilationError,
    ProjectEntryPointError,
    ProjectLinkError,
    ProjectValidationError,
    build_project,
)
from runtime.context import ExecutionContext
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


UNDEFINED_INVOCATION_SOURCE = """
directive BrokenCaller {
    state count = 0

    cause BrokenFlow {
        path primary @ 10 {
            invoke MissingDirective
        }
    }
}
"""


INVALID_SYNTAX_SOURCE = """
directive BrokenSyntax {
    state count =
}
"""


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(
            message
        )


def require_raises(
    expected_type: type[BaseException],
    function,
    message: str,
) -> BaseException:
    try:
        function()
    except expected_type as exc:
        return exc

    raise AssertionError(
        message
    )


def build_context(
    program: AIRProgram,
) -> ExecutionContext:
    return ExecutionContext(
        state=StateSnapshot.from_program_initials(
            program
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


def main() -> None:
    # Deliberately supply Caller before Callee even though filename sorting will
    # place Callee first. The explicit entry keeps execution semantics stable.
    first = build_project(
        {
            "20-Caller.apex": CALLER_SOURCE,
            "10-Callee.apex": CALLEE_SOURCE,
        },
        entry="Caller",
    )

    require(
        tuple(
            unit.name
            for unit in first.source_units
        ) == (
            "10-Callee.apex",
            "20-Caller.apex",
        ),
        "project builder did not normalize source order",
    )
    require(
        first.entry_directive
        == "directive:Caller",
        "project builder did not canonicalize the entry directive",
    )
    require(
        first.verified.program
        is first.program,
        "project build did not preserve the canonical verified wrapper",
    )

    result = first.execute(
        build_context(
            first.program
        )
    )

    require(
        result.ok,
        f"project execution failed: {result.diagnostics!r}",
    )
    require(
        result.final_state.get_int(
            "caller_count"
        ) == 3,
        "caller did not resume after project-level invocation",
    )
    require(
        result.final_state.get_int(
            "callee_count"
        ) == 7,
        "callee did not execute inside the built project",
    )
    require(
        tuple(
            event.event
            for event in result.delta.events
        ) == (
            "event:callee_done",
            "event:caller_done",
        ),
        "project runtime event order is not deterministic",
    )

    # Reversing source insertion order must produce the same linked artifact.
    second = build_project(
        {
            "10-Callee.apex": CALLEE_SOURCE,
            "20-Caller.apex": CALLER_SOURCE,
        },
        entry="directive:Caller",
    )

    require(
        tuple(
            directive.id
            for directive in first.program.directives
        )
        == tuple(
            directive.id
            for directive in second.program.directives
        ),
        "source insertion order changed linked directive ordering",
    )
    require(
        tuple(
            directive.order
            for directive in first.program.directives
        )
        == tuple(
            directive.order
            for directive in second.program.directives
        ),
        "source insertion order changed global directive orders",
    )

    # Two different filenames containing the same directive must fail linking.
    require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "A.apex": CALLEE_SOURCE,
                "B.apex": CALLEE_SOURCE,
            },
            entry="Callee",
        ),
        "project builder must reject duplicate linked declarations",
    )

    validation_error = require_raises(
        ProjectValidationError,
        lambda: build_project(
            {
                "BrokenCaller.apex": (
                    UNDEFINED_INVOCATION_SOURCE
                ),
            },
            entry="BrokenCaller",
        ),
        "undefined cross-source invocation must fail validation",
    )

    require(
        "MissingDirective" in str(
            validation_error
        ),
        "validation failure did not retain the undefined target",
    )

    compilation_error = require_raises(
        ProjectCompilationError,
        lambda: build_project(
            {
                "BrokenSyntax.apex": (
                    INVALID_SYNTAX_SOURCE
                ),
            },
            entry="BrokenSyntax",
        ),
        "syntax failure must stop project construction",
    )

    require(
        "BrokenSyntax.apex" in str(
            compilation_error
        ),
        "compilation failure did not identify its source filename",
    )

    require_raises(
        ProjectEntryPointError,
        lambda: build_project(
            {
                "Callee.apex": CALLEE_SOURCE,
            },
            entry="NotPresent",
        ),
        "project builder must reject an undefined entry directive",
    )

    # A failed construction returns no partially executable ProjectBuild.
    partial = None

    try:
        partial = build_project(
            {
                "BrokenSyntax.apex": (
                    INVALID_SYNTAX_SOURCE
                ),
            }
        )
    except ProjectCompilationError:
        pass

    require(
        partial is None,
        "failed project construction exposed a partial build artifact",
    )

    print(
        "ApexForge project builder smoke test passed."
    )
    print(
        "Multi-source compile and link: PASS"
    )
    print(
        "Cross-file invocation execution: PASS"
    )
    print(
        "Source-order determinism: PASS"
    )
    print(
        "Filename-aware compilation errors: PASS"
    )
    print(
        "Link and validation failure isolation: PASS"
    )
    print(
        "Entry directive resolution: PASS"
    )


if __name__ == "__main__":
    main()