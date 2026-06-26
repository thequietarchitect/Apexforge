"""Human-readable runtime reports for ApexForge results."""

from __future__ import annotations


def _facts_dict(event) -> dict:
    return {
        fact.key: fact.value
        for fact in event.facts
    }


def render_runtime_report(title: str, result, state_key: str) -> str:
    lines = []

    lines.append("=" * 34)
    lines.append(f"ApexForge Runtime: {title}")
    lines.append("=" * 34)
    lines.append(f"Execution OK: {result.ok}")
    lines.append("")

    lines.append("MESSAGES")
    lines.append("--------")

    found_message = False

    for event in result.delta.events:
        facts = _facts_dict(event)
        message = facts.get("message")

        if message:
            found_message = True
            lines.append(message)

    if not found_message:
        lines.append("No messages emitted.")

    lines.append("")
    lines.append("STATE")
    lines.append("-----")
    lines.append(
        f"{state_key}: {result.final_state.get_int(f'state:{state_key}')}"
    )

    lines.append("")
    lines.append("EVENTS")
    lines.append("------")

    for event in result.delta.events:
        lines.append(event.event)

    return "\n".join(lines)


def print_runtime_report(title: str, result, state_key: str) -> None:
    print(render_runtime_report(title, result, state_key))