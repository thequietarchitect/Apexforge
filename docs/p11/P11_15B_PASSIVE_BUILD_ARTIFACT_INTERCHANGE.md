# P11.15B â€” Passive Build-Artifact Interchange

## Status

RED contract following frozen P11.15A.

Frozen predecessor:

- P11.15A commit: `57a4da779cde05cc39a227479fc20c9005ea0a59`
- annotated tag: `afp-p11-15a-freeze`

RED introduces no production `interoperability` package.

## Exact production owner

Future GREEN owner:

```text
interoperability.build_artifact
```

The package root remains explicit-module-only:

```python
__all__ = ()
```

## Exact production surface

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

## Input boundary

The inspection function accepts exact `bytes` only.

It rejects:

- `bytearray`;
- `memoryview`;
- `str`;
- path-like objects;
- file objects;
- other buffer providers.

Empty bytes are rejected.

The function performs no filesystem I/O.

## JSON boundary

The bytes must:

1. decode as UTF-8;
2. parse as JSON;
3. contain one JSON object;
4. contain an exact string `schema` member.

Invalid UTF-8 is not translated into a custom error.

Invalid JSON is not translated into a custom error.

## Supported schema set

Exactly:

```text
apexforge.build-artifact/v1
apexforge.build-artifact/v2
apexforge.build-artifact/v3
```

The production implementation must import and reuse:

```python
BUILD_ARTIFACT_SCHEMA
BUILD_ARTIFACT_SCHEMA_V2
BUILD_ARTIFACT_SCHEMA_V3
```

from `tooling.build_artifact`.

Unknown schemas are rejected.

No prefix matching, wildcard compatibility, future-version acceptance, or
downgrade behavior exists in B.

## Result boundary

On success:

```python
BuildArtifactInterchange(
    schema=<recognized exact schema text>,
    content=<exact original input bytes object>,
)
```

The result:

- is frozen;
- preserves exact input-byte identity;
- preserves exact input bytes;
- carries only `schema` and `content`;
- retains no JSON mapping.

## Deliberately deferred

B does not validate:

- complete top-level field sets;
- nested project shape;
- AIR;
- narrative payloads;
- rich-document payloads;
- package declarations;
- fingerprint object shape;
- fingerprint correctness;
- canonical JSON byte form;
- semantic validity;
- runtime executability.

B also performs no:

- artifact reconstruction;
- file reading;
- file writing;
- network I/O;
- subprocess execution;
- runtime integration;
- host-effect execution;
- Quad-Vector provider invocation;
- CLI/editor integration;
- FFI;
- ABI;
- native handles;
- target lowering;
- binary linking.

## Package export boundary

`interoperability.__all__` remains exactly:

```python
()
```

Neither B symbol is re-exported from the package root.

## Exact GREEN candidate

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

Package initializer:

```python
"""Explicit-module-only interoperability package for P11.15."""

__all__ = ()
```

## RED expectation

Before GREEN:

```python
import interoperability.build_artifact
```

must fail specifically because the entire package is absent:

```text
ModuleNotFoundError: No module named 'interoperability'
```

A different failure is not the intended RED state.

## GREEN acceptance

The smoke test must prove:

1. exact package `__all__ == ()`;
2. exact module `__all__`;
3. exact frozen dataclass;
4. exact field order `schema`, `content`;
5. exact function parameter `content`;
6. exact-bytes input requirement;
7. empty bytes rejected;
8. invalid UTF-8 propagates `UnicodeDecodeError`;
9. invalid JSON propagates `json.JSONDecodeError`;
10. JSON scalar/list/null rejected;
11. missing schema rejected;
12. non-string schema rejected;
13. v1 accepted;
14. v2 accepted;
15. v3 accepted;
16. unknown schema rejected;
17. exact input bytes identity preserved;
18. schema text preserved;
19. no mapping retained;
20. record mutation rejected;
21. no file I/O;
22. no network/subprocess;
23. no runtime/agent/effect/QV integration;
24. no fingerprint validation;
25. no artifact reconstruction;
26. frozen A and P11.14 owners unchanged.