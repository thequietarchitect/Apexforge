"""Workflow graph export utilities."""

from __future__ import annotations

import json
from pathlib import Path


def export_workflow_graph(workflow_result, path: str) -> None:
    nodes = []
    edges = []

    results = workflow_result.results

    for i, (name, result) in enumerate(results):
        if name not in nodes:
            nodes.append(name)

        for event in result.delta.events:
            if i + 1 < len(results):
                next_name = results[i + 1][0]

                edges.append(
                    {
                        "event": event.event,
                        "from": name,
                        "to": next_name,
                    }
                )

    graph = {
        "name": workflow_result.name,
        "nodes": nodes,
        "edges": edges,
    }

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(graph, indent=2),
        encoding="utf-8",
    )