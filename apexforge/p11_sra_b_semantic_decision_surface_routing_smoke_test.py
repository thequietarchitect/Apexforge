"""SRA-B semantic-decision CLI surface-routing regression."""

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from tooling.cli import EXIT_SUCCESS, EXIT_USAGE, main


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def invoke(argv):
    stdout = StringIO()
    stderr = StringIO()
    code = main(argv, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def main_test() -> None:
    source = """decision ToolingDecision {
    candidate KeepOpen when routeOpen
    candidate Destroy
    incompatible KeepOpen, Destroy
    converge using "rank.explicit-order" {
        KeepOpen
        Destroy
    }
    paradox elevate
        requires information_loss
}"""

    with TemporaryDirectory() as temporary:
        project = Path(temporary) / "SemanticDecisionRouting"
        project.mkdir()
        (project / "apexforge.json").write_text('{"schema":1,"name":"SemanticDecisionRouting","sources":["main.apex"],"entry":null}', encoding="utf-8")
        (project / "main.apex").write_text(source, encoding="utf-8")

        code, stdout, stderr = invoke(["check", str(project)])
        require(code == EXIT_SUCCESS, "valid semantic-decision check failed")
        require(stderr == "", "semantic-decision check wrote stderr")

        code, stdout, stderr = invoke(["run", str(project)])
        require(code == EXIT_USAGE, "semantic-decision run did not reject at usage boundary")
        require(stdout == "", "semantic-decision run wrote stdout")
        require(
            "run currently does not support semantic-decision projects." in stderr,
            "semantic-decision run boundary diagnostic changed: " + repr(stderr),
        )

        output = Path(temporary) / "semantic-decision-build.json"
        code, stdout, stderr = invoke(["build", str(project), "--output", str(output)])
        require(code == EXIT_USAGE, "semantic-decision build did not reject at usage boundary")
        require(stdout == "", "semantic-decision build wrote stdout")
        require(
            "build currently does not support semantic-decision projects." in stderr,
            "semantic-decision build boundary diagnostic changed: " + repr(stderr),
        )
        require(not output.exists(), "unsupported semantic-decision build created an artifact")

    print("P11 SRA-B semantic-decision surface-routing smoke test passed.")
    print("Semantic-decision check route: PASS")
    print("Run capability boundary: PASS")
    print("Build capability boundary: PASS")
    print("No unsupported artifact emission: PASS")


if __name__ == "__main__":
    main_test()
