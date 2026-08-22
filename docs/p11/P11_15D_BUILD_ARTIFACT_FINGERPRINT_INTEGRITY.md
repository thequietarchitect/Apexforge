# P11.15D â€” Build-Artifact Fingerprint Integrity

## Status

RED contract following frozen P11.15C.

Frozen predecessor:

- P11.15C commit: `79976fc542f62242d28e3e5a8cd3683bf380b3a2`
- annotated tag: `afp-p11-15c-freeze`

RED introduces no production `interoperability.build_artifact_integrity`
module.

## Exact production owner

Future GREEN owner:

```text
interoperability.build_artifact_integrity
```

Frozen P11.15B remains untouched:

```text
interoperability.__init__
interoperability.build_artifact
```

The package root remains:

```python
__all__ = ()
```

## Exact public surface

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

No new dataclass or result record exists.

## Exact input boundary

The function accepts an exact:

```text
BuildArtifactInterchange
```

only.

It rejects subclasses and unrelated objects.

The function does not accept raw bytes, mappings, paths, or file objects.

## Content consistency

D re-parses `interchange.content`.

It requires:

1. UTF-8 decoding succeeds;
2. JSON decoding succeeds;
3. decoded JSON is an object;
4. exact string JSON `schema` equals `interchange.schema`.

This prevents a directly constructed `BuildArtifactInterchange` from pairing
one supported schema label with unrelated content.

## Fingerprint envelope

The parsed outer object must contain an exact `dict` fingerprint.

Its exact keys are:

```text
algorithm
value
```

No missing or additional fingerprint members are accepted.

The `algorithm` must equal the existing:

```python
BUILD_ARTIFACT_FINGERPRINT_ALGORITHM
```

from `tooling.build_artifact`.

The fingerprint `value` must be an exact string.

## Integrity rule

D creates a shallow copy of the parsed outer object:

```python
payload = dict(value)
```

removes only:

```text
fingerprint
```

and computes:

```python
hashlib.sha256(
    canonical_json_bytes(payload)
).hexdigest()
```

using `canonical_json_bytes` from `tooling.build_artifact`.

If the declared value differs from the computed value, D raises `ValueError`.

On success the function returns the declared verified fingerprint string.

## Supported schemas

Schema eligibility remains owned by frozen P11.15B.

Therefore D supports exactly the schemas accepted by
`BuildArtifactInterchange`:

```text
apexforge.build-artifact/v1
apexforge.build-artifact/v2
apexforge.build-artifact/v3
```

D contains no schema-specific branch.

## Canonical outer bytes

D does not require:

```python
interchange.content == canonical_json_bytes(parsed_outer_object)
```

A non-canonical JSON encoding with a valid declared fingerprint over the
canonicalized payload is therefore valid at the D boundary.

Canonical outer-byte enforcement remains a separate consumer policy.

## Not full validation

D does not validate:

- complete outer top-level keys;
- project payload shape;
- AIR payload shape;
- narrative payload shape;
- rich-document payload shape;
- package payload shape;
- semantic validity;
- runtime executability.

## No reconstruction

D reconstructs no:

- AIRProgram;
- ProjectBuild;
- NarrativeBuildArtifact;
- RichDocumentProjectBuild;
- package object;
- runtime object.

## No I/O or execution

D performs no:

- filesystem read/write;
- network I/O;
- subprocess;
- runtime integration;
- agent integration;
- host-effect execution;
- Quad-Vector execution;
- CLI/editor integration.

## No consumer rewiring

D does not modify or integrate:

```text
tooling.narrative_execution
tooling.narrative_session
```

Their exact C-baseline bytes remain frozen during D.

Consumer integration remains subject to a later architecture-first audit.

## Still deferred

- generic artifact loader;
- parsed immutable payload model;
- full generic build-artifact validation;
- canonical outer-byte validation;
- schema migration/conversion;
- file-path loading;
- network/RPC transport;
- FFI;
- ABI;
- native handles;
- binary linking;
- target lowering.

## Exact GREEN candidate

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

## RED expectation

Before GREEN:

```python
import interoperability.build_artifact_integrity
```

must fail specifically because that submodule does not exist:

```text
ModuleNotFoundError: No module named 'interoperability.build_artifact_integrity'
```

The package itself already exists from B.

A failure because `interoperability` itself is missing is not the intended D
RED state.

## GREEN acceptance requirements

The D smoke test must prove:

1. P11.15C freeze ancestry;
2. frozen B files unchanged;
3. narrative execution/session consumers unchanged;
4. package root exports remain empty;
5. exact D module `__all__`;
6. one public function only;
7. no dataclass/result record;
8. exact `BuildArtifactInterchange` input only;
9. valid v1 accepted;
10. valid v2 accepted;
11. valid v3 accepted;
12. exact declared fingerprint string returned;
13. interchange object/content remain unchanged;
14. invalid UTF-8 propagates `UnicodeDecodeError`;
15. invalid JSON propagates `json.JSONDecodeError`;
16. JSON object required;
17. schema/content mismatch rejected;
18. missing fingerprint rejected;
19. fingerprint exact dict required;
20. exact fingerprint keys required;
21. canonical fingerprint algorithm constant reused;
22. exact string fingerprint value required;
23. mismatched fingerprint rejected;
24. canonical payload-without-fingerprint SHA-256 rule;
25. no schema-specific branch;
26. non-canonical outer JSON bytes accepted when integrity is valid;
27. no full outer-shape validation;
28. no artifact reconstruction;
29. no file/network/subprocess;
30. no runtime/agent/effect/QV integration;
31. no narrative consumer rewiring;
32. no FFI/native/ABI/RPC surface.