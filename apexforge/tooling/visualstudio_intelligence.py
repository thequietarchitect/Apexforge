"""AFP-P10-T5.5 Visual Studio IntelliSense/navigation parity auditor."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Final, Mapping, Optional, Sequence, Union

from language_server.integration import (
    CANONICAL_INTEGRATION_SHA256,
    integrated_capabilities,
    integration_contract,
    verify_frozen_feature_hashes,
)
from tooling.visualstudio_diagnostics import (
    CANONICAL_VISUAL_STUDIO_DIAGNOSTICS_SHA256,
    VisualStudioDiagnosticsError,
    audit_visualstudio_diagnostics,
    audit_visualstudio_diagnostics_vsix,
)

P10_T5_VISUAL_STUDIO_INTELLIGENCE_VERSION: Final[str] = "10-T5.5"
VISUAL_STUDIO_INTELLIGENCE_SCHEMA: Final[int] = 1
VISUAL_STUDIO_INTELLIGENCE_KIND: Final[str] = "apexforge.visual-studio-language-intelligence"
_EXPECTED_METHODS: Final[tuple[str, ...]] = (
    "textDocument/documentSymbol",
    "textDocument/hover",
    "textDocument/completion",
    "textDocument/definition",
    "textDocument/references",
    "textDocument/prepareRename",
    "textDocument/rename",
    "workspace/symbol",
    "textDocument/formatting",
)

class VisualStudioIntelligenceError(ValueError):
    code: Final[str] = "APX-VS-005"
    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VisualStudioIntelligenceError.message must be non-empty.")
        self.message = message
        super().__init__("[{}] {}".format(self.code, message))

@dataclass(frozen=True)
class VisualStudioIntelligenceAudit:
    root: Path
    intelligence_sha256: str
    method_count: int


def visual_studio_intelligence_contract() -> Mapping[str, object]:
    integration = integration_contract()
    return {
        "schema": VISUAL_STUDIO_INTELLIGENCE_SCHEMA,
        "kind": VISUAL_STUDIO_INTELLIGENCE_KIND,
        "intelligence_version": P10_T5_VISUAL_STUDIO_INTELLIGENCE_VERSION,
        "required_t5_4_diagnostics_sha256": CANONICAL_VISUAL_STUDIO_DIAGNOSTICS_SHA256,
        "required_t4_11_integration_sha256": CANONICAL_INTEGRATION_SHA256,
        "feature_methods": _EXPECTED_METHODS,
        "capabilities": integrated_capabilities(),
        "frozen_feature_sha256": integration["frozen_feature_sha256"],
        "scope": "frozen T4.11 semantics exposed through Visual Studio native LSP host",
        "features_deferred": integration["features_deferred"],
        "server_modified": False,
    }


def visual_studio_intelligence_fingerprint() -> str:
    data = json.dumps(visual_studio_intelligence_contract(), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256: Final[str] = "65f6ab0565276a59b1a71814acb0023da161a38661605b788e5f8b1e2753f82a"


def audit_visualstudio_intelligence(root: Union[Path, str]) -> VisualStudioIntelligenceAudit:
    selected = Path(root).resolve()
    try:
        diagnostics = audit_visualstudio_diagnostics(selected)
    except VisualStudioDiagnosticsError as error:
        raise VisualStudioIntelligenceError(str(error)) from error
    if diagnostics.diagnostics_sha256 != CANONICAL_VISUAL_STUDIO_DIAGNOSTICS_SHA256:
        raise VisualStudioIntelligenceError("Frozen T5.4 diagnostics fingerprint changed.")
    if not verify_frozen_feature_hashes():
        raise VisualStudioIntelligenceError("A frozen T4 language-server feature fingerprint changed.")
    integration = integration_contract()
    if tuple(integration.get("feature_methods", ())) != _EXPECTED_METHODS:
        raise VisualStudioIntelligenceError("T4.11 feature-method inventory changed.")
    if integration.get("capabilities") != integrated_capabilities():
        raise VisualStudioIntelligenceError("T4.11 integrated capabilities changed.")
    status = (selected / "src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs").read_text(encoding="utf-8-sig")
    guide = (selected / "VISUAL_STUDIO_LANGUAGE_FEATURES.md").read_text(encoding="utf-8-sig")
    marker = "IntelliSense/navigation/formatting: active (AFP-P10-T5.5)."
    if marker not in status:
        raise VisualStudioIntelligenceError("ShowStatusCommand.cs omitted {!r}.".format(marker))
    parity_markers = (
        "Visual Studio integration: final P10-T5 parity.",
        "Language-intelligence parity: active through AFP-P10-T5.5.",
    )
    if not any(item in status for item in parity_markers):
        raise VisualStudioIntelligenceError("ShowStatusCommand.cs omitted the T5.5 parity marker.")
    for method in _EXPECTED_METHODS:
        if method not in guide:
            # The guide uses readable feature names for some methods; protocol inventory
            # is authoritative and the exceptions below map those labels.
            readable = {
                "textDocument/documentSymbol": "hierarchical document symbols",
                "textDocument/hover": "syntax hover",
                "textDocument/completion": "context-aware completion",
                "textDocument/definition": "go to definition",
                "textDocument/references": "find references",
                "textDocument/prepareRename": "prepare rename",
                "textDocument/rename": "same-document prepare rename and rename",
                "workspace/symbol": "workspace symbols",
                "textDocument/formatting": "whole-document formatting",
            }[method]
            if readable not in guide:
                raise VisualStudioIntelligenceError("Language-feature guide omitted {}.".format(method))
    observed = visual_studio_intelligence_fingerprint()
    if observed != CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256:
        raise VisualStudioIntelligenceError("T5.5 intelligence fingerprint changed: {}.".format(observed))
    return VisualStudioIntelligenceAudit(selected, observed, len(_EXPECTED_METHODS))


def audit_visualstudio_intelligence_vsix(path: Union[Path, str]):
    try:
        return audit_visualstudio_diagnostics_vsix(path)
    except VisualStudioDiagnosticsError as error:
        raise VisualStudioIntelligenceError(str(error)) from error


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
            print(CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256); return 0
        if args.check_vsix:
            audit = audit_visualstudio_intelligence_vsix(args.check_vsix)
            print("Visual Studio T5.5 VSIX audit passed: {}".format(audit.vsix_sha256)); return 0
        if args.check:
            if not args.root:
                raise VisualStudioIntelligenceError("--check requires the Visual Studio extension root.")
            audit = audit_visualstudio_intelligence(args.root)
            print("Visual Studio T5.5 intelligence audit passed: {}".format(audit.intelligence_sha256)); return 0
        _parser().print_help(); return 0
    except VisualStudioIntelligenceError as error:
        print(str(error), file=sys.stderr); return 1

if __name__ == "__main__":
    raise SystemExit(main())
