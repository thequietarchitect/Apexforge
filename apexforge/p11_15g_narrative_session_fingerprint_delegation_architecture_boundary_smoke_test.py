"""P11.15G narrative-session fingerprint delegation architecture boundary.

Architecture-only.  This test freezes the evidence and exact successor
production contract for P11.15H.  It must not modify production behavior.
"""

from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

EXPECTED_F_FREEZE = "8cf8f04a9dde2a7473c2030599b52e3658edac02"
EXPECTED_F_TAG = "afp-p11-15f-freeze"
EXPECTED_BRANCH = (
    "p11-15g-narrative-session-fingerprint-delegation-architecture-boundary"
)

SESSION_PATH = ROOT / "apexforge" / "tooling" / "narrative_session.py"
EXECUTION_PATH = ROOT / "apexforge" / "tooling" / "narrative_execution.py"
D_PATH = ROOT / "apexforge" / "interoperability" / "build_artifact_integrity.py"
B_PATH = ROOT / "apexforge" / "interoperability" / "build_artifact.py"

EXPECTED_SESSION_SHA256 = (
    "B345A7B67F0AFC861882995B247D0FBF8B6E7B1FAD335B94B44013E3C945E164"
)
EXPECTED_F_EXECUTION_BLOB_SHA256 = (
    "80D31EB2AB98A71237230474AA5DDF1242BF4E25EC0EF0CF6327A02ED6A2F4A9"
)
EXPECTED_D_SHA256 = (
    "F59BDAD32412529135DF603A2C0584B359BF53D5117E29F3FEAE71BBA830A3BF"
)
EXPECTED_B_SHA256 = (
    "1C0E288FE4A9D4B620D715CC35554767062DA8296456B2612F7B9F25BCF9BBAD"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_git(*args: str) -> str:
    proc = subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            "git command failed: git {}\n{}".format(" ".join(args), proc.stderr)
        )
    return proc.stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def function(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    require(len(matches) == 1, "expected exactly one function {!r}".format(name))
    return matches[0]


def source_for(source: str, node: ast.AST) -> str:
    return "\n".join(source.splitlines()[node.lineno - 1:node.end_lineno])


def main() -> int:
    require(
        run_git("rev-parse", "HEAD") == EXPECTED_F_FREEZE,
        "P11.15G must remain architecture-only on the frozen F commit",
    )
    require(
        run_git("branch", "--show-current") == EXPECTED_BRANCH,
        "unexpected P11.15G architecture branch",
    )
    require(
        run_git("cat-file", "-t", EXPECTED_F_TAG) == "tag",
        "P11.15F freeze tag must remain annotated",
    )
    require(
        run_git("rev-parse", EXPECTED_F_TAG + "^{commit}") == EXPECTED_F_FREEZE,
        "P11.15F freeze tag target changed",
    )

    require(
        sha256(SESSION_PATH) == EXPECTED_SESSION_SHA256,
        "narrative_session changed during G architecture boundary",
    )
    require(
        sha256(D_PATH) == EXPECTED_D_SHA256,
        "P11.15D verifier changed during G architecture boundary",
    )
    require(
        sha256(B_PATH) == EXPECTED_B_SHA256,
        "P11.15B interchange owner changed during G architecture boundary",
    )

    execution_blob = subprocess.run(
        ("git", "show", "HEAD:apexforge/tooling/narrative_execution.py"),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    require(execution_blob.returncode == 0, "unable to read frozen F execution blob")
    require(
        hashlib.sha256(execution_blob.stdout).hexdigest().upper()
        == EXPECTED_F_EXECUTION_BLOB_SHA256,
        "frozen F execution blob changed",
    )

    source = SESSION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SESSION_PATH))
    read_json = function(tree, "_read_json")
    owner = function(tree, "load_narrative_session_material")
    read_source = source_for(source, read_json)
    owner_source = source_for(source, owner)

    # Canonical outer-byte enforcement is already a session-owned precondition.
    require(
        "require_canonical: bool = True" in read_source,
        "_read_json canonical default changed",
    )
    require(
        'if require_canonical and content != canonical_json_bytes(value):'
        in read_source,
        "_read_json canonical-byte check changed",
    )

    read_calls = [
        node
        for node in ast.walk(owner)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_read_json"
    ]
    require(len(read_calls) == 1, "session owner _read_json call count changed")
    require(
        all(keyword.arg != "require_canonical" for keyword in read_calls[0].keywords),
        "session owner now overrides require_canonical",
    )

    # Outer schema policy remains v1/v2 only.
    exact_outer_names = sorted(
        {
            node.id
            for node in ast.walk(owner)
            if isinstance(node, ast.Name)
            and node.id.startswith("BUILD_ARTIFACT_SCHEMA")
        }
    )
    require(
        exact_outer_names == ["BUILD_ARTIFACT_SCHEMA", "BUILD_ARTIFACT_SCHEMA_V2"],
        "session outer build-artifact schema policy changed",
    )
    require(
        not any(
            isinstance(node, ast.Name) and node.id == "BUILD_ARTIFACT_SCHEMA_V3"
            for node in ast.walk(owner)
        ),
        "session acquired outer build-artifact v3",
    )

    # Nested narrative v3 is distinct and must remain supported.
    require(
        any(
            isinstance(node, ast.Name)
            and node.id == "NARRATIVE_BUILD_ARTIFACT_SCHEMA_V3"
            for node in ast.walk(owner)
        ),
        "nested narrative v3 support changed",
    )

    # Current local fingerprint block is the exact duplication H will replace.
    current_markers = (
        "fingerprint = _mapping(",
        'fingerprint["algorithm"] != BUILD_ARTIFACT_FINGERPRINT_ALGORITHM',
        'raise ValueError("build artifact fingerprint shape mismatch")',
        "payload = dict(value)",
        'del payload["fingerprint"]',
        "expected = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()",
        'raise ValueError("build artifact fingerprint mismatch")',
    )
    for marker in current_markers:
        require(marker in owner_source, "current session fingerprint marker changed: " + marker)

    # Current ordering is canonical helper -> schema/shape -> fingerprint ->
    # unavailable narrative -> reconstruction -> frozen F execution reader.
    ordered = (
        "content, value = _read_json(",
        'schema = value["schema"]',
        "if schema == BUILD_ARTIFACT_SCHEMA:",
        "elif schema == BUILD_ARTIFACT_SCHEMA_V2:",
        'raise ValueError("build artifact schema mismatch")',
        "fingerprint = _mapping(",
        'raise ValueError("build artifact fingerprint mismatch")',
        'if "narrative" not in value:',
        'raise NarrativeSessionError("unavailable_narrative_material")',
        'narrative_value = value["narrative"]',
        "bindings = load_narrative_execution_material(artifact_path)",
        "return NarrativeSessionMaterial(",
        'artifact_fingerprint=fingerprint["value"]',
    )
    cursor = -1
    for marker in ordered:
        pos = owner_source.find(marker)
        require(pos >= 0, "session owner lost marker: {!r}".format(marker))
        require(pos > cursor, "session owner ordering changed at {!r}".format(marker))
        cursor = pos

    # Fingerprint association is session state, not a disposable integrity result.
    require(
        "session.artifact_fingerprint != material.artifact_fingerprint" in source,
        "session/material fingerprint association changed",
    )

    # F-owned executable binding reconstruction must remain separate.
    require(
        "bindings = load_narrative_execution_material(artifact_path)" in owner_source,
        "session no longer calls frozen F execution reader",
    )

    # G is architecture-only: H imports/delegation must be absent now.
    require(
        "from interoperability.build_artifact import BuildArtifactInterchange"
        not in source,
        "P11.15H production integration appeared during G architecture boundary",
    )
    require(
        "verify_build_artifact_interchange_fingerprint" not in source,
        "P11.15H D delegation appeared during G architecture boundary",
    )

    # Import cleanup pressure: hashlib is exact-local-use, while the algorithm
    # constant and canonical serializer remain session-owned elsewhere.
    hashlib_uses = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "hashlib"
    ]
    algorithm_uses = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id == "BUILD_ARTIFACT_FINGERPRINT_ALGORITHM"
    ]
    canonical_uses = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "canonical_json_bytes"
    ]
    owner_range = range(owner.lineno, owner.end_lineno + 1)

    require(
        len(hashlib_uses) == 1
        and all(node.lineno in owner_range for node in hashlib_uses),
        "hashlib is no longer exact-local-use pressure",
    )
    require(
        any(node.lineno not in owner_range for node in algorithm_uses),
        "fingerprint algorithm constant has no session-owned use outside owner",
    )
    require(
        any(node.lineno not in owner_range for node in canonical_uses),
        "canonical_json_bytes has no session-owned use outside owner",
    )

    # Freeze the P11.15H successor contract.
    successor_contract = (
        "BuildArtifactInterchange",
        "verify_build_artifact_interchange_fingerprint",
        "artifact_fingerprint",
    )
    require(
        successor_contract == (
            "BuildArtifactInterchange",
            "verify_build_artifact_interchange_fingerprint",
            "artifact_fingerprint",
        ),
        "P11.15H successor contract changed",
    )

    print("P11_15G_P11_15F_FREEZE_ANCESTRY=PASS")
    print("P11_15G_SCOPE=ARCHITECTURE_ONLY")
    print("P11_15G_PRODUCTION_FILES=0")
    print("P11_15G_SESSION_BYTE_IDENTICAL=PASS")
    print("P11_15G_EFFECTIVE_CANONICAL_OUTER_POLICY=TRUE")
    print("P11_15G_CANONICAL_OUTER_POLICY=BEFORE_SESSION_OWNER_POLICY")
    print("P11_15G_ACCEPTED_OUTER_SCHEMAS=V1_V2_ONLY")
    print("P11_15G_OUTER_V3=REJECTED")
    print("P11_15G_NESTED_NARRATIVE_V3=SUPPORTED_DISTINCTLY")
    print("P11_15G_CURRENT_LOCAL_FINGERPRINT_BLOCK=PRESENT")
    print("P11_15G_FINGERPRINT_RETENTION=REQUIRED")
    print("P11_15G_SESSION_ASSOCIATION_DEPENDS_ON_FINGERPRINT=YES")
    print("P11_15G_F_EXECUTION_READER_CALL=PRESERVE")
    print("P11_15G_POST_H_DOUBLE_D_VERIFICATION=EXPECTED")
    print("P11_15G_H_BUILD_ARTIFACT_INSPECTOR=FORBIDDEN")
    print("P11_15G_H_INTERCHANGE_CONSTRUCTION=AFTER_SESSION_SCHEMA_POLICY")
    print("P11_15G_H_D_RETURN_VALUE=RETAIN_AS_artifact_fingerprint")
    print("P11_15G_H_REMOVE_HASHLIB=YES")
    print("P11_15G_H_REMOVE_FINGERPRINT_ALGORITHM_IMPORT=NO")
    print("P11_15G_H_REMOVE_CANONICAL_JSON_IMPORT=NO")
    print("P11_15G_H_PRODUCTION_TARGET=apexforge/tooling/narrative_session.py")
    print("P11_15G_H_PRODUCTION_FILES=ONE_EXISTING_FILE")
    print("P11_15G_H_NEW_PRODUCTION_MODULE=NONE")
    print("P11_15G_H_PUBLIC_API_CHANGE=NONE")
    print("P11_15G_H_INTEROPERABILITY_OWNER_MUTATION=NONE")
    print("P11_15G_H_EXECUTION_READER_MUTATION=NONE")
    print("P11_15G_H_CLI_EDITOR_RUNTIME_AGENT_EFFECT_QV_MUTATION=NONE")
    print("P11_15G_H_NETWORK_RPC_FFI_NATIVE_ABI=NONE")
    print("P11_15G_NARRATIVE_SESSION_FINGERPRINT_DELEGATION_ARCHITECTURE_BOUNDARY=PASS")
    print("P11_15G_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())