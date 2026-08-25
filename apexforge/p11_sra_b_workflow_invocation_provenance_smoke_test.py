"""SRA-B workflow invocation diagnostic-provenance regression."""

from language.project import ProjectValidationError, build_project


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source = """workflow Start {
    invoke Missing
}"""
    try:
        build_project({"workflow-missing.apex": source})
    except ProjectValidationError as exc:
        require(len(exc.diagnostics) == 1, "diagnostic cardinality changed")
        diagnostic = exc.diagnostics[0]
        require(diagnostic.code == "APX-VALIDATE-002", "workflow invocation validation code changed")
        require(diagnostic.message == "Workflow 'workflow:Start' invokes undefined directive 'Missing'.", "workflow invocation message changed: " + repr(diagnostic.message))
        require(diagnostic.air_id == "workflow:Start", "workflow invocation lost owning workflow AIR identity")
        require(diagnostic.span is not None and diagnostic.span.source_name == "workflow-missing.apex" and diagnostic.span.start.line == 2, "workflow invocation lost exact invoke-site source attribution")
    else:
        raise AssertionError("ProjectBuilder accepted an undefined workflow invocation")

    print("P11 SRA-B workflow invocation provenance smoke test passed.")
    print("APX-VALIDATE-002 classification: PASS")
    print("Owning workflow AIR identity: PASS")
    print("Exact invoke-site source attribution: PASS")


if __name__ == "__main__":
    main()
