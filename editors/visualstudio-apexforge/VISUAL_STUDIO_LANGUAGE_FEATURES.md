# ApexForge Visual Studio Language Features

## AFP-P10-T5.4 — Live diagnostics and document synchronization

The Visual Studio extension uses the native `ILanguageClient` code-remote bridge established in T5.3. The Visual Studio LSP host owns protocol dispatch and editor presentation; the frozen AFP-P10-T4.11 Python server remains the language authority.

Verified protocol surface:

- `textDocument/didOpen`
- `textDocument/didChange` with full-document synchronization
- `textDocument/didClose`
- `textDocument/publishDiagnostics`
- UTF-16 diagnostic ranges
- versioned diagnostic replacement and close-time clearing

## AFP-P10-T5.5 — IntelliSense, navigation, rename, and formatting

The same bridge exposes the complete frozen T4.11 feature surface to Visual Studio:

- hierarchical document symbols
- syntax hover
- context-aware completion
- same-document go to definition
- same-document find references
- safe same-document prepare rename and rename
- read-only workspace symbols
- deterministic whole-document formatting

Frozen boundaries remain unchanged: cross-file definition, workspace references, cross-file rename, range formatting, format-on-type, and a persistent workspace index are deferred beyond P10-T5.

## Manual Experimental Instance gate

Open a `.apex` file in the Experimental Instance and verify:

1. Introduce `#` inside a directive body. A syntax diagnostic appears in the editor/Error List.
2. Remove `#`. The diagnostic clears without reopening the document.
3. Hover over `count` to see ApexForge declaration information.
4. Invoke completion in a directive/cause/path body.
5. Use F12 on a same-document state or event reference.
6. Use Shift+F12 on the same symbol.
7. Use F2 on a renameable state/event/local symbol and verify all same-document occurrences update.
8. Run Format Document and verify deterministic four-space formatting.
9. Open Tools > ApexForge Extension Status and verify T5.3, T5.4, and T5.5 are active.
