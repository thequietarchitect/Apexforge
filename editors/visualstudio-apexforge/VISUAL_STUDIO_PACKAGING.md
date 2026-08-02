# AFP-P10-T5.7 — Visual Studio VSIX Packaging and Installation Hardening

T5.7 hardens the existing ApexForge Visual Studio extension artifact and its
Experimental Instance installation. It does not add ApexForge syntax, parser,
compiler, runtime, language-server, or editor-intelligence behavior.

## Hardened VSIX audit

The T5.7 auditor rejects:

- absolute, parent-traversal, drive-qualified, or backslash archive paths;
- duplicate normalized archive paths, including case-only duplicates;
- encrypted entries and symbolic links;
- nested VSIX, source, project, debug-symbol, cache, and IDE-state payloads;
- development directories such as `bin`, `obj`, `.git`, `.vs`, `.vscode`,
  `node_modules`, and `__pycache__`;
- oversized entries, excessive total expansion, and extreme compression ratios;
- missing or duplicate manifest, assembly, package-definition, or content-type
  entries;
- manifest identity, publisher, version, architecture, asset, or prerequisite
  drift.

## Hardened installed-copy audit

The installed Experimental Instance must contain exactly one ApexForge extension
manifest. Multiple matches are rejected as stale duplicate extension registrations.
The auditor then requires built/installed assembly SHA-256 equality between the
VSIX payload and the installed `ApexForge.VisualStudio.dll`.

## Boundary

T5.7 preserves the frozen T5.1 through T5.6 runtime and editor behavior. The
extension identity remains `GravitasStudios.ApexForge.VisualStudio`, package version
`0.1.0`, and installation architectures `amd64` and `arm64`.

T5.8 remains the final Visual Studio integration hardening and full P10-T5 freeze.
