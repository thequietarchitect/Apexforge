"""P11.12D Resonance-layer immutable owner-product reuse smoke test."""

from __future__ import annotations

from pathlib import Path
import subprocess

import incremental_cache
import incremental_cache.resonance as resonance_module
from incremental_cache import CacheEntry, cache_fingerprint
from incremental_cache.capture import capture_document, capture_tokens
from incremental_cache.resonance import (
    resonance_dependencies_fingerprint,
    resonance_dependency,
    resonance_fingerprint,
    resonance_identity,
    resonance_input_fingerprint,
    reuse_or_produce_resonance,
)
from language.compiler import CompiledSource, SourceMap, compile_source_with_map
from language.declarations import ProjectDeclarationOwnership
from language.identities import ProjectIdentityIndex
from language.modules import ModuleGraph, ProjectDocumentGraph
from language.narrative_graph import (
    NarrativeSemanticGraph,
    build_narrative_semantic_graph,
)
from language.narrative_model import NarrativeIdentity, NarrativeStory
from language.parser import SourceUnitNode, parse_source_unit
from language.project import ProjectBuild, build_project
from language.resolution_candidates import ProjectResolutionCandidateIndex
from quad_vector import ResultantVector
from semantic_lattice.construction import (
    SemanticLatticeSnapshot,
    construct_semantic_lattice_snapshot,
)
from semantic_lattice.model import (
    CORE_SEMANTIC_LATTICE_AXES,
    ParametricSemanticLattice,
)
from tam import TraceMap, trace_map_from_source_map
from tooling.project_loader import load_project


PREDECESSOR_TAG = "afp-p11-12c-freeze"
PREDECESSOR_COMMIT = "1fdf4480cec39f128cbb5961e68025f5fabf2627"

C_HASHES = {
    "apexforge/incremental_cache/capture.py":
        "FB3E6E84400B2FCB7F74BE5060F08609F1A481BBF25FD7881A85566541967C76",
    "apexforge/p11_12c_capture_layer_document_token_formatting_reuse_smoke_test.py":
        "D19C142E32E33052A35734170C5F1634EEE1F21B74857298CCAB4A3622FDB9DA",
    "docs/p11/P11_12C_CAPTURE_LAYER_DOCUMENT_TOKEN_FORMATTING_REUSE.md":
        "0BDB95022E68F3A38231F186436C58AD13C2C23891609F7187DCF88BC396BC74",
}

EXPECTED_PUBLIC = (
    "resonance_input_fingerprint",
    "resonance_fingerprint",
    "resonance_dependency",
    "resonance_dependencies_fingerprint",
    "resonance_identity",
    "reuse_or_produce_resonance",
)

ALLOWED_TYPES = (
    SourceUnitNode,
    ModuleGraph,
    ProjectDocumentGraph,
    CompiledSource,
    SourceMap,
    ProjectDeclarationOwnership,
    ProjectIdentityIndex,
    ProjectResolutionCandidateIndex,
    TraceMap,
    NarrativeSemanticGraph,
    ResultantVector,
    ParametricSemanticLattice,
    SemanticLatticeSnapshot,
)


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


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.12C freeze target changed",
    )
    _require(
        _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.12C freeze is not ancestor of P11.12D",
    )
    for relative, expected in C_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} P11.12C hash changed".format(relative),
        )


def _assert_surface_and_exclusions() -> None:
    _require(
        resonance_module.__all__ == EXPECTED_PUBLIC,
        "Resonance public surface changed",
    )
    _require(
        incremental_cache.__all__
        == (
            "CACHE_SCHEMA_VERSION",
            "CACHE_LAYER_IDS",
            "CACHE_FINGERPRINT_ALGORITHM",
            "CacheFingerprint",
            "CacheDependency",
            "CacheIdentity",
            "CacheEntry",
            "cache_fingerprint",
            "cache_identity_key",
        ),
        "P11.12D changed P11.12B top-level cache surface",
    )

    from air.model import VerifiedAIRProgram
    from workflow.air_runner import RegistryExecutionPlan

    for excluded in (
        ProjectBuild,
        VerifiedAIRProgram,
        RegistryExecutionPlan,
    ):
        try:
            resonance_identity(
                excluded,
                subject="excluded",
                input_fingerprint=cache_fingerprint(b"x"),
                configuration_fingerprint=cache_fingerprint(b""),
            )
        except TypeError:
            pass
        else:
            raise AssertionError(
                "{} crossed into Resonance".format(excluded.__name__)
            )


def _hit(
    expected_type,
    entry: CacheEntry,
    *,
    subject: str,
    input_fingerprint,
    configuration_fingerprint,
    dependencies=(),
) -> None:
    calls = []

    def forbidden():
        calls.append(True)
        raise AssertionError("owner producer invoked on exact Resonance hit")

    reused = reuse_or_produce_resonance(
        expected_type,
        subject=subject,
        input_fingerprint=input_fingerprint,
        configuration_fingerprint=configuration_fingerprint,
        dependencies=dependencies,
        producer=forbidden,
        cached=entry,
    )
    _require(reused is entry, "exact Resonance entry was not reused")
    _require(not calls, "owner producer ran on Resonance hit")


def _assert_real_owner_products() -> None:
    fixture = _root() / "apexforge" / "fixtures" / "p11_1b" / "manifest_entry"
    loaded = load_project(fixture)
    build_a = build_project(
        loaded.source_mapping(),
        entry=loaded.manifest.entry,
    )
    build_b = build_project(
        loaded.source_mapping(),
        entry=loaded.manifest.entry,
    )
    _require(build_a == build_b, "repeat ProjectBuild changed")

    document_entries = tuple(
        capture_document(source)
        for source in loaded.sources
    )
    token_entries = tuple(
        capture_tokens(source)
        for source in loaded.sources
    )
    document_dependencies = tuple(
        resonance_dependency(entry)
        for entry in document_entries
    )
    token_dependencies = tuple(
        resonance_dependency(entry)
        for entry in token_entries
    )

    source = loaded.sources[0]
    token_entry = token_entries[0]
    ast_dependencies = (resonance_dependency(token_entry),)
    ast_input = token_entry.artifact_fingerprint
    empty_config = cache_fingerprint(b"")

    ast_entry = reuse_or_produce_resonance(
        SourceUnitNode,
        subject=source.name,
        input_fingerprint=ast_input,
        configuration_fingerprint=empty_config,
        dependencies=ast_dependencies,
        producer=lambda: parse_source_unit(
            source.source,
            source_name=source.name,
        ),
    )
    _hit(
        SourceUnitNode,
        ast_entry,
        subject=source.name,
        input_fingerprint=ast_input,
        configuration_fingerprint=empty_config,
        dependencies=ast_dependencies,
    )

    compiled_config = resonance_input_fingerprint(
        {"allow_headerless_multi_directive": True}
    )
    compiled_entry = reuse_or_produce_resonance(
        CompiledSource,
        subject=source.name,
        input_fingerprint=token_entry.artifact_fingerprint,
        configuration_fingerprint=compiled_config,
        dependencies=(resonance_dependency(token_entry),),
        producer=lambda: compile_source_with_map(
            source.source,
            source_name=source.name,
            allow_headerless_multi_directive=True,
        ),
    )
    _hit(
        CompiledSource,
        compiled_entry,
        subject=source.name,
        input_fingerprint=token_entry.artifact_fingerprint,
        configuration_fingerprint=compiled_config,
        dependencies=(resonance_dependency(token_entry),),
    )

    graph_input = resonance_dependencies_fingerprint(document_dependencies)
    project_subject = "project:{}".format(loaded.manifest.name)

    module_graph_entry = reuse_or_produce_resonance(
        ModuleGraph,
        subject=project_subject,
        input_fingerprint=graph_input,
        configuration_fingerprint=empty_config,
        dependencies=document_dependencies,
        producer=lambda: build_a.module_graph,
    )
    _hit(
        ModuleGraph,
        module_graph_entry,
        subject=project_subject,
        input_fingerprint=graph_input,
        configuration_fingerprint=empty_config,
        dependencies=document_dependencies,
    )

    document_graph_dependencies = (
        *document_dependencies,
        resonance_dependency(module_graph_entry),
    )
    document_graph_input = resonance_dependencies_fingerprint(
        document_graph_dependencies
    )
    document_graph_entry = reuse_or_produce_resonance(
        ProjectDocumentGraph,
        subject=project_subject,
        input_fingerprint=document_graph_input,
        configuration_fingerprint=empty_config,
        dependencies=document_graph_dependencies,
        producer=lambda: build_a.document_graph,
    )
    _hit(
        ProjectDocumentGraph,
        document_graph_entry,
        subject=project_subject,
        input_fingerprint=document_graph_input,
        configuration_fingerprint=empty_config,
        dependencies=document_graph_dependencies,
    )

    source_map_input = resonance_dependencies_fingerprint(token_dependencies)
    source_map_entry = reuse_or_produce_resonance(
        SourceMap,
        subject=project_subject,
        input_fingerprint=source_map_input,
        configuration_fingerprint=empty_config,
        dependencies=token_dependencies,
        producer=lambda: build_a.source_map,
    )
    _hit(
        SourceMap,
        source_map_entry,
        subject=project_subject,
        input_fingerprint=source_map_input,
        configuration_fingerprint=empty_config,
        dependencies=token_dependencies,
    )

    index_dependencies = (
        resonance_dependency(module_graph_entry),
        resonance_dependency(document_graph_entry),
        resonance_dependency(source_map_entry),
    )
    index_input = resonance_dependencies_fingerprint(index_dependencies)

    ownership_entry = reuse_or_produce_resonance(
        ProjectDeclarationOwnership,
        subject=project_subject,
        input_fingerprint=index_input,
        configuration_fingerprint=empty_config,
        dependencies=index_dependencies,
        producer=lambda: build_a.declaration_ownership,
    )
    identity_entry = reuse_or_produce_resonance(
        ProjectIdentityIndex,
        subject=project_subject,
        input_fingerprint=index_input,
        configuration_fingerprint=empty_config,
        dependencies=index_dependencies,
        producer=lambda: build_a.identity_index,
    )

    candidate_dependencies = (
        resonance_dependency(ownership_entry),
        resonance_dependency(identity_entry),
    )
    candidate_input = resonance_dependencies_fingerprint(
        candidate_dependencies
    )
    candidate_entry = reuse_or_produce_resonance(
        ProjectResolutionCandidateIndex,
        subject=project_subject,
        input_fingerprint=candidate_input,
        configuration_fingerprint=empty_config,
        dependencies=candidate_dependencies,
        producer=lambda: build_a.resolution_candidate_index,
    )

    for expected_type, entry, dependencies, input_fp in (
        (
            ProjectDeclarationOwnership,
            ownership_entry,
            index_dependencies,
            index_input,
        ),
        (
            ProjectIdentityIndex,
            identity_entry,
            index_dependencies,
            index_input,
        ),
        (
            ProjectResolutionCandidateIndex,
            candidate_entry,
            candidate_dependencies,
            candidate_input,
        ),
    ):
        _hit(
            expected_type,
            entry,
            subject=project_subject,
            input_fingerprint=input_fp,
            configuration_fingerprint=empty_config,
            dependencies=dependencies,
        )

    trace_dependencies = (resonance_dependency(source_map_entry),)
    trace_input = resonance_dependencies_fingerprint(trace_dependencies)
    trace_entry = reuse_or_produce_resonance(
        TraceMap,
        subject=project_subject,
        input_fingerprint=trace_input,
        configuration_fingerprint=empty_config,
        dependencies=trace_dependencies,
        producer=lambda: trace_map_from_source_map(build_a.source_map),
    )
    _hit(
        TraceMap,
        trace_entry,
        subject=project_subject,
        input_fingerprint=trace_input,
        configuration_fingerprint=empty_config,
        dependencies=trace_dependencies,
    )

    story = NarrativeStory(
        NarrativeIdentity("story", ("CacheStory",)),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
    )
    narrative_input = resonance_input_fingerprint(story)
    narrative_entry = reuse_or_produce_resonance(
        NarrativeSemanticGraph,
        subject="story:CacheStory",
        input_fingerprint=narrative_input,
        configuration_fingerprint=empty_config,
        producer=lambda: build_narrative_semantic_graph(story),
    )
    _hit(
        NarrativeSemanticGraph,
        narrative_entry,
        subject="story:CacheStory",
        input_fingerprint=narrative_input,
        configuration_fingerprint=empty_config,
    )

    resultant = ResultantVector(
        x=10,
        y=4,
        contributions=(),
        provenance=("quad.input:cache",),
    )
    quad_input = resonance_input_fingerprint(
        ("quad.input:cache", 10, 4)
    )
    quad_entry = reuse_or_produce_resonance(
        ResultantVector,
        subject="quad.input:cache",
        input_fingerprint=quad_input,
        configuration_fingerprint=empty_config,
        producer=lambda: resultant,
    )
    _hit(
        ResultantVector,
        quad_entry,
        subject="quad.input:cache",
        input_fingerprint=quad_input,
        configuration_fingerprint=empty_config,
    )

    lattice = ParametricSemanticLattice(
        axes=CORE_SEMANTIC_LATTICE_AXES,
        parameters=(),
    )
    lattice_input = resonance_input_fingerprint(
        (CORE_SEMANTIC_LATTICE_AXES, ())
    )
    lattice_entry = reuse_or_produce_resonance(
        ParametricSemanticLattice,
        subject="semantic-lattice:core",
        input_fingerprint=lattice_input,
        configuration_fingerprint=empty_config,
        producer=lambda: lattice,
    )
    _hit(
        ParametricSemanticLattice,
        lattice_entry,
        subject="semantic-lattice:core",
        input_fingerprint=lattice_input,
        configuration_fingerprint=empty_config,
    )

    snapshot_dependencies = (resonance_dependency(lattice_entry),)
    snapshot_input = resonance_dependencies_fingerprint(
        snapshot_dependencies
    )
    snapshot_entry = reuse_or_produce_resonance(
        SemanticLatticeSnapshot,
        subject="semantic-lattice:core",
        input_fingerprint=snapshot_input,
        configuration_fingerprint=empty_config,
        dependencies=snapshot_dependencies,
        producer=lambda: construct_semantic_lattice_snapshot(lattice),
    )
    _hit(
        SemanticLatticeSnapshot,
        snapshot_entry,
        subject="semantic-lattice:core",
        input_fingerprint=snapshot_input,
        configuration_fingerprint=empty_config,
        dependencies=snapshot_dependencies,
    )

    entries = (
        ast_entry,
        module_graph_entry,
        document_graph_entry,
        compiled_entry,
        source_map_entry,
        ownership_entry,
        identity_entry,
        candidate_entry,
        trace_entry,
        narrative_entry,
        quad_entry,
        lattice_entry,
        snapshot_entry,
    )
    _require(len(entries) == len(ALLOWED_TYPES), "Resonance coverage count changed")
    _require(
        tuple(type(entry.value) for entry in entries) == ALLOWED_TYPES,
        "Resonance allowed-type coverage order changed",
    )

    for entry in entries:
        _require(
            entry.identity.layer_id == "resonance",
            "non-Resonance identity produced",
        )
        _require(
            entry.artifact_fingerprint == resonance_fingerprint(entry.value),
            "Resonance artifact integrity fingerprint changed",
        )

    corrupt = CacheEntry(
        identity=ast_entry.identity,
        artifact_fingerprint=cache_fingerprint(b"corrupt"),
        value=ast_entry.value,
    )
    calls = []

    def repair_ast():
        calls.append(True)
        return parse_source_unit(
            source.source,
            source_name=source.name,
        )

    repaired = reuse_or_produce_resonance(
        SourceUnitNode,
        subject=source.name,
        input_fingerprint=ast_input,
        configuration_fingerprint=empty_config,
        dependencies=ast_dependencies,
        producer=repair_ast,
        cached=corrupt,
    )
    _require(repaired is not corrupt, "corrupt Resonance entry was reused")
    _require(calls == [True], "corrupt Resonance entry did not re-run owner")


def _assert_no_store_or_execution() -> None:
    import ast

    source = (
        _root() / "apexforge" / "incremental_cache" / "resonance.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules = set()
    referenced_names = set()
    attribute_names = set()
    called_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split(".", 1)[0])
                referenced_names.add(alias.asname or alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.split(".", 1)[0])
            for alias in node.names:
                referenced_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Name):
            referenced_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            attribute_names.add(node.attr)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    forbidden_modules = {
        "pickle",
        "shelve",
        "sqlite3",
        "tempfile",
        "time",
        "datetime",
    }
    forbidden_symbols = {
        "ProjectBuilder",
        "build_project",
        "RuntimeEngine",
        "RegistryExecutionPlan",
        "VerifiedAIRProgram",
        "tap_check",
    }
    forbidden_calls_or_attributes = {
        "open",
        "write_bytes",
        "write_text",
        "stat",
        "getmtime",
    }

    for module_name in forbidden_modules:
        _require(
            module_name not in imported_modules,
            "Resonance layer imported forbidden module: " + module_name,
        )

    for symbol in forbidden_symbols:
        _require(
            symbol not in referenced_names
            and symbol not in attribute_names
            and symbol not in called_names,
            "Resonance layer acquired forbidden executable symbol: " + symbol,
        )

    for symbol in forbidden_calls_or_attributes:
        _require(
            symbol not in called_names,
            "Resonance layer acquired forbidden executable behavior: " + symbol,
        )


def _assert_owner_immutability() -> None:
    paths = (
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
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "P11.12D mutated semantic owners")


def main() -> None:
    _assert_predecessor()
    _assert_surface_and_exclusions()
    _assert_real_owner_products()
    _assert_no_store_or_execution()
    _assert_owner_immutability()

    print("P11_12C_FREEZE_ANCESTRY=PASS")
    print("P11_12B_TOP_LEVEL_CACHE_SURFACE=UNCHANGED")
    print("RESONANCE_PUBLIC_OPERATION_COUNT=6")
    print("RESONANCE_ALLOWED_OWNER_PRODUCT_COUNT=13")
    print("RESONANCE_AST=PASS")
    print("RESONANCE_COMPILED_SOURCE=PASS")
    print("RESONANCE_MODULE_GRAPH=PASS")
    print("RESONANCE_DOCUMENT_GRAPH=PASS")
    print("RESONANCE_SOURCE_MAP=PASS")
    print("RESONANCE_DECLARATION_OWNERSHIP=PASS")
    print("RESONANCE_IDENTITY_INDEX=PASS")
    print("RESONANCE_RESOLUTION_CANDIDATE_INDEX=PASS")
    print("RESONANCE_TAM_TRACE_MAP=PASS")
    print("RESONANCE_NARRATIVE_GRAPH=PASS")
    print("RESONANCE_QUAD_VECTOR_RESULTANT=PASS")
    print("RESONANCE_PARAMETRIC_LATTICE=PASS")
    print("RESONANCE_LATTICE_SNAPSHOT=PASS")
    print("RESONANCE_EXACT_HIT_OWNER_INVOCATION=NONE")
    print("RESONANCE_CORRUPT_ENTRY_REUSE=REJECTED")
    print("PROJECT_BUILD_MIXED_LAYER_OBJECT=EXCLUDED")
    print("VERIFIED_AIR=DEFERRED_TO_STABILITY")
    print("EXECUTION_PLAN=DEFERRED_TO_STABILITY")
    print("GENERAL_CACHE_STORE=NONE")
    print("PERSISTENCE=NONE")
    print("PROJECT_BUILDER_INTEGRATION=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("SEMANTIC_OWNER_MUTATION=NONE")
    print("P11_12D_RESONANCE_LAYER_REUSE=PASS")


if __name__ == "__main__":
    main()