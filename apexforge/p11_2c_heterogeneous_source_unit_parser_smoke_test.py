"""Focused parser-only coverage for P11.2C heterogeneous source units."""

from __future__ import annotations

from itertools import product

from language.parser import (
    AuthorityNode,
    DirectiveNode,
    FunctionNode,
    ParseError,
    PrincipalNode,
    RoleNode,
    SourceUnitNode,
    WorkflowNode,
    parse,
    parse_headerless_directive_source_unit,
    parse_source_unit,
)


DECLARATIONS = (
    ("directive", DirectiveNode, "directive Main {}"),
    ("function", FunctionNode, "function Helper() { return 0 }"),
    ("workflow", WorkflowNode, "workflow Flow {}"),
    ("authority", AuthorityNode, "authority Aegis {}"),
    ("principal", PrincipalNode, "principal Operator {}"),
    ("role", RoleNode, "role Architect {}"),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as error:
        return error
    raise AssertionError(message)


def test_each_kind_and_all_ordered_pairs() -> None:
    for kind, node_type, source in DECLARATIONS:
        unit = parse_source_unit(source, source_name=f"{kind}.apex")
        require(isinstance(unit, SourceUnitNode), f"{kind} lost source-unit shape")
        require(
            len(unit.declarations) == 1
            and isinstance(unit.declarations[0], node_type),
            f"{kind} did not parse alone",
        )

    pair_count = 0
    for first, second in product(DECLARATIONS, repeat=2):
        source = first[2] + "\n" + second[2]
        unit = parse_source_unit(
            source,
            source_name=f"{first[0]}-{second[0]}.apex",
        )
        require(
            tuple(type(node) for node in unit.declarations)
            == (first[1], second[1]),
            f"ordered pair {first[0]} then {second[0]} changed order",
        )
        pair_count += 1

    require(pair_count == 36, "the complete ordered pair matrix was not tested")


def test_all_kinds_order_repetition_comments_and_determinism() -> None:
    source = "\n".join(item[2] for item in DECLARATIONS)
    first = parse_source_unit(source, source_name="all-six.apex")
    second = parse_source_unit(source, source_name="all-six.apex")
    require(
        tuple(type(node) for node in first.declarations)
        == tuple(item[1] for item in DECLARATIONS),
        "the six-kind source did not preserve exact declaration order",
    )
    require(first == second, "repeated parsing produced unequal AST values")

    repeated = parse_source_unit(
        "directive Main {}\ndirective Main {}\ndirective Main {}",
        source_name="repeated.apex",
    )
    require(
        len(repeated.declarations) == 3
        and all(isinstance(node, DirectiveNode) for node in repeated.declarations),
        "repeated declarations were rejected by the parser",
    )

    commented = parse_source_unit(
        "role Architect {}\n"
        "// role to function\n"
        "function Helper() { return 0 }\n"
        "// function to principal\n"
        "principal Operator {}",
        source_name="comments.apex",
    )
    require(
        tuple(type(node) for node in commented.declarations)
        == (RoleNode, FunctionNode, PrincipalNode),
        "inter-declaration comments disturbed source order",
    )


def test_source_aware_failures_and_compatibility_apis() -> None:
    malformed = require_raises(
        ParseError,
        lambda: parse_source_unit(
            "directive Main {}\n"
            "workflow Flow {}\n"
            "function Broken() {\n"
            "    return\n"
            "}",
            source_name="malformed-later.apex",
        ),
        "a malformed later declaration was accepted",
    )
    malformed_span = malformed.diagnostic.span
    require(
        malformed.diagnostic.code == "APX-PARSE-004"
        and malformed_span is not None
        and malformed_span.source_name == "malformed-later.apex"
        and malformed_span.start.line == 5,
        "a malformed later declaration lost its actual source location",
    )

    unexpected = require_raises(
        ParseError,
        lambda: parse_source_unit(
            "directive Main {}\nunexpected",
            source_name="unexpected.apex",
        ),
        "an unsupported top-level token was ignored",
    )
    unexpected_span = unexpected.diagnostic.span
    require(
        unexpected.diagnostic.code == "APX-PARSE-002"
        and unexpected_span is not None
        and unexpected_span.source_name == "unexpected.apex"
        and unexpected_span.start.line == 2,
        "unexpected top-level diagnostic category or location changed",
    )

    empty = require_raises(
        ParseError,
        lambda: parse_source_unit("", source_name="empty.apex"),
        "an empty source unit was accepted",
    )
    empty_span = empty.diagnostic.span
    require(
        empty.diagnostic.code == "APX-PARSE-002"
        and empty_span is not None
        and empty_span.source_name == "empty.apex"
        and empty_span.start.line == 1
        and empty_span.start.column == 1,
        "empty-source rejection was not deterministic or source-aware",
    )

    single = parse("directive Main {}", source_name="single.apex")
    require(isinstance(single, DirectiveNode), "parse() rejected one declaration")

    two = require_raises(
        ParseError,
        lambda: parse(
            "directive Main {}\nworkflow Flow {}",
            source_name="two.apex",
        ),
        "parse() accepted two top-level declarations",
    )
    two_span = two.diagnostic.span
    require(
        two.diagnostic.code == "APX-PARSE-001"
        and two_span is not None
        and two_span.source_name == "two.apex"
        and two_span.start.line == 2,
        "parse() no longer uses its existing EOF diagnostic behavior",
    )

    directives = parse_headerless_directive_source_unit(
        "directive Main {}\ndirective Main {}",
        source_name="directives.apex",
    )
    require(
        len(directives) == 2
        and all(isinstance(node, DirectiveNode) for node in directives),
        "the P11.2B API rejected repeated directives",
    )

    heterogeneous = require_raises(
        ParseError,
        lambda: parse_headerless_directive_source_unit(
            "directive Main {}\nworkflow Flow {}",
            source_name="heterogeneous.apex",
        ),
        "the P11.2B API accepted a heterogeneous source unit",
    )
    require(
        heterogeneous.diagnostic.code == "APX-PARSE-001",
        "the P11.2B heterogeneous rejection diagnostic changed",
    )


def test_source_unit_and_declaration_spans() -> None:
    source = (
        "\n  directive Main {}\n"
        "// separator\n"
        "workflow Flow {}\n\n"
    )
    unit = parse_source_unit(source, source_name="spans.apex")
    require(unit.span is not None, "source-unit span is missing")
    require(
        all(node.span is not None for node in unit.declarations),
        "a declaration span is missing",
    )

    first, last = unit.declarations
    require(
        first.span is not None
        and last.span is not None
        and unit.span.start == first.span.start
        and unit.span.end == last.span.end
        and unit.span.source_name == "spans.apex",
        "source-unit span does not cover first through last declaration",
    )
    require(
        first.span.end.offset < last.span.start.offset
        and unit.span.end.offset < len(source),
        "declaration spans are unordered or source-unit span includes trailing trivia",
    )


def main() -> None:
    test_each_kind_and_all_ordered_pairs()
    test_all_kinds_order_repetition_comments_and_determinism()
    test_source_aware_failures_and_compatibility_apis()
    test_source_unit_and_declaration_spans()

    print("AFP-P11.2C heterogeneous source-unit parser smoke test passed.")
    print("Six standalone kinds and all 36 ordered pairs: PASS")
    print("Heterogeneous ordering, repetition, comments, and equality: PASS")
    print("Source-aware failures and compatibility APIs: PASS")
    print("Source-unit and declaration spans: PASS")


if __name__ == "__main__":
    main()
