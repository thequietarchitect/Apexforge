"""SRA-B workflow target closed-reference regression."""

from language.compiler import compile_source
from language.project import ProjectValidationError, build_project
from language.validation.runtime_validator import RuntimeValidator, UndefinedReferenceError


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    missing_source = "directive Main {\n    state count : int = 0\n}\n\nworkflow Start {\n    invoke Missing\n}"
    declared_source = "directive Main {\n    state count : int = 0\n}\n\nworkflow Start {\n    invoke Main\n}"

    program = compile_source(missing_source)
    try:
        RuntimeValidator().validate(program)
    except UndefinedReferenceError as exc:
        require(
            str(exc) == "Workflow 'workflow:Start' invokes undefined directive 'Missing'.",
            "direct RuntimeValidator missing-workflow-target diagnostic changed: " + repr(str(exc)),
        )
    else:
        raise AssertionError("RuntimeValidator accepted an undefined workflow invocation target")

    try:
        build_project({"main.apex": missing_source}, entry="Main")
    except ProjectValidationError as exc:
        require(len(exc.diagnostics) == 1, "project validation diagnostic cardinality changed")
        diagnostic = exc.diagnostics[0]
        require(diagnostic.code == "APX-VALIDATE-002", "project workflow diagnostic code changed")
        require(diagnostic.stage == "validate", "project validation stage changed")
        require(
            diagnostic.message == "Workflow 'workflow:Start' invokes undefined directive 'Missing'.",
            "project validation missing-workflow-target message changed: " + repr(diagnostic.message),
        )
    else:
        raise AssertionError("ProjectBuilder accepted an undefined workflow invocation target")

    valid = build_project({"main.apex": declared_source}, entry="Main")
    require(valid.entry_directive == "directive:Main", "declared workflow target positive control failed")

    print("P11 SRA-B workflow target closure smoke test passed.")
    print("Direct RuntimeValidator workflow closure: PASS")
    print("ProjectBuilder APX-VALIDATE-002 propagation: PASS")
    print("Declared workflow target positive control: PASS")


if __name__ == "__main__":
    main()
