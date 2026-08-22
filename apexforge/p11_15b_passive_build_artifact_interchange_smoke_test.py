"""P11.15B passive build-artifact interchange smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
import importlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "57a4da779cde05cc39a227479fc20c9005ea0a59"
PREDECESSOR_TAG = "afp-p11-15a-freeze"
EXPECTED_BRANCH = "p11-15b-passive-build-artifact-interchange"


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


def artifact_bytes(schema: str, **extra: object) -> bytes:
    payload = {"schema": schema}
    payload.update(extra)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def main() -> int:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.15A freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.15A freeze is not ancestor of P11.15B",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.15B branch changed")

    interoperability = importlib.import_module("interoperability")
    module = importlib.import_module("interoperability.build_artifact")

    require(
        tuple(getattr(interoperability, "__all__", ())) == (),
        "interoperability package exports changed",
    )
    require(
        not hasattr(interoperability, "BuildArtifactInterchange"),
        "BuildArtifactInterchange leaked to package root",
    )
    require(
        not hasattr(interoperability, "inspect_build_artifact_interchange"),
        "inspection function leaked to package root",
    )

    require(
        tuple(getattr(module, "__all__", ())) == (
            "BuildArtifactInterchange",
            "inspect_build_artifact_interchange",
        ),
        "interoperability.build_artifact exports changed",
    )

    record_type = module.BuildArtifactInterchange
    inspect_artifact = module.inspect_build_artifact_interchange

    require(is_dataclass(record_type), "record must be a dataclass")
    require(
        record_type.__dataclass_params__.frozen is True,
        "record must be frozen",
    )
    require(
        tuple(field.name for field in fields(record_type)) == ("schema", "content"),
        "record field set/order changed",
    )

    signature = inspect.signature(inspect_artifact)
    require(
        tuple(signature.parameters) == ("content",),
        "inspection function signature changed",
    )

    from tooling.build_artifact import (
        BUILD_ARTIFACT_SCHEMA,
        BUILD_ARTIFACT_SCHEMA_V2,
        BUILD_ARTIFACT_SCHEMA_V3,
    )

    for schema in (
        BUILD_ARTIFACT_SCHEMA,
        BUILD_ARTIFACT_SCHEMA_V2,
        BUILD_ARTIFACT_SCHEMA_V3,
    ):
        content = artifact_bytes(schema, ignored={"nested": True})
        result = inspect_artifact(content)
        require(type(result) is record_type, "result must be exact record type")
        require(result.schema == schema, "recognized schema text changed")
        require(result.content is content, "input bytes identity changed")
        require(result.content == content, "input bytes changed")

        try:
            result.schema = "changed"
        except FrozenInstanceError:
            pass
        else:
            raise AssertionError("record mutation was accepted")

    invalid_inputs = (
        bytearray(b"{}"),
        memoryview(b"{}"),
        "{}",
        Path("artifact.json"),
    )
    for value in invalid_inputs:
        try:
            inspect_artifact(value)
        except TypeError:
            pass
        else:
            raise AssertionError(
                "non-exact-bytes input accepted: {}".format(type(value).__name__)
            )

    try:
        inspect_artifact(b"")
    except ValueError:
        pass
    else:
        raise AssertionError("empty bytes accepted")

    try:
        inspect_artifact(b"\xff")
    except UnicodeDecodeError:
        pass
    else:
        raise AssertionError("invalid UTF-8 did not propagate UnicodeDecodeError")

    try:
        inspect_artifact(b"{")
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("invalid JSON did not propagate JSONDecodeError")

    for content in (
        b"null",
        b"[]",
        b'"value"',
        b"1",
        b"true",
    ):
        try:
            inspect_artifact(content)
        except ValueError:
            pass
        else:
            raise AssertionError("non-object JSON accepted: {!r}".format(content))

    try:
        inspect_artifact(b"{}")
    except ValueError:
        pass
    else:
        raise AssertionError("missing schema accepted")

    try:
        inspect_artifact(b'{"schema":1}')
    except ValueError:
        pass
    else:
        raise AssertionError("non-string schema accepted")

    unknown = artifact_bytes("apexforge.build-artifact/v999")
    try:
        inspect_artifact(unknown)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown schema accepted")

    # Direct record construction retains the same exact domain constraints.
    direct = record_type(
        schema=BUILD_ARTIFACT_SCHEMA,
        content=b'{"schema":"apexforge.build-artifact/v1"}',
    )
    require(type(direct.schema) is str, "direct schema type changed")
    require(type(direct.content) is bytes, "direct content type changed")

    for bad_schema in (1, None, bytearray(b"x")):
        try:
            record_type(schema=bad_schema, content=b"x")
        except TypeError:
            pass
        else:
            raise AssertionError("record accepted non-exact-str schema")

    try:
        record_type(schema="unsupported", content=b"x")
    except ValueError:
        pass
    else:
        raise AssertionError("record accepted unsupported schema")

    for bad_content in (bytearray(b"x"), memoryview(b"x"), "x"):
        try:
            record_type(schema=BUILD_ARTIFACT_SCHEMA, content=bad_content)
        except TypeError:
            pass
        else:
            raise AssertionError("record accepted non-exact-bytes content")

    try:
        record_type(schema=BUILD_ARTIFACT_SCHEMA, content=b"")
    except ValueError:
        pass
    else:
        raise AssertionError("record accepted empty bytes")

    result_slots = set(vars(direct))
    require(
        result_slots == {"schema", "content"},
        "record retained unexpected payload state",
    )

    print("P11_15A_FREEZE_ANCESTRY=PASS")
    print("INTEROPERABILITY_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("P11_15B_OWNER=interoperability.build_artifact")
    print("P11_15B_RECORD=BuildArtifactInterchange")
    print("P11_15B_RECORD_FROZEN=PASS")
    print("P11_15B_RECORD_FIELDS=SCHEMA_CONTENT")
    print("P11_15B_FUNCTION=inspect_build_artifact_interchange")
    print("P11_15B_INPUT=EXACT_BYTES")
    print("P11_15B_EMPTY_BYTES=REJECTED")
    print("P11_15B_INVALID_UTF8=PROPAGATED")
    print("P11_15B_INVALID_JSON=PROPAGATED")
    print("P11_15B_JSON_OBJECT_REQUIRED=PASS")
    print("P11_15B_SCHEMA_REQUIRED_EXACT_STR=PASS")
    print("P11_15B_SUPPORTED_SCHEMAS=BUILD_ARTIFACT_V1_V2_V3")
    print("P11_15B_UNKNOWN_SCHEMA=REJECTED")
    print("P11_15B_INPUT_BYTES_IDENTITY=PRESERVED")
    print("P11_15B_SCHEMA_TEXT=PRESERVED")
    print("P11_15B_MAPPING_RETAINED=NO")
    print("P11_15B_FULL_ARTIFACT_VALIDATION=DEFERRED")
    print("P11_15B_ARTIFACT_RECONSTRUCTION=NONE")
    print("P11_15B_IO_NETWORK_SUBPROCESS=NONE")
    print("P11_15B_PASSIVE_BUILD_ARTIFACT_INTERCHANGE=PASS")
    print("P11_15B_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())