from pipeline.execution_pipeline import ExecutionPipeline
from runtime.context import ExecutionContext

source = '''
directive Counter {
    state count = 2 + 3 * 4

    event updated

    cause start {
        path primary @ 1 {
            set count = count + 1
            message "Count: " + count
            emit updated
        }
    }
}
'''


# ----------------------------------------------------------------------
# Test authority
# ----------------------------------------------------------------------

class AllowAllAuthority:
    def allows(self, check):
        return True


# ----------------------------------------------------------------------
# Test runtime state
# ----------------------------------------------------------------------

class TestState:
    def __init__(self):
        self.applied_deltas = []

    def apply(self, delta):
        self.applied_deltas.append(delta)
        return self


# ----------------------------------------------------------------------
# Runtime context
# ----------------------------------------------------------------------

context = ExecutionContext(
    state=TestState(),
    authority=AllowAllAuthority(),
)


# ----------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------

pipeline = ExecutionPipeline()
result = pipeline.execute_source(
    source,
    context,
)

print("===================================")
print(" ApexForge Pipeline Verification")
print("===================================")

try:

    print("\n[1] Compiling...")

    program = pipeline.compile_source(source)

    print("EVENT DEFINITIONS:")
    for event in program.events:
            print(
                "id=", getattr(event, "id", None),
                "name=", getattr(event, "name", None),
    )

    print("EMISSIONS:")
    for decision in program.causal_decisions:
        for path in decision.paths:
            for emission in path.emits:
                print(
                    "path=", path.id,
                    "event=", emission.event,
            )

    print("PASS")
    print(program)


    print("\n[2] Validating...")

    verified = pipeline.verify_source(source)

    print("PASS")
    print(type(verified).__name__)


    print("\n[3] Executing...")

    result = pipeline.execute_source(
        source,
        context,
    )

    print("PASS")


    print("\n========== RESULT ==========")

    print("Final State:")
    print(result.final_state)

    print()

    print("Delta:")
    print(result.delta)

    print()

    print("Diagnostics:")
    print(result.diagnostics)

    print()

    print("Trace:")
    print(result.trace)

    print()

    print("SUCCESS!")
    print("Pipeline completed successfully.")

except Exception as exc:

    print("\nFAILED")

    print(type(exc).__name__)
    print(exc)

    print("OK:", result.ok)
    print("Diagnostics:", result.diagnostics)
    print("Delta:", result.delta)
    print("Final state:", result.final_state)
    print("Events:", result.delta.events)

    raise