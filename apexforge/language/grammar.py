"""AFP-P10-T2.1 canonical ApexForge source and grammar contract.

This module records the source spelling and grammar already implemented by the
frozen lexer, parser, and module-header pipeline. It is declarative metadata:
it does not replace those components or alter compilation semantics.
"""

from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import Final, Mapping


P10_T2_GRAMMAR_VERSION: Final[str] = "10-T2.1"
P11_2B_COMPATIBILITY_VERSION: Final[str] = "11.2B"

CANONICAL_SOURCE_EXTENSION: Final[str] = ".apex"
CANONICAL_SOURCE_GLOB: Final[str] = "*.apex"
CANONICAL_MAIN_FILENAME: Final[str] = "main.apex"

MODULE_HEADER_KEYWORDS: Final[tuple[str, ...]] = (
    "module",
    "import",
)

GRAMMAR_KEYWORD_TOKENS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "directive": "DIRECTIVE",
        "workflow": "WORKFLOW",
        "authority": "AUTHORITY",
        "capability": "CAPABILITY",
        "state": "STATE",
        "event": "EVENT",
        "cause": "CAUSE",
        "path": "PATH",
        "add": "ADD",
        "emit": "EMIT",
        "message": "MESSAGE",
        "invoke": "INVOKE",
        "requires": "REQUIRES",
        "extends": "EXTENDS",
        "principal": "PRINCIPAL",
        "role": "ROLE",
        "set": "SET",
        "when": "WHEN",
        "otherwise": "OTHERWISE",
        "and": "AND",
        "or": "OR",
        "not": "NOT",
        "true": "TRUE",
        "false": "FALSE",
        "function": "FUNCTION",
        "return": "RETURN",
        "let": "LET",
    }
)

GRAMMAR_TWO_CHARACTER_TOKENS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "==": "EQEQ",
        "!=": "NE",
        "<=": "LTE",
        ">=": "GTE",
    }
)

GRAMMAR_ONE_CHARACTER_TOKENS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "{": "LBRACE",
        "}": "RBRACE",
        "=": "EQUAL",
        "@": "AT",
        "+": "PLUS",
        "-": "MINUS",
        "*": "STAR",
        "/": "SLASH",
        "%": "PERCENT",
        "(": "LPAREN",
        ")": "RPAREN",
        ",": "COMMA",
        ":": "COLON",
        "<": "LT",
        ">": "GT",
    }
)

STRING_ESCAPE_SEQUENCES: Final[tuple[str, ...]] = (
    r"\n",
    r"\r",
    r"\t",
    r'\"',
    r"\\",
)

TOP_LEVEL_DECLARATIONS: Final[tuple[str, ...]] = (
    "function",
    "directive",
    "workflow",
    "authority",
    "principal",
    "role",
)

COMMENTS_SUPPORTED: Final[bool] = False
ORDINARY_SEMICOLONS_SUPPORTED: Final[bool] = False
MODULE_HEADER_SEMICOLONS_OPTIONAL: Final[bool] = True


class ApexSourceNameError(ValueError):
    """A source name does not use the canonical ApexForge spelling."""

    code: Final[str] = "APX-SOURCE-001"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("ApexSourceNameError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


def canonicalize_source_name(value: object) -> str:
    """Return a slash-normalized name ending in lowercase ``.apex``.

    This function owns only canonical source spelling. Project-root containment,
    traversal rejection, duplicate detection, and other path-safety rules remain
    owned by ``tooling.project_manifest``.
    """

    if type(value) is not str:
        raise ApexSourceNameError(
            "ApexForge source name must be a string; "
            f"received {type(value).__name__}."
        )
    if not value or value != value.strip():
        raise ApexSourceNameError(
            "ApexForge source name must be non-empty and contain no "
            "edge whitespace."
        )

    normalized = value.replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1]

    if (
        not basename
        or len(basename) <= len(CANONICAL_SOURCE_EXTENSION)
        or not basename.endswith(CANONICAL_SOURCE_EXTENSION)
    ):
        raise ApexSourceNameError(
            "Canonical ApexForge source names must end in lowercase "
            f"{CANONICAL_SOURCE_EXTENSION!r}; received {value!r}."
        )

    return normalized


def is_canonical_source_name(value: object) -> bool:
    """Return whether ``value`` already has canonical slash and extension form."""

    try:
        normalized = canonicalize_source_name(value)
    except ApexSourceNameError:
        return False
    return normalized == value


APEXFORGE_EBNF: Final[str] = r'''ApexForgeSource = HeaderSection? Declaration EOF ;

HeaderSection = BlankLine* ModuleHeader BlankLine*
                (ImportHeader BlankLine*)* ;
ModuleHeader   = "module" ModuleName ";"? LineEnd ;
ImportHeader   = "import" ModuleName ";"? LineEnd ;
ModuleName     = Identifier ("." Identifier)* ;

Declaration = FunctionDeclaration
            | DirectiveDeclaration
            | WorkflowDeclaration
            | AuthorityDeclaration
            | PrincipalDeclaration
            | RoleDeclaration ;

FunctionDeclaration = "function" Identifier TypeParameters?
                      "(" ParameterList? ")" TypeAnnotation?
                      "{" FunctionStatement* "}" ;
TypeParameters       = "<" TypeParameter ("," TypeParameter)* ">" ;
TypeParameter        = Identifier (":" Identifier)? ;
ParameterList        = Parameter ("," Parameter)* ;
Parameter            = Identifier TypeAnnotation? ;
TypeAnnotation       = ":" Identifier ;
FunctionStatement    = LetStatement | ReturnStatement | FunctionWhen ;
LetStatement         = "let" Identifier "=" Expression ;
ReturnStatement      = "return" Expression ;
FunctionWhen         = "when" Expression "{" FunctionStatement* "}"
                       ("otherwise" "{" FunctionStatement* "}")? ;

DirectiveDeclaration = "directive" Identifier "{" DirectiveMember* "}" ;
DirectiveMember      = StateDeclaration | EventDeclaration | CauseDeclaration
                     | "authority" Identifier | "requires" Identifier ;
StateDeclaration     = "state" Identifier TypeAnnotation? "=" Expression ;
EventDeclaration     = "event" Identifier ;
CauseDeclaration     = "cause" Identifier "{" PathDeclaration* "}" ;
PathDeclaration      = "path" Identifier "@" Integer
                       "{" PathAction* "}" ;
PathAction           = AddAction | SetAction | EmitAction | MessageAction
                     | InvokeAction | ActionWhen ;
AddAction            = "add" Identifier Expression ;
SetAction            = "set" Identifier "=" Expression ;
EmitAction           = "emit" Identifier ;
MessageAction        = "message" Expression ;
InvokeAction         = "invoke" Identifier ;
ActionWhen           = "when" Expression "{" PathAction* "}"
                       ("otherwise" "{" PathAction* "}")? ;

WorkflowDeclaration  = "workflow" Identifier
                       "{" ("invoke" Identifier)* "}" ;
AuthorityDeclaration = "authority" Identifier ("extends" Identifier)?
                       "{" ("capability" Identifier)* "}" ;
RoleDeclaration      = "role" Identifier
                       "{" ("authority" Identifier)* "}" ;
PrincipalDeclaration = "principal" Identifier
                       "{" (("authority" | "role") Identifier)* "}" ;

Expression         = OrExpression ;
OrExpression       = AndExpression ("or" AndExpression)* ;
AndExpression      = EqualityExpression ("and" EqualityExpression)* ;
EqualityExpression = ComparisonExpression
                     (("==" | "!=") ComparisonExpression)* ;
ComparisonExpression = AdditiveExpression
                       (("<" | "<=" | ">" | ">=") AdditiveExpression)* ;
AdditiveExpression = MultiplicativeExpression
                     (("+" | "-") MultiplicativeExpression)* ;
MultiplicativeExpression = UnaryExpression
                           (("*" | "/" | "%") UnaryExpression)* ;
UnaryExpression    = ("not" | "+" | "-") UnaryExpression | Primary ;
Primary            = Integer | Float | String | "true" | "false"
                   | Call | Identifier | "(" Expression ")" ;
Call               = Identifier TypeArguments? "(" ArgumentList? ")" ;
TypeArguments      = "<" Identifier ("," Identifier)* ">" ;
ArgumentList       = Expression ("," Expression)* ;

Identifier         = IdentifierStart IdentifierContinue* ;
IdentifierStart    = UnicodeLetter | "_" ;
IdentifierContinue = UnicodeLetter | UnicodeDigit | "_" ;
Integer            = Digit+ ;
Float              = Digit+ "." Digit+ ;
String             = '"' (StringCharacter | EscapeSequence)* '"' ;
EscapeSequence     = "\\n" | "\\r" | "\\t" | "\\\"" | "\\\\" ;
Digit              = "0" | "1" | "2" | "3" | "4"
                   | "5" | "6" | "7" | "8" | "9" ;

BlankLine = HorizontalWhitespace* LineEnd ;
LineEnd   = "\n" | "\r\n" ;
'''

GRAMMAR_CONTRACT_NOTES: Final[tuple[str, ...]] = (
    "The canonical source extension is lowercase .apex.",
    "The project loader remains extension-neutral for frozen T1 compatibility.",
    "A source unit contains one ordinary top-level declaration.",
    "Module/import headers are optional, line-oriented, and precede the declaration.",
    "An import requires a preceding module declaration.",
    "Only module/import header lines accept an optional semicolon.",
    "Ordinary declarations and statements are not semicolon-terminated.",
    "Whitespace separates tokens but is otherwise insignificant after headers.",
    "Comments are not part of the P10-T2.1 grammar.",
    "A function must contain at least one return statement (parser constraint).",
    "A message action must be immediately followed by emit (compiler constraint).",
)


# The frozen P10 EBNF and fingerprint remain the historical base contract.
# P11.2B adds this narrow overlay instead of redefining every source as a
# general declaration list or changing module/import source-unit semantics.
P11_2B_HEADERLESS_DIRECTIVE_SOURCE_EBNF: Final[str] = r'''P11_2B_Source =
    HeaderlessDirectiveSequence | P10_OrdinarySource ;
P10_OrdinarySource = HeaderSection? Declaration EOF ;
HeaderlessDirectiveSequence = DirectiveDeclaration
                              InterDirectiveTrivia DirectiveDeclaration
                              (InterDirectiveTrivia DirectiveDeclaration)* EOF ;
InterDirectiveTrivia = (Whitespace | LineComment)+ ;
LineComment = "//" LineCharacter* LineEnd ;
'''

P11_2B_GRAMMAR_COMPATIBILITY_NOTES: Final[tuple[str, ...]] = (
    "The historical P10 ordinary source rule remains one declaration.",
    "A headerless legacy source may additionally contain two or more sequential directives.",
    "Only // line comments between complete directives are P11.2B trivia; general comments remain unsupported.",
    "A module/import header retains the ordinary one-declaration boundary.",
    "Functions and mixed declaration families do not use the directive sequence exception.",
)


def _grammar_payload() -> bytes:
    value = {
        "ebnf": APEXFORGE_EBNF,
        "header_keywords": MODULE_HEADER_KEYWORDS,
        "keywords": tuple(GRAMMAR_KEYWORD_TOKENS.items()),
        "one_character_tokens": tuple(GRAMMAR_ONE_CHARACTER_TOKENS.items()),
        "two_character_tokens": tuple(GRAMMAR_TWO_CHARACTER_TOKENS.items()),
        "string_escapes": STRING_ESCAPE_SEQUENCES,
        "top_level_declarations": TOP_LEVEL_DECLARATIONS,
        "comments_supported": COMMENTS_SUPPORTED,
        "ordinary_semicolons_supported": ORDINARY_SEMICOLONS_SUPPORTED,
        "module_header_semicolons_optional": MODULE_HEADER_SEMICOLONS_OPTIONAL,
        "source_extension": CANONICAL_SOURCE_EXTENSION,
    }
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def grammar_fingerprint() -> str:
    """Return the deterministic SHA-256 grammar-contract fingerprint."""

    return hashlib.sha256(_grammar_payload()).hexdigest()


# Filled with the hash of the declarations above. The smoke test rejects drift.
CANONICAL_GRAMMAR_SHA256: Final[str] = "09abf328030692267297950d8d5894e69f3d2c9c9af6642c90b9d298f3515f18"


__all__ = (
    "APEXFORGE_EBNF",
    "ApexSourceNameError",
    "CANONICAL_GRAMMAR_SHA256",
    "CANONICAL_MAIN_FILENAME",
    "CANONICAL_SOURCE_EXTENSION",
    "CANONICAL_SOURCE_GLOB",
    "COMMENTS_SUPPORTED",
    "GRAMMAR_CONTRACT_NOTES",
    "GRAMMAR_KEYWORD_TOKENS",
    "GRAMMAR_ONE_CHARACTER_TOKENS",
    "GRAMMAR_TWO_CHARACTER_TOKENS",
    "MODULE_HEADER_KEYWORDS",
    "MODULE_HEADER_SEMICOLONS_OPTIONAL",
    "ORDINARY_SEMICOLONS_SUPPORTED",
    "P10_T2_GRAMMAR_VERSION",
    "P11_2B_COMPATIBILITY_VERSION",
    "P11_2B_GRAMMAR_COMPATIBILITY_NOTES",
    "P11_2B_HEADERLESS_DIRECTIVE_SOURCE_EBNF",
    "STRING_ESCAPE_SEQUENCES",
    "TOP_LEVEL_DECLARATIONS",
    "canonicalize_source_name",
    "grammar_fingerprint",
    "is_canonical_source_name",
)
