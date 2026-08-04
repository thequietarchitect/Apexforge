# P11.2F Linked AIR Legality and Governance Boundary

## Frozen predecessor

P11.2E is the reviewed predecessor for this continuation branch at commit
`bb1f3a3a33aabda0dc5ab5b37e0898fbbc636544`. P11.2F must preserve heterogeneous source-unit
compilation, canonical declaration models, deterministic AIRProgram assembly,
serialization compatibility, project compatibility, and the single linked
runtime transaction.

## Stage purpose

P11.2F defines and implements legality for a linked heterogeneous AIRProgram.
It closes references and declaration graphs before execution while preserving
the separation between compiler lowering, linker assembly, verification,
authorization, runtime execution, and Concordat governance.

P11.2F introduces no new source syntax.

## Ownership boundary

### Compiler

The compiler lowers source declarations and records source-map evidence. It may
defer cross-source references that cannot be decided inside one source unit.

### Linker

The linker:

- accepts AIRProgram compilation units only;
- enforces AIR-version compatibility;
- merges every canonical declaration family deterministically;
- rejects duplicate global definitions according to each declaration family's
  proven consumer identity semantics;
- preserves or reassigns deterministic global ordering where ordering belongs
  to the canonical model;
- does not authorize principals, execute directives, or resolve policy
  conflicts.

The linker must not apply a universal case-folding rule without evidence.
Directive, authority, principal, role, workflow, and function identity rules
must be tested against their actual registries, resolvers, and runtime
consumers.

Direct AIR linking retains the proven case-insensitive runtime collision
semantics for directive and principal identities. A nonlegacy module project
uses an explicit linker profile that preserves stored case distinctions for
those two flat AIR families, because the frozen module/entry consumer contract
permits `directive:Alpha` and `directive:alpha` as separate exact-case entries.
This project-only profile does not weaken direct AIR linking, registry lookup,
or authorization behavior.

### AIR verifier

AIRVerifier owns linked-program structural legality. It must eventually cover:

- uniqueness for principals, states, events, authority checks, causal
  decisions, directives, functions, workflows, authorities, and roles;
- directive principal, authority-check, causal-decision, authority-reference,
  and nested directive-invocation targets;
- workflow invocation targets;
- authority inheritance targets and cycles;
- principal role and authority references;
- role authority references;
- requirement ownership;
- deterministic diagnostics with stable codes, messages, node identities, and
  ordering.

A malformed symbol graph, missing target, duplicate declaration, or cyclic
inheritance graph is a structural error. It is rejected before runtime and is
not eligible for governance override.

### Authorization and runtime

Authorization decides whether an identified principal possesses required
authorities or capabilities. Runtime owns recursion, invocation-depth limits,
state transitions, event emission, and execution traces.

Runtime may retain defensive checks, but verified programs must not rely on
runtime entry to discover ordinary linked-program structural defects.

Registry-linked execution has one narrow compatibility exception: an invocation
target that cannot be resolved from the selected registry dependency closure may
remain deferred so RuntimeEngine can preserve the established RUN002 diagnostic
and full-transaction rollback contract. Direct AIR verification remains strict
by default, and this exception does not permit duplicate, malformed, cyclic, or
authorization-invalid AIR.

### Concordat governance

Concordat TAM-v3 remains the governance authority. Tap Check is observational
and never activates directives.

A genuine policy conflict may be represented as structured conflict evidence
and routed through Concordat Court using WCCD and Gravitas Mode. Concordat
governance must not legalize malformed AIR, invent missing declarations,
silently replace duplicate declarations, bypass principal authorization, or
mutate the canonical Gravitas directive artifact.

Structural errors and authorization denials remain non-overridable.

P11.2F-F implements this boundary in `governance.conflicts` using immutable
`ConflictPosition`, `ConflictEvidence`, and `ConflictReferral` values.
`route_conflict_evidence` classifies policy evidence for referral to Concordat
Court with WCCD and Gravitas Mode metadata. It does not select a winner, execute
AIR, activate directives, invoke Tap Check, authorize principals, or mutate the
canonical Gravitas artifact. Structural and authorization categories produce
explicitly ineligible referrals with no court destination or governance methods.

## Initial audit findings

1. AIRProgramLinker merges all promoted declaration families, but duplicate
   keys currently follow stored spelling rather than an explicitly documented
   family-specific canonical identity projection.
2. AIRVerifier checks historical declaration families but does not yet provide
   complete uniqueness and reference closure for functions, workflows,
   authorities, and roles.
3. Workflow lowering preserves invocation targets for linked-program
   resolution.
4. AuthorityRegistry is case-insensitive; P11.2F-D rejects canonical
   duplicate registration before mutating the registry.
5. AIRVerifier closes authority inheritance targets and reports deterministic
   inheritance cycles before authorization or capability resolution.
6. P11.2F-E rejects program-level requirement ownership ambiguity with
   AIR065. Registry-linked verification uses the existing directive-owner map to
   validate each original program independently, while runtime retains its
   defensive ownership rejection.
7. Registry-linked execution already builds one dependency closure and one
   runtime transaction. P11.2F must preserve that behavior.
8. P11.2F-F adds only passive, immutable conflict evidence and deterministic
   referral metadata. It does not alter AIR verification, authorization, causal
   selection, runtime execution, or the Gravitas directive artifact.

## Diagnostic contract

P11.2F implementation diagnostics must be deterministic and additive. Existing
AIR codes and messages remain unchanged unless a defect requires a separately
reviewed migration.

New linked-legality diagnostics must:

- use stable AIR codes;
- identify the declaration or reference owner;
- distinguish duplicate, unknown, cyclic, incompatible, and
  ownership-ambiguous conditions;
- sort deterministically;
- remain independent of hash order and registry insertion accidents.

## Focused smoke-test matrix

The implementation smoke test will cover:

1. every promoted declaration family in a valid linked program;
2. duplicate identities under proven canonical semantics for each family;
3. unresolved workflow and nested directive invocation targets;
4. unknown authority inheritance;
5. authority inheritance cycles;
6. unknown principal authorities and roles;
7. unknown role authorities;
8. unknown directive authority references;
9. ambiguous requirement ownership;
10. deterministic diagnostic ordering and repeated-run equality;
11. one linked registry execution transaction after successful verification;
12. unchanged serialization and project compatibility;
13. unchanged `apexforge/directives/gravitas.air.json`;
14. unchanged P11.5A and P11.5B frozen ownership guards;
15. policy-conflict referral to Concordat Court with WCCD and Gravitas Mode;
16. structural and authorization evidence remains explicitly non-overridable;
17. Tap Check remains observational and no referral activates directives.

## Patch sequence

### P11.2F-A — Architecture audit

Own only this document and
`apexforge/p11_2f_linked_air_legality_architecture_audit_smoke_test.py`.
Do not modify production code.

### P11.2F-B — Canonical linker collision contract

Add family-specific identity projection and deterministic duplicate coverage.
Do not move unresolved-reference policy into the linker.

### P11.2F-C — Heterogeneous AIRVerifier coverage

Add uniqueness and closed-reference diagnostics for promoted declaration
families and invocation targets.

### P11.2F-D — Authority, role, and principal graph legality

Validate authority inheritance, role authority references, principal role and
authority references, duplicate registry registration, and deterministic cycle
evidence before authorization.

### P11.2F-E — Requirement ownership closure

Make directive requirement ownership statically explicit or statically reject
ambiguity. Preserve runtime checks as defense in depth.

### P11.2F-F — Concordat conflict-evidence boundary

Introduce only the minimum passive conflict-evidence interface needed to route
eligible policy conflicts to Concordat Court using WCCD and Gravitas Mode.
Structural errors and authorization denials remain non-overridable.

### P11.2F-G — Integration and regression gate

Run focused tests, historical linker/verifier/authority/workflow tests,
compileall, the full regression harness with the two known P11.5 frozen
ownership exclusions, diff checks, and protected-file checks.

## Protected boundaries

P11.2F must not modify:

- `apexforge/directives/gravitas.air.json`;
- `apexforge/p11_5a_narrative_semantic_foundation_architecture_audit_smoke_test.py`;
- `apexforge/p11_5b_minimal_narrative_semantic_model_smoke_test.py`;
- the pre-existing untracked `examples/P11Validation/` fixture tree.

P11.2F-A creates no commit, push, tag, or freeze by itself.
