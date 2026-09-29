# P12.5-RCV-33 Recovered Managed Executable Carrier Derivation Mapping Census

RCV-33 is audit-only.

RCV-32 selected canonical AIR transport as the logical derivation source. This gate inventories the structural correspondence between canonical AIR/type-system nodes and the managed executable carrier without authorizing a decoder or construction bridge.

The census identifies 18 concrete mapping candidates:

- 8 executable-expression mappings,
- 5 function/control-flow mappings,
- 3 type mappings,
- 2 constraint mappings.

The remaining 7 managed carrier declarations are topology-only abstract/interface surfaces rather than independently serialized source nodes:

- `ManagedExecutableExpression`
- `ManagedTypeReference`
- `ManagedGenericTypeLike`
- `ManagedTypeLike`
- `ManagedTypeIdentity`
- `ManagedConstraintReference`
- `ManagedFunctionStatement`

The candidate mappings preserve the canonical structure while allowing only representation-level container normalization such as Python tuples to `IReadOnlyList<T>` and snake_case field names to corresponding PascalCase managed properties.

No mapping is authorized for production in this census. No decoder, transport, handoff coupling, execution, or dispatch is introduced.

Next gate: `P12.5-RCV-34 MANAGED EXECUTABLE CARRIER DERIVATION MAPPING CONTRACT`.
