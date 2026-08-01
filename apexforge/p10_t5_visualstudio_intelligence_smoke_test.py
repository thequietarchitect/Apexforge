"""AFP-P10-T5.5 Visual Studio language-intelligence parity smoke test."""
from __future__ import annotations

from pathlib import Path

from language_server.integration import (
    CANONICAL_INTEGRATION_SHA256,
    integrated_capabilities,
    verify_frozen_feature_hashes,
)
from language_server.server import LanguageServerSession
from tooling.visualstudio_intelligence import (
    CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256,
    audit_visualstudio_intelligence,
    visual_studio_intelligence_fingerprint,
)

EXPECTED_T4_11 = "c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897"
EXPECTED_T5_5 = "65f6ab0565276a59b1a71814acb0023da161a38661605b788e5f8b1e2753f82a"
URI = "file:///C:/ApexForgeVisualStudioIntelligence/Counter.apex"
SOURCE = """directive Counter {
    state count : int = 0
    event changed
    cause run {
        path primary @ 10 {
            add count 1
            message count
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

def all_capabilities() -> dict:
    return {
        "textDocument": {
            "publishDiagnostics": {"relatedInformation": True, "versionSupport": True},
            "documentSymbol": {"hierarchicalDocumentSymbolSupport": True},
            "hover": {"contentFormat": ["markdown", "plaintext"]},
            "completion": {"completionItem": {"snippetSupport": False}},
            "definition": {"linkSupport": False},
            "references": {},
            "rename": {"prepareSupport": True},
            "formatting": {"dynamicRegistration": False},
        },
        "workspace": {"symbol": {"dynamicRegistration": False}},
    }

def result(response: dict):
    require(type(response) is dict and "error" not in response, "language request failed: {!r}".format(response))
    return response.get("result")

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    extension_root = root / "editors/visualstudio-apexforge"
    require(CANONICAL_INTEGRATION_SHA256 == EXPECTED_T4_11, "T4.11 integration changed")
    require(verify_frozen_feature_hashes(), "a frozen T4 feature changed")
    require(visual_studio_intelligence_fingerprint() == EXPECTED_T5_5, "T5.5 fingerprint changed")
    require(CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256 == EXPECTED_T5_5, "declared T5.5 fingerprint changed")
    audit = audit_visualstudio_intelligence(extension_root)
    require(audit.intelligence_sha256 == EXPECTED_T5_5, "T5.5 source audit changed")
    require(audit.method_count == 9, "T5.5 method inventory changed")

    session = LanguageServerSession()
    initialized = session.process(request(1, "initialize", {"processId": None, "rootUri": "file:///C:/ApexForgeVisualStudioIntelligence", "capabilities": all_capabilities()}))
    require(result(initialized).get("capabilities") == integrated_capabilities(), "integrated capability negotiation changed")
    session.process(notification("initialized", {}))
    session.process(notification("textDocument/didOpen", {"textDocument": {"uri": URI, "languageId": "apexforge", "version": 1, "text": SOURCE}}))
    session.drain_outgoing_notifications()

    symbols = result(session.process(request(2, "textDocument/documentSymbol", {"textDocument": {"uri": URI}})))
    require(isinstance(symbols, list) and len(symbols) == 1, "document symbols unavailable")
    hover = result(session.process(request(3, "textDocument/hover", {"textDocument": {"uri": URI}, "position": {"line": 1, "character": 10}})))
    require(isinstance(hover, dict) and hover.get("contents"), "hover unavailable")
    completion = result(session.process(request(4, "textDocument/completion", {"textDocument": {"uri": URI}, "position": {"line": 4, "character": 8}})))
    require(isinstance(completion, dict) and isinstance(completion.get("items"), list), "completion unavailable")
    definition = result(session.process(request(5, "textDocument/definition", {"textDocument": {"uri": URI}, "position": {"line": 5, "character": 17}})))
    require(isinstance(definition, dict) and definition.get("range"), "definition unavailable")
    references = result(session.process(request(6, "textDocument/references", {"textDocument": {"uri": URI}, "position": {"line": 5, "character": 17}, "context": {"includeDeclaration": True}})))
    require(isinstance(references, (list, tuple)) and len(references) >= 2, "references unavailable")
    prepared = result(session.process(request(7, "textDocument/prepareRename", {"textDocument": {"uri": URI}, "position": {"line": 5, "character": 17}})))
    require(isinstance(prepared, dict) and prepared.get("range"), "prepareRename unavailable")
    renamed = result(session.process(request(8, "textDocument/rename", {"textDocument": {"uri": URI}, "position": {"line": 5, "character": 17}, "newName": "total"})))
    require(isinstance(renamed, dict) and renamed.get("changes"), "rename unavailable")
    formatted = result(session.process(request(9, "textDocument/formatting", {"textDocument": {"uri": URI}, "options": {"tabSize": 4, "insertSpaces": True}})))
    require(isinstance(formatted, (list, tuple)) and len(formatted) == 0, "already-formatted source should require no edits")

    print("AFP-P10-T5.5 Visual Studio language-intelligence parity smoke test passed.")
    print("Hierarchical document symbols: PASS")
    print("Hover and completion: PASS")
    print("Definition and references: PASS")
    print("Safe same-document rename: PASS")
    print("Deterministic document formatting: PASS")
    print("Workspace-symbol capability and frozen feature inventory: PASS")
    print("Deterministic T5.5 fingerprint: PASS")

if __name__ == "__main__":
    main()
