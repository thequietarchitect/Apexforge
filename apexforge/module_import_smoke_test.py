"""Smoke test for AFP-P6 module declarations and direct imports."""

from __future__ import annotations

from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from language.project import (
    ProjectCompilationError,
    ProjectModuleError,
    build_project,
)
from runtime.context import ExecutionContext
from runtime.state import StateSnapshot


WORKER_SOURCE = """module app.worker

directive Worker {
    state worker_count = 5
    event worker_done

    cause Work {
        path primary @ 10 {
            add worker_count 2
            emit worker_done
        }
    }
}
"""


CALLER_SOURCE = """module app.caller
import app.worker

directive Caller {
    state caller_count = 1
    event caller_done

    cause Call {
        path primary @ 10 {
            add caller_count 1
            invoke Worker
            add caller_count 1
            emit caller_done
        }
    }
}
"""


CALLER_WITHOUT_IMPORT = """module app.caller

directive Caller {
    state caller_count = 1

    cause Call {
        path primary @ 10 {
            invoke Worker
        }
    }
}
"""


MISSING_IMPORT_SOURCE = """module app.caller
import app.missing

directive Caller {
    state caller_count = 1
}
"""


CYCLE_A_SOURCE = """module cycle.a
import cycle.b

directive A {
    state value_a = 0
}
"""


CYCLE_B_SOURCE = """module cycle.b
import cycle.a

directive B {
    state value_b = 0
}
"""


DUPLICATE_MODULE_A = """module duplicate.name

directive First {
    state first_value = 0
}
"""


DUPLICATE_MODULE_B = """module duplicate.name

directive Second {
    state second_value = 0
}
"""


LEGACY_SOURCE = """directive Legacy {
    state count = 0
}
"""


BAD_BODY_SOURCE = """module app.bad

directive Bad {
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
    project,
) -> ExecutionContext:
    return ExecutionContext(
        state=StateSnapshot.from_program_initials(
            project.program
        ),
        authority=AuthorityEngine.from_grants(
            (
                AuthorityGrant(
                    principal="principal:Caller",
                    capability="directive.invoke:Caller",
                    resource="directive:Caller",
                ),
                AuthorityGrant(
                    principal="principal:Worker",
                    capability="directive.invoke:Worker",
                    resource="directive:Worker",
                ),
            )
        ),
    )


def main() -> None:
    project = build_project(
        {
            "20-Caller.apex": CALLER_SOURCE,
            "10-Worker.apex": WORKER_SOURCE,
        },
        entry="Caller",
    )

    require(
        not project.module_graph.is_legacy,
        "explicit module project was marked as legacy",
    )
    require(
        project.module_graph.order
        == (
            "app.worker",
            "app.caller",
        ),
        "module dependencies were not topologically ordered",
    )
    require(
        project.module_graph.direct_imports(
            "app.caller"
        )
        == (
            "app.worker",
        ),
        "direct import was not recorded",
    )
    require(
        tuple(
            directive.id
            for directive
            in project.program.directives
        )
        == (
            "directive:Worker",
            "directive:Caller",
        ),
        "linked directive order did not follow module dependency order",
    )

    result = project.execute(
        build_context(
            project
        )
    )

    require(
        result.ok,
        f"module project execution failed: "
        f"{result.diagnostics!r}",
    )
    require(
        result.final_state.get_int(
            "caller_count"
        )
        == 3,
        "caller did not resume after imported invocation",
    )
    require(
        result.final_state.get_int(
            "worker_count"
        )
        == 7,
        "imported worker did not execute",
    )
    require(
        tuple(
            event.event
            for event
            in result.delta.events
        )
        == (
            "event:worker_done",
            "event:caller_done",
        ),
        "module execution event order changed",
    )

    visibility_error = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "Caller.apex": (
                    CALLER_WITHOUT_IMPORT
                ),
                "Worker.apex": WORKER_SOURCE,
            },
            entry="Caller",
        ),
        "cross-module invocation without import "
        "must fail",
    )
    require(
        visibility_error.diagnostics[
            0
        ].code
        == "APX-MODULE-008",
        "missing direct import used the wrong code",
    )
    require(
        visibility_error.diagnostics[
            0
        ].span.source_name
        == "Caller.apex",
        "visibility error did not map to caller source",
    )
    require(
        visibility_error.diagnostics[
            0
        ].span.start.line
        == 8,
        "visibility error did not map to invoke line",
    )

    missing_error = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "Caller.apex": (
                    MISSING_IMPORT_SOURCE
                ),
            },
            entry="Caller",
        ),
        "undefined imported module must fail",
    )
    require(
        missing_error.diagnostics[
            0
        ].code
        == "APX-MODULE-006",
        "undefined import used the wrong code",
    )

    cycle_error = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "A.apex": CYCLE_A_SOURCE,
                "B.apex": CYCLE_B_SOURCE,
            }
        ),
        "module cycle must fail",
    )
    require(
        cycle_error.diagnostics[
            0
        ].code
        == "APX-MODULE-007",
        "module cycle used the wrong code",
    )
    require(
        "cycle.a -> cycle.b -> cycle.a"
        in str(
            cycle_error
        ),
        "cycle diagnostic did not contain the cycle path",
    )

    duplicate_error = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "A.apex": DUPLICATE_MODULE_A,
                "B.apex": DUPLICATE_MODULE_B,
            }
        ),
        "duplicate module names must fail",
    )
    require(
        duplicate_error.diagnostics[
            0
        ].code
        == "APX-MODULE-009",
        "duplicate module used the wrong code",
    )
    require(
        len(
            duplicate_error.diagnostics[
                0
            ].related_spans
        )
        == 1,
        "duplicate module diagnostic did not retain "
        "both declarations",
    )

    mixed_error = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "Module.apex": WORKER_SOURCE,
                "Legacy.apex": LEGACY_SOURCE,
            }
        ),
        "mixed explicit and legacy sources must fail",
    )
    require(
        mixed_error.diagnostics[
            0
        ].code
        == "APX-MODULE-005",
        "mixed module mode used the wrong code",
    )

    compilation_error = require_raises(
        ProjectCompilationError,
        lambda: build_project(
            {
                "Bad.apex": BAD_BODY_SOURCE,
            },
            entry="Bad",
        ),
        "bad module body must fail compilation",
    )
    require(
        compilation_error.diagnostics[
            0
        ].span.source_name
        == "Bad.apex",
        "masked module source lost filename provenance",
    )
    require(
        compilation_error.diagnostics[
            0
        ].span.start.line
        == 5,
         "masked module source did not preserve the unexpected-token line",
)

    legacy = build_project(
        {
            "Legacy.apex": LEGACY_SOURCE,
        },
        entry="Legacy",
    )
    require(
        legacy.module_graph.is_legacy,
        "header-free AFP-P4 project lost compatibility",
    )

    print(
        "ApexForge module/import smoke test passed."
    )
    print(
        "Header masking and source positions: PASS"
    )
    print(
        "Direct import visibility: PASS"
    )
    print(
        "Dependency-first module ordering: PASS"
    )
    print(
        "Undefined import rejection: PASS"
    )
    print(
        "Cycle detection: PASS"
    )
    print(
        "Duplicate module rejection: PASS"
    )
    print(
        "Legacy project compatibility: PASS"
    )


if __name__ == "__main__":
    main()