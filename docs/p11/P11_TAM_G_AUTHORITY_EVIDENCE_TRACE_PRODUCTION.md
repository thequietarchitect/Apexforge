# P11-TAM-G â€” Authority Evidence Trace Production

## Purpose

P11-TAM-G adds deterministic TAM projection for the canonical passive authority
model owned by `authority.model`.

This slice records authority evidence. It does not check, allow, deny, grant,
inherit, resolve roles, query registries, compile declarations, or execute
authority policy.

## Predecessor

P11-TAM-G begins from:

`afp-p11-tam-f-freeze`
â†’ `cce8d0dfe9e2564c947c3bb727504d54a53d5ba8`

P11-TAM-B through P11-TAM-F remain predecessor capabilities.

## Canonical evidence boundary

P11-TAM-G consumes exactly:

- `Principal`;
- `AuthorityCheck`;
- `AuthorityGrant`.

These are the canonical passive authority-model objects already used by the
runtime and semantic-lattice interoperability layers.

The boundary follows the existing semantic-lattice distinction:

- `Principal` owns a canonical authority subject identity through `Principal.id`;
- `AuthorityCheck` owns a canonical authority subject identity through
  `AuthorityCheck.id`;
- `AuthorityGrant` is ID-less evidence and must not receive a fabricated
  subject identity.

## AIR ownership remains separate

P11-TAM-G deliberately does not absorb:

- `AIRAuthority`;
- `AIRPrincipal`;
- `AIRRole`;
- `PrincipalAuthority`;
- `PrincipalRole`;
- `AIRRoleAuthority`;
- `DirectiveAuthority`;
- `DirectiveRequirement`.

Those are AIR-owned source/declaration structures. Existing semantic-lattice
projection already treats AIR authority/principal/role values as source-domain
`air` subjects rather than `authority.model` subjects.

TAM may connect AIR and authority evidence in a later graph-composition slice,
but P11-TAM-G does not duplicate AIR ownership.

## Production API

P11-TAM-G introduces:

- `trace_record_from_authority_evidence(evidence, evidence_index=...)`;
- `trace_map_from_authority_evidence(evidence)`.

The map producer requires an exact tuple and preserves input order.

## Principal subject boundary

A `Principal` record uses:

- domain: `authority`;
- producer/owner: `authority.model`;
- representation: `principal`;
- canonical identity: the existing `Principal.id`.

The TAM-local trace identity is based on the principal's canonical ID.

`display_name`, `roles`, and `authorities` are not reinterpreted by this slice.
That deliberately matches the existing passive subject-projection boundary:
P11-TAM-G records the authority subject identity and does not perform role or
effective-authority resolution.

## Authority check evidence

An `AuthorityCheck` record uses:

- domain: `authority`;
- producer/owner: `authority.model`;
- representation: `authority-check`;
- canonical identity: the existing `AuthorityCheck.id`.

Its TAM-local trace identity also preserves the already-supplied:

- principal;
- capability;
- resource.

TAM does not evaluate the check.

## Authority grant evidence

An `AuthorityGrant` record uses:

- domain: `authority`;
- producer/owner: `authority.model`;
- representation: `authority-grant`;
- canonical identity: `None`.

Its deterministic TAM-local identity preserves exactly:

- principal;
- capability;
- resource.

This follows the existing invariant that an `AuthorityGrant` is evidence rather
than a canonically identified subject.

## Source and graph boundary

`authority.model` values do not themselves own source spans. TAM therefore
sets `source_span=None`.

P11-TAM-G introduces no upstream or downstream links. Cross-domain relation
construction remains a later explicit graph-composition concern.

## Forbidden authority behavior

`tam.production` must not construct or invoke:

- `AuthorityEngine`;
- `AuthorityRegistry`;
- `RoleRegistry`;
- authority-policy `check` / `allows`;
- capability resolution;
- authority inheritance resolution;
- role resolution;
- registry registration or lookup;
- authority or principal compilation;
- semantic-lattice authority adapters as an indirect executor.

Therefore:

- `AUTHORITY_CHECK_EXECUTION=NONE`;
- `AUTHORITY_GRANT_EXECUTION=NONE`;
- `AUTHORITY_POLICY_EVALUATION=NONE`;
- `AUTHORITY_INHERITANCE_RESOLUTION=NONE`;
- `ROLE_RESOLUTION=NONE`;
- `REGISTRY_LOOKUP=NONE`.

## Completion condition

P11-TAM-G is complete when:

- TAM-F freeze ancestry is proven;
- Principal, AuthorityCheck, and AuthorityGrant are projected;
- all records use the `authority` domain;
- Principal and AuthorityCheck preserve their existing canonical IDs;
- AuthorityCheck factual payload is preserved without evaluation;
- AuthorityGrant facts are preserved without fabricated canonical identity;
- Principal subject projection stays ID-only and does not resolve roles or
  effective authorities;
- AIR-owned authority structures remain outside the TAM-G production surface;
- input order and repeated projection are deterministic;
- no source span or graph edge is fabricated;
- no authority engine, policy, registry, inheritance, role resolution, or
  semantic execution occurs;
- frozen authority, AIR, semantic-lattice, type-system, and prior TAM owners
  remain unchanged;
- durable authority and TAM predecessor regressions remain green.