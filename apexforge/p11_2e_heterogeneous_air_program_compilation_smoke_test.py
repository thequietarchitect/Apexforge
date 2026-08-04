"""Focused coverage for P11.2E heterogeneous AIRProgram compilation."""

from __future__ import annotations

import hashlib
from itertools import product
from pathlib import Path

from air.linker import AIRProgramLinker, DuplicateLinkDefinitionError, link_programs
from air.model import AIRAuthority, AIRProgram, DirectiveAuthority
from air.serialization import (
    AmbiguousLegacyDirectiveAuthorityError,
    air_from_dict,
    air_to_dict,
)
from language.compiler import compile_node, compile_source, compile_source_with_map
from language.parser import (
    ParseError,
    SourceUnitNode,
    parse,
    parse_headerless_directive_source_unit,
    parse_source_unit,
)
from language.project import build_project


DECLARATIONS = (
    ("directive", "directive Main {}", "directives", "directive:Main"),
    ("function", "function Helper() { return 0 }", "functions", "function:Helper"),
    ("workflow", "workflow Flow {}", "workflows", "workflow:Flow"),
    ("authority", "authority Aegis {}", "authorities", "authority:Aegis"),
    ("principal", "principal Operator {}", "principals", "principal:Operator"),
    ("role", "role Architect {}", "roles", "role:Architect"),
)
ALL_SIX = "\n".join(item[1] for item in DECLARATIONS)
HISTORICAL_PROGRAM_KEYS = (
    "version", "states", "events", "authority_checks", "causal_decisions",
    "directives", "requirements", "authorities", "principals", "roles", "functions",
)
FIXTURE_HASHES = {
    "apexforge.json": "8154bdc7668b7ba7979557e27db8c97ea945b3ca8993d7b0230fb3c550463405",
    "main.apex": "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as error:
        return error
    raise AssertionError(message)


def _collection_identity(collection: str, value: object) -> str:
    identifier = getattr(value, "id", None)
    if isinstance(identifier, str):
        return identifier
    if collection == "roles":
        return f"role:{value.name}"
    raise AssertionError(f"No declaration identity projection for {collection}")


def test_single_nodes_and_collection_placement() -> None:
    for kind, source, collection, air_id in DECLARATIONS:
        artifact = compile_source_with_map(source, source_name=f"{kind}.apex")
        require(isinstance(artifact.program, AIRProgram), f"{kind} did not compile to AIRProgram")
        require(
            sum(
                _collection_identity(collection, value) == air_id
                for value in getattr(artifact.program, collection)
            ) == 1,
            f"{kind} was not placed in AIRProgram.{collection}",
        )
        require(
            len(artifact.source_map.find(air_id=air_id, kind=kind)) == 1,
            f"{kind} declaration source-map entry is missing",
        )
        node_program = compile_node(parse(source, source_name=f"{kind}-node.apex"))
        require(isinstance(node_program, AIRProgram), f"compile_node returned non-program for {kind}")
        if kind == "role":
            require(len(node_program.roles) == 1, "role compilation returned standalone AIRRole")
        require(isinstance(compile_source(source), AIRProgram), f"compile_source failed for {kind}")


def test_pairs_all_six_source_maps_and_determinism() -> None:
    pair_count = 0
    for first, second in product(DECLARATIONS, repeat=2):
        source = first[1] + "\n" + second[1]
        artifact = compile_source_with_map(
            source,
            source_name=f"{first[0]}-{second[0]}.apex",
        )
        require(isinstance(artifact.program, AIRProgram), "ordered pair returned non-program")

        target_collections = {first[2], second[2]}
        for collection in target_collections:
            expected_count = sum(
                len(getattr(compile_source(item[1]), collection))
                for item in (first, second)
            )
            require(
                len(getattr(artifact.program, collection)) == expected_count,
                f"ordered pair {first[0]}/{second[0]} dropped {collection}",
            )
        for item in (first, second):
            require(
                sum(
                    _collection_identity(item[2], value) == item[3]
                    for value in getattr(artifact.program, item[2])
                ) == (2 if first[3] == second[3] else 1),
                f"ordered pair {first[0]}/{second[0]} lost {item[0]}",
            )

        expected_entries = ((first[0], first[3]), (second[0], second[3]))
        observed_entries = tuple(
            (entry.kind, entry.air_id)
            for entry in artifact.source_map.entries
            if (entry.kind, entry.air_id) in expected_entries
        )
        require(
            observed_entries == expected_entries,
            f"ordered pair {first[0]}/{second[0]} source maps lost physical order",
        )
        matching_offsets = tuple(
            entry.span.start.offset
            for entry in artifact.source_map.entries
            if (entry.kind, entry.air_id) in expected_entries
        )
        require(
            len(matching_offsets) == 2 and matching_offsets[0] < matching_offsets[1],
            f"ordered pair {first[0]}/{second[0]} declaration spans are incomplete",
        )
        pair_count += 1
    require(pair_count == 36, "all 36 ordered declaration pairs were not compiled")

    first = compile_source_with_map(ALL_SIX, source_name="all-six.apex")
    second = compile_source_with_map(ALL_SIX, source_name="all-six.apex")
    require(first.program == second.program, "repeated compilation produced unequal AIR")
    require(first.source_map == second.source_map, "repeated compilation produced unequal maps")
    require(
        len(first.program.directives) == len(first.program.functions)
        == len(first.program.workflows) == len(first.program.authorities)
        == len(first.program.roles) == 1
        and tuple(item.id for item in first.program.principals)
        == ("principal:Main", "principal:Operator"),
        "one or more all-six declarations were dropped or misplaced",
    )
    expected = tuple((item[0], item[3]) for item in DECLARATIONS)
    observed = tuple(
        (entry.kind, entry.air_id)
        for entry in first.source_map.entries
        if (entry.kind, entry.air_id) in expected
    )
    require(observed == expected, "all-six declaration maps lost source order")


def test_same_file_functions_and_independent_orders() -> None:
    twice = "function Twice(value : int) : int { return value * 2 }"
    entry = """directive Entry {
    state entry_count = 2
    cause entry_flow {
        path entry_path @ 10 {
            set entry_count = Twice(entry_count)
        }
    }
}"""
    caller = "function Caller(value : int) : int { return Twice(value) }"

    before = compile_source(twice + "\nrole Separator {}\n" + entry)
    after = compile_source(entry + "\nrole Separator {}\n" + twice)
    require(
        before.functions == after.functions
        and before.functions[0].id == "function:Twice",
        "moving a same-file function around another declaration lost its signature",
    )
    require(
        before.causal_decisions[0].paths[0].assignments[0].value.target == "Twice"
        and after.causal_decisions[0].paths[0].assignments[0].value.target == "Twice",
        "same-file directive function reference was not preserved",
    )

    functions_source = caller + "\nauthority Separator {}\n" + twice
    functions_first = compile_source(functions_source)
    functions_second = compile_source(functions_source)
    require(functions_first == functions_second, "same-file function compilation was nondeterministic")
    require(
        tuple((item.id, item.order) for item in functions_first.functions)
        == (("function:Caller", 0), ("function:Twice", 1)),
        "functions separated by another declaration lost local order",
    )
    require(
        functions_first.functions[0].return_expression.target == "Twice",
        "same-file function-to-function reference was not retained",
    )

    ordered = compile_source(
        "directive First {}\n"
        + twice
        + "\nprincipal Separator {}\n"
        + "directive Second {}"
    )
    require(
        tuple((item.id, item.order) for item in ordered.directives)
        == (("directive:First", 0), ("directive:Second", 1)),
        "directives separated by heterogeneous declarations lost local order",
    )


def test_directive_authority_workflow_and_compatibility_flag() -> None:
    directives = compile_source("directive First {}\ndirective Second {}")
    require(
        tuple((item.id, item.order) for item in directives.directives)
        == (("directive:First", 0), ("directive:Second", 1)),
        "P11.2B local directive ordering changed",
    )
    separated = compile_source(
        "authority Aegis { capability Execute }\n"
        "directive Main { authority Aegis }"
    )
    require(
        len(separated.authorities) == 1
        and isinstance(separated.authorities[0], AIRAuthority),
        "top-level authority was not stored as AIRAuthority",
    )
    require(
        separated.directives[0].authorities
        == (DirectiveAuthority(name="Aegis"),),
        "directive authority reference was not stored on AIRDirective",
    )
    require(
        all(isinstance(item, AIRAuthority) for item in separated.authorities),
        "directive authority reference leaked into AIRProgram.authorities",
    )
    workflow = compile_source(
        "workflow Flow { invoke Detect invoke Contain invoke Recover }"
    ).workflows[0]
    require(
        tuple(item.target for item in workflow.invocations)
        == ("Detect", "Contain", "Recover"),
        "workflow invocation order changed",
    )
    compatible = compile_source_with_map(
        ALL_SIX,
        source_name="compatibility-flag.apex",
        allow_headerless_multi_directive=False,
    )
    require(
        isinstance(compatible.program, AIRProgram)
        and len(compatible.program.workflows) == 1,
        "compatibility flag disabled heterogeneous source-unit compilation",
    )


def test_linker_integration_and_duplicate_workflows() -> None:
    fragments = tuple(compile_source(item[1]) for item in DECLARATIONS)
    linked = link_programs(*fragments)
    require(
        len(linked.authorities) == 1
        and len(linked.principals) == 2
        and len(linked.roles) == 1
        and len(linked.workflows) == 1
        and len(linked.functions) == 1
        and len(linked.directives) == 1,
        "linker dropped a promoted declaration fragment",
    )
    error = require_raises(
        DuplicateLinkDefinitionError,
        lambda: AIRProgramLinker().link(
            (compile_source("workflow Flow {}"), compile_source("workflow Flow {}"))
        ),
        "duplicate workflow IDs were accepted",
    )
    require(
        error.owner == "workflow"
        and error.identifier == "workflow:Flow"
        and str(error)
        == "Duplicate workflow definition 'workflow:Flow' while linking AIR programs.",
        "duplicate workflow diagnostic was not deterministic",
    )


def test_serialization_and_legacy_authority_migration() -> None:
    directive_data = air_to_dict(compile_source("directive Main {}"))
    function_data = air_to_dict(compile_source("function Helper() { return 0 }"))
    require(
        tuple(directive_data) == HISTORICAL_PROGRAM_KEYS
        and tuple(function_data) == HISTORICAL_PROGRAM_KEYS,
        "empty P11.2E fields changed historical directive/function AIR output",
    )
    require(
        "authorities" not in directive_data["directives"][0]
        and "workflows" not in directive_data,
        "empty new fields were serialized",
    )

    mixed = compile_source(
        "authority Aegis { capability Execute }\n"
        "directive Main { authority Aegis }"
    )
    mixed_data = air_to_dict(mixed)
    require(
        mixed_data["authorities"]
        == [{
            "id": "authority:Aegis",
            "name": "Aegis",
            "capabilities": ["Execute"],
            "inherits": [],
        }]
        and mixed_data["directives"][0]["authorities"] == [{"name": "Aegis"}],
        "mixed top-level and directive authority serialization was not separated",
    )
    require(air_from_dict(mixed_data) == mixed, "mixed authority program did not round-trip")

    workflow_program = compile_source("workflow Flow { invoke Detect invoke Recover }")
    workflow_data = air_to_dict(workflow_program)
    require(
        workflow_data["workflows"][0]["invocations"]
        == [{"target": "Detect"}, {"target": "Recover"}],
        "non-empty workflow serialization is missing",
    )
    backward = air_from_dict(directive_data)
    require(
        backward.workflows == () and backward.directives[0].authorities == (),
        "older documents without new fields were not accepted",
    )

    requirement_program = compile_source(
        "directive Main { requires Execute }"
    )
    require(
        air_from_dict(air_to_dict(requirement_program)).requirements
        == requirement_program.requirements,
        "requirements did not survive serialization",
    )

    for source, collection in (
        ("authority Aegis {}", "authorities"),
        ("principal Operator { authority Aegis }", "principals"),
        ("role Architect { authority Aegis }", "roles"),
        ("workflow Flow { invoke Main }", "workflows"),
    ):
        original = compile_source(source)
        restored = air_from_dict(air_to_dict(original))
        require(
            getattr(restored, collection) == getattr(original, collection),
            f"{collection} declaration program did not deserialize correctly",
        )

    legacy_single = dict(directive_data)
    legacy_single["authorities"] = [{"name": "Aegis"}]
    migrated = air_from_dict(legacy_single)
    require(
        migrated.authorities == ()
        and migrated.directives[0].authorities
        == (DirectiveAuthority(name="Aegis"),),
        "legacy single-directive authority references were not migrated",
    )
    canonical = air_from_dict(air_to_dict(compile_source("authority Aegis {}")))
    require(
        canonical.authorities
        == (AIRAuthority("authority:Aegis", "Aegis", (), ()),),
        "canonical AIRAuthority data was not deserialized as a declaration",
    )

    ambiguous_data = air_to_dict(
        compile_source("directive First {}\ndirective Second {}")
    )
    ambiguous_data["authorities"] = [{"name": "Aegis"}]
    first_error = require_raises(
        AmbiguousLegacyDirectiveAuthorityError,
        lambda: air_from_dict(ambiguous_data),
        "ambiguous legacy directive authority ownership was guessed",
    )
    second_error = require_raises(
        AmbiguousLegacyDirectiveAuthorityError,
        lambda: air_from_dict(ambiguous_data),
        "ambiguous legacy directive authority ownership was nondeterministic",
    )
    require(str(first_error) == str(second_error), "ambiguous legacy diagnostic changed")


def test_project_compatibility_entry_and_parser_boundaries() -> None:
    legacy = build_project({"all.apex": ALL_SIX}, entry="Main")
    module = build_project(
        {"all.apex": "module demo.main\n\n" + ALL_SIX},
        entry="Main",
    )
    for build in (legacy, module):
        require(
            len(build.program.directives) == 1
            and len(build.program.functions) == 1
            and len(build.program.workflows) == 1
            and len(build.program.authorities) == 1
            and len(build.program.roles) == 1,
            "project compilation dropped a heterogeneous declaration",
        )
        require(
            build.resolve_entry() == "directive:Main"
            and build.entry_directive == "directive:Main",
            "directive entry selection changed",
        )

    unit = parse_source_unit(ALL_SIX, source_name="parser-boundary.apex")
    require(
        isinstance(unit, SourceUnitNode) and len(unit.declarations) == 6,
        "P11.2C source-unit parser behavior changed",
    )
    require_raises(
        ParseError,
        lambda: parse("directive Main {}\nworkflow Flow {}"),
        "parse() stopped enforcing its single-declaration boundary",
    )
    require_raises(
        ParseError,
        lambda: parse_headerless_directive_source_unit(
            "directive Main {}\nworkflow Flow {}"
        ),
        "P11.2B parser API accepted a heterogeneous unit",
    )


def test_validation_fixture_is_unchanged() -> None:
    fixture_root = Path(__file__).resolve().parent.parent / "examples" / "P11Validation"
    observed = {
        name: hashlib.sha256((fixture_root / name).read_bytes()).hexdigest()
        for name in FIXTURE_HASHES
    }
    require(observed == FIXTURE_HASHES, "examples/P11Validation fixture was modified")


def main() -> None:
    test_single_nodes_and_collection_placement()
    test_pairs_all_six_source_maps_and_determinism()
    test_same_file_functions_and_independent_orders()
    test_directive_authority_workflow_and_compatibility_flag()
    test_linker_integration_and_duplicate_workflows()
    test_serialization_and_legacy_authority_migration()
    test_project_compatibility_entry_and_parser_boundaries()
    test_validation_fixture_is_unchanged()

    print("AFP-P11.2E heterogeneous AIRProgram compilation smoke test passed.")
    print("Six single forms, all 36 pairs, and all-six source units: PASS")
    print("Same-file function integration and independent local orders: PASS")
    print("Directive authority separation and workflow order: PASS")
    print("Linker declaration merges and workflow duplicate diagnostics: PASS")
    print("Serialization, requirements, and legacy authority migration: PASS")
    print("Legacy/module project compilation and directive entry selection: PASS")
    print("Parser boundaries and P11Validation fixture preservation: PASS")


if __name__ == "__main__":
    main()
