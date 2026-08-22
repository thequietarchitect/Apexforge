# P11.15E â€” Narrative-Execution Fingerprint Delegation Architecture Boundary

## Status

Architecture-only integration boundary following frozen P11.15D.

Frozen predecessor:

- P11.15D commit: `8525d6e4a0b9b35dda5e06af6b5e1289fd39a2ac`
- annotated tag: `afp-p11-15d-freeze`

P11.15E introduces no production changes.

## Audit conclusion

P11.15D now owns the generic passive build-artifact fingerprint integrity
primitive:

```text
interoperability.build_artifact_integrity
```

Both narrative readers still duplicate that integrity operation, but their
surrounding policies are not identical.

The safer successor is therefore one-consumer-at-a-time integration.

P11.15F is limited to:

```text
tooling.narrative_execution
```

`tooling.narrative_session` remains byte-frozen during F.

## Why narrative execution goes first

`load_narrative_execution_material` has the smaller integration boundary.

It performs, in order:

1. read/parse build artifact;
2. require canonical outer JSON bytes;
3. enforce exact consumer-owned top-level shape;
4. accept only build-artifact v1 or v2;
5. verify fingerprint envelope and hash;
6. reject historical v1 artifacts without narrative material;
7. reconstruct narrative bindings.

The fingerprint is used only for integrity verification.

The function does not retain the fingerprint after verification.

By contrast, `load_narrative_session_material` has a larger surrounding
reconstruction surface and later stores the verified fingerprint in
`NarrativeSessionMaterial`.

The two consumers therefore must not be coupled into one integration freeze.

## P11.15F exact production scope

F modifies exactly one existing production file:

```text
apexforge/tooling/narrative_execution.py
```

F adds no new production module.

F must not modify:

```text
apexforge/interoperability/__init__.py
apexforge/interoperability/build_artifact.py
apexforge/interoperability/build_artifact_integrity.py
apexforge/tooling/build_artifact.py
apexforge/tooling/narrative_session.py
apexforge/tooling/cli.py
apexforge/effects/host_execution.py
apexforge/quad_vector/execution.py
apexforge/agents/execution.py
apexforge/runtime/state.py
```

## F integration imports

F imports exactly the existing frozen interoperability types/functions it
needs:

```python
from interoperability.build_artifact import BuildArtifactInterchange
from interoperability.build_artifact_integrity import (
    verify_build_artifact_interchange_fingerprint,
)
```

F must not import or call:

```text
inspect_build_artifact_interchange
```

The B inspector is a generic schema recognizer supporting v1, v2, and v3.
Calling it as the narrative-execution entry policy would risk replacing the
consumer's narrower accepted-schema/error-order contract.

## Existing consumer policy remains authoritative

Before delegation, `load_narrative_execution_material` must continue to:

1. parse the artifact using its existing read path;
2. require exact canonical JSON outer bytes;
3. compute its existing top-level `keys`;
4. obtain its existing `schema`;
5. accept `BUILD_ARTIFACT_SCHEMA` under the existing historical/integrated key
   policy;
6. accept `BUILD_ARTIFACT_SCHEMA_V2` only under the existing native narrative
   key policy;
7. reject every other schema through the existing
   `"build artifact shape or schema mismatch"` path.

Only after those checks may F construct:

```python
BuildArtifactInterchange(
    schema=schema,
    content=content,
)
```

Therefore frozen B/D support for build-artifact v3 must not broaden
`load_narrative_execution_material`.

Build-artifact v3 remains rejected by narrative execution exactly as before.

## Exact fingerprint delegation

F replaces only the duplicated fingerprint block:

```python
fingerprint = _mapping(
    value["fingerprint"],
    frozenset(("algorithm", "value")),
)
if (
    fingerprint["algorithm"]
    != BUILD_ARTIFACT_FINGERPRINT_ALGORITHM
    or type(fingerprint["value"]) is not str
):
    raise ValueError("build artifact fingerprint shape mismatch")
payload = dict(value)
del payload["fingerprint"]
expected = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
if fingerprint["value"] != expected:
    raise ValueError("build artifact fingerprint mismatch")
```

with:

```python
verify_build_artifact_interchange_fingerprint(
    BuildArtifactInterchange(
        schema=schema,
        content=content,
    )
)
```

The return value is intentionally ignored.

Narrative execution needs verification, not fingerprint retention.

## Error-order preservation

F must preserve this order:

```text
read/JSON errors
canonical outer-byte error
consumer top-level shape/schema errors
fingerprint shape error
fingerprint mismatch error
historical narrative-unavailable routing
narrative reconstruction errors
```

The call to D therefore occurs only after canonical-byte and shape/schema
policy and before historical-material routing/reconstruction.

## Error-message preservation

For artifact cases that reach fingerprint verification, D already uses the
same two fingerprint error messages:

```text
build artifact fingerprint shape mismatch
build artifact fingerprint mismatch
```

F must prove those remain the reachable causes beneath the existing
`NarrativeExecutionRoutingError("malformed_build_material")` wrapper.

No new user-visible routing classification is introduced.

## Accepted schema preservation

Narrative execution currently accepts outer build-artifact:

```text
v1
v2
```

only.

F must prove:

```text
v1 behavior unchanged
v2 behavior unchanged
v3 remains rejected
unknown schemas remain rejected
```

D's broader generic v1/v2/v3 support must remain subordinate to the consumer.

## Canonical-byte preservation

Narrative execution currently rejects a non-canonical outer JSON encoding
before fingerprint verification:

```python
if content != canonical_json_bytes(value):
    raise ValueError("build artifact is not canonical JSON")
```

F must leave this exact consumer policy in place and before D delegation.

D itself intentionally allows non-canonical outer bytes; F must not expose
that broader D behavior through narrative execution.

## Top-level shape preservation

F must leave the existing exact key policies unchanged:

```text
historical_keys
integrated_keys
native_narrative_keys
```

D does not replace these checks.

## Historical behavior preservation

A valid historical v1 artifact with no `narrative` field must still have its
fingerprint verified first and then raise:

```text
NarrativeExecutionRoutingError("unavailable_narrative_material")
```

F must not move historical-material routing before integrity verification.

## Reconstruction preservation

F must leave:

```python
return _narrative_bindings(value["narrative"])
```

and all narrative-artifact reconstruction behavior unchanged.

D performs no reconstruction.

## Import cleanup

After exact delegation:

```text
hashlib
BUILD_ARTIFACT_FINGERPRINT_ALGORITHM
```

are no longer needed by `tooling.narrative_execution` and should be removed if
the F RED/implementation audit confirms they have no other uses.

`canonical_json_bytes` remains required by narrative execution for canonical
outer-byte enforcement and result serialization.

`BUILD_ARTIFACT_SCHEMA` and `BUILD_ARTIFACT_SCHEMA_V2` remain required for the
consumer's own schema policy.

## No public API expansion

F introduces no new public narrative-execution function, record, class, or
package export.

This is dependency delegation inside the existing
`load_narrative_execution_material` implementation.

## F acceptance requirements

F must prove:

1. P11.15E architecture freeze ancestry;
2. D/B production bytes unchanged;
3. narrative session bytes unchanged;
4. only `tooling.narrative_execution` changes in production;
5. no new public narrative-execution API;
6. `BuildArtifactInterchange` imported from its explicit module;
7. D verifier imported from its explicit module;
8. B inspector is not imported or called;
9. canonical outer-byte check remains exact and before delegation;
10. historical/integrated/native top-level key policies remain exact;
11. outer build-artifact v1 remains accepted under existing policy;
12. outer build-artifact v2 remains accepted under existing policy;
13. outer build-artifact v3 remains rejected;
14. unknown outer schema remains rejected;
15. D is called only after the consumer's schema/shape checks;
16. duplicated local fingerprint envelope/hash block is removed;
17. fingerprint-shape failure preserves the same routing classification and
    underlying message;
18. fingerprint-hash mismatch preserves the same routing classification and
    underlying message;
19. non-canonical outer bytes preserve the same routing classification and
    `"build artifact is not canonical JSON"` cause;
20. historical no-narrative behavior remains
    `"unavailable_narrative_material"` after fingerprint verification;
21. valid narrative bindings are unchanged;
22. narrative reconstruction logic remains consumer-owned;
23. D return value is not retained;
24. `hashlib` is removed if no other use remains;
25. `BUILD_ARTIFACT_FINGERPRINT_ALGORITHM` is removed if no other use remains;
26. `canonical_json_bytes` remains;
27. no narrative-session integration occurs;
28. no CLI/editor/runtime/agent/effect/QV integration occurs;
29. no file/network/RPC expansion occurs;
30. no FFI/native/ABI surface occurs.

## Post-F discipline

After F is frozen, P11.15G must audit `tooling.narrative_session` independently.

G must not assume the session integration is safe merely because narrative
execution successfully delegated.

In particular it must account for session material retaining the verified
fingerprint and for its separate read/canonicality helper behavior.

Every successor remains architecture-first.