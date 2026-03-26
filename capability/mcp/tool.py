"""
MCP Tool registration and management.

Every atomic capability in a Titan product is exposed as an
:class:`MCPTool` -- a self-describing function with a JSON Schema
parameter definition, a trust level, and a category tag.

Tool categories:

* **perception** -- Read-only data retrieval (query logs, fetch alerts).
* **decision** -- Analysis and classification (score risk, triage).
* **execution** -- State-changing actions (block IP, isolate host).
* **presentation** -- Output formatting (render report, build chart).
* **memory** -- Long-term storage operations (save finding, update KB).

The :class:`ToolRegistry` handles auto-discovery from a directory of
tool modules, and can export tool descriptions formatted for LLM system
prompts or auto-generated CLI commands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from titan.core.trust.model import TrustLevel


# ---------------------------------------------------------------------------
# MCPTool
# ---------------------------------------------------------------------------

@dataclass
class MCPTool:
    """An atomic capability exposed as an MCP Tool.

    Attributes
    ----------
    name : str
        Unique tool identifier (e.g. ``"alert.query"``, ``"firewall.block_ip"``).
    description : str
        Natural-language description optimised for LLM comprehension.
    parameters : dict
        JSON Schema defining the tool's input parameters.
    trust_level : TrustLevel
        How much human oversight this tool requires.
    category : str
        One of ``"perception"``, ``"decision"``, ``"execution"``,
        ``"presentation"``, ``"memory"``.
    handler : Callable, optional
        The async function that implements the tool logic.
    """

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    trust_level: TrustLevel = TrustLevel.AUTONOMOUS
    category: str = "perception"
    handler: Optional[Callable] = None

    async def execute(self, args: dict) -> dict:
        """Execute the tool with the given *args*.

        Parameters
        ----------
        args : dict
            Input arguments conforming to :pyattr:`parameters` schema.

        Returns
        -------
        dict
            Tool execution result.

        Raises
        ------
        NotImplementedError
            If no handler is registered.
        """
        ...


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """Registry for discovering, storing, and querying MCP tools.

    Example::

        registry = ToolRegistry()
        registry.discover("./tools/")
        print(registry.list_for_llm())
    """

    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        """Register a single MCP tool.

        Parameters
        ----------
        tool : MCPTool
            The tool to register.
        """
        ...

    def get(self, name: str) -> Optional[MCPTool]:
        """Retrieve a tool by name.

        Parameters
        ----------
        name : str
            The tool's unique identifier.

        Returns
        -------
        MCPTool or None
        """
        ...

    def discover(self, tools_dir: str) -> int:
        """Auto-discover tools from a directory of Python modules.

        Each module that defines an ``MCPTool`` instance or subclass is
        loaded and registered.

        Parameters
        ----------
        tools_dir : str
            Path to the directory containing tool modules.

        Returns
        -------
        int
            Number of tools discovered and registered.
        """
        ...

    def list_for_llm(self) -> str:
        """Format all registered tool descriptions for an LLM system prompt.

        Returns a structured text block that helps the LLM understand
        which tools are available, what they do, and what parameters
        they accept.

        Returns
        -------
        str
            Formatted tool listing.
        """
        ...

    def list_by_category(self, category: str) -> list[MCPTool]:
        """Return all tools in the given *category*.

        Parameters
        ----------
        category : str
            One of ``"perception"``, ``"decision"``, ``"execution"``,
            ``"presentation"``, ``"memory"``.

        Returns
        -------
        list[MCPTool]
        """
        ...

    def generate_cli(self) -> str:
        """Auto-generate CLI command definitions from registered tools.

        Produces a Click/Typer-compatible command group source string
        that mirrors the tool registry, enabling terminal-based access
        to every MCP tool.

        Returns
        -------
        str
            Python source code for a CLI command group.
        """
        ...
