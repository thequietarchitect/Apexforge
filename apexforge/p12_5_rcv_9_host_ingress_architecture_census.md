# P12.5-RCV-9 Recovered Host Ingress Architecture Census

RCV-9 is an audit-only slice. It inventories the existing host and runtime surfaces before any concrete ingress mechanism is selected.

Canonical AIR remains the language-semantic authority. `ApexForge.Runtime.Host` remains an orchestration/lifecycle shell and may not redefine language meaning.

The census considers four narrow ingress families for a later decision:

- command-line arguments
- standard input
- file path
- in-process API

RCV-9 does **not** choose among them.

Network listeners, HTTP servers, socket servers, named pipes, direct native dispatch, new external serialization, managed executable-carrier behavior, and execution dispatch remain outside this slice.

The census must confirm that the RCV-8 lifecycle implementation still builds and executes, that no premature ingress/dispatch surface has appeared, and that the P12.2 target-neutral lowering boundary remains present.

Next gate: `P12.5-RCV-10 HOST INGRESS CONTRACT DECISION`.
