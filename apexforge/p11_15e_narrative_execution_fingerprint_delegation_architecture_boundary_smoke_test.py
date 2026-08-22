"""P11.15E narrative-execution fingerprint delegation architecture boundary."""

from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "8525d6e4a0b9b35dda5e06af6b5e1289fd39a2ac"
PREDECESSOR_TAG = "afp-p11-15d-freeze"
EXPECTED_BRANCH = (
    "p11-15e-narrative-execution-fingerprint-delegation-architecture-boundary"
)

FROZEN_HASHES = {
    "apexforge/interoperability/build_artifact_integrity.py":
        "F59BDAD32412529135DF603A2C0584B359BF53D5117E29F3FEAE71BBA830A3BF",
    "apexforge/interoperability/__init__.py":
        "6DA040DF8EC6727CD9449A37C5EC07C8F8DD1C98D3F25F824B29F23F2261CA7B",
    "apexforge/interoperability/build_artifact.py":
        "1C0E288FE4A9D4B620D715CC35554767062DA8296456B2612F7B9F25BCF9BBAD",
    "apexforge/tooling/build_artifact.py":
        "FBB3B49E85D549705AF5BD0ED0459063DCEAB4487A65E68BAF24E6DD6972B76B",
    "apexforge/tooling/narrative_execution.py":
        "5E4AC0889F4703375A1861651312786E03163924EA938A9D43AF1D1C9582F59E",
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


def function_source(source: str, filename: str, name: str) -> str:
    tree = ast.parse(source, filename=filename)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return "\n".join(
                source.splitlines()[node.lineno - 1:node.end_lineno]
            )
    raise AssertionError("missing function: " + name)


def main() -> int:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.15D freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.15D freeze is not ancestor of P11.15E",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.15E branch changed")

    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))

    execution_path = ROOT / "apexforge" / "tooling" / "narrative_execution.py"
    session_path = ROOT / "apexforge" / "tooling" / "narrative_session.py"

    execution = execution_path.read_text(encoding="utf-8")
    session = session_path.read_text(encoding="utf-8")

    owner = function_source(
        execution,
        str(execution_path),
        "load_narrative_execution_material",
    )

    required_current_order = (
        'if content != canonical_json_bytes(value):',
        'raise ValueError("build artifact is not canonical JSON")',
        'historical_keys = frozenset(("air", "fingerprint", "project", "schema"))',
        'integrated_keys = historical_keys | frozenset(("narrative",))',
        'native_narrative_keys = frozenset(("fingerprint", "narrative", "project", "schema"))',
        'if schema == BUILD_ARTIFACT_SCHEMA:',
        'elif schema == BUILD_ARTIFACT_SCHEMA_V2:',
        'raise ValueError("build artifact shape or schema mismatch")',
        'fingerprint = _mapping(',
        'raise ValueError("build artifact fingerprint shape mismatch")',
        'del payload["fingerprint"]',
        'expected = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()',
        'raise ValueError("build artifact fingerprint mismatch")',
        'if keys == historical_keys:',
        '"unavailable_narrative_material"',
        'return _narrative_bindings(value["narrative"])',
    )

    cursor = -1
    for marker in required_current_order:
        position = owner.find(marker)
        require(position >= 0, "current execution owner lost marker: " + marker)
        require(
            position > cursor,
            "current execution owner ordering changed at: " + marker,
        )
        cursor = position

    # Current execution consumer has not already integrated B/D.
    for forbidden in (
        "BuildArtifactInterchange",
        "inspect_build_artifact_interchange",
        "verify_build_artifact_interchange_fingerprint",
        "interoperability.build_artifact",
        "interoperability.build_artifact_integrity",
    ):
        require(
            forbidden not in execution,
            "narrative_execution already acquired F dependency: " + forbidden,
        )

    # Session remains a separate later integration target.
    for forbidden in (
        "BuildArtifactInterchange",
        "inspect_build_artifact_interchange",
        "verify_build_artifact_interchange_fingerprint",
        "interoperability.build_artifact",
        "interoperability.build_artifact_integrity",
    ):
        require(
            forbidden not in session,
            "narrative_session unexpectedly acquired interoperability dependency: "
            + forbidden,
        )

    # Execution-specific cleanup is justified.
    require(execution.count("hashlib") == 2, "unexpected hashlib usage count")
    require(
        execution.count("BUILD_ARTIFACT_FINGERPRINT_ALGORITHM") == 2,
        "unexpected fingerprint algorithm usage count",
    )
    require(
        execution.count("canonical_json_bytes") >= 3,
        "canonical_json_bytes is not independently required",
    )
    require(
        execution.count("BUILD_ARTIFACT_SCHEMA") >= 2,
        "consumer build-artifact schema policy missing",
    )

    doc = (
        ROOT
        / "docs"
        / "p11"
        / "P11_15E_NARRATIVE_EXECUTION_FINGERPRINT_DELEGATION_ARCHITECTURE_BOUNDARY.md"
    ).read_text(encoding="utf-8")

    for marker in (
        "The safer successor is therefore one-consumer-at-a-time integration.",
        "P11.15F is limited to:",
        "tooling.narrative_execution",
        "`tooling.narrative_session` remains byte-frozen during F.",
        "F modifies exactly one existing production file:",
        "inspect_build_artifact_interchange",
        "BuildArtifactInterchange(",
        "verify_build_artifact_interchange_fingerprint(",
        "Build-artifact v3 remains rejected by narrative execution exactly as before.",
        "The return value is intentionally ignored.",
        "Error-order preservation",
        "Canonical-byte preservation",
        "Historical behavior preservation",
        "After F is frozen, P11.15G must audit `tooling.narrative_session` independently.",
        "Every successor remains architecture-first.",
    ):
        require(marker in doc, "P11.15E document omitted marker: " + marker)

    # E remains architecture-only.
    require(
        "verify_build_artifact_interchange_fingerprint" not in execution,
        "F production integration appeared during E",
    )

    print("P11_15D_FREEZE_ANCESTRY=PASS")
    print("P11_15E_ARCHITECTURE_ONLY=PASS")
    print("P11_15E_PRODUCTION_FILE_CHANGES=NONE")
    print("P11_15F_SCOPE=NARRATIVE_EXECUTION_ONLY")
    print("P11_15F_PRODUCTION_FILES=ONE_EXISTING_FILE")
    print("P11_15F_BUILD_ARTIFACT_INSPECTOR=FORBIDDEN")
    print("P11_15F_INTERCHANGE_CONSTRUCTION=AFTER_CONSUMER_SCHEMA_POLICY")
    print("P11_15F_CANONICAL_OUTER_POLICY=PRESERVE_BEFORE_DELEGATION")
    print("P11_15F_TOP_LEVEL_SHAPE_POLICY=PRESERVE")
    print("P11_15F_ACCEPTED_OUTER_SCHEMAS=V1_V2_ONLY")
    print("P11_15F_OUTER_V3=REMAINS_REJECTED")
    print("P11_15F_FINGERPRINT_DELEGATION=D_VERIFIER")
    print("P11_15F_D_RETURN_VALUE=IGNORED")
    print("P11_15F_ERROR_ORDERING=PRESERVE")
    print("P11_15F_ERROR_MESSAGES=PRESERVE")
    print("P11_15F_HISTORICAL_UNAVAILABLE_ROUTING=PRESERVE_AFTER_INTEGRITY")
    print("P11_15F_NARRATIVE_RECONSTRUCTION=PRESERVE_CONSUMER_OWNED")
    print("P11_15F_HASHLIB_IMPORT=REMOVE_IF_EXACT_LOCAL_USE")
    print("P11_15F_FINGERPRINT_ALGORITHM_IMPORT=REMOVE_IF_EXACT_LOCAL_USE")
    print("P11_15F_CANONICAL_JSON_IMPORT=RETAIN")
    print("P11_15F_NARRATIVE_SESSION_INTEGRATION=NONE")
    print("P11_15G_TARGET=NARRATIVE_SESSION_INDEPENDENT_AUDIT")
    print("P11_15E_NARRATIVE_EXECUTION_FINGERPRINT_DELEGATION_ARCHITECTURE_BOUNDARY=PASS")
    print("P11_15E_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())