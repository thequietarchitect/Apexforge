# Compiler Smoke Test #

import inspect

from air.model import Fact
from pipeline.execution_pipeline import ExecutionPipeline
from language.lexer import ONE_CHARACTER_TOKENS, TWO_CHARACTER_TOKENS

from language.parser import parse
from language.compiler import compile_directive


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

path = (
    program
    .causal_decisions[0]
    .paths[0]
)

import inspect
import language.compiler as compiler_module

ast_path = node.causes[0].paths[0]

print(
    "COMPILER LOADED FROM:",
    compiler_module.__file__,
)

print(
    "AST actions:",
    len(ast_path.actions),
    ast_path.actions,
)

print(
    "AIR path type:",
    type(path),
)

print(
    "AIR path module:",
    type(path).__module__,
)

print(
    "AIR path signature:",
    inspect.signature(
        type(path)
    ),
)

print(
    "AIR ordered actions:",
    len(path.actions),
    path.actions,
)

print(
    "legacy assignments:",
    path.assignments,
)

print(
    "legacy emits:",
    path.emits,
)

when_air = path.actions[0]


print(
    "AIR action:",
    type(when_air).__name__,
)

print(
    "true AIR actions:",
    len(when_air.actions),
)

print(
    "otherwise AIR actions:",
    len(when_air.otherwise_actions),
)

print(
    "true types:",
    [
        type(action).__name__
        for action in when_air.actions
    ],
)

print(
    "otherwise types:",
    [
        type(action).__name__
        for action
        in when_air.otherwise_actions
    ],
)

print(when_air)


assert (
    type(when_air).__name__
    == "AIRWhenAction"
)

assert len(
    when_air.actions
) == 2

assert len(
    when_air.otherwise_actions
) == 2

assert [
    type(action).__name__
    for action in when_air.actions
] == [
    "StateAssignment",
    "EventEmission",
]

assert [
    type(action).__name__
    for action
    in when_air.otherwise_actions
] == [
    "StateAssignment",
    "EventEmission",
]


print(
    "OTHERWISE COMPILER SMOKE TEST PASSED 💨"
)

pipeline = ExecutionPipeline()
program = pipeline.compile_source(source)

path = program.causal_decisions[0].paths[0]

assert ONE_CHARACTER_TOKENS["+"] == "PLUS"
assert TWO_CHARACTER_TOKENS[">="] == "GTE"

print(path.actions)

print(inspect.signature(Fact))
print(repr(source))

program = pipeline.compile_source(source)

print(program)