# P16.3 Reproducible Release Build & Artifact Assembly

## Frozen baseline and incoming hashes

Branch: `p16-1-release-baseline`.
HEAD / frozen P15 commit: `c9c5ca186c9d942ce336ac1ebfe1287b16953200`.
Predecessor: `afp-p15.14-freeze`.
Annotated tag object: `d7761c04e4422bfb91d9582275a60912874678f4`.
Peeled target and P15 branch: `c9c5ca186c9d942ce336ac1ebfe1287b16953200`.

Before implementation all refs matched; the exact six reviewed P16 paths were
untracked; tracked/staged diffs empty; no ignored/generated residue. SHA-256 census:

```text
P16_BASELINE=P15_14_FREEZE
P16_3_INCOMING_CANDIDATES=6
P15_REOPENED=False
77C69F98C842CAA3073E0D3CA36C2C042ED1FC97F90BC3A721288B4BB61D72F8  apexforge/p16_1_release_architecture_contract_test.py
72F967A103FA768DA4FC6202A491032B700C0E8A7AF392CFA323C9834BAC0F3B  apexforge/p16_2_release_versioning_compatibility_test.py
5BF82BF285BE9C353D2F853432B3D4059702019CC1FE8E0740EBEC6A23F8F82A  apexforge/tooling/release_architecture.py
0B7F1BF949A1803637F826F4F31FC7F68D384CFF6C2CD3EEE6C9D4024FED52CB  apexforge/tooling/release_versioning.py
1CCFB01BA43A4A178DEF2BA99FE10176F07FB9021C1D91F45F60B90600BA16A1  docs/p16/P16_1_RELEASE_ARCHITECTURE.md
F00CB44333888CF58575C5715441B53D9488CDF802F839B26B04C09D29EF647D  docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
```

## Build-owner census

| Existing functionality | Classification | P16.3 use / later owner |
| --- | --- | --- |
| pyproject.toml, setuptools metadata, P10 scaffold/project packaging | REFERENCE_ONLY; DEFER_TO_P16_5 | Python >=3.9, version 10.1.3 unchanged; no Python distribution builder |
| P10 vscode_package official vsce runner/archive/installed-copy audit | FROZEN_BUILD_OWNER; REFERENCE_ONLY; DEFER_TO_P16_6 | Preserve existing archive timestamp/source-payload distinction; do not invoke subprocess/Node/VSCE |
| Visual Studio packaging/integration source/VSIX/install-copy audit | FROZEN_BUILD_OWNER; REFERENCE_ONLY; DEFER_TO_P16_7 | Existing deterministic assembly/payload/architecture checks remain owner-specific |
| P12 native_execution, COFF/DLL reproducibility policy and tests | FROZEN_BUILD_OWNER; REFERENCE_ONLY; DEFER_TO_P16_8 | /Brepro, exact whole-image digest, explicit toolchain inputs; temp paths not release semantic identity; no compiler/linker/dispatch invocation |
| P14 ArtifactPayload/ArtifactDescriptor and package manifest content identity | FROZEN_PACKAGE_CONTRACT; REFERENCE_ONLY | Supplied digest/byte equality precedent; no replacement package identity |
| P11 build-artifact canonical JSON/fingerprint integrity | FROZEN_BUILD_OWNER; REFERENCE_ONLY | AIR build envelope remains separate; no new top-level artifact interchange/archive format |
| P15.1 canonical utility; P14 PackagePath/CanonicalReference | REUSE | Existing deterministic JSON/domain fingerprint and logical addressing/lineage |
| P16.1 release/target/artifact descriptor/matrix | REUSE | Exact source baseline, release, target and output declaration binding |
| P16.2 mapping/policy | REFERENCE_ONLY | Optional canonical references; build success grants no compatibility |
| Supplied input bytes -> COPY_BYTES -> artifact set | GENERIC_RELEASE_BUILD_EXTENSION_POINT | Sole new generic operation; target-neutral |
| Final release manifest/checksum/provenance bundle | DEFER_TO_P16_4 | Raw build digest evidence only, no final bundle policy |

Discovery's guessed artifact_emission.py was absent; repository search found the
native_execution owner and the actual frozen COFF/DLL policy/test contracts.
No predecessor defect or patch resulted. Native support stays the frozen
apexforge.native.win-x64.i64-literal-state-set/v1 profile.

.gitattributes requires LF only for spec/conformance/**. Other reviewed source
bytes may contain CRLF. P16.3 neither changes Git settings nor applies a host text
conversion. VSIX and native timestamp/toolchain rules remain with their owners.

## Generic byte-oriented contract

ReleaseBuildInput is immutable: exact ReleaseIdentity, validated logical
PackagePath, bounded role SOURCE_BYTES/EXISTING_ARTIFACT/SUPPLIED_DATA, bytes,
caller-declared SHA-256, optional canonical source reference and provenance.
Only exact immutable bytes are accepted. Declared digests are uppercase SHA-256;
mismatch fails with RELEASE_BUILD_INPUT_DIGEST_MISMATCH. A mismatch is never
replaced with a newly computed digest. Canonical input identity binds digest and
length, release, role, logical identity and evidence, not a host file handle.

ReleaseBuildEnvironment is passive: caller identifier/tool owner plus fixed
OPAQUE_EXACT_BYTES, UTF8_CANONICAL_JSON, PRESERVE_SUPPLIED_BYTES and INDEPENDENT
locale profile. It never inspects or attests to a real toolchain installation.
Changing declared identity/owner changes the recipe. Host default encodings,
newlines or locale settings are unsupported.

ReleaseBuildOutputSlot binds an exact existing P16.1 descriptor and explicit
input identity. It describes expected output only. UNAVAILABLE descriptors are
rejected, not silently promoted. Constructing a slot or recipe produces no bytes.

ReleaseBuildRecipe binds caller identity, exact release, COPY_BYTES operation,
explicit environment, exact unordered inputs/expected slots, provenance and
optional canonical references. Duplicate input/output identities, dangling inputs,
duplicate target/filename and mixed-release evidence fail closed. COPY_BYTES is
the only justified operation; no shell text, callback, script, archive format or
target-specific build recipe is accepted. It retains even explicitly supplied
unused context inputs, binding them into recipe identity without discovering extras.

Recipe inputs and outputs are canonically ordered. Its fingerprint is derived once
after complete immutable validation, using the existing canonical utility and its
own apexforge.release-build-recipe/v1 domain. No object repr/address or host state
enters the canonical form. The frozen snapshot is equivalent to recomputation
from the immutable record.

## Deterministic assembly and output identity

assemble(recipe) performs only in-process opaque byte copying to each declared
output. It returns a ReleaseArtifactSet containing ReleaseBuildArtifact records.
An artifact binds its exact recipe and output identity/descriptor, exact bytes,
verified digest/length, source input identity and provenance. It must match the
recipe's COPY_BYTES input exactly; wrong output bytes or digest fail closed.
Changing bytes, descriptor/release/role, recipe or environment changes the
appropriate fingerprints. Logical artifact name alone is not content identity.

No archive/PE/VSIX/wheel validity is inferred from a copied byte sequence or filename.
P16.1 descriptors remain declarations; an enclosing generic build artifact adds
actual copy evidence while reporting packaging_validation=NOT_PERFORMED.
Tests exercise all four P16.1 targets with the same generic copy, never certifying
target packaging. No final artifact format or top-level wire format is invented.

ReleaseArtifactSet binds an exact release, canonical recipe fingerprint set,
ordered exact artifacts and provenance. Duplicate logical output identity is
rejected across recipes or artifacts even when identical, and conflicting content
never wins. Output names are unique per target. Unknown recipes fail closed.
Missing expected outputs produce INCOMPLETE and structured
RELEASE_BUILD_OUTPUT_MISSING findings. Explicit empty caller bytes remain valid;
missing evidence never becomes an empty artifact. BUILT means the supplied generic
copy output set is complete, not target-package readiness, installation or release.

## Size bounds and deterministic paths/bytes

At most 1,024 inputs/outputs/references per bounded collection; at most 1 MiB per
input/artifact; at most 8 MiB total recipe input/output bytes. Artifact sets also
bound aggregate input count, expected output count, input/expected-output/actual
output bytes, and recipe count. Algorithms use deterministic iterative processing,
with no recursion-depth dependence or giant test files.

Canonical metadata uses explicit UTF-8 JSON with stable key/collection ordering.
No wall clock, timestamp, hostname, username, PID, cwd, temp path, shell profile,
environment-variable read, filesystem enumeration or implicit locale enters it.
Logical addresses reject absolute/traversal/drive paths under frozen PackagePath.

Opaque payload bytes are preserved exactly. Independently supplied identical CRLF
inputs reproduce; deliberately different LF bytes are different content and recipes.
No host line-ending conversion occurs. P16.3 does not inject host paths into
metadata or output bytes; it does not inspect or scrub arbitrary caller payloads.
A caller could supply bytes containing a literal path—this is opaque content,
not host discovery and not a claim that supplied data is sanitized or private.

## Reproducibility, provenance and limits

BuildReproducibilityEvidence compares two supplied artifact sets. PASS requires
exact release and recipe identities, complete expected outputs, exact output set,
lengths/digests and canonical artifact/set metadata. Missing output and release/
recipe/content/metadata differences retain deterministic sorted reason codes.
Invalid output evidence is rejected during artifact construction rather than
accepted as a successfully built artifact.

Independent construction tests create separate inputs, byte objects, recipes and
assembled outputs. The 1,000-input/1,000-output case independently constructs both
recipes, reverses insertion order on one side, and checks identical bytes/set
fingerprints/reproducibility. This is determinism evidence, not a benchmark.
Comparison of supplied immutable records is not proof of separate machine builds,
an authenticated build history or general external-toolchain reproducibility.

Lineage remains:
P15 freeze -> exact P16 release -> recipe -> exact input/source/provenance ->
output descriptor/artifact -> artifact set. P14 package/content references in the
P16.1 descriptor are preserved by inclusion, not replaced. P16.2 mapping references
can be supplied explicitly; they do not make building a compatibility determination.
No real-world authorship/authentication is inferred from provenance.

## Security and owning-layer boundaries

Production imports only dataclasses/hashlib/re, P16.1, existing canonical helpers
and frozen logical-path/reference carriers. Static import/class/call audit plus
dynamic traps cover subprocess, process creation, socket/hostname, file IO/walk,
cwd/PID/environment/time reads, eval/exec. Supplied script/pickle-looking binary
bytes remain opaque; no loading, import, interpretation or execution.

No RuntimeEngine, authority grant, compiler/linker, python -m build, dotnet,
MSBuild, npm/npx/vsce, OpenSCAD, package manager, download/restore, credential lookup,
Git invocation, signing, upload, Marketplace, GitHub release, installation or CI.
No P16.4 final release manifest/checksum/provenance bundle.
No P16.5/P16.6/P16.7/P16.8 target-specific packager. Their existing owners remain
references. No P16.1/P16.2 or frozen file is changed.

SHA-256 here verifies actual supplied bytes and records build evidence. It is not
a signature, trust decision, authentication, permission, compatibility proof or
semantic authority. CRYPTO_PROVIDER_UNAVAILABLE remains.

```text
BUILD_PLAN != EXECUTION_AUTHORITY
BUILD_RECIPE != PACKAGE_IDENTITY
BUILD_OUTPUT != CANONICAL_AIR
REPRODUCIBLE_BUILD != TRUSTED_BUILD
REPRODUCIBLE_BUILD != SIGNED_BUILD
REPRODUCIBLE_BUILD != PUBLISHED_RELEASE
ARTIFACT_DIGEST != AUTHENTICATION
BUILD_SUCCESS != COMPATIBILITY_PROOF
ASSEMBLED_ARTIFACT != INSTALLED_ARTIFACT
LOCAL_BUILD != RELEASE_PUBLICATION
VALID_BUILD_PLAN != BUILT_ARTIFACT
BUILD_PROVENANCE != AUTHENTICATION
CANONICAL_SEMANTIC_AUTHORITY=CANONICAL_AIR
CRYPTO_PROVIDER_UNAVAILABLE
```

## Validation and Patch Matrix

Final focused P16.3: 31/31 PASS.
Unchanged P16.2: 31/31 PASS; unchanged P16.1: 25/25 PASS.
Final P16 aggregate: 87/87 PASS.
Frozen P14: 330/330 PASS; native: 7/7 PASS.
Authority consolidation: canonical identities, exact grant, wrong
principal/capability/resource denial, authorized RuntimeEngine execution and
transactional denied execution PASS. Runtime execution belongs only to the unchanged
frozen smoke fixture, not P16.3 production.
Frozen P15: 428/428 PASS.
Final preservation audit: branch/HEAD/P15 branch/tag object/peeled target remain
exact. All six incoming hashes match the census; no P16.1/P16.2 or frozen
P15/P14/earlier path changed. Exactly nine intended candidates, tracked/staged
diffs empty, no generated residue. No staging, commit, tag, push, final manifest,
checksum bundle, target packaging, publication, installation, signing or P16.4
implementation occurred. Review remains with the project owner.

Exact Git status:

```text
?? apexforge/p16_1_release_architecture_contract_test.py
?? apexforge/p16_2_release_versioning_compatibility_test.py
?? apexforge/p16_3_reproducible_release_build_test.py
?? apexforge/tooling/release_architecture.py
?? apexforge/tooling/release_build.py
?? apexforge/tooling/release_versioning.py
?? docs/p16/P16_1_RELEASE_ARCHITECTURE.md
?? docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
?? docs/p16/P16_3_REPRODUCIBLE_RELEASE_BUILD.md
```

Commands use python -X utf8 -B with:
- apexforge/p16_3_reproducible_release_build_test.py
- apexforge/p16_2_release_versioning_compatibility_test.py
- apexforge/p16_1_release_architecture_contract_test.py
- -m unittest discover -s apexforge -p p16_*_test.py
- -m unittest discover -s apexforge -p p15_*_test.py
- -m unittest discover -s apexforge -p p14_*_test.py
- apexforge/p12_5_native_profile_contract_test.py
- apexforge/authority_consolidation_smoke_test.py

No focused test failure occurred. Final audit classified
RELEASE_BUILD_ARTIFACT_SET_GAP: per-recipe bounds alone needed aggregate input-count
and expected-output-byte bounds for multiple recipes. Owning P16.3; patch surface
new module/test only. Added those bounds and explicit multi-recipe rejection
coverage; focused 31/31 passed afterward. No predecessor repair or assertion
weakening; no unresolved owning-layer defect.

FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES ->
PATCH SURFACE -> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.

## Evidence-supported markers

The path/time/line-ending markers describe P16.3-owned metadata and absence of
host-derived injection/conversion. They do not certify or sanitize opaque caller
payload contents, as explained above.

```text
P16_BASELINE=P15_14_FREEZE
P15_REOPENED=False
P16_3_INCOMING_CANDIDATES=6
P16_3_BUILD_INPUT_CALLER_SUPPLIED=True
P16_3_INPUT_DIGEST_MISMATCH_FAILS_CLOSED=True
P16_3_BUILD_RECIPE_DETERMINISTIC=True
P16_3_BUILD_ENVIRONMENT_EXPLICIT=True
P16_3_HOST_STATE_NOT_CANONICAL_IDENTITY=True
P16_3_OUTPUT_EXACT_RECIPE_BOUND=True
P16_3_OUTPUT_CONTENT_IDENTITY_EXACT=True
P16_3_REPRODUCIBILITY_USES_INDEPENDENT_CONSTRUCTION=True
P16_3_CONFLICTING_ARTIFACT_DUPLICATE_FAILS_CLOSED=True
P16_3_ARTIFACT_SET_ORDER_DETERMINISTIC=True
P16_3_MISSING_OUTPUT_NOT_EMPTY_ARTIFACT=True
P16_3_BUILD_PROVENANCE_EXPLICIT=True
P16_3_GENERIC_ASSEMBLY_DETERMINISTIC=True
P16_3_REDEFINES_CORE_SEMANTICS=False
P16_3_TARGET_SPECIFIC_PACKAGING_IMPLEMENTED=False
P16_3_ARBITRARY_BUILD_COMMANDS_SUPPORTED=False
P16_3_WALL_CLOCK_IN_ARTIFACT_IDENTITY=False
P16_3_ABSOLUTE_PATHS_IN_CANONICAL_OUTPUT=False
P16_3_HOST_LINE_ENDING_CONVERSION_CANONICAL=False
P16_3_REPRODUCIBILITY_PROVES_AUTHENTICITY=False
P16_3_REDEFINES_RELEASE_ARCHITECTURE=False
P16_3_BUILD_SUCCESS_GRANTS_COMPATIBILITY=False
P16_3_REDEFINES_VERSION_POLICY=False
P16_3_FINAL_RELEASE_MANIFEST_IMPLEMENTED=False
P16_3_FINAL_CHECKSUM_BUNDLE_IMPLEMENTED=False
P16_3_PYTHON_DISTRIBUTION_BUILD_IMPLEMENTED=False
P16_3_VSCODE_RELEASE_PACKAGE_IMPLEMENTED=False
P16_3_VISUAL_STUDIO_RELEASE_PACKAGE_IMPLEMENTED=False
P16_3_NATIVE_RELEASE_PACKAGE_IMPLEMENTED=False
P16_3_EXTERNAL_TOOLCHAIN_EXECUTION=False
P16_3_HOST_COMMAND_EXECUTION=False
P16_3_FILESYSTEM_DISCOVERY=False
P16_3_NETWORK_ACCESS=False
P16_3_CREDENTIAL_ACQUISITION=False
P16_3_PUBLICATION_PERFORMED=False
P16_3_INSTALLATION_PERFORMED=False
P16_3_ARTIFACT_SIGNING_IMPLEMENTED=False
P16_3_CRYPTO_TRUST_FABRICATED=False
P16_3_BUILD_GRANTS_AUTHORITY=False
P16_3_BUILD_INPUT_BYTES_EXECUTED=False
CRYPTO_PROVIDER_UNAVAILABLE
P16_RELEASE_BUILD_MODEL=PASS
P16_RELEASE_BUILD_INPUT=PASS
P16_RELEASE_BUILD_RECIPE=PASS
P16_RELEASE_BUILD_ENVIRONMENT=PASS
P16_RELEASE_BUILD_OUTPUT=PASS
P16_RELEASE_ARTIFACT_SET=PASS
P16_RELEASE_BUILD_REPRODUCIBILITY=PASS
P16_RELEASE_BUILD_CONTENT_IDENTITY=PASS
P16_RELEASE_BUILD_PATH_DETERMINISM=PASS
P16_RELEASE_BUILD_METADATA_DETERMINISM=PASS
P16_RELEASE_BUILD_PROVENANCE=PASS
P16_RELEASE_BUILD_SECURITY_BOUNDARY=PASS
P16_RELEASE_BUILD_TOOLCHAIN_BOUNDARY=PASS
P16_2_REGRESSION=PASS
P16_1_REGRESSION=PASS
P16_AGGREGATE_REGRESSION=PASS
P15_AGGREGATE_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P16_AUTHORITY_COEXISTENCE=PASS
P15_FROZEN_PREDECESSOR_PRESERVED=True
PATCH_MATRIX=PASS
P16_3_READY_FOR_REVIEW=True
```
