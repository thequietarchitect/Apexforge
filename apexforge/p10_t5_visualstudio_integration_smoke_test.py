"""AFP-P10-T5.8 final Visual Studio integration smoke test."""
from __future__ import annotations

from pathlib import Path

from tooling.visualstudio_foundation import (
    CANONICAL_VISUAL_STUDIO_FOUNDATION_SHA256,
)
from tooling.visualstudio_extension import (
    CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256,
)
from tooling.visualstudio_syntax import (
    CANONICAL_VISUAL_STUDIO_SYNTAX_SHA256,
)
from tooling.visualstudio_editor import (
    CANONICAL_VISUAL_STUDIO_EDITOR_SHA256,
)
from tooling.visualstudio_bridge import (
    CANONICAL_VISUAL_STUDIO_BRIDGE_SHA256,
)
from tooling.visualstudio_diagnostics import (
    CANONICAL_VISUAL_STUDIO_DIAGNOSTICS_SHA256,
)
from tooling.visualstudio_intelligence import (
    CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256,
)
from tooling.visualstudio_commands import (
    CANONICAL_VISUAL_STUDIO_COMMANDS_SHA256,
)
from tooling.visualstudio_packaging import (
    CANONICAL_VISUAL_STUDIO_PACKAGING_SHA256,
)
from tooling.visualstudio_integration import (
    CANONICAL_VISUAL_STUDIO_INTEGRATION_SHA256,
    P10_T5_VISUAL_STUDIO_INTEGRATION_VERSION,
    VISUAL_STUDIO_INTEGRATION_KIND,
    VISUAL_STUDIO_INTEGRATION_SCHEMA,
    audit_visualstudio_integration_source,
    visual_studio_integration_contract,
    visual_studio_integration_fingerprint,
)

EXPECTED_PREDECESSORS = {
    "t5.1-foundation":
        "4c18e2840fa7ca7d74307f8ef71dc0510a84c0c6aa5b99619eb3a522ef4c3f54",
    "t5.1-extension":
        "06d8b8f428b033d5e522b4eaf842560fc7c5b4e953ebcf3338f7e1a87d6b363e",
    "t5.2-syntax":
        "a94182ea041461a46ed11281dbce09b4575e294ed9b5e1dff60a94b0a366987f",
    "t5.2-editor":
        "4aea8eff4f5c6e934be5220e4c880b6c7ac40722b0bea2caa037a141fa4c1b67",
    "t5.3-bridge":
        "443e19a53353e282130b0ada1c43812cf3a896977f64a9a5443133919c1b26c6",
    "t5.4-diagnostics":
        "54eff4034a801107463df9b9ccb8bfaa2e83e534b1e6f5ae80e21362f0a2271f",
    "t5.5-intelligence":
        "65f6ab0565276a59b1a71814acb0023da161a38661605b788e5f8b1e2753f82a",
    "t5.6-commands":
        "4a3dbadee01faee40b69098530d270164baf1a2a0411d68f83d1aa60f9a9d5ce",
    "t5.7-packaging":
        "44825d6431ffbce78bfc2f3c099bee34608518cb177b8196fd66c12df4bf0019",
}
EXPECTED_T5_8 = "bdb42496823c8e9fa10e196b1cc624817f48df02bcfa3ec7dab006cf7c6be026"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    extension_root = repo_root / "editors" / "visualstudio-apexforge"

    require(
        P10_T5_VISUAL_STUDIO_INTEGRATION_VERSION == "10-T5.8",
        "T5.8 version changed",
    )
    require(VISUAL_STUDIO_INTEGRATION_SCHEMA == 1, "T5.8 schema changed")
    require(
        VISUAL_STUDIO_INTEGRATION_KIND
        == "apexforge.visual-studio-final-integration",
        "T5.8 kind changed",
    )

    observed_predecessors = {
        "t5.1-foundation": CANONICAL_VISUAL_STUDIO_FOUNDATION_SHA256,
        "t5.1-extension": CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256,
        "t5.2-syntax": CANONICAL_VISUAL_STUDIO_SYNTAX_SHA256,
        "t5.2-editor": CANONICAL_VISUAL_STUDIO_EDITOR_SHA256,
        "t5.3-bridge": CANONICAL_VISUAL_STUDIO_BRIDGE_SHA256,
        "t5.4-diagnostics": CANONICAL_VISUAL_STUDIO_DIAGNOSTICS_SHA256,
        "t5.5-intelligence": CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256,
        "t5.6-commands": CANONICAL_VISUAL_STUDIO_COMMANDS_SHA256,
        "t5.7-packaging": CANONICAL_VISUAL_STUDIO_PACKAGING_SHA256,
    }
    require(
        observed_predecessors == EXPECTED_PREDECESSORS,
        "P10-T5 predecessor fingerprints changed",
    )
    require(
        visual_studio_integration_fingerprint() == EXPECTED_T5_8,
        "T5.8 integration fingerprint is not deterministic",
    )
    require(
        CANONICAL_VISUAL_STUDIO_INTEGRATION_SHA256 == EXPECTED_T5_8,
        "declared T5.8 integration fingerprint changed",
    )

    contract = visual_studio_integration_contract()
    require(contract["phase"] == "P10-T5", "T5 phase changed")
    require(contract["phase_status"] == "complete", "T5 completion flag changed")
    require(
        dict(contract["predecessor_sha256"]) == EXPECTED_PREDECESSORS,
        "T5.8 predecessor contract changed",
    )
    require(len(contract["source_audits"]) == 7, "source audit count changed")
    require(len(contract["vsix_audits"]) == 6, "VSIX audit count changed")
    require(
        len(contract["manual_acceptance_gates"]) == 7,
        "manual acceptance matrix changed",
    )
    require(
        contract["release_build_warnings_as_errors"] is True,
        "warnings-as-errors gate changed",
    )
    require(
        contract["full_regression_required"] is True,
        "full regression gate changed",
    )
    require(
        contract["runtime_feature_expansion"] is False,
        "T5.8 runtime boundary changed",
    )
    require(contract["t4_server_modified"] is False, "T4 boundary changed")
    require(
        tuple(contract["final_tags"])
        == ("afp-p10-t5.8-freeze", "afp-p10-t5-final-freeze"),
        "final tag contract changed",
    )

    audit = audit_visualstudio_integration_source(extension_root)
    require(audit.integration_sha256 == EXPECTED_T5_8, "source audit changed")
    require(
        dict(audit.predecessor_sha256) == EXPECTED_PREDECESSORS,
        "source predecessor audit changed",
    )
    require(len(audit.audited_components) == 7, "audited component count changed")

    print("AFP-P10-T5.8 final Visual Studio integration smoke test passed.")
    print("Frozen T5.1 through T5.7 contract composition: PASS")
    print("Final source integration audit: PASS")
    print("Release/VSIX/installed-copy gate contract: PASS")
    print("Live acceptance matrix contract: PASS")
    print("No runtime feature expansion: PASS")
    print("P10-T5 completion and final-tag contract: PASS")
    print(f"Final integration SHA-256: {EXPECTED_T5_8}")


if __name__ == "__main__":
    main()
