"""Bounded in-process copying of supplied bytes; no target packaging or toolchain."""
from dataclasses import dataclass, field
from hashlib import sha256
import re
from tooling import release_architecture as release
from tooling.domain_platform import CanonicalModel, _json
from tooling.package_manifest import PackagePath, CanonicalReference

MAX_ITEMS = 1024
MAX_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
INPUT_ROLES = ("SOURCE_BYTES", "EXISTING_ARTIFACT", "SUPPLIED_DATA")
OPERATIONS = ("COPY_BYTES",)


class ReleaseBuildError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code):
    if not ok:
        raise ReleaseBuildError(code)


def digest(data):
    require(type(data) is bytes and len(data) <= MAX_BYTES, "RELEASE_BUILD_BYTES_INVALID")
    return sha256(data).hexdigest().upper()


def check_digest(data, declared, code):
    require(type(declared) is str and re.fullmatch(r"[0-9A-F]{64}", declared) is not None, code)
    require(digest(data) == declared, code)


def name(value, code):
    require(type(value) is str and len(value) <= 128 and
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value, re.ASCII) is not None, code)


def ordered(values, cls, code):
    require(type(values) is tuple and len(values) <= MAX_ITEMS and all(type(v) is cls for v in values), code)
    keys = tuple(_json(v.record()) for v in values)
    require(len(set(keys)) == len(keys), code)
    return tuple(v for _,v in sorted(zip(keys,values),key=lambda pair:pair[0]))


@dataclass(frozen=True)
class ReleaseBuildInput(CanonicalModel):
    release: release.ReleaseIdentity
    identity: PackagePath
    role: str
    data: bytes = field(repr=False)
    declared_digest: str
    source: CanonicalReference | None = None
    provenance: tuple = ()
    DOMAIN = "apexforge.release-build-input/v1"

    def __post_init__(self):
        require(type(self.release) is release.ReleaseIdentity and type(self.identity) is PackagePath,
                "RELEASE_BUILD_INPUT_INVALID")
        require(type(self.role) is str and self.role in INPUT_ROLES, "RELEASE_BUILD_INPUT_INVALID")
        check_digest(self.data,self.declared_digest,"RELEASE_BUILD_INPUT_DIGEST_MISMATCH")
        require(self.source is None or type(self.source) is CanonicalReference, "RELEASE_BUILD_INPUT_INVALID")
        object.__setattr__(self,"provenance",ordered(self.provenance,CanonicalReference,"RELEASE_BUILD_PROVENANCE_INVALID"))

    def record(self):
        return {"release":self.release.record(),"logical_input":self.identity.value,"role":self.role,
                "digest":self.declared_digest,"length":len(self.data),
                "source":None if self.source is None else self.source.record(),
                "provenance":[p.record() for p in self.provenance],"evidence":"CALLER_SUPPLIED_BYTES"}


@dataclass(frozen=True)
class ReleaseBuildEnvironment(CanonicalModel):
    identifier: str
    owner: str
    byte_policy: str = "OPAQUE_EXACT_BYTES"
    metadata_encoding: str = "UTF8_CANONICAL_JSON"
    line_endings: str = "PRESERVE_SUPPLIED_BYTES"
    locale: str = "INDEPENDENT"
    DOMAIN = "apexforge.release-build-environment/v1"

    def __post_init__(self):
        name(self.identifier,"RELEASE_BUILD_ENVIRONMENT_INVALID")
        name(self.owner,"RELEASE_BUILD_ENVIRONMENT_INVALID")
        require((self.byte_policy,self.metadata_encoding,self.line_endings,self.locale) ==
                ("OPAQUE_EXACT_BYTES","UTF8_CANONICAL_JSON","PRESERVE_SUPPLIED_BYTES","INDEPENDENT"),
                "RELEASE_BUILD_ENVIRONMENT_INVALID")

    def record(self):
        return {"id":self.identifier,"owner":self.owner,"byte_policy":self.byte_policy,
                "metadata_encoding":self.metadata_encoding,"line_endings":self.line_endings,
                "locale":self.locale,"host_state":"NOT_INSPECTED"}


@dataclass(frozen=True)
class ReleaseBuildOutputSlot(CanonicalModel):
    descriptor: release.ReleaseArtifactDescriptor
    input_identity: PackagePath
    DOMAIN = "apexforge.release-build-output-slot/v1"

    def __post_init__(self):
        require(type(self.descriptor) is release.ReleaseArtifactDescriptor and type(self.input_identity) is PackagePath,
                "RELEASE_BUILD_OUTPUT_INVALID")
        require(self.descriptor.availability != "UNAVAILABLE", "RELEASE_BUILD_OUTPUT_UNAVAILABLE")

    def record(self):
        return {"descriptor":self.descriptor.record(),"input":self.input_identity.value,
                "bytes":"NOT_ASSEMBLED_BY_SLOT_CONSTRUCTION"}


@dataclass(frozen=True)
class ReleaseBuildRecipe(CanonicalModel):
    identifier: str
    release: release.ReleaseIdentity
    operation: str
    environment: ReleaseBuildEnvironment
    inputs: tuple
    outputs: tuple
    provenance: tuple = ()
    references: tuple = ()
    _fingerprint: str = field(init=False,repr=False)
    DOMAIN = "apexforge.release-build-recipe/v1"

    def __post_init__(self):
        name(self.identifier,"RELEASE_BUILD_RECIPE_INVALID")
        require(type(self.release) is release.ReleaseIdentity, "RELEASE_BUILD_RECIPE_INVALID")
        require(type(self.operation) is str and self.operation in OPERATIONS, "RELEASE_BUILD_OPERATION_UNSUPPORTED")
        require(type(self.environment) is ReleaseBuildEnvironment, "RELEASE_BUILD_ENVIRONMENT_INVALID")
        inputs=ordered(self.inputs,ReleaseBuildInput,"RELEASE_BUILD_INPUT_INVALID")
        outputs=ordered(self.outputs,ReleaseBuildOutputSlot,"RELEASE_BUILD_OUTPUT_INVALID")
        require(bool(inputs) and bool(outputs), "RELEASE_BUILD_RECIPE_INVALID")
        require(sum(len(i.data) for i in inputs) <= MAX_TOTAL_BYTES, "RELEASE_BUILD_SIZE_LIMIT")
        require(all(i.release == self.release for i in inputs), "RELEASE_BUILD_RELEASE_MISMATCH")
        require(len({i.identity for i in inputs}) == len(inputs), "RELEASE_BUILD_INPUT_CONFLICT")
        require(all(o.descriptor.release == self.release for o in outputs), "RELEASE_BUILD_RELEASE_MISMATCH")
        require(len({o.descriptor.identity for o in outputs}) == len(outputs), "RELEASE_BUILD_OUTPUT_CONFLICT")
        require(all(o.input_identity in {i.identity for i in inputs} for o in outputs), "RELEASE_BUILD_INPUT_MISSING")
        require(sum(len(next(i.data for i in inputs if i.identity == o.input_identity)) for o in outputs)
                <= MAX_TOTAL_BYTES, "RELEASE_BUILD_SIZE_LIMIT")
        require(len({(o.descriptor.target,o.descriptor.filename) for o in outputs}) == len(outputs),
                "RELEASE_BUILD_OUTPUT_CONFLICT")
        object.__setattr__(self,"inputs",inputs)
        object.__setattr__(self,"outputs",outputs)
        object.__setattr__(self,"provenance",ordered(self.provenance,CanonicalReference,"RELEASE_BUILD_PROVENANCE_INVALID"))
        object.__setattr__(self,"references",ordered(self.references,CanonicalReference,"RELEASE_BUILD_REFERENCE_INVALID"))
        object.__setattr__(self,"_fingerprint",CanonicalModel.fingerprint(self))

    def record(self):
        return {"id":self.identifier,"schema":self.DOMAIN,"release":self.release.record(),"operation":self.operation,
                "environment":self.environment.record(),"inputs":[i.record() for i in self.inputs],
                "expected_outputs":[o.record() for o in self.outputs],
                "provenance":[p.record() for p in self.provenance],"references":[p.record() for p in self.references],
                "execution_authority":False,"target_packaging_validation":"NOT_PERFORMED"}

    def fingerprint(self):
        return self._fingerprint


@dataclass(frozen=True)
class ReleaseBuildArtifact(CanonicalModel):
    recipe: ReleaseBuildRecipe
    identity: release.ReleaseArtifactIdentity
    data: bytes = field(repr=False)
    declared_digest: str
    _slot: ReleaseBuildOutputSlot = field(init=False,repr=False)
    DOMAIN = "apexforge.release-build-artifact/v1"

    def __post_init__(self):
        require(type(self.recipe) is ReleaseBuildRecipe and type(self.identity) is release.ReleaseArtifactIdentity,
                "RELEASE_BUILD_OUTPUT_INVALID")
        check_digest(self.data,self.declared_digest,"RELEASE_BUILD_OUTPUT_DIGEST_MISMATCH")
        slot=next((o for o in self.recipe.outputs if o.descriptor.identity == self.identity),None)
        require(slot is not None,"RELEASE_BUILD_OUTPUT_UNEXPECTED")
        supplied=next(i for i in self.recipe.inputs if i.identity == slot.input_identity)
        require(self.data == supplied.data,"RELEASE_BUILD_OUTPUT_CONTENT_MISMATCH")
        object.__setattr__(self,"_slot",slot)

    def record(self):
        return {"recipe":self.recipe.fingerprint(),"artifact":self.identity.record(),
                "descriptor":self._slot.descriptor.record(),"length":len(self.data),"digest":self.declared_digest,
                "input":self._slot.input_identity.value,
                "provenance":{"recipe":[p.record() for p in self.recipe.provenance],
                              "input":next(i.record() for i in self.recipe.inputs if i.identity == self._slot.input_identity)},
                "packaging_validation":"NOT_PERFORMED","grants_authority":False,"grants_compatibility":False,
                "authentication":"CRYPTO_PROVIDER_UNAVAILABLE","semantic_authority":"CANONICAL_AIR"}


@dataclass(frozen=True)
class ReleaseArtifactSet(CanonicalModel):
    release: release.ReleaseIdentity
    recipes: tuple
    artifacts: tuple
    provenance: tuple = ()
    DOMAIN = "apexforge.release-build-artifact-set/v1"

    def __post_init__(self):
        require(type(self.release) is release.ReleaseIdentity,"RELEASE_BUILD_RELEASE_MISMATCH")
        require(type(self.recipes) is tuple and 0 < len(self.recipes) <= MAX_ITEMS and
                all(type(r) is ReleaseBuildRecipe for r in self.recipes),"RELEASE_BUILD_RECIPE_INVALID")
        require(len({r.fingerprint() for r in self.recipes}) == len(self.recipes),"RELEASE_BUILD_RECIPE_CONFLICT")
        require(all(r.release == self.release for r in self.recipes),"RELEASE_BUILD_RELEASE_MISMATCH")
        recipes=tuple(sorted(self.recipes,key=lambda r:r.fingerprint()))
        require(sum(len(r.inputs) for r in recipes) <= MAX_ITEMS,"RELEASE_BUILD_SIZE_LIMIT")
        require(sum(len(i.data) for r in recipes for i in r.inputs) <= MAX_TOTAL_BYTES,"RELEASE_BUILD_SIZE_LIMIT")
        require(sum(len(next(i.data for i in r.inputs if i.identity == o.input_identity))
                    for r in recipes for o in r.outputs) <= MAX_TOTAL_BYTES,"RELEASE_BUILD_SIZE_LIMIT")
        slots=tuple(o for r in recipes for o in r.outputs)
        require(len(slots) <= MAX_ITEMS,"RELEASE_BUILD_SIZE_LIMIT")
        require(len({o.descriptor.identity for o in slots}) == len(slots),"RELEASE_BUILD_OUTPUT_CONFLICT")
        require(len({(o.descriptor.target,o.descriptor.filename) for o in slots}) == len(slots),
                "RELEASE_BUILD_OUTPUT_CONFLICT")
        require(type(self.artifacts) is tuple and len(self.artifacts) <= MAX_ITEMS and
                all(type(a) is ReleaseBuildArtifact for a in self.artifacts),"RELEASE_BUILD_OUTPUT_INVALID")
        require(len({a.identity for a in self.artifacts}) == len(self.artifacts),"RELEASE_BUILD_OUTPUT_CONFLICT")
        require(all(a.recipe in recipes for a in self.artifacts),"RELEASE_BUILD_RECIPE_MISMATCH")
        require(sum(len(a.data) for a in self.artifacts) <= MAX_TOTAL_BYTES,"RELEASE_BUILD_SIZE_LIMIT")
        object.__setattr__(self,"recipes",recipes)
        object.__setattr__(self,"artifacts",tuple(sorted(self.artifacts,key=lambda a:a.identity.identifier)))
        object.__setattr__(self,"provenance",ordered(self.provenance,CanonicalReference,"RELEASE_BUILD_PROVENANCE_INVALID"))

    @property
    def missing(self):
        expected={o.descriptor.identity for r in self.recipes for o in r.outputs}
        return tuple(sorted((i.identifier for i in expected-{a.identity for a in self.artifacts})))

    @property
    def status(self):
        return "INCOMPLETE" if self.missing else "BUILT"

    def record(self):
        return {"release":self.release.record(),"recipes":[r.fingerprint() for r in self.recipes],
                "artifacts":[a.record() for a in self.artifacts],"status":self.status,
                "findings":[{"code":"RELEASE_BUILD_OUTPUT_MISSING","artifact":i} for i in self.missing],
                "provenance":[p.record() for p in self.provenance],"published":False,"installed":False,
                "grants_trust":False,"final_release_manifest":False}


def assemble(recipe):
    require(type(recipe) is ReleaseBuildRecipe,"RELEASE_BUILD_RECIPE_INVALID")
    inputs={i.identity:i for i in recipe.inputs}
    artifacts=tuple(ReleaseBuildArtifact(recipe,o.descriptor.identity,inputs[o.input_identity].data,
                        inputs[o.input_identity].declared_digest) for o in recipe.outputs)
    return ReleaseArtifactSet(recipe.release,(recipe,),artifacts,recipe.provenance)


@dataclass(frozen=True)
class BuildReproducibilityEvidence(CanonicalModel):
    first: ReleaseArtifactSet
    second: ReleaseArtifactSet
    DOMAIN = "apexforge.release-build-reproducibility/v1"

    def __post_init__(self):
        require(type(self.first) is ReleaseArtifactSet and type(self.second) is ReleaseArtifactSet,
                "RELEASE_BUILD_REPRODUCIBILITY_INVALID")

    @property
    def findings(self):
        codes=set()
        if self.first.release != self.second.release:
            codes.add("RELEASE_BUILD_RELEASE_MISMATCH")
        if tuple(r.fingerprint() for r in self.first.recipes) != tuple(r.fingerprint() for r in self.second.recipes):
            codes.add("RELEASE_BUILD_RECIPE_MISMATCH")
        if self.first.status != "BUILT" or self.second.status != "BUILT":
            codes.add("RELEASE_BUILD_OUTPUT_MISSING")
        if self.first.canonical_json() != self.second.canonical_json():
            codes.add("RELEASE_BUILD_REPRODUCIBILITY_MISMATCH")
        return tuple(sorted(codes))

    @property
    def status(self):
        return "MISMATCH" if self.findings else "PASS"

    def record(self):
        return {"first":self.first.fingerprint(),"second":self.second.fingerprint(),"status":self.status,
                "findings":list(self.findings),"comparison":"SUPPLIED_RECORDS_NOT_EXECUTION_AUTHENTICATION",
                "authenticity_proven":False,"trust_granted":False,"signed":False}
