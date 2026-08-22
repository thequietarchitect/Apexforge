# P11.15F â€” Narrative-Execution Fingerprint Delegation

## Status

RED contract following frozen P11.15E.

Frozen predecessor:

- P11.15E commit: `99253c16939299a7f8a6ad209772a5038c8ca28e`
- annotated tag: `afp-p11-15e-freeze`

RED introduces no production changes.

## Exact production target

GREEN modifies exactly one existing production file:

```text
apexforge/tooling/narrative_execution.py
```

No new production module is introduced.

`tooling.narrative_session` remains byte-identical to its P11.15E baseline.

## Exact integration

GREEN imports:

```python
from interoperability.build_artifact import BuildArtifactInterchange
from interoperability.build_artifact_integrity import (
    verify_build_artifact_interchange_fingerprint,
)
```

GREEN must not import or call:

```text
inspect_build_artifact_interchange
```

The generic B inspector is not the narrative-execution schema-policy owner.

## Exact delegation location

Inside:

```text
load_narrative_execution_material
```

the current sequence remains:

```text
read/parse
canonical outer-byte check
consumer top-level key policy
consumer outer schema policy (v1/v2 only)
D fingerprint delegation
historical unavailable routing
narrative reconstruction
```

Only the local fingerprint envelope/hash block is replaced.

## Exact GREEN replacement

The current local block beginning with:

```python
fingerprint = _mapping(
```

and ending with:

```python
if fingerprint["value"] != expected:
    raise ValueError("build artifact fingerprint mismatch")
```

is removed.

In its place:

```python
verify_build_artifact_interchange_fingerprint(
    BuildArtifactInterchange(
        schema=schema,
        content=content,
    )
)
```

The return value is ignored.

## Preserved canonical outer-byte policy

This remains before delegation:

```python
if content != canonical_json_bytes(value):
    raise ValueError("build artifact is not canonical JSON")
```

D's more permissive outer-byte policy must not become reachable through
narrative execution.

## Preserved top-level shape and schema policy

These remain consumer-owned and unchanged:

```text
historical_keys
integrated_keys
native_narrative_keys
```

Narrative execution continues to accept only outer build-artifact:

```text
v1
v2
```

Outer v3 remains rejected by the existing:

```text
build artifact shape or schema mismatch
```

path before D is called.

Unknown schemas likewise remain rejected before D is called.

## Preserved fingerprint failures

For inputs that pass canonical/shape/schema policy and reach D:

```text
build artifact fingerprint shape mismatch
build artifact fingerprint mismatch
```

remain the exact underlying `ValueError` messages wrapped by:

```text
NarrativeExecutionRoutingError("malformed_build_material")
```

## Preserved historical routing

A valid historical v1 artifact with no `narrative` field must:

1. pass D integrity verification;
2. then raise `NarrativeExecutionRoutingError("unavailable_narrative_material")`.

Integrity verification must not move after historical routing.

## Preserved reconstruction

The existing:

```python
return _narrative_bindings(value["narrative"])
```

remains consumer-owned and after integrity verification.

No narrative reconstruction moves into interoperability.

## Import cleanup

Because the local fingerprint implementation is removed, GREEN removes:

```python
import hashlib
```

and removes:

```text
BUILD_ARTIFACT_FINGERPRINT_ALGORITHM
```

from the `tooling.build_artifact` import list, provided their only
narrative-execution uses are the replaced block.

GREEN retains:

```text
canonical_json_bytes
BUILD_ARTIFACT_SCHEMA
BUILD_ARTIFACT_SCHEMA_V2
```

because narrative execution still owns canonical-byte and schema policy.

## No other integration

GREEN does not modify:

```text
tooling.narrative_session
tooling.cli
runtime
agents
effects
quad_vector
interoperability.build_artifact
interoperability.build_artifact_integrity
```

No file/network/RPC/native/FFI/ABI surface is introduced.

## RED expectation

Before GREEN, the F smoke test must fail specifically because
`tooling.narrative_execution` has not yet imported/used the D integration.

The intended first RED assertion is:

```text
P11.15F integration absent: missing BuildArtifactInterchange import
```

The existing local fingerprint block must still be present during RED.

## GREEN acceptance

GREEN must prove:

1. P11.15E freeze ancestry;
2. frozen B/D bytes unchanged;
3. narrative session bytes unchanged;
4. only `tooling.narrative_execution` changes in production;
5. explicit `BuildArtifactInterchange` import;
6. explicit D verifier import;
7. no B inspector import/call;
8. no new public narrative-execution API;
9. canonical outer-byte check remains before delegation;
10. top-level key policy remains unchanged;
11. v1 remains accepted by existing consumer policy;
12. v2 remains accepted by existing consumer policy;
13. v3 remains rejected before D;
14. unknown schema remains rejected before D;
15. exact D delegation occurs after schema/shape checks;
16. D return value is ignored;
17. local fingerprint `_mapping`/hash block is removed;
18. local `hashlib` import is removed;
19. local fingerprint-algorithm import is removed;
20. `canonical_json_bytes` remains;
21. fingerprint-shape cause text remains exact;
22. fingerprint-mismatch cause text remains exact;
23. non-canonical outer-byte cause remains exact and occurs before D;
24. invalid top-level shape occurs before D;
25. historical no-narrative routing remains after successful D verification;
26. narrative reconstruction remains consumer-owned;
27. narrative session remains byte-identical;
28. no CLI/runtime/agent/effect/QV integration;
29. no transport/RPC expansion;
30. no FFI/native/ABI expansion.

After F freeze, P11.15G independently audits narrative-session delegation.