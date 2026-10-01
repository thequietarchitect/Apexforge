# P12.8-5 — Security and Resource-Lifetime Closure

## Authority, baseline and threat model

This is bounded security/resource-lifetime review evidence for human approval, not a
universal secure claim, final backend closure or freeze declaration. Branch is
`p12-8-backend-closure`; HEAD and peeled `afp-p12.7-freeze` are
`e25b98699098f9b3d61d1478c42ea27b54aea78f`. Before implementation, the exact eight
incoming candidates were individually hashed, tracked/cached diffs were empty and no
generated native/bin/obj/__pycache__ residue remained. Only the requested new test
and this document are added; all production and observer modules are unchanged.

Threat model: accidental/stale cross-binding, caller-supplied substitutions at existing
validation seams, released executable custody, stale retained metadata/trace/result
association, principal/routing/profile confusion and observation/cleanup path confusion.
Tests use controlled repository-owned roots, files and API inputs. No tampered image is
launched: a launch trap protects negative cases; positive cases execute real native code.
Installed tools, issuing Python process and quiescent test-owned build roots retain the
frozen trusted-custody assumption. This is not hostile-process isolation, remote artifact
import/signature validation, credential revocation, an OS security audit or a race-proof
filesystem namespace guarantee.

```text
P12_8_SEMANTIC_AUTHORITY=CANONICAL_AIR
P12_8_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P12_8_MSC_SEMANTIC_ENGINE=False
P12_8_MSC_RUNTIME_DEPENDENCY=False
P12_7_THREE_INDEPENDENT_EXECUTORS_CLAIM=False
P12_7_DOTNET_INDEPENDENT_EXECUTION_PROVEN=False
```

MSC supplies engineering lifecycle vocabulary only. The governing invariant is:

`Retained Resource => Known Owner + Known Purpose + Known Lifetime + Valid Authority/Provenance Binding`

`Expired Lifetime => No Authorized Reuse` applies to expired ephemeral custody; persistent
evidence instead requires explicit identity binding and validation before reuse. Deletion
alone does not prove integrity, and persistence alone does not prove unsafe retention.

## Existing security evidence reused

| Unchanged suite / implementation | Reused boundary | Qualification |
| --- | --- | --- |
| P12.5 native profile ContractTests / native_execution_contract | Exact schema, unsupported surfaces, owner transport, routing, I64/count bounds, admission before compiler | Bounded v1 only; no authority-bearing native programs |
| P12.5 native acceptance NativeTests / native_execution | Process-local issuance tuple, receipt substitution, image digest/lock, input mismatch, malformed output, timeout/build failure and no fallback | Positive native is real; failure seams use disclosed injected OS outcomes |
| P12.6-3 metadata identity | Source identity, stale source/span, operation/plan association and owner mismatch | Canonical metadata does not evaluate AIR |
| P12.6-4 source/native mapping | Emitter correspondence, stale/substituted mapping/source/receipt/image and unchanged admission | Hand-built native fixture has UNMAPPED_SOURCE; no invented language-source mapping |
| P12.6-6 trace/provenance | Scope/payload/order/family/authority guards and result association substitution | Supplied evidence and provenance, not reconstructed intermediate execution |
| P12.6-8 controlled integration | Native pre/post validation, result/receipt/image substitution, wrong managed context/policy, exactly-once execution and cleanup | Canonical owners execute; retained evidence is not a second engine |
| P12.7 equivalence | Canonical/managed/native projection and native no-fallback within bounded domain | Does not prove three independent executors or independent .NET execution |
| P12.8-2 observer | Containment, parent traversal, actual link/junction, reparse flags, I/O unavailable, inert-file inventory, semantic passivity | Observation is stat-only; quiescent selected roots, no authority granted by presence |
| P12.8-3 continuity | Fresh native custody, zero residue, weak issuance release, repeated bindings and retained wrapper release | Bounded repeated observations, no universal leak guarantee |
| P12.8-4 load envelope | Maximum sampled state custody and unchanged six-pillar/resource-bound qualifications | Reused inspection evidence; expensive load suite is not rerun for this security-only composition |

The new suite composes lifecycle boundaries rather than copying these individual
contracts. All listed predecessor security suites except the load envelope are rerun
below. Existing P12.5–P12.7 limitations remain in force.

## Resource lifetime and ownership model

The test-only frozen `LifetimeWitness` contains scope, an analytical state label and an
immutable ResourceSnapshot. ACTIVE, RETAINED_AUTHORIZED, RELEASED and STALE are evidence
labels, not a new authority state machine or production expiration mechanism. A scope
groups different resources; a retained evidence witness after file release never denotes
resurrection of the root/image. Existing validators decide admission, not the witness.

| Resource/class | Owner and purpose | Authorized lifetime and binding |
| --- | --- | --- |
| Build child, generated C, obj, discovery command, executable / IRR | Test-owned TemporaryDirectory; one fresh native build/dispatch | Until child scope exits; native image/receipt bound by existing issuance and AIR/routing digest checks |
| Mapped artifact and weak issuance entry / DHF | Caller wrapper and backend weak-key table; process-local artifact admission | While ticket owner is reachable, with live issued image and immutable issuance tuple; last wrapper release removes entry |
| Native retention ledger / DHF | Test function; validate three intentional retained outcomes | Exactly three lifecycles/test lifetime; each original binding/evidence revalidated after file cleanup |
| Canonical receipt/result review evidence / CER | Explicit ledger/document custodian; preserve original outcome/provenance | May persist after executable deletion; does not authorize importing or relaunching an image |
| AIR/directive/principal/routing/profile provenance / SHR | Existing canonical structures; continuity identity | Remain bound under reconstruction/revalidation; not replaced by observer identity or incidental resource identity |
| Neighbor sentinel / IRR | Outer test hierarchy; detect scope escape | Survives each inner cleanup; removed only when its separately owned outer scope exits |

File DBL and wrapper/ticket DBL are separate. The test deliberately keeps a wrapper
reachable just long enough after file cleanup to verify missing-image rejection, then
releases it. A still-reachable ticket does not make a nonexistent executable reusable.
Missing path evidence records root_present=0, not a valid live artifact. No file is
recreated to manufacture a stale-resource scenario; no ticket is manually revoked or
forged in the composition test.

## New composed tests and outcomes

`p12_8_5_security_resource_lifetime_test.py` has three methods:

1. Three real sequential native lifecycles: frozen P12.5/P12.7 A fixture, B with a
   different supported literal assignment, then identical-content A again. Canonical
   AIR is the expected-result authority. Each fresh root starts empty, the prior roots
   are absent and prior weak tickets released. One legitimate retained dispatch per
   lifecycle succeeds and agrees with the complete canonical projection.
2. A resource snapshot cannot be passed as a NativeArtifact, cannot launch native code
   and has no execute method. Measurement counts/hashes are observational evidence,
   not execution/provenance authority.
3. Composed path, absence and cleanup custody: parent traversal and neighboring-root
   observation reject; an inert .exe is inventoried without launching it; controlled
   symlink/junction targets and redirected authority roots reject; redirects themselves
   are detached before owned cleanup, and a neighboring sentinel remains unchanged.

### Artifact, receipt, mapping and routing/profile substitution

Each real artifact is tested before legitimate dispatch. Image bytes are appended only
inside the owned root; canonical dispatch rejects with NATIVE_ARTIFACT_SUBSTITUTED while
the launch seam is trapped. Original bytes are restored before the positive case.
Receipt profile and routing are replaced and the receipt digest recomputed; existing
issuance-tuple validation rejects NATIVE_ARTIFACT_INVALID before launch. Later samples
also reject the previous different-input lifecycle's receipt on the current artifact.
A different-input native mapping and a stale plan association reject before retained
dispatch. None of these checks disables hashing, changes system policy or runs a
modified executable.

The physical generated C file is a build input, not an independently trusted post-build
execution authority. Protected source identity is the canonical emitter content bound
into mapping/receipt and the compiled image digest. This stage does not invent a
requirement that changing/deleting scratch C after compilation must invalidate an
otherwise intentionally owned issued image. Scratch files still terminate at their DBL.

### Cross-execution and principal/authority binding

A artifact plus B verified AIR/plan rejects NATIVE_PROVENANCE_MISMATCH before launch.
Verified AIR combined with another program's owner plan also rejects. A principal-only
variant changes the actual Principal.id and matching directive principal reference;
its association differs and cannot consume the original image. Thus identical semantic
final values do not permit principal/provenance exchange.

Native v1 deliberately excludes roles, authority grants/checks and authority-bearing
programs. No live credential expiry or new authorization subsystem is asserted. Broader
managed policy/context identity and actual authority trace guards are reused through
P12.6 controlled integration and trace suites. The authority/principal marker below is
qualified by these existing exposed contracts, not a universal revocation guarantee.

### Stale-after-DBL and retained evidence

After each child exits, its absence-aware inventory records files=0, root_present=0;
the filesystem snapshot is associated with a named LifecycleBoundary. Calling canonical
dispatch with the still-reachable old wrapper rejects NATIVE_ARTIFACT_UNAVAILABLE before
launch; mapped validation rejects FileNotFoundError. Releasing the artifact wrapper then
releases its weak ticket and restores the baseline issuance count. Prior roots/tickets
are checked again at the next independent lifecycle.

The retained native outcome deliberately survives. validate_snapshot succeeds after
physical cleanup under its original binding. Changed AIR/plan bindings, another
lifecycle's collection/evidence and an altered result-provenance fingerprint reject.
Each earlier retained ledger entry is revalidated against its own binding, including
at the end of the three-lifecycle sequence. Persistent evidence is retained intentionally,
not treated as stale executable custody.

Identical-content A returns at iteration three. Content-addressed identities need not
differ across independent executions; they are not per-execution nonces. The contract
requires fresh artifact custody and correct binding, not artificial identity churn or
rejection of intentionally identical canonical evidence. No stale resource is consumed
as the current executable.

### Observer and cleanup confinement

Unauthorized `..` and neighboring roots reject with ObservationPathError. Redirected
root, descendant and authority-root combinations reject through the existing observer.
All sentinels/targets are controlled temporary neighbors inside the test hierarchy;
there are no destructive external-path tests. Redirect cleanup uses unlink/os.rmdir
on the link itself, never a recursive traversal of its target. TemporaryDirectory then
cleans only its directly owned root. Both native and observer sentinel bytes survive
inner cleanup. Missing versus present-empty root fingerprints differ through root_present;
I/O failure remains unavailable under unchanged predecessor tests. Absence is a valid
observation of absence, not a valid artifact or fabricated successful security check.
This does not establish protection against concurrent adversarial namespace replacement.

## Cache participation, bounds and host policy

`P12_8_SECURITY_CACHE_REUSE_SURFACE=NONE_FOR_TESTED_PATH`

No persistent compiler/discovery/result cache participates. Tool discovery/hashing is
performed per build. The native weak issuance table is process-local authorization
bookkeeping, not a durable cache/import mechanism. Python/OS library retention is not
reclassified as a backend cache. No unrelated cache surface is introduced.

Frozen security controls remain 1–256 states, 1–4096 stores/decisions, signed-I64 literal
values, exact admitted schemas and empty unsupported/action surfaces, one directive and
principal, exact fixed output 8 bytes/state (at most 2048 bytes), zero stderr, finite
positive timeouts at most 300 seconds (build default 60; dispatch default 10), image
custody/digest checks, shell=False structured dispatch and bounded retention checks.
Unchanged native admission/acceptance regressions exercise rejection before compile,
malformed output, invalid timeout, child kill/wait on timeout and build failures without
fallback. Generated C/ABI and installed toolchain assumptions remain frozen.

RESOURCE_BOUND_GAP persists for aggregate parent/child/Python memory, handles and
artifact-byte/lifecycle-wide budgets. Output/retention validation does not impose a
whole-process allocation ceiling. P12.8-4 measured timings are not new security limits
or evidence of a vulnerability. Child peak resource visibility remains incomplete.

Windows Application Control is unchanged. No policy bypass, disabling, signature change
or alternate execution fallback is used. Current generated positive images were allowed
to execute; this does not attest universal policy permission or erase predecessor
0x800711C7 environmental history. Any future block requires environmental classification,
not silent fallback or weakening host controls.

## Failure classification and focused validation

Initial focused run: TEST_FIXTURE_DEFECT, one error among three methods in 0.050 seconds.
The principal variant used nonexistent Principal.name; corrected to the actual canonical
id field after inspecting Principal. Failure preceded native construction. Production
and observer implementation were never modified. Corrected final focused run: three
methods PASS in 9.939 seconds, three real build/dispatch lifecycles, no skips. Shell
sandbox setup initially failed (TEST_INVOCATION_DEFECT/environment runner startup);
the same read-only baseline command was rerun with execution approval.

Regression results, preservation and evaluated markers follow below.

## Exact regression results

All runs use LYRA Python
`C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe -X utf8 -B`.
Ordinary suites run as `apexforge/<suite>.py`, sequentially after the focused PASS.

| Exact suite / selected class | Final methods | Seconds | Final result |
| --- | --- | --- | --- |
| p12_8_5_security_resource_lifetime_test.py | 3 | 9.939 | PASS |
| p12_8_2_resource_observability_ownership_test.py | 19 | 5.283 | PASS |
| p12_8_3_execution_continuity_resource_pressure_test.py | 8 | 89.457 | PASS |
| p12_7_2_bounded_behavioral_equivalence_test.py | 4 | 60.510 | PASS |
| p12_6_3_metadata_identity_association_test.py | 8 | 0.045 | PASS |
| p12_6_4_source_native_mapping_test.py | 11 | 10.458 | PASS |
| p12_6_6_trace_provenance_reference_test.py | 12 | 3.368 | PASS on unchanged retry |
| p12_6_8_controlled_trace_integration_test.py | 12 | 16.929 | PASS |
| p12_5_native_profile_contract_test.py | 7 | 0.036 | PASS |
| p12_5_native_execution_acceptance_test.NativeTests | 13 | 14.049 | PASS |

Final selected runs: 97 passing test methods, no skips. Counts are method counts;
nested predecessor assertions, sampled cases and injected fault variants are not
inflated into additional tests. The earlier failed attempts are separately disclosed.

P12.6-6 initially ran 12 methods in 4.496 seconds with one error: PermissionError at
line 258 when its unchanged test attempted to write the owned program.exe after two
legitimate dispatches. The batch stopped; integration/admission/acceptance did not run
until the subsequent remainder command. Classification: ENVIRONMENTAL_CONSTRAINT,
transient Windows image-write denial. Inspection confirmed child.wait and scoped
capture/image file closures; exact OS actor/cause is not established. The unchanged
suite passed on the next invocation. No sleep/retry was inserted into the test, no
assertion was weakened, and no host security policy was changed. This is not evidence
of an Application Control launch block or a proven backend security defect; it remains
a disclosed environment/reliability qualification.

Native acceptance was loaded by the unchanged NativeTests class to avoid its __main__
block writing the tracked frozen P12.5 JSON report. Exact selection:

```python
import sys, unittest
sys.path.insert(0, "apexforge")
suite = unittest.defaultTestLoader.loadTestsFromName(
    "p12_5_native_execution_acceptance_test.NativeTests")
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
```

This executes all 13 acceptance methods unchanged, including native maximum admission,
image-lock, process-failure and substitution controls. Its report-writing main block
and incidental imported ContractTests discovery are not executed; the seven admission
methods were run separately. No full RCV-51/50 or historical closure harness was started.

## Remaining qualifications and gaps

| Classification | Remaining surface | Disposition |
| --- | --- | --- |
| RESOURCE_BOUND_GAP | Aggregate memory/handles/artifact/lifecycle-wide budgets | Preserved from census/load envelope; no empirical maximum becomes a security cap |
| SECURITY_EVIDENCE_GAP | Adversarial concurrent in-process/namespace races, hostile toolchain/remote import, external credential revocation | Outside frozen trusted-custody model; no universal integrity/isolation claim |
| NATIVE_PROFILE_LIMIT | Authority-bearing AIR, wider actions/types/platforms | Excluded and still fail closed; no profile expansion |
| ENVIRONMENTAL_CONSTRAINT | One unchanged P12.6-6 image-write denial | Unchanged retry passed; cause not isolated and history retained |

No implementation defect was demonstrated, no production fix was attempted and no
observer extension was justified. Security/lifetime PASS applies to the tested existing
contracts and their composition. It does not close every census lifecycle surface,
compiler-descendant resource accounting, all memory/resource bounds, whole-language
security or the six-pillar backend. Reproducibility/determinism closure, final closure,
freeze preparation and P13 were not activated; existing determinism checks inside
unchanged regression suites retain their predecessor scope.

## Preservation evidence and exact Git status

Incoming SHA-256 values were checked before edits and matched after final regressions:

| Incoming path | Preserved SHA-256 |
| --- | --- |
| apexforge/tooling/resource_observability.py | BDAA6A4CCBB24B8122FA1CA658134F2741EB13926AC5940A70D186A3EBB92D54 |
| apexforge/p12_8_2_resource_observability_ownership_test.py | 473D57CB22C32141C72A1F0A673B8746891A62CEA7932BEF3CC97E26767C9769 |
| apexforge/p12_8_3_execution_continuity_resource_pressure_test.py | 638EBFB10A6DD6CCA11E097CAEE171FC69CA50792A28D2F0337F7BCC8E1A003E |
| apexforge/p12_8_4_scale_c_load_performance_resource_test.py | 3FB5B6F4D32C55F4AC8F5AB037171844BE8B8BE617A6FFB89AE475671B991067 |
| docs/p12/P12_8_1_BACKEND_CLOSURE_CAPABILITY_CENSUS.md | CE792211422D0F3242D97474B918F71E35FBFD2965225814F10DFF7C158C02FB |
| docs/p12/P12_8_2_RESOURCE_OBSERVABILITY_AND_OWNERSHIP_FOUNDATION.md | 12CDC7BE19E72B6D656EC28936D5CC45365C3DD2CB08D28FBB8EB86CA810A071 |
| docs/p12/P12_8_3_EXECUTION_CONTINUITY_RESOURCE_PRESSURE_VALIDATION.md | D414ED0A3543AF70C203D30372AD358F29A2E5ACF346BDC5958CCD640E4D6988 |
| docs/p12/P12_8_4_SCALE_C_LOAD_PERFORMANCE_RESOURCE_ENVELOPE.md | F64D4354BEB622404380FCDE3BEB9B5CF4AD4FE2E059E666B8B0D3D7EAD812EA |

HEAD/freeze/branch remain the baseline. Tracked and staged diffs are empty. Scans found
zero generated native executable/DLL/object/PDB/pyc files, no bin/obj/__pycache__
directories and zero build entries. Frozen predecessor files and the P12.5 acceptance
JSON are untouched. No commit/tag/push occurred. Exactly ten untracked candidate paths:

```text
?? apexforge/p12_8_2_resource_observability_ownership_test.py
?? apexforge/p12_8_3_execution_continuity_resource_pressure_test.py
?? apexforge/p12_8_4_scale_c_load_performance_resource_test.py
?? apexforge/p12_8_5_security_resource_lifetime_test.py
?? apexforge/tooling/resource_observability.py
?? docs/p12/P12_8_1_BACKEND_CLOSURE_CAPABILITY_CENSUS.md
?? docs/p12/P12_8_2_RESOURCE_OBSERVABILITY_AND_OWNERSHIP_FOUNDATION.md
?? docs/p12/P12_8_3_EXECUTION_CONTINUITY_RESOURCE_PRESSURE_VALIDATION.md
?? docs/p12/P12_8_4_SCALE_C_LOAD_PERFORMANCE_RESOURCE_ENVELOPE.md
?? docs/p12/P12_8_5_SECURITY_RESOURCE_LIFETIME_CLOSURE.md
```

## Evidence-supported markers

These apply only to the reviewed/tested contracts and lifetime surfaces, including the
authority/profile/trusted-root qualifications above. "Unexpectedly=False" records no
observed unauthorized persistence in these scopes, not universal revocation enforcement.

```text
P12_8_SECURITY_RESOURCE_LIFETIME=PASS
P12_8_ARTIFACT_SUBSTITUTION_REJECTED=True
P12_8_PROVENANCE_SUBSTITUTION_REJECTED=True
P12_8_CROSS_EXECUTION_REBINDING_REJECTED=True
P12_8_STALE_RESOURCE_REUSE_REJECTED=True
P12_8_STALE_METADATA_REJECTED=True
P12_8_STALE_TRACE_PROVENANCE_REJECTED=True
P12_8_AUTHORITY_PRINCIPAL_BINDING_PRESERVED=True
P12_8_CLEANUP_OWNERSHIP_CONFINED=True
P12_8_OBSERVER_PATH_ESCAPE_REJECTED=True
P12_8_NATIVE_SECURITY_FALLBACK_USED=False
P12_8_RESOURCE_LIFETIME_EXCEEDS_AUTHORITY_UNEXPECTEDLY=False
P12_8_SECURITY_SEMANTICS_UNCHANGED=True
P12_8_NATIVE_PROFILE_EXPANDED=False
P12_8_P13_DEBUGGER_SCOPE_ENTERED=False
P12_8_5_READY_FOR_REVIEW=True
P12_8_SECURITY_CACHE_REUSE_SURFACE=NONE_FOR_TESTED_PATH
```

Stop boundary: P12.8-5 candidate ready for human review. No next stage is started.
