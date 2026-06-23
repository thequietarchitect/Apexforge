"""Workflow JSON loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple


def load_workflow_json(path: str) -> tuple[str, Tuple[str, ...]]:
    data = json.loads(
        Path(path).read_text(encoding="utf-8")
    )

    return (
        data["name"],
        tuple(data["steps"]),
    )