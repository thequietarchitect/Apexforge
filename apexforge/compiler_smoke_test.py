# Compiler Smoke Test #

import inspect

from air.model import Fact
from pipeline.execution_pipeline import ExecutionPipeline
from language.lexer import one_character_expressions, two_character_expressions

source= """directive Counter {
                state count = 14

                event updated

                cause start {
                    path primary @ 1 {
                        set count = count + 1

                        when count >= 10 {
                        message "Threshold reached"
                        emit updated
                        }
                    }
                }
            }"""

pipeline = ExecutionPipeline()
program = pipeline.compile_source(source)

path = program.causal_decisions[0].paths[0]

assert one_character_expressions["+"] == "PLUS"
assert two_character_expressions[">="] == "GTE"

print(path.actions)

print(inspect.signature(Fact))
print(repr(source))

program = pipeline.compile_source(source)

print(program)