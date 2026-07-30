"""ApexForge source-module declarations and import graph resolution.

AFP-P6 module headers are line-oriented and precede the ordinary
ApexForge top-level declaration:

    module application.caller
    import application.worker

    directive Caller {
        ...
    }

Module headers are masked, not removed, before ordinary lexing. Masking
preserves every source offset, line, and column used by AFP-P5 diagnostics.
"""

from __future__ import annotations

import heapq
import re
from dataclasses import dataclass
from typing import Iterable, Optional

from language.diagnostics import (
    BuildDiagnostic,
    render_diagnostics,
)
from language.source import (
    SourceSpan,
    SourceText,
)


_MODULE_NAME = (
    r"[A-Za-z_][A-Za-z0-9_]*"
    r"(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
)

_HEADER_PATTERN = re.compile(
    rf"^(?P<indent>[ \t]*)"
    rf"(?P<kind>module|import)"
    rf"[ \t]+"
    rf"(?P<name>{_MODULE_NAME})"
    rf"[ \t]*;?[ \t]*"
    rf"(?P<newline>\r?\n)?$"
)

_HEADER_PREFIX_PATTERN = re.compile(
    r"^[ \t]*(module|import)(?:[ \t]|$)"
)


class ModuleError(Exception):
    """One or more deterministic module-system diagnostics."""

    def __init__(
        self,
        diagnostics: Iterable[BuildDiagnostic],
    ) -> None:
        normalized = tuple(
            sorted(
                tuple(diagnostics),
                key=lambda item: item.sort_key(),
            )
        )

        if not normalized:
            raise ValueError(
                "ModuleError requires at least one diagnostic."
            )

        self.diagnostics = normalized
        super().__init__(
            render_diagnostics(normalized)
        )


@dataclass(frozen=True, order=True)
class ModuleImport:
    """One direct module dependency declared in source."""

    name: str
    span: SourceSpan

    def __post_init__(self) -> None:
        normalized = _normalize_module_name(
            self.name
        )

        if not isinstance(
            self.span,
            SourceSpan,
        ):
            raise TypeError(
                "ModuleImport.span must be SourceSpan."
            )

        object.__setattr__(
            self,
            "name",
            normalized,
        )


@dataclass(frozen=True)
class ModuleSource:
    """Parsed module headers plus an offset-preserving compiler source."""

    source_name: str
    module_name: Optional[str]
    module_span: Optional[SourceSpan]
    imports: tuple[ModuleImport, ...]
    masked_source: str

    def __post_init__(self) -> None:
        if not isinstance(
            self.source_name,
            str,
        ) or not self.source_name.strip():
            raise ValueError(
                "ModuleSource.source_name must be a non-empty string."
            )

        if self.module_name is not None:
            object.__setattr__(
                self,
                "module_name",
                _normalize_module_name(
                    self.module_name
                ),
            )

        if self.module_span is not None and not isinstance(
            self.module_span,
            SourceSpan,
        ):
            raise TypeError(
                "ModuleSource.module_span must be SourceSpan or None."
            )

        normalized_imports = tuple(
            self.imports
        )

        if any(
            not isinstance(
                dependency,
                ModuleImport,
            )
            for dependency in normalized_imports
        ):
            raise TypeError(
                "ModuleSource.imports must contain ModuleImport values."
            )

        if not isinstance(
            self.masked_source,
            str,
        ):
            raise TypeError(
                "ModuleSource.masked_source must be a string."
            )

        object.__setattr__(
            self,
            "source_name",
            self.source_name.strip(),
        )
        object.__setattr__(
            self,
            "imports",
            normalized_imports,
        )


@dataclass(frozen=True)
class ModuleRecord:
    """One explicit module in a resolved project graph."""

    name: str
    source_name: str
    span: SourceSpan
    imports: tuple[ModuleImport, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "name",
            _normalize_module_name(
                self.name
            ),
        )

        if not isinstance(
            self.source_name,
            str,
        ) or not self.source_name.strip():
            raise ValueError(
                "ModuleRecord.source_name must be non-empty."
            )

        if not isinstance(
            self.span,
            SourceSpan,
        ):
            raise TypeError(
                "ModuleRecord.span must be SourceSpan."
            )

        dependencies = tuple(
            self.imports
        )

        if any(
            not isinstance(
                dependency,
                ModuleImport,
            )
            for dependency in dependencies
        ):
            raise TypeError(
                "ModuleRecord.imports must contain ModuleImport values."
            )

        object.__setattr__(
            self,
            "source_name",
            self.source_name.strip(),
        )
        object.__setattr__(
            self,
            "imports",
            dependencies,
        )


@dataclass(frozen=True)
class ModuleGraph:
    """Resolved direct-import graph for one ApexForge source project."""

    modules: tuple[ModuleRecord, ...] = ()
    order: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        modules = tuple(
            self.modules
        )
        order = tuple(
            self.order
        )

        if any(
            not isinstance(
                module,
                ModuleRecord,
            )
            for module in modules
        ):
            raise TypeError(
                "ModuleGraph.modules must contain ModuleRecord values."
            )

        names = tuple(
            module.name
            for module in modules
        )

        if len(set(names)) != len(names):
            raise ValueError(
                "ModuleGraph contains duplicate module names."
            )

        if order:
            if set(order) != set(names) or len(order) != len(names):
                raise ValueError(
                    "ModuleGraph.order must contain each module once."
                )
        elif modules:
            raise ValueError(
                "A non-empty ModuleGraph requires a resolved order."
            )

        object.__setattr__(
            self,
            "modules",
            modules,
        )
        object.__setattr__(
            self,
            "order",
            order,
        )

    @property
    def is_legacy(self) -> bool:
        return not self.modules

    def find(
        self,
        name: str,
    ) -> Optional[ModuleRecord]:
        normalized = _normalize_module_name(
            name
        )

        for module in self.modules:
            if module.name == normalized:
                return module

        return None

    def direct_imports(
        self,
        name: str,
    ) -> tuple[str, ...]:
        module = self.find(
            name
        )

        if module is None:
            return ()

        return tuple(
            dependency.name
            for dependency in module.imports
        )

    def source_order(
        self,
    ) -> tuple[str, ...]:
        by_name = {
            module.name: module.source_name
            for module in self.modules
        }

        return tuple(
            by_name[name]
            for name in self.order
        )


def _normalize_module_name(
    name: str,
) -> str:
    if not isinstance(
        name,
        str,
    ):
        raise TypeError(
            "Module name must be a string."
        )

    normalized = name.strip()

    if not normalized or re.fullmatch(
        _MODULE_NAME,
        normalized,
    ) is None:
        raise ValueError(
            f"Invalid ApexForge module name {name!r}."
        )

    return normalized


def _diagnostic(
    *,
    code: str,
    message: str,
    span: Optional[SourceSpan],
    related_spans: tuple[SourceSpan, ...] = (),
    air_id: str = "",
) -> BuildDiagnostic:
    return BuildDiagnostic(
        severity="error",
        code=code,
        message=message,
        stage="module",
        span=span,
        air_id=air_id,
        related_spans=related_spans,
    )


def _mask_line(
    line: str,
) -> str:
    return "".join(
        character
        if character in {
            "\r",
            "\n",
        }
        else " "
        for character in line
    )


def parse_module_source(
    source_name: str,
    source: str,
) -> ModuleSource:
    """Parse leading module/import headers without shifting source text."""

    if not isinstance(
        source_name,
        str,
    ) or not source_name.strip():
        raise ValueError(
            "Module source name must be a non-empty string."
        )

    if not isinstance(
        source,
        str,
    ):
        raise TypeError(
            "Module source text must be a string."
        )

    source_text = SourceText(
        source_name,
        source,
    )

    lines = source.splitlines(
        keepends=True
    )

    if not lines and source == "":
        lines = []

    offset = 0
    body_started = False
    module_name: Optional[str] = None
    module_span: Optional[SourceSpan] = None
    imports: list[ModuleImport] = []
    import_names: dict[str, ModuleImport] = {}
    masked_parts: list[str] = []

    for line in lines:
        match = _HEADER_PATTERN.fullmatch(
            line
        )
        stripped = line.strip()

        if not body_started and match is not None:
            kind = match.group(
                "kind"
            )
            name = match.group(
                "name"
            )

            name_start = (
                offset
                + match.start(
                    "name"
                )
            )
            name_end = (
                offset
                + match.end(
                    "name"
                )
            )
            name_span = source_text.span(
                name_start,
                name_end,
            )

            if kind == "module":
                if module_name is not None:
                    raise ModuleError(
                        (
                            _diagnostic(
                                code="APX-MODULE-002",
                                message=(
                                    "A source unit may declare only "
                                    "one module."
                                ),
                                span=name_span,
                                related_spans=(
                                    module_span,
                                )
                                if module_span is not None
                                else (),
                            ),
                        )
                    )

                if imports:
                    raise ModuleError(
                        (
                            _diagnostic(
                                code="APX-MODULE-003",
                                message=(
                                    "The module declaration must "
                                    "precede every import."
                                ),
                                span=name_span,
                            ),
                        )
                    )

                module_name = name
                module_span = name_span
            else:
                if module_name is None:
                    raise ModuleError(
                        (
                            _diagnostic(
                                code="APX-MODULE-003",
                                message=(
                                    "An import requires a preceding "
                                    "module declaration."
                                ),
                                span=name_span,
                            ),
                        )
                    )

                if name in import_names:
                    raise ModuleError(
                        (
                            _diagnostic(
                                code="APX-MODULE-004",
                                message=(
                                    f"Duplicate import {name!r}."
                                ),
                                span=name_span,
                                related_spans=(
                                    import_names[name].span,
                                ),
                            ),
                        )
                    )

                dependency = ModuleImport(
                    name=name,
                    span=name_span,
                )
                imports.append(
                    dependency
                )
                import_names[name] = dependency

            masked_parts.append(
                _mask_line(
                    line
                )
            )
            offset += len(
                line
            )
            continue

        if not body_started and not stripped:
            masked_parts.append(
                line
            )
            offset += len(
                line
            )
            continue

        if match is not None or _HEADER_PREFIX_PATTERN.match(
            line
        ):
            line_span = source_text.span(
                offset,
                offset + len(
                    line.rstrip(
                        "\r\n"
                    )
                ),
            )
            raise ModuleError(
                (
                    _diagnostic(
                        code="APX-MODULE-001",
                        message=(
                            "Module and import headers must be "
                            "well-formed and precede the "
                            "top-level declaration."
                        ),
                        span=line_span,
                    ),
                )
            )

        body_started = True
        masked_parts.append(
            line
        )
        offset += len(
            line
        )

    # splitlines(keepends=True) includes every character except that an
    # empty source has no lines. The join therefore preserves exact length.
    masked_source = "".join(
        masked_parts
    )

    if len(masked_source) != len(source):
        raise AssertionError(
            "Module header masking changed source length."
        )

    return ModuleSource(
        source_name=source_name,
        module_name=module_name,
        module_span=module_span,
        imports=tuple(
            imports
        ),
        masked_source=masked_source,
    )


def build_module_graph(
    sources: Iterable[ModuleSource],
) -> ModuleGraph:
    """Resolve explicit modules, imports, missing dependencies, and cycles."""

    units = tuple(
        sources
    )

    if any(
        not isinstance(
            unit,
            ModuleSource,
        )
        for unit in units
    ):
        raise TypeError(
            "build_module_graph requires ModuleSource values."
        )

    explicit = tuple(
        unit
        for unit in units
        if unit.module_name is not None
    )

    if not explicit:
        return ModuleGraph()

    missing_declarations = tuple(
        unit
        for unit in units
        if unit.module_name is None
    )

    if missing_declarations:
        diagnostics = tuple(
            _diagnostic(
                code="APX-MODULE-005",
                message=(
                    "Every source unit must declare a module when "
                    "module mode is active."
                ),
                span=SourceText(
                    unit.source_name,
                    unit.masked_source,
                ).span(
                    0,
                    0,
                ),
            )
            for unit in missing_declarations
        )
        raise ModuleError(
            diagnostics
        )

    by_name: dict[str, ModuleSource] = {}
    by_folded: dict[str, ModuleSource] = {}

    for unit in explicit:
        assert unit.module_name is not None
        assert unit.module_span is not None

        folded = unit.module_name.casefold()

        if folded in by_folded:
            previous = by_folded[
                folded
            ]
            assert previous.module_span is not None

            raise ModuleError(
                (
                    _diagnostic(
                        code="APX-MODULE-009",
                        message=(
                            "Duplicate module declaration "
                            f"{unit.module_name!r}."
                        ),
                        span=unit.module_span,
                        related_spans=(
                            previous.module_span,
                        ),
                    ),
                )
            )

        by_name[
            unit.module_name
        ] = unit
        by_folded[
            folded
        ] = unit

    for unit in explicit:
        assert unit.module_name is not None

        for dependency in unit.imports:
            if dependency.name not in by_name:
                raise ModuleError(
                    (
                        _diagnostic(
                            code="APX-MODULE-006",
                            message=(
                                f"Module {unit.module_name!r} imports "
                                f"undefined module "
                                f"{dependency.name!r}."
                            ),
                            span=dependency.span,
                        ),
                    )
                )

    cycle = _find_cycle(
        by_name
    )

    if cycle is not None:
        cycle_names, edge_spans = cycle
        message = (
            "Module import cycle detected: "
            + " -> ".join(
                cycle_names
            )
            + "."
        )
        primary = (
            edge_spans[0]
            if edge_spans
            else None
        )
        related = tuple(
            edge_spans[1:]
        )

        raise ModuleError(
            (
                _diagnostic(
                    code="APX-MODULE-007",
                    message=message,
                    span=primary,
                    related_spans=related,
                ),
            )
        )

    order = _topological_order(
        by_name
    )

    records = tuple(
        ModuleRecord(
            name=name,
            source_name=by_name[name].source_name,
            span=by_name[name].module_span,
            imports=by_name[name].imports,
        )
        for name in sorted(
            by_name,
            key=lambda value: (
                value.casefold(),
                value,
            ),
        )
    )

    return ModuleGraph(
        modules=records,
        order=order,
    )


def validate_module_visibility(
    graph: ModuleGraph,
    compiled_by_module: dict[str, object],
) -> None:
    """Require invocation targets to be local or directly imported.

    AIR identifiers remain globally unique in AFP-P6. Modules establish
    dependency ownership and visibility; namespace-qualified AIR IDs are a
    later compatibility milestone.
    """

    if not isinstance(
        graph,
        ModuleGraph,
    ):
        raise TypeError(
            "validate_module_visibility requires ModuleGraph."
        )

    if graph.is_legacy:
        return

    definition_owner: dict[str, str] = {}

    for module_name in graph.order:
        artifact = compiled_by_module[
            module_name
        ]
        program = getattr(
            artifact,
            "program",
            None,
        )

        for directive in tuple(
            getattr(
                program,
                "directives",
                (),
            )
            or ()
        ):
            identifier = getattr(
                directive,
                "id",
                "",
            )

            if isinstance(
                identifier,
                str,
            ) and identifier:
                definition_owner[
                    identifier
                ] = module_name

    for module_name in graph.order:
        artifact = compiled_by_module[
            module_name
        ]
        source_map = getattr(
            artifact,
            "source_map",
            None,
        )
        entries = tuple(
            getattr(
                source_map,
                "entries",
                (),
            )
            or ()
        )
        visible = {
            module_name,
            *graph.direct_imports(
                module_name
            ),
        }

        for entry in entries:
            if getattr(
                entry,
                "kind",
                "",
            ) != "directive_invocation":
                continue

            reference = getattr(
                entry,
                "reference",
                "",
            )

            if not isinstance(
                reference,
                str,
            ) or not reference:
                continue

            target_id = (
                reference
                if reference.startswith(
                    "directive:"
                )
                else f"directive:{reference}"
            )
            owner = definition_owner.get(
                target_id
            )

            # Undefined targets remain RuntimeValidator responsibility.
            if owner is None:
                continue

            if owner in visible:
                continue

            raise ModuleError(
                (
                    _diagnostic(
                        code="APX-MODULE-008",
                        message=(
                            f"Module {module_name!r} invokes "
                            f"{target_id!r} from module {owner!r} "
                            "without directly importing it."
                        ),
                        span=getattr(
                            entry,
                            "span",
                            None,
                        ),
                        air_id=getattr(
                            entry,
                            "air_id",
                            "",
                        ),
                    ),
                )
            )


def _find_cycle(
    by_name: dict[str, ModuleSource],
) -> Optional[
    tuple[
        tuple[str, ...],
        tuple[SourceSpan, ...],
    ]
]:
    state: dict[str, int] = {
        name: 0
        for name in by_name
    }
    stack: list[str] = []

    def visit(
        name: str,
    ) -> Optional[
        tuple[
            tuple[str, ...],
            tuple[SourceSpan, ...],
        ]
    ]:
        state[
            name
        ] = 1
        stack.append(
            name
        )

        dependencies = sorted(
            by_name[name].imports,
            key=lambda item: (
                item.name.casefold(),
                item.name,
            ),
        )

        for dependency in dependencies:
            target = dependency.name

            if state[
                target
            ] == 0:
                result = visit(
                    target
                )

                if result is not None:
                    return result

            elif state[
                target
            ] == 1:
                start_index = stack.index(
                    target
                )
                path = tuple(
                    stack[start_index:]
                    + [
                        target,
                    ]
                )

                spans: list[SourceSpan] = []

                for source_name, target_name in zip(
                    path,
                    path[1:],
                ):
                    edge = next(
                        item
                        for item in by_name[
                            source_name
                        ].imports
                        if item.name == target_name
                    )
                    spans.append(
                        edge.span
                    )

                return (
                    path,
                    tuple(
                        spans
                    ),
                )

        stack.pop()
        state[
            name
        ] = 2
        return None

    for name in sorted(
        by_name,
        key=lambda value: (
            value.casefold(),
            value,
        ),
    ):
        if state[
            name
        ] != 0:
            continue

        result = visit(
            name
        )

        if result is not None:
            return result

    return None


def _topological_order(
    by_name: dict[str, ModuleSource],
) -> tuple[str, ...]:
    indegree = {
        name: len(
            by_name[name].imports
        )
        for name in by_name
    }
    dependents: dict[str, list[str]] = {
        name: []
        for name in by_name
    }

    for importer, unit in by_name.items():
        for dependency in unit.imports:
            dependents[
                dependency.name
            ].append(
                importer
            )

    heap: list[
        tuple[
            str,
            str,
        ]
    ] = []

    for name, degree in indegree.items():
        if degree == 0:
            heapq.heappush(
                heap,
                (
                    name.casefold(),
                    name,
                ),
            )

    result: list[str] = []

    while heap:
        _, name = heapq.heappop(
            heap
        )
        result.append(
            name
        )

        for dependent in sorted(
            dependents[
                name
            ],
            key=lambda value: (
                value.casefold(),
                value,
            ),
        ):
            indegree[
                dependent
            ] -= 1

            if indegree[
                dependent
            ] == 0:
                heapq.heappush(
                    heap,
                    (
                        dependent.casefold(),
                        dependent,
                    ),
                )

    if len(result) != len(
        by_name
    ):
        raise AssertionError(
            "Module graph cycle escaped cycle detection."
        )

    return tuple(
        result
    )


__all__ = (
    "ModuleError",
    "ModuleGraph",
    "ModuleImport",
    "ModuleRecord",
    "ModuleSource",
    "build_module_graph",
    "parse_module_source",
    "validate_module_visibility",
)