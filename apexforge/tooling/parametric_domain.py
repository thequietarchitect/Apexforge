"""Exact passive parameter contracts; no CAD, expression or fabrication execution."""
from dataclasses import dataclass
import re

from tooling import domain_platform as sdk
from tooling.package_manifest import PackageManifest, ExactVersion, CanonicalReference

PLATFORM = sdk.DomainPlatformIdentity("apexforge.parametric", "parametric")
OPERATIONS = ("parametric.design.describe", "parametric.parameters.describe", "parametric.variant.describe")
KINDS = frozenset(("scalar", "integer", "boolean", "enumeration"))
SCALAR_UNITS = frozenset((("length", "m"), ("length", "mm"), ("angle", "rad"),
    ("ratio", "1"), ("unitless", "1")))
MAX_PARAMETERS = 4096


class ParametricError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise ParametricError(code)


def name(value, code):
    try:
        sdk._name(value, code)
    except sdk.DomainContractError as error:
        raise ParametricError(code) from error


def refs(owner, field="provenance"):
    try:
        sdk._refs(owner, field, CanonicalReference, "PARAMETRIC_REFERENCE_INVALID")
    except sdk.DomainContractError as error:
        raise ParametricError("PARAMETRIC_REFERENCE_INVALID") from error


@dataclass(frozen=True)
class ParametricDesignIdentity(sdk.CanonicalModel):
    identifier: str
    DOMAIN = "apexforge.parametric.design-identity/v1"

    def __post_init__(self):
        name(self.identifier, "PARAMETRIC_DESIGN_ID_INVALID")

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier}


@dataclass(frozen=True)
class ParameterIdentity(sdk.CanonicalModel):
    identifier: str
    DOMAIN = "apexforge.parametric.parameter-identity/v1"

    def __post_init__(self):
        name(self.identifier, "PARAMETER_ID_INVALID")

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier}


@dataclass(frozen=True)
class ParametricScalar(sdk.CanonicalModel):
    value: str
    DOMAIN = "apexforge.parametric.scalar/v1"

    def __post_init__(self):
        require(type(self.value) is str and len(self.value) <= 29 and
            re.fullmatch(r"-?(?:0|[1-9][0-9]{0,17})(?:\.[0-9]{1,9})?", self.value) is not None,
            "PARAMETER_SCALAR_INVALID")
        value = self.value.rstrip("0").rstrip(".") if "." in self.value else self.value
        object.__setattr__(self, "value", "0" if value == "-0" else value)

    @property
    def ticks(self):
        whole, _, fraction = self.value.lstrip("-").partition(".")
        value = int(whole) * 10 ** 9 + int(fraction.ljust(9, "0"))
        return -value if self.value.startswith("-") else value

    def record(self):
        return {"schema": self.DOMAIN, "value": self.value}


@dataclass(frozen=True)
class ParameterValue(sdk.CanonicalModel):
    kind: str
    value: object
    unit: str | None = None
    DOMAIN = "apexforge.parametric.value/v1"

    def __post_init__(self):
        require(type(self.kind) is str and self.kind in KINDS, "PARAMETER_KIND_UNSUPPORTED")
        if self.kind == "scalar":
            require(type(self.value) is ParametricScalar and type(self.unit) is str and
                self.unit in {unit for _, unit in SCALAR_UNITS}, "PARAMETER_VALUE_INVALID")
        elif self.kind == "integer":
            require(type(self.value) is int and -(2 ** 63) <= self.value < 2 ** 63 and
                self.unit == "count", "PARAMETER_VALUE_INVALID")
        elif self.kind == "boolean":
            require(type(self.value) is bool and self.unit is None, "PARAMETER_VALUE_INVALID")
        else:
            name(self.value, "PARAMETER_VALUE_INVALID")
            require(self.unit is None, "PARAMETER_VALUE_INVALID")

    def record(self):
        return {"schema": self.DOMAIN, "kind": self.kind, "unit": self.unit,
            "value": self.value.value if self.kind == "scalar" else self.value}


@dataclass(frozen=True)
class ParameterDefinition(sdk.CanonicalModel):
    identity: ParameterIdentity
    kind: str
    dimension: str | None = None
    unit: str | None = None
    required: bool = True
    minimum: object = None
    maximum: object = None
    alternatives: tuple = ()
    presentation: str | None = None
    DOMAIN = "apexforge.parametric.parameter-definition/v1"

    def __post_init__(self):
        require(type(self.identity) is ParameterIdentity, "PARAMETER_ID_INVALID")
        require(type(self.kind) is str and self.kind in KINDS, "PARAMETER_KIND_UNSUPPORTED")
        require(type(self.required) is bool, "PARAMETER_REQUIRED_INVALID")
        require(self.presentation is None or (type(self.presentation) is str and len(self.presentation) <= 4096),
            "PARAMETER_PRESENTATION_INVALID")
        require(type(self.alternatives) is tuple and all(type(v) is str for v in self.alternatives),
            "PARAMETER_ALTERNATIVES_INVALID")
        if self.kind == "scalar":
            require(type(self.dimension) is str and type(self.unit) is str and
                (self.dimension, self.unit) in SCALAR_UNITS, "PARAMETER_UNIT_INVALID")
            bound_type = ParametricScalar
        elif self.kind == "integer":
            require(self.dimension == "count" and self.unit == "count", "PARAMETER_UNIT_INVALID")
            bound_type = int
        else:
            require(self.dimension is None and self.unit is None, "PARAMETER_UNIT_INVALID")
            bound_type = None
        for bound in (self.minimum, self.maximum):
            require(bound is None or (bound_type is not None and type(bound) is bound_type), "PARAMETER_BOUND_INVALID")
            if bound is not None and self.kind == "integer":
                require(-(2 ** 63) <= bound < 2 ** 63, "PARAMETER_BOUND_INVALID")
        if self.minimum is not None and self.maximum is not None:
            require(self._number(self.minimum) <= self._number(self.maximum), "PARAMETER_BOUND_INVALID")
        if self.kind == "enumeration":
            require(bool(self.alternatives) and len(set(self.alternatives)) == len(self.alternatives),
                "PARAMETER_ALTERNATIVES_INVALID")
            for alternative in self.alternatives:
                name(alternative, "PARAMETER_ALTERNATIVES_INVALID")
            object.__setattr__(self, "alternatives", tuple(sorted(self.alternatives)))
        else:
            require(not self.alternatives, "PARAMETER_ALTERNATIVES_INVALID")

    def _number(self, value):
        return value.ticks if self.kind == "scalar" else value

    def validate(self, value):
        require(type(value) is ParameterValue and value.kind == self.kind, "PARAMETER_VALUE_KIND_MISMATCH")
        require(value.unit == self.unit, "PARAMETER_VALUE_UNIT_MISMATCH")
        if self.kind == "enumeration":
            require(value.value in self.alternatives, "PARAMETER_ENUM_NOT_ALLOWED")
        for bound, lower in ((self.minimum, True), (self.maximum, False)):
            if bound is not None:
                number, limit = self._number(value.value), self._number(bound)
                require(number >= limit if lower else number <= limit, "PARAMETER_RANGE_VIOLATION")

    def record(self):
        return {"schema": self.DOMAIN, "identity": self.identity.record(), "kind": self.kind,
            "dimension": self.dimension, "unit": self.unit, "required": self.required,
            "minimum": self.minimum.value if type(self.minimum) is ParametricScalar else self.minimum,
            "maximum": self.maximum.value if type(self.maximum) is ParametricScalar else self.maximum,
            "alternatives": list(self.alternatives), "default_policy": "NO_DEFAULTS"}


@dataclass(frozen=True)
class ParameterReference(sdk.CanonicalModel):
    source: ParameterIdentity
    target: ParameterIdentity
    relation: str = "references"
    DOMAIN = "apexforge.parametric.parameter-reference/v1"

    def __post_init__(self):
        require(type(self.source) is ParameterIdentity and type(self.target) is ParameterIdentity and
            self.relation == "references", "PARAMETER_EDGE_INVALID")

    def record(self):
        return {"schema": self.DOMAIN, "source": self.source.record(), "target": self.target.record(),
            "relation": self.relation, "evaluation": "NOT_PERFORMED"}


def parametric_platform(manifest):
    require(type(manifest) is PackageManifest, "PARAMETRIC_PACKAGE_INVALID")
    return sdk.DomainPlatformDescriptor(PLATFORM, sdk.ImplementationPackage.from_manifest(manifest),
        ExactVersion(1, 0, 0), OPERATIONS, (sdk.DomainCapability("parametric.describe"),), provenance=manifest.provenance)


@dataclass(frozen=True)
class ParametricDesign(sdk.CanonicalModel):
    identity: ParametricDesignIdentity
    platform: sdk.DomainPlatformDescriptor
    parameters: tuple
    references: tuple = ()
    representations: tuple = ()
    provenance: tuple = ()
    DOMAIN = "apexforge.parametric.design/v1"

    def __post_init__(self):
        require(type(self.identity) is ParametricDesignIdentity, "PARAMETRIC_DESIGN_ID_INVALID")
        require(type(self.platform) is sdk.DomainPlatformDescriptor and self.platform.identity == PLATFORM and
            self.platform.contract_version == ExactVersion(1, 0, 0) and self.platform.operations == tuple(sorted(OPERATIONS)) and
            self.platform.capabilities == (sdk.DomainCapability("parametric.describe"),) and not self.platform.dependencies,
            "PARAMETRIC_PLATFORM_INVALID")
        require(type(self.parameters) is tuple and len(self.parameters) <= MAX_PARAMETERS and
            all(type(p) is ParameterDefinition for p in self.parameters), "PARAMETER_DEFINITION_INVALID")
        ids = set(p.identity for p in self.parameters)
        require(len(ids) == len(self.parameters), "PARAMETER_DECLARATION_DUPLICATE")
        object.__setattr__(self, "parameters", tuple(sorted(self.parameters, key=lambda p: p.identity.identifier)))
        require(type(self.references) is tuple and all(type(e) is ParameterReference for e in self.references),
            "PARAMETER_GRAPH_INVALID")
        pairs = tuple((e.source.identifier, e.target.identifier) for e in self.references)
        require(len(set(pairs)) == len(pairs), "PARAMETER_EDGE_DUPLICATE")
        require(all(e.source in ids and e.target in ids for e in self.references), "PARAMETER_REFERENCE_MISSING")
        object.__setattr__(self, "references", tuple(e for _, e in sorted(zip(pairs, self.references))))
        refs(self, "representations")
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "identity": self.identity.record(), "platform": self.platform.record(),
            "platform_fingerprint": self.platform.fingerprint(), "parameters": [p.record() for p in self.parameters],
            "graph": [e.record() for e in self.references], "representations": [r.record() for r in self.representations],
            "provenance": [r.record() for r in self.provenance], "semantic_authority": "CANONICAL_AIR",
            "geometry_generated": False, "grants_authority": False}


@dataclass(frozen=True)
class ParameterAssignment(sdk.CanonicalModel):
    identity: ParameterIdentity
    value: ParameterValue
    DOMAIN = "apexforge.parametric.assignment/v1"

    def __post_init__(self):
        require(type(self.identity) is ParameterIdentity and type(self.value) is ParameterValue, "PARAMETER_ASSIGNMENT_INVALID")

    def record(self):
        return {"identity": self.identity.record(), "value": self.value.record()}


@dataclass(frozen=True)
class ParameterSet(sdk.CanonicalModel):
    design: ParametricDesign
    assignments: tuple
    provenance: tuple = ()
    DOMAIN = "apexforge.parametric.parameter-set/v1"

    def __post_init__(self):
        require(type(self.design) is ParametricDesign, "PARAMETRIC_DESIGN_BINDING_INVALID")
        require(type(self.assignments) is tuple and all(type(a) is ParameterAssignment for a in self.assignments),
            "PARAMETER_ASSIGNMENT_INVALID")
        ids = set(a.identity for a in self.assignments)
        require(len(ids) == len(self.assignments), "PARAMETER_ASSIGNMENT_DUPLICATE")
        definitions = {p.identity: p for p in self.design.parameters}
        require(ids <= definitions.keys(), "PARAMETER_ASSIGNMENT_UNDECLARED")
        require(all(not p.required or p.identity in ids for p in self.design.parameters), "PARAMETER_REQUIRED_MISSING")
        ordered = tuple(sorted(self.assignments, key=lambda a: a.identity.identifier))
        for assignment in ordered:
            definitions[assignment.identity].validate(assignment.value)
        object.__setattr__(self, "assignments", ordered)
        refs(self)

    def record(self):
        assigned = set(a.identity for a in self.assignments)
        return {"schema": self.DOMAIN, "design": self.design.identity.record(), "design_fingerprint": self.design.fingerprint(),
            "assignments": [a.record() for a in self.assignments],
            "omitted_optional": [p.identity.record() for p in self.design.parameters if p.identity not in assigned],
            "provenance": [r.record() for r in self.provenance], "local_constraints": "SATISFIED"}


@dataclass(frozen=True)
class ParametricVariant(sdk.CanonicalModel):
    parameters: ParameterSet
    provenance: tuple = ()
    DOMAIN = "apexforge.parametric.variant/v1"

    def __post_init__(self):
        require(type(self.parameters) is ParameterSet, "PARAMETRIC_VARIANT_INVALID")
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "parameter_set": self.parameters.record(),
            "parameter_set_fingerprint": self.parameters.fingerprint(), "provenance": [r.record() for r in self.provenance],
            "geometry_generated": False, "engineering_safety_proven": False, "grants_authority": False}


def parametric_artifact(record, *, semantic_inputs=(), symbols=()):
    require(type(record) in (ParametricDesign, ParameterSet, ParametricVariant), "PARAMETRIC_ARTIFACT_INVALID")
    design = record if type(record) is ParametricDesign else (record.design if type(record) is ParameterSet else record.parameters.design)
    operation = "parametric.design.describe" if type(record) is ParametricDesign else (
        "parametric.parameters.describe" if type(record) is ParameterSet else "parametric.variant.describe")
    payload = sdk._json({"record": record.record(), "record_fingerprint": record.fingerprint()}).encode("utf-8")
    return sdk.DomainArtifact.from_bytes(design.platform, operation, "model", payload,
        semantic_inputs=semantic_inputs, symbols=symbols, provenance=record.provenance)
