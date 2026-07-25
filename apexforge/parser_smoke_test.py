from language.parser import (
    BinaryExpressionNode,
    MessageActionNode,
    WhenActionNode,
    parse,
)

import inspect
import language.parser as parser_module

from language.lexer import lex


source = '''
directive Counter {
    state count = 14

    event updated

    cause start {
        path primary @ 1 {
            when count >= 10 {
                message "Threshold reached"
                emit updated
            }
        }
    }
}
'''

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

assert when_action.condition.operator == ">="

assert len(when_action.actions) == 2

assert isinstance(
    when_action.actions[0],
    MessageActionNode,
)


print("WHEN PARSER TEST PASSED")
print(when_action)
