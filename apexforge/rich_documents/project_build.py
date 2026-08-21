"""P11.13F2 native rich-document project build integration.

This module composes already-loaded F1 package declarations with the frozen
P11.13 rich-document parser and executable-block compiler. It does not mutate
project loading, synthesize aggregate AIR, route CLI behavior, or execute
runtime semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, TYPE_CHECKING, Tuple

from air.serialization import air_to_dict
from rich_documents.compilation import (
    ApexExecutableBlockCompilation,
    compile_apex_document_blocks,
)
from rich_documents.model import ApexDocument, PackageDescriptor
from rich_documents.parser import parse_apex_document


if TYPE_CHECKING:
    from tooling.project_loader import LoadedProject, LoadedProjectSource


RICH_DOCUMENT_PROJECT_BUILD_SCHEMA = "apexforge.rich-document-project-build/v1"


@dataclass(frozen=True)
class RichDocumentProjectBuild:
    """One native package-declared rich-document project build."""

    package: PackageDescriptor
    documents: Tuple[ApexDocument, ...]
    compilations: Tuple[ApexExecutableBlockCompilation, ...]

    def __post_init__(self) -> None:
        if type(self.package) is not PackageDescriptor:
            raise TypeError(
                "RichDocumentProjectBuild.package must be an exact "
                "PackageDescriptor"
            )
        if type(self.documents) is not tuple:
            raise TypeError("RichDocumentProjectBuild.documents must be a tuple")
        if any(type(document) is not ApexDocument for document in self.documents):
            raise TypeError(
                "RichDocumentProjectBuild.documents must contain exact "
                "ApexDocument values"
            )
        if type(self.compilations) is not tuple:
            raise TypeError(
                "RichDocumentProjectBuild.compilations must be a tuple"
            )
        if any(
            type(compilation) is not ApexExecutableBlockCompilation
            for compilation in self.compilations
        ):
            raise TypeError(
                "RichDocumentProjectBuild.compilations must contain exact "
                "ApexExecutableBlockCompilation values"
            )

        if tuple(document.source_name for document in self.documents) != (
            self.package.documents
        ):
            raise ValueError(
                "RichDocumentProjectBuild document order must match "
                "PackageDescriptor.documents"
            )

        document_names = frozenset(
            document.source_name for document in self.documents
        )
        if any(
            compilation.source.source_name.split("::apexdoc::", 1)[0]
            not in document_names
            for compilation in self.compilations
        ):
            raise ValueError(
                "RichDocumentProjectBuild compilation lineage is not owned "
                "by a package document"
            )


def _loaded_source_by_name(
    loaded: LoadedProject,
) -> Dict[str, LoadedProjectSource]:
    return {source.name: source for source in loaded.sources}


def build_rich_document_project(
    loaded: LoadedProject,
) -> RichDocumentProjectBuild:
    """Build package-declared rich documents from the immutable loaded snapshot."""

    # Import lazily to preserve the rich_documents -> tooling layering boundary.
    # A top-level import would cycle through tooling.__init__ -> build_artifact
    # -> rich_documents.project_build during package initialization.
    from tooling.project_loader import LoadedProject

    if type(loaded) is not LoadedProject:
        raise TypeError(
            "build_rich_document_project requires an exact LoadedProject"
        )

    package = loaded.manifest.package
    if package is None:
        raise ValueError(
            "build_rich_document_project requires manifest package declaration"
        )
    if type(package) is not PackageDescriptor:
        raise TypeError(
            "loaded manifest package must be an exact PackageDescriptor"
        )

    sources = _loaded_source_by_name(loaded)
    documents = []
    compilations = []

    for document_name in package.documents:
        source = sources.get(document_name)
        if source is None:
            raise ValueError(
                "package document {!r} is absent from loaded project "
                "snapshot".format(document_name)
            )

        try:
            exact_text = source.source_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "package document {!r} is not valid UTF-8".format(
                    document_name
                )
            ) from exc

        document = parse_apex_document(document_name, exact_text)
        documents.append(document)
        compilations.extend(compile_apex_document_blocks(document))

    return RichDocumentProjectBuild(
        package=package,
        documents=tuple(documents),
        compilations=tuple(compilations),
    )


def _package_payload(package: PackageDescriptor) -> Dict[str, Any]:
    return {
        "id": package.package_id,
        "tier": package.tier.value,
        "version": package.version,
    }


def _document_payload(document: ApexDocument) -> Dict[str, Any]:
    return {
        "id": document.document_id,
        "path": document.source_name,
        "blocks": [
            {
                "id": block.block_id,
                "kind": block.kind.value,
                "content": block.content,
            }
            for block in document.blocks
        ],
    }


def _source_position_payload(position: Any) -> Dict[str, int]:
    return {
        "line": position.line,
        "column": position.column,
        "offset": position.offset,
    }


def _source_span_payload(span: Any) -> Dict[str, Any]:
    return {
        "source_name": span.source_name,
        "start": _source_position_payload(span.start),
        "end": _source_position_payload(span.end),
    }


def _source_map_entry_payload(entry: Any) -> Dict[str, Any]:
    return {
        "air_id": entry.air_id,
        "kind": entry.kind,
        "reference": entry.reference,
        "span": _source_span_payload(entry.span),
    }


def _executable_block_payload(
    compilation: ApexExecutableBlockCompilation,
) -> Dict[str, Any]:
    source = compilation.source
    compiled = compilation.compiled
    return {
        "document_id": source.document_id,
        "block_id": source.block_id,
        "source_name": source.source_name,
        "text": source.text,
        "air": air_to_dict(compiled.program),
        "source_map": [
            _source_map_entry_payload(entry)
            for entry in compiled.source_map.entries
        ],
    }


def rich_document_project_build_payload(
    build: RichDocumentProjectBuild,
) -> Dict[str, Any]:
    """Return the deterministic nested payload for one native document build."""

    if type(build) is not RichDocumentProjectBuild:
        raise TypeError(
            "rich_document_project_build_payload requires an exact "
            "RichDocumentProjectBuild"
        )

    return {
        "schema": RICH_DOCUMENT_PROJECT_BUILD_SCHEMA,
        "package": _package_payload(build.package),
        "documents": [
            _document_payload(document)
            for document in build.documents
        ],
        "executable_blocks": [
            _executable_block_payload(compilation)
            for compilation in build.compilations
        ],
    }


__all__ = (
    "RICH_DOCUMENT_PROJECT_BUILD_SCHEMA",
    "RichDocumentProjectBuild",
    "build_rich_document_project",
    "rich_document_project_build_payload",
)