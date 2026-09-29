# P12.5-RCV-6 Recovered Dedicated Managed Runtime Host Project Skeleton

RCV-6 adds the dedicated `ApexForge.Runtime.Host` executable project required by the frozen RCV-5 topology contract.

The host is additive and references `ApexForge.Runtime`; it does not replace `ManagedRuntimeHost`, own language semantics, duplicate `ManagedNativeAbi`, select ingress or serialization, reconstruct the target-neutral handoff, or enable execution dispatch.

The executable skeleton only constructs the existing `ManagedRuntimeHost` and reports its existing runtime identity.

Deferred after RCV-6: host ingress, external serialization, target-neutral handoff reconstruction, managed executable carrier, native host, and execution dispatch.

Next gate: `P12.5-RCV-7 HOST LIFECYCLE AND STARTUP CONTRACT`.
