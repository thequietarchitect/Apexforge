"""ApexForge executable entrypoint."""

from __future__ import annotations

from workflow.air_registry import AirRegistry
from workflow.air_workflow import run_air_workflow_from_file
from tools.workflow_viewer import print_workflow_trace
from tools.workflow_export import export_workflow_graph


DIRECTIVES_FOLDER = "apexforge/directives"
WORKFLOW_FILE = "apexforge/directives/governance.workflow.json"
GRAPH_EXPORT_FILE = "apexforge/exports/governance_graph.json"


def main() -> None:
    print("APEXFORGE — AIR RUNTIME")
    print("-----------------------")

    registry = AirRegistry()
    registry.discover(DIRECTIVES_FOLDER)

    print("Loaded AIR directives:", registry.names())

    workflow_result = run_air_workflow_from_file(
        registry,
        WORKFLOW_FILE,
    )

    print_workflow_trace(workflow_result)

    export_workflow_graph(
        workflow_result,
        GRAPH_EXPORT_FILE,
    )

    print()
    print("Workflow graph exported:", GRAPH_EXPORT_FILE)


if __name__ == "__main__":
    main()
