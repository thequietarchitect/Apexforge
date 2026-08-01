"""AFP-P10-T3.2 VS Code TextMate syntax smoke test."""

from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

from tooling.vscode_extension import (
    CANONICAL_VSCODE_FOUNDATION_SHA256,
    audit_vscode_extension,
)
from tooling.vscode_syntax import (
    CANONICAL_TEXTMATE_FILETYPE,
    CANONICAL_TEXTMATE_NAME,
    CANONICAL_TEXTMATE_PATH,
    CANONICAL_TEXTMATE_SCOPE,
    CANONICAL_VSCODE_SYNTAX_SHA256,
    P10_T3_VSCODE_SYNTAX_VERSION,
    VSCODE_SYNTAX_KIND,
    VSCODE_SYNTAX_SCHEMA,
    VSCodeSyntaxError,
    audit_vscode_syntax,
    main as syntax_main,
    syntax_fingerprint,
)


EXPECTED_SYNTAX_SHA256 = (
    "cb8e7e35005e7ba8fe2f933cf45247aaf5a8e8a4e7cbc1dd1bbe07ef6c584466"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_syntax_error(operation, message: str) -> VSCodeSyntaxError:
    try:
        operation()
    except VSCodeSyntaxError as error:
        require(error.code == "APX-VSCODE-002", "syntax error code changed")
        return error
    raise AssertionError(message)


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    require(
        P10_T3_VSCODE_SYNTAX_VERSION == "10-T3.2",
        "T3.2 version changed",
    )
    require(VSCODE_SYNTAX_SCHEMA == 1, "T3.2 schema changed")
    require(
        VSCODE_SYNTAX_KIND == "apexforge.vscode-syntax",
        "T3.2 kind changed",
    )
    require(CANONICAL_TEXTMATE_NAME == "ApexForge", "grammar name changed")
    require(
        CANONICAL_TEXTMATE_SCOPE == "source.apexforge",
        "TextMate scope changed",
    )
    require(CANONICAL_TEXTMATE_FILETYPE == "apex", "file type changed")
    require(
        CANONICAL_TEXTMATE_PATH
        == "./syntaxes/apexforge.tmLanguage.json",
        "TextMate path changed",
    )

    repository_root = Path(__file__).resolve().parent.parent
    extension_root = repository_root / "editors" / "vscode-apexforge"

    foundation = audit_vscode_extension(
        extension_root,
        repository_root=repository_root,
    )
    require(
        foundation.foundation_sha256 == CANONICAL_VSCODE_FOUNDATION_SHA256,
        "T3.1 foundation changed after adding syntax highlighting",
    )

    audit = audit_vscode_syntax(
        extension_root,
        repository_root=repository_root,
    )
    require(audit.language_id == "apexforge", "syntax language id changed")
    require(audit.scope_name == "source.apexforge", "audit scope changed")
    require(audit.repository_count == 17, "repository rule count changed")
    require(audit.regex_count == 20, "regex rule count changed")
    require(
        audit.syntax_sha256 == EXPECTED_SYNTAX_SHA256,
        "syntax audit hash changed",
    )
    require(
        CANONICAL_VSCODE_SYNTAX_SHA256 == EXPECTED_SYNTAX_SHA256,
        "declared syntax hash changed",
    )

    package = json.loads(
        (extension_root / "package.json").read_text(encoding="utf-8")
    )
    grammar_path = (
        extension_root / "syntaxes" / "apexforge.tmLanguage.json"
    )
    grammar = json.loads(grammar_path.read_text(encoding="utf-8"))
    require(
        syntax_fingerprint(package, grammar) == EXPECTED_SYNTAX_SHA256,
        "syntax projection is not deterministic",
    )

    contribution = package["contributes"]["grammars"][0]
    require(contribution["language"] == "apexforge", "language link changed")
    require(
        contribution["scopeName"] == "source.apexforge",
        "contributed scope changed",
    )
    require(
        contribution["path"] == "./syntaxes/apexforge.tmLanguage.json",
        "contributed path changed",
    )
    require(
        grammar["patterns"][0] == {"include": "#strings"},
        "strings are no longer first in tokenization order",
    )
    require(
        "comments" not in grammar["repository"],
        "unsupported comments repository appeared",
    )

    stdout = StringIO()
    stderr = StringIO()
    code = syntax_main(
        (str(extension_root), "--check"),
        stdout=stdout,
        stderr=stderr,
    )
    require(code == 0, "standalone syntax check failed")
    require(stderr.getvalue() == "", "successful syntax check wrote stderr")
    require(
        "AFP-P10-T3.2 VS Code TextMate syntax check passed.\n"
        in stdout.getvalue(),
        "standalone check omitted success heading",
    )
    require(
        f"Syntax SHA-256: {EXPECTED_SYNTAX_SHA256}\n"
        in stdout.getvalue(),
        "standalone check omitted syntax fingerprint",
    )

    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        copied_extension = temporary_root / "editors" / "vscode-apexforge"
        copied_extension.parent.mkdir(parents=True)
        copytree(extension_root, copied_extension)
        copytree(repository_root / "spec", temporary_root / "spec")

        copied_package_path = copied_extension / "package.json"
        copied_grammar_path = (
            copied_extension / "syntaxes" / "apexforge.tmLanguage.json"
        )

        bad_package = json.loads(
            copied_package_path.read_text(encoding="utf-8")
        )
        bad_package["contributes"]["grammars"][0]["path"] = (
            "./syntaxes/missing.tmLanguage.json"
        )
        write_json(copied_package_path, bad_package)
        require_syntax_error(
            lambda: audit_vscode_syntax(
                copied_extension,
                repository_root=temporary_root,
            ),
            "incorrect TextMate path unexpectedly passed",
        )

        write_json(copied_package_path, package)
        bad_grammar = json.loads(
            copied_grammar_path.read_text(encoding="utf-8")
        )
        bad_grammar["repository"]["comments"] = {
            "name": "comment.line.number-sign.apexforge",
            "match": "#.*$",
        }
        write_json(copied_grammar_path, bad_grammar)
        require_syntax_error(
            lambda: audit_vscode_syntax(
                copied_extension,
                repository_root=temporary_root,
            ),
            "unsupported comment highlighting unexpectedly passed",
        )

        write_json(copied_grammar_path, grammar)
        bad_grammar = json.loads(
            copied_grammar_path.read_text(encoding="utf-8")
        )
        keyword_match = bad_grammar["repository"]["keywords"]["match"]
        bad_grammar["repository"]["keywords"]["match"] = keyword_match.replace(
            "|let",
            "",
        )
        write_json(copied_grammar_path, bad_grammar)
        require_syntax_error(
            lambda: audit_vscode_syntax(
                copied_extension,
                repository_root=temporary_root,
            ),
            "keyword inventory drift unexpectedly passed",
        )

        write_json(copied_grammar_path, grammar)
        bad_grammar = json.loads(
            copied_grammar_path.read_text(encoding="utf-8")
        )
        bad_grammar["scopeName"] = "source.apex"
        write_json(copied_grammar_path, bad_grammar)
        require_syntax_error(
            lambda: audit_vscode_syntax(
                copied_extension,
                repository_root=temporary_root,
            ),
            "incorrect TextMate scope unexpectedly passed",
        )

    print("AFP-P10-T3.2 VS Code TextMate syntax smoke test passed.")
    print("T3.1 foundation preservation: PASS")
    print("Canonical TextMate grammar contribution: PASS")
    print("Frozen T2 keyword synchronization: PASS")
    print("Declaration and member highlighting: PASS")
    print("Type, literal, operator, and call highlighting: PASS")
    print("Module/import highlighting: PASS")
    print("No-comment syntax boundary: PASS")
    print("Conformance-corpus coverage: PASS")
    print("Deterministic syntax fingerprint: PASS")
    print("Standalone syntax validator: PASS")


if __name__ == "__main__":
    main()
