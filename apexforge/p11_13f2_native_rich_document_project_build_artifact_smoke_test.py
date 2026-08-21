from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from air.serialization import air_to_dict
import rich_documents.project_build as project_build_owner
from rich_documents.model import DocumentBlockKind
from rich_documents.project_build import (
    RICH_DOCUMENT_PROJECT_BUILD_SCHEMA,
    RichDocumentProjectBuild,
    build_rich_document_project,
    rich_document_project_build_payload,
)
from tooling.build_artifact import (
    BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
    BUILD_ARTIFACT_SCHEMA_V3,
    CanonicalBuildArtifact,
    canonical_json_bytes,
    construct_rich_document_build_artifact,
    write_build_artifact_atomic,
)
from tooling.project_loader import LoadedProject, LoadedProjectSource, load_project


EXPECTED_F1_COMMIT = "b79ab744677cf888031ebeab24833210ceac0676"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def raises(error_type, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except error_type as error:
        return error
    except Exception as error:
        raise AssertionError(
            "expected {}, got {}: {}".format(
                error_type.__name__,
                type(error).__name__,
                error,
            )
        )
    raise AssertionError("expected {}".format(error_type.__name__))


def _write_package_project(root: Path):
    non_apex_kind = next(
        kind for kind in DocumentBlockKind if kind is not DocumentBlockKind.APEX
    )

    exact_z = (
        "@apexdoc Zed\r\n"
        "@block {} intro\r\n"
        "Zed line\r\n"
        "@endblock\r\n"
    ).format(non_apex_kind.value).encode("utf-8")

    exact_a = (
        "@apexdoc Alpha\n"
        "@block {} intro\n"
        "Alpha line\n"
        "@endblock\n"
    ).format(non_apex_kind.value).encode("utf-8")

    payload = {
        "schema": 1,
        "name": "RichPackage",
        "sources": [
            "docs/z.apexdoc",
            "docs/a.apexdoc",
        ],
        "entry": None,
        "package": {
            "id": "rich-package",
            "tier": "standard",
            "version": "1",
            "documents": [
                "docs/z.apexdoc",
                "docs/a.apexdoc",
            ],
        },
    }

    (root / "docs").mkdir(parents=True)
    (root / "apexforge.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    (root / "docs" / "z.apexdoc").write_bytes(exact_z)
    (root / "docs" / "a.apexdoc").write_bytes(exact_a)

    return non_apex_kind, exact_z, exact_a


def _assert_owner_contracts() -> None:
    require(dataclasses.is_dataclass(RichDocumentProjectBuild),
            "RichDocumentProjectBuild must be a dataclass")
    require(RichDocumentProjectBuild.__dataclass_params__.frozen,
            "RichDocumentProjectBuild must remain frozen")
    require(
        tuple(RichDocumentProjectBuild.__dataclass_fields__)
        == ("package", "documents", "compilations"),
        "RichDocumentProjectBuild field contract changed",
    )

    require(
        project_build_owner.parse_apex_document.__module__
        == "rich_documents.parser",
        "F2 must reuse rich_documents.parser.parse_apex_document",
    )
    require(
        project_build_owner.compile_apex_document_blocks.__module__
        == "rich_documents.compilation",
        "F2 must reuse rich_documents.compilation.compile_apex_document_blocks",
    )

    require(
        tuple(CanonicalBuildArtifact.__dataclass_fields__)
        == (
            "content",
            "entry",
            "fingerprint",
            "source_count",
            "narrative_artifact",
        ),
        "F2 changed CanonicalBuildArtifact fields",
    )
    require(
        tuple(LoadedProject.__dataclass_fields__)
        == ("root", "manifest_path", "manifest", "sources", "project_kind"),
        "F2 changed LoadedProject fields",
    )
    require(
        tuple(LoadedProjectSource.__dataclass_fields__)
        == ("name", "path", "source", "source_bytes"),
        "F2 changed LoadedProjectSource fields",
    )


def _assert_native_project_build() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        non_apex_kind, exact_z, exact_a = _write_package_project(root)
        loaded = load_project(root)

        require(loaded.project_kind == "air",
                "F2 must not add or change project kinds")
        require(
            tuple(source.name for source in loaded.sources)
            == ("docs/a.apexdoc", "docs/z.apexdoc"),
            "canonical manifest source sorting changed",
        )
        require(
            loaded.manifest.package is not None,
            "F1 package declaration disappeared",
        )
        require(
            loaded.manifest.package.documents
            == ("docs/z.apexdoc", "docs/a.apexdoc"),
            "package declaration order changed",
        )

        parse_calls = []
        compile_calls = []
        real_parse = project_build_owner.parse_apex_document
        real_compile = project_build_owner.compile_apex_document_blocks

        def observed_parse(source_name: str, text: str):
            parse_calls.append((source_name, text))
            return real_parse(source_name, text)

        def observed_compile(document):
            compile_calls.append(document.source_name)
            return real_compile(document)

        project_build_owner.parse_apex_document = observed_parse
        project_build_owner.compile_apex_document_blocks = observed_compile
        try:
            build = build_rich_document_project(loaded)
        finally:
            project_build_owner.parse_apex_document = real_parse
            project_build_owner.compile_apex_document_blocks = real_compile

        require(type(build) is RichDocumentProjectBuild,
                "native F2 project build type changed")
        require(build.package is loaded.manifest.package,
                "native F2 build lost exact package descriptor")
        require(
            tuple(document.source_name for document in build.documents)
            == ("docs/z.apexdoc", "docs/a.apexdoc"),
            "F2 did not preserve package document declaration order",
        )
        require(
            tuple(document.document_id for document in build.documents)
            == ("Zed", "Alpha"),
            "F2 document identities changed",
        )
        require(
            build.compilations == (),
            "text-only rich-document package unexpectedly produced Apex compilations",
        )

        require(
            parse_calls
            == [
                ("docs/z.apexdoc", exact_z.decode("utf-8")),
                ("docs/a.apexdoc", exact_a.decode("utf-8")),
            ],
            "F2 did not parse package documents from exact source bytes "
            "in package declaration order",
        )
        require(
            compile_calls == ["docs/z.apexdoc", "docs/a.apexdoc"],
            "F2 did not delegate each parsed document to the canonical "
            "rich-document compilation owner",
        )

        require(
            build.documents[0].blocks[0].content == "Zed line\r\n",
            "CRLF block content was normalized before rich-document parsing",
        )
        require(
            build.documents[1].blocks[0].content == "Alpha line\n",
            "LF block content changed during rich-document parsing",
        )

        nested = rich_document_project_build_payload(build)
        expected_nested = {
            "schema": RICH_DOCUMENT_PROJECT_BUILD_SCHEMA,
            "package": {
                "id": "rich-package",
                "tier": "standard",
                "version": "1",
            },
            "documents": [
                {
                    "id": "Zed",
                    "path": "docs/z.apexdoc",
                    "blocks": [
                        {
                            "id": "intro",
                            "kind": non_apex_kind.value,
                            "content": "Zed line\r\n",
                        }
                    ],
                },
                {
                    "id": "Alpha",
                    "path": "docs/a.apexdoc",
                    "blocks": [
                        {
                            "id": "intro",
                            "kind": non_apex_kind.value,
                            "content": "Alpha line\n",
                        }
                    ],
                },
            ],
            "executable_blocks": [],
        }
        require(nested == expected_nested,
                "native rich-document project payload changed")

        artifact = construct_rich_document_build_artifact(loaded, build)
        repeated = construct_rich_document_build_artifact(loaded, build)

        require(type(artifact) is CanonicalBuildArtifact,
                "F2 did not reuse CanonicalBuildArtifact envelope")
        require(artifact == repeated,
                "F2 artifact construction is not deterministic")
        require(artifact.entry is None,
                "document-only package unexpectedly gained an entry")
        require(artifact.source_count == 2,
                "F2 artifact source count changed")
        require(artifact.narrative_artifact is None,
                "F2 rich-document artifact polluted narrative metadata")

        value = json.loads(artifact.content.decode("utf-8"))
        require(value["schema"] == BUILD_ARTIFACT_SCHEMA_V3,
                "F2 top-level artifact schema changed")
        require(
            frozenset(value)
            == frozenset(
                ("fingerprint", "package", "project", "rich_documents", "schema")
            ),
            "F2 native rich-document top-level artifact shape changed",
        )
        require("air" not in value,
                "F2 synthesized a top-level AIR payload")
        require("narrative" not in value,
                "F2 rich-document artifact unexpectedly gained narrative material")

        require(
            value["project"]
            == {
                "entry": None,
                "name": "RichPackage",
                "source_count": 2,
                "sources": [
                    {
                        "path": "docs/a.apexdoc",
                        "sha256": hashlib.sha256(exact_a).hexdigest(),
                    },
                    {
                        "path": "docs/z.apexdoc",
                        "sha256": hashlib.sha256(exact_z).hexdigest(),
                    },
                ],
            },
            "F2 project metadata or exact-byte source fingerprints changed",
        )
        require(
            value["package"]
            == {
                "id": "rich-package",
                "tier": "standard",
                "version": "1",
                "documents": [
                    "docs/z.apexdoc",
                    "docs/a.apexdoc",
                ],
            },
            "F2 package artifact metadata changed",
        )
        require(value["rich_documents"] == expected_nested,
                "F2 nested rich-document build payload changed")

        fingerprint_payload = dict(value)
        fingerprint = fingerprint_payload.pop("fingerprint")
        expected_fingerprint = hashlib.sha256(
            canonical_json_bytes(fingerprint_payload)
        ).hexdigest()
        require(
            fingerprint
            == {
                "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
                "value": expected_fingerprint,
            },
            "F2 canonical artifact fingerprint changed",
        )
        require(artifact.fingerprint == expected_fingerprint,
                "F2 in-memory artifact fingerprint changed")

        output = root / "rich-build.json"
        write_build_artifact_atomic(artifact, output)
        require(output.read_bytes() == artifact.content,
                "F2 atomic artifact write changed bytes")



def _source_map_payload(source_map):
    return [
        {
            "air_id": entry.air_id,
            "kind": entry.kind,
            "reference": entry.reference,
            "span": {
                "source_name": entry.span.source_name,
                "start": {
                    "line": entry.span.start.line,
                    "column": entry.span.start.column,
                    "offset": entry.span.start.offset,
                },
                "end": {
                    "line": entry.span.end.line,
                    "column": entry.span.end.column,
                    "offset": entry.span.end.offset,
                },
            },
        }
        for entry in source_map.entries
    ]


def _assert_executable_block_semantic_artifact() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        payload = {
            "schema": 1,
            "name": "ExecutableRichPackage",
            "sources": ["exec.apexdoc"],
            "entry": None,
            "package": {
                "id": "exec-package",
                "tier": "domain",
                "version": "1",
                "documents": ["exec.apexdoc"],
            },
        }
        (root / "apexforge.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
        exact = (
            b"@apexdoc Exec\n"
            b"@block apex run\n"
            b"directive Main {}\n"
            b"@endblock\n"
        )
        (root / "exec.apexdoc").write_bytes(exact)

        loaded = load_project(root)
        build = build_rich_document_project(loaded)

        require(
            len(build.compilations) == 1,
            "executable Apex block did not compile exactly once",
        )
        compilation = build.compilations[0]
        require(
            compilation.source.document_id == "Exec"
            and compilation.source.block_id == "run"
            and compilation.source.source_name
            == "exec.apexdoc::apexdoc::Exec::run"
            and compilation.source.text == "directive Main {}\n",
            "executable block lineage or exact source text changed",
        )

        expected_air = air_to_dict(compilation.compiled.program)
        require(
            expected_air["version"] == "0.2"
            and tuple(
                directive["id"]
                for directive in expected_air["directives"]
            )
            == ("directive:Main",),
            "canonical executable-block AIR did not contain directive:Main",
        )

        expected_source_map = _source_map_payload(
            compilation.compiled.source_map
        )
        require(
            expected_source_map
            and all(
                item["span"]["source_name"]
                == "exec.apexdoc::apexdoc::Exec::run"
                for item in expected_source_map
            ),
            "canonical executable-block source-map lineage changed",
        )

        nested = rich_document_project_build_payload(build)
        require(
            len(nested["executable_blocks"]) == 1,
            "native payload did not serialize exactly one executable block",
        )
        executable = nested["executable_blocks"][0]
        require(
            frozenset(executable)
            == frozenset(
                (
                    "air",
                    "block_id",
                    "document_id",
                    "source_map",
                    "source_name",
                    "text",
                )
            ),
            "executable-block payload field set changed",
        )
        require(
            executable["document_id"] == "Exec"
            and executable["block_id"] == "run"
            and executable["source_name"]
            == "exec.apexdoc::apexdoc::Exec::run"
            and executable["text"] == "directive Main {}\n",
            "serialized executable block lost exact source lineage",
        )
        require(
            executable["air"] == expected_air,
            "serialized executable block lost canonical compiled AIR",
        )
        require(
            executable["source_map"] == expected_source_map,
            "serialized executable block lost canonical source-map provenance",
        )

        artifact = construct_rich_document_build_artifact(loaded, build)
        repeated = construct_rich_document_build_artifact(loaded, build)
        require(
            artifact == repeated,
            "executable rich-document artifact is not deterministic",
        )
        value = json.loads(artifact.content.decode("utf-8"))
        require(
            value["schema"] == BUILD_ARTIFACT_SCHEMA_V3
            and "air" not in value
            and "narrative" not in value,
            "executable semantics leaked into a synthetic top-level payload",
        )
        require(
            value["rich_documents"]["executable_blocks"][0]["air"]
            == expected_air,
            "canonical artifact dropped executable-block AIR",
        )
        require(
            value["rich_documents"]["executable_blocks"][0]["source_map"]
            == expected_source_map,
            "canonical artifact dropped executable-block source-map provenance",
        )

def _assert_package_required() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "apexforge.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "name": "Legacy",
                    "sources": ["guide.apexdoc"],
                    "entry": None,
                }
            ),
            encoding="utf-8",
            )
        (root / "guide.apexdoc").write_bytes(
            b"@apexdoc Guide\n"
        )
        loaded = load_project(root)
        require(loaded.manifest.package is None,
                "legacy fixture unexpectedly gained a package")
        error = raises(ValueError, build_rich_document_project, loaded)
        require("package" in str(error).lower(),
                "missing-package diagnostic lost package context")


def main() -> None:
    _assert_owner_contracts()
    _assert_native_project_build()
    _assert_executable_block_semantic_artifact()
    _assert_package_required()

    print("P11_13F1_FREEZE_BASELINE={}".format(EXPECTED_F1_COMMIT))
    print("RICH_DOCUMENT_PROJECT_BUILD_OWNER=rich_documents.project_build")
    print("RICH_DOCUMENT_PROJECT_BUILD_FIELDS=package,documents,compilations")
    print("PACKAGE_DOCUMENT_ORDER=DECLARATION_ORDER_PRESERVED")
    print("PACKAGE_DOCUMENT_PARSE_INPUT=EXACT_SOURCE_BYTES_UTF8")
    print("RICH_DOCUMENT_PARSER_REUSE=PASS")
    print("RICH_DOCUMENT_COMPILATION_REUSE=PASS")
    print("EXECUTABLE_BLOCK_CANONICAL_AIR_SERIALIZATION=PASS")
    print("EXECUTABLE_BLOCK_SOURCE_MAP_PROVENANCE=PASS")
    print("CANONICAL_BUILD_ARTIFACT_FIELDS=UNCHANGED")
    print("LOADED_PROJECT_FIELDS=UNCHANGED")
    print("PROJECT_KIND_SET=UNCHANGED")
    print("PROJECT_BUILDER_MUTATION=NONE")
    print("PROJECT_LOADER_IO_MUTATION=NONE")
    print("NATIVE_RICH_DOCUMENT_TOP_LEVEL_AIR=NONE")
    print("NATIVE_RICH_DOCUMENT_NARRATIVE_MATERIAL=NONE")
    print("CANONICAL_ARTIFACT_SCHEMA=apexforge.build-artifact/v3")
    print("CANONICAL_ARTIFACT_OWNER=tooling.build_artifact")
    print("CLI_ROUTING=DEFERRED_TO_F3")
    print("RUNTIME_EXECUTION=NONE")
    print("CACHE_INTEGRATION=NONE")
    print("TAM_TAP_INTEGRATION=NONE")
    print("REMOTE_REGISTRY_SOLVER_LOCKFILE_SIGNING=NONE")
    print("P11_13F2_NATIVE_RICH_DOCUMENT_PROJECT_BUILD_ARTIFACT=PASS")
    print("P11_13F2_EXIT=0")


if __name__ == "__main__":
    main()