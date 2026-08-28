"""P11 SRA-C manifested cross-file definition resolution.

This layer preserves the frozen P10 same-document definition contract and adds
project-aware navigation for imported directive invocation targets.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Mapping, Optional
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from language.diagnostics import diagnostics_from_exception
from language.modules import ModuleError, build_module_graph, parse_module_source
from language.parser import DirectiveNode, InvokeActionNode, WhenActionNode, parse_source_unit
from language.project import build_project
from language.resolution_context import ProjectResolutionContext
from language.resolution_outcomes import resolve_project_contextual_query
from language.resolution_queries import ProjectResolutionQuery, ProjectResolvedBinding
from language.source import SourceSpan
from language_server.diagnostics import offset_to_lsp_position
from language_server.hover import lsp_position_to_offset
from tooling.project_loader import load_project
from tooling.project_manifest import ProjectManifestError


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _file_uri_to_path(uri: str) -> Path:
    parsed = urlparse(uri)
    if parsed.scheme.casefold() != "file":
        raise ValueError("project definition resolution requires a file:// URI.")
    raw_path = url2pathname(unquote(parsed.path))
    if parsed.netloc and parsed.netloc.casefold() != "localhost":
        raw_path = f"//{parsed.netloc}{raw_path}"
    if os.name == "nt" and re.match(r"^/[A-Za-z]:", raw_path):
        raw_path = raw_path[1:]
    path = Path(raw_path)
    if not path.is_absolute():
        raise ValueError("definition URI must resolve to an absolute path.")
    return path.resolve()


def _iter_actions(actions: object):
    for action in tuple(actions or ()):
        yield action
        if isinstance(action, WhenActionNode):
            yield from _iter_actions(action.actions)
            yield from _iter_actions(action.otherwise_actions)


def _selected_invoke_target(
    source_name: str,
    text: str,
    masked_source: str,
    position: Mapping[str, object],
) -> Optional[str]:
    offset = lsp_position_to_offset(text, position)
    unit = parse_source_unit(masked_source, source_name=source_name)
    for node in unit.declarations:
        if not isinstance(node, DirectiveNode):
            continue
        for cause in node.causes:
            for path in cause.paths:
                for action in _iter_actions(path.actions):
                    if not isinstance(action, InvokeActionNode) or action.span is None:
                        continue
                    start = action.span.start.offset
                    end = action.span.end.offset
                    segment = text[start:end]
                    match = re.search(
                        r"\binvoke\s+(?P<name>" + _IDENTIFIER.pattern + r")\b",
                        segment,
                    )
                    if match is None:
                        continue
                    target_start = start + match.start("name")
                    target_end = start + match.end("name")
                    if (
                        target_start <= offset < target_end
                        and match.group("name") == action.target
                    ):
                        return action.target
    return None


def _module_segments(module_name: str) -> tuple[str, ...]:
    return tuple(module_name.split("."))


def _required_project_sources(graph: object, module_name: str) -> tuple[str, ...]:
    pending = [module_name]
    visited: set[str] = set()
    ordered_sources: list[str] = []

    while pending:
        current = pending.pop(0)
        if current in visited:
            continue
        visited.add(current)

        record = graph.find(current)
        if record is None:
            return ()
        ordered_sources.append(record.source_name)

        for imported in graph.direct_imports(current):
            if imported not in visited:
                pending.append(imported)

    return tuple(ordered_sources)


def _declaration_name_offsets(
    text: str,
    span: object,
    name: str,
) -> Optional[tuple[int, int]]:
    if not isinstance(span, SourceSpan) or type(name) is not str or not name:
        return None
    start = span.start.offset
    end = span.end.offset
    segment = text[start:end]
    match = re.search(
        r"\bdirective\s+(?P<name>" + _IDENTIFIER.pattern + r")\b",
        segment,
    )
    if match is None or match.group("name") != name:
        return None
    return start + match.start("name"), start + match.end("name")


def project_definition(
    uri: str,
    text: str,
    position: Mapping[str, object],
    open_documents: Optional[Mapping[str, str]] = None,
) -> Optional[dict[str, object]]:
    """Resolve one imported directive invocation through its manifested project."""

    try:
        active_path = _file_uri_to_path(uri)
        loaded = load_project(active_path)

        overlays: dict[Path, str] = {}
        for overlay_uri, overlay_text in dict(open_documents or {}).items():
            if type(overlay_uri) is not str or type(overlay_text) is not str:
                raise TypeError("open document overlays must map URI strings to text strings.")
            try:
                overlay_path = _file_uri_to_path(overlay_uri)
            except ValueError:
                continue
            overlays[overlay_path] = overlay_text

        current_source = next(
            (
                source
                for source in loaded.sources
                if source.path.resolve() == active_path
            ),
            None,
        )
        if current_source is None:
            return None

        effective_sources: dict[str, tuple[object, str]] = {}
        module_sources = []
        for source in loaded.sources:
            source_path = source.path.resolve()
            source_text = overlays.get(source_path, source.source)
            effective_sources[source.name] = (source, source_text)
            module_sources.append(parse_module_source(source.name, source_text))

        graph = build_module_graph(module_sources)
        current_module = next(
            (
                module_source
                for module_source in module_sources
                if module_source.source_name == current_source.name
            ),
            None,
        )
        if current_module is None or current_module.module_name is None:
            return None

        active_text = overlays.get(active_path, text)
        active_module = parse_module_source(current_source.name, active_text)
        target = _selected_invoke_target(
            current_source.name,
            active_text,
            active_module.masked_source,
            position,
        )
        if target is None:
            return None

        required_source_names = set(
            _required_project_sources(graph, current_module.module_name)
        )
        if not required_source_names or current_source.name not in required_source_names:
            return None

        resolution_sources = {
            source.name: effective_sources[source.name][1]
            for source in loaded.sources
            if source.name in required_source_names
        }
        project = build_project(resolution_sources)

        direct_imports = graph.direct_imports(current_module.module_name)
        query = ProjectResolutionQuery("directive", (target,))
        context = ProjectResolutionContext(
            current_source.name,
            _module_segments(current_module.module_name),
            tuple(_module_segments(name) for name in direct_imports),
        )
        outcome = resolve_project_contextual_query(
            project.resolution_candidate_index,
            query,
            context,
        )
        if not isinstance(outcome, ProjectResolvedBinding):
            return None

        candidate = outcome.candidate
        target_value = effective_sources.get(candidate.identity.source_name)
        if target_value is None:
            return None
        target_source, target_text = target_value
        offsets = _declaration_name_offsets(
            target_text,
            candidate.identity.span,
            candidate.identity.declared_name,
        )
        if offsets is None:
            return None

        return {
            "uri": target_source.path.resolve().as_uri(),
            "range": {
                "start": offset_to_lsp_position(target_text, offsets[0]),
                "end": offset_to_lsp_position(target_text, offsets[1]),
            },
        }
    except Exception as error:
        if isinstance(
            error,
            (
                ModuleError,
                OSError,
                ProjectManifestError,
                UnicodeError,
                ValueError,
            ),
        ) or diagnostics_from_exception(error):
            return None
        raise


__all__ = ("project_definition",)
