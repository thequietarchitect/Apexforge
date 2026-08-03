# P11.1B Canonical Public Run Command

## Scope

P11.1B adds one public command that loads, builds, and executes an ApexForge
project through the existing canonical project boundaries. It does not change
the grammar, compiler, linked AIR model, runtime engine, manifest schema, or
existing public commands.

## Command syntax and path behavior

```text
apexforge run [PATH] [--entry NAME]
```

`PATH` defaults to the current directory. It accepts the same project
directory, declared source path, or `apexforge.json` path behavior as the
existing `project` and `check` commands. Project discovery remains the
responsibility of `load_project`.

The public pipeline is exactly:

```text
load_project -> build_project -> ProjectBuild.execute
```

The CLI does not call `RuntimeEngine` directly and does not expose the
runtime's all-directive `entry_directives=None` compatibility path.

## Entry precedence

Entry selection uses this order:

1. `--entry NAME`, when present.
2. The manifest `entry`, when present.
3. The only linked directive, when the project contains exactly one.
4. The existing `ProjectEntryPointError` diagnostic for an ambiguous or
   undefined entry.

`ProjectBuild.resolve_entry` and `ProjectBuild.execute` share the existing
canonical entry resolver. A plain name such as `Main` resolves to the linked
canonical identity `directive:Main`; no second CLI resolver is used.

## Initial state and authority

Initial runtime state is constructed exactly as:

```python
StateSnapshot.from_program_initials(build.program)
```

Issuing `apexforge run` authorizes only invocation of the resolved entry
directive. For a resolved directive named `NAME`, the one constructed grant
uses these exact identities:

```text
principal:  principal:NAME
capability: directive.invoke:NAME
resource:   directive:NAME
```

More precisely, the principal and resource are taken from the resolved linked
directive (`directive.principal` and `directive.id`), and the capability is
`directive.invoke:<directive.name>`. The context contains exactly that one
`AuthorityGrant` in a deny-by-default `AuthorityEngine`.

The policy grants no root, wildcard, universal, cross-directive,
standard-library, host-effect, or internal capability. An entry directive that
invokes another directive reaches the callee's normal authority check. Because
the callee received no grant, that check retains its normal runtime diagnostic
and transaction behavior.

## Output and diagnostics

A successful run writes exactly this three-line shape to stdout:

```text
ApexForge run succeeded: PROJECT_NAME
Entry: directive:ENTRY_NAME
Runtime diagnostics: 0
```

It writes nothing to stderr. The output contains no absolute path, timing,
state serialization, opaque runtime value, or execution trace.

Runtime diagnostics are sorted using the runtime diagnostic ordering and
written to stderr, one per line, as:

```text
NODE_ID [CODE] MESSAGE
```

`<runtime>` replaces an absent node identity. A run that returns any runtime
diagnostic prints no success output and exits nonzero. Authority failures such
as `RUN001` are not suppressed or converted into success.

## Exit codes

- `0`: successful execution with zero runtime diagnostics.
- `2`: invalid CLI usage.
- `10`: manifest discovery, manifest validation, or source loading failure.
- `20`: compilation, linking, validation, or entry-resolution failure.
- `30`: runtime returned one or more diagnostics.
- `70`: unexpected internal CLI failure.
- `130`: keyboard interruption.

The existing `project`, `check`, `new`, and `--version` output and exit
behavior remain unchanged.

## Known limitations and deferred work

This slice intentionally provides only concise human output. It has no JSON,
trace, debugger, final-state dump, or output-file mode. It does not persist AIR
or create build artifacts. Build artifacts and richer output modes are deferred
to separately reviewed later work, including P11.1C where applicable.

Projects that require authority beyond invocation of the selected entry are
expected to fail with their existing runtime diagnostics. P11.1B does not add
an authority configuration surface or infer additional grants.
