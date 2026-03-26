"""
Factory agents that produce new capabilities under Schema constraints.

A **factory agent** detects capability gaps (e.g. a new alert type with no
detection rule), produces a schema-constrained artifact, and pushes it
through the :class:`~titan.core.verify.pipeline.VerificationPipeline`
before it can go live.

Built-in factory types:

* :class:`RuleFactory` -- produces detection / compliance rules.
* :class:`AgentFactory` -- meta-factory that produces new sub-agent
  definitions (the framework building itself).
* :class:`WorkflowFactory` -- produces deterministic workflow DAGs
  distilled from the solidification engine.
* :class:`CorpusFactory` -- produces curated knowledge corpus entries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class GapReport:
    """Describes a capability gap detected by a factory agent."""

    gap_type: str
    """Category of the gap (e.g. ``"missing_rule"``, ``"no_agent"``)."""

    description: str
    """Natural-language explanation of the gap."""

    evidence: list[dict] = field(default_factory=list)
    """Supporting data points that justify the gap detection."""

    severity: str = "medium"
    """One of ``"low"``, ``"medium"``, ``"high"``, ``"critical"``."""


@dataclass
class Artifact:
    """A schema-constrained artifact produced by a factory agent."""

    id: str
    """Unique artifact identifier."""

    kind: str
    """Schema kind (e.g. ``"DetectionRule"``, ``"SubAgentDef"``)."""

    version: int = 1
    """Monotonically increasing version number."""

    state: str = "draft"
    """Lifecycle state: draft -> validated -> approved -> canary -> active -> deprecated."""

    content: dict[str, Any] = field(default_factory=dict)
    """The actual artifact payload, conforming to its schema."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Provenance, authorship, timestamps, etc."""


@dataclass
class ValidationReport:
    """Result of validating an artifact through the verification pipeline."""

    artifact_id: str
    passed: bool
    gates: list[dict] = field(default_factory=list)
    """Per-gate results: ``[{"gate": "schema", "passed": True, "details": ...}]``."""

    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# FactoryAgent base
# ---------------------------------------------------------------------------

class FactoryAgent:
    """
    Base class for factory agents that produce Schema-constrained artifacts.

    Subclasses must define :pyattr:`artifact_schema` and implement the
    three core methods: :meth:`detect_gap`, :meth:`produce`, and
    :meth:`validate`.

    Attributes
    ----------
    artifact_schema : Schema
        The schema that constrains every artifact this factory produces.
    """

    artifact_schema: Any = None  # Schema instance set by subclasses

    async def detect_gap(self, context: dict) -> GapReport:
        """Identify a capability gap by analysing the current environment.

        Parameters
        ----------
        context : dict
            Environmental context (recent alerts, existing rules, etc.).

        Returns
        -------
        GapReport
            A report describing the detected gap.
        """
        ...

    async def produce(self, gap: GapReport) -> Artifact:
        """Produce a new artifact to fill the identified *gap*.

        The artifact **must** conform to :pyattr:`artifact_schema`.

        Parameters
        ----------
        gap : GapReport
            The gap report that motivates this production.

        Returns
        -------
        Artifact
            A draft artifact ready for verification.
        """
        ...

    async def validate(self, artifact: Artifact) -> ValidationReport:
        """Run the full verification pipeline on *artifact*.

        Parameters
        ----------
        artifact : Artifact
            The artifact to verify.

        Returns
        -------
        ValidationReport
            Detailed report with per-gate results.
        """
        ...


# ---------------------------------------------------------------------------
# Concrete factory stubs
# ---------------------------------------------------------------------------

class RuleFactory(FactoryAgent):
    """Factory that produces detection and compliance rules.

    Example artifact kinds: ``"DetectionRule"``, ``"CompliancePolicy"``.
    """
    ...


class AgentFactory(FactoryAgent):
    """Meta-factory that produces new sub-agent definitions.

    This is how Titan builds *itself* -- the framework can propose new
    specialised agents when it detects recurring task patterns that no
    existing agent handles well.
    """
    ...


class WorkflowFactory(FactoryAgent):
    """Factory that produces deterministic workflow DAGs.

    Typically driven by the :class:`~titan.core.solidify.engine.SolidifyEngine`
    which discovers repeating agent traces and distils them into fixed
    workflows.
    """
    ...


class CorpusFactory(FactoryAgent):
    """Factory that produces curated knowledge corpus entries.

    Transforms raw operational data (runbooks, post-mortems, vendor docs)
    into structured, indexed knowledge artifacts.
    """
    ...
