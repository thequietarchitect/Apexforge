"""SRA-B directive authority closed-reference regression."""

from language.compiler import compile_source
from language.project import ProjectValidationError, build_project
from language.validation.runtime_validator import RuntimeValidator, UndefinedReferenceError


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    missing_source = """directive Main {
    authority MissingAegis
}"""
    declared_source = """authority Aegis {
    capability Execute
}

directive Main {
    authority Aegis
}"""

    program = compile_source(missing_source)
    try:
        RuntimeValidator().validate(program)
    except UndefinedReferenceError as exc:
        require(
            str(exc) == "Directive 'directive:Main' references undefined authority 'MissingAegis'.",
            "direct RuntimeValidator missing-authority diagnostic changed: " + repr(str(exc)),
        )
    else:
        raise AssertionError("RuntimeValidator accepted an undefined directive authority")

    try:
        build_project({"main.apex": missing_source}, entry="Main")
    except ProjectValidationError as exc:
        require(len(exc.diagnostics) == 1, "project validation diagnostic cardinality changed")
        diagnostic = exc.diagnostics[0]
        require(diagnostic.code == "APX-VALIDATE-999", "project validation fallback code changed")
        require(diagnostic.stage == "validate", "project validation stage changed")
        require(
            diagnostic.message == "Directive 'directive:Main' references undefined authority 'MissingAegis'.",
            "project validation missing-authority message changed: " + repr(diagnostic.message),
        )
    else:
        raise AssertionError("ProjectBuilder accepted an undefined directive authority")

    valid = build_project({"main.apex": declared_source}, entry="Main")
    require(valid.entry_directive == "directive:Main", "declared authority positive control failed")

    print("P11 SRA-B directive authority closure smoke test passed.")
    print("Direct RuntimeValidator closed reference: PASS")
    print("ProjectBuilder validation propagation: PASS")
    print("Declared authority positive control: PASS")


if __name__ == "__main__":
    main()
