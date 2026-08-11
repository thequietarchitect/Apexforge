"""P11.7L canonical Quad-Vector descriptor-parsing smoke test."""

from dataclasses import FrozenInstanceError


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def expect_error(error_type, callback, message):
    try:
        callback()
    except error_type:
        return
    raise AssertionError(message)


def main():
    from quad_vector.discovery import (
        QuadVectorDiscoveryCandidate,
        QuadVectorDiscoverySource,
    )
    from quad_vector.parsing import (
        QuadVectorParsedDescriptor,
        parse_quad_vector_descriptor,
    )

    candidate = QuadVectorDiscoveryCandidate(
        source=QuadVectorDiscoverySource.MANIFEST,
        source_identity="source:manifest:quad-vector",
        descriptor_identity="descriptor:AdaptiveBalance",
        descriptor_reference="quad-vector.json#AdaptiveBalance",
        order=10,
    )
    text = (
        '{"canonical_id":"quad.module:AdaptiveBalance",'
        '"version":"1.0",'
        '"kind":"weighting_rule",'
        '"accepted_inputs":["quad.velocity","quad.eligibility"],'
        '"produced_outputs":["quad.weight"],'
        '"metadata":{"author":"architect","labels":["stable","deterministic"]}}'
    )

    parsed = parse_quad_vector_descriptor(candidate, text)

    require(
        type(parsed) is QuadVectorParsedDescriptor,
        "parser returned a non-canonical parsed descriptor snapshot",
    )
    require(
        parsed.candidate is candidate,
        "parser changed discovered candidate identity",
    )
    require(
        parsed.candidate.descriptor_reference == "quad-vector.json#AdaptiveBalance",
        "parser changed opaque descriptor reference",
    )
    require(
        parsed.fields
        == (
            ("canonical_id", "quad.module:AdaptiveBalance"),
            ("version", "1.0"),
            ("kind", "weighting_rule"),
            ("accepted_inputs", ("quad.velocity", "quad.eligibility")),
            ("produced_outputs", ("quad.weight",)),
            (
                "metadata",
                (
                    ("author", "architect"),
                    ("labels", ("stable", "deterministic")),
                ),
            ),
        ),
        "parser changed field order or recursive immutable JSON structure",
    )

    repeat = parse_quad_vector_descriptor(candidate, text)
    require(
        repeat.fields == parsed.fields,
        "descriptor parsing is not repeatable",
    )

    expect_error(
        ValueError,
        lambda: parse_quad_vector_descriptor(
            candidate,
            '{"canonical_id":"one","canonical_id":"two"}',
        ),
        "duplicate JSON object keys bypassed parsing validation",
    )
    expect_error(
        ValueError,
        lambda: parse_quad_vector_descriptor(candidate, '["not","an","object"]'),
        "non-object descriptor document was accepted",
    )
    expect_error(
        ValueError,
        lambda: parse_quad_vector_descriptor(candidate, '{"broken":'),
        "malformed descriptor JSON was accepted",
    )
    expect_error(
        TypeError,
        lambda: parse_quad_vector_descriptor(object(), text),
        "non-discovery candidate was accepted",
    )
    expect_error(
        TypeError,
        lambda: parse_quad_vector_descriptor(candidate, b"{}"),
        "non-string descriptor text was accepted",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(parsed, "fields", ()),
        "parsed descriptor snapshot became mutable",
    )

    for item in (parsed, parsed.candidate):
        require(
            not hasattr(item, "validate")
            and not hasattr(item, "canonicalize")
            and not hasattr(item, "register")
            and not hasattr(item, "bind")
            and not hasattr(item, "execute")
            and not hasattr(item, "run")
            and not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex"),
            "P11.7L parsed snapshot gained semantic/runtime/loader/Codex authority",
        )

    print("Discovered-candidate identity/reference preservation through parsing: PASS")
    print("Deterministic JSON descriptor field-order preservation: PASS")
    print("Recursive immutable descriptor-value freezing: PASS")
    print("Duplicate-key descriptor syntax rejection: PASS")
    print("Malformed/non-object descriptor rejection: PASS")
    print("Exact discovery-candidate/text parsing boundary: PASS")
    print("Immutable parsed-descriptor snapshot boundary: PASS")
    print("P11.7L validate/canonicalize/register/bind/execution/loader/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
