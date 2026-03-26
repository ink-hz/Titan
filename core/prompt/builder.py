"""
Titan System Prompt Builder — Dynamic prompt assembly engine.

Builds the system prompt by composing: role definition + tool descriptions +
component specs + data context + behavioral rules + domain-specific additions.

Usage:
    builder = PromptBuilder()
    builder.set_role("You are a DevOps super-agent...")
    builder.add_tools(tool_registry)           # Auto-generate tool descriptions
    builder.add_components(component_registry)  # Auto-generate component specs
    builder.add_context("alerts", alerts_json)  # Inject live data
    builder.add_rules(["Only output JSON", "Be concise"])
    prompt = builder.build()
"""

from typing import List, Dict, Optional


class PromptBuilder:
    """
    Dynamic system prompt assembly.

    Composes prompt from modular sections, each can be updated independently.
    """

    def __init__(self):
        self._role: str = ""
        self._tool_section: str = ""
        self._component_section: str = ""
        self._context_sections: Dict[str, str] = {}
        self._rules: List[str] = []
        self._output_format: str = ""
        self._custom_sections: Dict[str, str] = {}

    def set_role(self, role_description: str) -> "PromptBuilder":
        """Set the agent's role definition."""
        self._role = role_description
        return self

    def add_tools(self, tool_registry) -> "PromptBuilder":
        """Generate tool descriptions from registry."""
        if hasattr(tool_registry, 'list_for_llm'):
            self._tool_section = tool_registry.list_for_llm()
        elif hasattr(tool_registry, 'generate_llm_tool_prompt'):
            self._tool_section = tool_registry.generate_llm_tool_prompt()
        return self

    def add_tools_raw(self, tools_text: str) -> "PromptBuilder":
        """Set tool descriptions from raw text."""
        self._tool_section = tools_text
        return self

    def add_components(self, component_registry) -> "PromptBuilder":
        """Generate component specs from registry."""
        if hasattr(component_registry, 'list_for_llm'):
            self._component_section = component_registry.list_for_llm()
        return self

    def add_context(self, name: str, data) -> "PromptBuilder":
        """Add a data context section (will be JSON-serialized if not string)."""
        import json
        if isinstance(data, str):
            self._context_sections[name] = data
        else:
            self._context_sections[name] = json.dumps(data, ensure_ascii=False, indent=2)
        return self

    def add_rules(self, rules: List[str]) -> "PromptBuilder":
        """Add behavioral rules."""
        self._rules.extend(rules)
        return self

    def set_output_format(self, format_spec: str) -> "PromptBuilder":
        """Set the expected output format specification."""
        self._output_format = format_spec
        return self

    def add_section(self, name: str, content: str) -> "PromptBuilder":
        """Add a custom section."""
        self._custom_sections[name] = content
        return self

    def build(self) -> str:
        """Assemble the complete system prompt."""
        sections = []

        if self._role:
            sections.append(f"## Role\n{self._role}")

        if self._tool_section:
            sections.append(self._tool_section)

        if self._component_section:
            sections.append(self._component_section)

        if self._context_sections:
            sections.append("## Current Data")
            for name, data in self._context_sections.items():
                sections.append(f"### {name}\n{data}")

        for name, content in self._custom_sections.items():
            sections.append(f"## {name}\n{content}")

        if self._output_format:
            sections.append(f"## Output Format\n{self._output_format}")

        if self._rules:
            sections.append("## Rules")
            for i, rule in enumerate(self._rules, 1):
                sections.append(f"{i}. {rule}")

        return "\n\n".join(sections)
