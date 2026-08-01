# ApexForge Language Server

AFP-P10-T4.11 hardens the complete T4 language-server integration. It starts one
ApexForge server process for each file-system workspace folder and adds no new
language syntax or semantic scope beyond T4.1 through T4.10.

## Integrated feature surface

- Full-text synchronization and live `textDocument/publishDiagnostics`
- Hierarchical `textDocument/documentSymbol`
- Syntax-level `textDocument/hover`
- Context-aware `textDocument/completion`, including incomplete source
- Same-document `textDocument/definition` through **F12**
- Same-document `textDocument/references` through **Shift+F12**
- Safe `textDocument/prepareRename` and `textDocument/rename` through **F2**
- Read-only cross-file `workspace/symbol` through **Ctrl+T** or **Go to Symbol in Workspace**
- Whole-document `textDocument/formatting` through **Shift+Alt+F** or **Format Document**

Compatibility vocabulary retained by the frozen validators: syntax-level,
context-aware, incomplete source, same-document, cross-file, unsaved open-document,
read-only, Formatting, Find References, Rename, Workspace Symbols, and Go to Symbol
in Workspace.

## T4.11 hardening

The dependency-free client now connects editor cancellation tokens to
`$/cancelRequest`. A canceled request is rejected locally and removed from the
pending-request table, so a late response cannot overwrite newer editor state.
The synchronous Python server also maintains a bounded pre-dispatch cancellation
ledger and returns LSP request-cancelled code `-32800` when a request ID was
canceled before dispatch.

`$/setTrace` accepts `off`, `messages`, and `verbose`. Malformed notifications are
recorded and isolated rather than terminating the session. Unknown requests receive
Method Not Found, unknown notifications are ignored, document versions must increase,
and closing a document clears its diagnostics.

Extension restarts are serialized. A generation guard prevents an older startup
from replacing a newer server after configuration changes or repeated **ApexForge:
Restart Language Server** commands. Unexpected process exits clear synchronized
versions and diagnostics so the next provider request can start a clean process.

The VSIX audit verifies exact source parity for `extension.js`,
`runtime/lsp-client.js`, `LANGUAGE_SERVER.md`, and `package.json`; rejects unsafe,
duplicate, compiled-cache, nested-VSIX, Git, and workspace-setting payloads; and
checks JavaScript syntax.

## Formatting boundary retained

T4.10 formatting remains parser-backed and whole-document only. Invalid source
receives no edit. The canonical style uses LF line endings, one terminal newline,
one blank line between module/import headers and the declaration, same-line opening
braces, own-line closing braces, `} otherwise {`, one space around binary operators
and colons, and one space after commas. Indentation follows `tabSize` and
`insertSpaces`.

Range formatting, format-on-type, and an ApexForge-controlled format-on-save policy
remain deferred. Cross-file definition, workspace references, cross-file rename,
and a persistent workspace index also remain deferred.

## Commands

- `ApexForge: Show Language Server Output`
- `ApexForge: Restart Language Server`

The extension shuts each server down with the LSP `shutdown` request followed by
the `exit` notification. The final T4 freeze follows the T4.11 integrated smoke,
VSIX, installed-extension, and full regression checks.
