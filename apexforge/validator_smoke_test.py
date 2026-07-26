from pipeline.execution_pipeline import ExecutionPipeline

source = '''
directive Counter {
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
}
'''

pipeline = ExecutionPipeline()

program = pipeline.compile_source(source)

verified = pipeline.verify_source(source)

print(type(verified).__name__)
print("WHEN VALIDATION PASSED")