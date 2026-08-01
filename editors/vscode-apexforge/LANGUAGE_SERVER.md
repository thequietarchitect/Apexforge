# ApexForge Language Server

AFP-P10-T4.7 activates one ApexForge language-server process for each file-system
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
- Definition navigation: same-document `textDocument/definition`

Go to Definition resolves declaration names, function type parameters, function
parameters and prior local bindings, recursive function calls, directive state
actions and expressions, directive event emissions, and identifiers used by
`message` or `when` expressions. Use **F12**, **Ctrl+Click**, or the editor's
Go to Definition command on a supported identifier.

Completion remains available for top-level declarations, declaration-body
keywords, type and generic-constraint positions, directive state and event
targets, and function or directive expression names. The completion analyzer
tolerates incomplete source while typing and replaces only the current
identifier prefix.

Hover, completion, and definition remain open-document features. Definition is
limited to the current document. Imports, workflow or directive invocation
targets, authority, role, and capability references require later cross-file
resolution. References, rename, workspace symbols, formatting, compilation, and
type inference remain deferred.

The Python launcher and server path can be overridden in workspace settings.

## Commands

- `ApexForge: Show Language Server Output`
- `ApexForge: Restart Language Server`

The extension shuts each server down with the LSP `shutdown` request followed by
the `exit` notification.
