"""
Schema Registry -- Defines what AI-produced artifacts look like.

Every artifact that a :class:`~titan.core.factory.base.FactoryAgent`
produces must conform to a registered :class:`Schema`.  This ensures
structural correctness regardless of which LLM or prompt produced the
content.

The :class:`ArtifactStore` provides versioned persistence with a
defined lifecycle::

    draft -> validated -> approved -> canary -> active -> deprecated
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Result of validating an artifact against its schema."""

    valid: bool
    """Whether the artifact conforms to the schema."""

    errors: list[str] = field(default_factory=list)
    """Human-readable validation error messages."""

    warnings: list[str] = field(default_factory=list)
    """Non-blocking warnings."""


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class Schema:
    """
    A structural definition that constrains what AI can produce.

    Schemas are analogous to database table definitions or JSON Schema
    documents.  They declare the expected fields, types, constraints,
    and required/optional status for a particular artifact kind.

    Attributes
    ----------
    kind : str
        Artifact kind identifier (e.g. ``"DetectionRule"``,
        ``"SubAgentDef"``, ``"WorkflowDAG"``).
    fields : dict[str, dict]
        Field definitions.  Each key is a field name, each value is a
        dict with ``type``, ``required``, ``description``, and optional
        ``constraints``.
    version : int
        Schema version for forward-compatible evolution.
    """

    def __init__(self, kind: str, fields: dict[str, dict], version: int = 1) -> None:
        self.kind = kind
        self.fields = fields
        self.version = version

    def validate(self, artifact: dict) -> ValidationResult:
        """Validate *artifact* against this schema's field definitions.

        Parameters
        ----------
        artifact : dict
            The artifact payload to check.

        Returns
        -------
        ValidationResult
            Pass/fail with detailed error messages.
        """
        ...

    def __repr__(self) -> str:
        return f"Schema(kind={self.kind!r}, version={self.version})"


# ---------------------------------------------------------------------------
# SchemaRegistry
# ---------------------------------------------------------------------------

class SchemaRegistry:
    """Central registry of all artifact schemas.

    Typically initialised once at product boot and shared across the
    brain, factories, and verification pipeline.
    """

    def __init__(self) -> None:
        self._schemas: dict[str, Schema] = {}

    def register(self, schema: Schema) -> None:
        """Register a schema.  Overwrites if the same *kind* already exists.

        Parameters
        ----------
        schema : Schema
            The schema to register.
        """
        ...

    def get(self, kind: str) -> Optional[Schema]:
        """Retrieve a schema by *kind*.

        Parameters
        ----------
        kind : str
            Artifact kind identifier.

        Returns
        -------
        Schema or None
        """
        ...

    def list_all(self) -> list[Schema]:
        """Return all registered schemas."""
        ...


# ---------------------------------------------------------------------------
# ArtifactStore
# ---------------------------------------------------------------------------

class ArtifactStore:
    """Versioned artifact repository with lifecycle management.

    Lifecycle states::

        draft -> validated -> approved -> canary -> active -> deprecated

    Each state transition is an auditable event.
    """

    def __init__(self, backend: Optional[Any] = None) -> None:
        """
        Parameters
        ----------
        backend : object, optional
            Storage backend (database, filesystem, S3, etc.).
            Defaults to an in-memory store for development.
        """
        self._backend = backend
        self._store: dict[str, Any] = {}

    def save(self, artifact: Any) -> str:
        """Persist an artifact and return its unique identifier.

        Parameters
        ----------
        artifact : Artifact
            The artifact to save.

        Returns
        -------
        str
            The artifact's unique identifier.
        """
        ...

    def get(self, artifact_id: str) -> Optional[Any]:
        """Retrieve an artifact by its identifier.

        Parameters
        ----------
        artifact_id : str
            Unique artifact identifier.

        Returns
        -------
        Artifact or None
        """
        ...

    def promote(self, artifact_id: str, to_state: str) -> None:
        """Advance an artifact to the next lifecycle state.

        Parameters
        ----------
        artifact_id : str
            The artifact to promote.
        to_state : str
            Target state (must be a valid successor of the current state).

        Raises
        ------
        ValueError
            If the state transition is invalid.
        """
        ...

    def rollback(self, artifact_id: str) -> None:
        """Roll an artifact back to its previous lifecycle state.

        Parameters
        ----------
        artifact_id : str
            The artifact to roll back.
        """
        ...

    def list_by_state(self, state: str) -> list[Any]:
        """Return all artifacts in the given lifecycle *state*.

        Parameters
        ----------
        state : str
            One of ``"draft"``, ``"validated"``, ``"approved"``,
            ``"canary"``, ``"active"``, ``"deprecated"``.

        Returns
        -------
        list[Artifact]
        """
        ...
