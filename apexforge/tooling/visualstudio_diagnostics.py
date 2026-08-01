"""AFP-P10-T5.4 Visual Studio diagnostics and document-sync auditor."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Final, Mapping, Optional, Sequence, Union

from language_server.diagnostics import CANONICAL_LSP_DIAGNOSTICS_SHA256
from language_server.integration import (
    CANONICAL_INTEGRATION_SHA256,
    integration_contract,
    verify_frozen_feature_hashes,
)
from tooling.visualstudio_bridge import (
    CANONICAL_VISUAL_STUDIO_BRIDGE_SHA256,
    VisualStudioBridgeError,
    audit_visualstudio_bridge,
    audit_visualstudio_bridge_vsix,
)

P10_T5_VISUAL_STUDIO_DIAGNOSTICS_VERSION: Final[str] = "10-T5.4"
VISUAL_STUDIO_DIAGNOSTICS_SCHEMA: Final[int] = 1
VISUAL_STUDIO_DIAGNOSTICS_KIND: Final[str] = "apexforge.visual-studio-diagnostics"
_STATUS_SHA256: Final[str] = "4c25920ac0ca5f846e35c3f8aeb86e8d1cdb664ed405d4a8d9eccf3ec41a9d16"
_GUIDE_SHA256: Final[str] = "65ca7dd79997f7753605765bda6bb2fabcb3cb5f8e2b081e936ef3d3bd59ac85"

class VisualStudioDiagnosticsError(ValueError):
    code: Final[str] = "APX-VS-004"
    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VisualStudioDiagnosticsError.message must be non-empty.")
        self.message = message
        super().__init__("[{}] {}".format(self.code, message))

@dataclass(frozen=True)
class VisualStudioDiagnosticsAudit:
    root: Path
    diagnostics_sha256: str
    status_sha256: str
    guide_sha256: str


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    except (OSError, UnicodeError) as error:
        raise VisualStudioDiagnosticsError("Could not read UTF-8 file {}: {}".format(path, error)) from error


def _sha256_text(path: Path) -> str:
    return hashlib.sha256(_read_text(path).encode("utf-8")).hexdigest()


def visual_studio_diagnostics_contract() -> Mapping[str, object]:
    return {
        "schema": VISUAL_STUDIO_DIAGNOSTICS_SCHEMA,
        "kind": VISUAL_STUDIO_DIAGNOSTICS_KIND,
        "diagnostics_version": P10_T5_VISUAL_STUDIO_DIAGNOSTICS_VERSION,
        "required_t5_3_bridge_sha256": CANONICAL_VISUAL_STUDIO_BRIDGE_SHA256,
        "required_t4_11_integration_sha256": CANONICAL_INTEGRATION_SHA256,
        "required_t4_2_diagnostics_sha256": CANONICAL_LSP_DIAGNOSTICS_SHA256,
        "transport": "Visual Studio ILanguageClient code-remote stdio",
        "document_sync": "full",
        "notifications": (
            "textDocument/didOpen",
            "textDocument/didChange",
            "textDocument/didClose",
            "textDocument/publishDiagnostics",
        ),
        "position_encoding": "utf-16",
        "diagnostic_lifecycle": "versioned replace plus close-time clear",
        "server_modified": False,
        "status_sha256": _STATUS_SHA256,
        "guide_sha256": _GUIDE_SHA256,
    }


def visual_studio_diagnostics_fingerprint() -> str:
    data = json.dumps(visual_studio_diagnostics_contract(), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

CANONICAL_VISUAL_STUDIO_DIAGNOSTICS_SHA256: Final[str] = "54eff4034a801107463df9b9ccb8bfaa2e83e534b1e6f5ae80e21362f0a2271f"


def audit_visualstudio_diagnostics(root: Union[Path, str]) -> VisualStudioDiagnosticsAudit:
    selected = Path(root).resolve()
    try:
        bridge = audit_visualstudio_bridge(selected)
    except VisualStudioBridgeError as error:
        raise VisualStudioDiagnosticsError(str(error)) from error
    if bridge.bridge_sha256 != CANONICAL_VISUAL_STUDIO_BRIDGE_SHA256:
        raise VisualStudioDiagnosticsError("Frozen T5.3 bridge fingerprint changed.")
    if not verify_frozen_feature_hashes():
        raise VisualStudioDiagnosticsError("A frozen T4 language-server feature fingerprint changed.")
    contract = integration_contract()
    if contract.get("position_encoding") != "utf-16":
        raise VisualStudioDiagnosticsError("T4.11 position encoding changed.")
    if contract.get("capabilities", {}).get("textDocumentSync") != {"openClose": True, "change": 1, "save": False}:
        raise VisualStudioDiagnosticsError("T4.11 full document-sync capability changed.")
    methods = set(contract.get("protocol_notifications", ()))
    for method in ("textDocument/didOpen", "textDocument/didChange", "textDocument/didClose"):
        if method not in methods:
            raise VisualStudioDiagnosticsError("T4.11 integration omitted {}.".format(method))
    status_path = selected / "src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs"
    guide_path = selected / "VISUAL_STUDIO_LANGUAGE_FEATURES.md"
    status_hash = _sha256_text(status_path)
    guide_hash = _sha256_text(guide_path)
    if status_hash != _STATUS_SHA256:
        raise VisualStudioDiagnosticsError("T5.4/T5.5 status source drifted: {}.".format(status_hash))
    if guide_hash != _GUIDE_SHA256:
        raise VisualStudioDiagnosticsError("Visual Studio language-feature guide drifted: {}.".format(guide_hash))
    status = _read_text(status_path)
    guide = _read_text(guide_path)
    for marker in (
        "Language-server bridge: active (AFP-P10-T5.3).",
        "Diagnostics/document sync: active (AFP-P10-T5.4).",
        "ApexForgeLanguageServerTrace.LogPath",
    ):
        if marker not in status:
            raise VisualStudioDiagnosticsError("ShowStatusCommand.cs omitted {!r}.".format(marker))
    for marker in ("textDocument/didOpen", "textDocument/didChange", "textDocument/didClose", "textDocument/publishDiagnostics"):
        if marker not in guide:
            raise VisualStudioDiagnosticsError("Language-feature guide omitted {!r}.".format(marker))
    observed = visual_studio_diagnostics_fingerprint()
    if observed != CANONICAL_VISUAL_STUDIO_DIAGNOSTICS_SHA256:
        raise VisualStudioDiagnosticsError("T5.4 diagnostics fingerprint changed: {}.".format(observed))
    return VisualStudioDiagnosticsAudit(selected, observed, status_hash, guide_hash)


def audit_visualstudio_diagnostics_vsix(path: Union[Path, str]):
    try:
        return audit_visualstudio_bridge_vsix(path)
    except VisualStudioBridgeError as error:
        raise VisualStudioDiagnosticsError(str(error)) from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", help="Visual Studio extension root")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-vsix", metavar="PATH")
    parser.add_argument("--contract", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.contract:
            print(CANONICAL_VISUAL_STUDIO_DIAGNOSTICS_SHA256); return 0
        if args.check_vsix:
            audit = audit_visualstudio_diagnostics_vsix(args.check_vsix)
            print("Visual Studio T5.4 VSIX audit passed: {}".format(audit.vsix_sha256)); return 0
        if args.check:
            if not args.root:
                raise VisualStudioDiagnosticsError("--check requires the Visual Studio extension root.")
            audit = audit_visualstudio_diagnostics(args.root)
            print("Visual Studio T5.4 diagnostics audit passed: {}".format(audit.diagnostics_sha256)); return 0
        _parser().print_help(); return 0
    except VisualStudioDiagnosticsError as error:
        print(str(error), file=sys.stderr); return 1

if __name__ == "__main__":
    raise SystemExit(main())
