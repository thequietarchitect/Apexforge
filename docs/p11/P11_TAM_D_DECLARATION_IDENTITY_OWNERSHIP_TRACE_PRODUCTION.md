# P11-TAM-D â€” Declaration, Identity, and Ownership Trace Production

## Purpose

P11-TAM-D extends the deterministic Compiler Token Analysis Map producer layer
to the frozen project declaration-ownership and declared-identity metadata
introduced before TAM.

The slice consumes:

- `language.declarations.ProjectDeclarationOwner`;
- `language.declarations.ProjectDeclarationOwnership`;
- `language.identities.ProjectDeclaredIdentity`;
- `language.identities.ProjectIdentityIndex`.

TAM observes those contracts. It does not replace or regenerate them.

## Predecessor

P11-TAM-D begins from:

`afp-p11-tam-c-freeze`
â†’ `8e64220fba18ff4e72726468dd59f041bc493bd2`

The P11-TAM-B immutable trace model and P11-TAM-C SourceMap production
contracts remain predecessor capabilities.

## Production API

P11-TAM-D extends `tam.production` with:

- `trace_record_from_declaration_owner(declaration, declaration_index=...)`;
- `trace_record_from_declared_identity(identity, identity_index=...)`;
- `trace_map_from_declaration_identity_indexes(declaration_ownership, identity_index)`.

These functions are exported through `tam.__init__`.

## Declaration ownership records

Each existing `ProjectDeclarationOwner` produces one `ownership`-domain
`TraceRecord`.

The trace:

- preserves the exact existing `SourceSpan`;
- references the existing `air_id` as `canonical_identity`;
- identifies `language.declarations` as producer and owner;
- uses `project-declaration-owner` as its representation;
- does not invent provenance;
- does not infer graph links.

The TAM-local trace ID is deterministic over:

- its position in `ProjectDeclarationOwnership.declarations`;
- `kind`;
- existing `air_id`;
- `source_name`;
- existing optional `module_name`;
- exact source-span coordinates.

## Declared identity records

Each existing `ProjectDeclaredIdentity` produces one `declaration`-domain
`TraceRecord`.

The trace:

- preserves the exact existing `SourceSpan`;
- references `current_air_id` as `canonical_identity`;
- identifies `language.identities` as producer and owner;
- uses `project-declared-identity` as its representation;
- does not invent provenance;
- does not infer graph links.

Its deterministic TAM-local ID incorporates:

- its position in `ProjectIdentityIndex.identities`;
- `kind`;
- `declared_name`;
- existing `current_air_id`;
- `source_name`;
- existing optional `module_name`;
- `qualified_display_name`;
- exact source-span coordinates.

## Distinct observational contracts

An ownership record and a declared-identity record may reference the same AIR
ID. They remain distinct TAM records.

A shared AIR ID does not authorize TAM to collapse, join, resolve, or rewrite
the two records. Their domains, trace-ID namespaces, producing subsystems, and
representations remain distinct.

Therefore:

`OWNER_AND_IDENTITY_TRACES=DISTINCT`

## Ordering

`trace_map_from_declaration_identity_indexes` uses a deterministic block order:

1. all `ProjectDeclarationOwnership.declarations` in their existing tuple
   order;
2. all `ProjectIdentityIndex.identities` in their existing tuple order.

No sorting or semantic ranking is introduced.

The two source containers do not expose a shared global order, so TAM does not
fabricate one beyond this explicit stable block composition rule.

## Missing evidence

Empty ownership and identity containers produce an empty `TraceMap`.

P11-TAM-D does not synthesize:

- declarations;
- declared names;
- AIR IDs;
- module names;
- source spans;
- provenance;
- ownership relationships;
- identity-resolution relationships;
- graph edges.

## Frozen ownership boundary

P11-TAM-D does not modify:

- `tam.model`;
- `language.source`;
- `language.compiler`;
- `language.declarations`;
- `language.identities`;
- `language.project`;
- `ProjectBuilder`;
- project loading or CLI routing;
- LSP diagnostics;
- narrative analysis;
- semantic-decision analysis;
- semantic-lattice adapters;
- runtime execution.

The smoke test may use the frozen compiler solely to obtain a real canonical
`SourceSpan` and AIR ID for fixture evidence. That is test consumption, not
compiler instrumentation.

## Resolution boundary

The producer does not call declaration or identity lookup methods such as:

- `find_all`;
- `find_current_air_id`;
- `find_qualified_display_name`.

It consumes the ordered frozen tuples directly and records what is already
present.

Therefore:

`RESOLUTION_EXECUTION=NONE`

## Completion condition

P11-TAM-D is complete when:

- TAM-C freeze ancestry is proven;
- declaration ownership records are consumed;
- declared identity records are consumed;
- AIR IDs remain reference-only;
- exact `SourceSpan` references are preserved;
- ownership and identity traces remain distinct even for the same AIR ID;
- both input tuple orders are preserved;
- repeated input produces identical trace IDs and maps;
- empty indexes do not fabricate records;
- no graph/resolution semantics are inferred;
- all frozen semantic owners remain unchanged;
- TAM-C and durable SRC regression remain green.