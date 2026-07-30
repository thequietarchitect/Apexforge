"""AFP-P9.6 linked specialization-closure smoke test."""

from __future__ import annotations

from dataclasses import dataclass

from air.expressions import (
    AIRBinaryExpression,
    AIRCallExpression,
    AIRFloatLiteral,
    AIRIdentifierReference,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.functions import (
    AIRFunction,
    AIRFunctionReturn,
    AIRParameter,
)
from type_system.closure import collect_linked_specializations
from type_system.constraints import NUMERIC
from type_system.generics import ApexTypeVariable
from type_system.inference import TypeInferenceError
from type_system.model import FLOAT, INT, STRING


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


@dataclass(frozen=True)
class Program:
    functions: tuple[AIRFunction, ...]
    states: tuple[object, ...] = ()


def function(
    name: str,
    parameters: tuple[AIRParameter, ...],
    expression,
    *,
    return_type,
    type_parameters=(),
    order: int = 0,
) -> AIRFunction:
    return AIRFunction(
        id=f"function:{name}",
        name=name,
        parameters=parameters,
        return_expression=expression,
        order=order,
        body=(AIRFunctionReturn(expression),),
        return_type=return_type,
        type_parameters=tuple(type_parameters),
    )


def main() -> None:
    identity_t = ApexTypeVariable(
        name="T",
        owner="function:Identity",
    )
    identity = function(
        "Identity",
        (AIRParameter("value", identity_t),),
        AIRIdentifierReference("value"),
        return_type=identity_t,
        type_parameters=(identity_t,),
    )

    echo_u = ApexTypeVariable(
        name="U",
        owner="function:Echo",
    )
    echo = function(
        "Echo",
        (AIRParameter("value", echo_u),),
        AIRCallExpression(
            target="Identity",
            arguments=(AIRIdentifierReference("value"),),
            type_arguments=(echo_u,),
        ),
        return_type=echo_u,
        type_parameters=(echo_u,),
    )

    add_n = ApexTypeVariable(
        name="N",
        owner="function:Add",
        constraints=(NUMERIC,),
    )
    add = function(
        "Add",
        (
            AIRParameter("left", add_n),
            AIRParameter("right", add_n),
        ),
        AIRBinaryExpression(
            left=AIRIdentifierReference("left"),
            operator="+",
            right=AIRIdentifierReference("right"),
        ),
        return_type=add_n,
        type_parameters=(add_n,),
    )

    use_echo = function(
        "UseEcho",
        (),
        AIRCallExpression(
            target="Echo",
            arguments=(AIRIntegerLiteral(10),),
        ),
        return_type=INT,
        order=3,
    )
    use_identity_twice = function(
        "UseIdentityTwice",
        (),
        AIRBinaryExpression(
            left=AIRCallExpression(
                target="Identity",
                arguments=(AIRIntegerLiteral(1),),
            ),
            operator="+",
            right=AIRCallExpression(
                target="Identity",
                arguments=(AIRIntegerLiteral(2),),
            ),
        ),
        return_type=INT,
        order=4,
    )
    use_string = function(
        "UseString",
        (),
        AIRCallExpression(
            target="Identity",
            arguments=(AIRStringLiteral("ready"),),
            type_arguments=(STRING,),
        ),
        return_type=STRING,
        order=5,
    )
    use_add = function(
        "UseAdd",
        (),
        AIRCallExpression(
            target="Add",
            arguments=(AIRFloatLiteral(1.0), AIRFloatLiteral(2.0)),
        ),
        return_type=FLOAT,
        order=6,
    )

    unused_v = ApexTypeVariable(
        name="V",
        owner="function:Unused",
    )
    unused = function(
        "Unused",
        (AIRParameter("value", unused_v),),
        AIRIdentifierReference("value"),
        return_type=unused_v,
        type_parameters=(unused_v,),
        order=7,
    )

    program = Program(
        functions=(
            use_string,
            identity,
            unused,
            use_echo,
            add,
            echo,
            use_identity_twice,
            use_add,
        )
    )
    manifest = collect_linked_specializations(program)

    require(
        manifest.canonical_ids
        == (
            "Add<float>",
            "Echo<int>",
            "Identity<int>",
            "Identity<string>",
        ),
        f"unexpected specialization closure: {manifest.canonical_ids}",
    )
    require(
        len(manifest) == 4,
        "repeated generic calls were not deduplicated",
    )
    require(
        "Unused" not in " ".join(manifest.canonical_ids),
        "uninstantiated generic declaration entered closure",
    )

    edges = tuple(
        (dependency.caller, dependency.callee)
        for dependency in manifest.dependencies
    )
    require(
        ("function:UseEcho", "Echo<int>") in edges,
        "concrete root to generic specialization edge missing",
    )
    require(
        ("Echo<int>", "Identity<int>") in edges,
        "transitive generic-to-generic edge missing",
    )
    require(
        edges.count(("function:UseIdentityTwice", "Identity<int>")) == 1,
        "duplicate call sites did not collapse to one dependency edge",
    )

    reverse_program = Program(functions=tuple(reversed(program.functions)))
    reverse_manifest = collect_linked_specializations(reverse_program)
    require(
        reverse_manifest == manifest,
        "manifest depends on linked function input order",
    )

    bad = function(
        "Bad",
        (),
        AIRCallExpression(
            target="Add",
            arguments=(
                AIRStringLiteral("left"),
                AIRStringLiteral("right"),
            ),
        ),
        return_type=STRING,
    )
    try:
        collect_linked_specializations(
            Program(functions=(identity, add, bad))
        )
    except TypeInferenceError as error:
        require(
            error.code == "APX-TYPE-021",
            f"expected APX-TYPE-021, received {error.code}: {error}",
        )
    else:
        raise AssertionError(
            "constraint-invalid linked specialization unexpectedly closed"
        )

    print("AFP-P9.6 linked specialization closure smoke test passed.")
    print("Concrete root discovery: PASS")
    print("Transitive generic expansion: PASS")
    print("Explicit and inferred calls: PASS")
    print("Constraint-preserving closure: PASS")
    print("Repeated-call deduplication: PASS")
    print("Dependency edge canonicalization: PASS")
    print("Unused generic exclusion: PASS")
    print("Input-order independence: PASS")
    print("Invalid specialization rejection: PASS")


if __name__ == "__main__":
    main()