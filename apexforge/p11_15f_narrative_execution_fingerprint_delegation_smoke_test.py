"""P11.15F narrative-execution fingerprint delegation smoke test."""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "99253c16939299a7f8a6ad209772a5038c8ca28e"
PREDECESSOR_TAG = "afp-p11-15e-freeze"
EXPECTED_BRANCH = "p11-15f-narrative-execution-fingerprint-delegation"

FROZEN_HASHES = {
    "apexforge/interoperability/build_artifact_integrity.py":
        "F59BDAD32412529135DF603A2C0584B359BF53D5117E29F3FEAE71BBA830A3BF",
    "apexforge/interoperability/__init__.py":
        "6DA040DF8EC6727CD9449A37C5EC07C8F8DD1C98D3F25F824B29F23F2261CA7B",
    "apexforge/interoperability/build_artifact.py":
        "1C0E288FE4A9D4B620D715CC35554767062DA8296456B2612F7B9F25BCF9BBAD",
    "apexforge/tooling/build_artifact.py":
        "FBB3B49E85D549705AF5BD0ED0459063DCEAB4487A65E68BAF24E6DD6972B76B",
    "apexforge/tooling/narrative_session.py":
        "B345A7B67F0AFC861882995B247D0FBF8B6E7B1FAD335B94B44013E3C945E164",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper()


def owner_source(source: str, filename: str) -> str:
    tree = ast.parse(source, filename=filename)
    owners = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "load_narrative_execution_material"
    ]
    require(len(owners) == 1, "narrative-execution load owner changed")
    node = owners[0]
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
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.15E freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.15E freeze is not ancestor of P11.15F",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.15F branch changed")

    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))

    execution_path = ROOT / "apexforge" / "tooling" / "narrative_execution.py"
    source = execution_path.read_text(encoding="utf-8")
    owner = owner_source(source, str(execution_path))

    # Intended RED: this is the first integration assertion.
    require(
        "from interoperability.build_artifact import BuildArtifactInterchange"
        in source,
        "P11.15F integration absent: missing BuildArtifactInterchange import",
    )

    require(
        "from interoperability.build_artifact_integrity import" in source
        and "verify_build_artifact_interchange_fingerprint" in source,
        "P11.15F integration absent: missing D verifier import",
    )
    require(
        "inspect_build_artifact_interchange" not in source,
        "P11.15F incorrectly uses B inspector",
    )

    # Exact import cleanup.
    require("import hashlib" not in source, "local hashlib import remains")
    require(
        "BUILD_ARTIFACT_FINGERPRINT_ALGORITHM" not in source,
        "local fingerprint algorithm import/use remains",
    )
    require(
        "canonical_json_bytes" in source,
        "canonical_json_bytes was incorrectly removed",
    )

    # Exact local fingerprint block removed.
    for forbidden in (
        'fingerprint = _mapping(',
        'del payload["fingerprint"]',
        "hashlib.sha256(canonical_json_bytes(payload)).hexdigest()",
    ):
        require(forbidden not in owner, "local fingerprint block remains: " + forbidden)

    required_order = (
        'if content != canonical_json_bytes(value):',
        'raise ValueError("build artifact is not canonical JSON")',
        'historical_keys = frozenset(("air", "fingerprint", "project", "schema"))',
        'integrated_keys = historical_keys | frozenset(("narrative",))',
        'native_narrative_keys = frozenset(("fingerprint", "narrative", "project", "schema"))',
        'if schema == BUILD_ARTIFACT_SCHEMA:',
        'elif schema == BUILD_ARTIFACT_SCHEMA_V2:',
        'raise ValueError("build artifact shape or schema mismatch")',
        'verify_build_artifact_interchange_fingerprint(',
        'BuildArtifactInterchange(',
        'schema=schema',
        'content=content',
        'if keys == historical_keys:',
        '"unavailable_narrative_material"',
        'return _narrative_bindings(value["narrative"])',
    )
    cursor = -1
    for marker in required_order:
        position = owner.find(marker)
        require(position >= 0, "F owner lost marker: " + marker)
        require(position > cursor, "F owner ordering changed at: " + marker)
        cursor = position

    # D return is not retained.
    require(
        "= verify_build_artifact_interchange_fingerprint(" not in owner,
        "D return value is unexpectedly retained",
    )
    require(
        "return verify_build_artifact_interchange_fingerprint(" not in owner,
        "D return value is unexpectedly returned",
    )

    module = importlib.import_module("tooling.narrative_execution")
    from tooling.build_artifact import (
        BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
        BUILD_ARTIFACT_SCHEMA,
        BUILD_ARTIFACT_SCHEMA_V2,
        BUILD_ARTIFACT_SCHEMA_V3,
        canonical_json_bytes,
    )

    original_verify = module.verify_build_artifact_interchange_fingerprint

    def artifact(schema: str, keys: str = "historical", *, bad_fp=None) -> bytes:
        if keys == "historical":
            payload = {
                "air": {},
                "project": {},
                "schema": schema,
            }
        elif keys == "integrated":
            payload = {
                "air": {},
                "narrative": {},
                "project": {},
                "schema": schema,
            }
        elif keys == "native":
            payload = {
                "narrative": {},
                "project": {},
                "schema": schema,
            }
        else:
            raise AssertionError(keys)

        fingerprint = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
        value = dict(payload)
        value["fingerprint"] = (
            {
                "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
                "value": fingerprint,
            }
            if bad_fp is None
            else bad_fp
        )
        return canonical_json_bytes(value)

    # Consumer schema/shape/canonical checks must run before D.
    calls = []

    def tracker(interchange):
        calls.append(interchange)
        return "verified"

    module.verify_build_artifact_interchange_fingerprint = tracker
    try:
        # v3 remains rejected before D.
        path = write_temp(artifact(BUILD_ARTIFACT_SCHEMA_V3, "native"))
        try:
            try:
                module.load_narrative_execution_material(path)
            except module.NarrativeExecutionRoutingError as exc:
                require(
                    getattr(exc, "__cause__", None) is not None,
                    "v3 rejection lost malformed cause",
                )
                require(
                    str(exc.__cause__) == "build artifact shape or schema mismatch",
                    "v3 rejection cause changed",
                )
            else:
                raise AssertionError("outer v3 unexpectedly accepted")
            require(calls == [], "D was called before v3 rejection")
        finally:
            path.unlink(missing_ok=True)

        # Unknown schema remains rejected before D.
        path = write_temp(artifact("apexforge.build-artifact/unknown", "historical"))
        try:
            try:
                module.load_narrative_execution_material(path)
            except module.NarrativeExecutionRoutingError as exc:
                require(
                    str(exc.__cause__) == "build artifact shape or schema mismatch",
                    "unknown schema rejection cause changed",
                )
            else:
                raise AssertionError("unknown schema unexpectedly accepted")
            require(calls == [], "D was called before unknown-schema rejection")
        finally:
            path.unlink(missing_ok=True)

        # Noncanonical bytes remain rejected before D.
        canonical = artifact(BUILD_ARTIFACT_SCHEMA, "historical")
        pretty = json.dumps(
            json.loads(canonical.decode("utf-8")),
            indent=2,
        ).encode("utf-8")
        require(pretty != canonical, "noncanonical fixture unexpectedly canonical")
        path = write_temp(pretty)
        try:
            try:
                module.load_narrative_execution_material(path)
            except module.NarrativeExecutionRoutingError as exc:
                require(
                    str(exc.__cause__) == "build artifact is not canonical JSON",
                    "canonical-byte rejection cause changed",
                )
            else:
                raise AssertionError("noncanonical outer bytes unexpectedly accepted")
            require(calls == [], "D was called before canonical-byte rejection")
        finally:
            path.unlink(missing_ok=True)

        # Valid historical v1 reaches D before unavailable routing.
        path = write_temp(artifact(BUILD_ARTIFACT_SCHEMA, "historical"))
        try:
            try:
                module.load_narrative_execution_material(path)
            except module.NarrativeExecutionRoutingError as exc:
                require(
                    type(exc) is module.NarrativeExecutionRoutingError,
                    "historical unavailable routing exception type changed",
                )
                require(
                    str(exc)
                    == (
                        "[APX-NARRATIVE-112] canonical narrative build "
                        "material is unavailable."
                    ),
                    "historical unavailable routing changed",
                )
            else:
                raise AssertionError("historical no-narrative artifact unexpectedly loaded")
            require(len(calls) == 1, "historical v1 did not reach D exactly once")
            interchange = calls[-1]
            require(
                interchange.schema == BUILD_ARTIFACT_SCHEMA,
                "delegated interchange schema changed",
            )
            require(
                interchange.content == artifact(BUILD_ARTIFACT_SCHEMA, "historical"),
                "delegated interchange content changed",
            )
        finally:
            path.unlink(missing_ok=True)

        # v2 native shape reaches D before narrative reconstruction.
        calls.clear()

        class StopAfterD(RuntimeError):
            pass

        def stop_after_d(interchange):
            calls.append(interchange)
            raise StopAfterD()

        module.verify_build_artifact_interchange_fingerprint = stop_after_d
        path = write_temp(artifact(BUILD_ARTIFACT_SCHEMA_V2, "native"))
        try:
            try:
                module.load_narrative_execution_material(path)
            except StopAfterD:
                pass
            else:
                raise AssertionError("v2 did not delegate to D")
            require(len(calls) == 1, "v2 did not reach D exactly once")
        finally:
            path.unlink(missing_ok=True)

    finally:
        module.verify_build_artifact_interchange_fingerprint = original_verify

    # Actual D errors preserve existing underlying text.
    malformed = {
        "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
    }
    for bad_fp, expected_message in (
        (malformed, "build artifact fingerprint shape mismatch"),
        (
            {
                "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
                "value": "0" * 64,
            },
            "build artifact fingerprint mismatch",
        ),
    ):
        path = write_temp(
            artifact(
                BUILD_ARTIFACT_SCHEMA,
                "historical",
                bad_fp=bad_fp,
            )
        )
        try:
            try:
                module.load_narrative_execution_material(path)
            except module.NarrativeExecutionRoutingError as exc:
                require(
                    getattr(exc, "__cause__", None) is not None,
                    "fingerprint failure lost malformed cause",
                )
                require(
                    str(exc.__cause__) == expected_message,
                    "fingerprint failure message changed",
                )
            else:
                raise AssertionError("invalid fingerprint unexpectedly accepted")
        finally:
            path.unlink(missing_ok=True)

    print("P11_15E_FREEZE_ANCESTRY=PASS")
    print("P11_15F_SCOPE=NARRATIVE_EXECUTION_ONLY")
    print("P11_15F_D_B_FILES_BYTE_IDENTICAL=PASS")
    print("P11_15F_NARRATIVE_SESSION_BYTE_IDENTICAL=PASS")
    print("P11_15F_EXPLICIT_INTERCHANGE_IMPORT=PASS")
    print("P11_15F_EXPLICIT_D_VERIFIER_IMPORT=PASS")
    print("P11_15F_BUILD_ARTIFACT_INSPECTOR=ABSENT")
    print("P11_15F_LOCAL_FINGERPRINT_BLOCK=REMOVED")
    print("P11_15F_HASHLIB_IMPORT=REMOVED")
    print("P11_15F_FINGERPRINT_ALGORITHM_IMPORT=REMOVED")
    print("P11_15F_CANONICAL_JSON_IMPORT=RETAINED")
    print("P11_15F_CANONICAL_OUTER_POLICY=PRESERVED_BEFORE_DELEGATION")
    print("P11_15F_TOP_LEVEL_SHAPE_POLICY=PRESERVED")
    print("P11_15F_ACCEPTED_OUTER_SCHEMAS=V1_V2_ONLY")
    print("P11_15F_OUTER_V3=REJECTED_BEFORE_D")
    print("P11_15F_UNKNOWN_SCHEMA=REJECTED_BEFORE_D")
    print("P11_15F_D_RETURN_VALUE=IGNORED")
    print("P11_15F_HISTORICAL_UNAVAILABLE_ROUTING=AFTER_D")
    print("P11_15F_FINGERPRINT_ERROR_MESSAGES=PRESERVED")
    print("P11_15F_NARRATIVE_RECONSTRUCTION=CONSUMER_OWNED")
    print("P11_15F_NARRATIVE_SESSION_INTEGRATION=NONE")
    print("P11_15F_NARRATIVE_EXECUTION_FINGERPRINT_DELEGATION=PASS")
    print("P11_15F_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())