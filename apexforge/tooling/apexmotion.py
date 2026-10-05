"""P15.3 passive motion descriptions; no physics, transforms or execution."""
from dataclasses import dataclass
from hashlib import sha256
import json
import re
from types import MappingProxyType

from tooling import domain_platform as sdk
from tooling.package_manifest import PackageManifest, ExactVersion, CanonicalReference, SymbolReference

OPERATIONS = ("motion.state.describe", "motion.trajectory.describe",
              "motion.constraint.describe", "motion.plan.describe")
UNITS = MappingProxyType({"position": "m", "velocity": "m/s", "acceleration": "m/s2"})


class ApexMotionError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(ok, code):
    if not ok:
        raise ApexMotionError(code)


def _id(value, code):
    _require(type(value) is str and len(value) <= 128 and
        re.fullmatch(r"[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)*", value), code)


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _provenance(owner):
    values = owner.provenance
    _require(type(values) is tuple and all(type(v) is CanonicalReference for v in values), "MOTION_PROVENANCE_INVALID")
    keys = tuple(_json(v.record()) for v in values)
    _require(len(set(keys)) == len(keys), "MOTION_PROVENANCE_DUPLICATE")
    object.__setattr__(owner, "provenance", tuple(v for _, v in sorted(zip(keys, values), key=lambda p: p[0])))


class MotionRecord:
    def canonical_bytes(self):
        return _json(self.record()).encode("utf-8")

    def fingerprint(self):
        return sha256(self.SCHEMA.encode() + b"\0" + self.canonical_bytes()).hexdigest().upper()


@dataclass(frozen=True)
class MotionScalar:
    """Exact decimal input: <=18 integer digits, <=9 fractional digits, no exponent/float."""
    value: str

    def __post_init__(self):
        _require(type(self.value) is str and len(self.value) <= 29 and
            re.fullmatch(r"-?(?:0|[1-9][0-9]{0,17})(?:\.[0-9]{1,9})?", self.value), "MOTION_SCALAR_INVALID")
        text = self.value.rstrip("0").rstrip(".") if "." in self.value else self.value
        if text == "-0":
            text = "0"
        object.__setattr__(self, "value", text)

    @property
    def ticks(self):
        parts = self.value.lstrip("-").split(".")
        amount = int(parts[0]) * 1000000000 + int((parts[1] if len(parts) == 2 else "").ljust(9, "0"))
        return -amount if self.value.startswith("-") else amount


@dataclass(frozen=True)
class MotionEntity:
    identifier: str

    def __post_init__(self):
        _id(self.identifier, "MOTION_ENTITY_INVALID")


@dataclass(frozen=True)
class FrameIdentity:
    identifier: str

    def __post_init__(self):
        _id(self.identifier, "MOTION_FRAME_INVALID")


@dataclass(frozen=True)
class ReferenceFrame(MotionRecord):
    identity: FrameIdentity
    handedness: str
    parent: FrameIdentity | None = None
    dimensions: int = 3
    SCHEMA = "apexforge.apexmotion.frame/v1"

    def __post_init__(self):
        _require(type(self.identity) is FrameIdentity and type(self.dimensions) is int and self.dimensions == 3,
                 "MOTION_FRAME_INVALID")
        _require(type(self.handedness) is str and self.handedness in ("right", "left"), "MOTION_FRAME_INVALID")
        _require(self.parent is None or (type(self.parent) is FrameIdentity and self.parent != self.identity),
                 "MOTION_FRAME_PARENT_INVALID")

    def record(self):
        return {"schema": self.SCHEMA, "id": self.identity.identifier, "dimensions": self.dimensions,
                "handedness": self.handedness, "parent": None if self.parent is None else self.parent.identifier}


@dataclass(frozen=True)
class MotionVector(MotionRecord):
    x: MotionScalar
    y: MotionScalar
    z: MotionScalar
    unit: str
    frame: ReferenceFrame
    SCHEMA = "apexforge.apexmotion.vector/v1"

    def __post_init__(self):
        _require(all(type(v) is MotionScalar for v in (self.x, self.y, self.z)), "MOTION_VECTOR_INVALID")
        _require(type(self.unit) is str and self.unit in ("m", "m/s", "m/s2"), "MOTION_UNIT_INVALID")
        _require(type(self.frame) is ReferenceFrame, "MOTION_FRAME_REQUIRED")

    def record(self):
        return {"schema": self.SCHEMA, "x": self.x.value, "y": self.y.value, "z": self.z.value,
                "unit": self.unit, "frame": self.frame.record()}


@dataclass(frozen=True)
class MotionTime(MotionRecord):
    value: MotionScalar
    origin: str
    unit: str = "s"
    SCHEMA = "apexforge.apexmotion.time/v1"

    def __post_init__(self):
        _require(type(self.value) is MotionScalar, "MOTION_TIME_INVALID")
        _id(self.origin, "MOTION_TIME_ORIGIN_INVALID")
        _require(self.unit == "s", "MOTION_UNIT_INVALID")

    def record(self):
        return {"schema": self.SCHEMA, "value": self.value.value, "origin": self.origin, "unit": self.unit}


@dataclass(frozen=True)
class MotionState(MotionRecord):
    entity: MotionEntity
    time: MotionTime
    position: MotionVector
    velocity: MotionVector | None = None
    acceleration: MotionVector | None = None
    provenance: tuple[CanonicalReference, ...] = ()
    SCHEMA = "apexforge.apexmotion.state/v1"

    def __post_init__(self):
        _require(type(self.entity) is MotionEntity and type(self.time) is MotionTime, "MOTION_STATE_INVALID")
        _require(type(self.position) is MotionVector, "MOTION_POSITION_REQUIRED")
        for name in UNITS:
            vector = getattr(self, name)
            if vector is None and name != "position":
                continue
            _require(type(vector) is MotionVector and vector.unit == UNITS[name], "MOTION_COMPONENT_UNIT_INVALID")
            _require(vector.frame == self.position.frame, "MOTION_COMPONENT_FRAME_MISMATCH")
        _provenance(self)

    @property
    def frame(self):
        return self.position.frame

    def record(self):
        return {"schema": self.SCHEMA, "entity": self.entity.identifier, "time": self.time.record(),
            "position": self.position.record(), "velocity": None if self.velocity is None else self.velocity.record(),
            "acceleration": None if self.acceleration is None else self.acceleration.record(),
            "provenance": [p.record() for p in self.provenance], "origin_status": "CALLER_SUPPLIED",
            "semantic_authority": "CANONICAL_AIR"}


def _same_context(a, b, code):
    _require((a.entity, a.frame, a.time.origin) == (b.entity, b.frame, b.time.origin), code)


@dataclass(frozen=True)
class MotionTrajectory(MotionRecord):
    samples: tuple[MotionState, ...]
    provenance: tuple[CanonicalReference, ...] = ()
    SCHEMA = "apexforge.apexmotion.trajectory/v1"

    def __post_init__(self):
        _require(type(self.samples) is tuple and bool(self.samples) and
            all(type(s) is MotionState for s in self.samples), "MOTION_TRAJECTORY_INVALID")
        for sample in self.samples:
            _same_context(self.samples[0], sample, "MOTION_TRAJECTORY_CONTEXT_MISMATCH")
        times = tuple(s.time.value.ticks for s in self.samples)
        _require(len(set(times)) == len(times), "MOTION_TRAJECTORY_TIME_DUPLICATE")
        object.__setattr__(self, "samples", tuple(sorted(self.samples, key=lambda s: s.time.value.ticks)))
        _provenance(self)

    def record(self):
        return {"schema": self.SCHEMA, "samples": [s.record() for s in self.samples],
            "provenance": [p.record() for p in self.provenance], "interpolation": "NOT_IMPLEMENTED",
            "execution": "NOT_PERFORMED"}


@dataclass(frozen=True)
class MotionConstraint(MotionRecord):
    entity: MotionEntity
    component: str
    lower: MotionVector
    upper: MotionVector
    provenance: tuple[CanonicalReference, ...] = ()
    SCHEMA = "apexforge.apexmotion.constraint/v1"

    def __post_init__(self):
        _require(type(self.entity) is MotionEntity and type(self.component) is str and self.component in UNITS,
                 "MOTION_CONSTRAINT_INVALID")
        _require(type(self.lower) is MotionVector and type(self.upper) is MotionVector and
            self.lower.unit == self.upper.unit == UNITS[self.component], "MOTION_CONSTRAINT_UNIT_INVALID")
        _require(self.lower.frame == self.upper.frame, "MOTION_CONSTRAINT_FRAME_MISMATCH")
        _require(all(getattr(self.lower, axis).ticks <= getattr(self.upper, axis).ticks for axis in ("x", "y", "z")),
                 "MOTION_CONSTRAINT_BOUND_INVALID")
        _provenance(self)

    def record(self):
        return {"schema": self.SCHEMA, "entity": self.entity.identifier, "component": self.component,
            "lower": self.lower.record(), "upper": self.upper.record(),
            "provenance": [p.record() for p in self.provenance], "satisfaction": "NOT_EVALUATED"}


@dataclass(frozen=True)
class MotionPlan(MotionRecord):
    initial: MotionState
    target: MotionState
    constraints: tuple[MotionConstraint, ...] = ()
    trajectory: MotionTrajectory | None = None
    provenance: tuple[CanonicalReference, ...] = ()
    SCHEMA = "apexforge.apexmotion.plan/v1"

    def __post_init__(self):
        _require(type(self.initial) is MotionState and type(self.target) is MotionState, "MOTION_PLAN_INVALID")
        _same_context(self.initial, self.target, "MOTION_PLAN_CONTEXT_MISMATCH")
        _require(self.target.time.value.ticks >= self.initial.time.value.ticks, "MOTION_PLAN_TIME_INVALID")
        _require(type(self.constraints) is tuple and all(type(c) is MotionConstraint for c in self.constraints),
                 "MOTION_PLAN_CONSTRAINT_INVALID")
        for constraint in self.constraints:
            _require(constraint.entity == self.initial.entity and constraint.lower.frame == self.initial.frame,
                     "MOTION_PLAN_CONSTRAINT_CONTEXT_MISMATCH")
        keys = tuple(c.fingerprint() for c in self.constraints)
        _require(len(set(keys)) == len(keys), "MOTION_PLAN_CONSTRAINT_DUPLICATE")
        object.__setattr__(self, "constraints", tuple(c for _, c in sorted(zip(keys, self.constraints), key=lambda p: p[0])))
        if self.trajectory is not None:
            _require(type(self.trajectory) is MotionTrajectory and self.trajectory.samples[0] == self.initial and
                self.trajectory.samples[-1] == self.target, "MOTION_PLAN_TRAJECTORY_MISMATCH")
        _provenance(self)

    def record(self):
        return {"schema": self.SCHEMA, "initial": self.initial.record(), "target": self.target.record(),
            "constraints": [c.record() for c in self.constraints],
            "trajectory": None if self.trajectory is None else self.trajectory.record(),
            "provenance": [p.record() for p in self.provenance], "execution": "NOT_PERFORMED", "grants_authority": False}


def apexmotion_platform(manifest):
    _require(type(manifest) is PackageManifest, "APEXMOTION_PACKAGE_INVALID")
    return sdk.DomainPlatformDescriptor(sdk.DomainPlatformIdentity("apexforge.apexmotion", "motion"),
        sdk.ImplementationPackage.from_manifest(manifest), ExactVersion(1, 0, 0), OPERATIONS,
        (sdk.DomainCapability("motion.describe"),), provenance=manifest.provenance)


def _operation(record):
    if type(record) is MotionState:
        return "motion.state.describe"
    if type(record) is MotionTrajectory:
        return "motion.trajectory.describe"
    if type(record) is MotionConstraint:
        return "motion.constraint.describe"
    if type(record) is MotionPlan:
        return "motion.plan.describe"
    raise ApexMotionError("APEXMOTION_RECORD_INVALID")


def motion_payload(record):
    _operation(record)
    return _json({"record": record.record(), "record_fingerprint": record.fingerprint()}).encode("utf-8")


def motion_artifact(descriptor, record, *, semantic_inputs=(), symbols=()):
    _require(type(descriptor) is sdk.DomainPlatformDescriptor and
        descriptor.identity == sdk.DomainPlatformIdentity("apexforge.apexmotion", "motion") and
        descriptor.contract_version == ExactVersion(1, 0, 0) and descriptor.operations == tuple(sorted(OPERATIONS)) and
        descriptor.capabilities == (sdk.DomainCapability("motion.describe"),) and not descriptor.dependencies,
        "APEXMOTION_PLATFORM_BINDING_INVALID")
    return sdk.DomainArtifact.from_bytes(descriptor, _operation(record),
        "plan" if type(record) is MotionPlan else "model", motion_payload(record),
        semantic_inputs=semantic_inputs, symbols=symbols, provenance=record.provenance)


def motion_request(descriptor, record, *, semantic_inputs=(), symbols=()):
    artifact = motion_artifact(descriptor, record, semantic_inputs=semantic_inputs, symbols=symbols)
    return sdk.DomainRequest(descriptor, _operation(record), semantic_inputs=semantic_inputs, symbols=symbols,
        artifacts=(artifact,), capabilities=(sdk.DomainCapability("motion.describe"),), provenance=record.provenance)
