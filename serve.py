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

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from titan.core.brain.engine import AgentBrain


def serve(
    brain: AgentBrain,
    ui: str = "panorama+chat+workspace",
    port: int = 8086,
    host: str = "0.0.0.0",
    *,
    debug: bool = False,
    cors_origins: Optional[list[str]] = None,
) -> None:
    """Launch a complete super-agent product.

    This is the main entry point for deploying a Titan-based product.
    It initialises the HTTP server, mounts API routes for the brain,
    and serves the selected UI modes.

    Parameters
    ----------
    brain : AgentBrain
        A fully configured ``AgentBrain`` instance with tools, agents,
        and factories already registered.
    ui : str
        UI modes to enable, joined by ``+``.  Valid tokens are
        ``"panorama"``, ``"chat"``, and ``"workspace"``.
    port : int
        TCP port to listen on.
    host : str
        Network interface to bind to.
    debug : bool
        Enable debug mode with auto-reload and verbose logging.
    cors_origins : list[str], optional
        Allowed CORS origins.  Defaults to ``["*"]`` in debug mode.

    Raises
    ------
    ValueError
        If *ui* contains an unrecognised mode token.

    Example
    -------
    ::

        from titan import AgentBrain, serve

        brain = AgentBrain(model="deepseek-r1")
        brain.register_tools("./tools/")
        brain.enable_solidify()
        serve(brain, port=8086)
    """
    ...
