"""AFP-P8.1 canonical type-model smoke test."""

from __future__ import annotations

from typing import Callable, Type

from type_system.model import (
    ApexType,
    BOOL,
    BUILTIN_TYPES,
    FLOAT,
    INT,
    STRING,
    VOID,
    is_builtin_type,
    is_void_type,
    resolve_builtin_type,
)


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(
    expected: Type[BaseException],
    operation: Callable[[], object],
    message: str,
) -> None:
    try:
        operation()
    except expected:
        return

    raise AssertionError(message)


def main() -> None:
    require(
        tuple(str(apex_type) for apex_type in BUILTIN_TYPES[:5])
        == ("int", "bool", "string", "float", "void"),
        "P8 primitive type order or spelling changed",
    )

    require(
        resolve_builtin_type("int") is INT,
        "int did not resolve to the canonical INT object",
    )
    require(
        resolve_builtin_type("bool") is BOOL,
        "bool did not resolve to the canonical BOOL object",
    )
    require(
        resolve_builtin_type("string") is STRING,
        "string did not resolve to the canonical STRING object",
    )
    require(
        resolve_builtin_type("float") is FLOAT,
        "float did not resolve to the canonical FLOAT object",
    )
    require(
        resolve_builtin_type("void") is VOID,
        "void did not resolve to the canonical VOID object",
    )

    require(
        resolve_builtin_type(ApexType("int")) is INT,
        "equivalent type identity was not canonicalized",
    )

    require(
        is_builtin_type(INT),
        "canonical INT was not recognized as built-in",
    )
    require(
        is_builtin_type("string"),
        "string spelling was not recognized as built-in",
    )
    require(
        not is_builtin_type("decimal"),
        "unknown decimal type was accepted",
    )

    require(
        is_void_type(VOID),
        "canonical VOID was not recognized",
    )
    require(
        is_void_type("void"),
        "void spelling was not recognized",
    )
    require(
        not is_void_type(INT),
        "INT was incorrectly recognized as void",
    )

    future_generic = ApexType(
        "List",
        (INT,),
    )
    require(
        str(future_generic) == "List<int>",
        "structural type rendering is unstable",
    )

    require_raises(
        ValueError,
        lambda: resolve_builtin_type("decimal"),
        "unknown built-in type was not rejected",
    )
    require_raises(
        ValueError,
        lambda: resolve_builtin_type(future_generic),
        "applied generic type was accepted during P8",
    )
    require_raises(
        TypeError,
        lambda: resolve_builtin_type(7),  # type: ignore[arg-type]
        "non-type input was not rejected",
    )
    require_raises(
        ValueError,
        lambda: ApexType(""),
        "empty type name was not rejected",
    )
    require_raises(
        ValueError,
        lambda: ApexType("not valid"),
        "invalid type identifier was not rejected",
    )

    print("AFP-P8.1 canonical type-model smoke test passed.")
    print("Built-in type identities: PASS")
    print("Canonical type resolution: PASS")
    print("Type predicates: PASS")
    print("Unknown type rejection: PASS")
    print("P9 structural extension seam: PASS")


if __name__ == "__main__":
    main()