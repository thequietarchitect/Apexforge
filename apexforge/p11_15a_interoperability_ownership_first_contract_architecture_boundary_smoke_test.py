"""P11.15A interoperability ownership / first-contract architecture boundary."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "93145f9927919c15e4df28d5cf8c9c5fcc0a903c"
PREDECESSOR_TAG = "afp-p11-14-freeze"
EXPECTED_BRANCH = (
    "p11-15a-interoperability-ownership-first-contract-architecture-boundary"
)

FROZEN_HASHES = {
    "apexforge/agents/__init__.py":
        "7EA62141AC47C0DC6B2B78952CA2EE29F0E03A7FF8B929C89C1FDEEE3CC23E3D",
    "apexforge/agents/model.py":
        "C602EE903A2E45008B6BB9181F77E3DC75E7060A44B64C2B3360A7E33C59928A",
    "apexforge/agents/catalog.py":
        "8BCF6363F5D9B8D3897A410112577F2F7A2DE57CE369E45E61246983D895F8B3",
    "apexforge/agents/resolution.py":
        "FB17DEDDCB2B215C520F1D9D0A28ADA6978CE04374171C0481230BB438316000",
    "apexforge/agents/character_binding.py":
        "635644E7D1D45E17738BF8A1EC076819BAE7A232B43A9891FBD1B7E4AAF88E58",
    "apexforge/agents/planning.py":
        "6E157C3EA2831E7D226C858C5018B3DF7533957B9F456D2933DD8A8F53EB226A",
    "apexforge/agents/plan_projection.py":
        "5313A46B833FE914F34C940704FB6E2E75D4F964F6DAD46E36A5AC7366C75163",
    "apexforge/agents/execution.py":
        "34572E70633600FFB417502B3D3D1B6AAE8D6704F9FE3C12B2CF4DA890818C4C",
    "apexforge/p11_14p_agent_operative_core_completion_architecture_boundary_smoke_test.py":
        "2CAB6BDF1E217DBDF42F4C806BF53AE3C208D1A25765B3DEFD6A3BC4A583369D",
    "docs/p11/P11_14P_AGENT_OPERATIVE_CORE_COMPLETION_ARCHITECTURE_BOUNDARY.md":
        "15457075D426EF76C5134F30ABA3317CFF93D546D3EBD00871D842BC541A5728",
    "apexforge/effects/host_execution.py":
        "AC9C7834861E83E91504F327B3102C3DB850A994B292049F2F777E32C4EE2A61",
    "apexforge/quad_vector/execution.py":
        "2733638F73AE89C91A7DED524E7787F9690C823D7C0F66052C2E1AAC36950CD0",
    "apexforge/tooling/build_artifact.py":
        "FBB3B49E85D549705AF5BD0ED0459063DCEAB4487A65E68BAF24E6DD6972B76B",
    "apexforge/tooling/cli.py":
        "F1A36F9FC043A6175E22830F49273D45856A4FB88F28F1C2FE2AFCDA9B74EDEC",
    "apexforge/rich_documents/projections.py":
        "743DCB144EC58F1BB0C2CE47B76F579E5E5C2B788633570441417D89CFB87C83",
    "apexforge/language_server/__init__.py":
        "98BC8774705538B9E4602B7DB1546F2FE6588CBB9DD368ED90C049F46624D0CA",
    "apexforge/runtime/state.py":
        "2B5EBA312E110E58DF7CCA75CD9A9F19683F5F70EEB864DF93CEDAAFB8F0DA11",
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


def main() -> int:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.14 freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14 freeze is not ancestor of P11.15A",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.15A branch changed")

    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))

    for path in (
        ROOT / "apexforge" / "interoperability.py",
        ROOT / "apexforge" / "interoperability",
        ROOT / "apexforge" / "interop.py",
        ROOT / "apexforge" / "interop",
        ROOT / "apexforge" / "ffi.py",
        ROOT / "apexforge" / "foreign.py",
        ROOT / "apexforge" / "bridge.py",
    ):
        require(not path.exists(), "{} unexpectedly exists".format(path))

    build_artifact = (
        ROOT / "apexforge" / "tooling" / "build_artifact.py"
    ).read_text(encoding="utf-8")

    for marker in (
        'BUILD_ARTIFACT_SCHEMA = "apexforge.build-artifact/v1"',
        'BUILD_ARTIFACT_SCHEMA_V2 = "apexforge.build-artifact/v2"',
        'BUILD_ARTIFACT_SCHEMA_V3 = "apexforge.build-artifact/v3"',
        "def canonical_json_bytes(",
        "def construct_build_artifact(",
        "def construct_narrative_build_artifact(",
        "def construct_rich_document_build_artifact(",
        "def write_build_artifact_atomic(",
    ):
        require(marker in build_artifact, "build-artifact owner changed: " + marker)

    host = (
        ROOT / "apexforge" / "effects" / "host_execution.py"
    ).read_text(encoding="utf-8")
    require(
        "def execute_host_effect(" in host and "handler(intent)" in host,
        "host-effect boundary changed",
    )

    qv = (
        ROOT / "apexforge" / "quad_vector" / "execution.py"
    ).read_text(encoding="utf-8")
    require(
        "implementations: Mapping[" in qv,
        "Quad-Vector explicit implementation-provider boundary changed",
    )
    require(
        "explicit implementation provider must be callable" in qv,
        "Quad-Vector provider-callable boundary changed",
    )

    narrative_execution = (
        ROOT / "apexforge" / "tooling" / "narrative_execution.py"
    ).read_text(encoding="utf-8")
    require(
        "build artifact shape or schema mismatch" in narrative_execution,
        "narrative specialized build-artifact read boundary changed",
    )

    narrative_session = (
        ROOT / "apexforge" / "tooling" / "narrative_session.py"
    ).read_text(encoding="utf-8")
    require(
        "build artifact schema mismatch" in narrative_session,
        "narrative-session specialized artifact read boundary changed",
    )

    air_serialization = (
        ROOT / "apexforge" / "air" / "serialization.py"
    ).read_text(encoding="utf-8")
    require(
        "def load_air_json(" in air_serialization,
        "AIR JSON load precedent changed",
    )

    doc = (
        ROOT
        / "docs"
        / "p11"
        / "P11_15A_INTEROPERABILITY_OWNERSHIP_FIRST_CONTRACT_ARCHITECTURE_BOUNDARY.md"
    ).read_text(encoding="utf-8")

    for marker in (
        "P11.15 begins as passive versioned data interchange.",
        "interoperability.build_artifact",
        "class BuildArtifactInterchange:",
        "def inspect_build_artifact_interchange(",
        "apexforge.build-artifact/v1",
        "apexforge.build-artifact/v2",
        "apexforge.build-artifact/v3",
        "B is a schema-inspection boundary, not a complete build-artifact validator.",
        "Explicitly deferred to P12 Native Backend",
        "Every successor remains architecture-first.",
    ):
        require(marker in doc, "P11.15A document omitted marker: " + marker)

    print("P11_14_PHASE_FREEZE_ANCESTRY=PASS")
    print("P11_15A_ARCHITECTURE_ONLY=PASS")
    print("P11_15A_PRODUCTION_FILE_CHANGES=NONE")
    print("P11_15_PRIMARY_MODE=PASSIVE_VERSIONED_DATA_INTERCHANGE")
    print("P11_15_GENERIC_FFI=NOT_JUSTIFIED")
    print("P11_15_NATIVE_ABI_LOWERING=P12_DEFERRED")
    print("P11_15_RPC_NETWORK=NOT_JUSTIFIED")
    print("P11_15_EDITOR_CLI_BRIDGES=REMAIN_TOOLING_OWNED")
    print("P11_15_HOST_EFFECT_BOUNDARY=REMAINS_EFFECTS_OWNED")
    print("P11_15_QUAD_VECTOR_PROVIDERS=REMAIN_QUAD_VECTOR_OWNED")
    print("P11_15_BUILD_ARTIFACT_WRITER=REMAINS_TOOLING_OWNED")
    print("P11_15_GENERIC_READ_SIDE_GAP=CONFIRMED")
    print("P11_15B_OWNER=interoperability.build_artifact")
    print("P11_15B_RECORD=BuildArtifactInterchange")
    print("P11_15B_FUNCTION=inspect_build_artifact_interchange")
    print("P11_15B_INPUT=EXACT_BYTES")
    print("P11_15B_SUPPORTED_SCHEMAS=BUILD_ARTIFACT_V1_V2_V3")
    print("P11_15B_RESULT=PRESERVE_SCHEMA_AND_EXACT_INPUT_BYTES")
    print("P11_15B_FULL_ARTIFACT_VALIDATION=DEFERRED")
    print("P11_15B_ARTIFACT_RECONSTRUCTION=NONE")
    print("P11_15B_IO_NETWORK_SUBPROCESS=NONE")
    print("P11_15A_INTEROPERABILITY_OWNERSHIP_FIRST_CONTRACT_ARCHITECTURE_BOUNDARY=PASS")
    print("P11_15A_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())