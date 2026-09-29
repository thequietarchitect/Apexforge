# P12.5-RCV-29 Recovered Managed Executable Carrier Corrected Type-Shape Contract

RCV-29 converts the RCV-28 historical census into a corrected implementation contract.

The recovered R1 materialization is not restored byte-for-byte because it was not build-valid. Three documented transcription defects are resolved:

1. `IjeadOnlyList<ManagedGenericTypeLike>` -> `IReadOnlyList<ManagedGenericTypeLike>`
2. `IjeadOnlyList<ManagedConstraintReference>` -> `IReadOnlyList<ManagedConstraintReference>`
3. smoke-side `ManagedUnharyExpression` -> `ManagedUnaryExpression`

No other shape change is authorized by this gate.

The corrected carrier contract contains exactly 25 declarations in `ApexForge.Runtime`, preserving the recovered expression graph, type graph, constraint graph, statement graph, and executable-function record.

Key scalar representation remains:

- integer: `System.Numerics.BigInteger`
- floating point: `double` / IEEE-754 binary64
- string: `string`
- boolean: `bool`
- collections: `IReadOnlyList<T>`

This carrier is a data representation surface only. It may not serialize, execute, dispatch, call native ABI, admit target-neutral handoffs, or become a second language-semantic implementation.

`ManagedExecutableCarrier.cs` is still absent at this contract gate.

Next gate: `P12.5-RCV-30 MANAGED EXECUTABLE CARRIER IMPLEMENTATION FOUNDATION`.
