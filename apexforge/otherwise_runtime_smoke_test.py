from types import SimpleNamespace

from language.compiler import compile_directive
from language.parser import parse
from runtime.context import ExecutionContext
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from language.validation.runtime_validator import RuntimeValidator


class AllowAllAuthority:
    def allows(
        self,
        check,
    ) -> bool:
        return True


def build_initial_state(
    program,
) -> StateSnapshot:
    """
    Temporary adapter while compiled state initializers
    remain AIR literal objects.
    """

    primitive_initial_program = SimpleNamespace(
        states=tuple(
            SimpleNamespace(
                id=state_definition.id,
                initial=getattr(
                    state_definition.initial,
                    "value",
                    state_definition.initial,
                ),
            )
            for state_definition in program.states
        )
    )

    return StateSnapshot.from_program_initials(
        primitive_initial_program
    )


def run_case(
    initial_count: int,
):
    source = f"""
directive Counter {{
    state count = {initial_count}

    event updated

    cause start {{
        path primary @ 1 {{
            when count >= 10 {{
                add count 5
                message "High count"
                emit updated
            }}
            otherwise {{
                add count 1
                message "Low count"
                emit updated
            }}
        }}
    }}
}}
"""

    node = parse(source)
    program = compile_directive(node)

    verified_program = RuntimeValidator().validate(
        program
    )

    context = ExecutionContext(
        state=build_initial_state(
            program
        ),
        authority=AllowAllAuthority(),
    )

    return RuntimeEngine().execute(
        verified_program,
        context,
    )


# ------------------------------------------------------------------
# True branch
# ------------------------------------------------------------------

true_result = run_case(
    initial_count=12,
)

print("\nTRUE CASE")
print("ok:", true_result.ok)
print(
    "final count:",
    true_result.final_state.get_int(
        "state:count"
    ),
)
print(
    "assignments:",
    len(true_result.delta.assignments),
)
print(
    "events:",
    len(true_result.delta.events),
)
print(true_result.trace.render())


assert true_result.ok

assert (
    true_result.final_state.get_int(
        "state:count"
    )
    == 17
)

assert len(
    true_result.delta.assignments
) == 1

assert len(
    true_result.delta.events
) == 1


# ------------------------------------------------------------------
# Otherwise branch
# ------------------------------------------------------------------

false_result = run_case(
    initial_count=2,
)

print("\nOTHERWISE CASE")
print("ok:", false_result.ok)
print(
    "final count:",
    false_result.final_state.get_int(
        "state:count"
    ),
)
print(
    "assignments:",
    len(false_result.delta.assignments),
)
print(
    "events:",
    len(false_result.delta.events),
)
print(false_result.trace.render())


assert false_result.ok

assert (
    false_result.final_state.get_int(
        "state:count"
    )
    == 3
)

assert len(
    false_result.delta.assignments
) == 1

assert len(
    false_result.delta.events
) == 1


print(
    "\nOTHERWISE RUNTIME SMOKE TEST PASSED 💨"
)