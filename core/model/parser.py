"""
Model Output Parser — Robust parsing of LLM structured output.

Handles JSON extraction from model responses with fallback strategies.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List


@dataclass
class ParsedOutput:
    """Parsed and structured model output."""
    thinking_summary: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    text: str = ""
    components: List[Dict] = field(default_factory=list)
    new_artifact: Optional[Dict] = None
    needs_approval: Optional[Dict] = None
    solidify_hint: Optional[Dict] = None
    capability_stats: Dict = field(default_factory=lambda: {
        "perception": 0, "decision": 0, "execution": 0, "presentation": 0, "memory": 0
    })
    raw: str = ""


class OutputParser:
    """
    Parse LLM output into structured format with robust fallback.

    Strategies:
    1. Try direct JSON parse
    2. Try extracting JSON from markdown code blocks
    3. Try extracting JSON from mixed text
    4. Fallback: treat entire output as text response

    Usage:
        parser = OutputParser()
        result = parser.parse(raw_model_output)
        # result.tool_calls, result.text, result.components, etc.
    """

    def parse(self, raw: str) -> ParsedOutput:
        """Parse raw model output into structured ParsedOutput."""
        clean = raw.strip()

        # Strategy 1: Direct JSON
        try:
            data = json.loads(clean)
            return self._from_dict(data, raw)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code blocks
        code_block = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', clean)
        if code_block:
            try:
                data = json.loads(code_block.group(1))
                return self._from_dict(data, raw)
            except json.JSONDecodeError:
                pass

        # Strategy 3: Find first { ... } block
        brace_match = re.search(r'\{[\s\S]*\}', clean)
        if brace_match:
            try:
                data = json.loads(brace_match.group(0))
                return self._from_dict(data, raw)
            except json.JSONDecodeError:
                pass

        # Strategy 4: Fallback — treat as plain text
        return ParsedOutput(text=clean, raw=raw)

    def _from_dict(self, data: dict, raw: str) -> ParsedOutput:
        """Convert a parsed dict to ParsedOutput with robust type checking."""
        # Ensure tool_calls is always a list of dicts
        tool_calls_raw = data.get("tool_calls", [])
        if not isinstance(tool_calls_raw, list):
            tool_calls_raw = []
        tool_calls = [tc for tc in tool_calls_raw if isinstance(tc, dict)]

        # Ensure components is always a list of dicts
        components_raw = data.get("components", [])
        if not isinstance(components_raw, list):
            components_raw = []
        components = [c for c in components_raw if isinstance(c, dict)]

        # Ensure capability_stats has all required keys
        default_stats = {"perception": 0, "decision": 0, "execution": 0, "presentation": 0, "memory": 0}
        stats_raw = data.get("capability_stats")
        if isinstance(stats_raw, dict):
            # Merge with defaults, ensuring all keys exist and values are ints
            for key in default_stats:
                val = stats_raw.get(key, 0)
                default_stats[key] = int(val) if isinstance(val, (int, float)) else 0
        capability_stats = default_stats

        # Safely extract optional dict fields
        needs_approval = data.get("needs_approval")
        if not isinstance(needs_approval, dict):
            # Handle boolean true (model sometimes outputs needs_approval: true)
            needs_approval = None

        solidify_hint = data.get("solidify_hint")
        if not isinstance(solidify_hint, dict):
            solidify_hint = None

        new_artifact = data.get("new_artifact")
        if not isinstance(new_artifact, dict):
            new_artifact = None

        return ParsedOutput(
            thinking_summary=str(data.get("thinking_summary", "")),
            tool_calls=tool_calls,
            text=str(data.get("text", "")),
            components=components,
            new_artifact=new_artifact,
            needs_approval=needs_approval,
            solidify_hint=solidify_hint,
            capability_stats=capability_stats,
            raw=raw,
        )
