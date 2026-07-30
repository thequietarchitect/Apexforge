"""ApexForge multi-source project construction with structured diagnostics."""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Protocol

from air.linker import AIRProgramLinker
from air.model import AIRProgram, VerifiedAIRProgram
from language.compiler import (
    CompiledSource,
    SourceMap,
    compile_source_with_map,
)
from language.diagnostics import (
    BuildDiagnostic,
    diagnostics_from_exception,
    render_diagnostics,
)
from language.source import SourceSpan, SourceText
from language.validation.runtime_validator import RuntimeValidator
from runtime.context import ExecutionContext
from runtime.engine import ExecutionResult, RuntimeEngine


class ProjectBuildError(Exception):
    """Base class for source-project construction failures."""

    def __init__(
        self,
        message: str,
        *,
        diagnostics: tuple[BuildDiagnostic, ...] = (),
        cause: Optional[BaseException] = None,
    ) -> None:
        self.diagnostics = tuple(
            sorted(diagnostics, key=lambda item: item.sort_key())
        )
        self.cause = cause

        rendered = render_diagnostics(self.diagnostics)
        super().__init__(f"{message}\n{rendered}" if rendered else message)


class EmptyProjectError(ProjectBuildError):
    pass


class InvalidSourceUnitError(ProjectBuildError):
    pass


class DuplicateSourceUnitError(ProjectBuildError):
    pass


class ProjectCompilationError(ProjectBuildError):
    def __init__(
        self,
        source_name: str,
        cause: BaseException,
        *,
        source: str = "",
    ) -> None:
        self.source_name = source_name
        diagnostics = diagnostics_from_exception(cause)

        if not diagnostics:
            span = SourceText(source_name, source).span(0, 0)
            diagnostics = (
                BuildDiagnostic(
                    severity="error",
                    code="APX-COMPILE-999",
                    message=f"{type(cause).__name__}: {cause}",
                    stage="compile",
                    span=span,
                ),
            )

        super().__init__(
            f"Compilation failed for source {source_name!r}.",
            diagnostics=diagnostics,
            cause=cause,
        )


class ProjectLinkError(ProjectBuildError):
    def __init__(
        self,
        cause: BaseException,
        *,
        source_map: SourceMap,
    ) -> None:
        owner = getattr(cause, "owner", "definition")
        identifier = getattr(cause, "identifier", "")
        matches = source_map.find(air_id=identifier) if identifier else ()
        span = matches[0].span if matches else None
        related = tuple(entry.span for entry in matches[1:])

        if matches:
            source_names = tuple(
                dict.fromkeys(entry.span.source_name for entry in matches)
            )
            location_text = ", ".join(repr(name) for name in source_names)
            message = (
                f"Duplicate {owner} definition {identifier!r} appears in "
                f"{location_text}."
            )
            code = "APX-LINK-001"
        else:
            message = f"{type(cause).__name__}: {cause}"
            code = "APX-LINK-999"

        diagnostic = BuildDiagnostic(
            severity="error",
            code=code,
            message=message,
            stage="link",
            span=span,
            air_id=identifier,
            related_spans=related,
        )

        super().__init__(
            "AIR project linking failed.",
            diagnostics=(diagnostic,),
            cause=cause,
        )


class ProjectValidationError(ProjectBuildError):
    def __init__(
        self,
        cause: BaseException,
        *,
        source_map: SourceMap,
    ) -> None:
        message = str(cause)
        span: Optional[SourceSpan] = None
        air_id = ""
        code = "APX-VALIDATE-999"

        invocation_match = re.search(
            r"invokes undefined directive\s+'([^']+)'",
            message,
        )

        if invocation_match is not None:
            target = invocation_match.group(1)
            matches = source_map.find(
                kind="directive_invocation",
                reference=target,
            )

            if not matches and target.startswith("directive:"):
                matches = source_map.find(
                    kind="directive_invocation",
                    reference=target[len("directive:") :],
                )

            if matches:
                span = matches[0].span
                air_id = matches[0].air_id

            code = "APX-VALIDATE-002"

        diagnostic = BuildDiagnostic(
            severity="error",
            code=code,
            message=message,
            stage="validate",
            span=span,
            air_id=air_id,
        )

        super().__init__(
            "Linked AIR project validation failed.",
            diagnostics=(diagnostic,),
            cause=cause,
        )


class ProjectEntryPointError(ProjectBuildError):
    pass


class _Compiler(Protocol):
    def __call__(
        self,
        source: str,
        *,
        source_name: str = "<memory>",
    ) -> Any:
        ...


@dataclass(frozen=True, order=True)
class SourceUnit:
    name: str
    source: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise InvalidSourceUnitError(
                "SourceUnit name must be a string."
            )

        normalized_name = self.name.strip()
        if not normalized_name:
            raise InvalidSourceUnitError(
                "SourceUnit name cannot be empty."
            )
        if not isinstance(self.source, str):
            raise InvalidSourceUnitError(
                f"SourceUnit {normalized_name!r} source must be a string."
            )

        object.__setattr__(self, "name", normalized_name)


@dataclass(frozen=True)
class ProjectBuild:
    source_units: tuple[SourceUnit, ...]
    program: AIRProgram
    verified: VerifiedAIRProgram
    source_map: SourceMap
    entry_directive: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_units", tuple(self.source_units))

        if not isinstance(self.program, AIRProgram):
            raise TypeError("ProjectBuild.program must be AIRProgram.")
        if not isinstance(self.verified, VerifiedAIRProgram):
            raise TypeError("ProjectBuild.verified must be VerifiedAIRProgram.")
        if self.verified.program is not self.program:
            raise ValueError(
                "ProjectBuild verified wrapper must reference its program."
            )
        if not isinstance(self.source_map, SourceMap):
            raise TypeError("ProjectBuild.source_map must be SourceMap.")

        if self.entry_directive is not None:
            object.__setattr__(
                self,
                "entry_directive",
                _resolve_entry_directive(self.program, self.entry_directive),
            )

    def execute(
        self,
        context: ExecutionContext,
        *,
        entry: Optional[str] = None,
        engine: Optional[RuntimeEngine] = None,
    ) -> ExecutionResult:
        selected = entry if entry is not None else self.entry_directive

        if selected is None:
            directives = tuple(self.program.directives)
            if len(directives) == 1:
                selected = directives[0].id
            else:
                raise ProjectEntryPointError(
                    "A multi-directive project requires an explicit entry directive."
                )

        entry_id = _resolve_entry_directive(self.program, selected)
        runtime = engine or RuntimeEngine()

        if not isinstance(runtime, RuntimeEngine):
            raise TypeError(
                "ProjectBuild.execute engine must be RuntimeEngine; "
                f"received {type(runtime).__name__}."
            )

        return runtime.execute(
            self.verified,
            context,
            entry_directives=(entry_id,),
        )


class ProjectBuilder:
    def __init__(
        self,
        *,
        compiler: _Compiler = compile_source_with_map,
        linker: Optional[AIRProgramLinker] = None,
        validator: Optional[RuntimeValidator] = None,
    ) -> None:
        self._compiler = compiler
        self._linker = linker or AIRProgramLinker()
        self._validator = validator or RuntimeValidator()

    def _compile_unit(self, unit: SourceUnit) -> CompiledSource:
        try:
            signature = inspect.signature(self._compiler)
            accepts_source_name = (
                "source_name" in signature.parameters
                or any(
                    parameter.kind == inspect.Parameter.VAR_KEYWORD
                    for parameter in signature.parameters.values()
                )
            )
        except (TypeError, ValueError):
            accepts_source_name = True

        try:
            compiled = (
                self._compiler(unit.source, source_name=unit.name)
                if accepts_source_name
                else self._compiler(unit.source)
            )
        except Exception as exc:
            raise ProjectCompilationError(
                unit.name,
                exc,
                source=unit.source,
            ) from exc

        if isinstance(compiled, CompiledSource):
            artifact = compiled
        elif isinstance(compiled, AIRProgram):
            artifact = CompiledSource(
                program=compiled,
                source_map=SourceMap(),
            )
        else:
            cause = TypeError(
                "Top-level source did not compile to AIRProgram; "
                f"received {type(compiled).__name__}."
            )
            raise ProjectCompilationError(
                unit.name,
                cause,
                source=unit.source,
            ) from cause

        if not isinstance(artifact.program, AIRProgram):
            cause = TypeError(
                "Top-level source did not compile to AIRProgram; "
                f"received {type(artifact.program).__name__}."
            )
            raise ProjectCompilationError(
                unit.name,
                cause,
                source=unit.source,
            ) from cause

        return artifact

    def build(
        self,
        sources: Mapping[str, str] | Iterable[SourceUnit],
        *,
        entry: Optional[str] = None,
    ) -> ProjectBuild:
        units = self._normalize_sources(sources)
        artifacts = tuple(self._compile_unit(unit) for unit in units)
        programs = tuple(artifact.program for artifact in artifacts)
        source_map = SourceMap.merge(
            *(artifact.source_map for artifact in artifacts)
        )

        try:
            program = self._linker.link(programs)
        except Exception as exc:
            raise ProjectLinkError(
                exc,
                source_map=source_map,
            ) from exc

        try:
            verified = self._validator.validate(program)
        except Exception as exc:
            raise ProjectValidationError(
                exc,
                source_map=source_map,
            ) from exc

        resolved_entry = (
            _resolve_entry_directive(program, entry)
            if entry is not None
            else None
        )

        return ProjectBuild(
            source_units=units,
            program=program,
            verified=verified,
            source_map=source_map,
            entry_directive=resolved_entry,
        )

    def _normalize_sources(
        self,
        sources: Mapping[str, str] | Iterable[SourceUnit],
    ) -> tuple[SourceUnit, ...]:
        if isinstance(sources, Mapping):
            raw_units = tuple(
                SourceUnit(name=name, source=source)
                for name, source in sources.items()
            )
        else:
            if isinstance(sources, (str, bytes)):
                raise InvalidSourceUnitError(
                    "Project sources must be a mapping or SourceUnit iterable."
                )
            try:
                raw_units = tuple(sources)
            except TypeError as exc:
                raise InvalidSourceUnitError(
                    "Project sources must be iterable."
                ) from exc

            for index, unit in enumerate(raw_units):
                if not isinstance(unit, SourceUnit):
                    raise InvalidSourceUnitError(
                        "Iterable project sources must contain SourceUnit values; "
                        f"item[{index}] was {type(unit).__name__}."
                    )

        if not raw_units:
            raise EmptyProjectError(
                "ApexForge project requires at least one source unit."
            )

        seen: dict[str, str] = {}
        for unit in raw_units:
            key = unit.name.casefold()
            if key in seen:
                raise DuplicateSourceUnitError(
                    f"Duplicate project source name {unit.name!r}; "
                    f"conflicts with {seen[key]!r}."
                )
            seen[key] = unit.name

        return tuple(
            sorted(
                raw_units,
                key=lambda unit: (unit.name.casefold(), unit.name),
            )
        )


def _resolve_entry_directive(program: AIRProgram, reference: str) -> str:
    if not isinstance(reference, str):
        raise ProjectEntryPointError(
            "Project entry directive must be a string."
        )

    normalized = reference.strip()
    if not normalized:
        raise ProjectEntryPointError(
            "Project entry directive cannot be empty."
        )

    directive_ids = {directive.id for directive in tuple(program.directives)}
    if normalized in directive_ids:
        return normalized

    canonical = (
        normalized
        if normalized.startswith("directive:")
        else f"directive:{normalized}"
    )
    if canonical in directive_ids:
        return canonical

    raise ProjectEntryPointError(
        f"Undefined project entry directive {reference!r}."
    )


def build_project(
    sources: Mapping[str, str] | Iterable[SourceUnit],
    *,
    entry: Optional[str] = None,
) -> ProjectBuild:
    return ProjectBuilder().build(sources, entry=entry)


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