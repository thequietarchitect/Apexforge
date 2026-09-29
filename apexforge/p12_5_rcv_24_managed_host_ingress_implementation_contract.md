# P12.5-RCV-24 Recovered Managed Host Ingress Implementation Contract

RCV-24 selects the narrowest recovery implementation contract consistent with the earlier `IN_PROCESS_API` decision.

Historical evidence names `ApexForge.Runtime.Host.RuntimeHostIngress`, but does not preserve the original implementation body, constructor shape, method name, or lifecycle coupling. This contract therefore makes a recovery-selected choice without claiming historical identity equivalence.

## Selected contract

`RuntimeHostIngress` will be a sealed in-process adapter owned by `ApexForge.Runtime.Host`.

It will:

- receive an existing `ApexForge.Runtime.ManagedRuntimeHost` through its constructor,
- reject a null runtime dependency,
- expose `Admit(TargetNeutralLoweringHandoff handoff)`,
- delegate directly to `ManagedRuntimeHost.AdmitTargetNeutralHandoff(handoff)`,
- return the delegate result unchanged.

The ingress adapter will not duplicate handoff validation. It gains no language-semantic, lowering, reinterpretation, transport, native-ABI, or execution authority.

Initial lifecycle coupling is explicitly `NONE_IN_INITIAL_IMPLEMENTATION`; lifecycle coordination may be considered later only through a separate gate.

External serialization remains unselected. Python-to-.NET runtime transport remains unauthorized. Execution dispatch remains deferred.

Next gate: `P12.5-RCV-25 MANAGED HOST INGRESS IMPLEMENTATION FOUNDATION`.
