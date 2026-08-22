# P11.15H â€” Narrative-Session Fingerprint Delegation

## Status

Production integration stage following frozen P11.15G.

Predecessor:

- P11.15G freeze commit:
  `8605f06c276e9ba4e737bc0de26bb5b89dd0439f`
- annotated predecessor tag:
  `afp-p11-15g-freeze`

## Scope

P11.15H modifies exactly one existing production file:

```text
apexforge/tooling/narrative_session.py
```

It introduces no new production module and no new public API.

## Required integration

Add explicit imports:

```python
from interoperability.build_artifact import BuildArtifactInterchange
from interoperability.build_artifact_integrity import (
    verify_build_artifact_interchange_fingerprint,
)
```

Do not import or call:

```python
inspect_build_artifact_interchange
```

After the existing session-owned outer build-artifact v1/v2 schema and shape
policy, replace the local fingerprint verification block with:

```python
artifact_fingerprint = verify_build_artifact_interchange_fingerprint(
    BuildArtifactInterchange(
        schema=schema,
        content=content,
    )
)
```

The return value is retained.

When constructing `NarrativeSessionMaterial`, use:

```python
artifact_fingerprint=artifact_fingerprint,
```

rather than the old local mapping expression.

## Import cleanup

Remove:

```python
import hashlib
```

because it is used only by the local build-artifact fingerprint block.

Retain:

```python
BUILD_ARTIFACT_FINGERPRINT_ALGORITHM
canonical_json_bytes
```

because both have session-owned uses outside this integration.

## Required preserved ordering

1. path read and JSON decoding;
2. `_read_json` canonical outer-byte enforcement;
3. session-owned outer shape/schema policy;
4. D fingerprint verification;
5. unavailable narrative routing;
6. session-owned nested narrative reconstruction;
7. frozen F `load_narrative_execution_material` call;
8. artifact-change/story agreement;
9. `NarrativeSessionMaterial` construction.

## Required schema behavior

Outer build artifacts remain:

- v1 accepted under historical/integrated shape policy;
- v2 accepted under native narrative shape policy;
- outer v3 rejected;
- unknown outer schemas rejected.

Nested narrative v3 remains supported and is distinct from outer build-artifact
v3.

## Required error behavior

D fingerprint shape/integrity errors remain wrapped by the session reader as:

```python
NarrativeSessionError("malformed_build_artifact")
```

with the D error retained as the cause:

- `build artifact fingerprint shape mismatch`
- `build artifact fingerprint mismatch`

Historical outer v1 without narrative remains
`unavailable_narrative_material` after successful D verification.

## Frozen execution-reader ownership

P11.15H must preserve:

```python
bindings = load_narrative_execution_material(artifact_path)
```

The F reader performs its own D verification.  Therefore double D verification
of the same artifact is expected after H and is not grounds for coupling the
two readers or removing either ownership boundary.

## Non-goals

P11.15H does not:

- mutate B or D;
- mutate the frozen F execution reader;
- broaden outer schema acceptance;
- change nested narrative schemas;
- change session APIs;
- change CLI/editor/runtime/agents/effects/Quad-Vector;
- add network/RPC/FFI/native/ABI behavior.