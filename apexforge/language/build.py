"""Compile .apex files into AIR JSON."""

from __future__ import annotations

from pathlib import Path

from air.serialization import save_air_json
from language.compiler import compile_source


def compile_file(source_path: str):
    source = Path(source_path).read_text(
        encoding="utf-8"
    )

    return compile_source(source)


def build_air(
    source_path: str,
    output_path: str,
):
    program = compile_file(source_path)

    save_air_json(
        program,
        output_path,
    )

    return output_path