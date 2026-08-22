# P11 Supplemental Release Acceptance â€” Final Capability Census

Status: **FROZEN**

Baseline: terminal P11 freeze `1d2a6b8fc43eeb361b684f89f6486c9c90a7b14c` / `afp-p11-16-freeze`.

This census separates unlike capability classes instead of collapsing raw textual mentions into misleading totals.

## Core language and library

| Metric | Post-P11 authoritative candidate |
| --- | ---: |
| Core source words | **29** |
| Core lexer keywords | **27** |
| Built-in functions | **134** |
| Generic built-ins | **16** |
| Built-in types | **11** |
| Standard-library groups | **12** |
| Standard-library version | **10.12** |

The 29-word core source grammar is the 27 lexer-owned keywords plus the grammar-owned structural words `module` and `import`. Narrative-source kinds and semantic-decision scalar vocabularies are separately tracked and are not inflated into the core-keyword count.

## CLI

- **9 top-level commands:** `project`, `check`, `run`, `simulate`, `build`, `narrative`, `narrative-session`, `tap-check`, `new`.
- **4 `narrative-session` actions:** `create`, `step`, `terminate`, `interact`.
- **13 public command routes** when top-level commands and nested narrative-session actions are counted separately.
- The repository contains 10 `add_parser(...)` calls. That is an implementation-declaration count, not the user-facing top-level command count.

## Public contracts

| Metric | Count |
| --- | ---: |
| Explicit qualified package exports | **423** |
| Package export owners | **17** |
| Explicit schema contracts | **55** |
| Named `apexforge.*` schema IDs | **15** |
| Numeric schema-version contracts | **40** |
| Dynamic supported-schema sets | **1** |
| Production diagnostic-code union | **160** |

## Semantic systems

| Metric | Count |
| --- | ---: |
| Core semantic lattice axes | **8** |
| Quad-Vector implementation modules | **21** |
| Quad-Vector foundational modules | **2** |
| Quad-Vector operational capability modules | **19** |
| AETHER behavior kinds | **4** |
| Core convergence policies | **3** |

Paradox Elevation remains a **separate semantic mechanism**, represented by 4 public model/evidence classes and 2 public operations, rather than being falsely counted as a fourth convergence policy.

## Packages, rich documents, and interchange

- **4 package tiers:** core, standard, domain, experimental.
- **7 rich-document block kinds.**
- **3 canonical package/project operations** in the current owner set.
- Interchange exposes **1 model + 2 operations** (3 public contract elements).

## Freeze and fingerprint architecture

| Metric | Count |
| --- | ---: |
| Freeze tags | **166** |
| Annotated freeze tags | **132** |
| Historical lightweight freeze tags | **34** |
| P10 freeze tags | **7** |
| P11 freeze tags | **157** |
| Other-phase freeze tags | **2** |
| Canonical public SHA-256 anchors | **37** |
| Public fingerprint functions | **44** |
| Private mirrored/reference hashes | **9** |

## Terminal P11 repository scale

- **612 / 612** tracked Python files parse.
- **277** smoke tests are discoverable at the terminal P11 freeze.
- **178 / 178** routed verification surfaces are closed.
- **48 / 48** durable-current verification rows pass.
- **130 / 130** non-durable rows are resolved.

## P10 reconciliation

The frozen P10 standard-library contract remains intact after P11:

| P10 metric | P10 | Post-P11 | Delta |
| --- | ---: | ---: | ---: |
| Built-in functions | 134 | 134 | 0 |
| Generic built-ins | 16 | 16 | 0 |
| Built-in types | 11 | 11 | 0 |
| Standard-library groups | 12 | 12 | 0 |

P11 therefore expanded ApexForge **above** the standard-library layer rather than silently rewriting that frozen contract.

## Milestone reconciliation expansion

The first P11 milestone reconciliation did **not** authorize the census to freeze. It found five established P11 capability families that were present in milestone/repository evidence but lacked dedicated census sections:

1. Agents
2. Authority / Workflow
3. Identity / Nesting / Resolution
4. Incremental Cache
5. TAM

Those five families are now represented explicitly.

### TAM

- **3 implementation modules**
- **27 root public exports**
- **Trace schema version 1**
- **10 canonical trace domains**
- **4 public trace model types**
- **19 production trace-adapter operations**
- **1 whole-map composition operation**

### Incremental Cache

- **6 implementation modules**
- **9 root public exports**
- **33 module-level public contract elements**
- **3 canonical layers:** Capture, Resonance, Stability
- **7 public class declarations**
- **23 public function declarations**
- **Cache schema version 1**

### Agents

- **7 implementation modules**
- **10 module-level public contract elements**
- **7 public class declarations**
- **3 public function declarations**
- The package root intentionally has no explicit `__all__`; the module contracts remain the counted ownership surface.
- Agent planning/projection remains distinct from host-effect execution.

### Identity / Nesting / Resolution

- **6 canonical owner files**
- **17 explicit exports**
- **12 public class declarations**
- **5 public function declarations**
- **4 visibility bases:** same source, same module, imported module, legacy context

### Authority / Workflow / Governance

- **24 canonical owner files**
  - authority: 7
  - authorization: 1
  - governance: 1
  - principal compiler: 1
  - workflow: 14
- **4 explicit exports**
- **45 public class declarations**
- **23 public function declarations**
- TAP Check governance mode remains **observational**.

## SRA-A final census freeze

The expanded P11 milestone capability reconciliation rerun closed with:

- **16 / 16** major P11 milestone families represented.
- **5 / 5** previously missing capability families closed.
- **0** remaining census gaps.
- Compiler TAM: **ACCOUNTED_DEDICATED**.
- Production mutation: **none**.
- Existing tracked-file mutation: **none**.

The Final Capability Census is therefore frozen under the annotated tag
`afp-p11-sra-a-final-capability-census-freeze`.

This freeze seals **Supplemental Release Acceptance A only**. It does not
freeze or satisfy the remaining release-acceptance layers: real `.apex`
PowerShell acceptance, Visual Studio experimental acceptance,
PowerShell/Visual Studio equivalence, or optimization acceptance. P12 remains
blocked until those later supplemental gates are completed.
