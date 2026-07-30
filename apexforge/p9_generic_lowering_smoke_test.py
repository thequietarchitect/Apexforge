"""AFP-P9.7 deterministic generic AIR lowering smoke test."""

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
from type_system.constraints import NUMERIC
from type_system.generics import ApexTypeVariable
from type_system.lowering import lower_linked_generics
from type_system.model import FLOAT, INT, STRING


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


@dataclass(frozen=True)
class Program:
    functions: tuple[AIRFunction, ...]
    states: tuple[object, ...] = ()
    entry_expression: object = None


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


def body_expression(function: AIRFunction):
    if function.body:
        return function.body[-1].expression
    return function.return_expression


def function_snapshot(functions: tuple[AIRFunction, ...]):
    return tuple(
        (
            function.id,
            function.name,
            function.order,
            tuple(
                None if parameter.value_type is None else parameter.value_type.name
                for parameter in function.parameters
            ),
            None if function.return_type is None else function.return_type.name,
            tuple(parameter.name for parameter in function.type_parameters),
            repr(function.return_expression),
            repr(function.body),
        )
        for function in functions
    )


def evaluate(expression, functions, locals_=None):
    locals_ = dict(locals_ or {})
    if isinstance(expression, AIRIntegerLiteral):
        return expression.value
    if isinstance(expression, AIRFloatLiteral):
        return expression.value
    if isinstance(expression, AIRStringLiteral):
        return expression.value
    if isinstance(expression, AIRIdentifierReference):
        return locals_[expression.name]
    if isinstance(expression, AIRBinaryExpression):
        left = evaluate(expression.left, functions, locals_)
        right = evaluate(expression.right, functions, locals_)
        if expression.operator == "+":
            return left + right
        raise AssertionError(f"unsupported test operator {expression.operator}")
    if isinstance(expression, AIRCallExpression):
        function = functions[expression.target]
        values = tuple(
            evaluate(argument, functions, locals_)
            for argument in expression.arguments
        )
        frame = {
            parameter.name: value
            for parameter, value in zip(function.parameters, values)
        }
        return evaluate(body_expression(function), functions, frame)
    raise AssertionError(f"unsupported test expression {type(expression).__name__}")


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
        order=1,
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
            AIRIdentifierReference("left"),
            "+",
            AIRIdentifierReference("right"),
        ),
        return_type=add_n,
        type_parameters=(add_n,),
        order=2,
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
    use_string = function(
        "UseString",
        (),
        AIRCallExpression(
            target="Identity",
            arguments=(AIRStringLiteral("ready"),),
            type_arguments=(STRING,),
        ),
        return_type=STRING,
        order=4,
    )
    use_add = function(
        "UseAdd",
        (),
        AIRCallExpression(
            target="Add",
            arguments=(AIRFloatLiteral(1.0), AIRFloatLiteral(2.0)),
        ),
        return_type=FLOAT,
        order=5,
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
        order=6,
    )

    program = Program(
        functions=(
            use_string,
            identity,
            unused,
            use_echo,
            add,
            echo,
            use_add,
        ),
        entry_expression=AIRCallExpression(
            target="Identity",
            arguments=(AIRIntegerLiteral(99),),
        ),
    )
    result = lower_linked_generics(program)

    require(
        result.canonical_ids
        == (
            "Add<float>",
            "Echo<int>",
            "Identity<int>",
            "Identity<string>",
        ),
        f"unexpected lowering closure: {result.canonical_ids}",
    )
    require(
        len(result.specialized_functions) == 4,
        "closed specialization count changed during lowering",
    )
    require(
        all(not function.type_parameters for function in result.specialized_functions),
        "lowered specialization retained generic type parameters",
    )

    identity_int_target = result.lowered_target("Identity<int>")
    identity_string_target = result.lowered_target("Identity<string>")
    echo_int_target = result.lowered_target("Echo<int>")
    add_float_target = result.lowered_target("Add<float>")
    require(
        all(
            isinstance(target, str) and target.startswith("__apx_spec__")
            for target in (
                identity_int_target,
                identity_string_target,
                echo_int_target,
                add_float_target,
            )
        ),
        "specialization identities were not deterministically mangled",
    )

    by_name = {function.name: function for function in result.functions}
    require(
        by_name["Identity"] is identity,
        "original generic declaration was not preserved",
    )
    require(
        by_name["Echo"] is echo,
        "transitive generic declaration was not preserved",
    )
    require(
        by_name["Unused"] is unused,
        "unused generic declaration was not preserved",
    )
    require(
        result.lowered_target("Unused<int>") is None,
        "unused generic declaration was unexpectedly specialized",
    )

    lowered_identity_int = by_name[identity_int_target]
    require(
        lowered_identity_int.parameters[0].value_type is INT,
        "Identity<int> parameter was not projected to int",
    )
    require(
        lowered_identity_int.return_type is INT,
        "Identity<int> return was not projected to int",
    )

    lowered_echo_int = by_name[echo_int_target]
    echo_call = body_expression(lowered_echo_int)
    require(
        isinstance(echo_call, AIRCallExpression),
        "Echo<int> body did not remain a call",
    )
    require(
        echo_call.target == identity_int_target,
        "transitive generic call was not rewritten to Identity<int>",
    )
    require(
        echo_call.type_arguments == (),
        "lowered transitive call retained type arguments",
    )

    use_echo_call = body_expression(by_name["UseEcho"])
    require(
        use_echo_call.target == echo_int_target,
        "concrete root did not target Echo<int>",
    )
    require(
        body_expression(by_name["UseString"]).target == identity_string_target,
        "explicit generic call did not lower to Identity<string>",
    )
    require(
        body_expression(by_name["UseAdd"]).target == add_float_target,
        "constrained generic call did not lower to Add<float>",
    )

    entry = result.program.entry_expression
    require(
        isinstance(entry, AIRCallExpression)
        and entry.target == identity_int_target
        and entry.type_arguments == (),
        "program-level generic call was not lowered",
    )

    runtime_index = {
        function.name: function
        for function in result.functions
    }
    require(
        evaluate(body_expression(by_name["UseEcho"]), runtime_index) == 10,
        "lowered nested call did not preserve runtime value",
    )
    require(
        evaluate(body_expression(by_name["UseString"]), runtime_index) == "ready",
        "lowered explicit call did not preserve runtime value",
    )
    require(
        evaluate(body_expression(by_name["UseAdd"]), runtime_index) == 3.0,
        "lowered constrained call did not preserve runtime value",
    )

    reverse_result = lower_linked_generics(
        Program(
            functions=tuple(reversed(program.functions)),
            entry_expression=program.entry_expression,
        )
    )
    require(
        reverse_result.bindings == result.bindings,
        "lowered specialization identities depend on input order",
    )
    require(
        function_snapshot(reverse_result.functions)
        == function_snapshot(result.functions),
        "lowered AIR output depends on input order",
    )

    print("AFP-P9.7 deterministic generic lowering smoke test passed.")
    print("Closed specialization materialization: PASS")
    print("Stable concrete function identities: PASS")
    print("Concrete parameter projection: PASS")
    print("Concrete return projection: PASS")
    print("Root call rewriting: PASS")
    print("Transitive call rewriting: PASS")
    print("Explicit type-argument erasure: PASS")
    print("Program-level expression rewriting: PASS")
    print("Original generic traceability: PASS")
    print("Unused generic preservation: PASS")
    print("Constraint-preserving lowering: PASS")
    print("Runtime semantic preservation: PASS")
    print("Input-order independence: PASS")


if __name__ == "__main__":
    main()