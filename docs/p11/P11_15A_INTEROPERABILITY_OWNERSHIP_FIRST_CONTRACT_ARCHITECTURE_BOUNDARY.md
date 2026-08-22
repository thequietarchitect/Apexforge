# P11.15A â€” Interoperability Ownership / First Contract Architecture Boundary

## Status

Architecture-only boundary following the frozen P11.14 phase.

Frozen predecessor:

- P11.14 completion commit: `93145f9927919c15e4df28d5cf8c9c5fcc0a903c`
- annotated phase tag: `afp-p11-14-freeze`

P11.15A introduces no production module, type, function, parser, serializer,
runtime hook, file operation, network behavior, native value, or external
process invocation.

## Audit conclusion

The repository already contains several domain-specific external boundaries:

- canonical versioned build-artifact writers;
- narrative-specific artifact readers;
- explicit host-effect handler callables;
- explicit Quad-Vector implementation providers;
- CLI, VS Code, and Visual Studio tooling bridges;
- AIR JSON serialization/loading.

Those owners are already coherent and must not be collapsed into one generic
FFI or bridge abstraction.

The first real P11.15 gap is narrower:

**ApexForge has one canonical generic build-artifact write boundary with v1,
v2, and v3 schemas, but no generic read-side schema inspection boundary that
recognizes those three outer artifact generations without becoming a
domain-specific loader.**

Narrative execution/session code performs specialized read-side validation for
the artifact generations it consumes, but that is narrative tooling ownership,
not a reusable generic interchange boundary.

## P11.15 scope selection

P11.15 begins as passive versioned data interchange.

It does not begin as:

- FFI;
- ABI;
- native code generation;
- binary linking;
- target lowering;
- foreign/native runtime values;
- RPC;
- networking;
- subprocess orchestration;
- plugin loading;
- editor integration;
- package registry/distribution.

## Existing owners remain authoritative

### `tooling.build_artifact`

Remains the canonical owner of:

- build-artifact schema strings;
- canonical artifact construction;
- canonical JSON writing;
- artifact fingerprint production;
- atomic filesystem output.

P11.15 does not move or duplicate those responsibilities.

### `effects.host_execution`

Remains the explicit caller-supplied host-effect execution seam.

A host-effect callable is not reclassified as FFI.

### `quad_vector.execution`

Remains the explicit implementation-provider execution owner.

P11.15 does not create another provider registry.

### editor / CLI tooling

VS Code, Visual Studio, LSP, and CLI bridges remain tooling-owned.

They do not define core interoperability semantics.

## First P11.15 production owner

The first production owner, if B passes RED/GREEN, is:

```text
interoperability.build_artifact
```

The package root:

```text
interoperability
```

will remain explicit-module-only initially:

```python
__all__ = ()
```

No symbols are promoted from `interoperability.build_artifact` into the package
root during B.

## P11.15B exact minimal contract

B introduces exactly one immutable record and one inspection function.

```python
@dataclass(frozen=True)
class BuildArtifactInterchange:
    schema: str
    content: bytes
```

and:

```python
def inspect_build_artifact_interchange(
    content: bytes,
) -> BuildArtifactInterchange:
    ...
```

Module export:

```python
__all__ = (
    "BuildArtifactInterchange",
    "inspect_build_artifact_interchange",
)
```

## Input contract

`inspect_build_artifact_interchange` accepts exact `bytes` only.

It rejects:

- `bytearray`;
- `memoryview`;
- `str`;
- path-like objects;
- file objects;
- arbitrary buffer providers.

The function performs no filesystem access.

## JSON boundary

The supplied bytes must:

1. be non-empty;
2. decode as UTF-8;
3. parse as one JSON object;
4. contain an exact string `schema` member.

B is a schema-inspection boundary, not a complete build-artifact validator.

It does not reconstruct:

- AIR;
- ProjectBuild;
- NarrativeBuildArtifact;
- RichDocumentProjectBuild;
- package declarations;
- runtime state.

## Supported schema set

B recognizes exactly the existing canonical outer build-artifact schemas owned
by `tooling.build_artifact`, in historical order:

```text
apexforge.build-artifact/v1
apexforge.build-artifact/v2
apexforge.build-artifact/v3
```

The implementation must import and reuse:

```python
BUILD_ARTIFACT_SCHEMA
BUILD_ARTIFACT_SCHEMA_V2
BUILD_ARTIFACT_SCHEMA_V3
```

rather than duplicate their literal ownership.

Unknown schema strings are rejected.

No wildcard, prefix, future-version, downgrade, or best-effort acceptance is
introduced in B.

## Result contract

On success:

```python
BuildArtifactInterchange(
    schema=<exact recognized schema object from parsed JSON>,
    content=<exact input bytes object>,
)
```

The result therefore preserves:

- the recognized schema value;
- exact input-byte identity;
- exact input bytes.

No JSON mapping is retained in the result.

This avoids introducing a mutable payload object as a new ownership surface.

## What B does not validate

B does not yet validate:

- complete top-level field sets for v1/v2/v3;
- nested project shape;
- AIR shape;
- narrative shape;
- rich-document shape;
- package shape;
- fingerprint object shape;
- fingerprint correctness;
- canonical JSON byte form;
- semantic validity;
- runtime executability.

Those are separate compatibility/validation decisions and require their own
evidence.

## Why the result keeps bytes rather than a mapping

A `dict` or generic Mapping would create questions about:

- mutability;
- deep freezing;
- key/value normalization;
- ownership of nested payload schemas;
- reconstruction semantics.

Exact bytes are already the canonical external interchange unit produced by
the build-artifact writer and can be preserved without changing any frozen
artifact schema.

## Why B is not placed in `tooling.build_artifact`

`tooling.build_artifact` owns production of canonical artifact bytes.

P11.15 needs a consumer-side interoperability boundary without mutating that
frozen writer or making the tooling writer responsible for all future external
consumption.

The new owner references the writer's schema constants but does not duplicate
construction, serialization, fingerprint, or output behavior.

## Why B is not a generic FFI

The repository contains no established foreign/native runtime-value model.

Existing caller-supplied host-effect handlers and Quad-Vector implementations
already provide explicit host boundaries.

Creating an FFI now would preempt:

- P12 Native Backend;
- future ABI decisions;
- native lowering;
- binary/linker ownership;
- foreign-memory or native-handle policy.

Therefore those areas remain deferred.

## P12 boundary

Explicitly deferred to P12 Native Backend:

- ABI design;
- machine/native value representation;
- foreign/native handles;
- native call frames;
- binary/object emission;
- linker integration;
- target calling conventions;
- native symbol resolution;
- target-specific lowering.

## Later ecosystem boundary

Explicitly deferred to later ecosystem/package work:

- plugin discovery/loading;
- package registry protocols;
- package publication;
- remote package resolution;
- network transport;
- RPC/service discovery.

Editor bridges remain in their current tooling owners.

## P11.15B candidate implementation shape

The exact implementation shape to test in B is:

```python
"""Passive build-artifact interoperability inspection for P11.15B."""

from __future__ import annotations

from dataclasses import dataclass
import json

from tooling.build_artifact import (
    BUILD_ARTIFACT_SCHEMA,
    BUILD_ARTIFACT_SCHEMA_V2,
    BUILD_ARTIFACT_SCHEMA_V3,
)


_SUPPORTED_SCHEMAS = (
    BUILD_ARTIFACT_SCHEMA,
    BUILD_ARTIFACT_SCHEMA_V2,
    BUILD_ARTIFACT_SCHEMA_V3,
)


@dataclass(frozen=True)
class BuildArtifactInterchange:
    """Exact bytes plus one recognized outer build-artifact schema."""

    schema: str
    content: bytes

    def __post_init__(self) -> None:
        if type(self.schema) is not str:
            raise TypeError(
                "BuildArtifactInterchange.schema must be an exact str"
            )
        if self.schema not in _SUPPORTED_SCHEMAS:
            raise ValueError(
                "BuildArtifactInterchange.schema is not supported"
            )
        if type(self.content) is not bytes:
            raise TypeError(
                "BuildArtifactInterchange.content must be exact bytes"
            )
        if not self.content:
            raise ValueError(
                "BuildArtifactInterchange.content must not be empty"
            )


def inspect_build_artifact_interchange(
    content: bytes,
) -> BuildArtifactInterchange:
    """Inspect one build artifact without reconstructing or executing it."""

    if type(content) is not bytes:
        raise TypeError(
            "inspect_build_artifact_interchange requires exact bytes"
        )
    if not content:
        raise ValueError(
            "inspect_build_artifact_interchange content must not be empty"
        )

    text = content.decode("utf-8")
    value = json.loads(text)

    if type(value) is not dict:
        raise ValueError(
            "build artifact interchange content must contain a JSON object"
        )

    schema = value.get("schema")
    if type(schema) is not str:
        raise ValueError(
            "build artifact interchange schema must be an exact str"
        )
    if schema not in _SUPPORTED_SCHEMAS:
        raise ValueError(
            "build artifact interchange schema is not supported"
        )

    return BuildArtifactInterchange(
        schema=schema,
        content=content,
    )


__all__ = (
    "BuildArtifactInterchange",
    "inspect_build_artifact_interchange",
)
```

## B acceptance boundaries

B must prove:

1. exact `bytes` input only;
2. empty bytes rejected;
3. invalid UTF-8 propagates decoding failure;
4. invalid JSON propagates JSON decoding failure;
5. non-object JSON rejected;
6. missing schema rejected;
7. non-string schema rejected;
8. v1 accepted;
9. v2 accepted;
10. v3 accepted;
11. unknown schema rejected;
12. exact input bytes object identity preserved;
13. exact schema text preserved;
14. result is immutable;
15. no mapping retained;
16. no file I/O;
17. no subprocess;
18. no network;
19. no runtime integration;
20. no artifact reconstruction;
21. no fingerprint validation;
22. no canonical-byte normalization;
23. build-artifact writer remains byte-identical;
24. host-effect and Quad-Vector boundaries remain untouched;
25. P11.14 remains frozen;
26. `interoperability.__all__ == ()`.

## P11.15 successor discipline

After B, P11.15 must audit the next real consumer requirement.

It must not assume that B automatically justifies:

- complete artifact validation;
- generic artifact loading;
- conversion among v1/v2/v3;
- execution from artifact bytes;
- FFI;
- RPC;
- native values.

Every successor remains architecture-first.