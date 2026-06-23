"""AIR registry for loading ApexForge directives from AIR JSON files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from air.model import AIRProgram
from air.serialization import load_air_json


class AirRegistry:
    def __init__(self) -> None:
        self._programs: Dict[str, AIRProgram] = {}

    def load(self, name: str, path: str) -> None:
        self._programs[name] = load_air_json(path)

    def resolve(self, name: str) -> AIRProgram:
        return self._programs[name]

    def names(self) -> list[str]:
        return sorted(self._programs.keys())

    def discover(self, folder: str) -> None:
        root = Path(folder)

        for path in sorted(root.glob("*.air.json")):
            name = path.name.replace(".air.json", "")
            self.load(name, str(path))