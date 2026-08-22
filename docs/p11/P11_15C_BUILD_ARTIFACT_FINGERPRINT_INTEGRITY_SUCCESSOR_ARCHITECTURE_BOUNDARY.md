# P11.15C â€” Build-Artifact Fingerprint Integrity Successor Architecture Boundary

## Status

Architecture-only successor boundary following frozen P11.15B.

Frozen predecessor:

- P11.15B commit: `19f1e1cc00eb88da46e1968f4cb9dfa274f067f3`
- annotated tag: `afp-p11-15b-freeze`

P11.15C introduces no production module or integration.

## Audit conclusion

P11.15B itself has no production consumer.

The repository therefore does not justify:

- a generic build-artifact loader;
- a parsed Mapping retained by `BuildArtifactInterchange`;
- a generic reconstruction API;
- schema conversion or migration;
- a file-path loader;
- network/RPC transport;
- FFI/native integration.

However, the audit found one concrete duplicated interoperability concern in
existing production consumers.

Both:

```text
tooling.narrative_execution
tooling.narrative_session
```

independently perform the same outer build-artifact fingerprint integrity
operation:

1. require a fingerprint mapping with exactly `algorithm` and `value`;
2. require the canonical build-artifact fingerprint algorithm;
3. copy the parsed outer artifact mapping;
4. remove `fingerprint`;
5. compute SHA-256 over `canonical_json_bytes(payload)`;
6. compare the computed value to the declared fingerprint;
7. reject a mismatch.

That duplicated operation is not narrative semantics. It is an outer
build-artifact integrity rule shared by every existing build-artifact schema
writer.

This is sufficient evidence for one additional passive interoperability
primitive.

## Why D is not a consumer integration stage

The existing narrative readers also enforce domain-specific behavior around:

- exact outer field sets;
- narrative payload shape;
- canonical input bytes;
- narrative artifact reconstruction;
- session/execution-specific material.

Those responsibilities remain narrative-tooling-owned.

D therefore adds only the reusable integrity primitive.

Rewiring narrative readers to consume D is deferred to a later architecture
audit after D itself is frozen.

## Frozen B remains untouched

P11.15B remains byte-frozen:

```text
interoperability.__init__
interoperability.build_artifact
```

D must not modify either B production file.

## P11.15D owner

New explicit module:

```text
interoperability.build_artifact_integrity
```

The package root remains:

```python
__all__ = ()
```

No D symbol is re-exported from the package root.

## Exact D public surface

One function only:

```python
def verify_build_artifact_interchange_fingerprint(
    interchange: BuildArtifactInterchange,
) -> str:
    ...
```

Module export:

```python
__all__ = (
    "verify_build_artifact_interchange_fingerprint",
)
```

No new result record is justified.

## Input boundary

The function accepts one exact:

```text
BuildArtifactInterchange
```

Subclasses and other objects are rejected.

D does not accept:

- bytes directly;
- mappings;
- paths;
- file objects.

B remains the schema-inspection entry boundary.

## Content parsing

D re-parses `interchange.content` from exact bytes.

This is intentional because B retains no mutable mapping.

D requires:

1. UTF-8 decoding succeeds;
2. JSON decoding succeeds;
3. the decoded JSON is an object;
4. the object's exact string `schema` equals `interchange.schema`.

Direct construction of `BuildArtifactInterchange` can otherwise pair a
supported schema with unrelated bytes, so D must verify this internal
consistency before checking integrity.

## Fingerprint envelope

The outer object must contain `fingerprint`.

The value must be an exact `dict`.

Its exact key set must be:

```text
algorithm
value
```

No extra fingerprint fields are accepted.

The algorithm must equal the existing canonical constant:

```python
BUILD_ARTIFACT_FINGERPRINT_ALGORITHM
```

owned by `tooling.build_artifact`.

The fingerprint `value` must be an exact string.

D does not invent another fingerprint algorithm or identifier.

## Integrity computation

D copies the decoded outer object shallowly:

```python
payload = dict(value)
```

and removes only:

```text
fingerprint
```

It then computes:

```python
hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
```

using the existing canonical JSON function owned by `tooling.build_artifact`.

If the declared fingerprint differs from the computed fingerprint, D raises
`ValueError`.

On success D returns the declared fingerprint string.

## Why D returns `str`

Existing consumers use the verified fingerprint as identity/evidence.

Returning the exact declared string is sufficient.

A new record would add no information beyond:

- the already-held `BuildArtifactInterchange`;
- the verified fingerprint string.

Therefore no `BuildArtifactIntegrityRecord` is introduced.

## Schema coverage

Because the input must already be a valid `BuildArtifactInterchange`, D applies
to exactly B's supported outer schemas:

```text
apexforge.build-artifact/v1
apexforge.build-artifact/v2
apexforge.build-artifact/v3
```

D does not branch on schema generation.

The writer uses the same fingerprint algorithm and the same
`canonical_json_bytes(payload)` rule for all three generations.

## D is not full artifact validation

D does not validate:

- outer top-level field sets other than the fingerprint envelope;
- project shape;
- AIR shape;
- narrative shape;
- rich-document shape;
- package shape;
- semantic validity;
- runtime executability.

A correctly fingerprinted artifact can still be semantically or structurally
invalid for a specific consumer.

## D does not enforce canonical outer bytes

D verifies the fingerprint over the canonicalized payload after parsing.

It does not require:

```python
interchange.content == canonical_json_bytes(parsed_outer_object)
```

Canonical outer-byte enforcement remains a distinct consumer policy.

This avoids silently expanding fingerprint integrity into complete canonical
serialization validation.

## D performs no reconstruction

D returns no:

- AIRProgram;
- ProjectBuild;
- NarrativeBuildArtifact;
- RichDocumentProjectBuild;
- package object;
- runtime object.

## D performs no I/O or execution

D performs no:

- file read/write;
- network I/O;
- subprocess;
- runtime integration;
- host-effect execution;
- agent execution;
- Quad-Vector execution;
- CLI/editor integration.

## Deferred boundaries

Still deferred:

- generic artifact loader;
- full generic artifact validation;
- canonical outer-byte validation;
- parsed immutable payload representation;
- schema migration/conversion;
- consumer adapter/integration;
- file-path loading;
- network/RPC transport;
- FFI;
- ABI;
- native handles;
- binary linking;
- target lowering.

## Exact D candidate

```python
"""Passive build-artifact fingerprint integrity verification for P11.15D."""

from __future__ import annotations

import hashlib
import json

from tooling.build_artifact import (
    BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
    canonical_json_bytes,
)

from .build_artifact import BuildArtifactInterchange


def verify_build_artifact_interchange_fingerprint(
    interchange: BuildArtifactInterchange,
) -> str:
    """Verify one inspected build artifact's declared canonical fingerprint."""

    if type(interchange) is not BuildArtifactInterchange:
        raise TypeError(
            "verify_build_artifact_interchange_fingerprint requires an exact "
            "BuildArtifactInterchange"
        )

    text = interchange.content.decode("utf-8")
    value = json.loads(text)

    if type(value) is not dict:
        raise ValueError(
            "build artifact integrity content must contain a JSON object"
        )

    schema = value.get("schema")
    if type(schema) is not str or schema != interchange.schema:
        raise ValueError(
            "build artifact interchange schema/content mismatch"
        )

    fingerprint = value.get("fingerprint")
    if (
        type(fingerprint) is not dict
        or frozenset(fingerprint) != frozenset(("algorithm", "value"))
    ):
        raise ValueError(
            "build artifact fingerprint shape mismatch"
        )

    if (
        fingerprint["algorithm"] != BUILD_ARTIFACT_FINGERPRINT_ALGORITHM
        or type(fingerprint["value"]) is not str
    ):
        raise ValueError(
            "build artifact fingerprint shape mismatch"
        )

    payload = dict(value)
    del payload["fingerprint"]

    expected = hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()

    if fingerprint["value"] != expected:
        raise ValueError(
            "build artifact fingerprint mismatch"
        )

    return fingerprint["value"]


__all__ = (
    "verify_build_artifact_interchange_fingerprint",
)
```

## D acceptance requirements

D must prove:

1. B production files remain byte-identical;
2. package root `__all__ == ()`;
3. exact D module export surface;
4. no new dataclass/result type;
5. exact `BuildArtifactInterchange` input only;
6. valid v1 fingerprint accepted;
7. valid v2 fingerprint accepted;
8. valid v3 fingerprint accepted;
9. declared fingerprint string returned;
10. interchange object/content remain unchanged;
11. JSON object required;
12. schema/content consistency required;
13. missing fingerprint rejected;
14. fingerprint must be exact dict;
15. fingerprint keys exactly `algorithm`, `value`;
16. canonical algorithm constant reused;
17. fingerprint value exact string;
18. mismatched fingerprint rejected;
19. fingerprint recomputed over canonical payload without `fingerprint`;
20. no schema-specific branch;
21. no full outer-shape validation;
22. no canonical outer-byte requirement;
23. no reconstruction;
24. no file/network/subprocess behavior;
25. no runtime/agent/effect/Quad-Vector integration;
26. no consumer rewiring;
27. no FFI/native/ABI/RPC surface.

## Successor discipline

After D is frozen, P11.15E must audit whether the existing narrative readers
should consume the generic integrity primitive.

That integration is not presumed merely because duplicated code exists.

The E audit must prove that replacing the duplicate fingerprint block does not
change each reader's:

- canonical-byte policy;
- accepted schema set;
- top-level field policy;
- narrative reconstruction;
- error ordering;
- error semantics.

Every successor remains architecture-first.