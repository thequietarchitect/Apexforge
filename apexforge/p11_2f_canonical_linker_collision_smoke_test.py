"""P11.2F-B canonical linker collision contract coverage."""

from __future__ import annotations

from air.linker import DuplicateLinkDefinitionError, link_programs
from air.model import AIRDirective, AIRProgram
from air.types import AIR_VERSION
from language.compiler import compile_source
from language.project import (
    ProjectEntryPointError,
    build_project,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_collision(
    owner: str,
    identifier: str,
    first_source: str,
    second_source: str,
) -> None:
    messages = []

    for sources in (
        (first_source, second_source),
        (second_source, first_source),
    ):
        try:
            link_programs(*(compile_source(source) for source in sources))
        except DuplicateLinkDefinitionError as error:
            require(error.owner == owner, f"{owner} collision owner changed")
            require(
                error.identifier == identifier,
                f"{owner} collision identity changed: {error.identifier!r}",
            )
            messages.append(str(error))
        else:
            raise AssertionError(
                f"case-variant {owner} definitions were accepted"
            )

    expected = (
        f"Duplicate {owner} definition {identifier!r} "
        "while linking AIR programs."
    )
    require(
        tuple(messages) == (expected, expected),
        f"{owner} collision diagnostic depends on unit order",
    )


def directive_program(identifier: str, name: str) -> AIRProgram:
    return AIRProgram(
        version=AIR_VERSION,
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(
            AIRDirective(
                id=identifier,
                name=name,
                principal="principal:Shared",
                authority_checks=(),
                causal_decisions=(),
            ),
        ),
        requirements=(),
    )


def test_proven_casefolded_consumers() -> None:
    directive_messages = []

    for programs in (
        (
            directive_program("directive:Sentinel", "Sentinel"),
            directive_program("directive:sentinel", "sentinel"),
        ),
        (
            directive_program("directive:sentinel", "sentinel"),
            directive_program("directive:Sentinel", "Sentinel"),
        ),
    ):
        try:
            link_programs(*programs)
        except DuplicateLinkDefinitionError as error:
            require(
                error.owner == "directive",
                "directive collision owner changed",
            )
            require(
                error.identifier == "directive:sentinel",
                "directive collision identity changed",
            )
            directive_messages.append(str(error))
        else:
            raise AssertionError(
                "case-variant directive definitions were accepted"
            )

    require(
        tuple(directive_messages)
        == (
            "Duplicate directive definition 'directive:sentinel' "
            "while linking AIR programs.",
            "Duplicate directive definition 'directive:sentinel' "
            "while linking AIR programs.",
        ),
        "directive collision diagnostic depends on unit order",
    )

    require_collision(
        "principal",
        "principal:operator",
        "principal Operator {}",
        "principal operator {}",
    )
    require_collision(
        "authority",
        "authority:aegis",
        "authority Aegis {}",
        "authority aegis {}",
    )


def test_exact_duplicate_messages_remain_compatible() -> None:
    try:
        link_programs(
            directive_program("directive:Main", "Main"),
            directive_program("directive:Main", "Main"),
        )
    except DuplicateLinkDefinitionError as error:
        require(
            error.owner == "directive"
            and error.identifier == "directive:Main",
            "historical exact directive diagnostic changed",
        )
        require(
            str(error)
            == (
                "Duplicate directive definition 'directive:Main' "
                "while linking AIR programs."
            ),
            "historical exact directive message changed",
        )
    else:
        raise AssertionError("exact duplicate directive was accepted")

    cases = (
        (
            "principal",
            "principal:Operator",
            "principal Operator {}",
        ),
        (
            "authority",
            "authority:Aegis",
            "authority Aegis {}",
        ),
        (
            "workflow",
            "workflow:Flow",
            "workflow Flow {}",
        ),
    )

    for owner, identifier, source in cases:
        try:
            link_programs(compile_source(source), compile_source(source))
        except DuplicateLinkDefinitionError as error:
            require(
                error.owner == owner and error.identifier == identifier,
                f"historical exact {owner} diagnostic changed",
            )
            require(
                str(error)
                == (
                    f"Duplicate {owner} definition {identifier!r} "
                    "while linking AIR programs."
                ),
                f"historical exact {owner} message changed",
            )
        else:
            raise AssertionError(f"exact duplicate {owner} was accepted")


def test_module_project_preserves_exact_case_identity() -> None:
    project = build_project(
        {
            "a.apex": (
                "module App.A\n\n"
                "directive Alpha {}\n"
            ),
            "b.apex": (
                "module App.B\n\n"
                "directive alpha {}\n"
            ),
        }
    )

    require(
        tuple(
            directive.id
            for directive in project.program.directives
        )
        == (
            "directive:Alpha",
            "directive:alpha",
        ),
        "module project lost exact-case directive identity",
    )
    require(
        tuple(
            principal.id
            for principal in project.program.principals
        )
        == (
            "principal:Alpha",
            "principal:alpha",
        ),
        "module project lost exact-case implicit principal identity",
    )
    require(
        project.resolve_entry("Alpha") == "directive:Alpha"
        and project.resolve_entry("directive:alpha")
        == "directive:alpha",
        "module project entry identity stopped being exact-case",
    )

    try:
        project.resolve_entry("ALPHA")
    except ProjectEntryPointError:
        pass
    else:
        raise AssertionError(
            "module project entry lookup became case-insensitive"
        )


def test_unproven_families_keep_stored_identity_semantics() -> None:
    linked = link_programs(
        compile_source("function Helper() { return 0 }"),
        compile_source("function helper() { return 0 }"),
        compile_source("workflow Flow {}"),
        compile_source("workflow flow {}"),
        compile_source("role Architect {}"),
        compile_source("role architect {}"),
    )

    require(
        tuple(item.id for item in linked.functions)
        == ("function:Helper", "function:helper"),
        "function identity was case-folded without consumer evidence",
    )
    require(
        tuple(item.id for item in linked.workflows)
        == ("workflow:Flow", "workflow:flow"),
        "workflow identity was case-folded without consumer evidence",
    )
    require(
        tuple(item.name for item in linked.roles)
        == ("Architect", "architect"),
        "role identity was case-folded without consumer evidence",
    )


def main() -> None:
    test_proven_casefolded_consumers()
    test_exact_duplicate_messages_remain_compatible()
    test_module_project_preserves_exact_case_identity()
    test_unproven_families_keep_stored_identity_semantics()
    print("P11.2F-B canonical linker collision smoke test passed.")
    print("Directive, principal, and authority casefold collisions: PASS")
    print("Exact duplicate diagnostics remain compatible: PASS")
    print("Module-project exact-case identities preserved: PASS")
    print("Function, workflow, and role stored identities preserved: PASS")


if __name__ == "__main__":
    main()
