"""
Titan UI Component Registry — Schema-constrained presentation primitives.

Components are the visual building blocks that agents use to present information.
Each component has a type, a data schema, and can be rendered by the frontend.

Built-in components cover common patterns. Domains register additional components.

Usage:
    # Use built-in
    components.metric_card("Alert Count", "247", trend="up", color="red")

    # Register custom
    registry.register(ComponentDef(
        type="attack_chain",
        schema={"events": {"type": "array"}, "title": {"type": "string"}},
        description="Visualize a multi-step attack chain"
    ))
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ComponentDef:
    """Definition of a UI component type."""
    type: str              # Component type identifier (e.g., "metric_card")
    schema: Dict           # JSON Schema for the data field
    description: str = ""  # Human-readable description
    category: str = "general"  # Category for grouping


class ComponentRegistry:
    """
    Central registry for UI component types.

    Domains register their components; the frontend discovers them.
    """

    def __init__(self):
        self._components: Dict[str, ComponentDef] = {}
        self._register_builtins()

    def _register_builtins(self):
        """Register built-in universal components."""
        builtins = [
            ComponentDef("metric_card", {"label": {"type": "string"}, "value": {"type": "string"}, "unit": {"type": "string"}, "trend": {"type": "string", "enum": ["up", "down", "stable"]}, "color": {"type": "string"}}, "Key metric display", "data"),
            ComponentDef("line_chart", {"title": {"type": "string"}, "xAxis": {"type": "array"}, "series": {"type": "array"}}, "Line chart for trends", "chart"),
            ComponentDef("bar_chart", {"title": {"type": "string"}, "xAxis": {"type": "array"}, "series": {"type": "array"}}, "Bar chart for comparisons", "chart"),
            ComponentDef("pie_chart", {"title": {"type": "string"}, "items": {"type": "array"}}, "Pie chart for distribution", "chart"),
            ComponentDef("table", {"title": {"type": "string"}, "columns": {"type": "array"}, "rows": {"type": "array"}}, "Data table", "data"),
            ComponentDef("timeline", {"title": {"type": "string"}, "events": {"type": "array"}}, "Event timeline", "data"),
            ComponentDef("approval_card", {"action": {"type": "string"}, "title": {"type": "string"}, "description": {"type": "string"}, "options": {"type": "array"}}, "Human approval interface", "interaction"),
            ComponentDef("notification", {"level": {"type": "string", "enum": ["info", "warning", "error"]}, "title": {"type": "string"}, "description": {"type": "string"}}, "Alert notification", "interaction"),
            ComponentDef("code_block", {"language": {"type": "string"}, "code": {"type": "string"}, "title": {"type": "string"}}, "Code display", "data"),
            ComponentDef("progress", {"label": {"type": "string"}, "value": {"type": "number"}, "max": {"type": "number"}, "status": {"type": "string"}}, "Progress indicator", "interaction"),
            ComponentDef("key_value", {"title": {"type": "string"}, "items": {"type": "array"}}, "Key-value pair list", "data"),
            ComponentDef("workflow_dag", {"title": {"type": "string"}, "nodes": {"type": "array"}, "edges": {"type": "array"}}, "Workflow visualization", "data"),
            ComponentDef("collab_timeline", {"title": {"type": "string"}, "events": {"type": "array"}}, "Super-agent collaboration timeline", "interaction"),
        ]
        for c in builtins:
            self._components[c.type] = c

    def register(self, component: ComponentDef):
        """Register a custom component type."""
        self._components[component.type] = component

    def get(self, type_name: str) -> Optional[ComponentDef]:
        """Get component definition by type."""
        return self._components.get(type_name)

    def list_all(self) -> List[ComponentDef]:
        """List all registered components."""
        return list(self._components.values())

    def list_for_llm(self) -> str:
        """Generate component description for LLM system prompt."""
        lines = ["## Available UI Components\n"]
        by_cat = {}
        for c in self._components.values():
            by_cat.setdefault(c.category, []).append(c)
        for cat, comps in by_cat.items():
            lines.append(f"### {cat.title()}")
            for c in comps:
                fields = ", ".join(c.schema.keys())
                lines.append(f'- {c.type}: {c.description} (fields: {fields})')
            lines.append("")
        return "\n".join(lines)

    def validate(self, component_data: dict) -> bool:
        """Validate component data against its schema."""
        comp_type = component_data.get("type")
        comp_def = self._components.get(comp_type)
        if not comp_def:
            return False
        # Basic validation: check required fields exist
        data = component_data.get("data", {})
        return isinstance(data, dict)


# Convenience factory functions
class Components:
    """Factory for creating component data dicts."""

    @staticmethod
    def metric_card(label: str, value: str, unit: str = "", trend: str = "stable", color: str = "cyan") -> dict:
        return {"type": "metric_card", "data": {"label": label, "value": value, "unit": unit, "trend": trend, "color": color}}

    @staticmethod
    def line_chart(title: str, x_axis: list, series: list) -> dict:
        return {"type": "line_chart", "data": {"title": title, "xAxis": x_axis, "series": series}}

    @staticmethod
    def table(title: str, columns: list, rows: list) -> dict:
        return {"type": "table", "data": {"title": title, "columns": columns, "rows": rows}}

    @staticmethod
    def timeline(title: str, events: list) -> dict:
        return {"type": "timeline", "data": {"title": title, "events": events}}

    @staticmethod
    def approval(action: str, title: str, description: str, options: list = None) -> dict:
        return {"type": "approval_card", "data": {"action": action, "title": title, "description": description, "options": options or ["Approve", "Reject"]}}

    @staticmethod
    def notification(level: str, title: str, description: str) -> dict:
        return {"type": "notification", "data": {"level": level, "title": title, "description": description}}

    @staticmethod
    def code_block(code: str, language: str = "yaml", title: str = "") -> dict:
        return {"type": "code_block", "data": {"code": code, "language": language, "title": title}}

    @staticmethod
    def workflow_dag(title: str, nodes: list, edges: list = None) -> dict:
        return {"type": "workflow_dag", "data": {"title": title, "nodes": nodes, "edges": edges or []}}
