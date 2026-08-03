"""ApexForge multi-source project construction with AFP-P7 functions."""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass
from typing import (
    Any,
    Iterable,
    Mapping,
    Optional,
    Protocol,
)

from air.linker import AIRProgramLinker
from air.model import (
    AIRProgram,
    VerifiedAIRProgram,
)
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
from language.modules import (
    ModuleError,
    ModuleGraph,
    ModuleSource,
    build_module_graph,
    parse_module_source,
    validate_module_visibility,
)
from language.source import (
    SourceSpan,
    SourceText,
)
from language.validation.runtime_validator import (
    RuntimeValidator,
)
from runtime.context import ExecutionContext
from runtime.engine import (
    ExecutionResult,
    RuntimeEngine,
)


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
            sorted(
                diagnostics,
                key=lambda item: item.sort_key(),
            )
        )
        self.cause = cause

        rendered = render_diagnostics(
            self.diagnostics
        )

        super().__init__(
            f"{message}\n{rendered}"
            if rendered
            else message
        )


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
        diagnostics = diagnostics_from_exception(
            cause
        )

        if not diagnostics:
            span = SourceText(
                source_name,
                source,
            ).span(
                0,
                0,
            )
            diagnostics = (
                BuildDiagnostic(
                    severity="error",
                    code="APX-COMPILE-999",
                    message=(
                        f"{type(cause).__name__}: "
                        f"{cause}"
                    ),
                    stage="compile",
                    span=span,
                ),
            )

        super().__init__(
            f"Compilation failed for source "
            f"{source_name!r}.",
            diagnostics=diagnostics,
            cause=cause,
        )


class ProjectModuleError(ProjectBuildError):
    """Raised when module declarations or imports are invalid."""

    def __init__(
        self,
        cause: ModuleError,
    ) -> None:
        super().__init__(
            "ApexForge module resolution failed.",
            diagnostics=cause.diagnostics,
            cause=cause,
        )


class ProjectLinkError(ProjectBuildError):
    def __init__(
        self,
        cause: BaseException,
        *,
        source_map: SourceMap,
    ) -> None:
        owner = getattr(
            cause,
            "owner",
            "definition",
        )
        identifier = getattr(
            cause,
            "identifier",
            "",
        )
        matches = (
            source_map.find(
                air_id=identifier
            )
            if identifier
            else ()
        )
        span = (
            matches[0].span
            if matches
            else None
        )
        related = tuple(
            entry.span
            for entry in matches[1:]
        )

        if matches:
            source_names = tuple(
                dict.fromkeys(
                    entry.span.source_name
                    for entry in matches
                )
            )
            location_text = ", ".join(
                repr(
                    name
                )
                for name in source_names
            )
            message = (
                f"Duplicate {owner} definition "
                f"{identifier!r} appears in "
                f"{location_text}."
            )
            code = "APX-LINK-001"
        else:
            message = (
                f"{type(cause).__name__}: "
                f"{cause}"
            )
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
            diagnostics=(
                diagnostic,
            ),
            cause=cause,
        )


def _reference_source_entries(
    source_map: SourceMap,
    *,
    kind: str,
    reference: str,
    prefix: str,
) -> tuple[Any, ...]:
    candidates = [reference]

    if reference.startswith(prefix):
        plain = reference[len(prefix):]
        if plain:
            candidates.append(plain)
    else:
        candidates.append(f"{prefix}{reference}")

    matches: list[Any] = []
    seen: set[tuple[object, ...]] = set()

    for candidate in candidates:
        for entry in source_map.find(
            kind=kind,
            reference=candidate,
        ):
            key = (
                entry.air_id,
                entry.span.source_name,
                entry.span.start.offset,
                entry.span.end.offset,
            )
            if key not in seen:
                seen.add(key)
                matches.append(entry)

    return tuple(matches)


def _validation_location(
    entries: tuple[Any, ...],
) -> tuple[Optional[SourceSpan], str, tuple[SourceSpan, ...]]:
    if not entries:
        return None, "", ()

    primary = entries[0]
    related: list[SourceSpan] = []
    seen = {
        (
            primary.span.source_name,
            primary.span.start.offset,
            primary.span.end.offset,
        )
    }

    for entry in entries[1:]:
        key = (
            entry.span.source_name,
            entry.span.start.offset,
            entry.span.end.offset,
        )
        if key in seen:
            continue
        seen.add(key)
        related.append(entry.span)

    return (
        primary.span,
        primary.air_id,
        tuple(related),
    )


class ProjectValidationError(ProjectBuildError):
    def __init__(
        self,
        cause: BaseException,
        *,
        source_map: SourceMap,
    ) -> None:
        carried = diagnostics_from_exception(
            cause
        )

        if carried:
            super().__init__(
                "Linked AIR project validation failed.",
                diagnostics=carried,
                cause=cause,
            )
            return

        message = str(
            cause
        )
        code = "APX-VALIDATE-999"
        entries: tuple[Any, ...] = ()

        invocation_match = re.search(
            r"invokes undefined directive\s+'([^']+)'",
            message,
        )
        undefined_function_match = re.search(
            r"calls undefined function\s+'([^']+)'",
            message,
        )
        arity_match = re.search(
            r"calls function\s+'([^']+)'\s+with\s+"
            r"\d+\s+argument\(s\);\s+expected\s+\d+",
            message,
        )
        recursion_match = re.search(
            r"Recursive function cycle detected:\s*(.+?)\.?$",
            message,
        )

        if invocation_match is not None:
            entries = _reference_source_entries(
                source_map,
                kind="directive_invocation",
                reference=invocation_match.group(1),
                prefix="directive:",
            )
            code = "APX-VALIDATE-002"

        elif undefined_function_match is not None:
            entries = _reference_source_entries(
                source_map,
                kind="function_call",
                reference=undefined_function_match.group(1),
                prefix="function:",
            )
            code = "APX-VALIDATE-003"

        elif arity_match is not None:
            entries = _reference_source_entries(
                source_map,
                kind="function_call",
                reference=arity_match.group(1),
                prefix="function:",
            )
            code = "APX-VALIDATE-004"

        elif recursion_match is not None:
            cycle_names = tuple(
                name.strip()
                for name in recursion_match.group(1).rstrip(".").split("->")
                if name.strip()
            )
            collected: list[Any] = []

            for name in cycle_names:
                declaration_matches = source_map.find(
                    kind="function",
                    reference=name,
                )
                if not declaration_matches and name.startswith(
                    "function:"
                ):
                    declaration_matches = source_map.find(
                        kind="function",
                        reference=name[len("function:"):],
                    )
                collected.extend(declaration_matches[:1])

            entries = tuple(collected)
            code = "APX-VALIDATE-005"

        else:
            function_owner = re.search(
                r"[Ff]unction\s+'([^']+)'",
                message,
            )
            if function_owner is not None:
                function_reference = function_owner.group(1)
                plain_reference = (
                    function_reference[len("function:"):]
                    if function_reference.startswith("function:")
                    else function_reference
                )
                entries = source_map.find(
                    kind="function",
                    reference=plain_reference,
                )
                code = "APX-VALIDATE-006"

        span, air_id, related_spans = _validation_location(
            entries
        )
        diagnostic = BuildDiagnostic(
            severity="error",
            code=code,
            message=message,
            stage="validate",
            span=span,
            air_id=air_id,
            related_spans=related_spans,
        )

        super().__init__(
            "Linked AIR project validation failed.",
            diagnostics=(
                diagnostic,
            ),
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
        allow_headerless_multi_directive: bool = True,
    ) -> Any:
        ...


@dataclass(frozen=True, order=True)
class SourceUnit:
    name: str
    source: str

    def __post_init__(
        self,
    ) -> None:
        if not isinstance(
            self.name,
            str,
        ):
            raise InvalidSourceUnitError(
                "SourceUnit name must be a string."
            )

        normalized_name = self.name.strip()

        if not normalized_name:
            raise InvalidSourceUnitError(
                "SourceUnit name cannot be empty."
            )

        if not isinstance(
            self.source,
            str,
        ):
            raise InvalidSourceUnitError(
                f"SourceUnit {normalized_name!r} "
                "source must be a string."
            )

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )


@dataclass(frozen=True)
class ProjectBuild:
    source_units: tuple[SourceUnit, ...]
    program: AIRProgram
    verified: VerifiedAIRProgram
    source_map: SourceMap
    module_graph: ModuleGraph = ModuleGraph()
    entry_directive: Optional[str] = None

    def __post_init__(
        self,
    ) -> None:
        object.__setattr__(
            self,
            "source_units",
            tuple(
                self.source_units
            ),
        )

        if not isinstance(
            self.program,
            AIRProgram,
        ):
            raise TypeError(
                "ProjectBuild.program must be AIRProgram."
            )

        if not isinstance(
            self.verified,
            VerifiedAIRProgram,
        ):
            raise TypeError(
                "ProjectBuild.verified must be "
                "VerifiedAIRProgram."
            )

        if self.verified.program is not self.program:
            raise ValueError(
                "ProjectBuild verified wrapper must "
                "reference its program."
            )

        if not isinstance(
            self.source_map,
            SourceMap,
        ):
            raise TypeError(
                "ProjectBuild.source_map must be SourceMap."
            )

        if not isinstance(
            self.module_graph,
            ModuleGraph,
        ):
            raise TypeError(
                "ProjectBuild.module_graph must be "
                "ModuleGraph."
            )

        if self.entry_directive is not None:
            object.__setattr__(
                self,
                "entry_directive",
                _resolve_entry_directive(
                    self.program,
                    self.entry_directive,
                ),
            )

    def resolve_entry(
        self,
        entry: Optional[str] = None,
    ) -> str:
        """Resolve one canonical project entry without executing it."""

        selected = (
            entry
            if entry is not None
            else self.entry_directive
        )

        if selected is None:
            directives = tuple(
                self.program.directives
            )

            if len(
                directives
            ) == 1:
                selected = directives[
                    0
                ].id
            else:
                raise ProjectEntryPointError(
                    "A multi-directive project "
                    "requires an explicit entry "
                    "directive."
                )

        return _resolve_entry_directive(
            self.program,
            selected,
        )

    def execute(
        self,
        context: ExecutionContext,
        *,
        entry: Optional[str] = None,
        engine: Optional[RuntimeEngine] = None,
    ) -> ExecutionResult:
        entry_id = self.resolve_entry(
            entry,
        )
        runtime = (
            engine
            or RuntimeEngine()
        )

        if not isinstance(
            runtime,
            RuntimeEngine,
        ):
            raise TypeError(
                "ProjectBuild.execute engine must be "
                "RuntimeEngine; received "
                f"{type(runtime).__name__}."
            )

        return runtime.execute(
            self.verified,
            context,
            entry_directives=(
                entry_id,
            ),
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
        self._linker = (
            linker
            or AIRProgramLinker()
        )
        self._validator = (
            validator
            or RuntimeValidator()
        )

    def _compile_unit(
        self,
        unit: SourceUnit,
        *,
        compiler_source: Optional[str] = None,
        allow_headerless_multi_directive: bool = True,
    ) -> CompiledSource:
        source = (
            unit.source
            if compiler_source is None
            else compiler_source
        )

        try:
            signature = inspect.signature(
                self._compiler
            )
            accepts_source_name = (
                "source_name"
                in signature.parameters
                or any(
                    parameter.kind
                    == inspect.Parameter.VAR_KEYWORD
                    for parameter
                    in signature.parameters.values()
                )
            )
            accepts_multi_directive = (
                "allow_headerless_multi_directive"
                in signature.parameters
                or any(
                    parameter.kind
                    == inspect.Parameter.VAR_KEYWORD
                    for parameter
                    in signature.parameters.values()
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            accepts_source_name = True
            accepts_multi_directive = True

        try:
            compiler_arguments: dict[str, object] = {}
            if accepts_source_name:
                compiler_arguments["source_name"] = unit.name
            if accepts_multi_directive:
                compiler_arguments[
                    "allow_headerless_multi_directive"
                ] = allow_headerless_multi_directive
            compiled = self._compiler(
                source,
                **compiler_arguments,
            )
        except Exception as exc:
            raise ProjectCompilationError(
                unit.name,
                exc,
                source=unit.source,
            ) from exc

        if isinstance(
            compiled,
            CompiledSource,
        ):
            artifact = compiled
        elif isinstance(
            compiled,
            AIRProgram,
        ):
            artifact = CompiledSource(
                program=compiled,
                source_map=SourceMap(),
            )
        else:
            cause = TypeError(
                "Top-level source did not compile "
                "to AIRProgram; received "
                f"{type(compiled).__name__}."
            )
            raise ProjectCompilationError(
                unit.name,
                cause,
                source=unit.source,
            ) from cause

        if not isinstance(
            artifact.program,
            AIRProgram,
        ):
            cause = TypeError(
                "Top-level source did not compile "
                "to AIRProgram; received "
                f"{type(artifact.program).__name__}."
            )
            raise ProjectCompilationError(
                unit.name,
                cause,
                source=unit.source,
            ) from cause

        return artifact

    def _analyze_modules(
        self,
        units: tuple[SourceUnit, ...],
    ) -> tuple[
        tuple[ModuleSource, ...],
        ModuleGraph,
    ]:
        try:
            analyzed = tuple(
                parse_module_source(
                    unit.name,
                    unit.source,
                )
                for unit in units
            )
            graph = build_module_graph(
                analyzed
            )
        except ModuleError as exc:
            raise ProjectModuleError(
                exc
            ) from exc

        return (
            analyzed,
            graph,
        )

    def build(
        self,
        sources: (
            Mapping[str, str]
            | Iterable[SourceUnit]
        ),
        *,
        entry: Optional[str] = None,
    ) -> ProjectBuild:
        units = self._normalize_sources(
            sources
        )
        analyzed, graph = self._analyze_modules(
            units
        )

        units_by_source = {
            unit.name: unit
            for unit in units
        }
        analysis_by_source = {
            unit.source_name: unit
            for unit in analyzed
        }

        if graph.is_legacy:
            compile_source_names = tuple(
                unit.name
                for unit in units
            )
        else:
            compile_source_names = graph.source_order()

        artifacts_by_source: dict[
            str,
            CompiledSource,
        ] = {}

        for source_name in compile_source_names:
            unit = units_by_source[
                source_name
            ]
            analysis = analysis_by_source[
                source_name
            ]
            artifacts_by_source[
                source_name
            ] = self._compile_unit(
                unit,
                compiler_source=analysis.masked_source,
                allow_headerless_multi_directive=graph.is_legacy,
            )

        if graph.is_legacy:
            artifacts = tuple(
                artifacts_by_source[
                    unit.name
                ]
                for unit in units
            )
        else:
            artifacts = tuple(
                artifacts_by_source[
                    source_name
                ]
                for source_name
                in compile_source_names
            )

        source_map = SourceMap.merge(
            *(
                artifact.source_map
                for artifact in artifacts
            )
        )

        if not graph.is_legacy:
            module_by_source = {
                module.source_name: module.name
                for module in graph.modules
            }
            compiled_by_module = {
                module_by_source[
                    source_name
                ]: artifacts_by_source[
                    source_name
                ]
                for source_name
                in compile_source_names
            }

            try:
                validate_module_visibility(
                    graph,
                    compiled_by_module,
                )
            except ModuleError as exc:
                raise ProjectModuleError(
                    exc
                ) from exc

        programs = tuple(
            artifact.program
            for artifact in artifacts
        )

        try:
            program = self._linker.link(
                programs
            )
        except Exception as exc:
            raise ProjectLinkError(
                exc,
                source_map=source_map,
            ) from exc

        try:
            verified = self._validator.validate(
                program
            )
        except Exception as exc:
            raise ProjectValidationError(
                exc,
                source_map=source_map,
            ) from exc

        resolved_entry = (
            _resolve_entry_directive(
                program,
                entry,
            )
            if entry is not None
            else None
        )

        return ProjectBuild(
            source_units=units,
            program=program,
            verified=verified,
            source_map=source_map,
            module_graph=graph,
            entry_directive=resolved_entry,
        )

    def _normalize_sources(
        self,
        sources: (
            Mapping[str, str]
            | Iterable[SourceUnit]
        ),
    ) -> tuple[SourceUnit, ...]:
        if isinstance(
            sources,
            Mapping,
        ):
            raw_units = tuple(
                SourceUnit(
                    name=name,
                    source=source,
                )
                for name, source
                in sources.items()
            )
        else:
            if isinstance(
                sources,
                (
                    str,
                    bytes,
                ),
            ):
                raise InvalidSourceUnitError(
                    "Project sources must be a "
                    "mapping or SourceUnit iterable."
                )

            try:
                raw_units = tuple(
                    sources
                )
            except TypeError as exc:
                raise InvalidSourceUnitError(
                    "Project sources must be iterable."
                ) from exc

            for index, unit in enumerate(
                raw_units
            ):
                if not isinstance(
                    unit,
                    SourceUnit,
                ):
                    raise InvalidSourceUnitError(
                        "Iterable project sources must "
                        "contain SourceUnit values; "
                        f"item[{index}] was "
                        f"{type(unit).__name__}."
                    )

        if not raw_units:
            raise EmptyProjectError(
                "ApexForge project requires at least "
                "one source unit."
            )

        seen: dict[
            str,
            str,
        ] = {}

        for unit in raw_units:
            key = unit.name.casefold()

            if key in seen:
                raise DuplicateSourceUnitError(
                    "Duplicate project source name "
                    f"{unit.name!r}; conflicts with "
                    f"{seen[key]!r}."
                )

            seen[
                key
            ] = unit.name

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
    if not isinstance(
        reference,
        str,
    ):
        raise ProjectEntryPointError(
            "Project entry directive must be "
            "a string."
        )

    normalized = reference.strip()

    if not normalized:
        raise ProjectEntryPointError(
            "Project entry directive cannot "
            "be empty."
        )

    directive_ids = {
        directive.id
        for directive
        in tuple(
            program.directives
        )
    }

    if normalized in directive_ids:
        return normalized

    canonical = (
        normalized
        if normalized.startswith(
            "directive:"
        )
        else f"directive:{normalized}"
    )

    if canonical in directive_ids:
        return canonical

    raise ProjectEntryPointError(
        f"Undefined project entry directive "
        f"{reference!r}."
    )


def build_project(
    sources: (
        Mapping[str, str]
        | Iterable[SourceUnit]
    ),
    *,
    entry: Optional[str] = None,
) -> ProjectBuild:
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
    "ProjectModuleError",
    "ProjectValidationError",
    "SourceUnit",
    "build_project",
)
