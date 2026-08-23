"""SRA-B zero-directive entry diagnostic regression."""

from language.project import ProjectEntryPointError, build_project


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    project = build_project({"main.apex": "function Helper(value) { return value * 2 }"})

    try:
        project.resolve_entry()
    except ProjectEntryPointError as exc:
        require(
            str(exc) == "A project with no directives has no entry directive to execute.",
            "zero-directive entry diagnostic changed: " + repr(str(exc)),
        )
    else:
        raise AssertionError("zero-directive project unexpectedly resolved an entry directive")

    print("P11 SRA-B zero-directive entry diagnostic smoke test passed.")
    print("Zero-directive rejection: PASS")
    print("Exact user-facing diagnostic: PASS")


if __name__ == "__main__":
    main()
