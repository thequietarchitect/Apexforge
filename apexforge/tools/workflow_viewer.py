"""Workflow visualization utilities for ApexForge."""

from __future__ import annotations


def render_workflow_trace(workflow_result) -> str:
    lines = []

    lines.append("")
    lines.append(workflow_result.name)
    lines.append("=" * len(workflow_result.name))
    lines.append(f"Workflow OK: {workflow_result.ok}")
    lines.append("")

    for index, (name, result) in enumerate(workflow_result.results):
        lines.append(f"{index + 1}. {name}")

        emitted_events = [
            event.event
            for event in result.delta.events
        ]

        if emitted_events:
            for event in emitted_events:
                lines.append(f"   ↓ emits {event}")
        else:
            lines.append("   ↓ emits nothing")

        lines.append("")

    lines.append("Context")
    lines.append("-------")

    for key, value in sorted(workflow_result.context.states.items()):
        clean_key = key.replace("state:", "")
        lines.append(f"{clean_key}: {value}")

    lines.append("")

    lines.append("Events")
    lines.append("------")

    for event in workflow_result.context.events:
        lines.append(event)

    return "\n".join(lines)


def print_workflow_trace(workflow_result) -> None:
    print(render_workflow_trace(workflow_result))