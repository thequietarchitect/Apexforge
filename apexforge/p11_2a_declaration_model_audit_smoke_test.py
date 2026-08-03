"""P11.2A current declaration-model compatibility audit.

This smoke test records behavior that predates P11.2A. It deliberately does
not add declaration syntax, compiler behavior, AIR shapes, or runtime policy.
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from air.model import AIRRole
from air.serialization import air_to_dict
from language.compiler import compile_source_with_map
from language.project import (
    ProjectCompilationError,
    ProjectEntryPointError,
    ProjectLinkError,
    ProjectValidationError,
    build_project,
)
from tooling.project_loader import load_project
from type_system.closure import collect_linked_specializations
from type_system.lowering import lower_linked_generics


ENTRY_SOURCE = """directive Entry {
    state entry_count = 2
    event entry_done

    cause entry_flow {
        path entry_path @ 10 {
            set entry_count = Twice(entry_count)
            invoke Worker
            emit entry_done
        }
    }
}
"""


WORKER_SOURCE = """directive Worker {
    state worker_count = 1
    event worker_done

    cause worker_flow {
        path worker_path @ 10 {
            add worker_count 1
            emit worker_done
        }
    }
}
"""


CALLER_SOURCE = """function Caller(value : int) : int {
    return Callee(value)
}
"""


CALLEE_SOURCE = """function Callee(value : int) : int {
    return Twice(value)
}
"""


TWICE_SOURCE = """function Twice(value : int) : int {
    return value * 2
}
"""


GENERIC_SOURCE = """function Identity<T : numeric>(value : T) : T {
    return value
}
"""


GENERIC_USER_SOURCE = """function UseIdentity(value : int) : int {
    return Identity<int>(value)
}
"""


COLLISION_DIRECTIVE_SOURCE = """directive Collision {
    state collision_state = 0
    event collision_event

    cause collision_cause {
        path collision_path @ 1 {
            emit collision_event
        }
    }
}
"""


COLLISION_FUNCTION_SOURCE = """function Collision(value : int) : int {
    return value
}
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as exc:
        return exc
    raise AssertionError(message)


def diagnostic_of(error):
    diagnostics = tuple(getattr(error, "diagnostics", ()) or ())
    require(len(diagnostics) == 1, "expected exactly one audit diagnostic")
    return diagnostics[0]


def core_sources() -> dict[str, str]:
    # The insertion order is intentionally the reverse of canonical filename
    # order. ProjectBuilder must normalize it before compilation and linking.
    return {
        "50-twice.apex": TWICE_SOURCE,
        "40-callee.apex": CALLEE_SOURCE,
        "30-caller.apex": CALLER_SOURCE,
        "20-worker.apex": WORKER_SOURCE,
        "10-entry.apex": ENTRY_SOURCE,
    }


def test_cross_source_declarations_and_ordering() -> None:
    first = build_project(core_sources())
    second = build_project(dict(reversed(tuple(core_sources().items()))))

    require(
        tuple(unit.name for unit in first.source_units)
        == (
            "10-entry.apex",
            "20-worker.apex",
            "30-caller.apex",
            "40-callee.apex",
            "50-twice.apex",
        ),
        "legacy project source order is not canonical filename order",
    )
    require(
        tuple((item.id, item.order) for item in first.program.directives)
        == (("directive:Entry", 0), ("directive:Worker", 1)),
        "linked directive identities or orders changed",
    )
    require(
        tuple((item.id, item.order) for item in first.program.functions)
        == (
            ("function:Caller", 0),
            ("function:Callee", 1),
            ("function:Twice", 2),
        ),
        "linked function identities or orders changed",
    )
    require(
        air_to_dict(first.program) == air_to_dict(second.program),
        "mapping insertion order changed linked AIR",
    )

    # These exact prefixes are existing compiler identities, not a new
    # namespace design. Nested directive identities remain globally short.
    require(
        tuple(item.id for item in first.program.principals)
        == ("principal:Entry", "principal:Worker"),
        "directive principal identities changed",
    )
    require(
        tuple(item.id for item in first.program.authority_checks)
        == ("auth:Entry", "auth:Worker"),
        "directive authority-check identities changed",
    )
    require(
        tuple(item.id for item in first.program.states)
        == ("state:entry_count", "state:worker_count"),
        "state identities changed",
    )
    require(
        tuple(item.id for item in first.program.events)
        == ("event:entry_done", "event:worker_done"),
        "event identities changed",
    )
    require(
        tuple(item.id for item in first.program.causal_decisions)
        == ("cause:entry_flow", "cause:worker_flow"),
        "cause identities changed",
    )
    require(
        tuple(
            path.id
            for decision in first.program.causal_decisions
            for path in decision.paths
        )
        == ("path:entry_path", "path:worker_path"),
        "path identities changed",
    )

    invocation = first.program.causal_decisions[0].paths[0].invocations[0]
    require(
        invocation.target == "Worker",
        "cross-directive invocation did not preserve its short reference",
    )
    caller = first.program.functions[0]
    require(
        caller.return_expression.target == "Callee",
        "forward cross-function call target changed",
    )


def test_one_source_boundary_and_invalid_nesting() -> None:
    scenarios = (
        ("two-directives.apex", ENTRY_SOURCE + "\n" + WORKER_SOURCE),
        ("two-functions.apex", CALLER_SOURCE + "\n" + CALLEE_SOURCE),
        ("mixed-function-first.apex", CALLER_SOURCE + "\n" + ENTRY_SOURCE),
        ("mixed-directive-first.apex", ENTRY_SOURCE + "\n" + CALLER_SOURCE),
    )

    for source_name, source in scenarios:
        error = require_raises(
            ProjectCompilationError,
            lambda source_name=source_name, source=source: build_project(
                {source_name: source}
            ),
            "a source containing two top-level declarations was accepted",
        )
        diagnostic = diagnostic_of(error)
        require(
            diagnostic.stage == "parse"
            and diagnostic.code == "APX-PARSE-001"
            and diagnostic.span is not None
            and diagnostic.span.source_name == source_name,
            "one-declaration-per-source rejection lost its stable category",
        )

    nested_name = "nested-function.apex"
    nested_error = require_raises(
        ProjectCompilationError,
        lambda: build_project(
            {
                nested_name: (
                    "directive Outer {\n"
                    "    function Inner(value) { return value }\n"
                    "}\n"
                )
            }
        ),
        "a function nested in a directive was accepted",
    )
    nested_diagnostic = diagnostic_of(nested_error)
    require(
        nested_diagnostic.stage == "parse"
        and nested_diagnostic.code == "APX-PARSE-003"
        and nested_diagnostic.span is not None
        and nested_diagnostic.span.source_name == nested_name,
        "invalid nesting lost same-file source attribution",
    )


def test_duplicates_collisions_and_diagnostics() -> None:
    duplicate_function = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a-duplicate.apex": CALLER_SOURCE,
                "b-duplicate.apex": CALLER_SOURCE,
            }
        ),
        "duplicate functions across files were accepted",
    )
    function_diagnostic = diagnostic_of(duplicate_function)
    require(
        function_diagnostic.stage == "link"
        and function_diagnostic.code == "APX-LINK-001"
        and function_diagnostic.air_id == "function:Caller"
        and function_diagnostic.span is not None
        and function_diagnostic.span.source_name == "a-duplicate.apex"
        and tuple(span.source_name for span in function_diagnostic.related_spans)
        == ("b-duplicate.apex",),
        "cross-file duplicate diagnostic lost canonical source attribution",
    )

    duplicate_directive = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "a-directive.apex": COLLISION_DIRECTIVE_SOURCE,
                "b-directive.apex": COLLISION_DIRECTIVE_SOURCE,
            }
        ),
        "duplicate directives across files were accepted",
    )
    require(
        diagnostic_of(duplicate_directive).code == "APX-LINK-001",
        "duplicate directive rejection changed category",
    )

    cross_kind = build_project(
        {
            "directive.apex": COLLISION_DIRECTIVE_SOURCE,
            "function.apex": COLLISION_FUNCTION_SOURCE,
        }
    )
    require(
        tuple(item.id for item in cross_kind.program.directives)
        == ("directive:Collision",)
        and tuple(item.id for item in cross_kind.program.functions)
        == ("function:Collision",),
        "cross-kind identical short names no longer coexist",
    )

    undefined = require_raises(
        ProjectValidationError,
        lambda: build_project(
            {
                "caller.apex": (
                    "function Broken(value : int) : int {\n"
                    "    return Missing(value)\n"
                    "}\n"
                ),
                "other.apex": TWICE_SOURCE,
            }
        ),
        "undefined cross-file function call was accepted",
    )
    undefined_diagnostic = diagnostic_of(undefined)
    require(
        undefined_diagnostic.stage == "validate"
        and undefined_diagnostic.code == "APX-VALIDATE-003"
        and undefined_diagnostic.span is not None
        and undefined_diagnostic.span.source_name == "caller.apex",
        "cross-file resolution failure lost its call-site diagnostic",
    )


def test_entry_and_generic_compatibility() -> None:
    core = build_project(core_sources())
    require(
        core.resolve_entry("Entry") == "directive:Entry"
        and core.resolve_entry("directive:Worker") == "directive:Worker",
        "short or canonical entry resolution changed",
    )
    require_raises(
        ProjectEntryPointError,
        core.resolve_entry,
        "multi-directive entry ambiguity was accepted",
    )

    single = build_project({"solo.apex": WORKER_SOURCE})
    require(
        single.resolve_entry() == "directive:Worker",
        "one-directive entry fallback changed",
    )
    function_only = build_project({"function.apex": TWICE_SOURCE})
    require_raises(
        ProjectEntryPointError,
        function_only.resolve_entry,
        "zero-directive entry selection was accepted",
    )

    generic = build_project(
        {
            "20-identity.apex": GENERIC_SOURCE,
            "10-use.apex": GENERIC_USER_SOURCE,
        }
    )
    identity = generic.program.functions[1]
    require(
        identity.id == "function:Identity"
        and tuple(item.name for item in identity.type_parameters) == ("T",)
        and identity.type_parameters[0].owner == "function:Identity",
        "generic declaration identity changed across source linking",
    )
    manifest = collect_linked_specializations(generic.program)
    require(
        manifest.canonical_ids == ("Identity<int>",),
        "cross-source generic specialization closure changed",
    )
    lowered = lower_linked_generics(generic.program)
    require(
        lowered.canonical_ids == ("Identity<int>",)
        and len(lowered.specialized_functions) == 1,
        "cross-source generic specialization lowering changed",
    )


def test_other_frozen_top_level_forms() -> None:
    # The P10 grammar recognizes all four forms. P11.2A records their current
    # non-project boundaries without promoting them into linked declarations.
    for source in (
        "workflow Flow { invoke Entry }",
        "authority Observer { capability Read }",
        "principal User { role Observer }",
    ):
        error = require_raises(
            ProjectCompilationError,
            lambda source=source: build_project({"form.apex": source}),
            "parsed-only top-level form entered the project pipeline",
        )
        diagnostic = diagnostic_of(error)
        require(
            diagnostic.stage == "compile"
            and diagnostic.code == "APX-COMPILE-007",
            "parsed-only form changed compiler rejection category",
        )

    role = compile_source_with_map(
        "role Observer { authority ReadOnly }",
        source_name="role.apex",
    )
    require(
        isinstance(role.program, AIRRole),
        "standalone role lowering boundary changed",
    )
    require_raises(
        ProjectCompilationError,
        lambda: build_project(
            {"role.apex": "role Observer { authority ReadOnly }"}
        ),
        "standalone AIRRole entered the AIRProgram project pipeline",
    )


def test_manifest_source_order() -> None:
    with TemporaryDirectory(prefix="apexforge-p11-2a-") as temporary:
        root = Path(temporary)
        source_root = root / "src"
        source_root.mkdir()
        (source_root / "20-worker.apex").write_text(
            WORKER_SOURCE,
            encoding="utf-8",
        )
        (source_root / "10-entry.apex").write_text(
            ENTRY_SOURCE,
            encoding="utf-8",
        )
        (source_root / "30-twice.apex").write_text(
            TWICE_SOURCE,
            encoding="utf-8",
        )
        manifest_path = root / "apexforge.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "name": "P11_2A_Audit",
                    # Authored in reverse order; ProjectManifest's frozen
                    # behavior canonicalizes by casefolded relative path.
                    "sources": [
                        "src/30-twice.apex",
                        "src/20-worker.apex",
                        "src/10-entry.apex",
                    ],
                    "entry": "Entry",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        loaded = load_project(root)
        expected = (
            "src/10-entry.apex",
            "src/20-worker.apex",
            "src/30-twice.apex",
        )
        require(
            loaded.manifest.sources == expected
            and tuple(source.name for source in loaded.sources) == expected,
            "loader did not preserve canonical manifest source order",
        )
        built = build_project(
            loaded.source_mapping(),
            entry=loaded.manifest.entry,
        )
        require(
            tuple(item.id for item in built.program.directives)
            == ("directive:Entry", "directive:Worker")
            and built.entry_directive == "directive:Entry",
            "manifest order was not preserved through project linking",
        )


def main() -> None:
    test_cross_source_declarations_and_ordering()
    test_one_source_boundary_and_invalid_nesting()
    test_duplicates_collisions_and_diagnostics()
    test_entry_and_generic_compatibility()
    test_other_frozen_top_level_forms()
    test_manifest_source_order()

    print("AFP-P11.2A declaration-model audit smoke test passed.")
    print("Cross-source directives, functions, and mixed declarations: PASS")
    print("One-declaration-per-source and invalid-nesting boundaries: PASS")
    print("Canonical identities, ordering, duplicates, and collisions: PASS")
    print("Forward resolution, entries, and linked generics: PASS")
    print("Source-aware diagnostics and manifest ordering: PASS")
    print("Parsed-only top-level declaration boundaries: PASS")


if __name__ == "__main__":
    main()
