"""
Intent-Level Collaboration -- Super-agents communicate via natural language intent.

Instead of rigid API contracts, Titan super-agents exchange **intents**:
natural-language descriptions of what they need from each other.  The
receiving agent interprets the intent using its own brain and responds
with structured results.

This enables loose coupling between independently developed super-agent
products -- they only need to agree on the intent protocol, not on
internal data models.

Example::

    collab = IntentCollaborator(agent_id="aegis-security")
    response = await collab.send_intent(
        target="titan-it-ops",
        intent="Check if host 10.0.0.5 has any open maintenance tickets",
        context={"alert_id": "ALT-1234"},
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class IntentMessage:
    """A natural language intent sent between super-agents.

    Attributes
    ----------
    sender : str
        Identifier of the sending super-agent product.
    target : str
        Identifier of the target super-agent product.
    intent : str
        Natural-language description of what the sender needs.
    context : dict
        Optional structured context to accompany the intent.
    message_id : str
        Unique message identifier for tracking and correlation.
    """

    sender: str = ""
    target: str = ""
    intent: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    message_id: str = ""


@dataclass
class IntentResponse:
    """Response to an :class:`IntentMessage`.

    Attributes
    ----------
    message_id : str
        Identifier of the original intent message.
    success : bool
        Whether the target agent fulfilled the intent.
    result : Any
        The response payload (structured data or free text).
    confidence : float
        Target agent's confidence in its response.
    error : str, optional
        Error description if the intent could not be fulfilled.
    """

    message_id: str = ""
    success: bool = False
    result: Any = None
    confidence: float = 0.0
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# IntentCollaborator
# ---------------------------------------------------------------------------

class IntentCollaborator:
    """Handles intent-level communication with external super-agents.

    Each Titan product has one ``IntentCollaborator`` that manages both
    outbound requests (asking other products for help) and inbound
    requests (responding to other products' needs).

    Parameters
    ----------
    agent_id : str
        This super-agent product's unique identifier.
    transport : object, optional
        Message transport layer (HTTP, gRPC, message queue, etc.).
        Defaults to a local in-process transport for development.
    """

    def __init__(self, agent_id: str, transport: Optional[Any] = None) -> None:
        self.agent_id = agent_id
        self.transport = transport

    async def send_intent(
        self,
        target: str,
        intent: str,
        context: Optional[dict] = None,
    ) -> IntentResponse:
        """Send a natural-language intent to another super-agent.

        Parameters
        ----------
        target : str
            Identifier of the target super-agent product.
        intent : str
            Natural-language description of what you need.
        context : dict, optional
            Structured context to help the target agent understand the
            request.

        Returns
        -------
        IntentResponse
            The target agent's response.
        """
        ...

    async def receive_intent(self, message: IntentMessage) -> IntentResponse:
        """Handle an incoming intent from another super-agent.

        This method is invoked by the transport layer when an intent
        message arrives.  The default implementation delegates to the
        local :class:`~titan.core.brain.engine.AgentBrain`.

        Parameters
        ----------
        message : IntentMessage
            The incoming intent message.

        Returns
        -------
        IntentResponse
            This agent's response to the intent.
        """
        ...

    async def broadcast_intent(
        self,
        intent: str,
        context: Optional[dict] = None,
    ) -> list[IntentResponse]:
        """Broadcast an intent to all known super-agents.

        Parameters
        ----------
        intent : str
            Natural-language description of what you need.
        context : dict, optional
            Structured context.

        Returns
        -------
        list[IntentResponse]
            Responses from all agents that replied.
        """
        ...
