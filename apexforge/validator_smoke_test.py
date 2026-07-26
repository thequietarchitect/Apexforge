from types import SimpleNamespace

from authority.engine import AuthorityEngine
from language.compiler import compile_directive
from language.validation.runtime_validator import RuntimeValidator
from language.parser import parse
from air.model import VerifiedAIRProgram
from authority.model import AuthorityGrant
from pipeline.execution_pipeline import ExecutionPipeline
from runtime.context import ExecutionContext
from runtime.state import StateSnapshot
from runtime.engine import RuntimeEngine
import inspect

source = """
directive Counter {
    state count = 9

    event updated

    cause start {
        path primary @ 1 {
            set count = count + 1

            when count >= 10 {
                add count 5
                message "Threshold reached"
                emit updated
            }
        }
    }
}"""

print(
    inspect.signature(
        AuthorityGrant
    )
)

node = parse(source)

program = compile_directive(node)

verified_program = RuntimeValidator().validate(
    program
)


pipeline = ExecutionPipeline()



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

initial_state = StateSnapshot.from_program_initials(
    primitive_initial_program
)



class AllowAllAuthority:
    def allows(
        self,
        check,
    ) -> bool:
        return True

execution_context = ExecutionContext(
    state=initial_state,
    authority=AllowAllAuthority(),
)

result = RuntimeEngine().execute(
    verified_program,
    execution_context,
)


print(
    "initial count:",
    initial_state.get_int(
        "state:count"
    ),
)

print("ok:", result.ok)

print(
    "final count:",
    result.final_state.get_int(
        "state:count"
    ),
)

print(
    "assignments:",
    len(result.delta.assignments),
)

print(
    "events:",
    len(result.delta.events),
)

print(result.trace.render())