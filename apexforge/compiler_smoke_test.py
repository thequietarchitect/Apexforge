# Compiler Smoke Test #

import inspect

from air.model import Fact
from pipeline.execution_pipeline import ExecutionPipeline

source = '''
directive Counter {
    state count = 2 + 3 * 4

    event updated

    cause start {
        path primary @ 1 {
            add count count + 1
            message "Count: " + count
            emit updated
        }
    }
}
'''

pipeline = ExecutionPipeline()

print(inspect.signature(Fact))
print(repr(source))

program = pipeline.compile_source(source)



print(program)