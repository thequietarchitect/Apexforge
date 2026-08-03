# ApexForge Agent Instructions

## Repository authority
- The repository owner and human reviewer retain final authority.
- Never reinterpret a requested milestone into a broader redesign.
- Work on one explicitly named roadmap slice at a time.
- Do not declare a milestone complete, frozen, canonized, or released.

## Frozen baseline
- P10 Standard Library and P10-T1 through P10-T5 are frozen.
- Baseline commit: 38a3778.
- Required freeze tags: afp-p10-t5.8-freeze and afp-p10-t5-final-freeze.
- Preserve all frozen behavior unless the active task explicitly introduces a tested compatibility change.

## Current program
- Current stage: P11.4A Identity and Nesting Architecture Audit.
- P11.3 is frozen at commit 05d836a under tag afp-p11.3-freeze; P11.2 is frozen at commit 6b82f79 under tag afp-p11.2-freeze; P11.1 remains frozen at commit 5ba048a under tag afp-p11.1-freeze.
- Immediate target: Audit identity and nesting architecture on top of the frozen P11.3 module, document-graph, and declaration-ownership foundation, including declared, alias, qualified, canonical, display, and composite identities; ownership and module/import visibility; duplicate, collision, and ambiguity handling; generic specialization identities; nested declaration scope; diagnostics; CLI, manifest, and artifact compatibility; and language-server impacts; do not change production code or begin P11.4B, P11.5, or later work.

## Required engineering behavior
- Inspect existing implementation and tests before editing.
- State assumptions and unresolved ambiguity explicitly.
- Prefer the smallest coherent patch.
- Never modify grammar, compiler, AIR, runtime, CLI, and tooling together unless the task requires every affected layer.
- Add focused tests for every behavior change.
- Run focused tests before the full regression harness.
- Report changed files, tests executed, failures, risks, and remaining work.
- Never hide failing tests, weaken assertions, delete coverage, or rewrite expected output merely to obtain a pass.
- Do not create commits, tags, releases, or remote pushes unless explicitly instructed.

## Determinism and safety
- ApexForge's compiler and runtime core must remain deterministic and usable without an AI service.
- AI-generated proposals are advisory until deterministic validation and human review succeed.
- Do not bypass validation, authority checks, TAP Check boundaries, or frozen-contract protections.
- Do not access files outside this repository unless explicitly authorized.
- Do not expose secrets, credentials, tokens, private keys, or machine-specific personal data.

## Architectural continuity
- Preserve Concordat TAM-v3 as the governance-level Token Analysis Map.
- Tap Check is user-controlled, diagnostic-only, read-only, and non-activating.
- Preserve the Quad-Vector, AETHER-AIR, Varenic Theory, rich-storytelling, and ApexMotion roadmap direction.
- The compiler Token Analysis Map implements traceability but does not replace Concordat TAM-v3.

## Working completion standard
A task is not complete until its contract, implementation, focused tests, regression impact, diagnostics, documentation impact, and known limitations have been reported.
