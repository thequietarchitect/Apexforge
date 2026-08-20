# P11-SRC-C - Deterministic Semantic Decision Source Parser

## Status

Production parser slice following `afp-p11-src-b-freeze`.

P11-SRC-C introduces opt-in semantic-decision source recognition and deterministic parsing into the immutable P11-SRC-B AST. It does not construct P11.10 semantic objects or execute semantic-decision behavior.

## Public parser surface

`apexforge/language/semantic_decision_parser.py` exports:

- `SemanticDecisionSourceParseError`
- `is_semantic_decision_source_document`
- `parse_semantic_decision_source`

Recognition is lexical and exact: after leading whitespace, the first identifier must be `decision`.

This keeps semantic-decision documents isolated from ordinary AIR source and narrative `story` documents.

## Initial source grammar

A document contains one or more `decision` declarations.

A decision may contain, in source order:

- `candidate NAME`
- `candidate NAME when EXPRESSION`
- `incompatible LEFT, RIGHT`
- one optional `converge using POLICY { ... }`
- one optional `paradox elevate` declaration with optional `when` and `requires` clauses

The convergence block preserves authored candidate-reference order.

`POLICY` may be a quoted string or a dotted identifier. P11-SRC-C does not verify that a policy is a canonical P11.10 policy.

Candidate `when`, Paradox Elevation `when`, and Paradox Elevation `requires` values are preserved as source scalars or source expression text. They are not evaluated.

## Determinism and provenance

Repeated parsing of the same source and source name produces equal immutable source documents.

All parser-created source records preserve `SourceSpan` provenance derived from `SourceText`.

Malformed input raises `SemanticDecisionSourceParseError` with:

- severity `error`
- diagnostic code `APX-SEMANTIC-DECISION-SYNTAX`
- stage `parse`
- the source span where parsing failed

## Predecessor compatibility

The frozen P11-SRC-B smoke test is a stage-boundary proof: it intentionally asserts that the semantic-decision parser and lowering modules do not yet exist. The parser-absence assertion becomes intentionally false in P11-SRC-C and therefore is not a forward-compatible regression condition.

P11-SRC-C leaves the frozen P11-SRC-B test unchanged and directly re-verifies the durable B capabilities: frozen source records, exact tuple ownership, source provenance, and optional keyword/value structural invariants.

## Ownership boundary

P11-SRC-C owns source recognition and parsing only.

P11-SRC-B continues to own the immutable source AST.

P11.10 continues to own semantic condition evaluation, admissibility, convergence policy behavior, convergence resolution, incompatibility evidence semantics, Paradox Elevation assessment/elevation, validation, projection, and reporting.

The ordinary ApexForge lexer keyword table remains unchanged in this slice. The parser uses a dedicated opt-in scanner, following the established narrative-source ownership pattern.

## Deliberate exclusions

P11-SRC-C does not:

- add the proposed semantic-decision words to `language.lexer.KEYWORDS`;
- extend `SourceUnitNode`;
- modify the ordinary AIR parser or compiler;
- modify `ProjectBuild`;
- construct `AdvancedCondition`, `CandidateAlternative`, or other P11.10 objects;
- validate candidate-reference resolution;
- validate canonical convergence policy IDs;
- evaluate authored condition text;
- resolve convergence;
- assess or perform Paradox Elevation;
- create semantic-decision lowering;
- add runtime behavior.

## Next slice

P11-SRC-D will begin from the P11-SRC-C freeze with a deliberate red gate for deterministic semantic lowering/adaptation. It will translate the parsed source records into the already-frozen P11.10 semantic-decision contracts without duplicating P11.10 semantic authority.