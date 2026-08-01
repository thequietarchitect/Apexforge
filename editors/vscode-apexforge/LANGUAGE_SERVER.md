# ApexForge Language Server

AFP-P10-T4.4 activates one ApexForge language-server process for each file-system
workspace folder that contains the configured server entry point.

## Default launch

- Python launcher: `py` on Windows, `python3` elsewhere
- Server path: `apexforge/apexforge_lsp.py`
- Arguments: `--stdio`
- Transport: JSON-RPC 2.0 over LSP `Content-Length` framing
- Document synchronization: full text
- Diagnostics: `textDocument/publishDiagnostics`
- Outline navigation: hierarchical `textDocument/documentSymbol`

The Python launcher and server path can be overridden in workspace settings.

## Commands

- `ApexForge: Show Language Server Output`
- `ApexForge: Restart Language Server`

The extension shuts each server down with the LSP `shutdown` request followed by
the `exit` notification.
