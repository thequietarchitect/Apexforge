# P12.5-RCV-52 Native Execution Dispatch Capability Census

## Checkpoint and scope

This census was reconstructed on A16 from HEAD
`542be090e193b3d931d27c08e16de3efd961a01e`, with a clean initial worktree.
The annotated `afp-p12.5-freeze` tag object is
`9e2d7a4f57a10e0499d788f8584ace477f624b07`; its peeled commit equals HEAD.
The `afp-p12.4-freeze` tag object is
`7c475986ed3ed1d58cc30148603fbfe8b09529ee`, peeled commit
`13f7646f1052746f54f906076d66d29117ee2718`.
Neither tag was changed. No prior post-freeze RCV-52/53 files were present.
The active user assignment supersedes the stale P11.4A scope in AGENTS.md;
its safety, review, and frozen-contract requirements still apply.

## Live source census

* `workflow/air_runner.py`: `RegistryExecutionPlan` owns the program, entry,
  and directive-owner routing. Its builder links registry programs.
* `air/model.py`, `air/verify.py`: canonical AIR and its verifier own the
  accepted program. `VerifiedAIRProgram` is a public dataclass wrapper, not
  an unforgeable verification certificate.
* `native_backend/lowering_input.py`: delegates serialization to canonical
  `air_to_dict`; hashes canonical JSON. It does not generate native code.
* `native_backend/execution_plan_binding.py`: checks serialized program
  equality and binds entry/owner IDs. Its routing hash does not certify
  owner-program contents or prove valid entry membership.
* `native_backend/target_neutral_lowering.py`: wraps transport, AIR hash,
  routing hash, and entry metadata. This is structural representation,
  not verified executable lowering.
* `native_backend/result.py`, `payload.py`, `value.py`: provide result
  fingerprints and BOOL/I64/UTF8 payload validation. They do not provide
  a native executor, artifact attestation, or complete runtime-result mapping.
* `runtimes/native/link/apexforge_native.def`: exports only
  `apexforge_release_handle` and `apexforge_release_buffer`.
  The native sources are lifecycle infrastructure. Searches for process
  launch and program entry points in `native_backend` and `runtimes/native`
  found no native ApexForge executor/result-producing entry point.
* Frozen RCV-51 expressly defers execution dispatch and carrier execution.

## Executable environment evidence

`vswhere` with the x64 VC tools component requirement found a Visual Studio
installation. A directly nested, quoted `cmd /d /s /c` invocation failed
before entering VsDevCmd, reporting that the quoted Program path was not a
command. This establishes a quoting failure for that invocation, not a
failure of Visual Studio or evidence for an unobserved previous patch.

The checked-in `p12_5_rcv_52_toolchain_probe.cmd` instead uses a literal batch
`call`, discovers the installation through vswhere, and requests host/target
x64. Running it through `cmd /d /c` succeeded and printed:

```
Microsoft (R) C/C++ Optimizing Compiler Version 19.51.36256 for x64
```

This is compiler discovery evidence only. No ApexForge native program was
compiled or executed, and no binary determinism claim follows from it.
No full environment dump or personal machine paths were persisted.

`py --list` reported `No Installed Pythons Found!`; `py --version` reported
`Can't find a default Python.` Both `where python` and `where python3`
failed. Repository discovery found no Python executable or virtualenv config.
The project requires Python >=3.9. The focused binding test and full
regression harness were actually invoked through `py`; both stopped before
test execution with the same missing-interpreter error.

## Resumed evidence

Python 3.9.13 is now installed. The compiler probe and existing P12.2D binding
test pass. The executable `p12_5_execution_completion_census_test.py` passes:
canonical invalid-version rejection, plan/program mismatch rejection, repeated
structural lowering, and lifecycle-only exports were exercised. It also proves
that structural binding alone accepts a missing entry and is not executable
admission. Current regression results will be recorded separately.

## Historical classification (cleared)

`ENV-PYTHON-UNAVAILABLE` was the environment blocker for executable canonical
verification, focused acceptance, and current regression evidence. It was
cleared when the user provisioned Python 3.9.13. The agent performed no Python
installation or external download.

The dispatch/result ownership contract and pre-implementation semantic audit
are recorded in RCV-53. At the original census point the production chain was
unimplemented and readiness was false. The subsequently authorized bounded
implementation and executable evidence are recorded in RCV-54; the current
freeze-review decision is recorded separately in RCV-55.
