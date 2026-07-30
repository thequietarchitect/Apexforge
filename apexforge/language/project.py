"""ApexForge multi-source project construction and execution.

This module owns the source-project boundary:

    SourceUnit values
        -> independent compilation
        -> deterministic AIR linking
        -> runtime validation
        -> immutable ProjectBuild

A ProjectBuild is created only after every source unit compiles, the complete
AIR program links, and RuntimeValidator accepts the linked result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Protocol, Sequence

from air.linker import AIRProgramLinker
from air.model import AIRProgram, VerifiedAIRProgram
from language.compiler import compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.context import ExecutionContext
from runtime.engine import ExecutionResult, RuntimeEngine


class ProjectBuildError(Exception):
    """Base class for all ApexForge project-construction failures."""


class EmptyProjectError(ProjectBuildError):
    """Raised when a project contains no source units."""


class InvalidSourceUnitError(ProjectBuildError):
    """Raised when a source unit has an invalid name or source value."""


class DuplicateSourceUnitError(ProjectBuildError):
    """Raised when two source units use the same normalized filename."""


class ProjectCompilationError(ProjectBuildError):
    """Raised when one source unit cannot compile into an AIRProgram."""

    def __init__(
        self,
        source_name: str,
        cause: BaseException,
    ) -> None:
        self.source_name = source_name
        self.cause = cause

        super().__init__(
            f"Compilation failed for source {source_name!r}: "
            f"{type(cause).__name__}: {cause}"
        )


class ProjectLinkError(ProjectBuildError):
    """Raised when independently compiled AIR units cannot be linked."""

    def __init__(
        self,
        cause: BaseException,
    ) -> None:
        self.cause = cause

        super().__init__(
            "AIR project linking failed: "
            f"{type(cause).__name__}: {cause}"
        )


class ProjectValidationError(ProjectBuildError):
    """Raised when the linked AIR program fails runtime validation."""

    def __init__(
        self,
        cause: BaseException,
    ) -> None:
        self.cause = cause

        super().__init__(
            "Linked AIR project validation failed: "
            f"{type(cause).__name__}: {cause}"
        )


class ProjectEntryPointError(ProjectBuildError):
    """Raised when a project entry directive is absent or ambiguous."""


class _Compiler(Protocol):
    def __call__(
        self,
        source: str,
    ) -> Any:
        ...


@dataclass(frozen=True, order=True)
class SourceUnit:
    """One named ApexForge source compilation unit."""

    name: str
    source: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise InvalidSourceUnitError(
                "SourceUnit name must be a string; "
                f"received {type(self.name).__name__}."
            )

        normalized_name = self.name.strip()

        if not normalized_name:
            raise InvalidSourceUnitError(
                "SourceUnit name cannot be empty."
            )

        if not isinstance(self.source, str):
            raise InvalidSourceUnitError(
                f"SourceUnit {normalized_name!r} source must be a string; "
                f"received {type(self.source).__name__}."
            )

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )


@dataclass(frozen=True)
class ProjectBuild:
    """A fully compiled, linked, and validated ApexForge project."""

    source_units: tuple[SourceUnit, ...]
    program: AIRProgram
    verified: VerifiedAIRProgram
    entry_directive: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_units",
            tuple(self.source_units),
        )

        if not isinstance(self.program, AIRProgram):
            raise TypeError(
                "ProjectBuild.program must be AIRProgram."
            )

        if not isinstance(self.verified, VerifiedAIRProgram):
            raise TypeError(
                "ProjectBuild.verified must be VerifiedAIRProgram."
            )

        if self.verified.program is not self.program:
            raise ValueError(
                "ProjectBuild verified wrapper must reference "
                "ProjectBuild.program."
            )

        if self.entry_directive is not None:
            resolved = _resolve_entry_directive(
                self.program,
                self.entry_directive,
            )
            object.__setattr__(
                self,
                "entry_directive",
                resolved,
            )

    def execute(
        self,
        context: ExecutionContext,
        *,
        entry: Optional[str] = None,
        engine: Optional[RuntimeEngine] = None,
    ) -> ExecutionResult:
        """Execute one explicit project entry directive.

        A stored build entry is used when ``entry`` is omitted. A one-directive
        project may omit both because its sole directive is unambiguous.
        """

        selected = entry

        if selected is None:
            selected = self.entry_directive

        if selected is None:
            directives = tuple(self.program.directives)

            if len(directives) == 1:
                selected = directives[0].id
            else:
                raise ProjectEntryPointError(
                    "A multi-directive project requires an explicit "
                    "entry directive."
                )

        entry_id = _resolve_entry_directive(
            self.program,
            selected,
        )

        runtime = engine or RuntimeEngine()

        if not isinstance(runtime, RuntimeEngine):
            raise TypeError(
                "ProjectBuild.execute engine must be RuntimeEngine; "
                f"received {type(runtime).__name__}."
            )

        return runtime.execute(
            self.verified,
            context,
            entry_directives=(
                entry_id,
            ),
        )


class ProjectBuilder:
    """Compile, link, validate, and package an ApexForge source project."""

    def __init__(
        self,
        *,
        compiler: _Compiler = compile_source,
        linker: Optional[AIRProgramLinker] = None,
        validator: Optional[RuntimeValidator] = None,
    ) -> None:
        self._compiler = compiler
        self._linker = linker or AIRProgramLinker()
        self._validator = validator or RuntimeValidator()

    def build(
        self,
        sources: Mapping[str, str] | Iterable[SourceUnit],
        *,
        entry: Optional[str] = None,
    ) -> ProjectBuild:
        units = self._normalize_sources(
            sources
        )

        programs: list[AIRProgram] = []

        for unit in units:
            try:
                compiled = self._compiler(
                    unit.source
                )
            except Exception as exc:
                raise ProjectCompilationError(
                    unit.name,
                    exc,
                ) from exc

            if not isinstance(compiled, AIRProgram):
                cause = TypeError(
                    "Top-level source did not compile to AIRProgram; "
                    f"received {type(compiled).__name__}."
                )
                raise ProjectCompilationError(
                    unit.name,
                    cause,
                ) from cause

            programs.append(
                compiled
            )

        try:
            program = self._linker.link(
                programs
            )
        except Exception as exc:
            raise ProjectLinkError(
                exc
            ) from exc

        try:
            verified = self._validator.validate(
                program
            )
        except Exception as exc:
            raise ProjectValidationError(
                exc
            ) from exc

        resolved_entry = None

        if entry is not None:
            resolved_entry = _resolve_entry_directive(
                program,
                entry,
            )

        return ProjectBuild(
            source_units=units,
            program=program,
            verified=verified,
            entry_directive=resolved_entry,
        )

    def _normalize_sources(
        self,
        sources: Mapping[str, str] | Iterable[SourceUnit],
    ) -> tuple[SourceUnit, ...]:
        if isinstance(sources, Mapping):
            raw_units = tuple(
                SourceUnit(
                    name=name,
                    source=source,
                )
                for name, source in sources.items()
            )
        else:
            if isinstance(
                sources,
                (str, bytes),
            ):
                raise InvalidSourceUnitError(
                    "Project sources must be a filename-to-source mapping "
                    "or an iterable of SourceUnit values."
                )

            try:
                raw_units = tuple(
                    sources
                )
            except TypeError as exc:
                raise InvalidSourceUnitError(
                    "Project sources must be iterable."
                ) from exc

            for index, unit in enumerate(raw_units):
                if not isinstance(unit, SourceUnit):
                    raise InvalidSourceUnitError(
                        "Iterable project sources must contain SourceUnit "
                        f"values; item[{index}] was "
                        f"{type(unit).__name__}."
                    )

        if not raw_units:
            raise EmptyProjectError(
                "ApexForge project requires at least one source unit."
            )

        seen: dict[str, str] = {}

        for unit in raw_units:
            # Case-folded detection avoids ambiguous filenames on
            # case-insensitive filesystems while retaining the original name.
            key = unit.name.casefold()

            if key in seen:
                raise DuplicateSourceUnitError(
                    "Duplicate project source name "
                    f"{unit.name!r}; conflicts with {seen[key]!r}."
                )

            seen[key] = unit.name

        # Filename ordering makes the linked artifact independent of mapping or
        # iterable insertion order.
        return tuple(
            sorted(
                raw_units,
                key=lambda unit: (
                    unit.name.casefold(),
                    unit.name,
                ),
            )
        )


def _resolve_entry_directive(
    program: AIRProgram,
    reference: str,
) -> str:
    if not isinstance(reference, str):
        raise ProjectEntryPointError(
            "Project entry directive must be a string; "
            f"received {type(reference).__name__}."
        )

    normalized = reference.strip()

    if not normalized:
        raise ProjectEntryPointError(
            "Project entry directive cannot be empty."
        )

    by_id = {
        directive.id: directive
        for directive in tuple(
            program.directives
        )
    }

    if normalized in by_id:
        return normalized

    canonical = (
        normalized
        if normalized.startswith("directive:")
        else f"directive:{normalized}"
    )

    if canonical in by_id:
        return canonical

    raise ProjectEntryPointError(
        f"Undefined project entry directive {reference!r}."
    )


def build_project(
    sources: Mapping[str, str] | Iterable[SourceUnit],
    *,
    entry: Optional[str] = None,
) -> ProjectBuild:
    """Build one immutable, executable ApexForge project artifact."""

    return ProjectBuilder().build(
        sources,
        entry=entry,
    )


__all__ = (
    "DuplicateSourceUnitError",
    "EmptyProjectError",
    "InvalidSourceUnitError",
    "ProjectBuild",
    "ProjectBuildError",
    "ProjectBuilder",
    "ProjectCompilationError",
    "ProjectEntryPointError",
    "ProjectLinkError",
    "ProjectValidationError",
    "SourceUnit",
    "build_project",
)