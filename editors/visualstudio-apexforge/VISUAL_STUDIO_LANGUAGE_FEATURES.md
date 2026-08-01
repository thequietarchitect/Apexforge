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

## AFP-P10-T5.6 — Native editor commands and controlled restart

The Visual Studio Tools menu now contains three ApexForge commands:

- **ApexForge Extension Status**
- **Restart ApexForge Language Server**
- **Open ApexForge Language Server Log**

The restart command uses the Visual Studio `ILanguageClient` lifecycle. It invokes `StopAsync` so the host can send the LSP `shutdown` request, terminates any surviving process, and then invokes `StartAsync` so Visual Studio calls `ActivateAsync` again. Restart operations are serialized to prevent overlapping stop/start sequences.

A restart is not reported as successful until `OnServerInitializedAsync` confirms the replacement server completed initialization. The client then permits a short document-resynchronization interval before completing the command so rename, references, formatting, and other open-document requests do not race the restarted server.

The log command opens `%TEMP%\ApexForge\visualstudio-language-client.log`. Whole-document formatting remains available through Visual Studio's native **Format Document** command.

## Manual Experimental Instance gate

Open the ApexForge repository as a folder, then open a `.apex` file and verify:

1. **Tools > ApexForge Extension Status** reports T5.3 through T5.6 active and `Language client loaded: True`.
2. **Tools > Open ApexForge Language Server Log** opens the stable client log.
3. Record the current language-server PID from the log.
4. **Tools > Restart ApexForge Language Server** reports success.
5. Reopen the log and confirm a restart request, a completed restart sequence, and a new process PID.
6. Run **Format Document** and confirm deterministic four-space formatting still works.
7. Use **Rename** (`Ctrl+R`, `Ctrl+R` in the current Visual Studio profile) on a same-document state or event and confirm all supported occurrences update.
