from language.parser import (
    parse,
    WhenActionNode,
    BinaryExpressionNode,
    AddActionNode,
    MessageActionNode,
    EmitActionNode,
)
import inspect
import language.parser as parser_module

from language.lexer import lex


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
}"""


node = parse(source)

when_action = (
    node.causes[0]
    .paths[0]
    .actions[0]
)

print(type(when_action).__name__)

print(
    "true actions:",
    len(when_action.actions),
)

print(
    "otherwise actions:",
    len(
        when_action.otherwise_actions
    ),
)

print(when_action)

for index, token in enumerate(lex(source)):
    print(
        index,
        token.kind,
        repr(token.value),
    )

print(
    "PARSER LOADED FROM:",
    parser_module.__file__,
)

print("SOURCE:")
print(repr(source))

node = parse(source)

path = node.causes[0].paths[0]
when_action = path.actions[0]

assert isinstance(
    when_action,
    WhenActionNode,
)

assert isinstance(
    when_action.condition,
    BinaryExpressionNode,
)

assert len(when_action.actions) == 3
assert len(when_action.otherwise_actions) == 3

print(
    "actual type:",
    type(when_action),
)

print(
    "expected type:",
    WhenActionNode,
)

print(
    "actual module:",
    type(when_action).__module__,
)

print(
    "expected module:",
    WhenActionNode.__module__,
)

print(
    "same class object:",
    type(when_action) is WhenActionNode,
)

print(
    "condition actual:",
    type(when_action.condition),
)

print(
    "condition expected:",
    BinaryExpressionNode,
)

print(
    "condition module:",
    type(when_action.condition).__module__,
    BinaryExpressionNode.__module__,
)

print("OTHERWISE PARSER SMOKE TEST PASSED 💨")