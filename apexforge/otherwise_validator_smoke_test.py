from dataclasses import replace

from language.compiler import compile_directive
from language.parser import parse
from language.validation.runtime_validator import RuntimeValidator


source = """
directive Counter {
    state count = 2

    event updated

    cause start {
        path primary @ 1 {
            when count >= 10 {
                add count 5
                message "High count"
                emit updated
            }
            otherwise {
                add count 1
                message "Low count"
                emit updated
            }
        }
    }
}
"""


node = parse(source)
program = compile_directive(node)

decision = program.causal_decisions[0]
path = decision.paths[0]
when_air = path.actions[0]




print(
    "true AIR actions:",
    len(when_air.actions),
)

print(
    "otherwise AIR actions:",
    len(when_air.otherwise_actions),
)


# ------------------------------------------------------------------
# Valid-program test
# ------------------------------------------------------------------

verified_program = RuntimeValidator().validate(
    program
)

print(
    "validated result:",
    type(verified_program).__name__,
)

assert (
    type(verified_program).__name__
    == "VerifiedAIRProgram"
)


# ------------------------------------------------------------------
# Negative test:
# Deliberately corrupt only the otherwise branch.
# The validator must find the undefined state.
# ------------------------------------------------------------------

bad_false_assignment = replace(
    when_air.otherwise_actions[0],
    state="state:missing",
)

bad_when = replace(
    when_air,
    otherwise_actions=(
        bad_false_assignment,
        *when_air.otherwise_actions[1:],
    ),
)

bad_path = replace(
    path,
    actions=(
        bad_when,
        *path.actions[1:],
    ),
)

bad_decision = replace(
    decision,
    paths=(
        bad_path,
        *decision.paths[1:],
    ),
)

bad_program = replace(
    program,
    causal_decisions=(
        bad_decision,
        *program.causal_decisions[1:],
    ),
)


try:
    RuntimeValidator().validate(
        bad_program
    )
except Exception as exc:
    print(
        "expected rejection:",
        type(exc).__name__,
    )

    print(
        "message:",
        str(exc),
    )

    assert (
        type(exc).__name__
        == "UndefinedReferenceError"
    )
else:
    raise AssertionError(
        "Validator accepted an undefined state "
        "inside otherwise_actions."
    )


print(
    "OTHERWISE VALIDATOR SMOKE TEST PASSED 💨"
)