"""AFP-P7.3 project, module, diagnostic, and regression smoke test."""

from __future__ import annotations

from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from language.project import (
    ProjectModuleError,
    ProjectValidationError,
    build_project,
)
from runtime.context import ExecutionContext
from runtime.state import StateSnapshot


CORE_SOURCE = """module math.core

function double(value) {
    return value * 2
}
"""


ADJUST_SOURCE = """module math.adjust
import math.core

function increase(value) {
    let doubled = double(value)
    return doubled + 1
}
"""


COUNTER_SOURCE = """module app.counter
import math.adjust

directive Counter {
    state count = 3

    cause update {
        path normal @ 10 {
            set count = increase(count)
        }
    }
}
"""


COUNTER_WITHOUT_IMPORT = """module app.counter

directive Counter {
    state count = 3

    cause update {
        path normal @ 10 {
            set count = increase(count)
        }
    }
}
"""


TRANSITIVE_CALL_SOURCE = """module app.transitive
import math.adjust

directive Transitive {
    state count = 3

    cause update {
        path normal @ 10 {
            set count = double(count)
        }
    }
}
"""


UNDEFINED_CALL_SOURCE = """module app.broken

directive Broken {
    state count = 3

    cause update {
        path normal @ 10 {
            set count = missing(count)
        }
    }
}
"""


ARITY_CALL_SOURCE = """module app.arity
import math.core

directive Arity {
    state count = 3

    cause update {
        path normal @ 10 {
            set count = double(count, count)
        }
    }
}
"""


RECURSIVE_SOURCE = """module math.loop

function loop(value) {
    return loop(value)
}
"""


WORKER_SOURCE = """module app.worker

directive Worker {
    state worker_count = 1

    cause work {
        path normal @ 10 {
            add worker_count 1
        }
    }
}
"""


CALLER_WITHOUT_WORKER_IMPORT = """module app.caller

directive Caller {
    state caller_count = 1

    cause call {
        path normal @ 10 {
            invoke Worker
        }
    }
}
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as exc:
        return exc
    raise AssertionError(message)


def context_for(project, directive_name: str) -> ExecutionContext:
    return ExecutionContext(
        state=StateSnapshot.from_program_initials(project.program),
        authority=AuthorityEngine.from_grants(
            (
                AuthorityGrant(
                    principal=f"principal:{directive_name}",
                    capability=f"directive.invoke:{directive_name}",
                    resource=f"directive:{directive_name}",
                ),
            )
        ),
    )


def main() -> None:
    project = build_project(
        {
            "30-Counter.apex": COUNTER_SOURCE,
            "20-Adjust.apex": ADJUST_SOURCE,
            "10-Core.apex": CORE_SOURCE,
        },
        entry="Counter",
    )

    require(
        project.module_graph.order
        == (
            "math.core",
            "math.adjust",
            "app.counter",
        ),
        "function modules were not dependency ordered",
    )
    require(
        tuple(function.id for function in project.program.functions)
        == (
            "function:double",
            "function:increase",
        ),
        "linked function order did not follow module order",
    )

    function_calls = tuple(
        entry
        for entry in project.source_map.entries
        if entry.kind == "function_call"
    )
    require(
        tuple(entry.reference for entry in function_calls)
        == (
            "double",
            "increase",
        ),
        "function call source-map entries were not preserved",
    )

    result = project.execute(
        context_for(project, "Counter")
    )
    require(result.ok, f"P7 project execution failed: {result.diagnostics!r}")
    require(
        result.final_state.get_int("count") == 7,
        "cross-module nested function execution returned the wrong value",
    )

    missing_import = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "Counter.apex": COUNTER_WITHOUT_IMPORT,
                "Adjust.apex": ADJUST_SOURCE,
                "Core.apex": CORE_SOURCE,
            },
            entry="Counter",
        ),
        "cross-module function call without import must fail",
    )
    require(
        missing_import.diagnostics[0].code == "APX-MODULE-008",
        "function visibility failure used the wrong module code",
    )
    require(
        missing_import.diagnostics[0].span.source_name == "Counter.apex"
        and missing_import.diagnostics[0].span.start.line == 8,
        "function visibility diagnostic did not map to the call site",
    )

    transitive_import = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "Transitive.apex": TRANSITIVE_CALL_SOURCE,
                "Adjust.apex": ADJUST_SOURCE,
                "Core.apex": CORE_SOURCE,
            },
            entry="Transitive",
        ),
        "transitive import must not expose an unimported function",
    )
    require(
        transitive_import.diagnostics[0].code == "APX-MODULE-008",
        "transitive function visibility failure used the wrong code",
    )

    undefined_call = require_raises(
        ProjectValidationError,
        lambda: build_project(
            {"Broken.apex": UNDEFINED_CALL_SOURCE},
            entry="Broken",
        ),
        "undefined function call must fail linked validation",
    )
    require(
        undefined_call.diagnostics[0].code == "APX-VALIDATE-003",
        "undefined function used the wrong validation code",
    )
    require(
        undefined_call.diagnostics[0].span.source_name == "Broken.apex"
        and undefined_call.diagnostics[0].span.start.line == 8,
        "undefined function diagnostic did not map to the call site",
    )

    arity_call = require_raises(
        ProjectValidationError,
        lambda: build_project(
            {
                "Arity.apex": ARITY_CALL_SOURCE,
                "Core.apex": CORE_SOURCE,
            },
            entry="Arity",
        ),
        "wrong function arity must fail linked validation",
    )
    require(
        arity_call.diagnostics[0].code == "APX-VALIDATE-004",
        "wrong function arity used the wrong validation code",
    )
    require(
        arity_call.diagnostics[0].span.source_name == "Arity.apex"
        and arity_call.diagnostics[0].span.start.line == 9,
        "arity diagnostic did not map to the call site",
    )

    recursive = require_raises(
        ProjectValidationError,
        lambda: build_project(
            {"Loop.apex": RECURSIVE_SOURCE}
        ),
        "recursive function must fail project validation",
    )
    require(
        recursive.diagnostics[0].code == "APX-VALIDATE-005",
        "recursive function used the wrong validation code",
    )
    require(
        recursive.diagnostics[0].span.source_name == "Loop.apex"
        and recursive.diagnostics[0].span.start.line == 3,
        "recursion diagnostic did not map to the function declaration",
    )

    directive_visibility = require_raises(
        ProjectModuleError,
        lambda: build_project(
            {
                "Caller.apex": CALLER_WITHOUT_WORKER_IMPORT,
                "Worker.apex": WORKER_SOURCE,
            },
            entry="Caller",
        ),
        "P6 directive visibility regression was not rejected",
    )
    require(
        directive_visibility.diagnostics[0].code == "APX-MODULE-008",
        "P6 directive visibility code changed",
    )

    print("AFP-P7.3 project integration smoke test passed.")
    print("Cross-module function execution: PASS")
    print("Direct function import visibility: PASS")
    print("Transitive-import isolation: PASS")
    print("Function call source mapping: PASS")
    print("Undefined-function diagnostics: PASS")
    print("Arity diagnostics: PASS")
    print("Recursion diagnostics: PASS")
    print("P6 directive visibility regression: PASS")


if __name__ == "__main__":
    main()