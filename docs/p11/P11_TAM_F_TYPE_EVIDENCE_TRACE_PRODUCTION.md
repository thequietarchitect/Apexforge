# P11-TAM-F â€” Type Evidence Trace Production

## Purpose

P11-TAM-F adds deterministic TAM projection for already-existing canonical
ApexForge type identities and already-produced type-system results.

The slice is observational. TAM does not infer, resolve, coerce, bind,
specialize, close, validate, or reflect types.

## Predecessor

P11-TAM-F begins from:

`afp-p11-tam-e-freeze`
â†’ `17eafc6784ec972dab02eee7f63779d72f700304`

P11-TAM-B through P11-TAM-E remain predecessor capabilities.

## Canonical evidence boundary

P11-TAM-F consumes only already-created instances of:

- `ApexType`;
- `ApexTypeConstraint`;
- `ApexTypeVariable`;
- `FunctionSignature`;
- `GenericSubstitution`;
- `GenericSpecialization`.

These objects remain owned by their existing `type_system.*` modules.

`GenericInstantiationTable` is not itself assigned a TAM subject identity in
this slice. Its canonical `records` order may supply already-produced
`GenericSpecialization` evidence to TAM.

`GenericSpecializationManifest` and dependency closure are excluded from this
slice. They contain linked specialization dependency structure and belong to a
later ownership/transformation trace decision rather than the minimum
canonical type-evidence boundary.

`P9FreezeManifest`, `P9FreezeAudit`, and `RuntimeTypeInfo` are also excluded.
They are release-audit or runtime/standard-library reflection structures, not
compiler type evidence owned by TAM.

## Production API

P11-TAM-F introduces:

- `trace_record_from_type_evidence(evidence, evidence_index=...)`;
- `trace_map_from_type_evidence(evidence)`.

The record producer accepts only the six canonical evidence classes listed
above. Strings such as `"int"` are not accepted because accepting type-like
input would require TAM to resolve it.

## Type-domain mapping

Every P11-TAM-F record uses the existing canonical TAM `type` domain.

Representations are:

- `ApexType` â†’ `apex-type`;
- `ApexTypeConstraint` â†’ `apex-type-constraint`;
- `ApexTypeVariable` â†’ `apex-type-variable`;
- `FunctionSignature` â†’ `function-signature`;
- `GenericSubstitution` â†’ `generic-substitution`;
- `GenericSpecialization` â†’ `generic-specialization`.

Producer and owner names preserve the frozen module that owns each object.

## Structural identity preservation

TAM-local trace identity includes the existing factual structure of the
observed object.

For `ApexType`, that includes the type name and recursively ordered arguments.

For `ApexTypeConstraint`, it includes name and description.

For `ApexTypeVariable`, it includes name, owner, and the already-normalized
constraint tuple.

For `FunctionSignature`, it includes name, ordered parameter types, optional
return type, and ordered type parameters.

For `GenericSubstitution`, it includes the already-normalized ordered binding
tuple. TAM does not call `bind` or `resolve`.

For `GenericSpecialization`, it includes the existing specialization key,
type arguments, ordered parameter types, and optional return type. TAM does
not call `resolve_call_specialization`.

## Canonical identity field boundary

`TraceRecord.canonical_identity` remains `None` for P11-TAM-F records.

The observed type-system objects are canonical structural identities and
results, but they do not expose one uniform existing AIR-style canonical-ID
string suitable for that field. TAM therefore preserves their full factual
structure in its own deterministic `TraceIdentity` instead of inventing a
new canonical string identity.

## Source boundary

These type-system values do not themselves own a `SourceSpan`.

P11-TAM-F therefore sets `source_span=None`.

A later composition slice may connect type evidence to source/declaration
traces only when an existing owner supplies that relationship explicitly.

## Deterministic ordering

`trace_map_from_type_evidence` requires an exact tuple and preserves that tuple
order.

When a caller supplies `GenericInstantiationTable.records`, that order has
already been canonically normalized by the type-system owner. TAM merely
observes the resulting specializations.

## Forbidden operations

`tam.production` must not call:

- `resolve_builtin_type`;
- `resolve_type`;
- `resolve_type_constraint`;
- `infer_expression_type`;
- `infer_expression_type_partial`;
- `infer_call_substitution`;
- `infer_explicit_call_substitution`;
- `resolve_call_specialization`;
- constraint-satisfaction functions;
- `GenericSubstitution.bind`;
- `GenericSubstitution.resolve`;
- `collect_linked_specializations`;
- `LinkedSpecializationCollector`;
- `audit_lowered_generics`;
- runtime type-reflection helpers.

Therefore:

- `TYPE_INFERENCE=NONE`;
- `TYPE_RESOLUTION=NONE`;
- `TYPE_COERCION=NONE`;
- `CONSTRAINT_EVALUATION=NONE`;
- `GENERIC_BINDING_EXECUTION=NONE`;
- `SPECIALIZATION_RESOLUTION=NONE`;
- `CLOSURE_COMPUTATION=NONE`;
- `RUNTIME_TYPE_REFLECTION=NONE`.

## Authority boundary

Authority evidence remains reserved for P11-TAM-G.

P11-TAM-F imports no authority model or engine and makes no authority
decision.

## Graph boundary

P11-TAM-F introduces no upstream or downstream TAM graph edges. This slice
first freezes direct type evidence projection. Cross-domain graph composition
requires explicit edge ownership in a later slice.

## Completion condition

P11-TAM-F is complete when:

- TAM-E freeze ancestry is proven;
- all six canonical type-evidence classes are projected into the `type` domain;
- nested structural type identity is preserved;
- constraint and generic-variable factual identity is preserved;
- existing substitution and specialization results are observed without
  recomputation;
- input order is deterministic and preserved;
- no string canonical identity or source span is fabricated;
- no graph links are inferred;
- no type resolution, inference, coercion, constraint evaluation, generic
  binding, specialization resolution, closure computation, or runtime
  reflection occurs;
- frozen type-system and prior semantic owners remain unchanged;
- durable type-system and TAM predecessor regressions remain green.