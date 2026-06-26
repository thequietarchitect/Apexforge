from air.serialization import load_air_json, save_air_json
from language.compiler import compile_source
from workflow.air_runner import run_air_with_invocation_report

source = """
directive Sentinel {
    state Awareness = 0
    event SentinelObservation

    cause Observation {
        path Investigate @ 80 {
            invoke AEGIS
            invoke Gravitas
            message "Investigation initiated."
            add Awareness 3
            emit SentinelObservation
        }
    }
}
"""

program = compile_source(source)

save_air_json(
    program,
    "apexforge/exports/invoke_test.air.json",
)

loaded = load_air_json(
    "apexforge/exports/invoke_test.air.json",
)

result, invocations = run_air_with_invocation_report(loaded)

print(result.ok)
print(result.final_state.get_int("state:Awareness"))
print(invocations)