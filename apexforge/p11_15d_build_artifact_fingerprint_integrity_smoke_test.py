"""P11.15D build-artifact fingerprint-integrity smoke test."""

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import subprocess
import sys
from dataclasses import is_dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "79976fc542f62242d28e3e5a8cd3683bf380b3a2"
PREDECESSOR_TAG = "afp-p11-15c-freeze"
EXPECTED_BRANCH = "p11-15d-build-artifact-fingerprint-integrity"

FROZEN_HASHES = {
    "apexforge/interoperability/__init__.py":
        "6DA040DF8EC6727CD9449A37C5EC07C8F8DD1C98D3F25F824B29F23F2261CA7B",
    "apexforge/interoperability/build_artifact.py":
        "1C0E288FE4A9D4B620D715CC35554767062DA8296456B2612F7B9F25BCF9BBAD",
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


def sha256_file(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper()


def main() -> int:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.15C freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.15C freeze is not ancestor of P11.15D",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.15D branch changed")

    for relative, expected in FROZEN_HASHES.items():
        require(sha256_file(relative) == expected, "{} changed".format(relative))

    package = importlib.import_module("interoperability")
    require(
        tuple(getattr(package, "__all__", ())) == (),
        "interoperability package exports changed",
    )

    module = importlib.import_module("interoperability.build_artifact_integrity")

    require(
        tuple(getattr(module, "__all__", ())) == (
            "verify_build_artifact_interchange_fingerprint",
        ),
        "D module exports changed",
    )

    verify = module.verify_build_artifact_interchange_fingerprint
    signature = inspect.signature(verify)
    require(
        tuple(signature.parameters) == ("interchange",),
        "D function signature changed",
    )

    # D introduces no dataclass/result record.
    local_dataclasses = [
        value
        for name, value in vars(module).items()
        if not name.startswith("_")
        and isinstance(value, type)
        and getattr(value, "__module__", None) == module.__name__
        and is_dataclass(value)
    ]
    require(local_dataclasses == [], "D introduced an unjustified result dataclass")

    from interoperability.build_artifact import (
        BuildArtifactInterchange,
        inspect_build_artifact_interchange,
    )
    from tooling.build_artifact import (
        BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
        BUILD_ARTIFACT_SCHEMA,
        BUILD_ARTIFACT_SCHEMA_V2,
        BUILD_ARTIFACT_SCHEMA_V3,
        canonical_json_bytes,
    )

    def artifact_content(schema: str, *, pretty: bool = False) -> tuple[bytes, str]:
        payload = {
            "schema": schema,
            "arbitrary": {"nested": [1, 2, 3]},
        }
        fingerprint = hashlib.sha256(
            canonical_json_bytes(payload)
        ).hexdigest()
        artifact = dict(payload)
        artifact["fingerprint"] = {
            "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
            "value": fingerprint,
        }
        if pretty:
            return (
                json.dumps(
                    artifact,
                    indent=2,
                    sort_keys=False,
                ).encode("utf-8"),
                fingerprint,
            )
        return canonical_json_bytes(artifact), fingerprint

    for schema in (
        BUILD_ARTIFACT_SCHEMA,
        BUILD_ARTIFACT_SCHEMA_V2,
        BUILD_ARTIFACT_SCHEMA_V3,
    ):
        content, fingerprint = artifact_content(schema)
        interchange = inspect_build_artifact_interchange(content)
        returned = verify(interchange)
        require(returned == fingerprint, "verified fingerprint changed")
        require(returned is not None, "D returned no fingerprint")
        require(interchange.content is content, "D replaced interchange bytes")
        require(interchange.schema == schema, "D mutated interchange schema")

    # Non-canonical outer bytes are allowed if canonical payload integrity is valid.
    pretty_content, pretty_fingerprint = artifact_content(
        BUILD_ARTIFACT_SCHEMA_V3,
        pretty=True,
    )
    pretty_interchange = inspect_build_artifact_interchange(pretty_content)
    require(
        pretty_content != canonical_json_bytes(json.loads(pretty_content.decode("utf-8"))),
        "non-canonical fixture unexpectedly canonical",
    )
    require(
        verify(pretty_interchange) == pretty_fingerprint,
        "D incorrectly requires canonical outer bytes",
    )

    # Exact input type only.
    class Derived(BuildArtifactInterchange):
        pass

    derived_content, _ = artifact_content(BUILD_ARTIFACT_SCHEMA)
    derived = Derived(
        schema=BUILD_ARTIFACT_SCHEMA,
        content=derived_content,
    )
    try:
        verify(derived)
    except TypeError:
        pass
    else:
        raise AssertionError("D accepted BuildArtifactInterchange subclass")

    for value in (
        b"{}",
        {},
        Path("artifact.json"),
        object(),
    ):
        try:
            verify(value)
        except TypeError:
            pass
        else:
            raise AssertionError(
                "D accepted wrong input type: {}".format(type(value).__name__)
            )

    # Directly constructed B records can carry invalid bytes; D rechecks them.
    try:
        verify(
            BuildArtifactInterchange(
                schema=BUILD_ARTIFACT_SCHEMA,
                content=b"\xff",
            )
        )
    except UnicodeDecodeError:
        pass
    else:
        raise AssertionError("invalid UTF-8 did not propagate")

    try:
        verify(
            BuildArtifactInterchange(
                schema=BUILD_ARTIFACT_SCHEMA,
                content=b"{",
            )
        )
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("invalid JSON did not propagate")

    try:
        verify(
            BuildArtifactInterchange(
                schema=BUILD_ARTIFACT_SCHEMA,
                content=b"[]",
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError("non-object JSON accepted")

    mismatch_content, _ = artifact_content(BUILD_ARTIFACT_SCHEMA_V2)
    mismatch = BuildArtifactInterchange(
        schema=BUILD_ARTIFACT_SCHEMA,
        content=mismatch_content,
    )
    try:
        verify(mismatch)
    except ValueError:
        pass
    else:
        raise AssertionError("schema/content mismatch accepted")

    def encoded(artifact: object) -> bytes:
        return json.dumps(
            artifact,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def direct(artifact: dict[str, object]) -> BuildArtifactInterchange:
        return BuildArtifactInterchange(
            schema=BUILD_ARTIFACT_SCHEMA,
            content=encoded(artifact),
        )

    base = {"schema": BUILD_ARTIFACT_SCHEMA, "arbitrary": 1}

    # Missing fingerprint.
    try:
        verify(direct(dict(base)))
    except ValueError:
        pass
    else:
        raise AssertionError("missing fingerprint accepted")

    # Wrong fingerprint value container type.
    wrong_type = dict(base)
    wrong_type["fingerprint"] = ["sha256", "x"]
    try:
        verify(direct(wrong_type))
    except ValueError:
        pass
    else:
        raise AssertionError("non-dict fingerprint accepted")

    # Missing/extra exact keys.
    for fingerprint in (
        {"algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM},
        {"value": "x"},
        {
            "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
            "value": "x",
            "extra": 1,
        },
    ):
        artifact = dict(base)
        artifact["fingerprint"] = fingerprint
        try:
            verify(direct(artifact))
        except ValueError:
            pass
        else:
            raise AssertionError("invalid fingerprint key set accepted")

    # Wrong algorithm.
    artifact = dict(base)
    artifact["fingerprint"] = {"algorithm": "sha512", "value": "x"}
    try:
        verify(direct(artifact))
    except ValueError:
        pass
    else:
        raise AssertionError("wrong fingerprint algorithm accepted")

    # Non-string fingerprint value.
    artifact = dict(base)
    artifact["fingerprint"] = {
        "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
        "value": 1,
    }
    try:
        verify(direct(artifact))
    except ValueError:
        pass
    else:
        raise AssertionError("non-string fingerprint value accepted")

    # Well-shaped but mismatched hash.
    artifact = dict(base)
    artifact["fingerprint"] = {
        "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
        "value": "0" * 64,
    }
    try:
        verify(direct(artifact))
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched fingerprint accepted")

    print("P11_15C_FREEZE_ANCESTRY=PASS")
    print("P11_15B_FILES_BYTE_IDENTICAL=PASS")
    print("P11_15C_EXISTING_CONSUMERS_BYTE_IDENTICAL=PASS")
    print("INTEROPERABILITY_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("P11_15D_OWNER=interoperability.build_artifact_integrity")
    print("P11_15D_PUBLIC_SURFACE=ONE_FUNCTION")
    print("P11_15D_RESULT_RECORD=NONE")
    print("P11_15D_FUNCTION=verify_build_artifact_interchange_fingerprint")
    print("P11_15D_INPUT=EXACT_BUILD_ARTIFACT_INTERCHANGE")
    print("P11_15D_SCHEMAS=V1_V2_V3_THROUGH_FROZEN_B")
    print("P11_15D_SCHEMA_CONTENT_CONSISTENCY=PASS")
    print("P11_15D_FINGERPRINT_KEYS=ALGORITHM_VALUE_EXACT")
    print("P11_15D_FINGERPRINT_ALGORITHM=REUSED")
    print("P11_15D_HASH_RULE=SHA256_CANONICAL_PAYLOAD_WITHOUT_FINGERPRINT")
    print("P11_15D_RETURN=DECLARED_VERIFIED_FINGERPRINT_STR")
    print("P11_15D_CANONICAL_OUTER_BYTES=NOT_REQUIRED")
    print("P11_15D_FULL_ARTIFACT_VALIDATION=DEFERRED")
    print("P11_15D_ARTIFACT_RECONSTRUCTION=NONE")
    print("P11_15D_IO_NETWORK_SUBPROCESS=NONE")
    print("P11_15D_CONSUMER_INTEGRATION=NONE")
    print("P11_15D_FFI_NATIVE_ABI_RPC=DEFERRED")
    print("P11_15D_BUILD_ARTIFACT_FINGERPRINT_INTEGRITY=PASS")
    print("P11_15D_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())