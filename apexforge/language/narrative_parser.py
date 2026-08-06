"""Dedicated opt-in parser for ApexForge narrative source documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from language.diagnostics import BuildDiagnostic, DiagnosticError
from language.narrative_source import (
    NarrativeSourceCharacter,
    NarrativeSourceChoice,
    NarrativeSourceChoicePath,
    NarrativeSourceContinuity,
    NarrativeSourceContinuityConstraint,
    NarrativeSourceDialogue,
    NarrativeSourceDocument,
    NarrativeSourceIdentifier,
    NarrativeSourcePerspective,
    NarrativeSourceReference,
    NarrativeSourceScalar,
    NarrativeSourceScene,
    NarrativeSourceState,
    NarrativeSourceStateFact,
    NarrativeSourceStory,
    NarrativeSourceTimeline,
)
from language.source import SourceSpan, SourceText


__all__ = (
    "NarrativeSourceParseError",
    "parse_narrative_source",
)


class NarrativeSourceParseError(DiagnosticError):
    """One deterministic narrative-source syntax failure."""


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str
    span: SourceSpan


_PUNCTUATION = {
    "{": "LBRACE",
    "}": "RBRACE",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ",": "COMMA",
    ":": "COLON",
    ".": "DOT",
    "=": "EQUAL",
}

_ESCAPES = {
    '"': '"',
    "\\": "\\",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


def _error(
    span: SourceSpan,
    message: str,
) -> NarrativeSourceParseError:
    return NarrativeSourceParseError(
        BuildDiagnostic(
            severity="error",
            code="APX-NARRATIVE-SYNTAX",
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

        if character.isspace():
            index += 1
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
                            "Unterminated escape sequence in narrative string.",
                        )
                    escaped = text[index]
                    replacement = _ESCAPES.get(escaped)
                    if replacement is None:
                        raise _error(
                            source_text.span(escape_start, index + 1),
                            f"Unsupported narrative string escape '\\{escaped}'.",
                        )
                    value_parts.append(replacement)
                    index += 1
                    continue

                if selected in {"\n", "\r"}:
                    raise _error(
                        source_text.span(start, index),
                        "Narrative string literals cannot cross a line boundary.",
                    )

                value_parts.append(selected)
                index += 1
            else:
                raise _error(
                    source_text.span(start, len(text)),
                    "Unterminated narrative string literal.",
                )
            continue

        if character == "_" or character.isalpha():
            start = index
            index += 1
            while index < len(text):
                selected = text[index]
                if selected == "_" or selected.isalnum():
                    index += 1
                    continue
                break
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

        raise _error(
            source_text.span(index, index + 1),
            f"Unexpected character {character!r} in narrative source.",
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

    def expect_kind(
        self,
        kind: str,
        description: str,
    ) -> _Token:
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
                f"Expected narrative keyword '{word}'; "
                f"found {self.describe(token)}.",
                token,
            )
        return self.advance()

    @staticmethod
    def describe(token: _Token) -> str:
        if token.kind == "EOF":
            return "end of source"
        if token.kind == "STRING":
            return "a string literal"
        if token.kind == "IDENT":
            return f"identifier {token.value!r}"
        if token.kind == "BOOLEAN":
            return f"boolean {token.value!r}"
        return repr(token.value)

    def identifier(self) -> NarrativeSourceIdentifier:
        token = self.expect_kind("IDENT", "an identifier")
        return NarrativeSourceIdentifier(token.value, token.span)

    def reference(self, expected_kind: str) -> NarrativeSourceReference:
        return NarrativeSourceReference(
            expected_kind,
            self.identifier(),
        )

    def scalar(self) -> NarrativeSourceScalar:
        token = self.current()
        if token.kind == "IDENT":
            self.advance()
            return NarrativeSourceScalar(
                "identifier",
                token.value,
                token.span,
            )
        if token.kind == "STRING":
            self.advance()
            return NarrativeSourceScalar(
                "string",
                token.value,
                token.span,
            )
        if token.kind == "BOOLEAN":
            self.advance()
            return NarrativeSourceScalar(
                "boolean",
                token.value,
                token.span,
            )
        self.fail(
            "Expected an identifier, string, or lowercase boolean scalar.",
            token,
        )
        raise AssertionError("unreachable")

    def span_from(
        self,
        start: _Token,
        end: _Token,
    ) -> SourceSpan:
        return self.source_text.span(
            start.span.start.offset,
            end.span.end.offset,
        )

    def parse_document(self) -> NarrativeSourceDocument:
        story = self.parse_story()
        self.expect_kind("EOF", "end of source")
        return NarrativeSourceDocument(
            story,
            self.source_text.span(0, len(self.source_text.text)),
        )

    def parse_story(self) -> NarrativeSourceStory:
        start = self.expect_word("story")
        name = self.identifier()
        self.expect_kind("LBRACE", "'{' after the story name")

        characters = []
        scenes = []
        dialogues = []
        choices = []
        perspectives = []
        timelines = []
        states = []
        continuities = []

        while self.current().kind != "RBRACE":
            token = self.current()
            if token.kind == "EOF":
                self.fail("Expected '}' to close the story.", token)
            if token.kind != "IDENT":
                self.fail(
                    "Expected a narrative declaration inside the story.",
                    token,
                )

            declaration_kind = token.value
            if declaration_kind == "character":
                characters.append(self.parse_character())
            elif declaration_kind == "scene":
                scenes.append(self.parse_scene())
            elif declaration_kind == "dialogue":
                dialogues.append(self.parse_dialogue())
            elif declaration_kind == "choice":
                choices.append(self.parse_choice())
            elif declaration_kind == "perspective":
                perspectives.append(self.parse_perspective())
            elif declaration_kind == "timeline":
                timelines.append(self.parse_timeline())
            elif declaration_kind == "narrative_state":
                states.append(self.parse_state())
            elif declaration_kind == "continuity":
                continuities.append(self.parse_continuity())
            else:
                self.fail(
                    f"Unknown narrative declaration {declaration_kind!r}.",
                    token,
                )

        closing = self.expect_kind("RBRACE", "'}' to close the story")
        return NarrativeSourceStory(
            start.span,
            name,
            tuple(characters),
            tuple(scenes),
            tuple(dialogues),
            tuple(choices),
            tuple(perspectives),
            tuple(timelines),
            tuple(states),
            tuple(continuities),
            self.span_from(start, closing),
        )

    def parse_character(self) -> NarrativeSourceCharacter:
        start = self.expect_word("character")
        name = self.identifier()
        return NarrativeSourceCharacter(
            start.span,
            name,
            self.source_text.span(
                start.span.start.offset,
                name.span.end.offset,
            ),
        )

    def parse_scene(self) -> NarrativeSourceScene:
        start = self.expect_word("scene")
        name = self.identifier()
        return NarrativeSourceScene(
            start.span,
            name,
            self.source_text.span(
                start.span.start.offset,
                name.span.end.offset,
            ),
        )

    def parse_dialogue(self) -> NarrativeSourceDialogue:
        start = self.expect_word("dialogue")
        name = self.identifier()
        self.expect_kind("LBRACE", "'{' after the dialogue name")

        scene_keyword = self.expect_word("scene")
        scene = self.reference("scene")
        speaker_keyword = self.expect_word("speaker")
        speaker = self.reference("character")
        participants_keyword = self.expect_word("participants")
        participants = self.reference_list("character", "participants")

        closing = self.expect_kind("RBRACE", "'}' to close the dialogue")
        return NarrativeSourceDialogue(
            start.span,
            name,
            scene_keyword.span,
            scene,
            speaker_keyword.span,
            speaker,
            participants_keyword.span,
            participants,
            self.span_from(start, closing),
        )

    def parse_choice(self) -> NarrativeSourceChoice:
        start = self.expect_word("choice")
        name = self.identifier()
        self.expect_kind("LBRACE", "'{' after the choice name")

        scene_keyword = self.expect_word("scene")
        scene = self.reference("scene")
        paths = []
        while (
            self.current().kind == "IDENT"
            and self.current().value == "path"
        ):
            paths.append(self.parse_choice_path())

        if not paths:
            self.fail(
                "Expected at least one 'path' declaration inside the choice."
            )

        closing = self.expect_kind("RBRACE", "'}' to close the choice")
        return NarrativeSourceChoice(
            start.span,
            name,
            scene_keyword.span,
            scene,
            tuple(paths),
            self.span_from(start, closing),
        )

    def parse_choice_path(self) -> NarrativeSourceChoicePath:
        start = self.expect_word("path")
        label_token = self.expect_kind(
            "STRING",
            "a quoted choice-path label",
        )
        if not label_token.value:
            self.fail(
                "Choice-path labels must not be empty.",
                label_token,
            )
        label = NarrativeSourceScalar(
            "string",
            label_token.value,
            label_token.span,
        )

        self.expect_kind("LBRACE", "'{' after the choice-path label")
        destination_keyword = self.expect_word("destination")
        destination = self.reference("scene")

        condition_keyword_span = None
        condition = None
        consequence_keyword_span = None
        consequence = None

        if (
            self.current().kind == "IDENT"
            and self.current().value == "condition"
        ):
            condition_keyword = self.advance()
            condition_keyword_span = condition_keyword.span
            condition = self.scalar()

        if (
            self.current().kind == "IDENT"
            and self.current().value == "consequence"
        ):
            consequence_keyword = self.advance()
            consequence_keyword_span = consequence_keyword.span
            consequence = self.scalar()

        closing = self.expect_kind("RBRACE", "'}' to close the choice path")
        return NarrativeSourceChoicePath(
            keyword_span=start.span,
            label=label,
            destination_keyword_span=destination_keyword.span,
            destination=destination,
            span=self.span_from(start, closing),
            condition_keyword_span=condition_keyword_span,
            condition=condition,
            consequence_keyword_span=consequence_keyword_span,
            consequence=consequence,
        )

    def parse_perspective(self) -> NarrativeSourcePerspective:
        start = self.expect_word("perspective")
        name = self.identifier()
        self.expect_kind("LBRACE", "'{' after the perspective name")
        viewpoint_keyword = self.expect_word("viewpoint")
        viewpoint = self.reference("character")
        closing = self.expect_kind("RBRACE", "'}' to close the perspective")
        return NarrativeSourcePerspective(
            start.span,
            name,
            viewpoint_keyword.span,
            viewpoint,
            self.span_from(start, closing),
        )

    def parse_timeline(self) -> NarrativeSourceTimeline:
        start = self.expect_word("timeline")
        name = self.identifier()
        self.expect_kind("LBRACE", "'{' after the timeline name")
        scenes_keyword = self.expect_word("scenes")
        scenes = self.reference_list("scene", "timeline scenes")
        closing = self.expect_kind("RBRACE", "'}' to close the timeline")
        return NarrativeSourceTimeline(
            start.span,
            name,
            scenes_keyword.span,
            scenes,
            self.span_from(start, closing),
        )

    def parse_state(self) -> NarrativeSourceState:
        start = self.expect_word("narrative_state")
        name = self.identifier()
        self.expect_kind("LBRACE", "'{' after the narrative-state name")
        facts = []

        while (
            self.current().kind == "IDENT"
            and self.current().value == "fact"
        ):
            facts.append(self.parse_state_fact())

        closing = self.expect_kind(
            "RBRACE",
            "'}' to close the narrative state",
        )
        return NarrativeSourceState(
            start.span,
            name,
            tuple(facts),
            self.span_from(start, closing),
        )

    def parse_state_fact(self) -> NarrativeSourceStateFact:
        start = self.expect_word("fact")
        subject = self.reference("character")
        self.expect_kind("DOT", "'.' between fact subject and name")
        name = self.identifier()
        self.expect_kind("EQUAL", "'=' before the fact value")
        value = self.scalar()
        return NarrativeSourceStateFact(
            start.span,
            subject,
            name,
            value,
            self.source_text.span(
                start.span.start.offset,
                value.span.end.offset,
            ),
        )

    def parse_continuity(self) -> NarrativeSourceContinuity:
        start = self.expect_word("continuity")
        name = self.identifier()
        self.expect_kind("LBRACE", "'{' after the continuity name")
        constraints = []

        while (
            self.current().kind == "IDENT"
            and self.current().value == "require"
        ):
            constraints.append(self.parse_continuity_constraint())

        closing = self.expect_kind("RBRACE", "'}' to close continuity")
        return NarrativeSourceContinuity(
            start.span,
            name,
            tuple(constraints),
            self.span_from(start, closing),
        )

    def parse_continuity_constraint(
        self,
    ) -> NarrativeSourceContinuityConstraint:
        start = self.expect_word("require")
        subjects = [self.reference("character")]
        while self.current().kind == "COMMA":
            self.advance()
            subjects.append(self.reference("character"))
        self.expect_kind("COLON", "':' before the continuity assertion")
        assertion_token = self.expect_kind(
            "STRING",
            "a quoted continuity assertion",
        )
        assertion = NarrativeSourceScalar(
            "string",
            assertion_token.value,
            assertion_token.span,
        )
        return NarrativeSourceContinuityConstraint(
            start.span,
            tuple(subjects),
            assertion,
            self.source_text.span(
                start.span.start.offset,
                assertion.span.end.offset,
            ),
        )

    def reference_list(
        self,
        expected_kind: str,
        description: str,
    ) -> tuple[NarrativeSourceReference, ...]:
        self.expect_kind("LBRACKET", f"'[' before {description}")
        references = [self.reference(expected_kind)]
        while self.current().kind == "COMMA":
            self.advance()
            references.append(self.reference(expected_kind))
        self.expect_kind("RBRACKET", f"']' after {description}")
        return tuple(references)


def parse_narrative_source(
    source: str,
    *,
    source_name: str = "<memory>",
) -> NarrativeSourceDocument:
    """Parse one explicit narrative document into immutable source records."""

    if type(source) is not str:
        raise TypeError("Narrative source must be an exact str.")
    if type(source_name) is not str:
        raise TypeError("Narrative source_name must be an exact str.")

    source_text = SourceText(source_name, source)
    parser = _Parser(source_text, _scan(source_text))
    return parser.parse_document()
