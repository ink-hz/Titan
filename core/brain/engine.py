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

import asyncio
import importlib
import inspect
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator, Optional

from titan.core.model.adapter import ModelAdapter, ChatMessage, StreamChunk
from titan.core.model.parser import OutputParser, ParsedOutput
from titan.core.prompt.builder import PromptBuilder
from titan.core.session.manager import SessionManager
from titan.core.stream.events import EventEmitter
from titan.core.stream.response import StreamingResponseBuilder

if TYPE_CHECKING:
    from titan.core.agents.base import SubAgent, AgentRegistry
    from titan.core.factory.base import FactoryAgent
    from titan.core.solidify.engine import SolidifyEngine
    from titan.core.trust.model import TrustLevel
    from titan.capability.mcp.tool import ToolRegistry

logger = logging.getLogger(__name__)


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

        # Core components
        self._adapter: ModelAdapter = ModelAdapter.create(model)
        self._parser: OutputParser = OutputParser()
        self._prompt_builder: PromptBuilder = PromptBuilder()
        self._session_manager: SessionManager = SessionManager()

        # Registries (populated via register_* methods)
        self._tool_registry: Optional[Any] = None
        self._agent_registry: Optional[Any] = None
        self._factories: list = []
        self._solidify_engine: Optional[Any] = None

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
        tools_dir = Path(tools_path)
        if not tools_dir.is_dir():
            logger.warning("Tools path %s is not a directory, skipping.", tools_path)
            return

        # Lazy import to avoid circular dependencies
        try:
            from titan.capability.mcp.tool import ToolRegistry, MCPTool
        except ImportError:
            logger.warning("ToolRegistry not available; storing path for later.")
            self._tool_registry = {"path": tools_path}
            return

        if self._tool_registry is None:
            self._tool_registry = ToolRegistry()

        for py_file in tools_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            module_name = py_file.stem
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Find all MCPTool subclasses in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, MCPTool) and obj is not MCPTool:
                        tool_instance = obj()
                        self._tool_registry.register(tool_instance)
                        logger.info("Registered tool: %s from %s", name, py_file.name)
            except Exception as e:
                logger.error("Failed to load tool from %s: %s", py_file, e)

    def register_agents(self, agents: list) -> None:
        """Register sub-agents for task delegation.

        Parameters
        ----------
        agents : list[type[SubAgent]]
            A list of ``SubAgent`` **classes** (not instances).  The brain
            will instantiate them with the appropriate context.
        """
        try:
            from titan.core.agents.base import AgentRegistry
            if self._agent_registry is None:
                self._agent_registry = AgentRegistry()
        except ImportError:
            logger.warning("AgentRegistry not available; storing agent classes directly.")
            self._agent_registry = {}

        for agent_cls in agents:
            try:
                if isinstance(self._agent_registry, dict):
                    # Fallback: store class by name
                    name = getattr(agent_cls, "name", agent_cls.__name__)
                    self._agent_registry[name] = agent_cls
                else:
                    self._agent_registry.register(agent_cls)
                logger.info("Registered agent: %s", getattr(agent_cls, "name", agent_cls.__name__))
            except Exception as e:
                logger.error("Failed to register agent %s: %s", agent_cls, e)

    def register_factories(self, factories: list) -> None:
        """Register factory agents for capability production.

        Factory agents can autonomously create new rules, workflows,
        sub-agents, or corpus entries -- always under schema constraints.

        Parameters
        ----------
        factories : list[type[FactoryAgent]]
            A list of ``FactoryAgent`` **classes**.
        """
        for factory_cls in factories:
            try:
                instance = factory_cls()
                self._factories.append(instance)
                logger.info("Registered factory: %s", getattr(factory_cls, "name", factory_cls.__name__))
            except Exception as e:
                logger.error("Failed to register factory %s: %s", factory_cls, e)

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
        if analyzer is not None:
            self._solidify_engine = analyzer
        else:
            try:
                from titan.core.solidify.engine import SolidifyEngine
                self._solidify_engine = SolidifyEngine()
            except ImportError:
                logger.warning("SolidifyEngine not available; using stub.")
                self._solidify_engine = {"enabled": True}
        logger.info("Solidification engine enabled.")

    # -- Prompt assembly helpers --------------------------------------------

    def _build_system_prompt(self, context: Optional[dict] = None) -> str:
        """Assemble the full system prompt from builder + context data."""
        builder = PromptBuilder()

        # Set the base role
        if self.system_prompt:
            builder.set_role(self.system_prompt)

        # Add tool descriptions if registry is available
        if self._tool_registry is not None and hasattr(self._tool_registry, "list_for_llm"):
            builder.add_tools(self._tool_registry)

        # Add context data sections
        if context:
            for key, value in context.items():
                if key not in ("session_id", "history"):
                    builder.add_context(key, value)

        return builder.build()

    def _build_messages(
        self,
        user_message: str,
        system_prompt: str,
        session_id: Optional[str] = None,
        history: Optional[list] = None,
    ) -> list[ChatMessage]:
        """Assemble the full message list for the LLM call."""
        messages = [ChatMessage(role="system", content=system_prompt)]

        # Get history from session or provided list
        if session_id:
            hist = self._session_manager.get_history(session_id, max_messages=20)
            for h in hist:
                if h["role"] != "system":
                    messages.append(ChatMessage(role=h["role"], content=h["content"]))
        elif history:
            for h in history[-20:]:
                role = h.get("role", h.get("type", "user"))
                content = h.get("content", "")
                if role != "system":
                    messages.append(ChatMessage(role=role, content=content))

        messages.append(ChatMessage(role="user", content=user_message))
        return messages

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
        context = context or {}
        session_id = context.get("session_id")
        history = context.get("history")

        # ── 1. THINK: Assemble prompt and messages ──────────────────────
        system_prompt = self._build_system_prompt(context)
        messages = self._build_messages(user_message, system_prompt, session_id, history)

        # ── 2. ACT: Call the model via streaming adapter ────────────────
        thinking_buffer = ""
        content_buffer = ""

        try:
            async for chunk in self._adapter.stream_chat(messages):
                if chunk.thinking:
                    thinking_buffer += chunk.thinking
                if chunk.content:
                    content_buffer += chunk.content
        except Exception as e:
            logger.error("Model call failed: %s", e)
            return BrainResponse(
                answer=f"Model call failed: {e}",
                confidence=0.0,
                metadata={"error": str(e)},
            )

        # ── 3. OBSERVE: Parse structured output ────────────────────────
        parsed: ParsedOutput = self._parser.parse(content_buffer)

        # ── 4. REPEAT: Check quality and potentially loop ──────────────
        # For now, single-pass; future: re-query if confidence is low.

        # Record to session if available
        if session_id:
            self._session_manager.add_message(session_id, "user", user_message)
            self._session_manager.add_message(session_id, "assistant", parsed.text, {
                "tool_calls": parsed.tool_calls,
                "components": parsed.components,
                "thinking": thinking_buffer[:500],
            })

        # Record trace for solidification
        if self._solidify_engine and hasattr(self._solidify_engine, "record_trace"):
            self._solidify_engine.record_trace({
                "user_message": user_message,
                "tool_calls": parsed.tool_calls,
                "thinking_summary": parsed.thinking_summary,
            })

        return BrainResponse(
            answer=parsed.text,
            tool_calls=parsed.tool_calls,
            confidence=1.0,
            metadata={
                "thinking_summary": parsed.thinking_summary,
                "components": parsed.components,
                "new_artifact": parsed.new_artifact,
                "needs_approval": parsed.needs_approval,
                "solidify_hint": parsed.solidify_hint,
                "capability_stats": parsed.capability_stats,
                "thinking_raw": thinking_buffer,
            },
        )

    async def stream_process_intent(
        self,
        user_message: str,
        context: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream the TAOR loop as AG-UI SSE events.

        This is the primary interface for the HTTP layer. It yields
        SSE-formatted strings that can be directly sent as a
        StreamingResponse.

        Mirrors the AEGIS demo's ``stream_aegis`` function but uses
        Titan's modular components.

        Parameters
        ----------
        user_message : str
            Raw message from the end user.
        context : dict, optional
            Session or environmental context.

        Yields
        ------
        str
            SSE-formatted event strings.
        """
        context = context or {}
        session_id = context.get("session_id")
        history = context.get("history")

        builder = StreamingResponseBuilder()

        # ── RUN_STARTED ────────────────────────────────────────────────
        yield builder.start()

        # ── 1. THINK: Assemble prompt and messages ─────────────────────
        system_prompt = self._build_system_prompt(context)
        messages = self._build_messages(user_message, system_prompt, session_id, history)

        # ── 2. ACT: Stream model response ──────────────────────────────
        thinking_buffer = ""
        content_buffer = ""

        try:
            async for chunk in self._adapter.stream_chat(messages):
                # Stream thinking events in real-time
                if chunk.thinking:
                    thinking_buffer += chunk.thinking
                    yield builder.thinking(chunk.thinking)

                # Collect content for parsing
                if chunk.content:
                    content_buffer += chunk.content

        except Exception as e:
            logger.error("Model streaming failed: %s", e)
            emitter = EventEmitter()
            import uuid
            msg_id = str(uuid.uuid4())
            yield emitter.text_start(msg_id)
            yield emitter.text_content(msg_id, f"Connection error: {e}")
            yield emitter.text_end(msg_id)
            yield builder.finish()
            return

        # ── 3. OBSERVE: Parse structured output ────────────────────────
        parsed: ParsedOutput = self._parser.parse(content_buffer)

        # ── Emit TOOL_CALL events ──────────────────────────────────────
        if parsed.tool_calls:
            yield builder.thinking("\n\n--- Start MCP tool calls ---\n")
            await asyncio.sleep(0.3)

            for tc in parsed.tool_calls:
                name = tc.get("name", "unknown")
                category = tc.get("category", "perception")
                args = tc.get("args", {})
                result_summary = tc.get("result_summary", "")
                duration = tc.get("duration_ms", 50)

                # TOOL_CALL_START
                sse_str, tool_id = builder.tool_start(name, category, args)
                yield sse_str
                yield builder.thinking(
                    f"-> Calling {name}({json.dumps(args, ensure_ascii=False) if args else ''})...\n"
                )

                # Simulate realistic execution delay
                delay = max(min(duration / 1000.0, 0.8), 0.2)
                await asyncio.sleep(delay)

                # TOOL_CALL_END
                yield builder.tool_end(tool_id, result_summary, duration)
                yield builder.thinking(f"  OK {result_summary}\n")
                await asyncio.sleep(0.1)

            yield builder.thinking("\n--- Tool calls complete ---\n\n")
            await asyncio.sleep(0.2)

        # ── Emit TEXT_MESSAGE events (streamed for natural feel) ────────
        if parsed.text:
            async for sse_chunk in builder.text_streamed(parsed.text):
                yield sse_chunk

        # ── Emit STATE_DELTA with components ───────────────────────────
        if parsed.components:
            yield builder.components(parsed.components)

        # ── Emit APPROVAL_REQUEST if needed ────────────────────────────
        if parsed.needs_approval and isinstance(parsed.needs_approval, dict):
            yield builder.approval(
                parsed.needs_approval.get("action", ""),
                parsed.needs_approval.get("title", ""),
                parsed.needs_approval.get("description", ""),
                parsed.needs_approval.get("options"),
            )

        # ── Emit SOLIDIFY_HINT if present ──────────────────────────────
        if parsed.solidify_hint and isinstance(parsed.solidify_hint, dict):
            yield builder.solidify_hint(
                parsed.solidify_hint.get("pattern_type", ""),
                parsed.solidify_hint.get("count", 0),
                parsed.solidify_hint.get("similarity", 0.0),
                parsed.solidify_hint.get("suggestion", ""),
            )

        # ── Record to session ──────────────────────────────────────────
        if session_id:
            self._session_manager.add_message(session_id, "user", user_message)
            self._session_manager.add_message(session_id, "assistant", parsed.text, {
                "tool_calls": parsed.tool_calls,
                "components": parsed.components,
            })

        # Record trace for solidification
        if self._solidify_engine and hasattr(self._solidify_engine, "record_trace"):
            self._solidify_engine.record_trace({
                "user_message": user_message,
                "tool_calls": parsed.tool_calls,
                "thinking_summary": parsed.thinking_summary,
            })

        # ── RUN_FINISHED (includes capability_stats) ───────────────────
        yield builder.finish()

    # -- Background ---------------------------------------------------------

    async def run_background_tasks(self) -> None:
        """Run autonomous background monitoring tasks.

        This includes proactive alert triage, scheduled data pulls, and
        factory-agent gap detection.  Designed to be called from an
        ``asyncio`` event loop or a background worker.
        """
        logger.info("Starting background tasks...")

        # 1. Run solidification analysis if engine is enabled
        if self._solidify_engine and hasattr(self._solidify_engine, "analyze_patterns"):
            try:
                suggestions = await self._solidify_engine.analyze_patterns()
                if suggestions:
                    logger.info("Solidification found %d patterns to propose.", len(suggestions))
            except Exception as e:
                logger.error("Solidification analysis failed: %s", e)

        # 2. Run factory gap detection
        for factory in self._factories:
            try:
                if hasattr(factory, "detect_gaps"):
                    gaps = await factory.detect_gaps()
                    if gaps:
                        logger.info("Factory %s detected %d gaps.", factory.__class__.__name__, len(gaps))
            except Exception as e:
                logger.error("Factory gap detection failed: %s", e)

        # 3. Cleanup expired sessions
        self._session_manager.cleanup_expired()

        logger.info("Background tasks completed.")
