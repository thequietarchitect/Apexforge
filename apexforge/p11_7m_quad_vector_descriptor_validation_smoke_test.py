"""P11.7M canonical Quad-Vector descriptor-validation red-gate smoke test."""

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
    from quad_vector.model import QuadVectorLane, QuadVectorResourceBudget
    from quad_vector.module import QuadVectorModuleKind
    from quad_vector.parsing import parse_quad_vector_descriptor
    from quad_vector.validation import (
        QuadVectorValidatedDescriptor,
        validate_quad_vector_descriptor,
    )

    candidate = QuadVectorDiscoveryCandidate(
        source=QuadVectorDiscoverySource.MANIFEST,
        source_identity="source:manifest:quad-vector",
        descriptor_identity="descriptor:AdaptiveBalance",
        descriptor_reference="quad-vector.json#AdaptiveBalance",
        order=0,
    )
    text = (
        '{"canonical_id":"quad.module:AdaptiveBalance",'
        '"version":"1.0",'
        '"kind":"weighting_rule",'
        '"accepted_inputs":["quad.velocity","quad.eligibility"],'
        '"produced_outputs":["quad.weight"],'
        '"eligible_vectors":["+X","-X","+Y","-Y"],'
        '"dependencies":["quad.module:BaseVelocity"],'
        '"determinism_contract":"pure-deterministic",'
        '"authority_requirements":["quad.vector.read"],'
        '"resource_budget":{"max_modules":8,"max_contributions":32,"max_iterations":64},'
        '"implementation_reference":"python:quad_plugins.adaptive_balance",'
        '"metadata":{"author":"architect"}}'
    )
    parsed = parse_quad_vector_descriptor(candidate, text)
    validated = validate_quad_vector_descriptor(parsed)

    require(
        type(validated) is QuadVectorValidatedDescriptor,
        "validator returned a non-canonical validated snapshot",
    )
    require(validated.parsed is parsed, "validator changed parsed descriptor identity")
    require(validated.canonical_id == "quad.module:AdaptiveBalance", "canonical_id changed")
    require(validated.version == "1.0", "version changed")
    require(
        validated.kind is QuadVectorModuleKind.WEIGHTING_RULE,
        "module kind was not semantically validated",
    )
    require(
        validated.accepted_inputs == ("quad.velocity", "quad.eligibility"),
        "accepted_inputs validation changed order",
    )
    require(
        validated.produced_outputs == ("quad.weight",),
        "produced_outputs validation changed order",
    )
    require(
        validated.eligible_vectors
        == (
            QuadVectorLane.POSITIVE_X,
            QuadVectorLane.NEGATIVE_X,
            QuadVectorLane.POSITIVE_Y,
            QuadVectorLane.NEGATIVE_Y,
        ),
        "eligible vector validation changed canonical lane order",
    )
    require(
        validated.dependencies == ("quad.module:BaseVelocity",),
        "dependency validation changed order",
    )
    require(
        validated.determinism_contract == "pure-deterministic",
        "determinism contract changed",
    )
    require(
        validated.authority_requirements == ("quad.vector.read",),
        "authority requirements changed",
    )
    require(
        type(validated.resource_budget) is QuadVectorResourceBudget
        and validated.resource_budget.max_modules == 8
        and validated.resource_budget.max_contributions == 32
        and validated.resource_budget.max_iterations == 64,
        "resource budget was not semantically validated",
    )
    require(
        validated.implementation_reference == "python:quad_plugins.adaptive_balance",
        "implementation reference changed",
    )

    def validate_text(body):
        return validate_quad_vector_descriptor(
            parse_quad_vector_descriptor(candidate, body)
        )

    expect_error(
        ValueError,
        lambda: validate_text('{"version":"1.0"}'),
        "missing required descriptor fields were accepted",
    )
    expect_error(
        ValueError,
        lambda: validate_text(text.replace('"weighting_rule"', '"unknown_kind"')),
        "unknown module kind was accepted",
    )
    expect_error(
        ValueError,
        lambda: validate_text(text.replace('"+Y"', '"diagonal"')),
        "unknown vector lane was accepted",
    )
    expect_error(
        ValueError,
        lambda: validate_text(
            text.replace(
                '["quad.velocity","quad.eligibility"]',
                '["quad.velocity","quad.velocity"]',
            )
        ),
        "duplicate accepted_inputs were accepted",
    )
    expect_error(
        ValueError,
        lambda: validate_text(
            text.replace('"max_modules":8', '"max_modules":true')
        ),
        "non-integer resource budget was accepted",
    )
    expect_error(
        TypeError,
        lambda: validate_quad_vector_descriptor(object()),
        "non-parsed descriptor was accepted",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(validated, "version", "2.0"),
        "validated descriptor snapshot became mutable",
    )

    for item in (validated, validated.parsed):
        require(
            not hasattr(item, "canonicalize")
            and not hasattr(item, "register")
            and not hasattr(item, "bind")
            and not hasattr(item, "execute")
            and not hasattr(item, "run")
            and not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex"),
            "P11.7M validation snapshot gained downstream/runtime/loader/Codex authority",
        )

    print("Required canonical descriptor field validation: PASS")
    print("Recognized module-kind semantic validation: PASS")
    print("Input/output/dependency/authority tuple validation: PASS")
    print("Canonical lane-name semantic validation: PASS")
    print("Determinism/resource-budget/implementation-reference validation: PASS")
    print("Parsed-descriptor identity preservation through validation: PASS")
    print("Immutable validated-descriptor snapshot boundary: PASS")
    print("P11.7M canonicalize/register/bind/execution/loader/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
