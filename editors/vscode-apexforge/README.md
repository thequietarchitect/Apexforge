# ApexForge Language for Visual Studio Code

AFP-P10-T3.1 establishes the VS Code language-extension foundation for
ApexForge source files.

## Included in T3.1

- Language ID: `apexforge`
- Canonical source extension: `.apex`
- Display name: `ApexForge`
- Brace and parenthesis matching
- Automatic closing for braces, parentheses, and strings
- Four-space indentation defaults
- Block indentation for lines ending in `{`

ApexForge comments remain unsupported by the frozen P10-T2 grammar, so this
configuration intentionally does not declare comment syntax.

Syntax highlighting is added separately in AFP-P10-T3.2.
