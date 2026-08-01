# ApexForge Language Server

AFP-P10-T4.6 activates one ApexForge language-server process for each file-system
workspace folder that contains the configured server entry point.

## Default launch

- Python launcher: `py` on Windows, `python3` elsewhere
- Server path: `apexforge/apexforge_lsp.py`
- Arguments: `--stdio`
- Transport: JSON-RPC 2.0 over LSP `Content-Length` framing
- Document synchronization: full text
- Diagnostics: `textDocument/publishDiagnostics`
- Outline navigation: hierarchical `textDocument/documentSymbol`
- Hover intelligence: syntax-level `textDocument/hover` with Markdown content
- Completion: context-aware `textDocument/completion`

Completion is available for top-level declarations, declaration-body keywords,
type and generic-constraint positions, directive state and event targets, and
function or directive expression names. The completion analyzer tolerates
incomplete source while typing and replaces only the current identifier prefix.

Hover and completion remain open-document features. They do not perform
cross-file resolution, compilation, type inference, definition lookup,
references, rename, workspace symbols, or formatting.

The Python launcher and server path can be overridden in workspace settings.

## Commands

- `ApexForge: Show Language Server Output`
- `ApexForge: Restart Language Server`

The extension shuts each server down with the LSP `shutdown` request followed by
the `exit` notification.
