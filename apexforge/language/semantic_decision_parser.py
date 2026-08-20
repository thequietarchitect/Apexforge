"""Dedicated opt-in parser for ApexForge semantic-decision source documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from language.diagnostics import BuildDiagnostic, DiagnosticError
from language.semantic_decision_source import (
    SemanticDecisionSourceCandidate,
    SemanticDecisionSourceConvergence,
    SemanticDecisionSourceDeclaration,
    SemanticDecisionSourceDocument,
    SemanticDecisionSourceIdentifier,
    SemanticDecisionSourceIncompatibility,
    SemanticDecisionSourceParadoxElevation,
    SemanticDecisionSourceScalar,
)
from language.source import SourceSpan, SourceText


__all__ = (
    "SemanticDecisionSourceParseError",
    "is_semantic_decision_source_document",
    "parse_semantic_decision_source",
)


class SemanticDecisionSourceParseError(DiagnosticError):
    """One deterministic semantic-decision source syntax failure."""


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str
    span: SourceSpan


_PUNCTUATION = {
    "{": "LBRACE",
    "}": "RBRACE",
    ",": "COMMA",
    ".": "DOT",
}

_ESCAPES = {
    '"': '"',
    "\\": "\\",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


def _identifier_end(text: str, start: int) -> int:
    index = start + 1
    while index < len(text):
        character = text[index]
        if character == "_" or character.isalnum():
            index += 1
            continue
        break
    return index


def is_semantic_decision_source_document(source: str) -> bool:
    """Lexically classify the exact leading semantic-decision ``decision`` word."""

    if type(source) is not str:
        raise TypeError("Semantic-decision source must be an exact str.")

    index = 0
    while index < len(source) and source[index].isspace():
        index += 1

    if index >= len(source):
        return False

    character = source[index]
    if character != "_" and not character.isalpha():
        return False

    end = _identifier_end(source, index)
    return source[index:end] == "decision"


def _error(
    span: SourceSpan,
    message: str,
) -> SemanticDecisionSourceParseError:
    return SemanticDecisionSourceParseError(
        BuildDiagnostic(
            severity="error",
            code="APX-SEMANTIC-DECISION-SYNTAX",
            message=message,
            stage="parse",
            span=span,
        )
    )


def _scan(
    source_text: SourceText,
) -> tuple[_Token, ...]:
    text = source_text.text
    tokens = []
    index = 0

    while index < len(text):
        character = text[index]

        if character in {" ", "\t", "\f", "\v"}:
            index += 1
            continue

        if character in {"\n", "\r"}:
            start = index
            if character == "\r" and index + 1 < len(text) and text[index + 1] == "\n":
                index += 2
            else:
                index += 1
            tokens.append(
                _Token(
                    "NEWLINE",
                    "\n",
                    source_text.span(start, index),
                )
            )
            continue

        punctuation_kind = _PUNCTUATION.get(character)
        if punctuation_kind is not None:
            tokens.append(
                _Token(
                    punctuation_kind,
                    character,
                    source_text.span(index, index + 1),
                )
            )
            index += 1
            continue

        if character == '"':
            start = index
            index += 1
            value_parts = []

            while index < len(text):
                selected = text[index]
                if selected == '"':
                    index += 1
                    tokens.append(
                        _Token(
                            "STRING",
                            "".join(value_parts),
                            source_text.span(start, index),
                        )
                    )
                    break

                if selected == "\\":
                    escape_start = index
                    index += 1
                    if index >= len(text):
                        raise _error(
                            source_text.span(escape_start, len(text)),
                            "Unterminated escape sequence in semantic-decision string.",
                        )
                    escaped = text[index]
                    replacement = _ESCAPES.get(escaped)
                    if replacement is None:
                        raise _error(
                            source_text.span(escape_start, index + 1),
                            (
                                "Unsupported semantic-decision string escape "
                                f"'\\{escaped}'."
                            ),
                        )
                    value_parts.append(replacement)
                    index += 1
                    continue

                if selected in {"\n", "\r"}:
                    raise _error(
                        source_text.span(start, index),
                        "Semantic-decision string literals cannot cross a line boundary.",
                    )

                value_parts.append(selected)
                index += 1
            else:
                raise _error(
                    source_text.span(start, len(text)),
                    "Unterminated semantic-decision string literal.",
                )
            continue

        if character == "_" or character.isalpha():
            start = index
            index = _identifier_end(text, index)
            value = text[start:index]
            kind = "BOOLEAN" if value in {"true", "false"} else "IDENT"
            tokens.append(
                _Token(
                    kind,
                    value,
                    source_text.span(start, index),
                )
            )
            continue

        start = index
        index += 1
        while index < len(text):
            selected = text[index]
            if (
                selected.isspace()
                or selected in _PUNCTUATION
                or selected == '"'
                or selected == "_"
                or selected.isalpha()
            ):
                break
            index += 1
        tokens.append(
            _Token(
                "SYMBOL",
                text[start:index],
                source_text.span(start, index),
            )
        )

    tokens.append(
        _Token(
            "EOF",
            "",
            source_text.span(len(text), len(text)),
        )
    )
    return tuple(tokens)


class _Parser:
    def __init__(
        self,
        source_text: SourceText,
        tokens: tuple[_Token, ...],
    ) -> None:
        self.source_text = source_text
        self.tokens = tokens
        self.index = 0

    def current(self) -> _Token:
        return self.tokens[self.index]

    def advance(self) -> _Token:
        token = self.current()
        if token.kind != "EOF":
            self.index += 1
        return token

    def fail(
        self,
        message: str,
        token: Optional[_Token] = None,
    ) -> None:
        selected = token if token is not None else self.current()
        raise _error(selected.span, message)

    def skip_newlines(self) -> None:
        while self.current().kind == "NEWLINE":
            self.advance()

    def expect_kind(self, kind: str, description: str) -> _Token:
        token = self.current()
        if token.kind != kind:
            self.fail(
                f"Expected {description}; found {self.describe(token)}.",
                token,
            )
        return self.advance()

    def expect_word(self, word: str) -> _Token:
        token = self.current()
        if token.kind != "IDENT" or token.value != word:
            self.fail(
                f"Expected {word!r}; found {self.describe(token)}.",
                token,
            )
        return self.advance()

    @staticmethod
    def describe(token: _Token) -> str:
        if token.kind == "EOF":
            return "end of source"
        if token.kind == "NEWLINE":
            return "line boundary"
        return repr(token.value)

    def identifier(self) -> SemanticDecisionSourceIdentifier:
        token = self.expect_kind("IDENT", "identifier")
        return SemanticDecisionSourceIdentifier(token.value, token.span)

    def _span(self, start: _Token, end: _Token) -> SourceSpan:
        return self.source_text.span(
            start.span.start.offset,
            end.span.end.offset,
        )

    def _line_scalar(
        self,
        *,
        owner: str,
    ) -> SemanticDecisionSourceScalar:
        start_index = self.index
        while self.current().kind not in {"NEWLINE", "RBRACE", "EOF"}:
            self.advance()

        if self.index == start_index:
            self.fail(f"{owner} requires a source value.")

        selected = self.tokens[start_index:self.index]
        first = selected[0]
        last = selected[-1]
        span = self.source_text.span(
            first.span.start.offset,
            last.span.end.offset,
        )

        if len(selected) == 1:
            token = selected[0]
            if token.kind == "STRING":
                return SemanticDecisionSourceScalar("string", token.value, span)
            if token.kind == "BOOLEAN":
                return SemanticDecisionSourceScalar("boolean", token.value, span)
            if token.kind == "IDENT":
                return SemanticDecisionSourceScalar("identifier", token.value, span)

        text = self.source_text.text[
            first.span.start.offset:last.span.end.offset
        ].strip()
        return SemanticDecisionSourceScalar("expression", text, span)

    def _policy_scalar(self) -> SemanticDecisionSourceScalar:
        token = self.current()
        if token.kind == "STRING":
            self.advance()
            return SemanticDecisionSourceScalar("string", token.value, token.span)

        first = self.expect_kind("IDENT", "policy identifier or string")
        parts = [first.value]
        last = first
        while self.current().kind == "DOT":
            self.advance()
            selected = self.expect_kind("IDENT", "policy identifier segment")
            parts.append(selected.value)
            last = selected

        return SemanticDecisionSourceScalar(
            "identifier",
            ".".join(parts),
            self.source_text.span(
                first.span.start.offset,
                last.span.end.offset,
            ),
        )

    def _finish_statement(self, owner: str) -> None:
        token = self.current()
        if token.kind == "NEWLINE":
            self.advance()
            return
        if token.kind in {"RBRACE", "EOF"}:
            return
        self.fail(f"{owner} must end at a line boundary.", token)

    def parse_candidate(self) -> SemanticDecisionSourceCandidate:
        keyword = self.expect_word("candidate")
        name = self.identifier()
        condition = None
        when_keyword = None
        last = self.tokens[self.index - 1]

        if self.current().kind == "IDENT" and self.current().value == "when":
            when_keyword = self.advance()
            condition = self._line_scalar(owner="candidate when")
            last = self.tokens[self.index - 1]

        self._finish_statement("candidate declaration")
        return SemanticDecisionSourceCandidate(
            keyword_span=keyword.span,
            name=name,
            span=self._span(keyword, last),
            when_keyword_span=None if when_keyword is None else when_keyword.span,
            condition=condition,
        )

    def parse_incompatibility(self) -> SemanticDecisionSourceIncompatibility:
        keyword = self.expect_word("incompatible")
        left = self.identifier()
        self.expect_kind("COMMA", "','")
        right = self.identifier()
        last = self.tokens[self.index - 1]
        self._finish_statement("incompatible declaration")
        return SemanticDecisionSourceIncompatibility(
            keyword_span=keyword.span,
            left=left,
            right=right,
            span=self._span(keyword, last),
        )

    def parse_convergence(self) -> SemanticDecisionSourceConvergence:
        keyword = self.expect_word("converge")
        using_keyword = self.expect_word("using")
        policy = self._policy_scalar()
        self.expect_kind("LBRACE", "'{'")
        self.skip_newlines()

        candidates = []
        while self.current().kind != "RBRACE":
            if self.current().kind == "EOF":
                self.fail("Unterminated converge block.")
            candidates.append(self.identifier())
            if self.current().kind == "COMMA":
                self.advance()
            elif self.current().kind == "NEWLINE":
                self.skip_newlines()
            elif self.current().kind != "RBRACE":
                self.fail(
                    "Convergence candidate references must be separated by commas "
                    "or line boundaries."
                )

        if not candidates:
            self.fail("Converge block must contain at least one candidate reference.")

        closing = self.expect_kind("RBRACE", "'}'")
        self._finish_statement("converge declaration")
        return SemanticDecisionSourceConvergence(
            keyword_span=keyword.span,
            using_keyword_span=using_keyword.span,
            policy=policy,
            candidates=tuple(candidates),
            span=self._span(keyword, closing),
        )

    def parse_paradox_elevation(self) -> SemanticDecisionSourceParadoxElevation:
        paradox_keyword = self.expect_word("paradox")
        elevate_keyword = self.expect_word("elevate")
        when_keyword = None
        condition = None
        requires_keyword = None
        requirement = None
        last = elevate_keyword

        if self.current().kind == "IDENT" and self.current().value in {
            "when",
            "requires",
        }:
            pass
        elif self.current().kind == "NEWLINE":
            self.skip_newlines()
        elif self.current().kind not in {"RBRACE", "EOF"}:
            self.fail(
                "paradox elevate accepts only optional 'when' and 'requires' clauses."
            )

        while (
            self.current().kind == "IDENT"
            and self.current().value in {"when", "requires"}
        ):
            clause = self.current().value
            if clause == "when":
                if when_keyword is not None:
                    self.fail("paradox elevate may contain only one 'when' clause.")
                when_keyword = self.advance()
                condition = self._line_scalar(owner="paradox elevate when")
                last = self.tokens[self.index - 1]
            else:
                if requires_keyword is not None:
                    self.fail("paradox elevate may contain only one 'requires' clause.")
                requires_keyword = self.advance()
                requirement = self._line_scalar(owner="paradox elevate requires")
                last = self.tokens[self.index - 1]

            if self.current().kind == "NEWLINE":
                self.skip_newlines()
            elif self.current().kind not in {"RBRACE", "EOF"}:
                self.fail("paradox elevate clause must end at a line boundary.")

        return SemanticDecisionSourceParadoxElevation(
            paradox_keyword_span=paradox_keyword.span,
            elevate_keyword_span=elevate_keyword.span,
            span=self._span(paradox_keyword, last),
            when_keyword_span=None if when_keyword is None else when_keyword.span,
            condition=condition,
            requires_keyword_span=(
                None if requires_keyword is None else requires_keyword.span
            ),
            requirement=requirement,
        )

    def parse_decision(self) -> SemanticDecisionSourceDeclaration:
        keyword = self.expect_word("decision")
        name = self.identifier()
        self.expect_kind("LBRACE", "'{'")
        self.skip_newlines()

        candidates = []
        incompatibilities = []
        convergence = None
        paradox_elevation = None

        while self.current().kind != "RBRACE":
            token = self.current()
            if token.kind == "EOF":
                self.fail("Unterminated decision declaration.", token)
            if token.kind == "NEWLINE":
                self.skip_newlines()
                continue
            if token.kind != "IDENT":
                self.fail("Expected semantic-decision declaration entry.", token)

            if token.value == "candidate":
                candidates.append(self.parse_candidate())
            elif token.value == "incompatible":
                incompatibilities.append(self.parse_incompatibility())
            elif token.value == "converge":
                if convergence is not None:
                    self.fail("Decision may contain only one converge declaration.")
                convergence = self.parse_convergence()
            elif token.value == "paradox":
                if paradox_elevation is not None:
                    self.fail("Decision may contain only one paradox elevate declaration.")
                paradox_elevation = self.parse_paradox_elevation()
            else:
                self.fail(
                    f"Unsupported semantic-decision entry {token.value!r}.",
                    token,
                )

        closing = self.expect_kind("RBRACE", "'}'")
        if self.current().kind == "NEWLINE":
            self.skip_newlines()

        return SemanticDecisionSourceDeclaration(
            keyword_span=keyword.span,
            name=name,
            candidates=tuple(candidates),
            incompatibilities=tuple(incompatibilities),
            convergence=convergence,
            paradox_elevation=paradox_elevation,
            span=self._span(keyword, closing),
        )

    def parse_document(self) -> SemanticDecisionSourceDocument:
        self.skip_newlines()
        decisions = []

        while self.current().kind != "EOF":
            decisions.append(self.parse_decision())
            self.skip_newlines()

        if not decisions:
            self.fail("Semantic-decision document must contain at least one decision.")

        return SemanticDecisionSourceDocument(
            decisions=tuple(decisions),
            span=self.source_text.span(0, len(self.source_text.text)),
        )


def parse_semantic_decision_source(
    source: str,
    *,
    source_name: str = "<memory>",
) -> SemanticDecisionSourceDocument:
    """Parse one explicit semantic-decision document into immutable source records."""

    if type(source) is not str:
        raise TypeError("Semantic-decision source must be an exact str.")
    if type(source_name) is not str:
        raise TypeError("Semantic-decision source_name must be an exact str.")

    source_text = SourceText(source_name, source)
    parser = _Parser(source_text, _scan(source_text))
    return parser.parse_document()