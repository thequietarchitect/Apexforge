"""Bounded, sequential exact kinematics; no acquisition or execution adapters."""
from dataclasses import dataclass
from fractions import Fraction

from tooling import apexmotion as motion
from tooling import domain_platform as sdk

PROFILE = "apexforge.apexmotion.kinematics.constant-acceleration/v1"
MAX_STEPS = 4096
SCALE = 10 ** 9
MAX_TICKS = 10 ** 27 - 1


class SimulationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise SimulationError(code)


def scalar(ticks):
    ticks = Fraction(ticks)
    require(ticks.denominator == 1, "SIMULATION_NUMERIC_PRECISION_ERROR")
    value = ticks.numerator
    require(abs(value) <= MAX_TICKS, "SIMULATION_NUMERIC_RANGE_ERROR")
    whole, fraction = divmod(abs(value), SCALE)
    return motion.MotionScalar(("-" if value < 0 else "") + str(whole) +
        ("." + str(fraction).zfill(9) if fraction else ""))


@dataclass(frozen=True)
class SimulationSpec(motion.MotionRecord):
    descriptor: sdk.DomainPlatformDescriptor
    initial: motion.MotionState
    time_step: motion.MotionScalar
    step_count: int
    constraints: tuple = ()
    profile: str = PROFILE
    time_step_unit: str = "s"
    SCHEMA = "apexforge.apexmotion.simulation-spec/v1"

    def __post_init__(self):
        require(self.profile == PROFILE, "SIMULATION_MODEL_UNSUPPORTED")
        require(type(self.initial) is motion.MotionState, "SIMULATION_INITIAL_STATE_INVALID")
        # Reuse the exact passive platform admission boundary; this does not dispatch an operation.
        try:
            motion.motion_artifact(self.descriptor, self.initial)
        except (motion.ApexMotionError, sdk.DomainContractError) as error:
            raise SimulationError("SIMULATION_PLATFORM_INVALID") from error
        require(self.initial.velocity is not None, "SIMULATION_VELOCITY_REQUIRED")
        require(self.initial.acceleration is not None, "SIMULATION_ACCELERATION_REQUIRED")
        require(type(self.time_step) is motion.MotionScalar and self.time_step.ticks > 0 and
            self.time_step_unit == "s", "SIMULATION_TIME_STEP_INVALID")
        require(type(self.step_count) is int and 0 <= self.step_count <= MAX_STEPS,
            "SIMULATION_STEP_COUNT_INVALID")
        require(type(self.constraints) is tuple and all(type(c) is motion.MotionConstraint
            for c in self.constraints), "SIMULATION_CONSTRAINT_INVALID")
        require(all(c.entity == self.initial.entity and c.lower.frame == self.initial.frame
            for c in self.constraints), "SIMULATION_CONSTRAINT_CONTEXT_MISMATCH")
        keys = tuple(c.fingerprint() for c in self.constraints)
        require(len(set(keys)) == len(keys), "SIMULATION_CONSTRAINT_DUPLICATE")
        object.__setattr__(self, "constraints", tuple(c for _, c in sorted(zip(keys, self.constraints))))

    def record(self):
        return {"schema": self.SCHEMA, "profile": self.profile,
            "descriptor": self.descriptor.record(), "descriptor_fingerprint": self.descriptor.fingerprint(),
            "initial": self.initial.record(), "initial_fingerprint": self.initial.fingerprint(),
            "time_step": {"value": self.time_step.value, "unit": self.time_step_unit},
            "step_count": self.step_count, "constraints": [c.record() for c in self.constraints],
            "constraint_policy": "REPORT_AND_CONTINUE", "semantic_authority": "CANONICAL_AIR"}


@dataclass(frozen=True)
class ConstraintCheck(motion.MotionRecord):
    constraint_fingerprint: str
    state_fingerprint: str
    violated_axes: tuple
    SCHEMA = "apexforge.apexmotion.constraint-check/v1"

    def __post_init__(self):
        require(type(self.violated_axes) is tuple and self.violated_axes ==
            tuple(a for a in ("x", "y", "z") if a in self.violated_axes), "SIMULATION_CHECK_INVALID")

    def record(self):
        return {"schema": self.SCHEMA, "constraint_fingerprint": self.constraint_fingerprint,
            "state_fingerprint": self.state_fingerprint, "violated_axes": list(self.violated_axes),
            "status": "VIOLATED" if self.violated_axes else "SATISFIED", "state_adjusted": False}


def check_constraints(spec, state):
    checks = []
    for constraint in spec.constraints:
        vector = getattr(state, constraint.component)
        axes = tuple(axis for axis in ("x", "y", "z") if not
            getattr(constraint.lower, axis).ticks <= getattr(vector, axis).ticks <=
            getattr(constraint.upper, axis).ticks)
        checks.append(ConstraintCheck(constraint.fingerprint(), state.fingerprint(), axes))
    return tuple(checks)


def evolve(spec, prior):
    require(type(spec) is SimulationSpec and type(prior) is motion.MotionState and
        prior.entity == spec.initial.entity and prior.frame == spec.initial.frame and
        prior.time.origin == spec.initial.time.origin and prior.velocity is not None and
        prior.acceleration == spec.initial.acceleration, "SIMULATION_STATE_CONTEXT_MISMATCH")
    dt = Fraction(spec.time_step.ticks, SCALE)
    position, velocity = [], []
    for axis in ("x", "y", "z"):
        x = getattr(prior.position, axis).ticks
        v = getattr(prior.velocity, axis).ticks
        a = getattr(prior.acceleration, axis).ticks
        position.append(scalar(x + v * dt + a * dt * dt / 2))
        velocity.append(scalar(v + a * dt))
    return motion.MotionState(prior.entity,
        motion.MotionTime(scalar(prior.time.value.ticks + spec.time_step.ticks), prior.time.origin),
        motion.MotionVector(*position, "m", prior.frame),
        motion.MotionVector(*velocity, "m/s", prior.frame), prior.acceleration, prior.provenance)


@dataclass(frozen=True)
class SimulationStep(motion.MotionRecord):
    specification_fingerprint: str
    index: int
    prior_state_fingerprint: str
    state: motion.MotionState
    checks: tuple
    SCHEMA = "apexforge.apexmotion.simulation-step/v1"

    def __post_init__(self):
        require(type(self.index) is int and 1 <= self.index <= MAX_STEPS and
            type(self.state) is motion.MotionState and type(self.checks) is tuple and
            all(type(c) is ConstraintCheck for c in self.checks), "SIMULATION_STEP_INVALID")

    def record(self):
        # A computed-state projection, not a replacement MotionState identity algorithm.
        state = self.state.record()
        state.pop("origin_status")
        return {"schema": self.SCHEMA, "specification_fingerprint": self.specification_fingerprint,
            "index": self.index, "prior_state_fingerprint": self.prior_state_fingerprint,
            "state_fingerprint": self.state.fingerprint(), "state_fields": state,
            "checks": [c.record() for c in self.checks], "origin_status": "SIMULATED",
            "physical_event_proven": False}


@dataclass(frozen=True)
class SimulationTrace(motion.MotionRecord):
    specification: SimulationSpec
    steps: tuple
    diagnostic: str | None = None
    SCHEMA = "apexforge.apexmotion.simulation-trace/v1"

    def __post_init__(self):
        require(type(self.specification) is SimulationSpec and type(self.steps) is tuple,
            "SIMULATION_TRACE_INVALID")
        prior = self.specification.initial
        for index, step in enumerate(self.steps, 1):
            require(type(step) is SimulationStep and step.index == index and
                step.specification_fingerprint == self.specification.fingerprint() and
                step.prior_state_fingerprint == prior.fingerprint() and
                step.state == evolve(self.specification, prior) and
                step.checks == check_constraints(self.specification, step.state), "SIMULATION_TRACE_INVALID")
            prior = step.state
        require(len(self.steps) <= self.specification.step_count, "SIMULATION_TRACE_INVALID")
        if self.diagnostic is None:
            require(len(self.steps) == self.specification.step_count, "SIMULATION_TRACE_INCOMPLETE")
        else:
            require(len(self.steps) < self.specification.step_count, "SIMULATION_TRACE_INVALID")
            try:
                evolve(self.specification, prior)
            except SimulationError as error:
                require(error.code == self.diagnostic, "SIMULATION_TRACE_INVALID")
            else:
                raise SimulationError("SIMULATION_TRACE_INVALID")

    @property
    def status(self):
        if self.diagnostic:
            return self.diagnostic.removeprefix("SIMULATION_")
        checks = check_constraints(self.specification, self.specification.initial) + tuple(
            c for step in self.steps for c in step.checks)
        return "CONSTRAINT_VIOLATION" if any(c.violated_axes for c in checks) else "COMPLETED"

    def record(self):
        return {"schema": self.SCHEMA, "specification": self.specification.record(),
            "specification_fingerprint": self.specification.fingerprint(),
            "initial_checks": [c.record() for c in check_constraints(self.specification, self.specification.initial)],
            "steps": [s.record() for s in self.steps], "status": self.status,
            "diagnostics": [] if self.diagnostic is None else [{"code": self.diagnostic,
                "failed_step": len(self.steps) + 1}], "origin_status": "SIMULATED",
            "initial_inclusion": "SEPARATE_INITIAL_AND_ONE_BASED_COMPUTED_STEPS",
            "semantic_authority": "CANONICAL_AIR", "grants_authority": False,
            "physical_event_proven": False}


def simulate(spec):
    require(type(spec) is SimulationSpec, "SIMULATION_SPEC_INVALID")
    prior, steps = spec.initial, []
    for index in range(1, spec.step_count + 1):
        try:
            state = evolve(spec, prior)
        except SimulationError as error:
            return SimulationTrace(spec, tuple(steps), error.code)
        steps.append(SimulationStep(spec.fingerprint(), index, prior.fingerprint(), state,
            check_constraints(spec, state)))
        prior = state
    return SimulationTrace(spec, tuple(steps))


def simulation_artifact(record, *, semantic_inputs=(), symbols=()):
    require(type(record) in (SimulationSpec, SimulationTrace), "SIMULATION_RECORD_INVALID")
    spec = record if type(record) is SimulationSpec else record.specification
    return sdk.DomainArtifact.from_bytes(spec.descriptor,
        "motion.plan.describe" if type(record) is SimulationSpec else "motion.trajectory.describe",
        "plan" if type(record) is SimulationSpec else "model", record.canonical_bytes(),
        semantic_inputs=semantic_inputs, symbols=symbols, provenance=spec.initial.provenance)
