# P11.2I-B Opt-In Human-Readable Runtime Result Report

## Scope

P11.2I-B implements one observational console feature:

```text
apexforge run <project> --report
```

The implementation owns:

```text
apexforge/tooling/cli.py
apexforge/tools/runtime_report.py
apexforge/p11_2i_opt_in_runtime_result_report_smoke_test.py
docs/p11/P11_2I_B_OPT_IN_RUNTIME_RESULT_REPORT.md
```

P11.2I-B also narrowly aligns the P11.2I-A executable ownership audit so the
reviewed successor can be validated before and after publication.

## Frozen predecessor

```text
annotated tag: afp-p11.2h-freeze
commit: 28b61e7392d164cc91c3ecaf2bb8c24cba522153
```

The P11.2I-A architecture document remains unchanged.

## Public command contract

Without `--report`, the existing output remains byte-for-byte:

```text
ApexForge run succeeded: <project>
Entry: directive:<entry>
Runtime diagnostics: 0
```

With `--report`, the command executes the same project and canonical entry
exactly once, prints the same success preamble, prints one blank line, and
appends the deterministic report.

## Canonical report source

The renderer consumes only the `ExecutionResult` returned by the existing
`ProjectBuild.execute` call. It reads the result status, diagnostics, state
delta, trace, and final state. It does not rebuild, re-resolve, or re-execute.

## Deterministic report format

The exact section order is:

```text
APEXFORGE RUNTIME REPORT

RESULT
DIAGNOSTICS
ASSIGNMENTS
EVENTS
EFFECTS
TRACE
FINAL STATE
END RUNTIME REPORT
```

Every empty collection is rendered as `(none)`.

Diagnostics use deterministic diagnostic ordering. Assignments, events,
effects, and trace steps retain runtime order. Final state retains canonical
`StateSnapshot` key order. Facts retain their existing canonical key order.

Runtime booleans, integers, floats, strings, and AIR literal wrappers are
rendered deterministically. Unsupported values expose only their type name,
never an object identity or memory address.

## Failure and stream behavior

Runtime failure keeps the existing behavior:

- diagnostics go to `stderr`;
- the runtime exit code remains unchanged;
- no success preamble is printed;
- no report is printed.

The report is written only through the CLI's supplied `stdout` stream.

## Build-artifact separation

P11.2I-B does not modify build-artifact v1, artifact JSON or fingerprints, AIR
serialization, runtime models, manifest schema, grammar, linker, verifier, or
compiler behavior.

## Compatibility boundary

P11.2I-B preserves the CLI name and version, all existing exit codes, canonical
entry resolution, entry-only authority grants, one execution per invocation,
ordinary run output, project checking, build behavior, editor tooling, and the
protected P11Validation fixture.

No report file, JSON protocol, telemetry, timing, filtering, editor
integration, network behavior, or P11.5 ownership change is introduced.

## Acceptance evidence

The focused smoke test proves exact rendering, ordinary-output compatibility,
opt-in append behavior, one execution per invocation, canonical entry
selection, unchanged failure routing, exact ownership, and preservation of
cwd, environment, repository status, and bytecode state.
