# P12.5-RCV-54 Bounded native execution acceptance

Profile: `apexforge.native.win-x64.i64-literal-state-set/v1`.
The RCV-53 contract is the enumerated admission boundary. This is native
execution of that profile only, not whole-language execution or P12.7 equivalence.

## Production chain

`native_backend/native_execution_contract.py` revalidates the exact canonical
AIR graph and snapshots the canonical registry plan's ownership mapping.
It enforces the closed profile before filesystem writes or compiler discovery.
Its immutable admission contains source fingerprints, exact state-ID
relocations, literal initializers, and ordered stores. It does not calculate
final state or evaluate expressions.

`native_backend/native_execution.py` emits volatile I64 initialization/stores
and Windows output calls. MSVC compiles/links a real x64 executable without a
managed runtime, Python child, C runtime, or fallback executor. The generated
entry performs the stores; output is not a precomputed Python execution result.

The backend issues an in-process artifact ticket and deterministic receipt.
The receipt binds AIR, exact admitted ownership/routing, entry, state IDs,
profile, source bytes, compiler/linker/companion DLL and kernel32 library
hashes, fixed compiler options, and the executable digest. Build paths and
timestamps are excluded. `/Brepro` applies to both compiler and linker.

Dispatch re-admits inputs, validates the issuance record, and checks the image
digest while holding a Windows handle denying write/delete sharing through
child exit. It launches exactly the image path through `subprocess.Popen` with
`shell=False`, explicit cwd, a minimal environment, closed stdin, timeout, and
file-backed capture. The issued program emits at most 2,048 bytes. Any exit
failure, stderr, output-size mismatch, or timeout fails closed.

Signed little-endian I64 output is mapped to `CanonicalExecutionValue` using
the original state IDs. `CanonicalExecutionResult.input_fingerprint` binds the
entire build receipt. Infrastructure faults raise `NativeExecutionError` with
a stable code; they are not invented ApexForge semantic FAILURE results.

## API

From a repository-configured Python environment:

```python
from pathlib import Path
from air.verify import AIRVerifier
from workflow.air_runner import build_registry_execution_plan
from apexforge.native_backend.native_execution import execute_native

plan = build_registry_execution_plan(registry, "main")
verified = AIRVerifier().verify(plan.program).require_verified()
build_root = Path("build")
build_root.mkdir(exist_ok=True)
evidence = execute_native(verified, plan, build_root)
result = evidence.result
```

`execute_native` removes its temporary build when done. `build_native` and
`dispatch_native` are separately available when the caller needs to retain
an artifact; the build directory must exist and be empty. Issuance is scoped
to the current backend process. A receipt cannot import an arbitrary binary
or reauthorize one in another process.

## Executable evidence

Run `py -B apexforge/p12_5_native_profile_contract_test.py` before
`py -B apexforge/p12_5_native_execution_acceptance_test.py`.

The contract gate uses canonically verified fixtures and prohibits process
launches during admission. The same rejected-surface matrix is passed through
`build_native` with a compiler-discovery trap, proving rejection precedes
compilation. Exact dataclass field inventories make future schema expansion
fail closed pending review.

Native positive tests execute real generated programs and compare state with
the existing canonical runtime as a test oracle. They cover signed-I64 extrema,
ordered overwrites, untouched state, Unicode IDs, and the 256-state/4,096-store
profile maximum. Repeated independent builds compare whole executable bytes
and receipts; four real dispatches compare outputs and canonical results.

Negative tests cover modified executable bytes, forged receipts/tickets/paths,
changed inputs, image write-lock enforcement, invalid timeouts, compiler
failures, malformed result bytes, stderr, nonzero exit, and timeout cleanup.
Process-failure/malformed-output cases use explicitly marked fault injection
at the OS adapter boundary. Positive native execution and artifact byte
substitution checks are live, not mocked.

The executable acceptance script writes
`p12_5_rcv_54_native_execution_acceptance.json` with observed provenance and
source hashes. A native gate pass is not a regression or freeze-review pass.

## No-second-semantic-implementation audit of the actual code

* The contract imports canonical dataclasses, INT, AIRVerifier, and existing
  registry binding/serialization. It imports no expression evaluator or causal
  selector. Exact canonical IDs are relocated only after canonical verification.
* The emitter consumes admitted literals and store order. It preserves even
  overwritten stores; it has no operator table, type inference, source-name
  resolver, branch selector, managed calls, or runtime evaluator.
* Native control flow handles byte encoding and Windows I/O failures only.
  There is no ApexForge conditional or weighted-path selection in this profile.
* Tests inspect these dependencies and emitted store order, and compare real
  native results with the existing runtime only in test code.

No frozen production files were changed. The new modules are opt-in APIs;
grammar, compiler, canonical AIR, managed runtime, CLI, and lifecycle ABI stay
outside this patch. Frozen historical smoke inventories are unchanged: new
acceptance files use `_test.py`, not the counted `_smoke_test.py` suffix.

## Limits and remaining review

Reproducible PE identity is proven only on the recorded toolchain. Receipts
provide provenance within a trusted backend process, not remote signatures or
protection against arbitrary hostile Python code in that process. Build roots
and the installed toolchain must be trusted. Persistent artifact admission,
other platforms, language expressions, authority-bearing programs, events,
effects, traces, and wider behavioral equivalence are not supported by v1.

Current regression evidence and the final readiness decision are separate.
No staging, commit, tag, push, release, or P12.6 work is authorized here.
