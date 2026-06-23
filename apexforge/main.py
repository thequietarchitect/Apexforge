"""ApexForge executable entrypoint."""

from __future__ import annotations

from examples.gravitas import run_gravitas_demo, run_smoke_tests as run_gravitas_smoke_tests
from examples.sentinel import run_sentinel_demo, run_smoke_tests as run_sentinel_smoke_tests
from examples.aegis import run_aegis_demo, run_smoke_tests as run_aegis_smoke_tests
from tools.trace_viewer import print_trace, print_summary
from tools.trace_export import save_trace_json, save_trace_text
from tools.trace_viewer import render_trace
from workflow.governance import run_routed_governance_workflow
from tools.workflow_viewer import print_workflow_trace
from tools.workflow_export import export_workflow_graph

def print_result(name, result, state_key: str) -> None:
    print()
    print_summary(name, result, state_key)
    print_trace(f"{name} TRACE", result)
    print(f"{name} RESULT")
    print("-" * (len(name) + 7))
    print("Execution OK:", result.ok)
    print(f"Final {state_key}:", result.final_state.get_int(f"state:{state_key}"))
    print()
    print("Trace:")

def main() -> None:
    print("APEXFORGE — MAIN RUNTIME")
    print("------------------------")

    run_sentinel_smoke_tests()
    print("Sentinel Smoke Test: PASSED")

    run_aegis_smoke_tests()
    print("AEGIS Smoke Test: PASSED")

    run_gravitas_smoke_tests()
    print("Gravitas Smoke Test: PASSED")
    
    sentinel_result = run_sentinel_demo()
    gravitas_result = run_gravitas_demo()
    aegis_result = run_aegis_demo()

    print_result("SENTINEL", sentinel_result, "Awareness")
    print_result("GRAVITAS", gravitas_result, "Vigilance")
    print_result("AEGIS", aegis_result, "Integrity")

    

    print_trace("SENTINEL TRACE", sentinel_result)
    print_trace("AEGIS TRACE", aegis_result)
    print_trace("GRAVITAS TRACE", gravitas_result)

    save_trace_json("SENTINEL", sentinel_result, "Awareness", "apexforge/exports/sentinel_trace.json")
    save_trace_json("AEGIS", aegis_result, "Integrity", "apexforge/exports/aegis_trace.json")
    save_trace_json("GRAVITAS", gravitas_result, "Vigilance", "apexforge/exports/gravitas_trace.json")

    save_trace_text("SENTINEL", render_trace("SENTINEL TRACE", sentinel_result), "apexforge/exports/sentinel_trace.txt")
    save_trace_text("AEGIS", render_trace("AEGIS TRACE", aegis_result), "apexforge/exports/aegis_trace.txt")
    save_trace_text("GRAVITAS", render_trace("GRAVITAS TRACE", gravitas_result), "apexforge/exports/gravitas_trace.txt")

print()
print("Trace exports written.")

workflow_result = run_routed_governance_workflow()
export_workflow_graph(
    workflow_result,
    "apexforge/exports/governance_graph.json",
)
print_workflow_trace(workflow_result)
    
if __name__ == "__main__":
    main()

