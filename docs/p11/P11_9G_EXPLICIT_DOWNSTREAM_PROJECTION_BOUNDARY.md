# P11.9G - Explicit Downstream Projection Boundary

## Status

Production passive downstream-projection boundary layered over the frozen P11.9F validation contracts.

## Purpose

P11.9G introduces an immutable explicit projection record from already-validated AETHER-AIR state toward a caller-declared downstream consumer.

The projection preserves the exact P11.9F validation receipt as structural evidence. It does not construct Optimized AIR, construct a Native Backend representation, lower semantics, optimize behavior, compile, emit code, serialize an executable artifact, execute behavior, or choose a backend.

## Canonical implementation

The implementation lives in `apexforge/aether_air/projection.py` and exports only:

- `AetherAirDownstreamProjection`
- `project_validated_aether_air`

These symbols are re-exported through `apexforge/aether_air/__init__.py`.

## Projection record

`AetherAirDownstreamProjection` contains exactly:

- `validation`
- `consumer`
- `provenance`

The record is frozen.

`validation` must be an exact `AetherAirValidationReceipt` or exact `AetherAirTransformationValidationReceipt`. The exact supplied receipt object is preserved. P11.9G does not reconstruct or revalidate its canonical AETHER-AIR state.

`consumer` is an exact non-empty trimmed string supplied explicitly by the caller. It describes a downstream consumer boundary only.

`provenance` is an exact tuple of non-empty trimmed strings preserved in caller encounter order.

## Open consumer boundary

Consumer labels remain open descriptive metadata. Values such as `optimized-air` and `native-backend` may identify intended downstream consumer categories, but P11.9G does not establish a closed backend registry or dispatch table.

A consumer label does not load a provider, select an implementation, choose a code generator, grant backend capability, or prove that a downstream implementation exists.

## Projection intent is not dispatch

The frozen P11.9B `projection.intent` behavior kind remains behavioral-intent data.

P11.9G does not infer the `consumer` field from `projection.intent`, behavior text, parameters, predecessor metadata, provenance, validation checks, transformation operation labels, encounter order, or any other canonical metadata.

An explicit caller-supplied consumer remains authoritative only for describing the projection boundary. It is not semantic or executable authority.

## Exact validation-receipt preservation

P11.9G consumes an already-produced P11.9F receipt.

It does not call `validate_aether_air_snapshot` or `validate_aether_air_transformation`.

For a snapshot validation receipt, the exact receipt continues to own access to the validated snapshot, extension-kind IDs, provenance, and completed checks.

For a transformation validation receipt, the exact receipt continues to own access to the frozen P11.9E transformation and its source/result validation receipts. This preserves transformation context across the downstream boundary without copying or replacing it.

## Determinism and identity

Equivalent explicit projection inputs produce equivalent passive projection values.

Projection preserves exact validation-receipt identity and caller provenance encounter order.

P11.9G does not sort, rank, merge, deduplicate, rewrite, clone, replace, normalize, repair, or reinterpret the validated AETHER-AIR objects reachable through the receipt.

## Projection is not lowering

P11.9G projection means a passive declaration that validated AETHER-AIR state is being presented toward an explicitly named downstream consumer.

It is not:

- Optimized AIR construction;
- Native Backend construction;
- AIR rewriting;
- optimization;
- instruction selection;
- backend selection;
- code generation;
- compilation;
- emission;
- executable serialization;
- runtime loading;
- runtime execution.

Actual lowering, optimization, backend representation, code generation, and execution remain owned by later downstream stages.

## Serialization boundary

`AetherAirDownstreamProjection` is an in-memory immutable semantic boundary record.

P11.9G defines no JSON schema, binary format, persistent wire format, build artifact, import format, object file, executable format, or backend serialization contract.

A later owner must introduce any such representation explicitly.

## P11.10 boundary

P11.9G does not evaluate advanced conditionals, select branches, rank alternatives, perform convergence, recompute Quad-Vector resultants, convert metadata into operative precedence, or create Paradox Elevation semantics.

A consumer label and projection encounter order never become P11.10 selection or convergence inputs merely because they exist.

## Non-operative boundary

The projection record exposes no execute, run, bind, resolve, select, rank, converge, grant, deny, synchronize, normalize, transform, lower, optimize, compile, emit, serialize, load, import, mutate, or repair methods.

P11.9G gains no parser ownership, AIR verifier/linker authority, authority-policy power, narrative execution ownership, Quad-Vector resultant-resolution ownership, Parametric Semantic Lattice mutation ownership, runtime state mutation, CLI authority, provider-loading privilege, dynamic-import privilege, backend code-generation authority, or Codex privilege.

## Frozen predecessor preservation

P11.9G layers over the frozen P11.9B model, P11.9C records, P11.9D construction, P11.9E transformation, and P11.9F validation surfaces without changing their record shapes or established behavior.

## Compatibility invariant

Existing AIR, authority, narrative, Quad-Vector, Parametric Semantic Lattice, runtime, compiler, tooling, serialization, and backend behavior remains unchanged.

## Next stage

P11.9H may add reporting, tooling, and traceability surfaces over frozen P11.9G projection records without turning those records into executable backend artifacts or resolver authority.

P11.9I may then perform final P11.9 integration regression and freeze over the completed AETHER-AIR stack.
