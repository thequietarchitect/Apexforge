from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from rich_documents.model import PackageDescriptor, PackageTier
from tooling.project_loader import LoadedProject, load_project
from tooling.project_manifest import PROJECT_MANIFEST_SCHEMA, ProjectManifest, ProjectManifestError

PREDECESSOR_TAG = "afp-p11-13e-freeze"
PREDECESSOR_COMMIT = "88757be22340e3870e0eda9df98c784caf1935e4"
EXPECTED_ARTIFACTS = (
    "apexforge/tooling/project_manifest.py",
    "apexforge/p11_13f1_manifest_package_declaration_integration_smoke_test.py",
    "docs/p11/P11_13F1_MANIFEST_PACKAGE_DECLARATION_INTEGRATION.md",
)

def root() -> Path:
    return Path(__file__).resolve().parents[1]

def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(("git", *args), cwd=root(), check=False, text=True,
                          encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def raises(error_type, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except error_type as error:
        return error
    except Exception as error:
        raise AssertionError("expected {}, got {}: {}".format(
            error_type.__name__, type(error).__name__, error))
    raise AssertionError("expected {}".format(error_type.__name__))

def package_payload():
    return {
        "schema": 1,
        "name": "Documents",
        "sources": ["src/main.apex", "docs/z.apexdoc", "docs/a.apexdoc"],
        "entry": "Main",
        "package": {
            "id": "documents",
            "tier": "domain",
            "version": "2026.1",
            "documents": ["docs/z.apexdoc", "docs/a.apexdoc"],
        },
    }

def main() -> None:
    require(git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG)).stdout.strip()
            == PREDECESSOR_COMMIT, "P11.13E freeze changed")
    require(PROJECT_MANIFEST_SCHEMA == 1, "manifest schema changed")
    require(dataclasses.is_dataclass(ProjectManifest), "ProjectManifest lost dataclass")
    require(ProjectManifest.__dataclass_params__.frozen, "ProjectManifest lost frozen")
    require(tuple(ProjectManifest.__dataclass_fields__)
            == ("name", "sources", "entry", "schema", "package"),
            "F1 manifest fields changed")

    legacy = ProjectManifest("Legacy", ("src/z.apex", "src/a.apex"), "Main", 1)
    require(legacy.package is None, "legacy manifest gained package")
    expected_legacy = {
        "schema": 1,
        "name": "Legacy",
        "sources": ["src/a.apex", "src/z.apex"],
        "entry": "Main",
    }
    require(legacy.to_mapping() == expected_legacy, "legacy mapping changed")
    require(legacy.canonical_json() == json.dumps(
        expected_legacy, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "legacy canonical JSON changed")

    manifest = ProjectManifest.from_mapping(package_payload())
    require(type(manifest.package) is PackageDescriptor, "package type changed")
    require(manifest.package.tier is PackageTier.DOMAIN, "package tier changed")
    require(manifest.package.documents == ("docs/z.apexdoc", "docs/a.apexdoc"),
            "package document order changed")
    require(manifest.sources == ("docs/a.apexdoc", "docs/z.apexdoc", "src/main.apex"),
            "source sorting changed")
    require(ProjectManifest.from_mapping(json.loads(manifest.canonical_json())) == manifest,
            "package canonical JSON round trip failed")

    direct = ProjectManifest(
        "Direct",
        ("docs/a.apexdoc", "docs/b.apexdoc"),
        None,
        1,
        PackageDescriptor(
            "direct",
            PackageTier.EXPERIMENTAL,
            "v1",
            ("docs\\b.apexdoc", "docs/a.apexdoc"),
        ),
    )
    require(direct.package.documents == ("docs/b.apexdoc", "docs/a.apexdoc"),
            "package path normalization changed")

    cases = []
    value = package_payload(); value["package"]["unexpected"] = True; cases.append(value)
    value = package_payload(); del value["package"]["version"]; cases.append(value)
    value = package_payload(); value["package"] = []; cases.append(value)
    value = package_payload(); value["package"]["tier"] = "privileged"; cases.append(value)
    value = package_payload(); value["package"]["documents"] = "docs/a.apexdoc"; cases.append(value)
    value = package_payload(); value["package"]["documents"] = ["docs/missing.apexdoc"]; cases.append(value)
    value = package_payload(); value["package"]["documents"] = ["docs/a.apexdoc", "docs/a.apexdoc"]; cases.append(value)
    value = package_payload(); value["sources"].append("docs/a.APEXDOC"); value["package"]["documents"] = ["docs/a.APEXDOC"]; cases.append(value)
    for value in cases:
        error = raises(ProjectManifestError, ProjectManifest.from_mapping, value)
        require(error.code == "APX-TOOL-009", "package error code changed")

    metadata = PackageDescriptor(
        "metadata", PackageTier.DOMAIN, "1", ("docs/a.apexdoc",),
        (("owner", "example"),),
    )
    require(raises(ProjectManifestError, ProjectManifest, "Metadata",
                   ("docs/a.apexdoc",), None, 1, metadata).code == "APX-TOOL-009",
            "manifest package metadata boundary changed")

    require(tuple(LoadedProject.__dataclass_fields__)
            == ("root", "manifest_path", "manifest", "sources", "project_kind"),
            "LoadedProject fields changed")
    with TemporaryDirectory() as temporary:
        project = Path(temporary)
        payload = {
            "schema": 1,
            "name": "DocPackage",
            "sources": ["guide.apexdoc"],
            "entry": None,
            "package": {
                "id": "doc-package",
                "tier": "standard",
                "version": "1",
                "documents": ["guide.apexdoc"],
            },
        }
        (project / "apexforge.json").write_text(json.dumps(payload), encoding="utf-8")
        exact = b"@apexdoc Guide\r\n@block text intro\r\nHello\r\n@endblock\r\n"
        (project / "guide.apexdoc").write_bytes(exact)
        loaded = load_project(project)
        require(loaded.project_kind == "air", "F1 changed project kind")
        require(loaded.sources[0].source_bytes == exact, "exact bytes changed")
        require(loaded.sources[0].source
                == "@apexdoc Guide\n@block text intro\nHello\n@endblock\n",
                "universal newline source changed")

    protected = (
        "apexforge/tooling/project_loader.py",
        "apexforge/tooling/build_artifact.py",
        "apexforge/tooling/cli.py",
        "apexforge/tooling/project_scaffold.py",
        "apexforge/language",
        "apexforge/air",
        "apexforge/runtime",
        "apexforge/incremental_cache",
        "apexforge/tam",
        "apexforge/tap_check",
        "apexforge/rich_documents",
    )
    require(git("diff", "--exit-code", PREDECESSOR_TAG, "--", *protected).returncode == 0,
            "F1 mutated deferred/frozen owner")

    status = git("status", "--porcelain=v1", "--untracked-files=all")
    actual = tuple(line[3:].replace("\\", "/") for line in status.stdout.splitlines()
                   if line.strip())
    require(set(actual) == set(EXPECTED_ARTIFACTS),
            "F1 artifact set changed: {}".format(actual))

    print("P11_13E_FREEZE_ANCESTRY=PASS")
    print("PROJECT_MANIFEST_SCHEMA=1_UNCHANGED")
    print("PROJECT_MANIFEST_OWNER=tooling.project_manifest")
    print("PROJECT_MANIFEST_FIELDS=name,sources,entry,schema,package")
    print("PROJECT_MANIFEST_PACKAGE=OPTIONAL")
    print("LEGACY_MANIFEST_MAPPING=UNCHANGED_WITHOUT_PACKAGE")
    print("LEGACY_CANONICAL_JSON=UNCHANGED_WITHOUT_PACKAGE")
    print("POSITIONAL_SCHEMA_COMPATIBILITY=PASS")
    print("PACKAGE_DESCRIPTOR_OWNER=rich_documents.model.PackageDescriptor")
    print("PACKAGE_TIER_OWNER=rich_documents.model.PackageTier")
    print("PACKAGE_JSON_KEYS=id,tier,version,documents")
    print("PACKAGE_UNKNOWN_KEYS=REJECTED")
    print("PACKAGE_DOCUMENT_PATH_NORMALIZER=CANONICAL_PROJECT_SOURCE_NORMALIZER")
    print("PACKAGE_DOCUMENT_MEMBERSHIP=MANIFEST_SOURCES_REQUIRED")
    print("PACKAGE_DOCUMENT_EXTENSION=LOWERCASE_APEXDOC")
    print("PACKAGE_DOCUMENT_ORDER=DECLARATION_ORDER_PRESERVED")
    print("PACKAGE_METADATA_IN_MANIFEST=EMPTY_ONLY")
    print("MANIFEST_SOURCE_SORTING=UNCHANGED")
    print("LOADED_PROJECT_FIELDS=UNCHANGED")
    print("PROJECT_KIND_SET=UNCHANGED")
    print("LOAD_PROJECT_IO=UNCHANGED")
    print("SOURCE_BYTES_EXACT=PASS")
    print("SOURCE_TEXT_UNIVERSAL_NEWLINE=UNCHANGED")
    print("BUILD_INTEGRATION=NONE")
    print("ARTIFACT_INTEGRATION=NONE")
    print("CLI_INTEGRATION=NONE")
    print("CACHE_INTEGRATION=NONE")
    print("TAM_INTEGRATION=NONE")
    print("TAP_OWNERSHIP=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("REMOTE_REGISTRY_SOLVER_LOCKFILE_SIGNING=NONE")
    print("P11_13F1_MANIFEST_PACKAGE_DECLARATION_INTEGRATION=PASS")

if __name__ == "__main__":
    main()