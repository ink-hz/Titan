"""
Trust Hierarchy Model -- Humans approve, agents execute.

Every tool call in Titan passes through a trust evaluation.  The
:class:`TrustLevel` enum defines four tiers that control how much
autonomy the agent has for a given operation:

=================  ====================================================
Level              Behaviour
=================  ====================================================
``AUTONOMOUS``     Agent executes freely (e.g. read-only perception).
``REPORT_AFTER``   Agent executes, then notifies humans.
``APPROVE_BEFORE`` Agent proposes, human must approve before execution.
``HUMAN_ONLY``     Agent can only suggest; human performs the action.
=================  ====================================================

:class:`TrustHook` provides pre- and post-execution hooks that the
brain's tool dispatcher invokes around every tool call.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Trust levels
# ---------------------------------------------------------------------------

class TrustLevel(IntEnum):
    """Ordered trust tiers -- higher value = more human involvement."""

    AUTONOMOUS = 0
    """Agent executes freely (perception tools, read-only queries)."""

    REPORT_AFTER = 1
    """Agent executes, reports the action afterwards (low-risk writes)."""

    APPROVE_BEFORE = 2
    """Agent proposes the action, human must approve before execution."""

    HUMAN_ONLY = 3
    """Agent can only suggest; a human performs the operation manually."""


# ---------------------------------------------------------------------------
# Hook data classes
# ---------------------------------------------------------------------------

@dataclass
class HookDecision:
    """Decision returned by a :meth:`TrustHook.pre_tool_use` invocation."""

    allow: bool
    """Whether the tool call should proceed."""

    reason: str = ""
    """Human-readable explanation of the decision."""

    modified_args: Optional[dict] = None
    """If set, these arguments replace the original ones (policy rewrite)."""


# ---------------------------------------------------------------------------
# TrustHook
# ---------------------------------------------------------------------------

class TrustHook:
    """Pre/Post tool execution hooks for trust enforcement.

    The brain invokes :meth:`pre_tool_use` **before** dispatching a tool
    call and :meth:`post_tool_use` **after** receiving the result.  This
    is the primary enforcement point for the trust hierarchy.

    Subclass this to integrate with your approval system (Slack, PagerDuty,
    JIRA, custom UI, etc.).
    """

    async def pre_tool_use(
        self,
        tool_name: str,
        args: dict,
        trust_level: TrustLevel,
    ) -> HookDecision:
        """Called before a tool is executed.

        For ``APPROVE_BEFORE`` tools, this method should block until a
        human decision is received (or a timeout fires).

        Parameters
        ----------
        tool_name : str
            Fully qualified tool name (e.g. ``"firewall.block_ip"``).
        args : dict
            The arguments that will be passed to the tool.
        trust_level : TrustLevel
            The trust level assigned to this tool.

        Returns
        -------
        HookDecision
            Whether to allow, deny, or modify the tool call.
        """
        ...

    async def post_tool_use(
        self,
        tool_name: str,
        result: dict,
        trust_level: TrustLevel,
    ) -> None:
        """Called after a tool has executed.

        Use this for audit logging, notification delivery, or anomaly
        detection on tool outputs.

        Parameters
        ----------
        tool_name : str
            Fully qualified tool name.
        result : dict
            The tool's return value.
        trust_level : TrustLevel
            The trust level assigned to this tool.
        """
        ...
