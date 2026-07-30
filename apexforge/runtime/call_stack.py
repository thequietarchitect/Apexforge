"""Immutable AFP-P7 pure-function call frames and stacks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class LocalBinding:
    """One immutable local name/value binding."""

    name: str
    value: Any

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(
                "LocalBinding.name must be a non-empty string."
            )

        object.__setattr__(
            self,
            "name",
            self.name.strip(),
        )


@dataclass(frozen=True)
class CallFrame:
    """One immutable pure-function activation record."""

    function_id: str
    function_name: str
    bindings: tuple[LocalBinding, ...] = ()
    depth: int = 0

    def __post_init__(self) -> None:
        if not isinstance(
            self.function_id,
            str,
        ) or not self.function_id.strip():
            raise ValueError(
                "CallFrame.function_id must be a non-empty string."
            )

        if not isinstance(
            self.function_name,
            str,
        ) or not self.function_name.strip():
            raise ValueError(
                "CallFrame.function_name must be a non-empty string."
            )

        if isinstance(self.depth, bool) or not isinstance(
            self.depth,
            int,
        ) or self.depth < 0:
            raise ValueError(
                "CallFrame.depth must be a non-negative integer."
            )

        normalized = tuple(self.bindings)
        seen: set[str] = set()

        for binding in normalized:
            if not isinstance(binding, LocalBinding):
                raise TypeError(
                    "CallFrame.bindings must contain LocalBinding values; "
                    f"received {type(binding).__name__}."
                )

            if binding.name in seen:
                raise ValueError(
                    "duplicate call-frame binding "
                    f"{binding.name!r}."
                )

            seen.add(binding.name)

        object.__setattr__(
            self,
            "function_id",
            self.function_id.strip(),
        )
        object.__setattr__(
            self,
            "function_name",
            self.function_name.strip(),
        )
        object.__setattr__(
            self,
            "bindings",
            normalized,
        )

    @classmethod
    def bind(
        cls,
        *,
        function: Any,
        values: Iterable[Any],
        depth: int,
    ) -> "CallFrame":
        parameters = tuple(
            getattr(function, "parameters", ()) or ()
        )
        arguments = tuple(values)

        if len(parameters) != len(arguments):
            raise ValueError(
                "CallFrame.bind parameter/argument count mismatch: "
                f"{len(parameters)} parameter(s), "
                f"{len(arguments)} argument(s)."
            )

        return cls(
            function_id=getattr(function, "id"),
            function_name=getattr(function, "name"),
            bindings=tuple(
                LocalBinding(
                    name=getattr(parameter, "name"),
                    value=value,
                )
                for parameter, value in zip(
                    parameters,
                    arguments,
                )
            ),
            depth=depth,
        )

    def try_resolve(
        self,
        name: str,
    ) -> tuple[bool, Any]:
        for binding in self.bindings:
            if binding.name == name:
                return True, binding.value

        return False, None

    def resolve(
        self,
        name: str,
    ) -> Any:
        found, value = self.try_resolve(name)

        if not found:
            raise KeyError(name)

        return value


@dataclass(frozen=True)
class CallStack:
    """An immutable sequence of active pure-function frames."""

    frames: tuple[CallFrame, ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(self.frames)

        for index, frame in enumerate(normalized):
            if not isinstance(frame, CallFrame):
                raise TypeError(
                    "CallStack.frames must contain CallFrame values; "
                    f"received {type(frame).__name__}."
                )

            if frame.depth != index:
                raise ValueError(
                    f"CallStack frame {frame.function_id!r} has depth "
                    f"{frame.depth}, expected {index}."
                )

        object.__setattr__(
            self,
            "frames",
            normalized,
        )

    @property
    def depth(self) -> int:
        return len(self.frames)

    @property
    def current(self) -> Optional[CallFrame]:
        if not self.frames:
            return None

        return self.frames[-1]

    def contains(
        self,
        function_id: str,
    ) -> bool:
        return any(
            frame.function_id == function_id
            for frame in self.frames
        )

    def push(
        self,
        frame: CallFrame,
    ) -> "CallStack":
        if not isinstance(frame, CallFrame):
            raise TypeError(
                "CallStack.push requires CallFrame; "
                f"received {type(frame).__name__}."
            )

        if frame.depth != self.depth:
            raise ValueError(
                f"Call frame depth {frame.depth} does not match "
                f"stack depth {self.depth}."
            )

        return type(self)(
            self.frames + (frame,)
        )


__all__ = (
    "CallFrame",
    "CallStack",
    "LocalBinding",
)