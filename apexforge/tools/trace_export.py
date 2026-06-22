"""Trace export utilities for ApexForge."""

from __future__ import annotations

import json
from pathlib import Path


def trace_to_dict(title: str, result, state_key: str) -> dict:
    return {
        "title": title,
        "ok": result.ok,
        "final_state": {
            state_key: result.final_state.get_int(f"state:{state_key}")
        },
        "diagnostics": [
            {
                "severity": d.severity,
                "code": d.code,
                "message": d.message,
                "node_id": d.node_id,
            }
            for d in result.diagnostics
        ],
        "trace": [
            {
                "kind": step.kind,
                "message": step.message,
                "facts": {
                    fact.key: fact.value
                    for fact in step.facts
                },
            }
            for step in result.trace.steps
        ],
    }


def save_trace_json(title: str, result, state_key: str, path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = trace_to_dict(title, result, state_key)

    output_path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def save_trace_text(title: str, rendered_trace: str, path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered_trace, encoding="utf-8")