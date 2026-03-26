"""
Base class for all sub-agents in Titan.

A **sub-agent** is a specialised worker that the :class:`AgentBrain` can
delegate tasks to.  Each sub-agent operates in an isolated context with
scoped tool permissions (perception / decision / execution).

Example sub-agents in a security product:

* ``InvestigatorAgent`` -- triages alerts, queries logs, builds timelines.
* ``PolicyAgent`` -- evaluates compliance rules, suggests remediations.
* ``ResponseAgent`` -- executes containment actions (with human approval).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A unit of work assigned by the brain to a sub-agent."""

    id: str
    """Unique task identifier."""

    description: str
    """Natural-language description of what needs to be done."""

    parameters: dict[str, Any] = field(default_factory=dict)
    """Structured inputs for the task."""

    parent_task_id: Optional[str] = None
    """If this task was decomposed from a larger task."""


@dataclass
class AgentResult:
    """Result returned by a sub-agent after executing a task."""

    task_id: str
    """Identifier of the completed task."""

    success: bool
    """Whether the task completed successfully."""

    output: Any = None
    """Structured or free-text output produced by the agent."""

    tool_calls: list[dict] = field(default_factory=list)
    """Ordered list of tool invocations the agent made."""

    error: Optional[str] = None
    """Error message if ``success`` is *False*."""


# ---------------------------------------------------------------------------
# SubAgent
# ---------------------------------------------------------------------------

class SubAgent:
    """
    A specialised sub-agent with isolated context and scoped permissions.

    Subclasses must set :pyattr:`name` and :pyattr:`role`, and implement
    :meth:`execute`.

    Attributes
    ----------
    name : str
        Human-readable agent name (e.g. ``"InvestigatorAgent"``).
    role : str
        One-line description of the agent's responsibility.
    tools : list[str]
        Names of MCP tools this agent is allowed to call.
    permissions : dict[str, bool]
        Capability scopes: ``{"perception": True, "decision": True,
        "execution": False}``.
    """

    name: str = ""
    role: str = ""
    tools: list[str] = []
    permissions: dict[str, bool] = {
        "perception": True,
        "decision": True,
        "execution": False,
    }

    async def execute(self, task: Task, context: dict) -> AgentResult:
        """Execute the given *task* within the provided *context*.

        Parameters
        ----------
        task : Task
            The unit of work to perform.
        context : dict
            Environmental context (active session, user info, memory, etc.).

        Returns
        -------
        AgentResult
            Structured result of the execution.
        """
        ...


# ---------------------------------------------------------------------------
# AgentRegistry
# ---------------------------------------------------------------------------

class AgentRegistry:
    """Manages registration and discovery of sub-agents.

    The brain delegates to the registry when it needs to find the best agent
    for a particular task.
    """

    def __init__(self) -> None:
        self._agents: dict[str, SubAgent] = {}

    def register(self, agent: SubAgent) -> None:
        """Register a sub-agent instance.

        Parameters
        ----------
        agent : SubAgent
            An instantiated sub-agent.
        """
        ...

    def get(self, name: str) -> Optional[SubAgent]:
        """Retrieve a registered agent by name.

        Parameters
        ----------
        name : str
            The agent's ``name`` attribute.

        Returns
        -------
        SubAgent or None
        """
        ...

    def handoff(self, task: Task) -> SubAgent:
        """Select the best agent for *task* based on role matching.

        Uses the task description and agent roles to determine the most
        suitable sub-agent.  Falls back to a generic agent if no strong
        match is found.

        Parameters
        ----------
        task : Task
            The task that needs an owner.

        Returns
        -------
        SubAgent
            The selected agent.
        """
        ...

    def list_all(self) -> list[SubAgent]:
        """Return all registered sub-agents."""
        ...
