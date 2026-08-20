"""P11-TAM-I canonical lexer token evidence trace production."""

from __future__ import annotations

from pathlib import Path
import dataclasses
import subprocess

from language.lexer import Token, lex
from tam import (
    TraceDomain,
    TraceMap,
    trace_map_from_token_evidence,
    trace_record_from_token_evidence,
)


PREDECESSOR_TAG = "afp-p11-tam-h-freeze"
PREDECESSOR_COMMIT = "cdd23d15a9cb699e11c2e82278371652a4439f8d"


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect(exc_type, operation):
    try:
        operation()
    except exc_type as error:
        return error
    raise AssertionError("Expected {}.".format(exc_type.__name__))


def _assert_predecessor() -> None:
    tag = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(tag.returncode == 0, tag.stderr.strip())
    _require(
        tag.stdout.strip() == PREDECESSOR_COMMIT,
        "TAM-H freeze target changed",
    )
    ancestry = _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD")
    _require(ancestry.returncode == 0, "TAM-H is not an ancestor of TAM-I")


def _real_tokens():
    tokens = tuple(
        lex(
            'state count : int = 1',
            source_name="TokenTrace.apex",
        )
    )
    _require(tokens, "lexer returned no tokens")
    _require(tokens[-1].kind == "EOF", "canonical lexer EOF token disappeared")
    _require(
        all(type(token) is Token for token in tokens),
        "canonical lexer returned non-Token values",
    )
    _require(
        all(token.span is not None for token in tokens),
        "canonical lexer omitted source provenance",
    )
    return tokens


def _assert_public_owner_contract() -> None:
    _require(dataclasses.is_dataclass(Token), "Token stopped being a dataclass")
    _require(
        tuple(field.name for field in dataclasses.fields(Token))
        == ("kind", "value", "span"),
        "canonical Token field contract changed",
    )


def _assert_real_token_projection() -> None:
    tokens = _real_tokens()
    first = tuple(
        trace_record_from_token_evidence(
            token,
            token_index=index,
        )
        for index, token in enumerate(tokens)
    )
    second = tuple(
        trace_record_from_token_evidence(
            token,
            token_index=index,
        )
        for index, token in enumerate(tokens)
    )
    _require(first == second, "same lexer tokens produced different records")

    for token, record in zip(tokens, first):
        _require(
            record.domain == TraceDomain("token"),
            "token evidence escaped token domain",
        )
        _require(
            record.owner == "language.lexer"
            and record.producer == "language.lexer",
            "canonical lexer ownership changed",
        )
        _require(
            record.representation == "token",
            "token representation changed",
        )
        _require(
            record.source_span is token.span,
            "token SourceSpan was copied, rebuilt, or replaced",
        )
        _require(
            record.canonical_identity is None,
            "TAM fabricated canonical identity for lexical token",
        )
        _require(
            record.provenance == (),
            "TAM fabricated provenance for lexical token",
        )
        _require(
            record.upstream_trace_ids == ()
            and record.downstream_trace_ids == (),
            "TAM fabricated graph links for lexical token",
        )

    _require(
        first[-1].source_span is tokens[-1].span,
        "EOF token provenance was not preserved",
    )


def _assert_kind_value_and_span_preserved() -> None:
    base = Token("IDENT", "alpha", None)
    kind_changed = Token("OTHER", "alpha", None)
    value_changed = Token("IDENT", "beta", None)

    base_record = trace_record_from_token_evidence(base, token_index=0)
    _require(
        base_record.source_span is None,
        "span-less token fabricated SourceSpan",
    )
    _require(
        base_record.trace_id
        != trace_record_from_token_evidence(
            kind_changed,
            token_index=0,
        ).trace_id,
        "token kind did not participate in trace identity",
    )
    _require(
        base_record.trace_id
        != trace_record_from_token_evidence(
            value_changed,
            token_index=0,
        ).trace_id,
        "token value did not participate in trace identity",
    )

    repeated = tuple(
        token
        for token in lex(
            "alpha alpha",
            source_name="TokenTrace.apex",
        )
        if token.kind == "IDENT"
    )
    _require(len(repeated) == 2, "fixture did not yield repeated IDENT tokens")
    _require(
        repeated[0].kind == repeated[1].kind
        and repeated[0].value == repeated[1].value
        and repeated[0].span != repeated[1].span,
        "fixture did not isolate SourceSpan distinction",
    )
    _require(
        trace_record_from_token_evidence(
            repeated[0],
            token_index=0,
        ).trace_id
        != trace_record_from_token_evidence(
            repeated[1],
            token_index=0,
        ).trace_id,
        "token SourceSpan did not participate in trace identity",
    )


def _assert_map_projection() -> None:
    tokens = _real_tokens()
    first = trace_map_from_token_evidence(tokens)
    second = trace_map_from_token_evidence(tokens)
    _require(type(first) is TraceMap, "token evidence did not return TraceMap")
    _require(first == second, "same lexer tokens produced different maps")
    _require(
        first.records
        == tuple(
            trace_record_from_token_evidence(
                token,
                token_index=index,
            )
            for index, token in enumerate(tokens)
        ),
        "token evidence order changed",
    )
    _require(
        trace_map_from_token_evidence(()).records == (),
        "empty token evidence fabricated records",
    )


def _assert_type_guards() -> None:
    token = Token("IDENT", "alpha", None)
    _expect(
        TypeError,
        lambda: trace_record_from_token_evidence(
            object(),
            token_index=0,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_record_from_token_evidence(
            token,
            token_index=True,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_map_from_token_evidence([token]),
    )
    _expect(
        TypeError,
        lambda: trace_map_from_token_evidence((object(),)),
    )


def _assert_no_lexing_or_parser_ownership() -> None:
    text = (_root() / "apexforge/tam/production.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "lex(",
        "scan_string(",
        "KEYWORDS",
        "ONE_CHARACTER_TOKENS",
        "TWO_CHARACTER_TOKENS",
        "LexError",
        "Parser(",
        "parse_source",
        "parse_source_unit(",
        "parse_narrative_source(",
        "parse_semantic_decision_source(",
        "NarrativeSource",
        "SemanticDecisionSource",
        "SyntaxToken",
        "classify_apexforge_source(",
        "language_server.completion",
        "tooling.visualstudio_syntax",
    )
    for token in forbidden:
        _require(
            token not in text,
            "TAM-I acquired non-observational token behavior: " + token,
        )


def _assert_frozen_owners_unchanged() -> None:
    paths = (
        "apexforge/tam/model.py",
        "apexforge/language/source.py",
        "apexforge/language/lexer.py",
        "apexforge/language/parser.py",
        "apexforge/language/parse.py",
        "apexforge/language/narrative_parser.py",
        "apexforge/language/semantic_decision_parser.py",
        "apexforge/language/narrative_source.py",
        "apexforge/language/semantic_decision_source.py",
        "apexforge/language/compiler.py",
        "apexforge/language/grammar.py",
        "apexforge/language/grammar_conformance.py",
        "apexforge/language/grammar_export.py",
        "apexforge/language_server/completion.py",
        "apexforge/language_server/diagnostics.py",
        "apexforge/tooling/visualstudio_syntax.py",
        "apexforge/tooling/vscode_syntax.py",
        "apexforge/tooling/cli.py",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "TAM-I mutated frozen token/source owner")


def main() -> None:
    _assert_predecessor()
    _assert_public_owner_contract()
    _assert_real_token_projection()
    _assert_kind_value_and_span_preserved()
    _assert_map_projection()
    _assert_type_guards()
    _assert_no_lexing_or_parser_ownership()
    _assert_frozen_owners_unchanged()

    print("P11_TAM_H_FREEZE_ANCESTRY=PASS")
    print("CANONICAL_PUBLIC_TOKEN=language.lexer.Token")
    print("TOKEN_FIELD_CONTRACT=KIND_VALUE_SPAN")
    print("REAL_LEXER_TOKEN_CONSUMPTION=PASS")
    print("TOKEN_DOMAIN=TOKEN")
    print("TOKEN_KIND=PRESERVED")
    print("TOKEN_VALUE=PRESERVED")
    print("TOKEN_SOURCE_SPAN=EXACT_REFERENCE")
    print("SPANLESS_TOKEN_SOURCE_SPAN=NONE_NO_FABRICATION")
    print("EOF_TOKEN_EVIDENCE=PRESERVED")
    print("TOKEN_CANONICAL_IDENTITY=NONE_NO_FABRICATION")
    print("TOKEN_EVIDENCE_INPUT_ORDER=PRESERVED")
    print("PARSER_PRIVATE_TOKENS=DISTINCT_OWNER")
    print("EDITOR_TOKENS=DISTINCT_OWNER")
    print("GRAPH_LINK_INFERENCE=NONE")
    print("SAME_INPUT_SAME_TRACE_ID=PASS")
    print("SAME_INPUT_SAME_TRACE_MAP=PASS")
    print("LEXING_EXECUTION=NONE")
    print("TOKENIZATION_EXECUTION=NONE")
    print("PARSING_EXECUTION=NONE")
    print("SOURCE_RECONSTRUCTION=NONE")
    print("COMPILER_MUTATION=NONE")
    print("CLI_LSP_INTEGRATION=NONE")
    print("SEMANTIC_EXECUTION=NONE")
    print("P11_TAM_I_TOKEN_EVIDENCE_TRACE_PRODUCTION=PASS")


if __name__ == "__main__":
    main()