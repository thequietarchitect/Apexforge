# ApexForge Language Server

AFP-P10-T4.10 activates one ApexForge language-server process for each file-system
workspace folder and adds deterministic whole-document formatting.

## Default launch and features

- Python launcher: `py` on Windows, `python3` elsewhere
- Server path: `apexforge/apexforge_lsp.py`
- Transport: JSON-RPC 2.0 over LSP `Content-Length` framing
- Full-text synchronization and live syntax diagnostics
- Hierarchical `textDocument/documentSymbol` navigation
- Syntax-level `textDocument/hover` intelligence
- Context-aware `textDocument/completion`, including incomplete source
- Same-document `textDocument/definition` through **F12**
- Same-document `textDocument/references` through **Shift+F12**
- Safe `textDocument/prepareRename` and `textDocument/rename` through **F2**
- Read-only cross-file `workspace/symbol` search
- Whole-document `textDocument/formatting`

Compatibility vocabulary retained by the frozen validators: syntax-level, context-aware, incomplete source, same-document, cross-file, and Go to Symbol in Workspace.

Use **Shift+Alt+F** or **Format Document** in Visual Studio Code. T4.10 first
validates the open source through the frozen module-header and parser pipeline.
Invalid source receives no edit, preventing the formatter from concealing syntax
errors or guessing the user's intent. Already canonical source also receives no edit.

The canonical print style uses LF line endings, one terminal newline, one blank
line between module/import headers and the declaration, same-line opening braces,
own-line closing braces, `} otherwise {`, one space around binary operators and
colons, and one space after commas. Indentation follows the editor's `tabSize`
and `insertSpaces` formatting options. Formatting does not compile, link, execute,
resolve imports, infer types, reorder source-order members, or rewrite names.

T4.9 Workspace Symbols remain available through **Ctrl+T** or **Go to Symbol in
Workspace**. They scan `.apex` declarations across the workspace and overlay
unsaved open-document text. Workspace Symbols remain read-only.

Find References uses **Shift+F12** and Rename uses **F2** for symbols whose full
scope is known inside the current document. Cross-file definition, workspace
references, and cross-file rename remain deferred.

Range formatting, format-on-type, and an ApexForge-controlled format-on-save
policy are deferred. Visual Studio Code may still invoke whole-document formatting
on save when the user explicitly enables the editor's standard format-on-save
setting. T4.11 will perform full integration hardening and the final T4 freeze.

## Commands

- `ApexForge: Show Language Server Output`
- `ApexForge: Restart Language Server`

The extension shuts each server down with the LSP `shutdown` request followed by
the `exit` notification.
