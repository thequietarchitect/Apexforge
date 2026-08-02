"""AFP-P10-T5.8 final Visual Studio integration and freeze auditor."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Final, Mapping, Optional, Sequence, Union
import zipfile

from tooling.visualstudio_foundation import (
    CANONICAL_VISUAL_STUDIO_FOUNDATION_SHA256,
    visual_studio_foundation_fingerprint,
)
from tooling.visualstudio_extension import (
    CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256,
    VisualStudioExtensionError,
    audit_visualstudio_extension,
    audit_visualstudio_vsix,
)
from tooling.visualstudio_syntax import (
    CANONICAL_VISUAL_STUDIO_SYNTAX_SHA256,
    visual_studio_syntax_fingerprint,
)
from tooling.visualstudio_editor import (
    CANONICAL_VISUAL_STUDIO_EDITOR_SHA256,
    VisualStudioEditorError,
    audit_visualstudio_editor,
)
from tooling.visualstudio_bridge import (
    CANONICAL_VISUAL_STUDIO_BRIDGE_SHA256,
    VisualStudioBridgeError,
    audit_visualstudio_bridge,
    audit_visualstudio_bridge_vsix,
)
from tooling.visualstudio_diagnostics import (
    CANONICAL_VISUAL_STUDIO_DIAGNOSTICS_SHA256,
    VisualStudioDiagnosticsError,
    audit_visualstudio_diagnostics,
    audit_visualstudio_diagnostics_vsix,
)
from tooling.visualstudio_intelligence import (
    CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256,
    VisualStudioIntelligenceError,
    audit_visualstudio_intelligence,
    audit_visualstudio_intelligence_vsix,
)
from tooling.visualstudio_commands import (
    CANONICAL_VISUAL_STUDIO_COMMANDS_SHA256,
    VisualStudioCommandsError,
    audit_visualstudio_commands,
    audit_visualstudio_commands_vsix,
)
from tooling.visualstudio_packaging import (
    CANONICAL_VISUAL_STUDIO_PACKAGING_SHA256,
    VisualStudioInstalledAudit,
    VisualStudioPackagingError,
    audit_visualstudio_installed_copy,
    audit_visualstudio_packaging_source,
    audit_visualstudio_vsix_hardening,
)

P10_T5_VISUAL_STUDIO_INTEGRATION_VERSION: Final[str] = "10-T5.8"
VISUAL_STUDIO_INTEGRATION_SCHEMA: Final[int] = 1
VISUAL_STUDIO_INTEGRATION_KIND: Final[str] = (
    "apexforge.visual-studio-final-integration"
)

_EXPECTED_PREDECESSORS: Final[Mapping[str, str]] = {
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

_SOURCE_AUDITS: Final[tuple[str, ...]] = (
    "visualstudio_extension",
    "visualstudio_editor",
    "visualstudio_bridge",
    "visualstudio_diagnostics",
    "visualstudio_intelligence",
    "visualstudio_commands",
    "visualstudio_packaging",
)

_VSIX_AUDITS: Final[tuple[str, ...]] = (
    "visualstudio_extension",
    "visualstudio_bridge",
    "visualstudio_diagnostics",
    "visualstudio_intelligence",
    "visualstudio_commands",
    "visualstudio_packaging",
)

_MANUAL_ACCEPTANCE_GATES: Final[tuple[str, ...]] = (
    "syntax-highlighting",
    "live-diagnostics-and-document-sync",
    "outline-hover-completion",
    "definition-references-safe-same-document-rename",
    "whole-document-formatting",
    "status-restart-log-commands",
    "post-restart-feature-preservation",
)

_REQUIRED_DOCUMENT: Final[str] = "VISUAL_STUDIO_INTEGRATION.md"


class VisualStudioIntegrationError(ValueError):
    """Raised when the final P10-T5 Visual Studio integration drifts."""

    code: Final[str] = "APX-VS-INT-001"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError(
                "VisualStudioIntegrationError.message must be non-empty."
            )
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VisualStudioIntegrationSourceAudit:
    root: Path
    integration_sha256: str
    predecessor_sha256: Mapping[str, str]
    audited_components: tuple[str, ...]


@dataclass(frozen=True)
class VisualStudioIntegrationVsixAudit:
    path: Path
    integration_sha256: str
    vsix_sha256: str
    normalized_payload_sha256: str
    assembly_sha256: str
    audited_components: tuple[str, ...]


@dataclass(frozen=True)
class VisualStudioIntegrationInstalledAudit:
    profile_root: Path
    extension_root: Path
    manifest_path: Path
    assembly_path: Path
    assembly_sha256: str
    integration_sha256: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _read_utf8(path: Path, owner: str) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise VisualStudioIntegrationError(
            f"Could not read UTF-8 {owner} at {path}: {error}."
        ) from error


def _observed_predecessors() -> Mapping[str, str]:
    return {
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


def visual_studio_integration_contract() -> Mapping[str, object]:
    return {
        "schema": VISUAL_STUDIO_INTEGRATION_SCHEMA,
        "kind": VISUAL_STUDIO_INTEGRATION_KIND,
        "integration_version": P10_T5_VISUAL_STUDIO_INTEGRATION_VERSION,
        "phase": "P10-T5",
        "phase_status": "complete",
        "predecessor_sha256": dict(_EXPECTED_PREDECESSORS),
        "source_audits": _SOURCE_AUDITS,
        "vsix_audits": _VSIX_AUDITS,
        "installed_copy_policy": (
            "exactly-one-installed-manifest",
            "built-installed-assembly-sha256-equality",
            "same-final-integration-contract",
        ),
        "manual_acceptance_gates": _MANUAL_ACCEPTANCE_GATES,
        "release_build_warnings_as_errors": True,
        "full_regression_required": True,
        "runtime_feature_expansion": False,
        "t4_server_modified": False,
        "final_tags": (
            "afp-p10-t5.8-freeze",
            "afp-p10-t5-final-freeze",
        ),
        "documentation": _REQUIRED_DOCUMENT,
    }


def visual_studio_integration_fingerprint() -> str:
    return _sha256(_canonical_json(visual_studio_integration_contract()))


# Filled from the canonical contract above. Do not revise without a new phase.
CANONICAL_VISUAL_STUDIO_INTEGRATION_SHA256: Final[str] = "bdb42496823c8e9fa10e196b1cc624817f48df02bcfa3ec7dab006cf7c6be026"


def _require_predecessors() -> Mapping[str, str]:
    observed = _observed_predecessors()
    if observed != _EXPECTED_PREDECESSORS:
        changed = tuple(
            key
            for key in _EXPECTED_PREDECESSORS
            if observed.get(key) != _EXPECTED_PREDECESSORS[key]
        )
        raise VisualStudioIntegrationError(
            "Frozen P10-T5 predecessor fingerprints changed: "
            + repr(changed)
            + "."
        )
    if visual_studio_foundation_fingerprint() != _EXPECTED_PREDECESSORS[
        "t5.1-foundation"
    ]:
        raise VisualStudioIntegrationError(
            "T5.1 foundation payload no longer matches its declared fingerprint."
        )
    if visual_studio_syntax_fingerprint() != _EXPECTED_PREDECESSORS[
        "t5.2-syntax"
    ]:
        raise VisualStudioIntegrationError(
            "T5.2 syntax payload no longer matches its declared fingerprint."
        )
    return observed


def _require_final_fingerprint() -> str:
    observed = visual_studio_integration_fingerprint()
    if observed != CANONICAL_VISUAL_STUDIO_INTEGRATION_SHA256:
        raise VisualStudioIntegrationError(
            "Final P10-T5 Visual Studio integration fingerprint changed: "
            f"{observed}."
        )
    return observed


def audit_visualstudio_integration_source(
    root: Union[Path, str],
) -> VisualStudioIntegrationSourceAudit:
    selected = Path(root).resolve()
    if not selected.is_dir():
        raise VisualStudioIntegrationError(
            f"Visual Studio extension root does not exist: {selected}."
        )

    predecessor_sha256 = _require_predecessors()
    integration_sha256 = _require_final_fingerprint()

    try:
        audit_visualstudio_extension(selected)
        audit_visualstudio_editor(selected)
        audit_visualstudio_bridge(selected)
        audit_visualstudio_diagnostics(selected)
        audit_visualstudio_intelligence(selected)
        audit_visualstudio_commands(selected)
        audit_visualstudio_packaging_source(selected)
    except (
        VisualStudioExtensionError,
        VisualStudioEditorError,
        VisualStudioBridgeError,
        VisualStudioDiagnosticsError,
        VisualStudioIntelligenceError,
        VisualStudioCommandsError,
        VisualStudioPackagingError,
    ) as error:
        raise VisualStudioIntegrationError(str(error)) from error

    document = selected / _REQUIRED_DOCUMENT
    if not document.is_file():
        raise VisualStudioIntegrationError(
            f"Final integration document is missing: {_REQUIRED_DOCUMENT}."
        )
    documentation = _read_utf8(document, "T5.8 integration documentation")
    for marker in (
        "AFP-P10-T5.8",
        "P10-T5 complete",
        "no runtime feature expansion",
        "built/installed assembly SHA-256 equality",
        "afp-p10-t5-final-freeze",
    ):
        if marker not in documentation:
            raise VisualStudioIntegrationError(
                f"{_REQUIRED_DOCUMENT} omitted marker {marker!r}."
            )

    return VisualStudioIntegrationSourceAudit(
        root=selected,
        integration_sha256=integration_sha256,
        predecessor_sha256=dict(predecessor_sha256),
        audited_components=_SOURCE_AUDITS,
    )


def _normalized_payload_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with zipfile.ZipFile(path, "r") as archive:
            entries = sorted(
                (
                    PurePosixPath(info.filename.replace("\\", "/")).as_posix(),
                    info,
                )
                for info in archive.infolist()
                if not info.is_dir()
            )
            for normalized, info in entries:
                data = archive.read(info)
                digest.update(normalized.encode("utf-8"))
                digest.update(b"\0")
                digest.update(hashlib.sha256(data).digest())
                digest.update(b"\0")
    except (OSError, zipfile.BadZipFile, KeyError, RuntimeError) as error:
        raise VisualStudioIntegrationError(
            f"Could not compute normalized VSIX payload fingerprint: {error}."
        ) from error
    return digest.hexdigest()


def audit_visualstudio_integration_vsix(
    path: Union[Path, str],
) -> VisualStudioIntegrationVsixAudit:
    selected = Path(path).resolve()
    if not selected.is_file():
        raise VisualStudioIntegrationError(f"VSIX does not exist: {selected}.")

    _require_predecessors()
    integration_sha256 = _require_final_fingerprint()

    try:
        extension = audit_visualstudio_vsix(selected)
        bridge = audit_visualstudio_bridge_vsix(selected)
        diagnostics = audit_visualstudio_diagnostics_vsix(selected)
        intelligence = audit_visualstudio_intelligence_vsix(selected)
        commands = audit_visualstudio_commands_vsix(selected)
        packaging = audit_visualstudio_vsix_hardening(selected)
    except (
        VisualStudioExtensionError,
        VisualStudioBridgeError,
        VisualStudioDiagnosticsError,
        VisualStudioIntelligenceError,
        VisualStudioCommandsError,
        VisualStudioPackagingError,
    ) as error:
        raise VisualStudioIntegrationError(str(error)) from error

    observed_hashes = {
        extension.vsix_sha256,
        bridge.vsix_sha256,
        diagnostics.vsix_sha256,
        intelligence.vsix_sha256,
        commands.vsix_sha256,
        packaging.vsix_sha256,
    }
    if len(observed_hashes) != 1:
        raise VisualStudioIntegrationError(
            "P10-T5 VSIX auditors disagreed on the built archive SHA-256."
        )

    return VisualStudioIntegrationVsixAudit(
        path=selected,
        integration_sha256=integration_sha256,
        vsix_sha256=packaging.vsix_sha256,
        normalized_payload_sha256=_normalized_payload_sha256(selected),
        assembly_sha256=packaging.assembly_sha256,
        audited_components=_VSIX_AUDITS,
    )


def audit_visualstudio_integration_installed(
    vsix_path: Union[Path, str],
    profile_root: Union[Path, str],
) -> VisualStudioIntegrationInstalledAudit:
    built = audit_visualstudio_integration_vsix(vsix_path)
    try:
        installed: VisualStudioInstalledAudit = audit_visualstudio_installed_copy(
            vsix_path,
            profile_root,
        )
    except VisualStudioPackagingError as error:
        raise VisualStudioIntegrationError(str(error)) from error

    if installed.assembly_sha256 != built.assembly_sha256:
        raise VisualStudioIntegrationError(
            "Final installed assembly does not match the integrated built VSIX."
        )

    return VisualStudioIntegrationInstalledAudit(
        profile_root=installed.profile_root,
        extension_root=installed.extension_root,
        manifest_path=installed.manifest_path,
        assembly_path=installed.assembly_path,
        assembly_sha256=installed.assembly_sha256,
        integration_sha256=built.integration_sha256,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="apexforge-visualstudio-integration",
        description=(
            "Audit AFP-P10-T5.8 final Visual Studio source, VSIX, and "
            "Experimental Instance integration."
        ),
    )
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--contract", action="store_true")
    modes.add_argument("--check-source", metavar="ROOT")
    modes.add_argument("--check-vsix", metavar="PATH")
    modes.add_argument("--check-installed", metavar="VSIX")
    parser.add_argument(
        "--profile-root",
        help="Visual Studio profile root required with --check-installed",
    )
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    try:
        if arguments.contract:
            print(visual_studio_integration_fingerprint())
            return 0
        if arguments.check_source:
            audit = audit_visualstudio_integration_source(
                arguments.check_source
            )
            print(
                "AFP-P10-T5.8 final source integration audit passed: "
                f"{audit.root}"
            )
            print(f"Integration contract SHA-256: {audit.integration_sha256}")
            print(f"Audited components: {len(audit.audited_components)}")
            return 0
        if arguments.check_vsix:
            audit = audit_visualstudio_integration_vsix(arguments.check_vsix)
            print(
                "AFP-P10-T5.8 final VSIX integration audit passed: "
                f"{audit.path}"
            )
            print(f"VSIX SHA-256: {audit.vsix_sha256}")
            print(
                "Normalized payload SHA-256: "
                f"{audit.normalized_payload_sha256}"
            )
            print(f"Assembly SHA-256: {audit.assembly_sha256}")
            return 0
        if arguments.check_installed:
            if not arguments.profile_root:
                parser.error(
                    "--profile-root is required with --check-installed"
                )
            audit = audit_visualstudio_integration_installed(
                arguments.check_installed,
                arguments.profile_root,
            )
            print(
                "AFP-P10-T5.8 final installed integration audit passed: "
                f"{audit.extension_root}"
            )
            print(f"Installed assembly SHA-256: {audit.assembly_sha256}")
            print(f"Integration contract SHA-256: {audit.integration_sha256}")
            return 0
        raise AssertionError("unreachable CLI mode")
    except VisualStudioIntegrationError as error:
        print(str(error), file=sys.stderr)
        return 1


__all__ = (
    "CANONICAL_VISUAL_STUDIO_INTEGRATION_SHA256",
    "P10_T5_VISUAL_STUDIO_INTEGRATION_VERSION",
    "VISUAL_STUDIO_INTEGRATION_KIND",
    "VISUAL_STUDIO_INTEGRATION_SCHEMA",
    "VisualStudioIntegrationError",
    "VisualStudioIntegrationInstalledAudit",
    "VisualStudioIntegrationSourceAudit",
    "VisualStudioIntegrationVsixAudit",
    "audit_visualstudio_integration_installed",
    "audit_visualstudio_integration_source",
    "audit_visualstudio_integration_vsix",
    "main",
    "visual_studio_integration_contract",
    "visual_studio_integration_fingerprint",
)


if __name__ == "__main__":
    raise SystemExit(main())
