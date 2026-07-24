from __future__ import annotations

from typing import Dict, Iterable, Protocol, TypeVar


class HasId(Protocol):
    id: str


T = TypeVar("T", bound=HasId)


def index_by_id(items: Iterable[T]) -> Dict[str, T]:
    return {item.id: item for item in items}