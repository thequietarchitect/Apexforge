# ApexForge Language Server

AFP-P10-T4.8 activates one ApexForge language-server process for each file-system
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
- Reference discovery: same-document `textDocument/references`
- Rename preparation: guarded `textDocument/prepareRename`
- Rename edits: safe same-document `textDocument/rename`

Find References reuses the exact symbol identity and occurrence graph used by Go
to Definition. Use **Shift+F12** or the editor's Find All References command on
a supported type parameter, function parameter, prior local binding, recursive
function call, directive state, directive event, cause, path, or supported
declaration name. The request honors whether the declaration should be included.

Rename uses the same exact occurrence set as Find References. Use **F2** on a
function type parameter, function parameter, prior local binding, directive
state, directive event, cause, or path. The server validates ApexForge identifier
syntax, rejects reserved words and same-namespace collisions, and returns one
same-document `WorkspaceEdit`.

Workspace-visible declarations are deliberately protected from rename in T4.8.
Modules, functions, directives, workflows, authorities, capabilities, roles, and
principals may be referenced by other files, so they require later cross-file
indexing before they can be renamed safely.

Go to Definition continues to resolve declaration names, function type
parameters, function parameters and prior local bindings, recursive calls,
directive state actions and expressions, event emissions, and identifiers in
`message` or `when` expressions.

Completion remains available for top-level declarations, declaration-body
keywords, type and generic-constraint positions, directive state and event
targets, and function or directive expression names. The completion analyzer
tolerates incomplete source while typing and replaces only the current
identifier prefix.

Hover, completion, definition, references, and rename remain open-document
features. Imports, workflow or directive invocation targets, authority, role,
and capability references require later cross-file resolution. Workspace
symbols, formatting, compilation, and type inference remain deferred.

The Python launcher and server path can be overridden in workspace settings.

## Commands

- `ApexForge: Show Language Server Output`
- `ApexForge: Restart Language Server`

The extension shuts each server down with the LSP `shutdown` request followed by
the `exit` notification.
