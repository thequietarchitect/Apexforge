# P12.5-RCV-53 Native dispatch/result contract and semantic audit

Status: pre-implementation contract. Python 3.9.13 clears the interpreter
blocker. The user authorized the explicit native subset below; broader
AIR/managed/native equivalence remains P12.7 work. This is not a gate pass.

## Ownership and invocation

`apexforge.native_backend` owns deterministic native build/dispatch.
`workflow.air_runner.RegistryExecutionPlan` continues to own entry and routing.
Canonical verified AIR remains the sole semantic authority. Dispatch accepts
only a provenance-bound backend-produced Windows x64 executable and uses a
structured child-process argument vector with shell execution disabled.
There is no managed fallback, interpreter subprocess fallback, or arbitrary
transport protocol. Compiler discovery may invoke the developer batch file;
program dispatch must not use that shell mechanism.

Admission must revalidate canonical AIR through its existing verifier and
validate the plan against it, including entry and owner relationships. Merely
constructing `VerifiedAIRProgram` or trusting a supplied fingerprint is
insufficient. Recompute immutable input/routing records before build/dispatch;
reject mismatches and mutation. Preserve the existing canonical owners rather
than adding backend name resolution.

The build receipt must bind canonical AIR, validated routing, lowering profile
and version, emitted source, toolchain identity/options, and final executable
digest. Verify the executable's identity before launch; the eventual design
must address replacement between verification and launch. Never accept an
arbitrary executable because it emits plausible output. Use explicit cwd,
environment policy, timeout, exit-code policy, and bounded output handling.

## Result boundary

Reuse `CanonicalExecutionResult` only for its actual contract: an uppercase
64-hex input fingerprint, SUCCESS/FAILURE, and validated named BOOL/I64/UTF8
values. It has no native artifact field, trace/event schema, float encoding,
or process-failure taxonomy. Do not silently truncate arbitrary Apex integers,
invent float/null encodings, or label infrastructure failures as semantic
program failures. Bind the result input fingerprint to the validated build
receipt and retain artifact/dispatch provenance separately.

A successful process exit alone is not a canonical ApexForge result. The
supported lowering profile must specify and test the exact native observable
and its canonical mapping before acceptance. Output framing and supported
program domain are specified below.

## Bounded profile and pre-implementation audit

Profile: `apexforge.native.win-x64.i64-literal-state-set/v1`.

Accepted: exact canonical dataclass types, one directive (order zero), one
principal without authority/role membership, 1–256 INT states with raw-int or
AIRIntegerLiteral signed-I64 initializers, 1–4096 legacy `set_int` assignments
with raw-int or AIRIntegerLiteral signed-I64 values, and single-path canonical
`max_weight` causal decisions. Every decision must be referenced exactly once;
directive decision order and path assignment order are preserved. The plan's
exact entry must equal the directive ID and its single owner must serialize
identically to verified AIR. IDs are nonempty strings of at most 256 characters.

Rejected before compiler discovery: non-INT types, out-of-I64 values, other
expressions/operators, action carriers, conditions, alternative paths, calls,
functions, workflows, directive invocations, events/emissions, effects,
requirements, authority checks/declarations, roles, directive authorities,
multiple directives/principals, unused/repeated decisions, entry aliases,
owner mismatch, unknown types/fields, and profile-limit violations.
Canonical verification is rerun; a wrapper or supplied digest is not proof.

No semantic interpretation is required: explicit INT maps to native I64;
verified exact state IDs become storage relocations; `set_int` becomes a store;
singleton paths require no branch choice. The backend must not call a runtime
evaluator, infer types, resolve source names, copy operator/causal policies, or
precompute program outputs. Tests may use canonical runtime execution as an
oracle. This audit authorizes implementation of this profile only, subject to
an executable contract gate and inspection of the actual lowering.

The native observable is exactly eight little-endian bytes per state in
declaration order, emitted using Windows WriteFile. It is a fixed profile-local
result encoding, not a general transport. Dispatch takes no stdin or arbitrary
arguments; it maps signed values to existing I64 payload values named by state
ID. It does not invent trace/event/effect result semantics.

Receipts bind AIR, complete admitted routing/ownership, profile, source,
toolchain inputs/options, and executable digests. CanonicalExecutionResult's
input fingerprint is the receipt fingerprint. Only backend-issued artifacts
are dispatchable. A Windows read handle denies write/delete sharing from image
hash validation until child exit. Launch uses a structured argument list,
explicit cwd/environment, bounded capture, timeout, and no shell. Build/process
failure, stderr, malformed output, substituted artifacts, and changed inputs
raise classified errors rather than fabricated semantic FAILURE results.
No managed or interpreter fallback exists.

Determinism acceptance compares source, receipt, whole-PE, output, and result
fingerprints across repeated builds/runs on the recorded toolchain. It does not
claim binary identity across different toolchain installations or versions.

## Explicit no-second-semantic-implementation audit

At this pre-implementation audit, the frozen lowering modules only serialized
and bound AIR; no new production lowering was accepted. The following hazards
defined the admission boundary. RCV-54 records inspection and executable tests
of the subsequently implemented bounded profile:

| Observed canonical structure | Existing semantic owner | Native acceptance condition |
| --- | --- | --- |
| AIR identifier names and call targets | Canonical verification/runtime resolution | Consume canonical resolved identities; no independent lookup policy |
| Binary/unary operator strings without a resolved-operation field | Canonical verifier and RuntimeEngine expression handling | Translate only an explicitly verified operation mapping; no backend overload/type inference |
| Causal decisions retain weighted alternative paths | CausalEngine.select_path | Do not reproduce max-weight/tie-breaking policy or independently select a path |
| Authority checks and directive requirements | AuthorityEngine and registry execution guards | Preserve canonical decisions; never omit checks for native convenience |
| Conditions, functions, state actions, effects | Canonical AIR and runtime contracts | Preserve verified control flow and ordered actions; unsupported nodes fail before compilation |
| Public VerifiedAIRProgram wrapper and mutable owner mapping | AIRVerifier and RegistryExecutionPlan | Revalidate provenance and ownership rather than trusting wrapper identity |

`AIRVerifier.verify` returns the original program with diagnostics; it does not
produce a resolved typed opcode graph. `RegistryExecutionPlan` supplies routing,
not such a graph. This observation does not establish that native translation
is impossible. It rules out treating current serialization as an already
executable lowering, copying RuntimeEngine into the backend, or evaluating the
program in Python and embedding its precomputed answer in a native executable.
Any restricted profile must explicitly reject everything outside its proven
domain and must not be advertised as whole-language execution completion.

## Required acceptance evidence

1. Canonically verified positive programs execute emitted native instructions
   and yield documented canonical results through the production API.
2. Unverified/mismatched input, unsupported AIR, invalid routing, changed
   artifacts, failed builds, malformed results, abnormal exits, and timeouts
   fail closed without fallback. Negative tests must exercise executable paths.
3. Repeated builds and runs establish the stated determinism policy, distinguishing
   semantic/source identity from whole-PE reproducibility.
4. Result receipts demonstrate the complete input-to-artifact-to-result chain.
5. Focused tests precede current P12 and full repository regression evidence.
   Static documentation assertions cannot substitute for native execution.

Until all applicable evidence exists, the readiness flag must remain false.
RCV-55 records the current value of
`P12_5_READY_FOR_EXECUTION_COMPLETION_FREEZE_REVIEW` with regression evidence.
No commit, tag, release, staging, push, or P12.6 work is authorized by this record.
