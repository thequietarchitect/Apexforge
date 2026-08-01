"""AFP-P10-T5.6 Visual Studio native editor-command smoke test."""
from __future__ import annotations

from pathlib import Path

from tooling.visualstudio_intelligence import (
    CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256,
)
from tooling.visualstudio_commands import (
    CANONICAL_VISUAL_STUDIO_COMMANDS_SHA256,
    P10_T5_VISUAL_STUDIO_COMMANDS_VERSION,
    VISUAL_STUDIO_COMMANDS_KIND,
    VISUAL_STUDIO_COMMANDS_SCHEMA,
    audit_visualstudio_commands,
    visual_studio_commands_contract,
    visual_studio_commands_fingerprint,
)

EXPECTED_T5_5 = "65f6ab0565276a59b1a71814acb0023da161a38661605b788e5f8b1e2753f82a"
EXPECTED_T5_6 = "4a3dbadee01faee40b69098530d270164baf1a2a0411d68f83d1aa60f9a9d5ce"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    extension_root = repo_root / "editors" / "visualstudio-apexforge"

    require(
        P10_T5_VISUAL_STUDIO_COMMANDS_VERSION == "10-T5.6",
        "T5.6 version changed",
    )
    require(VISUAL_STUDIO_COMMANDS_SCHEMA == 1, "T5.6 schema changed")
    require(
        VISUAL_STUDIO_COMMANDS_KIND
        == "apexforge.visual-studio-editor-commands",
        "T5.6 kind changed",
    )
    require(
        CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256 == EXPECTED_T5_5,
        "T5.5 predecessor fingerprint changed",
    )
    require(
        visual_studio_commands_fingerprint() == EXPECTED_T5_6,
        "T5.6 command fingerprint is not deterministic",
    )
    require(
        CANONICAL_VISUAL_STUDIO_COMMANDS_SHA256 == EXPECTED_T5_6,
        "declared T5.6 command fingerprint changed",
    )

    contract = visual_studio_commands_contract()
    require(contract["menu"] == "Tools", "T5.6 menu changed")
    require(len(contract["commands"]) == 3, "T5.6 command inventory changed")
    require(
        tuple(contract["restart_lifecycle"])
        == (
            "StopAsync",
            "terminate surviving process",
            "StartAsync",
            "ActivateAsync",
            "await OnServerInitializedAsync",
            "document resynchronization grace",
        ),
        "T5.6 restart lifecycle changed",
    )
    require(contract["restart_serialized"] is True, "restart serialization lost")
    require(
        contract["restart_initialization_timeout_seconds"] == 15,
        "restart initialization timeout changed",
    )
    require(
        contract["document_resynchronization_delay_milliseconds"] == 350,
        "document resynchronization delay changed",
    )
    require(
        contract["restart_success_requires_initialized_server"] is True,
        "restart readiness gate changed",
    )
    require(
        contract["native_format_document_preserved"] is True,
        "native Format Document gate changed",
    )
    require(contract["t4_server_modified"] is False, "T4 server boundary changed")

    audit = audit_visualstudio_commands(extension_root)
    require(audit.commands_sha256 == EXPECTED_T5_6, "T5.6 source audit changed")
    require(audit.command_count == 3, "T5.6 audited command count changed")
    require(len(audit.file_sha256) == 7, "T5.6 audited file inventory changed")

    print("AFP-P10-T5.6 Visual Studio native editor-command smoke test passed.")
    print("Frozen T5.5 language-intelligence prerequisite: PASS")
    print("Tools-menu command registration: PASS")
    print("Host-controlled StopAsync/StartAsync restart lifecycle: PASS")
    print("Initialized-server readiness and document resynchronization gate: PASS")
    print("Serialized restart and surviving-process cleanup: PASS")
    print("Stable language-server log command: PASS")
    print("Native whole-document formatting preservation: PASS")
    print("Deterministic T5.6 fingerprint: PASS")


if __name__ == "__main__":
    main()
