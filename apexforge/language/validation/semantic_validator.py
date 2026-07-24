"""
ApexForge semantic validation.

This module validates the internal consistency of an AIRProgram after
compilation and before runtime execution.

The validator is intentionally pure:

- It does not mutate the AIRProgram.
- It does not register declarations.
- It does not resolve runtime capabilities.
- It raises semantic errors when the program is inconsistent.

Validation pipeline:

    AIRProgram
        ↓
    declaration validation
        ↓
    local reference validation
        ↓
    cross-reference validation
        ↓
    semantically valid AIRProgram
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, NoReturn

# Adjust these imports to match your project structure.
from air.model import AIRProgram


# ---------------------------------------------------------------------------
# Semantic errors
# ---------------------------------------------------------------------------


class SemanticValidationError(Exception):
    """Base class for all ApexForge semantic validation errors."""


class DuplicateDeclarationError(SemanticValidationError):
    """Raised when a declaration name is defined more than once."""


class UndefinedReferenceError(SemanticValidationError):
    """Raised when an AIR object references an undefined declaration."""


class InvalidReferenceError(SemanticValidationError):
    """Raised when a reference exists but is semantically invalid."""


class CircularReferenceError(SemanticValidationError):
    """Raised when a declaration graph contains a forbidden cycle."""


class InvalidDeclarationError(SemanticValidationError):
    """Raised when a declaration itself is malformed."""


# ---------------------------------------------------------------------------
# Internal name index
# ---------------------------------------------------------------------------


class _SemanticIndex:
    """
    Case-insensitive declaration index used during validation.

    The index only records normalized names. It does not modify or replace
    the registries used by the ApexForge runtime.
    """

    def __init__(self, program: AIRProgram) -> None:
        self.role_names = self._collect_names(
            declarations=program.roles,
            declaration_kind="role",
        )

        self.authority_names = self._collect_names(
            declarations=program.authorities,
            declaration_kind="authority",
        )

        self.principal_names = self._collect_names(
            declarations=program.principals,
            declaration_kind="principal",
        )

        self.state_names = self._collect_names(
            declarations=program.states,
            declaration_kind="state",
        )

        self.event_names = self._collect_names(
            declarations=program.events,
            declaration_kind="event",
        )

        self.directive_names = self._collect_names(
            declarations=program.directives,
            declaration_kind="directive",
            require_name=False,
        )

        self.requirement_names = self._collect_names(
            declarations=program.requirements,
            declaration_kind="requirement",
            require_name=False,
        )

    @classmethod
    def _collect_names(
        cls,
        declarations: Iterable[Any],
        declaration_kind: str,
        *,
        require_name: bool = True,
    ) -> frozenset[str]:
        names: set[str] = set()

        for declaration in declarations:
            raw_name = getattr(declaration, "name", None)

            if raw_name is None:
                if require_name:
                    raise InvalidDeclarationError(
                        f"{declaration_kind.capitalize()} declaration "
                        f"{declaration!r} has no 'name' field."
                    )

                # Some directive or requirement models may not be named.
                continue

            normalized_name = cls.normalize_name(
                raw_name,
                description=f"{declaration_kind} name",
            )

            if normalized_name in names:
                raise DuplicateDeclarationError(
                    f"Duplicate {declaration_kind} declaration "
                    f"'{raw_name}'."
                )

            names.add(normalized_name)

        return frozenset(names)

    @staticmethod
    def normalize_name(value: Any, *, description: str) -> str:
        if not isinstance(value, str):
            raise InvalidDeclarationError(
                f"{description.capitalize()} must be a string; "
                f"received {type(value).__name__}."
            )

        normalized = value.strip().lower()

        if not normalized:
            raise InvalidDeclarationError(
                f"{description.capitalize()} cannot be empty."
            )

        return normalized


# ---------------------------------------------------------------------------
# Semantic validator
# ---------------------------------------------------------------------------


class SemanticValidator:
    """
    Validates a complete AIRProgram.

    A SemanticValidator instance may be reused. No validation state is retained
    between calls.
    """

    def validate(self, program: AIRProgram) -> None:
        """
        Validate the supplied AIRProgram.

        Raises:
            SemanticValidationError:
                If any semantic rule is violated.
        """

        self._validate_program_type(program)

        # Building the index validates declaration names and duplicates.
        index = _SemanticIndex(program)

        self.validate_roles(program, index)
        self.validate_authorities(program, index)
        self.validate_principals(program, index)
        self.validate_states(program, index)
        self.validate_events(program, index)
        self.validate_requirements(program, index)
        self.validate_directives(program, index)
        self.validate_cross_references(program, index)

    # ------------------------------------------------------------------
    # Top-level program validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_program_type(program: AIRProgram) -> None:
        if not isinstance(program, AIRProgram):
            raise TypeError(
                "SemanticValidator.validate() requires an AIRProgram; "
                f"received {type(program).__name__}."
            )

    # ------------------------------------------------------------------
    # Role validation
    # ------------------------------------------------------------------

    def validate_roles(
        self,
        program: AIRProgram,
        index: _SemanticIndex,
    ) -> None:
        """
        Validate role declarations and their authority references.
        """

        for role in program.roles:
            role_name = self._required_name(role, "role")

            authorities = self._get_sequence_attribute(
                role,
                attribute_names=("authorities",),
                owner_description=f"Role '{role_name}'",
            )

            seen_authorities: set[str] = set()

            for authority_reference in authorities:
                authority_name = self._reference_name(
                    authority_reference,
                    reference_kind="authority",
                    owner_description=f"Role '{role_name}'",
                )

                normalized = self._normalize_reference(
                    authority_name,
                    description="authority name",
                )

                if normalized in seen_authorities:
                    raise DuplicateDeclarationError(
                        f"Role '{role_name}' references authority "
                        f"'{authority_name}' more than once."
                    )

                seen_authorities.add(normalized)

                if normalized not in index.authority_names:
                    raise UndefinedReferenceError(
                        f"Role '{role_name}' references undefined "
                        f"authority '{authority_name}'."
                    )

    # ------------------------------------------------------------------
    # Authority validation
    # ------------------------------------------------------------------

    def validate_authorities(
        self,
        program: AIRProgram,
        index: _SemanticIndex,
    ) -> None:
        """
        Validate authority declarations, inherited authorities,
        capabilities, and authority cycles.
        """

        inheritance_graph: dict[str, tuple[str, ...]] = {}

        for authority in program.authorities:
            authority_name = self._required_name(authority, "authority")
            authority_key = self._normalize_reference(
                authority_name,
                description="authority name",
            )

            inherited_references = self._get_sequence_attribute(
                authority,
                attribute_names=(
                    "inherits",
                    "inherited_authorities",
                    "parents",
                ),
                owner_description=f"Authority '{authority_name}'",
                required=False,
            )

            inherited_names: list[str] = []
            seen_inherited: set[str] = set()

            for inherited_reference in inherited_references:
                inherited_name = self._reference_name(
                    inherited_reference,
                    reference_kind="authority",
                    owner_description=f"Authority '{authority_name}'",
                )

                inherited_key = self._normalize_reference(
                    inherited_name,
                    description="inherited authority name",
                )

                if inherited_key == authority_key:
                    raise CircularReferenceError(
                        f"Authority '{authority_name}' cannot inherit "
                        "from itself."
                    )

                if inherited_key in seen_inherited:
                    raise DuplicateDeclarationError(
                        f"Authority '{authority_name}' inherits authority "
                        f"'{inherited_name}' more than once."
                    )

                if inherited_key not in index.authority_names:
                    raise UndefinedReferenceError(
                        f"Authority '{authority_name}' inherits undefined "
                        f"authority '{inherited_name}'."
                    )

                seen_inherited.add(inherited_key)
                inherited_names.append(inherited_key)

            inheritance_graph[authority_key] = tuple(inherited_names)

            capabilities = self._get_sequence_attribute(
                authority,
                attribute_names=("capabilities",),
                owner_description=f"Authority '{authority_name}'",
                required=False,
            )

            self._validate_unique_string_values(
                values=capabilities,
                value_kind="capability",
                owner_description=f"Authority '{authority_name}'",
            )

        self._validate_acyclic_graph(
            graph=inheritance_graph,
            declaration_kind="authority",
        )

    # ------------------------------------------------------------------
    # Principal validation
    # ------------------------------------------------------------------

    def validate_principals(
        self,
        program: AIRProgram,
        index: _SemanticIndex,
    ) -> None:
        """
        Validate principal role and authority references.
        """

        for principal in program.principals:
            principal_name = self._required_name(principal, "principal")

            roles = self._get_sequence_attribute(
                principal,
                attribute_names=("roles",),
                owner_description=f"Principal '{principal_name}'",
                required=False,
            )

            self._validate_reference_sequence(
                references=roles,
                valid_names=index.role_names,
                reference_kind="role",
                owner_description=f"Principal '{principal_name}'",
            )

            authorities = self._get_sequence_attribute(
                principal,
                attribute_names=("authorities",),
                owner_description=f"Principal '{principal_name}'",
                required=False,
            )

            self._validate_reference_sequence(
                references=authorities,
                valid_names=index.authority_names,
                reference_kind="authority",
                owner_description=f"Principal '{principal_name}'",
            )

    # ------------------------------------------------------------------
    # State validation
    # ------------------------------------------------------------------

    def validate_states(
        self,
        program: AIRProgram,
        index: _SemanticIndex,
    ) -> None:
        """
        Validate state declarations.

        This pass currently validates declaration identity and any state
        references exposed through common AIR field names.
        """

        for state in program.states:
            state_name = self._required_name(state, "state")

            initial_value = getattr(state, "initial_value", None)

            if initial_value is state:
                raise InvalidReferenceError(
                    f"State '{state_name}' cannot use itself as its "
                    "initial value."
                )

    # ------------------------------------------------------------------
    # Event validation
    # ------------------------------------------------------------------

    def validate_events(
        self,
        program: AIRProgram,
        index: _SemanticIndex,
    ) -> None:
        """
        Validate event declarations and direct state references.
        """

        for event in program.events:
            event_name = self._required_name(event, "event")

            state_references = self._get_sequence_attribute(
                event,
                attribute_names=(
                    "states",
                    "state_references",
                    "affected_states",
                ),
                owner_description=f"Event '{event_name}'",
                required=False,
            )

            self._validate_reference_sequence(
                references=state_references,
                valid_names=index.state_names,
                reference_kind="state",
                owner_description=f"Event '{event_name}'",
            )

    # ------------------------------------------------------------------
    # Requirement validation
    # ------------------------------------------------------------------

    def validate_requirements(
        self,
        program: AIRProgram,
        index: _SemanticIndex,
    ) -> None:
        """
        Validate directive requirements.

        Requirements may differ structurally between ApexForge versions.
        This pass recognizes common authority, principal, state, and event
        reference field names.
        """

        for position, requirement in enumerate(program.requirements):
            description = self._object_description(
                requirement,
                fallback=f"Requirement at index {position}",
            )

            self._validate_optional_single_reference(
                owner=requirement,
                attribute_names=("principal", "principal_name"),
                valid_names=index.principal_names,
                reference_kind="principal",
                owner_description=description,
            )

            self._validate_optional_single_reference(
                owner=requirement,
                attribute_names=("authority", "authority_name"),
                valid_names=index.authority_names,
                reference_kind="authority",
                owner_description=description,
            )

            self._validate_optional_single_reference(
                owner=requirement,
                attribute_names=("state", "state_name"),
                valid_names=index.state_names,
                reference_kind="state",
                owner_description=description,
            )

            self._validate_optional_single_reference(
                owner=requirement,
                attribute_names=("event", "event_name"),
                valid_names=index.event_names,
                reference_kind="event",
                owner_description=description,
            )

            required_capabilities = self._get_sequence_attribute(
                requirement,
                attribute_names=(
                    "capabilities",
                    "required_capabilities",
                ),
                owner_description=description,
                required=False,
            )

            self._validate_unique_string_values(
                values=required_capabilities,
                value_kind="capability",
                owner_description=description,
            )

    # ------------------------------------------------------------------
    # Directive validation
    # ------------------------------------------------------------------

    def validate_directives(
        self,
        program: AIRProgram,
        index: _SemanticIndex,
    ) -> None:
        """
        Validate directive-local references.
        """

        for position, directive in enumerate(program.directives):
            description = self._object_description(
                directive,
                fallback=f"Directive at index {position}",
            )

            self._validate_optional_single_reference(
                owner=directive,
                attribute_names=("principal", "principal_name"),
                valid_names=index.principal_names,
                reference_kind="principal",
                owner_description=description,
            )

            self._validate_optional_single_reference(
                owner=directive,
                attribute_names=("authority", "authority_name"),
                valid_names=index.authority_names,
                reference_kind="authority",
                owner_description=description,
            )

            self._validate_optional_single_reference(
                owner=directive,
                attribute_names=(
                    "event",
                    "event_name",
                    "trigger_event",
                ),
                valid_names=index.event_names,
                reference_kind="event",
                owner_description=description,
            )

            self._validate_optional_single_reference(
                owner=directive,
                attribute_names=(
                    "state",
                    "state_name",
                    "target_state",
                ),
                valid_names=index.state_names,
                reference_kind="state",
                owner_description=description,
            )

            required_capabilities = self._get_sequence_attribute(
                directive,
                attribute_names=(
                    "capabilities",
                    "required_capabilities",
                ),
                owner_description=description,
                required=False,
            )

            self._validate_unique_string_values(
                values=required_capabilities,
                value_kind="capability",
                owner_description=description,
            )

    # ------------------------------------------------------------------
    # Cross-reference validation
    # ------------------------------------------------------------------

    def validate_cross_references(
        self,
        program: AIRProgram,
        index: _SemanticIndex,
    ) -> None:
        """
        Validate program-wide references that cross declaration categories.
        """

        for position, authority_check in enumerate(program.authority_checks):
            description = self._object_description(
                authority_check,
                fallback=f"Authority check at index {position}",
            )

            self._validate_optional_single_reference(
                owner=authority_check,
                attribute_names=("principal", "principal_name"),
                valid_names=index.principal_names,
                reference_kind="principal",
                owner_description=description,
            )

            self._validate_optional_single_reference(
                owner=authority_check,
                attribute_names=("authority", "authority_name"),
                valid_names=index.authority_names,
                reference_kind="authority",
                owner_description=description,
            )

        for position, decision in enumerate(program.causal_decisions):
            description = self._object_description(
                decision,
                fallback=f"Causal decision at index {position}",
            )

            self._validate_optional_single_reference(
                owner=decision,
                attribute_names=(
                    "event",
                    "event_name",
                    "trigger_event",
                ),
                valid_names=index.event_names,
                reference_kind="event",
                owner_description=description,
            )

            self._validate_optional_single_reference(
                owner=decision,
                attribute_names=(
                    "state",
                    "state_name",
                    "target_state",
                ),
                valid_names=index.state_names,
                reference_kind="state",
                owner_description=description,
            )

    # ------------------------------------------------------------------
    # Generic reference helpers
    # ------------------------------------------------------------------

    def _validate_reference_sequence(
        self,
        references: Sequence[Any],
        valid_names: frozenset[str],
        reference_kind: str,
        owner_description: str,
    ) -> None:
        seen: set[str] = set()

        for reference in references:
            raw_name = self._reference_name(
                reference,
                reference_kind=reference_kind,
                owner_description=owner_description,
            )

            normalized = self._normalize_reference(
                raw_name,
                description=f"{reference_kind} name",
            )

            if normalized in seen:
                raise DuplicateDeclarationError(
                    f"{owner_description} references {reference_kind} "
                    f"'{raw_name}' more than once."
                )

            if normalized not in valid_names:
                raise UndefinedReferenceError(
                    f"{owner_description} references undefined "
                    f"{reference_kind} '{raw_name}'."
                )

            seen.add(normalized)

    def _validate_optional_single_reference(
        self,
        owner: Any,
        attribute_names: tuple[str, ...],
        valid_names: frozenset[str],
        reference_kind: str,
        owner_description: str,
    ) -> None:
        value = self._first_existing_attribute(
            owner,
            attribute_names,
        )

        if value is None:
            return

        raw_name = self._reference_name(
            value,
            reference_kind=reference_kind,
            owner_description=owner_description,
        )

        normalized = self._normalize_reference(
            raw_name,
            description=f"{reference_kind} name",
        )

        if normalized not in valid_names:
            raise UndefinedReferenceError(
                f"{owner_description} references undefined "
                f"{reference_kind} '{raw_name}'."
            )

    @staticmethod
    def _reference_name(
        reference: Any,
        *,
        reference_kind: str,
        owner_description: str,
    ) -> str:
        if isinstance(reference, str):
            return reference

        name = getattr(reference, "name", None)

        if isinstance(name, str):
            return name

        raise InvalidReferenceError(
            f"{owner_description} contains an invalid "
            f"{reference_kind} reference: {reference!r}."
        )

    @staticmethod
    def _required_name(declaration: Any, declaration_kind: str) -> str:
        name = getattr(declaration, "name", None)

        if not isinstance(name, str) or not name.strip():
            raise InvalidDeclarationError(
                f"{declaration_kind.capitalize()} declaration "
                f"{declaration!r} has an invalid name."
            )

        return name

    @staticmethod
    def _normalize_reference(value: str, *, description: str) -> str:
        return _SemanticIndex.normalize_name(
            value,
            description=description,
        )

    # ------------------------------------------------------------------
    # Capability and scalar helpers
    # ------------------------------------------------------------------

    def _validate_unique_string_values(
        self,
        values: Sequence[Any],
        *,
        value_kind: str,
        owner_description: str,
    ) -> None:
        seen: set[str] = set()

        for value in values:
            raw_value = self._extract_scalar_name(value)

            normalized = self._normalize_reference(
                raw_value,
                description=f"{value_kind} name",
            )

            if normalized in seen:
                raise DuplicateDeclarationError(
                    f"{owner_description} declares {value_kind} "
                    f"'{raw_value}' more than once."
                )

            seen.add(normalized)

    @staticmethod
    def _extract_scalar_name(value: Any) -> str:
        if isinstance(value, str):
            return value

        name = getattr(value, "name", None)

        if isinstance(name, str):
            return name

        value_field = getattr(value, "value", None)

        if isinstance(value_field, str):
            return value_field

        raise InvalidDeclarationError(
            f"Expected a string-like semantic value; received {value!r}."
        )

    # ------------------------------------------------------------------
    # Attribute helpers
    # ------------------------------------------------------------------

    def _get_sequence_attribute(
        self,
        owner: Any,
        attribute_names: tuple[str, ...],
        owner_description: str,
        *,
        required: bool = True,
    ) -> Sequence[Any]:
        value = self._first_existing_attribute(
            owner,
            attribute_names,
        )

        if value is None:
            if required:
                joined_names = ", ".join(attribute_names)

                raise InvalidDeclarationError(
                    f"{owner_description} is missing required field "
                    f"({joined_names})."
                )

            return ()

        if isinstance(value, (str, bytes)):
            raise InvalidDeclarationError(
                f"{owner_description} field must be a sequence, "
                "not a string."
            )

        if not isinstance(value, Sequence):
            try:
                return tuple(value)
            except TypeError as error:
                raise InvalidDeclarationError(
                    f"{owner_description} field must be iterable."
                ) from error

        return value

    @staticmethod
    def _first_existing_attribute(
        owner: Any,
        attribute_names: tuple[str, ...],
    ) -> Any | None:
        for attribute_name in attribute_names:
            if hasattr(owner, attribute_name):
                return getattr(owner, attribute_name)

        return None

    @staticmethod
    def _object_description(owner: Any, *, fallback: str) -> str:
        name = getattr(owner, "name", None)

        if isinstance(name, str) and name.strip():
            return f"{type(owner).__name__} '{name}'"

        return fallback

    # ------------------------------------------------------------------
    # Graph validation
    # ------------------------------------------------------------------

    def _validate_acyclic_graph(
        self,
        graph: dict[str, tuple[str, ...]],
        declaration_kind: str,
    ) -> None:
        """
        Validate a directed inheritance/reference graph using DFS.

        A node may be reached by separate branches without being treated as
        cyclic. Only a node encountered again on the active recursion path
        constitutes a cycle.
        """

        visited: set[str] = set()
        active_path: list[str] = []
        active_names: set[str] = set()

        def visit(node: str) -> None:
            if node in active_names:
                cycle_start = active_path.index(node)
                cycle = active_path[cycle_start:] + [node]
                rendered_cycle = " -> ".join(cycle)

                raise CircularReferenceError(
                    f"{declaration_kind.capitalize()} reference cycle "
                    f"detected: {rendered_cycle}."
                )

            if node in visited:
                return

            active_path.append(node)
            active_names.add(node)

            for referenced_node in graph.get(node, ()):
                visit(referenced_node)

            active_names.remove(node)
            active_path.pop()
            visited.add(node)

        for node_name in graph:
            visit(node_name)


# ---------------------------------------------------------------------------
# Functional entry point
# ---------------------------------------------------------------------------


def validate_semantics(program: AIRProgram) -> None:
    """
    Validate an AIRProgram using ApexForge's default semantic validator.

    This convenience function is suitable for the normal compiler pipeline:

        program = compile_program(ast)
        validate_semantics(program)
        execute(program)
    """

    SemanticValidator().validate(program)