# P11.15G â€” Narrative-Session Fingerprint Delegation Architecture Boundary

## Status

Architecture boundary only.

P11.15G freezes the evidence and successor contract for a later
**P11.15H production integration**.  P11.15G changes no production file.

Predecessor:

- P11.15F freeze commit:
  `8cf8f04a9dde2a7473c2030599b52e3658edac02`
- annotated predecessor tag:
  `afp-p11-15f-freeze`

## Why a separate session boundary is required

`tooling.narrative_session` is not structurally equivalent to
`tooling.narrative_execution`.

The session reader:

1. uses `_read_json(... require_canonical=True)` by default;
2. applies its own outer build-artifact v1/v2 shape and schema policy;
3. performs a local build-artifact fingerprint verification;
4. rejects unavailable narrative material;
5. reconstructs session-owned narrative identity/scene material;
6. calls the independently frozen narrative-execution reader to reconstruct
   executable bindings;
7. retains the verified build-artifact fingerprint in
   `NarrativeSessionMaterial`;
8. uses that retained fingerprint for later session/material association.

Therefore P11.15H must preserve session ownership and cannot simply copy the F
integration mechanically.

## Frozen current evidence

### Canonical outer-byte policy

`_read_json` has:

```python
require_canonical: bool = True
```

and enforces:

```python
if require_canonical and content != canonical_json_bytes(value):
    raise ValueError("JSON is not canonical")
```

`load_narrative_session_material` omits the `require_canonical` keyword.
Therefore the effective session policy is canonical outer bytes **before**
session-owned build-artifact schema/fingerprint policy.

P11.15H must not move D verification ahead of this policy.

### Outer build-artifact schema policy

The session reader accepts exactly:

- `BUILD_ARTIFACT_SCHEMA`
- `BUILD_ARTIFACT_SCHEMA_V2`

Outer `BUILD_ARTIFACT_SCHEMA_V3` is not imported or used by this owner and
continues to be rejected by the existing `else` branch.

### Nested narrative v3 is distinct

The session reader independently supports:

- `NARRATIVE_BUILD_ARTIFACT_SCHEMA_V1`
- `NARRATIVE_BUILD_ARTIFACT_SCHEMA`
- `NARRATIVE_BUILD_ARTIFACT_SCHEMA_V3`

Nested narrative v3 support must not be mistaken for outer build-artifact v3
support and must remain unchanged.

### Fingerprint retention

The current local build-artifact fingerprint verification produces
`fingerprint["value"]`, which is passed into:

```python
NarrativeSessionMaterial(
    artifact_fingerprint=fingerprint["value"],
    ...
)
```

Later session/material association compares:

```python
session.artifact_fingerprint != material.artifact_fingerprint
```

The verified fingerprint is therefore semantic session association data, not a
discardable verification side effect.

### F execution-reader interaction

The session reader calls:

```python
bindings = load_narrative_execution_material(artifact_path)
```

That call is owned by the frozen F narrative-execution boundary and must remain.

After P11.15H, the same canonical artifact will normally be verified by D:

1. once in the session reader; and
2. again in the frozen execution reader.

That double verification is expected.  P11.15H must not remove the execution
reader call, share reconstructed mappings, couple the two readers, or widen
their independent ownership boundaries merely to avoid repeated verification.

## Frozen P11.15H production contract

### Production scope

Exactly one existing production file:

```text
apexforge/tooling/narrative_session.py
```

No new production module.

No change to:

- `interoperability.build_artifact`;
- `interoperability.build_artifact_integrity`;
- `tooling.narrative_execution`;
- CLI/editor/runtime;
- agents;
- effects;
- Quad-Vector;
- network/RPC;
- FFI/native/ABI.

### Imports

P11.15H may add explicit imports:

```python
from interoperability.build_artifact import BuildArtifactInterchange
from interoperability.build_artifact_integrity import (
    verify_build_artifact_interchange_fingerprint,
)
```

P11.15H must not import or call:

```python
inspect_build_artifact_interchange
```

### Exact delegation shape

After the existing session outer v1/v2 schema/shape policy, replace the local
build-artifact fingerprint block with:

```python
artifact_fingerprint = verify_build_artifact_interchange_fingerprint(
    BuildArtifactInterchange(
        schema=schema,
        content=content,
    )
)
```

The D return value is intentionally retained.

### Material construction

Replace:

```python
artifact_fingerprint=fingerprint["value"],
```

with:

```python
artifact_fingerprint=artifact_fingerprint,
```

The retained value must be the exact verified declared fingerprint returned by
D.

### Import cleanup

`hashlib` is used only by the local build-artifact fingerprint block and may be
removed after delegation.

`BUILD_ARTIFACT_FINGERPRINT_ALGORITHM` must remain because
`tooling.narrative_session` has session-owned uses outside this block.

`canonical_json_bytes` must remain because the module has session-owned uses
outside this block, including canonical JSON handling.

### Required error/order preservation

P11.15H must preserve the existing effective order:

1. path read / JSON decoding;
2. canonical outer-byte policy;
3. session top-level shape and outer schema policy;
4. D fingerprint shape/integrity verification;
5. unavailable narrative routing;
6. session-owned narrative reconstruction;
7. frozen F execution-reader reconstruction;
8. final artifact-change/story agreement check;
9. `NarrativeSessionMaterial` construction.

D failures remain inside the existing session
`except (KeyError, TypeError, ValueError)` route and therefore must continue to
surface through:

```python
NarrativeSessionError("malformed_build_artifact")
```

with the underlying D cause preserving:

- `build artifact fingerprint shape mismatch`
- `build artifact fingerprint mismatch`

The existing unavailable narrative route must remain after successful D
verification.

## Explicit non-goals

P11.15H does not:

- broaden outer build-artifact schema acceptance;
- accept outer v3;
- change nested narrative schema support;
- remove canonical outer-byte enforcement;
- use the B inspector as consumer policy;
- reconstruct a build artifact generically;
- remove the frozen F execution-reader call;
- coalesce session and execution reconstruction;
- alter public session APIs;
- introduce network/RPC/plugin/FFI/native/ABI surfaces.

## Successor

After this architecture boundary is frozen, the next production stage is:

**P11.15H â€” narrative-session fingerprint delegation**.

P11.15G itself remains architecture-only.