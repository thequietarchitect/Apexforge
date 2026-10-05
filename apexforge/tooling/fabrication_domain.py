"""Offline declarative assembly plans; compatibility is not machine execution."""
from dataclasses import dataclass
from hashlib import sha256
import re

from tooling import domain_platform as sdk
from tooling.parametric_domain import ParametricScalar, ParametricVariant
from tooling.package_manifest import PackageManifest, ExactVersion, CanonicalReference

PROCESS = "apexforge.fabrication.assembly/v1"
PLATFORM = sdk.DomainPlatformIdentity("apexforge.fabrication", "fabrication")
OPERATIONS = ("fabrication.plan.describe", "fabrication.compatibility.validate", "fabrication.result.describe")


class FabricationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise FabricationError(code)


def name(value):
    try:
        sdk._name(value, "FABRICATION_ID_INVALID")
    except sdk.DomainContractError as error:
        raise FabricationError("FABRICATION_ID_INVALID") from error


def digest(value):
    require(type(value) is str and re.fullmatch(r"[0-9A-F]{64}", value) is not None, "FABRICATION_DIGEST_INVALID")


def refs(owner):
    try:
        sdk._refs(owner, "provenance", CanonicalReference, "FABRICATION_PROVENANCE_INVALID")
    except sdk.DomainContractError as error:
        raise FabricationError("FABRICATION_PROVENANCE_INVALID") from error


def declarations(values, *, processes=False):
    require(type(values) is tuple and all(type(v) is str for v in values), "FABRICATION_DECLARATION_INVALID")
    require(len(set(values)) == len(values), "FABRICATION_DECLARATION_DUPLICATE")
    for value in values:
        if processes:
            require(value == PROCESS, "FABRICATION_PROCESS_UNSUPPORTED")
        else:
            name(value)
    return tuple(sorted(values))


@dataclass(frozen=True)
class FabricationInput(sdk.CanonicalModel):
    kind: str
    digest: str
    payload: bytes | None = None
    variant: ParametricVariant | None = None
    provenance: tuple = ()
    DOMAIN = "apexforge.fabrication.input/v1"

    def __post_init__(self):
        require(type(self.kind) is str and self.kind in ("part-evidence", "geometry-evidence", "mesh"),
            "FABRICATION_INPUT_KIND_INVALID")
        digest(self.digest)
        require(self.payload is None or type(self.payload) is bytes, "FABRICATION_INPUT_BYTES_INVALID")
        if self.payload is not None:
            require(sha256(self.payload).hexdigest().upper() == self.digest, "FABRICATION_INPUT_INTEGRITY_FAILED")
        require(self.variant is None or type(self.variant) is ParametricVariant, "FABRICATION_VARIANT_REFERENCE_INVALID")
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "kind": self.kind, "digest": self.digest,
            "integrity": "BYTES_MATCH" if self.payload is not None else "BYTES_NOT_SUPPLIED",
            "variant_fingerprint": None if self.variant is None else self.variant.fingerprint(),
            "provenance": [r.record() for r in self.provenance], "geometry_interpreted": False}


@dataclass(frozen=True)
class MaterialProfile(sdk.CanonicalModel):
    identifier: str
    family: str
    processes: tuple | None
    provenance: tuple = ()
    DOMAIN = "apexforge.fabrication.material/v1"

    def __post_init__(self):
        name(self.identifier)
        name(self.family)
        if self.processes is not None:
            object.__setattr__(self, "processes", declarations(self.processes, processes=True))
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier, "family": self.family,
            "processes": None if self.processes is None else list(self.processes),
            "provenance": [r.record() for r in self.provenance], "material_certified": False}


@dataclass(frozen=True)
class BuildEnvelope(sdk.CanonicalModel):
    x: ParametricScalar
    y: ParametricScalar
    z: ParametricScalar
    unit: str
    DOMAIN = "apexforge.fabrication.envelope/v1"

    def __post_init__(self):
        require(all(type(v) is ParametricScalar and v.ticks > 0 for v in (self.x, self.y, self.z)) and
            type(self.unit) is str and self.unit in ("mm", "m"), "FABRICATION_ENVELOPE_INVALID")

    def record(self):
        return {"schema": self.DOMAIN, "x": self.x.value, "y": self.y.value, "z": self.z.value, "unit": self.unit}


@dataclass(frozen=True)
class MachineRequirementProfile(sdk.CanonicalModel):
    envelope: BuildEnvelope
    capabilities: tuple = ()
    process: str = PROCESS
    provenance: tuple = ()
    DOMAIN = "apexforge.fabrication.machine-requirements/v1"

    def __post_init__(self):
        require(type(self.process) is str and self.process == PROCESS, "FABRICATION_PROCESS_UNSUPPORTED")
        require(type(self.envelope) is BuildEnvelope, "FABRICATION_REQUIREMENT_INVALID")
        object.__setattr__(self, "capabilities", declarations(self.capabilities))
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "process": self.process, "envelope": self.envelope.record(),
            "capabilities": list(self.capabilities), "provenance": [r.record() for r in self.provenance],
            "declarative_only": True, "grants_authority": False}


@dataclass(frozen=True)
class MachineProfile(sdk.CanonicalModel):
    identifier: str
    processes: tuple | None = None
    envelope: BuildEnvelope | None = None
    material_families: tuple | None = None
    capabilities: tuple | None = None
    provenance: tuple = ()
    DOMAIN = "apexforge.fabrication.machine/v1"

    def __post_init__(self):
        name(self.identifier)
        require(self.envelope is None or type(self.envelope) is BuildEnvelope, "FABRICATION_MACHINE_INVALID")
        for field in ("processes", "material_families", "capabilities"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, declarations(value, processes=field == "processes"))
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier,
            "processes": None if self.processes is None else list(self.processes),
            "envelope": None if self.envelope is None else self.envelope.record(),
            "material_families": None if self.material_families is None else list(self.material_families),
            "capabilities": None if self.capabilities is None else list(self.capabilities),
            "provenance": [r.record() for r in self.provenance], "evidence_origin": "CALLER_SUPPLIED",
            "live_machine_state": False}


@dataclass(frozen=True)
class ProcessParameters(sdk.CanonicalModel):
    clearance: ParametricScalar
    unit: str
    process: str = PROCESS
    DOMAIN = "apexforge.fabrication.process-parameters/v1"

    def __post_init__(self):
        require(type(self.process) is str and self.process == PROCESS, "FABRICATION_PROCESS_UNSUPPORTED")
        require(type(self.clearance) is ParametricScalar and self.clearance.ticks >= 0 and
            type(self.unit) is str and self.unit in ("mm", "m"), "FABRICATION_PARAMETER_INVALID")

    def record(self):
        return {"schema": self.DOMAIN, "process": self.process, "clearance": self.clearance.value,
            "unit": self.unit, "applied_to_geometry": False}


@dataclass(frozen=True)
class FabricationJobIdentity(sdk.CanonicalModel):
    identifier: str
    DOMAIN = "apexforge.fabrication.job-identity/v1"

    def __post_init__(self):
        name(self.identifier)

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier}


def fabrication_platform(manifest):
    require(type(manifest) is PackageManifest, "FABRICATION_PACKAGE_INVALID")
    return sdk.DomainPlatformDescriptor(PLATFORM, sdk.ImplementationPackage.from_manifest(manifest),
        ExactVersion(1, 0, 0), OPERATIONS, (sdk.DomainCapability("fabrication.describe"),), provenance=manifest.provenance)


@dataclass(frozen=True)
class FabricationPlan(sdk.CanonicalModel):
    job: FabricationJobIdentity
    platform: sdk.DomainPlatformDescriptor
    input: FabricationInput
    material: MaterialProfile
    requirements: MachineRequirementProfile
    parameters: ProcessParameters
    provenance: tuple = ()
    DOMAIN = "apexforge.fabrication.plan/v1"

    def __post_init__(self):
        require(type(self.job) is FabricationJobIdentity and type(self.input) is FabricationInput and
            type(self.material) is MaterialProfile and type(self.requirements) is MachineRequirementProfile and
            type(self.parameters) is ProcessParameters, "FABRICATION_PLAN_INVALID")
        require(type(self.platform) is sdk.DomainPlatformDescriptor and self.platform.identity == PLATFORM and
            self.platform.contract_version == ExactVersion(1, 0, 0) and self.platform.operations == tuple(sorted(OPERATIONS)) and
            self.platform.capabilities == (sdk.DomainCapability("fabrication.describe"),) and not self.platform.dependencies,
            "FABRICATION_PLATFORM_INVALID")
        require(self.parameters.unit == self.requirements.envelope.unit, "FABRICATION_PARAMETER_UNIT_MISMATCH")
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "job": self.job.record(), "platform": self.platform.record(),
            "platform_fingerprint": self.platform.fingerprint(), "input": self.input.record(),
            "material": self.material.record(), "requirements": self.requirements.record(),
            "parameters": self.parameters.record(), "process": PROCESS,
            "provenance": [r.record() for r in self.provenance], "semantic_authority": "CANONICAL_AIR",
            "execution": "NOT_PERFORMED", "grants_authority": False}


@dataclass(frozen=True)
class FabricationCheck(sdk.CanonicalModel):
    dimension: str
    status: str
    code: str
    DOMAIN = "apexforge.fabrication.check/v1"

    def __post_init__(self):
        name(self.dimension)
        require(type(self.status) is str and self.status in ("COMPATIBLE", "INCOMPATIBLE", "UNKNOWN"),
            "FABRICATION_CHECK_INVALID")
        require(type(self.code) is str and re.fullmatch(r"[A-Z_]+", self.code) is not None, "FABRICATION_CHECK_INVALID")

    def record(self):
        return {"dimension": self.dimension, "status": self.status, "code": self.code}


@dataclass(frozen=True)
class FabricationValidation(sdk.CanonicalModel):
    plan: FabricationPlan
    machine: MachineProfile | None
    DOMAIN = "apexforge.fabrication.validation/v1"

    def __post_init__(self):
        require(type(self.plan) is FabricationPlan and (self.machine is None or type(self.machine) is MachineProfile),
            "FABRICATION_VALIDATION_INVALID")

    @property
    def checks(self):
        plan, machine = self.plan, self.machine
        result = []
        def check(dimension, evidence, matches, missing, mismatch):
            result.append(FabricationCheck(dimension, "UNKNOWN" if evidence is None else
                ("COMPATIBLE" if matches else "INCOMPATIBLE"), missing if evidence is None else
                ("EVIDENCE_MATCH" if matches else mismatch)))
        check("input.integrity", plan.input.payload, plan.input.payload is not None,
            "INPUT_BYTES_MISSING", "INPUT_DIGEST_MISMATCH")
        check("material.process", plan.material.processes, plan.material.processes is not None and PROCESS in plan.material.processes,
            "MATERIAL_PROCESS_MISSING", "MATERIAL_PROCESS_INCOMPATIBLE")
        for dimension, field, required in (("machine.process", "processes", (PROCESS,)),
            ("machine.material", "material_families", (plan.material.family,)),
            ("machine.capabilities", "capabilities", plan.requirements.capabilities)):
            evidence = None if machine is None else getattr(machine, field)
            # Empty requirement is satisfied without inventing any machine capability.
            check(dimension, () if not required else evidence, evidence is not None and set(required) <= set(evidence) or not required,
                "MACHINE_DECLARATION_MISSING", "MACHINE_DECLARATION_INCOMPATIBLE")
        envelope = None if machine is None else machine.envelope
        same_unit = envelope is not None and envelope.unit == plan.requirements.envelope.unit
        if envelope is not None and not same_unit:
            result.append(FabricationCheck("machine.envelope", "UNKNOWN", "UNIT_CONVERSION_UNSUPPORTED"))
        else:
            fits = same_unit and all(getattr(envelope, axis).ticks >= getattr(plan.requirements.envelope, axis).ticks for axis in "xyz")
            check("machine.envelope", envelope, fits, "MACHINE_ENVELOPE_MISSING", "MACHINE_ENVELOPE_TOO_SMALL")
        result.append(FabricationCheck("parameters", "COMPATIBLE", "DECLARATION_VALID"))
        return tuple(sorted(result, key=lambda c: c.dimension))

    @property
    def status(self):
        statuses = {c.status for c in self.checks}
        return "INVALID" if "INCOMPATIBLE" in statuses else ("INCOMPLETE" if "UNKNOWN" in statuses else "VALID")

    def record(self):
        return {"schema": self.DOMAIN, "plan_fingerprint": self.plan.fingerprint(),
            "machine_fingerprint": None if self.machine is None else self.machine.fingerprint(),
            "checks": [c.record() for c in self.checks], "status": self.status,
            "engineering_safety_proven": False, "grants_authority": False}


@dataclass(frozen=True)
class FabricationResultRecord(sdk.CanonicalModel):
    plan: FabricationPlan
    reported_status: str
    outputs: tuple = ()
    provenance: tuple = ()
    DOMAIN = "apexforge.fabrication.result/v1"

    def __post_init__(self):
        require(type(self.plan) is FabricationPlan and type(self.reported_status) is str and
            self.reported_status in ("REPORTED_COMPLETED", "REPORTED_FAILED", "REPORTED_ABORTED"), "FABRICATION_RESULT_INVALID")
        try:
            sdk._refs(self, "outputs", CanonicalReference, "FABRICATION_RESULT_INVALID")
        except sdk.DomainContractError as error:
            raise FabricationError("FABRICATION_RESULT_INVALID") from error
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "plan_fingerprint": self.plan.fingerprint(), "reported_status": self.reported_status,
            "outputs": [r.record() for r in self.outputs], "provenance": [r.record() for r in self.provenance],
            "evidence_origin": "EXTERNALLY_SUPPLIED", "physical_fabrication_verified": False}


def fabrication_artifact(record, *, semantic_inputs=(), symbols=()):
    require(type(record) in (FabricationPlan, FabricationValidation, FabricationResultRecord), "FABRICATION_ARTIFACT_INVALID")
    plan = record if type(record) is FabricationPlan else record.plan
    operation = "fabrication.plan.describe" if type(record) is FabricationPlan else (
        "fabrication.compatibility.validate" if type(record) is FabricationValidation else "fabrication.result.describe")
    payload = sdk._json({"record": record.record(), "record_fingerprint": record.fingerprint()}).encode("utf-8")
    return sdk.DomainArtifact.from_bytes(plan.platform, operation, "model", payload, semantic_inputs=semantic_inputs,
        symbols=symbols, provenance=record.provenance if type(record) is not FabricationValidation else plan.provenance)
