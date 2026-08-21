"""AFP-P10-T1.1 deterministic ApexForge project-manifest model.

The tooling manifest deliberately lists source files explicitly. The canonical
ApexForge source extension remains a P10-T2 decision and is not embedded here.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping, Optional, Tuple, Union

from rich_documents.model import PackageDescriptor, PackageTier


P10_T1_TOOLING_VERSION = "10-T1.1"
PROJECT_MANIFEST_NAME = "apexforge.json"
PROJECT_MANIFEST_SCHEMA = 1

_PROJECT_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
_ALLOWED_FIELDS = frozenset(("schema", "name", "sources", "entry", "package"))
_PACKAGE_ALLOWED_FIELDS = frozenset(("id", "tier", "version", "documents"))


class ProjectManifestError(ValueError):
    """Deterministic project-manifest validation failure."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        manifest_path: Optional[Path] = None,
    ) -> None:
        if type(code) is not str or not code:
            raise ValueError("ProjectManifestError.code must be non-empty.")
        if type(message) is not str or not message:
            raise ValueError("ProjectManifestError.message must be non-empty.")

        self.code = code
        self.message = message
        self.manifest_path = (
            Path(manifest_path) if manifest_path is not None else None
        )

        location = (
            f" ({self.manifest_path})"
            if self.manifest_path is not None
            else ""
        )
        super().__init__(f"[{code}] {message}{location}")


def _contains_control_character(value: str) -> bool:
    return any(
        ord(character) < 32 or ord(character) == 127
        for character in value
    )


def _normalize_project_name(value: Any) -> str:
    if type(value) is not str:
        raise ProjectManifestError(
            code="APX-TOOL-004",
            message=(
                "Project name must be a string; "
                f"received {type(value).__name__}."
            ),
        )

    normalized = value.strip()
    if not _PROJECT_NAME_PATTERN.fullmatch(normalized):
        raise ProjectManifestError(
            code="APX-TOOL-004",
            message=(
                "Project name must begin with an ASCII letter and contain "
                "only ASCII letters, digits, underscores, or hyphens; "
                "maximum length is 64."
            ),
        )
    return normalized


def _normalize_source_path(value: Any, *, index: int) -> str:
    if type(value) is not str:
        raise ProjectManifestError(
            code="APX-TOOL-005",
            message=(
                f"Project source[{index}] must be a string; "
                f"received {type(value).__name__}."
            ),
        )

    stripped = value.strip()
    if not stripped:
        raise ProjectManifestError(
            code="APX-TOOL-005",
            message=f"Project source[{index}] cannot be empty.",
        )
    if _contains_control_character(stripped):
        raise ProjectManifestError(
            code="APX-TOOL-005",
            message=(
                f"Project source[{index}] contains a control character."
            ),
        )

    normalized = stripped.replace("\\", "/")

    if normalized.startswith("/") or normalized.startswith("//"):
        raise ProjectManifestError(
            code="APX-TOOL-005",
            message=(
                f"Project source[{index}] must be relative to the project root."
            ),
        )
    if re.match(r"^[A-Za-z]:", normalized):
        raise ProjectManifestError(
            code="APX-TOOL-005",
            message=(
                f"Project source[{index}] must not contain a drive prefix."
            ),
        )

    parts = normalized.split("/")
    for part in parts:
        if part in ("", ".", ".."):
            raise ProjectManifestError(
                code="APX-TOOL-005",
                message=(
                    f"Project source[{index}] contains an unsafe path segment."
                ),
            )
        if part != part.strip():
            raise ProjectManifestError(
                code="APX-TOOL-005",
                message=(
                    f"Project source[{index}] contains segment-edge whitespace."
                ),
            )

    return "/".join(parts)


def _normalize_entry(value: Any) -> Optional[str]:
    if value is None:
        return None
    if type(value) is not str:
        raise ProjectManifestError(
            code="APX-TOOL-008",
            message=(
                "Project entry must be a string or null; "
                f"received {type(value).__name__}."
            ),
        )

    normalized = value.strip()
    if not normalized:
        raise ProjectManifestError(
            code="APX-TOOL-008",
            message="Project entry cannot be empty.",
        )
    if len(normalized) > 256:
        raise ProjectManifestError(
            code="APX-TOOL-008",
            message="Project entry cannot exceed 256 Unicode code points.",
        )
    if _contains_control_character(normalized):
        raise ProjectManifestError(
            code="APX-TOOL-008",
            message="Project entry contains a control character.",
        )
    return normalized


def _package_error(message: str) -> ProjectManifestError:
    return ProjectManifestError(code="APX-TOOL-009", message=message)


def _normalize_manifest_package(
    value: Optional[PackageDescriptor],
    *,
    sources: Tuple[str, ...],
) -> Optional[PackageDescriptor]:
    if value is None:
        return None
    if type(value) is not PackageDescriptor:
        raise _package_error(
            "Project package must be an exact PackageDescriptor or None; "
            "received {}.".format(type(value).__name__)
        )
    if value.metadata:
        raise _package_error(
            "Project manifest package metadata is not represented in P11.13F1."
        )

    documents = []
    seen = set()
    for index, document in enumerate(value.documents):
        try:
            normalized = _normalize_source_path(document, index=index)
        except ProjectManifestError as exc:
            raise _package_error(
                "Project package document[{}] is invalid: {}.".format(
                    index,
                    exc.message,
                )
            ) from exc
        if not normalized.endswith(".apexdoc"):
            raise _package_error(
                "Project package document[{}] must end in lowercase "
                "'.apexdoc'.".format(index)
            )
        if normalized not in sources:
            raise _package_error(
                "Project package document {!r} is not declared in "
                "manifest sources.".format(normalized)
            )
        if normalized in seen:
            raise _package_error(
                "Project package contains duplicate document {!r}.".format(
                    normalized
                )
            )
        seen.add(normalized)
        documents.append(normalized)

    return PackageDescriptor(
        package_id=value.package_id,
        tier=value.tier,
        version=value.version,
        documents=tuple(documents),
        metadata=(),
    )


def _package_from_mapping(
    value: Any,
    *,
    sources: Tuple[str, ...],
) -> Optional[PackageDescriptor]:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise _package_error(
            "ApexForge manifest field 'package' must be a JSON object or null; "
            "received {}.".format(type(value).__name__)
        )

    unknown = tuple(
        sorted(
            (str(key) for key in value.keys() if key not in _PACKAGE_ALLOWED_FIELDS),
            key=lambda item: (item.casefold(), item),
        )
    )
    if unknown:
        raise _package_error(
            "ApexForge manifest package contains unknown field(s): "
            + ", ".join(repr(field) for field in unknown)
            + "."
        )

    missing = tuple(
        field
        for field in ("id", "tier", "version", "documents")
        if field not in value
    )
    if missing:
        raise _package_error(
            "ApexForge manifest package is missing required field(s): "
            + ", ".join(repr(field) for field in missing)
            + "."
        )

    tier_value = value["tier"]
    if type(tier_value) is not str:
        raise _package_error("ApexForge manifest package tier must be a string.")
    try:
        tier = PackageTier(tier_value)
    except ValueError as exc:
        raise _package_error(
            "ApexForge manifest package tier must be one of: "
            + ", ".join(repr(item.value) for item in PackageTier)
            + "."
        ) from exc

    documents = value["documents"]
    if type(documents) is not list:
        raise _package_error(
            "ApexForge manifest package field 'documents' must be a JSON array."
        )

    try:
        descriptor = PackageDescriptor(
            package_id=value["id"],
            tier=tier,
            version=value["version"],
            documents=tuple(documents),
            metadata=(),
        )
    except (TypeError, ValueError) as exc:
        raise _package_error(str(exc)) from exc

    return _normalize_manifest_package(descriptor, sources=sources)


@dataclass(frozen=True)
class ProjectManifest:
    """One validated, immutable ApexForge project manifest."""

    name: str
    sources: Tuple[str, ...]
    entry: Optional[str] = None
    schema: int = PROJECT_MANIFEST_SCHEMA
    package: Optional[PackageDescriptor] = None

    def __post_init__(self) -> None:
        if type(self.schema) is not int or self.schema != PROJECT_MANIFEST_SCHEMA:
            raise ProjectManifestError(
                code="APX-TOOL-003",
                message=(
                    "Unsupported ApexForge manifest schema "
                    f"{self.schema!r}; expected {PROJECT_MANIFEST_SCHEMA}."
                ),
            )

        normalized_name = _normalize_project_name(self.name)

        try:
            raw_sources = tuple(self.sources)
        except TypeError as exc:
            raise ProjectManifestError(
                code="APX-TOOL-005",
                message="Project sources must be iterable.",
            ) from exc

        if not raw_sources:
            raise ProjectManifestError(
                code="APX-TOOL-005",
                message="ApexForge project requires at least one source file.",
            )

        normalized_sources = tuple(
            _normalize_source_path(value, index=index)
            for index, value in enumerate(raw_sources)
        )

        seen = {}
        for source in normalized_sources:
            key = source.casefold()
            previous = seen.get(key)
            if previous is not None:
                raise ProjectManifestError(
                    code="APX-TOOL-005",
                    message=(
                        f"Duplicate project source {source!r}; "
                        f"conflicts with {previous!r}."
                    ),
                )
            seen[key] = source

        canonical_sources = tuple(
            sorted(
                normalized_sources,
                key=lambda value: (value.casefold(), value),
            )
        )

        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "sources", canonical_sources)
        object.__setattr__(self, "entry", _normalize_entry(self.entry))
        object.__setattr__(
            self,
            "package",
            _normalize_manifest_package(
                self.package,
                sources=canonical_sources,
            ),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProjectManifest":
        if not isinstance(value, Mapping):
            raise ProjectManifestError(
                code="APX-TOOL-003",
                message=(
                    "ApexForge manifest root must be a JSON object; "
                    f"received {type(value).__name__}."
                ),
            )

        unknown = tuple(
            sorted(
                (str(key) for key in value.keys() if key not in _ALLOWED_FIELDS),
                key=lambda item: (item.casefold(), item),
            )
        )
        if unknown:
            raise ProjectManifestError(
                code="APX-TOOL-003",
                message=(
                    "ApexForge manifest contains unknown field(s): "
                    + ", ".join(repr(field) for field in unknown)
                    + "."
                ),
            )

        missing = tuple(
            field
            for field in ("schema", "name", "sources")
            if field not in value
        )
        if missing:
            raise ProjectManifestError(
                code="APX-TOOL-003",
                message=(
                    "ApexForge manifest is missing required field(s): "
                    + ", ".join(repr(field) for field in missing)
                    + "."
                ),
            )

        sources = value["sources"]
        if type(sources) is not list:
            raise ProjectManifestError(
                code="APX-TOOL-005",
                message=(
                    "ApexForge manifest field 'sources' must be a JSON array."
                ),
            )

        normalized_sources = tuple(
            _normalize_source_path(source, index=index)
            for index, source in enumerate(sources)
        )
        canonical_sources = tuple(
            sorted(
                normalized_sources,
                key=lambda item: (item.casefold(), item),
            )
        )

        return cls(
            schema=value["schema"],
            name=value["name"],
            sources=tuple(sources),
            entry=value.get("entry"),
            package=_package_from_mapping(
                value.get("package"),
                sources=canonical_sources,
            ),
        )

    def to_mapping(self) -> Mapping[str, Any]:
        value = {
            "schema": self.schema,
            "name": self.name,
            "sources": list(self.sources),
            "entry": self.entry,
        }
        if self.package is not None:
            value["package"] = {
                "id": self.package.package_id,
                "tier": self.package.tier.value,
                "version": self.package.version,
                "documents": list(self.package.documents),
            }
        return value

    def canonical_json(self) -> str:
        """Return one deterministic UTF-8-safe JSON representation."""

        return (
            json.dumps(
                self.to_mapping(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


def load_project_manifest(
    path: Union[str, Path],
) -> ProjectManifest:
    """Load and validate one ``apexforge.json`` file."""

    manifest_path = Path(path)

    if not manifest_path.is_file():
        raise ProjectManifestError(
            code="APX-TOOL-001",
            message="ApexForge project manifest was not found.",
            manifest_path=manifest_path,
        )

    try:
        raw_text = manifest_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ProjectManifestError(
            code="APX-TOOL-002",
            message="ApexForge project manifest is not valid UTF-8.",
            manifest_path=manifest_path,
        ) from exc
    except OSError as exc:
        raise ProjectManifestError(
            code="APX-TOOL-001",
            message=f"Unable to read ApexForge project manifest: {exc}.",
            manifest_path=manifest_path,
        ) from exc

    try:
        raw_value = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ProjectManifestError(
            code="APX-TOOL-002",
            message=(
                "Invalid ApexForge manifest JSON at "
                f"line {exc.lineno}, column {exc.colno}: {exc.msg}."
            ),
            manifest_path=manifest_path,
        ) from exc

    try:
        return ProjectManifest.from_mapping(raw_value)
    except ProjectManifestError as exc:
        if exc.manifest_path is not None:
            raise
        raise ProjectManifestError(
            code=exc.code,
            message=exc.message,
            manifest_path=manifest_path,
        ) from exc


__all__ = (
    "P10_T1_TOOLING_VERSION",
    "PROJECT_MANIFEST_NAME",
    "PROJECT_MANIFEST_SCHEMA",
    "ProjectManifest",
    "ProjectManifestError",
    "load_project_manifest",
)