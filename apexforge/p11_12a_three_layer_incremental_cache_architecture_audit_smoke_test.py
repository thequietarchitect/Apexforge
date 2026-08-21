"""P11.12A three-layer incremental-cache architecture and ownership audit."""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
from pathlib import Path
import subprocess

from air.model import VerifiedAIRProgram
from language.compiler import CompiledSource, SourceMap
from language.lexer import Token
from language.modules import ModuleGraph, ProjectDocumentGraph
from language.narrative_graph import NarrativeSemanticGraph
from language.parser import SourceUnitNode
from language.project import ProjectBuild
from quad_vector import ResultantVector
from semantic_lattice.construction import SemanticLatticeSnapshot
from semantic_lattice.model import ParametricSemanticLattice
from tam import TraceMap
from tooling.build_artifact import CanonicalBuildArtifact
from tooling.project_loader import LoadedProject, LoadedProjectSource
from workflow.air_runner import RegistryExecutionPlan


PREDECESSOR_TAG = "afp-p11-11g-freeze"
PREDECESSOR_COMMIT = "c05ef70aa9243dbeadee9a9542509348ccf12e39"

EXPECTED_LAYER_IDS = ("capture", "resonance", "stability")

EXPECTED_OWNER_FIELDS = {
    LoadedProjectSource: ("name", "path", "source", "source_bytes"),
    LoadedProject: ("root", "manifest_path", "manifest", "sources", "project_kind"),
    Token: ("kind", "value", "span"),
    SourceUnitNode: ("declarations", "span"),
    CompiledSource: ("program", "source_map"),
    SourceMap: ("entries",),
    ModuleGraph: ("modules", "order"),
    ProjectDocumentGraph: (
        "documents",
        "resolved_import_edges",
        "canonical_order",
        "dependency_order",
    ),
    ProjectBuild: (
        "source_units",
        "program",
        "verified",
        "source_map",
        "module_graph",
        "entry_directive",
        "document_graph",
        "declaration_ownership",
        "identity_index",
        "resolution_candidate_index",
    ),
    TraceMap: ("records",),
    NarrativeSemanticGraph: ("story", "nodes", "edges"),
    ResultantVector: ("x", "y", "contributions", "provenance"),
    ParametricSemanticLattice: ("axes", "parameters"),
    SemanticLatticeSnapshot: ("lattice", "subjects", "relationships"),
    VerifiedAIRProgram: ("program",),
    RegistryExecutionPlan: ("program", "entry_directive", "directive_owners"),
    CanonicalBuildArtifact: (
        "content",
        "entry",
        "fingerprint",
        "source_count",
        "narrative_artifact",
    ),
}


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _field_names(value: object) -> tuple[str, ...]:
    return tuple(field.name for field in dataclasses.fields(value))


def _assert_predecessor_and_clean_boundary() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.11G freeze target changed",
    )
    _require(
        _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.11G freeze is not an ancestor of P11.12A",
    )


def _assert_roadmap_contract() -> None:
    continuity = _root() / "docs" / "p11" / "P11_CONTINUITY_PULSE.md"
    text = continuity.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    _require(
        "P11.12 Three-layer incremental cache" in normalized,
        "canonical P11.12 roadmap stage disappeared",
    )


def _assert_immutable_owner_surfaces() -> None:
    for owner, expected_fields in EXPECTED_OWNER_FIELDS.items():
        _require(
            dataclasses.is_dataclass(owner),
            "{} stopped being a dataclass".format(owner.__name__),
        )
        _require(
            owner.__dataclass_params__.frozen,
            "{} stopped being frozen".format(owner.__name__),
        )
        _require(
            _field_names(owner) == expected_fields,
            "{} fields changed".format(owner.__name__),
        )


def _assert_exact_capture_hash_anchor() -> None:
    from tooling import build_artifact
    from tooling import project_loader

    loader_source = inspect.getsource(project_loader.load_project)
    artifact_source = inspect.getsource(build_artifact.construct_build_artifact)

    _require(
        "read_bytes()" in loader_source,
        "project loader stopped retaining exact source bytes",
    )
    _require(
        "source_bytes=source_bytes" in loader_source,
        "LoadedProjectSource stopped receiving exact bytes",
    )
    _require(
        "hashlib.sha256(source.source_bytes).hexdigest()" in artifact_source,
        "canonical build artifact stopped hashing exact loaded source bytes",
    )


def _assert_dependency_spine() -> None:
    fields = set(_field_names(ProjectDocumentGraph))
    _require(
        {"resolved_import_edges", "dependency_order"} <= fields,
        "project document graph lost dependency invalidation evidence",
    )


def _assert_stability_gaps_are_not_fabricated() -> None:
    production_paths = []
    for path in (_root() / "apexforge").rglob("*.py"):
        relative = path.relative_to(_root()).as_posix()
        if relative.endswith("_smoke_test.py"):
            continue
        if "/tests/" in relative:
            continue
        production_paths.append(path)

    for phrase in (
        "continuity checkpoint",
        "optimized artifact",
        "optimization decision",
    ):
        found = tuple(
            path.relative_to(_root()).as_posix()
            for path in production_paths
            if phrase in path.read_text(encoding="utf-8").lower()
        )
        _require(
            found == (),
            "P11.12A gap assumption changed for {!r}: {}".format(phrase, found),
        )


def _assert_no_cache_production_at_a_boundary() -> None:
    candidates = (
        _root() / "apexforge" / "incremental_cache",
        _root() / "apexforge" / "incremental_cache.py",
    )
    _require(
        not any(path.exists() for path in candidates),
        "dedicated P11.12 cache production already exists at A boundary",
    )


def _assert_a_is_audit_only() -> None:
    production_paths = (
        "apexforge/air",
        "apexforge/language",
        "apexforge/quad_vector",
        "apexforge/semantic_lattice",
        "apexforge/aether_air",
        "apexforge/tam",
        "apexforge/tap_check",
        "apexforge/runtime",
        "apexforge/workflow",
        "apexforge/tooling",
        "apexforge/type_system",
        "apexforge/governance",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *production_paths)
    _require(diff.returncode == 0, "P11.12A mutated predecessor production owners")


def _assert_hash_shape() -> None:
    sample = hashlib.sha256(b"apexforge-p11.12").hexdigest()
    _require(len(sample) == 64, "SHA-256 hex length changed")
    _require(sample == sample.lower(), "SHA-256 anchor is not lowercase hex")


def main() -> None:
    _assert_predecessor_and_clean_boundary()
    _assert_roadmap_contract()
    _assert_immutable_owner_surfaces()
    _assert_exact_capture_hash_anchor()
    _assert_dependency_spine()
    _assert_stability_gaps_are_not_fabricated()
    _assert_no_cache_production_at_a_boundary()
    _assert_a_is_audit_only()
    _assert_hash_shape()

    print("P11_12A_PREDECESSOR=P11.11G")
    print("P11_12A_PREDECESSOR_FREEZE={}".format(PREDECESSOR_TAG))
    print("P11_12_LAYER_COUNT=3")
    print("P11_12_LAYER_IDS={}".format(",".join(EXPECTED_LAYER_IDS)))
    print("CAPTURE_SOURCE_OWNER=tooling.project_loader.LoadedProjectSource")
    print("CAPTURE_SOURCE_HASH=SHA256_EXACT_SOURCE_BYTES")
    print("CAPTURE_TOKEN_OWNER=language.lexer.Token")
    print("CAPTURE_FORMATTING_OWNER=language_server.formatting")
    print("RESONANCE_AST_OWNER=language.parser.SourceUnitNode")
    print("RESONANCE_MODULE_GRAPH_OWNER=language.modules.ModuleGraph")
    print("RESONANCE_DOCUMENT_GRAPH_OWNER=language.modules.ProjectDocumentGraph")
    print("RESONANCE_COMPILED_SOURCE_OWNER=language.compiler.CompiledSource")
    print("RESONANCE_SYMBOL_PRODUCTS=ProjectBuild.declaration_ownership,ProjectBuild.identity_index,ProjectBuild.resolution_candidate_index")
    print("RESONANCE_TAM_OWNER=tam.TraceMap")
    print("RESONANCE_NARRATIVE_GRAPH_OWNER=language.narrative_graph.NarrativeSemanticGraph")
    print("RESONANCE_QUAD_VECTOR_PUBLIC_RESULT=quad_vector.ResultantVector")
    print("RESONANCE_LATTICE_OWNER=semantic_lattice.construction.SemanticLatticeSnapshot")
    print("STABILITY_VERIFIED_AIR_OWNER=air.model.VerifiedAIRProgram")
    print("STABILITY_EXECUTION_PLAN_OWNER=workflow.air_runner.RegistryExecutionPlan")
    print("STABILITY_CONTINUITY_CHECKPOINT_OWNER=ABSENT_DEFERRED")
    print("STABILITY_OPTIMIZED_ARTIFACT_OWNER=ABSENT_DEFERRED")
    print("WHOLE_BUILD_EQUIVALENCE_ORACLE=tooling.build_artifact.CanonicalBuildArtifact.fingerprint")
    print("DEPENDENCY_INVALIDATION_SPINE=ProjectDocumentGraph.resolved_import_edges+dependency_order")
    print("CACHE_CORRECTNESS_USES_CONTENT_IDENTITY=YES")
    print("TIMESTAMP_OR_MTIME_CORRECTNESS=FORBIDDEN")
    print("CACHE_SEMANTIC_OWNERSHIP=NONE")
    print("CACHE_RUNTIME_EXECUTION_OWNERSHIP=NONE")
    print("P11_12A_DEDICATED_CACHE_PRODUCTION=ABSENT_STAGE_BOUNDARY")
    print("P11_12A_PRODUCTION_MUTATION=NONE")
    print("P11_12A_THREE_LAYER_INCREMENTAL_CACHE_ARCHITECTURE_AUDIT=PASS")


if __name__ == "__main__":
    main()