# AFP-P10-T5.8 — Final Visual Studio Integration Hardening

AFP-P10-T5.8 closes the Visual Studio integration track and declares **P10-T5 complete** after the frozen T5.1 through T5.7 contracts pass together as one source, VSIX, installed-copy, regression, and live-editor system.

## Boundary

T5.8 adds a final composite auditor and release gate with **no runtime feature expansion**. It does not modify the ApexForge language server, parser, compiler, runtime, syntax classifier, language client, diagnostics, IntelliSense features, formatting, rename behavior, editor commands, or VSIX payload.

## Final automated gates

- Every frozen T5.1–T5.7 contract fingerprint must match.
- Every predecessor source auditor must pass against one extension tree.
- Release rebuild must complete with warnings treated as errors.
- Every predecessor VSIX auditor must agree on one archive SHA-256.
- The hardened VSIX path, payload, manifest, architecture, and assembly checks must pass.
- A normalized payload SHA-256 is reported independently of ZIP container metadata.
- The Experimental Instance must contain exactly one ApexForge registration.
- The final installed-copy gate requires built/installed assembly SHA-256 equality.
- The complete ApexForge regression harness must pass.

## Final live acceptance matrix

1. `.apex` syntax highlighting remains active.
2. Document synchronization and diagnostics remain active and clear after correction.
3. Outline, hover, and completion remain active.
4. Definition, references, and safe same-document rename remain active.
5. Whole-document formatting remains active.
6. Extension Status, Restart Language Server, and Open Language Server Log remain active.
7. All editor functions remain active after a controlled language-server restart.

## Freeze

After automated and live acceptance pass, create both final tags:

- `afp-p10-t5.8-freeze`
- `afp-p10-t5-final-freeze`

Those tags freeze the complete P10-T5 Visual Studio integration surface. Later Visual Studio work requires a new phase rather than silently changing a T5 contract.
