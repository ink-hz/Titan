"""
Titan Server -- Launch a super-agent product with one function call.

The ``serve`` function wires together the configured :class:`AgentBrain`,
attaches the chosen UI modes, and starts an HTTP server that exposes both
the agent API and the frontend.

Supported UI modes (combinable with ``+``):

* ``panorama`` -- Real-time operational dashboard with live metrics.
* ``chat`` -- Conversational interface for interacting with the brain.
* ``workspace`` -- Structured workspace for reviewing and approving
  artifacts, workflows, and agent proposals.

Example::

    from titan import AgentBrain, serve

    brain = AgentBrain(model="deepseek-r1")
    brain.register_tools("./tools/")
    brain.enable_solidify()
    serve(brain, ui="panorama+chat+workspace", port=8086)
"""

from __future__ import annotations

import json
import os
import asyncio
import time
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import yaml

if TYPE_CHECKING:
    from titan.core.brain.engine import AgentBrain

logger = logging.getLogger("titan.serve")


# ---------------------------------------------------------------------------
# Template loader
# ---------------------------------------------------------------------------

def load_template(template_name: str) -> "AgentBrain":
    """Load a brain configuration from a template directory.

    Reads ``titan.yaml`` from ``templates/<name>/`` and constructs a fully
    configured :class:`AgentBrain` with the model, system prompt, tools,
    and any template-specific settings.

    Parameters
    ----------
    template_name : str
        Name of the template directory (e.g. ``"security"``, ``"devops"``).

    Returns
    -------
    AgentBrain
        A configured brain instance ready to serve.

    Raises
    ------
    FileNotFoundError
        If the template directory or ``titan.yaml`` does not exist.
    """
    from .core.brain.engine import AgentBrain

    template_dir = Path(__file__).parent / "templates" / template_name
    if not template_dir.exists():
        available = [
            d.name
            for d in (Path(__file__).parent / "templates").iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ]
        raise FileNotFoundError(
            f"Template '{template_name}' not found. Available: {available}"
        )

    config_file = template_dir / "titan.yaml"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    # Build brain from template config
    model = config.get("model", "deepseek-r1")
    system_prompt = config.get("system_prompt", f"You are a Titan super-agent ({template_name} template).")

    brain = AgentBrain(model=model, system_prompt=system_prompt)

    # Register tools if specified
    tools_dir = config.get("tools_dir")
    if tools_dir:
        tools_path = template_dir / tools_dir
        if tools_path.exists():
            brain.register_tools(str(tools_path))

    # Enable solidify if configured
    if config.get("solidify", False):
        brain.enable_solidify()

    # Store template metadata on brain for the API
    brain._template_name = template_name
    brain._template_config = config
    brain._template_dir = template_dir

    return brain


# ---------------------------------------------------------------------------
# Main serve function
# ---------------------------------------------------------------------------

def serve(
    brain: AgentBrain = None,
    ui: str = "panorama+chat+workspace",
    port: int = 8086,
    host: str = "0.0.0.0",
    *,
    template: str = None,
    debug: bool = False,
    cors_origins: Optional[list[str]] = None,
) -> None:
    """Launch a complete super-agent product.

    This is the main entry point for deploying a Titan-based product.
    It initialises the HTTP server, mounts API routes for the brain,
    and serves the selected UI modes.

    Parameters
    ----------
    brain : AgentBrain, optional
        A fully configured ``AgentBrain`` instance. Either *brain* or
        *template* must be provided.
    ui : str
        UI modes to enable, joined by ``+``.  Valid tokens are
        ``"panorama"``, ``"chat"``, and ``"workspace"``.
    port : int
        TCP port to listen on.
    host : str
        Network interface to bind to.
    template : str, optional
        Template name to load a pre-configured brain from.
    debug : bool
        Enable debug mode with auto-reload and verbose logging.
    cors_origins : list[str], optional
        Allowed CORS origins.  Defaults to ``["*"]`` in debug mode.

    Raises
    ------
    ValueError
        If neither *brain* nor *template* is provided, or if *ui*
        contains an unrecognised mode token.
    """
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware

    from .core.stream.events import EventEmitter
    from .core.stream.response import StreamingResponseBuilder
    from .core.session.manager import SessionManager
    from .core.model.adapter import ModelAdapter, ChatMessage

    # ---- Resolve brain -----------------------------------------------------
    if template and brain is None:
        brain = load_template(template)
    if brain is None:
        raise ValueError("Either 'brain' or 'template' must be provided.")

    # ---- Validate UI modes -------------------------------------------------
    valid_modes = {"panorama", "chat", "workspace"}
    ui_modes = set(ui.split("+"))
    unknown = ui_modes - valid_modes
    if unknown:
        raise ValueError(f"Unrecognised UI mode(s): {unknown}. Valid: {valid_modes}")

    # ---- Application setup -------------------------------------------------
    template_label = getattr(brain, "_template_name", "custom")
    app = FastAPI(
        title=f"Titan Super-Agent ({template_label})",
        version="0.1.0",
        description="Titan -- Build Super-Intelligent Agent Products",
    )

    # CORS
    origins = cors_origins or (["*"] if debug else ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    sessions = SessionManager()
    model_adapter = ModelAdapter.create(brain.model)
    emitter = EventEmitter()

    # ---- Static files ------------------------------------------------------
    static_dir = Path(__file__).parent / "ui" / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # ---- Server start time for uptime tracking -----------------------------
    _start_time = time.time()

    # ---- Routes: UI --------------------------------------------------------

    @app.get("/", response_class=HTMLResponse)
    async def index():
        """Serve the built-in UI."""
        ui_path = static_dir / "index.html"
        if ui_path.exists():
            return ui_path.read_text(encoding="utf-8")
        return HTMLResponse(
            "<h1>Titan Super-Agent</h1>"
            "<p>No UI template found. Place index.html in titan/ui/static/</p>",
            status_code=200,
        )

    # ---- Routes: Chat API --------------------------------------------------

    @app.post("/api/chat")
    async def chat(request: Request):
        """Process a chat message and return an SSE stream of AG-UI events."""
        body = await request.json()
        message = body.get("message", "")
        history = body.get("history", [])
        session_id = body.get("session_id", "default")

        # Ensure session exists
        if sessions.get(session_id) is None:
            sessions.create(session_id)

        # Record user message
        sessions.add_message(session_id, "user", message)

        async def event_stream():
            builder = StreamingResponseBuilder()
            yield builder.start()

            # Build message list for LLM
            llm_messages = []
            if brain.system_prompt:
                llm_messages.append(ChatMessage(role="system", content=brain.system_prompt))
            for msg in history[-20:]:
                llm_messages.append(ChatMessage(
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                ))
            llm_messages.append(ChatMessage(role="user", content=message))

            # Stream from model
            content_buffer = ""
            thinking_buffer = ""
            msg_id = None

            try:
                async for chunk in model_adapter.stream_chat(llm_messages):
                    # Stream thinking tokens
                    if chunk.thinking:
                        thinking_buffer += chunk.thinking
                        yield builder.thinking(chunk.thinking)

                    # Stream content tokens
                    if chunk.content:
                        if msg_id is None:
                            msg_id = __import__("uuid").uuid4().hex
                            yield emitter.text_start(msg_id)
                        content_buffer += chunk.content
                        yield emitter.text_content(msg_id, chunk.content)

                if msg_id:
                    yield emitter.text_end(msg_id)
            except Exception as e:
                # On model error, send error as text
                logger.exception("Model streaming error")
                err_msg_id = __import__("uuid").uuid4().hex
                yield emitter.text_start(err_msg_id)
                yield emitter.text_content(err_msg_id, f"[Error] {e}")
                yield emitter.text_end(err_msg_id)
                content_buffer = f"[Error] {e}"

            # Record assistant reply
            sessions.add_message(session_id, "assistant", content_buffer)

            yield builder.finish()

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # ---- Routes: Capabilities ----------------------------------------------

    @app.get("/api/capabilities")
    async def capabilities():
        """Return the brain's registered capabilities and metadata."""
        template_config = getattr(brain, "_template_config", {})
        return JSONResponse({
            "template": getattr(brain, "_template_name", "custom"),
            "model": brain.model,
            "ui_modes": list(ui_modes),
            "tools": _get_tool_summary(),
            "intents": template_config.get("intents", []),
            "features": {
                "solidify": brain._solidify_engine is not None,
                "streaming": True,
                "multi_agent": brain._agent_registry is not None,
            },
        })

    # ---- Routes: Session management ----------------------------------------

    @app.post("/api/session")
    async def create_session(request: Request):
        """Create or reset a session."""
        body = await request.json()
        session_id = body.get("session_id")
        sid = sessions.create(session_id)
        return JSONResponse({"session_id": sid})

    @app.get("/api/session/{session_id}/history")
    async def get_history(session_id: str, max_messages: int = 50):
        """Retrieve conversation history."""
        history = sessions.get_history(session_id, max_messages=max_messages)
        return JSONResponse({"session_id": session_id, "messages": history})

    # ---- Routes: Health & stats --------------------------------------------

    @app.get("/api/health")
    async def health():
        """Health check endpoint."""
        uptime = time.time() - _start_time
        return JSONResponse({
            "status": "healthy",
            "uptime_seconds": round(uptime, 1),
            "model": brain.model,
            "template": getattr(brain, "_template_name", "custom"),
        })

    @app.get("/api/stats")
    async def stats():
        """Runtime statistics."""
        return JSONResponse({
            "uptime_seconds": round(time.time() - _start_time, 1),
            "active_sessions": len(sessions._sessions),
            "model": brain.model,
            "tools": _get_tool_summary(),
        })

    # ---- Routes: Template config (for frontend) ----------------------------

    @app.get("/api/config")
    async def config():
        """Return template configuration for the frontend."""
        template_config = getattr(brain, "_template_config", {})
        return JSONResponse({
            "template": getattr(brain, "_template_name", "custom"),
            "title": template_config.get("title", "Titan Super-Agent"),
            "description": template_config.get("description", ""),
            "intents": template_config.get("intents", []),
            "ui_modes": list(ui_modes),
            "branding": template_config.get("branding", {}),
        })

    # ---- Helpers -----------------------------------------------------------

    def _get_tool_summary() -> dict:
        """Summarize registered tools by category."""
        from .capability.mcp.decorator import get_registered_tools
        tools = get_registered_tools()
        summary = {"total": len(tools), "by_category": {}}
        for name, t in tools.items():
            cat = t.category
            summary["by_category"].setdefault(cat, [])
            summary["by_category"][cat].append({
                "name": t.name,
                "description": t.description,
            })
        return summary

    # ---- Launch ------------------------------------------------------------

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger.info("Titan Super-Agent starting on %s:%d", host, port)
    logger.info("Template: %s | Model: %s | UI: %s", template_label, brain.model, ui)

    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info" if not debug else "debug")


# ---------------------------------------------------------------------------
# __main__ support: python -m titan.serve --template security --port 8086
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Titan Super-Agent Server")
    parser.add_argument("--template", default=None, help="Template name to load")
    parser.add_argument("--port", type=int, default=8086, help="Port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--ui", default="panorama+chat+workspace", help="UI modes")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    serve(
        template=args.template,
        ui=args.ui,
        port=args.port,
        host=args.host,
        debug=args.debug,
    )
