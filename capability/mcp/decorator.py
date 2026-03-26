"""
Titan Tool Decorator — Register functions as MCP Tools with one decorator.

Usage:
    @tool(
        name="alert.query",
        description="Query security alerts by severity and time range",
        category="perception",
        trust_level=TrustLevel.AUTONOMOUS,
    )
    async def query_alerts(severity: str = "all", timerange: str = "24h") -> dict:
        '''Query alerts from the alert database.'''
        return {"total": 247, "critical": 3}
"""

import inspect
import functools
from typing import Callable, Optional, Dict, Any, get_type_hints

from ...core.trust.model import TrustLevel


# Global tool registry for auto-discovery
_registered_tools: Dict[str, "ToolDefinition"] = {}


class ToolDefinition:
    """A registered tool with metadata."""
    def __init__(self, func: Callable, name: str, description: str, category: str,
                 trust_level: TrustLevel, parameters: dict):
        self.func = func
        self.name = name
        self.description = description
        self.category = category
        self.trust_level = trust_level
        self.parameters = parameters

    async def execute(self, **kwargs) -> Any:
        """Execute the tool function."""
        if inspect.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        return self.func(**kwargs)

    def to_llm_description(self) -> str:
        """Format as description for LLM system prompt."""
        params_str = ", ".join(f"{k}: {v.get('type', 'any')}" for k, v in self.parameters.items())
        trust_label = {
            TrustLevel.AUTONOMOUS: "auto-execute",
            TrustLevel.REPORT_AFTER: "auto + report",
            TrustLevel.APPROVE_BEFORE: "needs approval",
            TrustLevel.HUMAN_ONLY: "human only",
        }.get(self.trust_level, "unknown")
        return f"- {self.name}({params_str}) → {self.description} [{self.category}, {trust_label}]"

    def to_json_schema(self) -> dict:
        """Export as JSON Schema for MCP protocol."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {"type": "object", "properties": self.parameters},
            "metadata": {"category": self.category, "trust_level": self.trust_level.name},
        }

    def to_cli_command(self) -> str:
        """Generate CLI command string."""
        parts = self.name.replace(".", " ")
        flags = " ".join(f"--{k} <{v.get('type', 'str')}>" for k, v in self.parameters.items())
        return f"titan {parts} {flags}"


def tool(
    name: str,
    description: str,
    category: str = "perception",
    trust_level: TrustLevel = TrustLevel.AUTONOMOUS,
    parameters: dict = None,
):
    """
    Decorator to register a function as a Titan MCP Tool.

    Args:
        name: Tool name (e.g., "alert.query")
        description: Natural language description for LLM
        category: perception | decision | execution | presentation | memory
        trust_level: TrustLevel enum value
        parameters: JSON Schema for parameters (auto-inferred if not provided)

    Example:
        @tool(name="alert.query", description="Query alerts", category="perception")
        async def query_alerts(severity: str = "all", timerange: str = "24h") -> dict:
            return {"total": 247}
    """
    def decorator(func: Callable):
        # Auto-infer parameters from function signature if not provided
        params = parameters
        if params is None:
            params = _infer_parameters(func)

        tool_def = ToolDefinition(
            func=func, name=name, description=description,
            category=category, trust_level=trust_level, parameters=params,
        )
        _registered_tools[name] = tool_def

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await tool_def.execute(**kwargs)

        wrapper._tool_definition = tool_def
        return wrapper

    return decorator


def _infer_parameters(func: Callable) -> dict:
    """Infer JSON Schema parameters from function signature."""
    sig = inspect.signature(func)
    hints = get_type_hints(func) if hasattr(func, '__annotations__') else {}
    params = {}
    type_map = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        py_type = hints.get(param_name, str)
        json_type = type_map.get(py_type, "string")
        param_def = {"type": json_type}
        if param.default is not inspect.Parameter.empty:
            param_def["default"] = param.default
        params[param_name] = param_def

    return params


def get_registered_tools() -> Dict[str, ToolDefinition]:
    """Get all registered tools."""
    return _registered_tools.copy()


def discover_tools(directory: str):
    """
    Auto-discover tools by importing all Python files in a directory.
    Each file that uses @tool decorator will auto-register its tools.
    """
    import importlib
    import sys
    from pathlib import Path

    tool_dir = Path(directory)
    if not tool_dir.exists():
        return

    for py_file in tool_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        module_name = f"titan_tools.{py_file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)


def generate_llm_tool_prompt(tools: Dict[str, ToolDefinition] = None) -> str:
    """
    Generate the tool description section for LLM system prompt.
    Groups tools by category with trust level annotations.
    """
    if tools is None:
        tools = _registered_tools

    categories = {}
    for t in tools.values():
        categories.setdefault(t.category, []).append(t)

    category_labels = {
        "perception": "👁️ Perception (auto-execute)",
        "decision": "🧠 Decision (auto-execute)",
        "execution": "⚡ Execution (needs approval)",
        "presentation": "📊 Presentation (on-demand)",
        "memory": "💾 Memory (experience)",
    }

    lines = ["## Available Tools\n"]
    for cat, label in category_labels.items():
        if cat in categories:
            lines.append(f"### {label}")
            for t in categories[cat]:
                lines.append(t.to_llm_description())
            lines.append("")

    return "\n".join(lines)


def generate_cli_commands(tools: Dict[str, ToolDefinition] = None) -> str:
    """Generate CLI help text from registered tools."""
    if tools is None:
        tools = _registered_tools

    lines = ["Available commands:\n"]
    for t in tools.values():
        lines.append(f"  {t.to_cli_command()}")
        lines.append(f"    {t.description}")
        lines.append("")

    return "\n".join(lines)
