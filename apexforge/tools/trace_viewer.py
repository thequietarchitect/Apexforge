"""Readable trace viewer for ApexForge execution results."""

from __future__ import annotations


def _facts_dict(step) -> dict:
    return {fact.key: fact.value for fact in step.facts}


def _format_step(step) -> list[str]:
    facts = _facts_dict(step)

    if step.kind == "authority.check":
        status = "ALLOW" if facts.get("allowed") else "DENY"
        return [
            f"  ├─ AUTHORITY {status}",
            f"  │  principal: {facts.get('principal')}",
            f"  │  capability: {facts.get('capability')}",
            f"  │  resource: {facts.get('resource')}",
        ]

    if step.kind == "causal.select":
        return [
            f"  ├─ CAUSAL SELECT",
            f"  │  path: {facts.get('path')}",
            f"  │  weight: {facts.get('weight')}",
        ]

    if step.kind == "state.delta":
        state = str(facts.get("state", "")).replace("state:", "")
        operation = facts.get("operation")
        value = facts.get("value")

        if operation == "add_int":
            change = f"{state} +{value}"
        elif operation == "set_int":
            change = f"{state} = {value}"
        else:
            change = f"{state} {operation} {value}"

        return [
            f"  ├─ STATE DELTA",
            f"  │  {change}",
            f"  │  path: {facts.get('path')}",
        ]

    if step.kind == "event.emit":
        return [
            f"  ├─ EVENT EMIT",
            f"  │  event: {facts.get('event')}",
            f"  │  id: {facts.get('event_id')}",
        ]

    if step.kind == "runtime.finish":
        return [
            f"  └─ RUNTIME FINISH",
            f"     events: {facts.get('events')}",
            f"     updates: {facts.get('updates')}",
        ]

    return [f"  ├─ {step.kind}: {step.message}"]


def render_summary(title: str, result, state_key: str) -> str:
    selected_path = None
    selected_weight = None

    for step in result.trace.steps:
        if step.kind == "causal.select":
            facts = _facts_dict(step)
            selected_path = facts.get("path")
            selected_weight = facts.get("weight")

    return "\n".join(
        [
            f"{title} SUMMARY",
            "-" * (len(title) + 8),
            f"Execution OK: {result.ok}",
            f"Selected Path: {selected_path}",
            f"Selected Weight: {selected_weight}",
            f"Final {state_key}: {result.final_state.get_int(f'state:{state_key}')}",
        ]
    )


def render_trace(title: str, result) -> str:
    lines = ["", title, "=" * len(title)]

    for step in result.trace.steps:
        lines.extend(_format_step(step))

    return "\n".join(lines)


def print_trace(title: str, result) -> None:
    print(render_trace(title, result))


def print_summary(title: str, result, state_key: str) -> None:
    print(render_summary(title, result, state_key))