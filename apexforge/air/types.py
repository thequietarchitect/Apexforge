from __future__ import annotations

from typing import Literal, Union

AIR_VERSION = "0.2"

Primitive = Union[int, str, bool]
StateOperation = Literal["set_int", "add_int"]


def is_int(value: object) -> bool:
    return type(value) is int


def as_tuple(values: object) -> tuple:
    if values is None:
        return ()
    if isinstance(values, tuple):
        return values
    return tuple(values)