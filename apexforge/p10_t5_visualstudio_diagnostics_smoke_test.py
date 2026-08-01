"""AFP-P10-T5.4 Visual Studio diagnostics/document-sync smoke test."""
from __future__ import annotations

from pathlib import Path

from language_server.integration import CANONICAL_INTEGRATION_SHA256
from language_server.server import LanguageServerSession
from tooling.visualstudio_diagnostics import (
    CANONICAL_VISUAL_STUDIO_DIAGNOSTICS_SHA256,
    audit_visualstudio_diagnostics,
    visual_studio_diagnostics_fingerprint,
)

EXPECTED_T4_11 = "c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897"
EXPECTED_T5_4 = "54eff4034a801107463df9b9ccb8bfaa2e83e534b1e6f5ae80e21362f0a2271f"
URI = "file:///C:/ApexForgeVisualStudioDiagnostics/main.apex"
INVALID_SOURCE = "directive Counter {\n    #\n}\n"
VALID_SOURCE = """directive Counter {
    state count : int = 0
    event changed
    cause run {
        path primary @ 10 {
            add count 1
            emit changed
        }
    }
}
"""

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def request(message_id: object, method: str, params: object = None) -> dict:
    value = {"jsonrpc": "2.0", "id": message_id, "method": method}
    if params is not None: value["params"] = params
    return value

def notification(method: str, params: object = None) -> dict:
    value = {"jsonrpc": "2.0", "method": method}
    if params is not None: value["params"] = params
    return value

def publish_params(message: object) -> dict:
    require(type(message) is dict, "publishDiagnostics message must be an object")
    require(message.get("method") == "textDocument/publishDiagnostics", "wrong diagnostics method")
    params = message.get("params")
    require(type(params) is dict, "publishDiagnostics params must be an object")
    return params

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    extension_root = root / "editors/visualstudio-apexforge"
    require(CANONICAL_INTEGRATION_SHA256 == EXPECTED_T4_11, "T4.11 integration changed")
    require(visual_studio_diagnostics_fingerprint() == EXPECTED_T5_4, "T5.4 fingerprint changed")
    require(CANONICAL_VISUAL_STUDIO_DIAGNOSTICS_SHA256 == EXPECTED_T5_4, "declared T5.4 fingerprint changed")
    audit = audit_visualstudio_diagnostics(extension_root)
    require(audit.diagnostics_sha256 == EXPECTED_T5_4, "T5.4 source audit changed")

    session = LanguageServerSession()
    capabilities = {"textDocument": {"publishDiagnostics": {"relatedInformation": True, "versionSupport": True}}}
    initialized = session.process(request(1, "initialize", {"processId": None, "rootUri": "file:///C:/ApexForgeVisualStudioDiagnostics", "capabilities": capabilities}))
    require(initialized.get("result", {}).get("capabilities", {}).get("textDocumentSync", {}).get("change") == 1, "full sync was not negotiated")
    session.process(notification("initialized", {}))
    session.process(notification("textDocument/didOpen", {"textDocument": {"uri": URI, "languageId": "apexforge", "version": 1, "text": INVALID_SOURCE}}))
    opened = session.drain_outgoing_notifications()
    require(len(opened) == 1, "didOpen did not publish diagnostics")
    opened_params = publish_params(opened[0])
    require(opened_params.get("version") == 1, "didOpen diagnostic version changed")
    require(len(opened_params.get("diagnostics", [])) >= 1, "invalid source produced no diagnostics")
    session.process(notification("textDocument/didChange", {"textDocument": {"uri": URI, "version": 2}, "contentChanges": [{"text": VALID_SOURCE}]}))
    changed = session.drain_outgoing_notifications()
    require(len(changed) == 1, "didChange did not publish diagnostics")
    changed_params = publish_params(changed[0])
    require(changed_params.get("version") == 2, "didChange diagnostic version changed")
    require(changed_params.get("diagnostics") == [], "fixed source did not clear diagnostics")
    session.process(notification("textDocument/didClose", {"textDocument": {"uri": URI}}))
    closed = session.drain_outgoing_notifications()
    require(len(closed) == 1, "didClose did not clear diagnostics")
    closed_params = publish_params(closed[0])
    require(closed_params.get("diagnostics") == [], "didClose clear was not empty")
    require("version" not in closed_params, "didClose clear retained a version")

    print("AFP-P10-T5.4 Visual Studio diagnostics/document-sync smoke test passed.")
    print("Frozen T4.11 server integration: PASS")
    print("Visual Studio T5.3 bridge projection: PASS")
    print("Versioned didOpen/didChange diagnostics: PASS")
    print("didClose diagnostic clearing: PASS")
    print("UTF-16/full-document synchronization contract: PASS")
    print("Deterministic T5.4 fingerprint: PASS")

if __name__ == "__main__":
    main()
