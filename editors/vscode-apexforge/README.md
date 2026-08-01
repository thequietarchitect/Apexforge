# ApexForge Language for Visual Studio Code

The ApexForge language extension recognizes canonical lowercase `.apex` source
files and provides editor behavior synchronized with the frozen P10-T2 grammar.

## Language support

- Language ID: `apexforge`
- Canonical source extension: `.apex`
- Brace and parenthesis matching
- Automatic closing for braces, parentheses, and strings
- Four-space indentation defaults
- TextMate highlighting for declarations, module headers, types, literals,
  operators, actions, control flow, and function calls

ApexForge comments remain unsupported by the frozen P10-T2 grammar, so the
extension intentionally does not declare or highlight comment syntax.

## Local VSIX packaging

AFP-P10-T3.3 packages this syntax-only extension with the official
`@vscode/vsce` tool and audits the resulting VSIX payload before installation.
The deterministic audit checks the embedded package manifest, TextMate grammar,
language configuration, documentation, archive safety, and installed extension
identity.

The local extension ID is:

```text
gravitas-studios.apexforge-language
```

The publisher field identifies the package namespace only. Marketplace
publication and publisher registration are outside the T3.3 local-install
milestone.
