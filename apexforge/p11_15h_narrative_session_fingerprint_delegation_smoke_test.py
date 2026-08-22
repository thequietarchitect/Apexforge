"""P11.15H narrative-session fingerprint delegation production contract."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

EXPECTED_G_FREEZE = "8605f06c276e9ba4e737bc0de26bb5b89dd0439f"
EXPECTED_G_TAG = "afp-p11-15g-freeze"
EXPECTED_BRANCH = "p11-15h-narrative-session-fingerprint-delegation"

SESSION_PATH = ROOT / "apexforge" / "tooling" / "narrative_session.py"
D_PATH = ROOT / "apexforge" / "interoperability" / "build_artifact_integrity.py"
B_PATH = ROOT / "apexforge" / "interoperability" / "build_artifact.py"
EXECUTION_PATH = ROOT / "apexforge" / "tooling" / "narrative_execution.py"
G_TEST_PATH = (
    ROOT
    / "apexforge"
    / "p11_15g_narrative_session_fingerprint_delegation_architecture_boundary_smoke_test.py"
)
G_DOC_PATH = (
    ROOT
    / "docs"
    / "p11"
    / "P11_15G_NARRATIVE_SESSION_FINGERPRINT_DELEGATION_ARCHITECTURE_BOUNDARY.md"
)

EXPECTED_D_SHA256 = (
    "F59BDAD32412529135DF603A2C0584B359BF53D5117E29F3FEAE71BBA830A3BF"
)
EXPECTED_B_SHA256 = (
    "1C0E288FE4A9D4B620D715CC35554767062DA8296456B2612F7B9F25BCF9BBAD"
)
EXPECTED_F_EXECUTION_BLOB_SHA256 = (
    "80D31EB2AB98A71237230474AA5DDF1242BF4E25EC0EF0CF6327A02ED6A2F4A9"
)
EXPECTED_G_TEST_SHA256 = (
    "5633ECFDDBB84286189F3ADFE294E499F4611DD623E6072A1BBC53CEBCE9DD02"
)
EXPECTED_G_DOC_SHA256 = (
    "5C16F0E73AFEF8F43D98FC2FD54ED98C6B4BF13E109CD046001DF05B02F808DA"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git(*args: str, binary: bool = False):
    proc = subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not binary,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (
            proc.stderr.decode("utf-8", "replace")
            if binary
            else proc.stderr
        )
        raise AssertionError(
            "git failed: git {}\n{}".format(" ".join(args), stderr)
        )
    return proc.stdout


def function(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    require(len(matches) == 1, "expected one function {!r}".format(name))
    return matches[0]


def owner_source(source: str, node: ast.AST) -> str:
    return "\n".join(source.splitlines()[node.lineno - 1:node.end_lineno])


def write_temp(content: bytes) -> Path:
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    try:
        handle.write(content)
        handle.flush()
        return Path(handle.name)
    finally:
        handle.close()


def main() -> int:
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_G_FREEZE,
        "P11.15H must start from exact frozen G HEAD",
    )
    require(
        git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "unexpected P11.15H branch",
    )
    require(
        git("cat-file", "-t", EXPECTED_G_TAG).strip() == "tag",
        "P11.15G freeze tag must remain annotated",
    )
    require(
        git("rev-parse", EXPECTED_G_TAG + "^{commit}").strip()
        == EXPECTED_G_FREEZE,
        "P11.15G freeze tag target changed",
    )

    require(sha256(D_PATH) == EXPECTED_D_SHA256, "P11.15D verifier changed")
    require(sha256(B_PATH) == EXPECTED_B_SHA256, "P11.15B interchange changed")
    require(sha256(G_TEST_PATH) == EXPECTED_G_TEST_SHA256, "G test changed")
    require(sha256(G_DOC_PATH) == EXPECTED_G_DOC_SHA256, "G doc changed")
    require(
        hashlib.sha256(
            git(
                "show",
                "HEAD:apexforge/tooling/narrative_execution.py",
                binary=True,
            )
        ).hexdigest().upper()
        == EXPECTED_F_EXECUTION_BLOB_SHA256,
        "frozen F execution reader changed",
    )

    source = SESSION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SESSION_PATH))
    owner = function(tree, "load_narrative_session_material")
    read_json = function(tree, "_read_json")
    owner_text = owner_source(source, owner)
    read_text = owner_source(source, read_json)

    # H integration must exist explicitly.
    require(
        "from interoperability.build_artifact import BuildArtifactInterchange"
        in source,
        "P11.15H integration absent: missing BuildArtifactInterchange import",
    )
    require(
        "from interoperability.build_artifact_integrity import (" in source
        and "verify_build_artifact_interchange_fingerprint" in source,
        "P11.15H integration absent: missing D verifier import",
    )
    require(
        "inspect_build_artifact_interchange" not in source,
        "P11.15H must not call the B inspector",
    )

    # Existing canonical policy is still the first material policy.
    require(
        "require_canonical: bool = True" in read_text,
        "_read_json canonical default changed",
    )
    require(
        'if require_canonical and content != canonical_json_bytes(value):'
        in read_text,
        "_read_json canonical byte policy changed",
    )

    # Exact outer schemas remain v1/v2 only; nested narrative v3 remains.
    outer_names = sorted(
        {
            node.id
            for node in ast.walk(owner)
            if isinstance(node, ast.Name)
            and node.id.startswith("BUILD_ARTIFACT_SCHEMA")
        }
    )
    require(
        outer_names == ["BUILD_ARTIFACT_SCHEMA", "BUILD_ARTIFACT_SCHEMA_V2"],
        "session outer schema policy changed",
    )
    require(
        any(
            isinstance(node, ast.Name)
            and node.id == "NARRATIVE_BUILD_ARTIFACT_SCHEMA_V3"
            for node in ast.walk(owner)
        ),
        "nested narrative v3 support changed",
    )

    # Local duplicate block is gone.
    for forbidden in (
        "fingerprint = _mapping(",
        "expected = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()",
        'del payload["fingerprint"]',
        'raise ValueError("build artifact fingerprint mismatch")',
    ):
        require(
            forbidden not in owner_text,
            "P11.15H local fingerprint block remains: " + forbidden,
        )

    # hashlib becomes removable, but session-owned imports remain.
    require("import hashlib" not in source, "P11.15H hashlib import remains")
    require(
        "BUILD_ARTIFACT_FINGERPRINT_ALGORITHM" in source,
        "session-owned fingerprint algorithm import was removed",
    )
    require(
        "canonical_json_bytes" in source,
        "session-owned canonical_json_bytes import was removed",
    )
    require(
        '"algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM' in source,
        "session serialization fingerprint algorithm use changed",
    )
    require(
        'return canonical_json_bytes(narrative_session_payload(session))'
        in source,
        "session canonical serialization changed",
    )

    # D return must be retained, unlike F.
    required_snippet = (
        "artifact_fingerprint = verify_build_artifact_interchange_fingerprint(\n"
        "            BuildArtifactInterchange(\n"
        "                schema=schema,\n"
        "                content=content,\n"
        "            )\n"
        "        )"
    )
    require(
        required_snippet in owner_text,
        "P11.15H retained D-return delegation shape changed",
    )
    require(
        "artifact_fingerprint=artifact_fingerprint" in owner_text,
        "P11.15H material does not retain D return",
    )
    require(
        'artifact_fingerprint=fingerprint["value"]' not in owner_text,
        "P11.15H still retains old local fingerprint mapping",
    )

    # Preserve order: helper/canonical -> schema -> D -> unavailable ->
    # session reconstruction -> frozen F reader -> material.
    ordered = (
        "content, value = _read_json(",
        'schema = value["schema"]',
        "if schema == BUILD_ARTIFACT_SCHEMA:",
        "elif schema == BUILD_ARTIFACT_SCHEMA_V2:",
        'raise ValueError("build artifact schema mismatch")',
        "artifact_fingerprint = verify_build_artifact_interchange_fingerprint(",
        "BuildArtifactInterchange(",
        "schema=schema",
        "content=content",
        'if "narrative" not in value:',
        'raise NarrativeSessionError("unavailable_narrative_material")',
        'narrative_value = value["narrative"]',
        "bindings = load_narrative_execution_material(artifact_path)",
        "return NarrativeSessionMaterial(",
        "artifact_fingerprint=artifact_fingerprint",
    )
    cursor = -1
    for marker in ordered:
        position = owner_text.find(marker)
        require(position >= 0, "session owner lost marker: {!r}".format(marker))
        require(position > cursor, "session owner order changed at {!r}".format(marker))
        cursor = position

    require(
        source.count("verify_build_artifact_interchange_fingerprint") == 2,
        "D verifier must appear in exactly one import and one session call",
    )
    require(
        "bindings = load_narrative_execution_material(artifact_path)"
        in owner_text,
        "frozen F execution-reader call was removed",
    )

    # Dynamic ordering and retained-return behavior.
    import tooling.narrative_session as module
    from interoperability.build_artifact import BuildArtifactInterchange
    from tooling.build_artifact import (
        BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
        BUILD_ARTIFACT_SCHEMA,
        BUILD_ARTIFACT_SCHEMA_V2,
        canonical_json_bytes,
    )

    def make_outer(schema: str, *, narrative=True, fingerprint=None) -> bytes:
        value = {
            "project": {},
            "schema": schema,
        }
        if schema == BUILD_ARTIFACT_SCHEMA:
            value["air"] = {}
        if narrative:
            value["narrative"] = {
                "schema": module.NARRATIVE_BUILD_ARTIFACT_SCHEMA,
                "source": "fixture.afp",
                "story": {},
                "bindings": {},
            }
        payload = dict(value)
        actual = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
        value["fingerprint"] = (
            {
                "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
                "value": actual,
            }
            if fingerprint is None
            else fingerprint
        )
        return canonical_json_bytes(value)

    original_verify = module.verify_build_artifact_interchange_fingerprint
    original_inventory = module._artifact_identity_inventory
    original_execution = module.load_narrative_execution_material
    original_material = module.NarrativeSessionMaterial

    calls = []
    retained = "a" * 64
    story = object()

    def verifier(interchange):
        require(
            type(interchange) is BuildArtifactInterchange,
            "session D call did not receive exact BuildArtifactInterchange",
        )
        calls.append(interchange)
        return retained

    def inventory(value, schema):
        return story, frozenset(), frozenset(), (), ()

    def execution_reader(path):
        return SimpleNamespace(story=story)

    def material_ctor(**kwargs):
        return kwargs

    module.verify_build_artifact_interchange_fingerprint = verifier
    module._artifact_identity_inventory = inventory
    module.load_narrative_execution_material = execution_reader
    module.NarrativeSessionMaterial = material_ctor
    try:
        valid = make_outer(BUILD_ARTIFACT_SCHEMA_V2)
        path = write_temp(valid)
        try:
            result = module.load_narrative_session_material(path)
        finally:
            path.unlink(missing_ok=True)

        require(len(calls) == 1, "valid v2 did not reach D exactly once")
        require(calls[0].schema == BUILD_ARTIFACT_SCHEMA_V2, "D schema changed")
        require(calls[0].content == valid, "D content bytes changed")
        require(
            result["artifact_fingerprint"] == retained,
            "NarrativeSessionMaterial did not retain D return",
        )

        calls.clear()

        # Noncanonical bytes are rejected before D.
        canonical = make_outer(BUILD_ARTIFACT_SCHEMA_V2)
        pretty = json.dumps(
            json.loads(canonical.decode("utf-8")),
            indent=2,
        ).encode("utf-8")
        require(pretty != canonical, "noncanonical fixture unexpectedly canonical")
        path = write_temp(pretty)
        try:
            try:
                module.load_narrative_session_material(path)
            except module.NarrativeSessionError as exc:
                require(
                    exc.classification == "malformed_build_artifact",
                    "noncanonical session routing changed",
                )
            else:
                raise AssertionError("noncanonical session artifact accepted")
        finally:
            path.unlink(missing_ok=True)
        require(not calls, "D ran before canonical outer-byte rejection")

        # Outer v3 is rejected before D.
        path = write_temp(make_outer("apexforge.build-artifact/v3"))
        try:
            try:
                module.load_narrative_session_material(path)
            except module.NarrativeSessionError as exc:
                require(
                    exc.classification == "malformed_build_artifact",
                    "outer v3 session routing changed",
                )
            else:
                raise AssertionError("outer v3 session artifact accepted")
        finally:
            path.unlink(missing_ok=True)
        require(not calls, "D ran before outer-v3 rejection")

    finally:
        module.verify_build_artifact_interchange_fingerprint = original_verify
        module._artifact_identity_inventory = original_inventory
        module.load_narrative_execution_material = original_execution
        module.NarrativeSessionMaterial = original_material

    # Real D failures keep the same underlying cause text and session wrapper.
    for fingerprint, expected in (
        (
            {"algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM},
            "build artifact fingerprint shape mismatch",
        ),
        (
            {
                "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
                "value": "0" * 64,
            },
            "build artifact fingerprint mismatch",
        ),
    ):
        path = write_temp(
            make_outer(
                BUILD_ARTIFACT_SCHEMA_V2,
                fingerprint=fingerprint,
            )
        )
        try:
            try:
                module.load_narrative_session_material(path)
            except module.NarrativeSessionError as exc:
                require(
                    exc.classification == "malformed_build_artifact",
                    "fingerprint session wrapper changed",
                )
                require(
                    str(exc.__cause__) == expected,
                    "fingerprint underlying D cause changed",
                )
            else:
                raise AssertionError("invalid fingerprint unexpectedly accepted")
        finally:
            path.unlink(missing_ok=True)

    # Historical v1 without narrative verifies first, then preserves the
    # unavailable-narrative classification.
    path = write_temp(make_outer(BUILD_ARTIFACT_SCHEMA, narrative=False))
    try:
        try:
            module.load_narrative_session_material(path)
        except module.NarrativeSessionError as exc:
            require(
                exc.classification == "unavailable_narrative_material",
                "historical unavailable-narrative session route changed",
            )
        else:
            raise AssertionError("historical artifact without narrative loaded")
    finally:
        path.unlink(missing_ok=True)

    print("P11_15G_FREEZE_ANCESTRY=PASS")
    print("P11_15H_SCOPE=NARRATIVE_SESSION_ONLY")
    print("P11_15H_D_B_G_F_FILES_BYTE_IDENTICAL=PASS")
    print("P11_15H_EXPLICIT_INTERCHANGE_IMPORT=PASS")
    print("P11_15H_EXPLICIT_D_VERIFIER_IMPORT=PASS")
    print("P11_15H_BUILD_ARTIFACT_INSPECTOR=ABSENT")
    print("P11_15H_LOCAL_FINGERPRINT_BLOCK=REMOVED")
    print("P11_15H_HASHLIB_IMPORT=REMOVED")
    print("P11_15H_FINGERPRINT_ALGORITHM_IMPORT=RETAINED")
    print("P11_15H_CANONICAL_JSON_IMPORT=RETAINED")
    print("P11_15H_CANONICAL_OUTER_POLICY=PRESERVED_BEFORE_DELEGATION")
    print("P11_15H_ACCEPTED_OUTER_SCHEMAS=V1_V2_ONLY")
    print("P11_15H_OUTER_V3=REJECTED_BEFORE_D")
    print("P11_15H_NESTED_NARRATIVE_V3=SUPPORTED_DISTINCTLY")
    print("P11_15H_D_RETURN_VALUE=RETAINED_AS_artifact_fingerprint")
    print("P11_15H_MATERIAL_FINGERPRINT_ASSOCIATION=PRESERVED")
    print("P11_15H_HISTORICAL_UNAVAILABLE_ROUTING=AFTER_D")
    print("P11_15H_FINGERPRINT_ERROR_MESSAGES=PRESERVED_VIA_D")
    print("P11_15H_SESSION_RECONSTRUCTION=SESSION_OWNED")
    print("P11_15H_F_EXECUTION_READER_CALL=PRESERVED")
    print("P11_15H_DOUBLE_D_VERIFICATION=EXPECTED")
    print("P11_15H_NARRATIVE_SESSION_FINGERPRINT_DELEGATION=PASS")
    print("P11_15H_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())