"""AFP-P11.6A narrative execution architecture audit smoke test.

Audit-only gate. This test proves the frozen P11.5 narrative model and the
existing AIR project/runtime/build contracts remain separate while recording
the exact integration seams P11.6 must use later.
"""

from __future__ import annotations

import ast
import hashlib
import subprocess
from pathlib import Path

EXPECTED_BRANCH = "p11.6a-narrative-execution-architecture-audit"
EXPECTED_HEAD = "42538fc2afe8dc2fca824249edf7b797740c11e7"
BASELINE_TAG = "afp-p11.5-freeze"

THIS_FILE = "apexforge/p11_6a_narrative_execution_architecture_audit_smoke_test.py"
DOC_FILE = "docs/p11/P11_6A_NARRATIVE_EXECUTION_ARCHITECTURE_AUDIT.md"
AUTHORIZED_PATHS = (THIS_FILE, DOC_FILE)
PROTECTED_FIXTURE_PATHS = (
    "examples/P11Validation/apexforge.json",
    "examples/P11Validation/main.apex",
)
PROTECTED_MAIN_SHA256 = "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9"

FROZEN_SURFACES = (
    "apexforge/language/narrative_model.py",
    "apexforge/language/narrative_analysis.py",
    "apexforge/language/narrative_validation.py",
    "apexforge/language/project.py",
    "apexforge/runtime/engine.py",
    "apexforge/runtime/state.py",
    "apexforge/tooling/project_manifest.py",
    "apexforge/tooling/project_loader.py",
    "apexforge/tooling/project_scaffold.py",
    "apexforge/tooling/build_artifact.py",
    "apexforge/tooling/cli.py",
)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def git(root: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ("git", *args), cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if check and completed.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed ({completed.returncode}): "
            f"{completed.stderr.strip()}"
        )
    return completed.stdout.strip()

def read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")

def frozen_bytes(root: Path, relative: str) -> bytes:
    completed = subprocess.run(
        ("git", "show", f"{BASELINE_TAG}:{relative}"),
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    require(completed.returncode == 0, f"unable to read frozen baseline bytes for {relative}")
    return completed.stdout

def class_fields(source: str, class_name: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            fields = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fields.append(item.target.id)
            return tuple(fields)
    raise AssertionError(f"class {class_name} not found")

def main() -> None:
    root = Path(__file__).resolve().parents[1]

    require(git(root, "branch", "--show-current") == EXPECTED_BRANCH, "branch guard failed")
    current_head = git(root, "rev-parse", "HEAD")
    candidate_mode = current_head == EXPECTED_HEAD
    if not candidate_mode:
        require(
            git(root, "rev-parse", "HEAD^") == EXPECTED_HEAD,
            "predecessor guard failed",
        )
    require(git(root, "cat-file", "-t", BASELINE_TAG) == "tag", "freeze tag is not annotated")
    require(
        git(root, "rev-parse", BASELINE_TAG + "^{}") == EXPECTED_HEAD,
        "freeze tag does not resolve to the P11.5 track freeze",
    )

    status_before = tuple(
        line for line in git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
        if line
    )
    observed_paths = tuple(sorted(line[3:].replace("\\", "/") for line in status_before))
    require(
        observed_paths == tuple(sorted((AUTHORIZED_PATHS + PROTECTED_FIXTURE_PATHS) if candidate_mode else PROTECTED_FIXTURE_PATHS)),
        f"unexpected P11.6A ownership/protected-fixture set: {observed_paths!r}",
    )
    require(
        all(line.startswith("?? ") for line in status_before),
        "P11.6A audit files and protected fixture must remain untracked and unstaged",
    )
    fixture_main = root / "examples/P11Validation/main.apex"
    require(fixture_main.is_file(), "protected P11Validation main.apex is missing")
    require(
        hashlib.sha256(fixture_main.read_bytes()).hexdigest() == PROTECTED_MAIN_SHA256,
        "protected P11Validation main.apex hash changed",
    )
    require(
        (root / "examples/P11Validation/apexforge.json").is_file(),
        "protected P11Validation apexforge.json is missing",
    )

    for relative in FROZEN_SURFACES:
        current = (root / relative).read_bytes()
        baseline = frozen_bytes(root, relative)
        require(current == baseline, f"frozen surface changed: {relative}")

    narrative_model = read(root, "apexforge/language/narrative_model.py")
    project = read(root, "apexforge/language/project.py")
    engine = read(root, "apexforge/runtime/engine.py")
    runtime_state = read(root, "apexforge/runtime/state.py")
    manifest = read(root, "apexforge/tooling/project_manifest.py")
    loader = read(root, "apexforge/tooling/project_loader.py")
    scaffold = read(root, "apexforge/tooling/project_scaffold.py")
    artifact = read(root, "apexforge/tooling/build_artifact.py")
    cli = read(root, "apexforge/tooling/cli.py")

    require(
        class_fields(narrative_model, "NarrativeChoicePath")
        == ("label", "destination", "condition", "consequence"),
        "NarrativeChoicePath frozen field contract changed",
    )
    require(
        "condition: _Optional[str] = None" in narrative_model
        and "consequence: _Optional[str] = None" in narrative_model,
        "P11.5 condition/consequence descriptors are no longer optional strings",
    )
    require(
        class_fields(narrative_model, "NarrativeStateFact") == ("subject", "name", "value"),
        "NarrativeStateFact frozen field contract changed",
    )
    require("value: str" in narrative_model, "P11.5 narrative-state values are no longer descriptive strings")
    require(
        class_fields(narrative_model, "NarrativeContinuityConstraint") == ("subjects", "assertion"),
        "NarrativeContinuityConstraint frozen field contract changed",
    )
    require("assertion: str" in narrative_model, "P11.5 continuity assertions are no longer descriptive strings")

    project_build_fields = class_fields(project, "ProjectBuild")
    require("program" in project_build_fields, "ProjectBuild lost AIRProgram ownership")
    require("verified" in project_build_fields, "ProjectBuild lost VerifiedAIRProgram ownership")
    require("verified: VerifiedAIRProgram" in project, "ProjectBuild verified AIR contract changed")
    require(
        "engine: Optional[RuntimeEngine] = None" in project
        and "or RuntimeEngine()" in project
        and "return runtime.execute(" in project
        and "self.verified" in project,
        "ProjectBuild.execute no longer routes through the frozen AIR RuntimeEngine contract",
    )

    require(
        '\"""AIR runtime execution engine with expression evaluation.\"""' in repr(engine),
        "RuntimeEngine module is no longer explicitly AIR-owned",
    )
    require(
        "RuntimeEngine.execute requires VerifiedAIRProgram" in engine,
        "RuntimeEngine verified AIR input guard changed",
    )
    require(
        class_fields(engine, "ExecutionResult") == ("delta", "trace", "diagnostics", "final_state"),
        "AIR ExecutionResult contract changed",
    )
    require(
        "class StateSnapshot:" in runtime_state and "class StateDelta:" in runtime_state,
        "canonical AIR runtime state contracts changed",
    )

    require('PROJECT_MANIFEST_SCHEMA = 1' in manifest, "project manifest schema changed during P11.6A")
    require(
        '_ALLOWED_FIELDS = frozenset(("schema", "name", "sources", "entry"))' in manifest,
        "schema-1 manifest field set changed",
    )
    require(
        class_fields(manifest, "ProjectManifest") == ("name", "sources", "entry", "schema"),
        "ProjectManifest schema-1 record changed",
    )
    require(
        "if key not in _ALLOWED_FIELDS" in manifest and "if unknown:" in manifest,
        "unknown manifest fields are no longer rejected",
    )
    require(
        "class LoadedProject:" in loader
        and "manifest: ProjectManifest" in loader
        and "sources: Tuple[LoadedProjectSource, ...]" in loader,
        "project loader snapshot contract changed",
    )
    require(
        'DEFAULT_PROJECT_ENTRY = "Main"' in scaffold
        and "DEFAULT_PROJECT_SOURCE_TEXT" in scaffold
        and '\"""directive Main {' in repr(scaffold),
        "default scaffold is no longer the frozen directive/AIR project",
    )

    require(
        'BUILD_ARTIFACT_SCHEMA = "apexforge.build-artifact/v1"' in artifact,
        "build-artifact v1 schema changed",
    )
    require(
        'BUILD_ARTIFACT_FINGERPRINT_ALGORITHM = "sha256"' in artifact,
        "build-artifact fingerprint algorithm changed",
    )
    require(
        '"air": air_to_dict(build.program)' in artifact
        and '"project": project' in artifact
        and '"schema": BUILD_ARTIFACT_SCHEMA' in artifact,
        "build-artifact v1 payload is no longer AIR-specific",
    )

    require(
        'run = commands.add_parser(' in cli
        and 'help="build and execute one canonical project entry directive"' in cli,
        "public run command contract changed",
    )
    require(
        'build = commands.add_parser(' in cli
        and 'help="write one canonical linked multi-source build artifact"' in cli,
        "public build command contract changed",
    )
    require("construct_build_artifact(loaded, build)" in cli, "public build command no longer uses frozen build-artifact construction")

    prohibited_new_symbols = (
        "NarrativeExecutionState",
        "NarrativeExecutionResult",
        "NarrativeExecutionTrace",
        "NarrativeRuntimeEngine",
        "NarrativeEngine",
        "execute_narrative",
    )
    joined_frozen = "\n".join(read(root, relative) for relative in FROZEN_SURFACES)
    require(
        not any(symbol in joined_frozen for symbol in prohibited_new_symbols),
        "P11.6A crossed the audit-only boundary by adding narrative execution symbols",
    )

    doc = read(root, DOC_FILE)
    required_doc_phrases = (
        "Audit-only",
        "P11.5 remains observational",
        "AIR runtime remains unchanged",
        "Separate narrative execution state",
        "Separate narrative execution result and trace",
        "Do not reinterpret P11.5 strings as executable code",
        "Manifest schema 1 remains unchanged",
        "Build artifact v1 remains unchanged",
        "apexforge run",
        "apexforge build",
    )
    for phrase in required_doc_phrases:
        require(phrase in doc, f"architecture document omitted required phrase: {phrase!r}")

    status_after = tuple(
        line for line in git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
        if line
    )
    require(status_after == status_before, "P11.6A audit smoke test mutated repository state")

    hashes = {
        relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
        for relative in AUTHORIZED_PATHS
    }

    print("AFP-P11.6A narrative execution architecture audit smoke test passed.")
    print("Frozen P11.5 predecessor and annotated tag: PASS")
    print("Exact two-file audit ownership and repository no-op boundary: PASS")
    print("Frozen P11.5 narrative semantics preserved: PASS")
    print("AIR ProjectBuild, RuntimeEngine, state, CLI, and build artifact v1 preserved: PASS")
    print("Manifest schema 1 and directive scaffold preserved: PASS")
    print("Narrative execution remains unimplemented in P11.6A: PASS")
    print("Future execution seams documented without crossing them: PASS")
    print(f"{THIS_FILE} sha256={hashes[THIS_FILE]}")
    print(f"{DOC_FILE} sha256={hashes[DOC_FILE]}")

if __name__ == "__main__":
    main()
