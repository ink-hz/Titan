"""
Titan AG-UI Event Stream Protocol

Defines all event types for real-time Agent↔Frontend communication via SSE.
This is the core communication layer for Agent-Native UI.

Event Categories:
- Lifecycle: RUN_STARTED, RUN_FINISHED
- Thinking: THINKING_CONTENT (real-time reasoning stream)
- Text: TEXT_MESSAGE_START/CONTENT/END (streamed response)
- Tools: TOOL_CALL_START/END (tool execution lifecycle)
- UI: STATE_DELTA (component updates), APPROVAL_REQUEST
- Agent: AGENT_HANDOFF, AGENT_COLLAB
- System: SOLIDIFY_HINT, CAPABILITY_STATS, EVOLUTION_UPDATE
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class EventType(str, Enum):
    # Lifecycle
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"

    # Thinking stream
    THINKING_CONTENT = "THINKING_CONTENT"

    # Text message (streamed)
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"

    # Tool calls
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_END = "TOOL_CALL_END"

    # UI state
    STATE_DELTA = "STATE_DELTA"
    APPROVAL_REQUEST = "APPROVAL_REQUEST"

    # Agent collaboration
    AGENT_HANDOFF = "AGENT_HANDOFF"
    AGENT_COLLAB = "AGENT_COLLAB"

    # System events
    SOLIDIFY_HINT = "SOLIDIFY_HINT"
    CAPABILITY_STATS = "CAPABILITY_STATS"
    EVOLUTION_UPDATE = "EVOLUTION_UPDATE"
    BACKGROUND_TASK = "BACKGROUND_TASK"


def sse_encode(event: dict) -> str:
    """Encode an event dict as SSE data line."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


class EventEmitter:
    """
    AG-UI Event emitter for Server-Sent Events streaming.

    Usage:
        emitter = EventEmitter()
        yield emitter.run_started()
        yield emitter.thinking("Analyzing user intent...")
        yield emitter.tool_start("alert.query", "perception", {"severity": "high"})
        yield emitter.tool_end(tool_id, "Found 247 alerts", 23)
        yield emitter.text_start()
        yield emitter.text_content("Here are the results...")
        yield emitter.text_end()
        yield emitter.state_delta([{"type": "line_chart", "data": {...}}])
        yield emitter.run_finished()
    """

    def run_started(self) -> str:
        return sse_encode({"type": EventType.RUN_STARTED, "runId": str(uuid.uuid4())})

    def run_finished(self) -> str:
        return sse_encode({"type": EventType.RUN_FINISHED})

    def thinking(self, content: str) -> str:
        return sse_encode({"type": EventType.THINKING_CONTENT, "content": content})

    def text_start(self, message_id: str = None) -> str:
        mid = message_id or str(uuid.uuid4())
        return sse_encode({"type": EventType.TEXT_MESSAGE_START, "messageId": mid})

    def text_content(self, message_id: str, content: str) -> str:
        return sse_encode({"type": EventType.TEXT_MESSAGE_CONTENT, "messageId": message_id, "content": content})

    def text_end(self, message_id: str) -> str:
        return sse_encode({"type": EventType.TEXT_MESSAGE_END, "messageId": message_id})

    def tool_start(self, name: str, category: str, args: dict = None, tool_id: str = None) -> str:
        tid = tool_id or str(uuid.uuid4())
        return sse_encode({
            "type": EventType.TOOL_CALL_START,
            "toolCallId": tid,
            "name": name,
            "category": category,
            "arguments": json.dumps(args or {}, ensure_ascii=False),
        })

    def tool_end(self, tool_id: str, result: str, duration_ms: int = 0) -> str:
        return sse_encode({
            "type": EventType.TOOL_CALL_END,
            "toolCallId": tool_id,
            "result": result,
            "duration_ms": duration_ms,
        })

    def state_delta(self, components: list) -> str:
        return sse_encode({"type": EventType.STATE_DELTA, "delta": {"components": components}})

    def approval_request(self, action: str, title: str, description: str, options: list = None) -> str:
        return sse_encode({
            "type": EventType.APPROVAL_REQUEST,
            "action": action,
            "title": title,
            "description": description,
            "options": options or ["Approve", "Reject"],
        })

    def agent_handoff(self, from_agent: str, to_agent: str, reason: str) -> str:
        return sse_encode({
            "type": EventType.AGENT_HANDOFF,
            "from": from_agent,
            "to": to_agent,
            "reason": reason,
        })

    def agent_collab(self, target: str, intent: str, status: str, conclusion: str = None) -> str:
        return sse_encode({
            "type": EventType.AGENT_COLLAB,
            "collab": {"target": target, "intent": intent, "status": status, "conclusion": conclusion},
        })

    def solidify_hint(self, pattern_type: str, count: int, similarity: float, suggestion: str) -> str:
        return sse_encode({
            "type": EventType.SOLIDIFY_HINT,
            "hint": {"pattern_type": pattern_type, "count": count, "similarity": similarity, "suggestion": suggestion},
        })

    def capability_stats(self, stats: dict) -> str:
        return sse_encode({"type": EventType.CAPABILITY_STATS, "stats": stats})

    def evolution_update(self, metrics: dict) -> str:
        return sse_encode({"type": EventType.EVOLUTION_UPDATE, "metrics": metrics})

    def background_task(self, task_name: str, status: str, detail: str = None) -> str:
        return sse_encode({
            "type": EventType.BACKGROUND_TASK,
            "task": {"name": task_name, "status": status, "detail": detail},
        })
