"""
Titan Agent Brain -- The operating system of a Super-Agent product.

The Brain understands user intent, plans tasks, dispatches to sub-agents,
and assembles results.  It runs a **TAOR loop** (Think-Act-Observe-Repeat)
that mirrors how a senior human operator works:

    1. **Think**   -- Interpret user intent, recall relevant memory, draft a plan.
    2. **Act**     -- Dispatch tool calls or delegate to sub-agents.
    3. **Observe** -- Collect results, evaluate quality & trust constraints.
    4. **Repeat**  -- Decide whether to refine, escalate, or respond.

Typical bootstrap::

    brain = AgentBrain(model="deepseek-r1")
    brain.register_tools("./tools/")
    brain.register_agents([InvestigatorAgent, PolicyAgent])
    brain.register_factories([RuleFactory])
    brain.enable_solidify()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from titan.core.agents.base import SubAgent, AgentRegistry
    from titan.core.factory.base import FactoryAgent
    from titan.core.solidify.engine import SolidifyEngine
    from titan.core.trust.model import TrustLevel
    from titan.capability.mcp.tool import ToolRegistry


# ---------------------------------------------------------------------------
# Data classes returned by the brain
# ---------------------------------------------------------------------------

@dataclass
class BrainResponse:
    """Structured response produced at the end of a TAOR loop iteration."""

    answer: str
    """Natural-language answer ready for the end user."""

    tool_calls: list[dict] = field(default_factory=list)
    """Ordered list of tool invocations that were executed during this turn."""

    delegated_to: list[str] = field(default_factory=list)
    """Names of sub-agents that participated in this turn."""

    confidence: float = 1.0
    """Self-assessed confidence in [0, 1]."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Arbitrary key-value pairs (trace ids, latency, token usage, etc.)."""


# ---------------------------------------------------------------------------
# AgentBrain
# ---------------------------------------------------------------------------

class AgentBrain:
    """
    Core agent brain that drives the entire super-agent product.

    The brain is the single entry-point that product code interacts with.
    It owns the TAOR loop, the tool registry, the sub-agent registry,
    factory agents, and the solidification engine.

    Example::

        brain = AgentBrain(model="deepseek-r1")
        brain.register_tools("./tools/")
        brain.register_agents([InvestigatorAgent, PolicyAgent])
        brain.register_factories([RuleFactory])
        brain.enable_solidify()

    Parameters
    ----------
    model : str
        Identifier of the backing LLM (e.g. ``"deepseek-r1"``, ``"gpt-4o"``).
    system_prompt : str, optional
        Base system prompt injected before every LLM call.
    memory : MemoryStore, optional
        Long-term memory backend (vector DB, graph store, etc.).
    """

    def __init__(
        self,
        model: str,
        system_prompt: Optional[str] = None,
        memory: Optional[Any] = None,
    ) -> None:
        self.model = model
        self.system_prompt = system_prompt
        self.memory = memory
        self._tool_registry: Optional[ToolRegistry] = None
        self._agent_registry: Optional[AgentRegistry] = None
        self._factories: list[FactoryAgent] = []
        self._solidify_engine: Optional[SolidifyEngine] = None

    # -- Registration -------------------------------------------------------

    def register_tools(self, tools_path: str) -> None:
        """Auto-discover and register MCP tools from *tools_path* directory.

        Each Python module in the directory that exposes an ``MCPTool``
        subclass is instantiated and added to the internal tool registry.

        Parameters
        ----------
        tools_path : str
            Filesystem path to a directory of tool modules.
        """
        ...

    def register_agents(self, agents: list) -> None:
        """Register sub-agents for task delegation.

        Parameters
        ----------
        agents : list[type[SubAgent]]
            A list of ``SubAgent`` **classes** (not instances).  The brain
            will instantiate them with the appropriate context.
        """
        ...

    def register_factories(self, factories: list) -> None:
        """Register factory agents for capability production.

        Factory agents can autonomously create new rules, workflows,
        sub-agents, or corpus entries -- always under schema constraints.

        Parameters
        ----------
        factories : list[type[FactoryAgent]]
            A list of ``FactoryAgent`` **classes**.
        """
        ...

    def enable_solidify(self, analyzer: Optional[Any] = None) -> None:
        """Enable the experience solidification engine.

        When enabled, every TAOR loop execution is traced.  The engine
        periodically analyses traces, discovers repeating patterns, and
        proposes deterministic workflow DAGs that replace costly LLM calls.

        Parameters
        ----------
        analyzer : object, optional
            Custom pattern analyzer.  Falls back to the built-in
            ``SolidifyEngine`` when *None*.
        """
        ...

    # -- Core loop ----------------------------------------------------------

    async def process_intent(
        self,
        user_message: str,
        context: Optional[dict] = None,
    ) -> BrainResponse:
        """Run the main TAOR loop for a single user turn.

        1. **Think** -- Parse *user_message*, retrieve memory, create a plan.
        2. **Act** -- Execute tool calls / delegate to sub-agents.
        3. **Observe** -- Validate results against trust constraints.
        4. **Repeat** -- If quality is insufficient, loop; otherwise respond.

        Parameters
        ----------
        user_message : str
            Raw message from the end user.
        context : dict, optional
            Session or environmental context (user role, active alerts, etc.).

        Returns
        -------
        BrainResponse
            Structured response containing the answer, tool traces, and
            metadata.
        """
        ...

    # -- Background ---------------------------------------------------------

    async def run_background_tasks(self) -> None:
        """Run autonomous background monitoring tasks.

        This includes proactive alert triage, scheduled data pulls, and
        factory-agent gap detection.  Designed to be called from an
        ``asyncio`` event loop or a background worker.
        """
        ...
