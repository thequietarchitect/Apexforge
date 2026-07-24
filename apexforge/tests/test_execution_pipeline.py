from pipeline.execution_pipeline import ExecutionPipeline
from language.compiler import source

pipeline = ExecutionPipeline()

program = pipeline.compile_source(source)

print("✓ COMPILE")
print(program)