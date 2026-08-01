# ApexForge Language Server

AFP-P10-T4.9 activates one ApexForge language-server process for each file-system
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
- Workspace declaration search: read-only `workspace/symbol`

Use **Ctrl+T** or **Go to Symbol in Workspace** to search ApexForge declarations
across every `.apex` file beneath the opened workspace folder. T4.9 searches
modules, functions, directives, states, events, causes, paths, workflows,
authorities, capabilities, roles, and principals. Results include their source
location and containing declaration where applicable.

The workspace-symbol request performs a deterministic recursive scan and overlays
unsaved open-document text over the on-disk file. It ignores `.git`, build,
`dist`, virtual-environment, `node_modules`, and cache directories. Search is
case-insensitive, supports multiple whitespace-separated terms, ranks exact and
prefix matches first, and returns a bounded result set.

Workspace Symbols are read-only in T4.9. They do not yet enable cross-file Go to
Definition, Find References, Rename, import resolution, or a persistent index.
Those operations remain protected until a later cross-file identity layer can
prove every affected declaration and occurrence.

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

Workspace-visible declarations remain protected from rename. Modules, functions,
directives, workflows, authorities, capabilities, roles, and principals may be
referenced by other files and cannot yet be renamed safely.

Go to Definition continues to resolve declaration names, function type
parameters, function parameters and prior local bindings, recursive calls,
directive state actions and expressions, event emissions, and identifiers in
`message` or `when` expressions.

Completion remains available for top-level declarations, declaration-body
keywords, type and generic-constraint positions, directive state and event
targets, and function or directive expression names. The completion analyzer
tolerates incomplete source while typing and replaces only the current
identifier prefix.

Formatting, cross-file definition, workspace references, cross-file rename,
compilation, linking, and type inference remain deferred.

The Python launcher and server path can be overridden in workspace settings.

## Commands

- `ApexForge: Show Language Server Output`
- `ApexForge: Restart Language Server`

The extension shuts each server down with the LSP `shutdown` request followed by
the `exit` notification.
