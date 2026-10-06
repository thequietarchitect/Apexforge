"""P16.2 caller-supplied release compatibility policy; no upgrade execution."""
from dataclasses import dataclass
import re
from tooling import release_architecture as release
from tooling.domain_platform import CanonicalModel, _json
from tooling.package_manifest import CanonicalReference

STATUSES = ("COMPATIBLE", "MIGRATION_REQUIRED", "INCOMPATIBLE", "UNKNOWN")
DOMAINS = ("PYTHON_PACKAGE", "VSCODE_EXTENSION", "VISUAL_STUDIO_EXTENSION", "NATIVE_PROFILE",
           "PACKAGE_CONTRACT", "SCHEMA_CONTRACT", "LANGUAGE_SEMANTICS")
PRIMARY = (("python", "PYTHON_PACKAGE"), ("vscode", "VSCODE_EXTENSION"),
           ("visual-studio", "VISUAL_STUDIO_EXTENSION"), ("native-win-x64", "NATIVE_PROFILE"))
MAX_ITEMS = 4096


class ReleaseVersioningError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code):
    if not ok:
        raise ReleaseVersioningError(code)


def name(value, code):
    require(type(value) is str and len(value) <= 128 and
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value, re.ASCII) is not None, code)


def ordered(values, cls, code):
    require(type(values) is tuple and len(values) <= MAX_ITEMS and all(type(v) is cls for v in values), code)
    keys = tuple(_json(v.record()) for v in values)
    require(len(set(keys)) == len(keys), code)
    return tuple(v for _,v in sorted(zip(keys,values),key=lambda pair:pair[0]))


@dataclass(frozen=True)
class ReleaseVersionSurface(CanonicalModel):
    target: release.ReleaseTarget
    domain: str
    component: str
    DOMAIN = "apexforge.release-version-surface/v1"

    def __post_init__(self):
        require(type(self.target) is release.ReleaseTarget, "RELEASE_SURFACE_UNKNOWN")
        require(type(self.domain) is str and self.domain in DOMAINS, "RELEASE_VERSION_DOMAIN_INVALID")
        if self.domain in dict(PRIMARY).values():
            require((self.target.identifier,self.domain) in PRIMARY, "RELEASE_VERSION_DOMAIN_INVALID")
        name(self.component,"RELEASE_COMPONENT_INVALID")

    def record(self):
        return {"target":self.target.record(),"version_domain":self.domain,"component":self.component}


@dataclass(frozen=True)
class ReleaseSurfaceVersion(CanonicalModel):
    release: release.ReleaseIdentity
    surface: ReleaseVersionSurface
    version: str
    provenance: tuple = ()
    DOMAIN = "apexforge.release-surface-version/v1"

    def __post_init__(self):
        require(type(self.release) is release.ReleaseIdentity and type(self.surface) is ReleaseVersionSurface,
                "RELEASE_VERSION_MAPPING_INVALID")
        require(type(self.version) is str and len(self.version) <= 256 and
                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/+-]*",self.version,re.ASCII) is not None,
                "RELEASE_SURFACE_VERSION_INVALID")
        if self.surface.domain == "NATIVE_PROFILE":
            require(self.version == self.surface.target.native_profile, "RELEASE_NATIVE_PROFILE_CHANGED")
        object.__setattr__(self,"provenance",ordered(self.provenance,CanonicalReference,"RELEASE_PROVENANCE_INVALID"))

    def record(self):
        return {"release":self.release.record(),"surface":self.surface.record(),"declared_version":self.version,
                "provenance":[p.record() for p in self.provenance],"implies_compatibility":False}


@dataclass(frozen=True)
class ReleaseMigrationReference(CanonicalModel):
    identifier: str
    source: ReleaseSurfaceVersion
    target: ReleaseSurfaceVersion
    owner: str
    provenance: tuple = ()
    DOMAIN = "apexforge.release-migration-reference/v1"

    def __post_init__(self):
        name(self.identifier,"RELEASE_MIGRATION_REFERENCE_INVALID")
        name(self.owner,"RELEASE_MIGRATION_REFERENCE_INVALID")
        require(type(self.source) is ReleaseSurfaceVersion and type(self.target) is ReleaseSurfaceVersion
                and self.source.surface == self.target.surface, "RELEASE_MIGRATION_REFERENCE_INVALID")
        object.__setattr__(self,"provenance",ordered(self.provenance,CanonicalReference,"RELEASE_PROVENANCE_INVALID"))

    def record(self):
        return {"id":self.identifier,"source":self.source.record(),"target":self.target.record(),"owner":self.owner,
                "provenance":[p.record() for p in self.provenance],"executes_migration":False}


@dataclass(frozen=True)
class ReleaseCompatibilityDeclaration(CanonicalModel):
    source: ReleaseSurfaceVersion
    target: ReleaseSurfaceVersion
    status: str
    evidence: tuple = ()
    migration: ReleaseMigrationReference | None = None
    DOMAIN = "apexforge.release-compatibility-declaration/v1"

    def __post_init__(self):
        require(type(self.source) is ReleaseSurfaceVersion and type(self.target) is ReleaseSurfaceVersion
                and self.source.surface == self.target.surface, "RELEASE_COMPATIBILITY_BINDING_INVALID")
        require(type(self.status) is str and self.status in STATUSES, "RELEASE_COMPATIBILITY_STATUS_INVALID")
        object.__setattr__(self,"evidence",ordered(self.evidence,CanonicalReference,"RELEASE_COMPATIBILITY_EVIDENCE_INVALID"))
        require(self.status == "UNKNOWN" or bool(self.evidence), "RELEASE_COMPATIBILITY_EVIDENCE_MISSING")
        if self.status == "MIGRATION_REQUIRED":
            require(type(self.migration) is ReleaseMigrationReference and self.migration.source == self.source
                    and self.migration.target == self.target, "RELEASE_MIGRATION_REFERENCE_INVALID")
        else:
            require(self.migration is None, "RELEASE_MIGRATION_REFERENCE_INVALID")

    def record(self):
        return {"source":self.source.record(),"target":self.target.record(),"status":self.status,
                "evidence":[p.record() for p in self.evidence],
                "migration":None if self.migration is None else self.migration.record(),
                "evidence_class":"CALLER_SUPPLIED_POLICY_DECLARATION"}


@dataclass(frozen=True)
class ReleaseCompatibilityPolicy(CanonicalModel):
    identifier: str
    revision: str
    source: release.ReleaseIdentity
    target: release.ReleaseIdentity
    surfaces: tuple
    source_versions: tuple = ()
    target_versions: tuple = ()
    declarations: tuple = ()
    provenance: tuple = ()
    DOMAIN = "apexforge.release-compatibility-policy/v1"

    def __post_init__(self):
        name(self.identifier,"RELEASE_POLICY_INVALID")
        name(self.revision,"RELEASE_POLICY_INVALID")
        require(type(self.source) is release.ReleaseIdentity and type(self.target) is release.ReleaseIdentity,
                "RELEASE_COMPATIBILITY_BINDING_INVALID")
        object.__setattr__(self,"surfaces",ordered(self.surfaces,ReleaseVersionSurface,"RELEASE_SURFACE_UNKNOWN"))
        require(bool(self.surfaces),"RELEASE_SURFACE_UNKNOWN")
        for field,expected,code in (("source_versions",self.source,"RELEASE_SOURCE_MISMATCH"),
                                    ("target_versions",self.target,"RELEASE_TARGET_MISMATCH")):
            values=ordered(getattr(self,field),ReleaseSurfaceVersion,"RELEASE_VERSION_MAPPING_INVALID")
            require(all(v.release == expected and v.surface in self.surfaces for v in values),code)
            require(len({v.surface for v in values}) == len(values),"RELEASE_VERSION_MAPPING_CONFLICT")
            object.__setattr__(self,field,values)
        # Contradictory or duplicate declarations never select a permissive result.
        require(type(self.declarations) is tuple and len(self.declarations) <= MAX_ITEMS and
                all(type(d) is ReleaseCompatibilityDeclaration for d in self.declarations),"RELEASE_POLICY_INVALID")
        require(len({d.source.surface for d in self.declarations}) == len(self.declarations),
                "RELEASE_COMPATIBILITY_CONFLICT")
        for d in self.declarations:
            require(d.source in self.source_versions,"RELEASE_SOURCE_MISMATCH")
            require(d.target in self.target_versions,"RELEASE_TARGET_MISMATCH")
        object.__setattr__(self,"declarations",ordered(self.declarations,ReleaseCompatibilityDeclaration,"RELEASE_POLICY_INVALID"))
        object.__setattr__(self,"provenance",ordered(self.provenance,CanonicalReference,"RELEASE_PROVENANCE_INVALID"))

    def record(self):
        return {"id":self.identifier,"revision":self.revision,"source":self.source.record(),"target":self.target.record(),
                "required_surfaces":[s.record() for s in self.surfaces],
                "source_versions":[v.record() for v in self.source_versions],
                "target_versions":[v.record() for v in self.target_versions],
                "declarations":[d.record() for d in self.declarations],
                "provenance":[p.record() for p in self.provenance],
                "version_ordering":"NOT_DEFINED","package_solver_override":False,"grants_authority":False}


@dataclass(frozen=True)
class ReleaseCompatibilityFinding(CanonicalModel):
    policy: ReleaseCompatibilityPolicy
    surface: ReleaseVersionSurface
    DOMAIN = "apexforge.release-compatibility-finding/v1"

    def __post_init__(self):
        require(type(self.policy) is ReleaseCompatibilityPolicy and type(self.surface) is ReleaseVersionSurface
                and self.surface in self.policy.surfaces,"RELEASE_COMPATIBILITY_BINDING_INVALID")

    def _assessment(self):
        source=next((v for v in self.policy.source_versions if v.surface == self.surface),None)
        target=next((v for v in self.policy.target_versions if v.surface == self.surface),None)
        declaration=next((d for d in self.policy.declarations if d.source.surface == self.surface),None)
        if source is None or target is None:
            return source,target,None,"UNKNOWN","RELEASE_VERSION_MAPPING_MISSING"
        if declaration is None:
            return source,target,None,"UNKNOWN","RELEASE_COMPATIBILITY_UNKNOWN"
        codes={"COMPATIBLE":"RELEASE_COMPATIBILITY_EXPLICIT","MIGRATION_REQUIRED":"RELEASE_MIGRATION_REQUIRED",
               "INCOMPATIBLE":"RELEASE_INCOMPATIBLE","UNKNOWN":"RELEASE_COMPATIBILITY_UNKNOWN"}
        return source,target,declaration,declaration.status,codes[declaration.status]

    @property
    def status(self):
        return self._assessment()[3]

    def record(self):
        source,target,declaration,status,reason=self._assessment()
        return {"policy":self.policy.fingerprint(),"source_release":self.policy.source.fingerprint(),
                "target_release":self.policy.target.fingerprint(),"surface":self.surface.record(),
                "source_version":None if source is None else source.record(),
                "target_version":None if target is None else target.record(),"status":status,"reason":reason,
                "upgrade_status":{"COMPATIBLE":"DIRECT","MIGRATION_REQUIRED":"MIGRATION_REQUIRED",
                                  "INCOMPATIBLE":"UNSUPPORTED","UNKNOWN":"INCOMPLETE"}[status],
                "declaration":None if declaration is None else declaration.record(),
                "provenance":[p.record() for p in self.policy.provenance],
                "grants_authority":False,"grants_trust":False,"authentication":"CRYPTO_PROVIDER_UNAVAILABLE",
                "semantic_authority":"CANONICAL_AIR"}


def compatibility_matrix(policy):
    require(type(policy) is ReleaseCompatibilityPolicy,"RELEASE_POLICY_INVALID")
    return tuple(ReleaseCompatibilityFinding(policy,surface) for surface in policy.surfaces)


@dataclass(frozen=True)
class ReleaseUpgradeAssessment(CanonicalModel):
    policy: ReleaseCompatibilityPolicy
    findings: tuple
    DOMAIN = "apexforge.release-upgrade-assessment/v1"

    def __post_init__(self):
        require(type(self.policy) is ReleaseCompatibilityPolicy,"RELEASE_POLICY_INVALID")
        values=ordered(self.findings,ReleaseCompatibilityFinding,"RELEASE_UPGRADE_FINDINGS_INVALID")
        require(all(f.policy == self.policy for f in values),"RELEASE_POLICY_MISMATCH")
        require(len({f.surface for f in values}) == len(values),"RELEASE_UPGRADE_FINDINGS_INVALID")
        object.__setattr__(self,"findings",values)

    @property
    def status(self):
        statuses={f.status for f in self.findings}
        if "INCOMPATIBLE" in statuses:
            return "UNSUPPORTED"
        if {f.surface for f in self.findings} != set(self.policy.surfaces) or "UNKNOWN" in statuses:
            return "INCOMPLETE"
        if "MIGRATION_REQUIRED" in statuses:
            return "MIGRATION_REQUIRED"
        return "DIRECT"

    def record(self):
        return {"policy":self.policy.fingerprint(),"source":self.policy.source.fingerprint(),
                "target":self.policy.target.fingerprint(),"status":self.status,
                "findings":[f.record() for f in self.findings],
                "execution":"NOT_PERFORMED","installation":"NOT_PERFORMED","rollback":"NOT_PERFORMED",
                "migration":"NOT_PERFORMED","publication":"NOT_PERFORMED","grants_authority":False,
                "grants_trust":False,"package_dependencies":"REQUIRE_SEPARATE_FROZEN_OWNER_EVIDENCE"}
