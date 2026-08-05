"""Deterministic human-readable reports for ApexForge runtime results."""

from __future__ import annotations

import json
from typing import Any, Iterable


EMPTY_MARKER = "(none)"
REPORT_HEADING = "APEXFORGE RUNTIME REPORT"
REPORT_END = "END RUNTIME REPORT"
_MISSING = object()


def _render_value(value: Any) -> str:
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is int:
        return str(value)
    if type(value) is float:
        return repr(value)
    if type(value) is str:
        return json.dumps(value, ensure_ascii=False)

    literal_value = getattr(value, "value", _MISSING)
    if type(literal_value) in {bool, int, float, str}:
        return _render_value(literal_value)

    return f"<{type(value).__name__}>"


def _render_facts(facts: Iterable[Any]) -> str:
    selected = tuple(facts)
    if not selected:
        return EMPTY_MARKER
    return ", ".join(
        f"{fact.key}={_render_value(fact.value)}"
        for fact in selected
    )


def _append_section(
    lines: list[str],
    heading: str,
    entries: Iterable[str],
) -> None:
    lines.append(heading)
    selected = tuple(entries)
    if selected:
        lines.extend(selected)
    else:
        lines.append(EMPTY_MARKER)
    lines.append("")


def render_runtime_report(result: Any) -> str:
    """Project one immutable ExecutionResult into deterministic console text."""

    lines = [
        REPORT_HEADING,
        "",
        "RESULT",
        f"OK: {'true' if result.ok else 'false'}",
        "",
    ]

    _append_section(
        lines,
        "DIAGNOSTICS",
        (
            (
                f"{index}. severity={diagnostic.severity}; "
                f"code={diagnostic.code}; "
                f"node={diagnostic.node_id or '<runtime>'}; "
                f"message={json.dumps(diagnostic.message, ensure_ascii=False)}"
            )
            for index, diagnostic in enumerate(
                sorted(tuple(result.diagnostics)),
                start=1,
            )
        ),
    )

    _append_section(
        lines,
        "ASSIGNMENTS",
        (
            (
                f"{index}. state={assignment.state}; "
                f"operation={assignment.operation}; "
                f"value={_render_value(assignment.value)}"
            )
            for index, assignment in enumerate(
                tuple(result.delta.assignments),
                start=1,
            )
        ),
    )

    _append_section(
        lines,
        "EVENTS",
        (
            (
                f"{index}. id={event.id}; "
                f"event={event.event}; "
                f"directive={event.directive}; "
                f"principal={event.principal}; "
                f"facts={_render_facts(event.facts)}"
            )
            for index, event in enumerate(
                tuple(result.delta.events),
                start=1,
            )
        ),
    )

    _append_section(
        lines,
        "EFFECTS",
        (
            (
                f"{index}. id={effect.id}; "
                f"type={effect.effect_type}; "
                f"facts={_render_facts(effect.facts)}"
            )
            for index, effect in enumerate(
                tuple(result.delta.effects),
                start=1,
            )
        ),
    )

    _append_section(
        lines,
        "TRACE",
        (
            (
                f"{index}. kind={step.kind}; "
                f"message={json.dumps(step.message, ensure_ascii=False)}; "
                f"facts={_render_facts(step.facts)}"
            )
            for index, step in enumerate(
                tuple(result.trace.steps),
                start=1,
            )
        ),
    )

    _append_section(
        lines,
        "FINAL STATE",
        (
            f"{cell.key} = {_render_value(cell.value)}"
            for cell in tuple(result.final_state.cells)
        ),
    )

    while lines and lines[-1] == "":
        lines.pop()
    lines.append(REPORT_END)
    return "\n".join(lines)


__all__ = (
    "EMPTY_MARKER",
    "REPORT_END",
    "REPORT_HEADING",
    "render_runtime_report",
)
