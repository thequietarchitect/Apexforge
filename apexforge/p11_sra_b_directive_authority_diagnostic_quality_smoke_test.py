"""SRA-B directive authority diagnostic-quality regression."""

from language.project import ProjectValidationError, build_project


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source = """directive Main {
    authority MissingAegis
}"""
    try:
        build_project({"missing-authority.apex": source}, entry="Main")
    except ProjectValidationError as exc:
        require(len(exc.diagnostics) == 1, "diagnostic cardinality changed")
        diagnostic = exc.diagnostics[0]
        require(diagnostic.code == "APX-VALIDATE-007", "missing authority did not receive canonical validation code")
        require(diagnostic.stage == "validate", "validation stage changed")
        require(diagnostic.message == "Directive 'directive:Main' references undefined authority 'MissingAegis'.", "missing-authority message changed: " + repr(diagnostic.message))
        require(diagnostic.air_id == "directive:Main", "missing authority lost owning directive AIR identity")
        require(diagnostic.span is not None and diagnostic.span.source_name == "missing-authority.apex", "missing authority lost directive-level source attribution")
    else:
        raise AssertionError("ProjectBuilder accepted an undefined directive authority")

    print("P11 SRA-B directive authority diagnostic-quality smoke test passed.")
    print("Canonical APX-VALIDATE-007 classification: PASS")
    print("Owning directive AIR identity: PASS")
    print("Directive-level source attribution: PASS")


if __name__ == "__main__":
    main()
