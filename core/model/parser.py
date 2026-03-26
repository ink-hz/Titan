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
        """Convert a parsed dict to ParsedOutput."""
        return ParsedOutput(
            thinking_summary=data.get("thinking_summary", ""),
            tool_calls=data.get("tool_calls", []),
            text=data.get("text", ""),
            components=data.get("components", []),
            new_artifact=data.get("new_artifact"),
            needs_approval=data.get("needs_approval") if isinstance(data.get("needs_approval"), dict) else None,
            solidify_hint=data.get("solidify_hint") if isinstance(data.get("solidify_hint"), dict) else None,
            capability_stats=data.get("capability_stats", {}),
            raw=raw,
        )
