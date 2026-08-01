"""AFP-P10-T4.9 ApexForge workspace-symbol search.

The analyzer builds a deterministic, read-only symbol view across ``.apex``
files beneath one file-based workspace root. Open-document text overlays the
on-disk snapshot so unsaved declarations can participate without introducing
cross-file linking, references, rename, compilation, or runtime execution.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from typing import Final, Iterable, Mapping, Optional
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from language_server.symbols import document_symbols


P10_T4_WORKSPACE_SYMBOL_VERSION: Final[str] = "10-T4.9"
WORKSPACE_SYMBOL_SCHEMA: Final[int] = 1
WORKSPACE_SYMBOL_KIND: Final[str] = "apexforge.language-server-workspace-symbols"
WORKSPACE_SYMBOL_METHOD: Final[str] = "workspace/symbol"
MAX_WORKSPACE_FILES: Final[int] = 4096
MAX_SYMBOL_RESULTS: Final[int] = 256

_IGNORED_DIRECTORIES: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "venv",
    }
)

_INDEXED_DETAILS: Final[frozenset[str]] = frozenset(
    {
        "module",
        "function",
        "directive",
        "event",
        "cause",
        "workflow",
        "capability",
        "role",
        "principal",
    }
)


def _require_uri(value: object, owner: str) -> str:
    if type(value) is not str or not value or ":" not in value:
        raise ValueError(f"{owner} must be a non-empty absolute URI.")
    return value


def _require_query(value: object) -> str:
    if type(value) is not str:
        raise TypeError("workspace/symbol query must be a string.")
    return value


def _file_uri_to_path(uri: str) -> Path:
    value = _require_uri(uri, "workspace root URI")
    parsed = urlparse(value)
    if parsed.scheme.casefold() != "file":
        raise ValueError("ApexForge workspace symbols require a file:// root URI.")
    raw_path = url2pathname(unquote(parsed.path))
    if parsed.netloc and parsed.netloc.casefold() != "localhost":
        raw_path = f"//{parsed.netloc}{raw_path}"
    if os.name == "nt" and re.match(r"^/[A-Za-z]:", raw_path):
        raw_path = raw_path[1:]
    path = Path(raw_path)
    if not path.is_absolute():
        raise ValueError("workspace root URI must resolve to an absolute path.")
    return path.resolve()


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except (OSError, ValueError):
        return False
    return True


def _iter_workspace_files(root: Path) -> tuple[Path, ...]:
    values: list[Path] = []
    for directory, names, files in os.walk(root):
        names[:] = sorted(
            (
                name
                for name in names
                if name.casefold() not in _IGNORED_DIRECTORIES
            ),
            key=lambda item: (item.casefold(), item),
        )
        for name in sorted(files, key=lambda item: (item.casefold(), item)):
            if not name.casefold().endswith(".apex"):
                continue
            values.append(Path(directory) / name)
            if len(values) >= MAX_WORKSPACE_FILES:
                return tuple(values)
    return tuple(values)


def _selection_start(symbol: Mapping[str, object]) -> tuple[int, int]:
    selection = symbol.get("selectionRange")
    if type(selection) is not dict:
        return (2**31 - 1, 2**31 - 1)
    start = selection.get("start")
    if type(start) is not dict:
        return (2**31 - 1, 2**31 - 1)
    line = start.get("line")
    character = start.get("character")
    return (
        line if type(line) is int else 2**31 - 1,
        character if type(character) is int else 2**31 - 1,
    )


def _detail_is_indexed(detail: str) -> bool:
    if detail in _INDEXED_DETAILS:
        return True
    return (
        detail.startswith("function")
        or detail.startswith("state")
        or detail.startswith("path @")
        or detail == "authority"
        or detail.startswith("authority extends ")
    )


def _flatten_document_symbols(
    uri: str,
    symbols: Iterable[Mapping[str, object]],
    *,
    container: Optional[str] = None,
) -> tuple[dict[str, object], ...]:
    values: list[dict[str, object]] = []
    for raw in symbols:
        name = raw.get("name")
        kind = raw.get("kind")
        detail = raw.get("detail")
        selection_range = raw.get("selectionRange")
        if (
            type(name) is str
            and name
            and type(kind) is int
            and type(detail) is str
            and type(selection_range) is dict
            and _detail_is_indexed(detail)
        ):
            item: dict[str, object] = {
                "name": name,
                "kind": kind,
                "location": {
                    "uri": uri,
                    "range": dict(selection_range),
                },
            }
            if container:
                item["containerName"] = container
            values.append(item)

        children = raw.get("children")
        if type(children) is list:
            next_container = name if type(name) is str and name else container
            values.extend(
                _flatten_document_symbols(
                    uri,
                    (
                        child
                        for child in children
                        if type(child) is dict
                    ),
                    container=next_container,
                )
            )
    return tuple(values)


def _query_score(symbol: Mapping[str, object], query: str) -> Optional[tuple[int, int]]:
    folded = query.casefold().strip()
    if not folded:
        return (4, 0)
    tokens = tuple(token for token in folded.split() if token)
    name = str(symbol.get("name", ""))
    container = str(symbol.get("containerName", ""))
    name_folded = name.casefold()
    haystack = f"{name_folded} {container.casefold()}"
    if not all(token in haystack for token in tokens):
        return None
    if name_folded == folded:
        return (0, len(name))
    if name_folded.startswith(folded):
        return (1, len(name))
    if folded in name_folded:
        return (2, len(name))
    return (3, len(name))


def workspace_symbols(
    root_uri: object,
    query: object,
    open_documents: Optional[Mapping[str, str]] = None,
) -> tuple[dict[str, object], ...]:
    """Return deterministic LSP ``SymbolInformation`` values for one workspace."""

    root = _file_uri_to_path(_require_uri(root_uri, "workspace root URI"))
    text_query = _require_query(query)
    if not root.is_dir():
        return ()

    overlays: dict[Path, tuple[str, str]] = {}
    for uri, text in dict(open_documents or {}).items():
        if type(uri) is not str or type(text) is not str:
            raise TypeError("open document overlays must map URI strings to text strings.")
        try:
            path = _file_uri_to_path(uri)
        except ValueError:
            continue
        if path.suffix.casefold() == ".apex" and _path_is_within(path, root):
            overlays[path] = (uri, text)

    sources: dict[Path, tuple[str, str]] = {}
    for path in _iter_workspace_files(root):
        resolved = path.resolve()
        if resolved in overlays:
            sources[resolved] = overlays[resolved]
            continue
        try:
            sources[resolved] = (resolved.as_uri(), path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            continue
    for path, value in overlays.items():
        sources[path] = value

    ranked: list[tuple[tuple[object, ...], dict[str, object]]] = []
    for path in sorted(sources, key=lambda item: (str(item).casefold(), str(item))):
        uri, text = sources[path]
        for symbol in _flatten_document_symbols(uri, document_symbols(uri, text)):
            score = _query_score(symbol, text_query)
            if score is None:
                continue
            location = symbol["location"]
            assert type(location) is dict
            position = _selection_start(
                {"selectionRange": location.get("range")}
            )
            key = (
                score,
                str(symbol["name"]).casefold(),
                str(symbol["name"]),
                str(symbol.get("containerName", "")).casefold(),
                uri.casefold(),
                uri,
                position,
            )
            ranked.append((key, symbol))

    ranked.sort(key=lambda item: item[0])
    return tuple(symbol for _, symbol in ranked[:MAX_SYMBOL_RESULTS])


def workspace_symbols_contract() -> Mapping[str, object]:
    return {
        "schema": WORKSPACE_SYMBOL_SCHEMA,
        "kind": WORKSPACE_SYMBOL_KIND,
        "workspace_symbol_version": P10_T4_WORKSPACE_SYMBOL_VERSION,
        "method": WORKSPACE_SYMBOL_METHOD,
        "root": "one file-based workspace folder",
        "source_files": "recursive .apex files",
        "open_document_overlay": True,
        "ignored_directories": tuple(sorted(_IGNORED_DIRECTORIES)),
        "indexed_details": tuple(sorted(_INDEXED_DETAILS)),
        "indexed_detail_prefixes": ("authority", "function", "path @", "state"),
        "query": {
            "case_sensitive": False,
            "token_mode": "all whitespace-separated tokens",
            "ranking": ("exact", "prefix", "substring", "container"),
        },
        "limits": {
            "workspace_files": MAX_WORKSPACE_FILES,
            "symbol_results": MAX_SYMBOL_RESULTS,
        },
        "result": "SymbolInformation[]",
        "features_deferred": (
            "persistent_index",
            "cross_file_definition",
            "workspace_references",
            "cross_file_rename",
            "workspace_symbol_resolve",
            "formatting",
        ),
    }


def workspace_symbols_fingerprint() -> str:
    payload = json.dumps(
        workspace_symbols_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# Filled after the public contract above is serialized.
CANONICAL_WORKSPACE_SYMBOLS_SHA256: Final[str] = "b163f9c607f9c592d3e1371788f99fc0ebaa1f271bc6e17ae183149de82ccf85"


__all__ = (
    "CANONICAL_WORKSPACE_SYMBOLS_SHA256",
    "MAX_SYMBOL_RESULTS",
    "MAX_WORKSPACE_FILES",
    "P10_T4_WORKSPACE_SYMBOL_VERSION",
    "WORKSPACE_SYMBOL_KIND",
    "WORKSPACE_SYMBOL_METHOD",
    "WORKSPACE_SYMBOL_SCHEMA",
    "workspace_symbols",
    "workspace_symbols_contract",
    "workspace_symbols_fingerprint",
)
