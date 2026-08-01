"""AFP-P10-T2.3 ApexForge grammar-conformance corpus audit.

The audit executes the frozen lexer, parser, module-header pipeline, project
builder, and grammar-export verifier against a versioned positive/negative
corpus. It does not add syntax or alter compilation behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final, Mapping, Optional, Sequence, TextIO

from language.grammar import (
    CANONICAL_GRAMMAR_SHA256,
    P10_T2_GRAMMAR_VERSION,
)
from language.grammar_export import (
    CANONICAL_GRAMMAR_EXPORT_SHA256,
    P10_T2_EXPORT_VERSION,
    verify_grammar_exports,
)
from language.modules import parse_module_source
from language.parser import (
    DirectiveNode,
    FunctionNode,
    parse,
)
from language.project import build_project


P10_T2_CONFORMANCE_VERSION: Final[str] = "10-T2.3"
CONFORMANCE_SCHEMA: Final[int] = 1
CONFORMANCE_KIND: Final[str] = "apexforge.grammar-conformance"
CANONICAL_CONFORMANCE_MANIFEST: Final[str] = "corpus.json"
CANONICAL_CONFORMANCE_SHA256: Final[str] = (
    "6bc21d12b6a667ba14e384f12e9b408a8c618a5eaf11dd91824c601745170884"
)


class GrammarConformanceError(ValueError):
    """The conformance corpus or its observed behavior is invalid."""

    code: Final[str] = "APX-GRAMMAR-002"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("GrammarConformanceError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True, order=True)
class ValidSourceCase:
    case_id: str
    path: str


@dataclass(frozen=True, order=True)
class ProjectCase:
    case_id: str
    directory: str
    entry: str
    sources: tuple[str, ...]


@dataclass(frozen=True, order=True)
class InvalidSourceCase:
    case_id: str
    path: str
    pipeline: str
    expected_code: str


@dataclass(frozen=True)
class ConformanceManifest:
    aggregate_entry: str
    valid: tuple[ValidSourceCase, ...]
    projects: tuple[ProjectCase, ...]
    invalid: tuple[InvalidSourceCase, ...]


@dataclass(frozen=True)
class ConformanceAudit:
    corpus_root: Path
    valid_source_count: int
    project_count: int
    invalid_source_count: int
    source_file_count: int
    corpus_sha256: str


_ALLOWED_INVALID_PIPELINES: Final[frozenset[str]] = frozenset(
    {
        "module",
        "source",
    }
)


def _require_string(value: object, owner: str) -> str:
    if type(value) is not str or not value:
        raise GrammarConformanceError(f"{owner} must be a non-empty string.")
    return value


def _normalize_relative_path(value: object, owner: str) -> str:
    text = _require_string(value, owner)
    if "\\" in text:
        raise GrammarConformanceError(
            f"{owner} must use forward slashes; received {text!r}."
        )

    segments = text.split("/")
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or any(segment in {"", ".", ".."} for segment in segments)
        or ":" in segments[0]
    ):
        raise GrammarConformanceError(
            f"{owner} must be a safe relative path; received {text!r}."
        )
    return path.as_posix()


def _require_unique_ids(values: Sequence[object], owner: str) -> None:
    ids = tuple(getattr(value, "case_id", None) for value in values)
    if len(ids) != len(set(ids)):
        raise GrammarConformanceError(f"{owner} contains duplicate case IDs.")


def _require_mapping(value: object, owner: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise GrammarConformanceError(f"{owner} must be a JSON object.")
    return value


def _require_list(value: object, owner: str) -> list[object]:
    if not isinstance(value, list):
        raise GrammarConformanceError(f"{owner} must be a JSON array.")
    return value


def load_conformance_manifest(corpus_root: object) -> ConformanceManifest:
    """Load and strictly validate the schema-1 conformance manifest."""

    try:
        root = Path(corpus_root)  # type: ignore[arg-type]
    except TypeError as exc:
        raise GrammarConformanceError(
            "Conformance corpus root must be path-like."
        ) from exc

    manifest_path = root / CANONICAL_CONFORMANCE_MANIFEST
    if not manifest_path.is_file():
        raise GrammarConformanceError(
            f"Missing conformance manifest {manifest_path}."
        )

    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GrammarConformanceError(
            f"Could not read conformance manifest {manifest_path}: {exc}."
        ) from exc

    mapping = _require_mapping(document, "Conformance manifest")

    expected_contract = {
        "schema": CONFORMANCE_SCHEMA,
        "kind": CONFORMANCE_KIND,
        "version": P10_T2_CONFORMANCE_VERSION,
        "grammar_version": P10_T2_GRAMMAR_VERSION,
        "grammar_sha256": CANONICAL_GRAMMAR_SHA256,
        "grammar_export_version": P10_T2_EXPORT_VERSION,
        "grammar_export_sha256": CANONICAL_GRAMMAR_EXPORT_SHA256,
    }
    for key, expected in expected_contract.items():
        if mapping.get(key) != expected:
            raise GrammarConformanceError(
                f"Conformance manifest field {key!r} must equal {expected!r}."
            )

    aggregate_entry = _require_string(
        mapping.get("aggregate_entry"),
        "Conformance aggregate_entry",
    )

    valid_cases: list[ValidSourceCase] = []
    for index, raw_case in enumerate(_require_list(mapping.get("valid"), "valid")):
        case = _require_mapping(raw_case, f"valid[{index}]")
        valid_cases.append(
            ValidSourceCase(
                case_id=_require_string(case.get("id"), f"valid[{index}].id"),
                path=_normalize_relative_path(
                    case.get("path"),
                    f"valid[{index}].path",
                ),
            )
        )

    project_cases: list[ProjectCase] = []
    for index, raw_case in enumerate(
        _require_list(mapping.get("projects"), "projects")
    ):
        case = _require_mapping(raw_case, f"projects[{index}]")
        raw_sources = _require_list(
            case.get("sources"),
            f"projects[{index}].sources",
        )
        sources = tuple(
            _normalize_relative_path(
                source,
                f"projects[{index}].sources[{source_index}]",
            )
            for source_index, source in enumerate(raw_sources)
        )
        if not sources or len(sources) != len(set(sources)):
            raise GrammarConformanceError(
                f"projects[{index}].sources must contain unique source names."
            )
        project_cases.append(
            ProjectCase(
                case_id=_require_string(case.get("id"), f"projects[{index}].id"),
                directory=_normalize_relative_path(
                    case.get("directory"),
                    f"projects[{index}].directory",
                ),
                entry=_require_string(
                    case.get("entry"),
                    f"projects[{index}].entry",
                ),
                sources=sources,
            )
        )

    invalid_cases: list[InvalidSourceCase] = []
    for index, raw_case in enumerate(
        _require_list(mapping.get("invalid"), "invalid")
    ):
        case = _require_mapping(raw_case, f"invalid[{index}]")
        pipeline = _require_string(
            case.get("pipeline"),
            f"invalid[{index}].pipeline",
        )
        if pipeline not in _ALLOWED_INVALID_PIPELINES:
            raise GrammarConformanceError(
                f"invalid[{index}].pipeline must be one of "
                f"{tuple(sorted(_ALLOWED_INVALID_PIPELINES))}."
            )
        expected_code = _require_string(
            case.get("expected_code"),
            f"invalid[{index}].expected_code",
        )
        if not expected_code.startswith("APX-"):
            raise GrammarConformanceError(
                f"invalid[{index}].expected_code must be an ApexForge code."
            )
        invalid_cases.append(
            InvalidSourceCase(
                case_id=_require_string(case.get("id"), f"invalid[{index}].id"),
                path=_normalize_relative_path(
                    case.get("path"),
                    f"invalid[{index}].path",
                ),
                pipeline=pipeline,
                expected_code=expected_code,
            )
        )

    if not valid_cases or not project_cases or not invalid_cases:
        raise GrammarConformanceError(
            "The conformance manifest requires valid, project, and invalid cases."
        )

    _require_unique_ids(valid_cases, "valid")
    _require_unique_ids(project_cases, "projects")
    _require_unique_ids(invalid_cases, "invalid")

    all_ids = tuple(
        case.case_id
        for group in (valid_cases, project_cases, invalid_cases)
        for case in group
    )
    if len(all_ids) != len(set(all_ids)):
        raise GrammarConformanceError(
            "Conformance case IDs must be unique across all groups."
        )

    return ConformanceManifest(
        aggregate_entry=aggregate_entry,
        valid=tuple(valid_cases),
        projects=tuple(project_cases),
        invalid=tuple(invalid_cases),
    )


def _expected_corpus_paths(manifest: ConformanceManifest) -> tuple[str, ...]:
    paths: list[str] = [CANONICAL_CONFORMANCE_MANIFEST]
    paths.extend(case.path for case in manifest.valid)
    for project in manifest.projects:
        paths.extend(
            str(PurePosixPath(project.directory) / source)
            for source in project.sources
        )
    paths.extend(case.path for case in manifest.invalid)
    return tuple(sorted(paths))


def corpus_fingerprint(corpus_root: object) -> str:
    """Hash exact manifest and source bytes in deterministic relative-path order."""

    try:
        root = Path(corpus_root)  # type: ignore[arg-type]
    except TypeError as exc:
        raise GrammarConformanceError(
            "Conformance corpus root must be path-like."
        ) from exc

    manifest = load_conformance_manifest(root)
    expected_paths = _expected_corpus_paths(manifest)
    actual_paths = tuple(
        sorted(
            {
                CANONICAL_CONFORMANCE_MANIFEST,
                *(
                    path.relative_to(root).as_posix()
                    for path in root.rglob("*.apex")
                    if path.is_file()
                ),
            }
        )
    )
    if actual_paths != expected_paths:
        missing = tuple(path for path in expected_paths if path not in actual_paths)
        unexpected = tuple(path for path in actual_paths if path not in expected_paths)
        raise GrammarConformanceError(
            "Conformance source inventory differs from the manifest; "
            f"missing={missing}, unexpected={unexpected}."
        )

    digest = hashlib.sha256()
    for relative_name in expected_paths:
        path = root / PurePosixPath(relative_name)
        if not path.is_file():
            raise GrammarConformanceError(
                f"Missing conformance file {relative_name!r}."
            )
        relative_bytes = relative_name.encode("utf-8")
        data = path.read_bytes()
        digest.update(len(relative_bytes).to_bytes(4, "big"))
        digest.update(relative_bytes)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _read_source(root: Path, relative_name: str) -> str:
    path = root / PurePosixPath(relative_name)
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise GrammarConformanceError(
            f"Could not read conformance source {relative_name!r}: {exc}."
        ) from exc


def _diagnostic_codes(error: BaseException) -> tuple[str, ...]:
    codes: list[str] = []

    diagnostic = getattr(error, "diagnostic", None)
    code = getattr(diagnostic, "code", None)
    if type(code) is str and code:
        codes.append(code)

    diagnostics = getattr(error, "diagnostics", None)
    if diagnostics is not None:
        for item in tuple(diagnostics):
            item_code = getattr(item, "code", None)
            if type(item_code) is str and item_code and item_code not in codes:
                codes.append(item_code)

    cause = getattr(error, "cause", None)
    if isinstance(cause, BaseException) and cause is not error:
        for cause_code in _diagnostic_codes(cause):
            if cause_code not in codes:
                codes.append(cause_code)

    return tuple(codes)


def _parse_source(source_name: str, source: str) -> object:
    unit = parse_module_source(source_name, source)
    return parse(unit.masked_source, source_name=source_name)


def _audit_invalid_case(root: Path, case: InvalidSourceCase) -> None:
    source = _read_source(root, case.path)

    try:
        if case.pipeline == "module":
            parse_module_source(case.path, source)
        else:
            _parse_source(case.path, source)
    except Exception as error:
        codes = _diagnostic_codes(error)
        if case.expected_code not in codes:
            raise GrammarConformanceError(
                f"Invalid case {case.case_id!r} expected {case.expected_code}, "
                f"but observed {codes or (type(error).__name__,)}."
            ) from error
        return

    raise GrammarConformanceError(
        f"Invalid case {case.case_id!r} unexpectedly passed."
    )


def audit_conformance_corpus(corpus_root: object) -> ConformanceAudit:
    """Execute the complete deterministic T2.3 syntax audit."""

    try:
        root = Path(corpus_root)  # type: ignore[arg-type]
    except TypeError as exc:
        raise GrammarConformanceError(
            "Conformance corpus root must be path-like."
        ) from exc

    if not root.is_dir():
        raise GrammarConformanceError(
            f"Conformance corpus root is not a directory: {root}."
        )

    manifest = load_conformance_manifest(root)
    observed_fingerprint = corpus_fingerprint(root)
    if observed_fingerprint != CANONICAL_CONFORMANCE_SHA256:
        raise GrammarConformanceError(
            "Conformance corpus fingerprint changed; expected "
            f"{CANONICAL_CONFORMANCE_SHA256}, received {observed_fingerprint}."
        )

    try:
        verify_grammar_exports(root.parent)
    except Exception as exc:
        raise GrammarConformanceError(
            f"Frozen grammar exports failed verification: {exc}."
        ) from exc

    aggregate_sources: dict[str, str] = {}
    for case in manifest.valid:
        source = _read_source(root, case.path)
        try:
            node = _parse_source(case.path, source)
        except Exception as exc:
            raise GrammarConformanceError(
                f"Valid source case {case.case_id!r} failed: {exc}."
            ) from exc

        # The parser recognizes six top-level declaration families. The
        # frozen ProjectBuilder boundary currently accepts only declarations
        # whose compiler result is an AIRProgram: directives and functions.
        # Role compilation returns AIRRole directly, while authority, principal,
        # and workflow lowering is not available. Those declarations remain
        # syntax-conformance cases and are intentionally excluded here.
        if isinstance(node, (DirectiveNode, FunctionNode)):
            aggregate_sources[case.path] = source

    if not aggregate_sources:
        raise GrammarConformanceError(
            "The valid corpus contains no compiler-supported aggregate sources."
        )

    try:
        build_project(
            aggregate_sources,
            entry=manifest.aggregate_entry,
        )
    except Exception as exc:
        raise GrammarConformanceError(
            f"Aggregate valid project failed: {exc}."
        ) from exc

    for project in manifest.projects:
        project_sources: dict[str, str] = {}
        for source_name in project.sources:
            relative_name = str(PurePosixPath(project.directory) / source_name)
            source = _read_source(root, relative_name)
            try:
                _parse_source(relative_name, source)
            except Exception as exc:
                raise GrammarConformanceError(
                    f"Valid project {project.case_id!r} source "
                    f"{source_name!r} failed: {exc}."
                ) from exc
            project_sources[source_name] = source

        try:
            build_project(project_sources, entry=project.entry)
        except Exception as exc:
            raise GrammarConformanceError(
                f"Valid project case {project.case_id!r} failed: {exc}."
            ) from exc

    for case in manifest.invalid:
        _audit_invalid_case(root, case)

    source_file_count = sum(1 for path in root.rglob("*.apex") if path.is_file())
    return ConformanceAudit(
        corpus_root=root.resolve(),
        valid_source_count=len(manifest.valid),
        project_count=1 + len(manifest.projects),
        invalid_source_count=len(manifest.invalid),
        source_file_count=source_file_count,
        corpus_sha256=observed_fingerprint,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m language.grammar_conformance",
        description="Audit the frozen ApexForge grammar-conformance corpus.",
    )
    parser.add_argument(
        "corpus_root",
        nargs="?",
        default="spec/conformance",
        help="conformance corpus directory (default: spec/conformance)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="accepted for explicit verification-mode invocation",
    )
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Run the standalone T2.3 conformance audit."""

    parser = _build_parser()
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)
    _ = arguments.check

    try:
        audit = audit_conformance_corpus(arguments.corpus_root)
    except GrammarConformanceError as error:
        print(str(error), file=stderr)
        return 1

    print(f"Verified corpus: {audit.corpus_root}", file=stdout)
    print(f"Valid sources: {audit.valid_source_count}", file=stdout)
    print(f"Project builds: {audit.project_count}", file=stdout)
    print(f"Invalid diagnostics: {audit.invalid_source_count}", file=stdout)
    print(f"Corpus SHA-256: {audit.corpus_sha256}", file=stdout)
    return 0


__all__ = (
    "CANONICAL_CONFORMANCE_MANIFEST",
    "CANONICAL_CONFORMANCE_SHA256",
    "CONFORMANCE_KIND",
    "CONFORMANCE_SCHEMA",
    "ConformanceAudit",
    "ConformanceManifest",
    "GrammarConformanceError",
    "InvalidSourceCase",
    "P10_T2_CONFORMANCE_VERSION",
    "ProjectCase",
    "ValidSourceCase",
    "audit_conformance_corpus",
    "corpus_fingerprint",
    "load_conformance_manifest",
    "main",
)


if __name__ == "__main__":
    raise SystemExit(main())
