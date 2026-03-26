"""
Streaming Response Builder

Converts AgentBrain processing into a stream of AG-UI events.
This is the bridge between the Brain's TAOR loop and the frontend.
"""

import asyncio
import uuid
from typing import AsyncGenerator, Tuple

from .events import EventEmitter


class StreamingResponseBuilder:
    """
    Builds a streaming SSE response from Brain processing.

    This is the core pattern: Brain thinks → tools execute → results assemble,
    and each step is streamed as AG-UI events in real-time.

    Usage:
        builder = StreamingResponseBuilder()

        async def stream():
            yield builder.start()

            # Stream thinking
            async for chunk in brain.think(message):
                yield builder.thinking(chunk)

            # Stream tool calls
            for tool_call in brain.planned_tools:
                yield builder.tool_start(tool_call)
                result = await tool_call.execute()
                yield builder.tool_end(tool_call, result)

            # Stream text response
            yield builder.text(response_text)

            # Push UI components
            yield builder.components(chart_data, table_data)

            # If approval needed
            if needs_approval:
                yield builder.approval(action, title, description)

            yield builder.finish()
    """

    def __init__(self):
        self.emitter = EventEmitter()
        self.run_id = str(uuid.uuid4())
        self._tool_count = {"perception": 0, "decision": 0, "execution": 0, "presentation": 0, "memory": 0}

    def start(self) -> str:
        """Emit RUN_STARTED event."""
        return self.emitter.run_started()

    def finish(self) -> str:
        """Emit RUN_FINISHED event with capability stats."""
        stats = self.emitter.capability_stats(self._tool_count)
        finished = self.emitter.run_finished()
        return stats + finished

    def thinking(self, content: str) -> str:
        """Emit a thinking content chunk."""
        return self.emitter.thinking(content)

    def tool_start(self, name: str, category: str, args: dict = None) -> Tuple[str, str]:
        """Emit tool execution start. Returns (sse_string, tool_id) tuple."""
        tool_id = str(uuid.uuid4())
        self._tool_count[category] = self._tool_count.get(category, 0) + 1
        return self.emitter.tool_start(name, category, args, tool_id), tool_id

    def tool_end(self, tool_id: str, result: str, duration_ms: int = 0) -> str:
        """Emit tool execution end with result."""
        return self.emitter.tool_end(tool_id, result, duration_ms)

    async def text_streamed(self, text: str, chunk_size: int = 5) -> AsyncGenerator[str, None]:
        """Stream text response character by character for natural feel."""
        msg_id = str(uuid.uuid4())
        yield self.emitter.text_start(msg_id)
        for i in range(0, len(text), chunk_size):
            yield self.emitter.text_content(msg_id, text[i:i+chunk_size])
            await asyncio.sleep(0.02)
        yield self.emitter.text_end(msg_id)

    def components(self, component_list: list) -> str:
        """Push UI components to frontend."""
        return self.emitter.state_delta(component_list)

    def approval(self, action: str, title: str, description: str, options: list = None) -> str:
        """Request human approval."""
        return self.emitter.approval_request(action, title, description, options)

    def handoff(self, from_agent: str, to_agent: str, reason: str) -> str:
        """Notify frontend of agent handoff."""
        return self.emitter.agent_handoff(from_agent, to_agent, reason)

    def collab(self, target: str, intent: str, status: str, conclusion: str = None) -> str:
        """Notify frontend of super-agent collaboration status."""
        return self.emitter.agent_collab(target, intent, status, conclusion)

    def solidify_hint(self, pattern_type: str, count: int, similarity: float, suggestion: str) -> str:
        """Suggest experience solidification."""
        return self.emitter.solidify_hint(pattern_type, count, similarity, suggestion)
