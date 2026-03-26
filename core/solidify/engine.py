"""
Experience Solidification Engine -- The flywheel that makes agents better over time.

The solidification loop:

1. **Record** -- Every agent TAOR loop execution is captured as an
   :class:`ActionTrace`.
2. **Analyse** -- Traces are clustered; repeating patterns are surfaced
   in a :class:`PatternReport`.
3. **Extract** -- High-confidence patterns are converted into
   deterministic :class:`WorkflowDAG` definitions.
4. **Canary** -- The DAG is replayed against historical data to measure
   precision / recall before going live.
5. **Promote** -- Approved DAGs replace expensive LLM reasoning with
   fast, predictable execution paths.

This is how a Titan product **learns**: it starts fully agentic and
gradually crystallises proven behaviour into code-level workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ActionTrace:
    """Record of a single agent execution.

    Captures the full trajectory from trigger event through tool calls
    to final conclusion.

    Attributes
    ----------
    run_id : str
        Unique identifier for the TAOR loop run.
    steps : list[dict]
        Ordered list of steps, each like::

            {
                "tool": "alert.query",
                "args": {"severity": "high"},
                "result": {"count": 42},
                "duration_ms": 23,
            }

    trigger : str
        What initiated this execution (user message, alert, cron, etc.).
    conclusion : str
        The final answer or action taken.
    similarity : float
        Cosine similarity to the nearest historical trace cluster.
    """

    run_id: str = ""
    steps: list[dict] = field(default_factory=list)
    trigger: str = ""
    conclusion: str = ""
    similarity: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternReport:
    """A cluster of similar action traces that form a repeating pattern."""

    pattern_id: str = ""
    alert_type: str = ""
    trace_count: int = 0
    common_steps: list[dict] = field(default_factory=list)
    confidence: float = 0.0
    """Confidence that this pattern is stable enough to solidify."""

    sample_trace_ids: list[str] = field(default_factory=list)


@dataclass
class WorkflowDAG:
    """A deterministic workflow extracted from a repeating pattern.

    Nodes are tool calls or decision points; edges encode the execution
    order and conditional branching.
    """

    dag_id: str = ""
    pattern_id: str = ""
    nodes: list[dict] = field(default_factory=list)
    """Each node: ``{"id": "n1", "tool": "...", "args_template": {...}}``."""

    edges: list[dict] = field(default_factory=list)
    """Each edge: ``{"from": "n1", "to": "n2", "condition": "..."}``."""


@dataclass
class CanaryResult:
    """Result of replaying a workflow DAG against historical data."""

    dag_id: str = ""
    total_replays: int = 0
    matches: int = 0
    mismatches: int = 0
    precision: float = 0.0
    recall: float = 0.0
    recommended_action: str = "review"
    """One of ``"promote"``, ``"review"``, ``"reject"``."""


# ---------------------------------------------------------------------------
# SolidifyEngine
# ---------------------------------------------------------------------------

class SolidifyEngine:
    """
    Analyses agent action traces, identifies repeating patterns,
    and distils them into deterministic workflows (Skills).

    Usage::

        engine = SolidifyEngine()
        engine.record_trace(run_id="run-001", trace=trace)
        # ... after many traces ...
        report = engine.analyze_patterns(alert_type="brute_force")
        dag = engine.extract_dag(report)
        result = engine.canary_test(dag, historical_data)
    """

    def __init__(self, min_traces: int = 10, confidence_threshold: float = 0.85) -> None:
        """
        Parameters
        ----------
        min_traces : int
            Minimum number of similar traces before pattern extraction
            is attempted.
        confidence_threshold : float
            Minimum confidence score to consider a pattern stable.
        """
        self.min_traces = min_traces
        self.confidence_threshold = confidence_threshold
        self._traces: list[ActionTrace] = []

    def record_trace(self, run_id: str, trace: ActionTrace) -> None:
        """Record a completed TAOR loop execution trace.

        Parameters
        ----------
        run_id : str
            Unique identifier for the execution.
        trace : ActionTrace
            The full action trace to store.
        """
        ...

    def analyze_patterns(self, alert_type: str) -> PatternReport:
        """Cluster traces by *alert_type* and surface repeating patterns.

        Parameters
        ----------
        alert_type : str
            The alert/event type to analyse (e.g. ``"brute_force"``).

        Returns
        -------
        PatternReport
            Identified pattern with confidence score and sample traces.
        """
        ...

    def extract_dag(self, pattern: PatternReport) -> WorkflowDAG:
        """Convert a high-confidence pattern into a deterministic workflow DAG.

        Parameters
        ----------
        pattern : PatternReport
            The pattern to distil.

        Returns
        -------
        WorkflowDAG
            A DAG encoding the deterministic execution path.
        """
        ...

    def canary_test(self, dag: WorkflowDAG, historical_data: list) -> CanaryResult:
        """Replay *dag* against *historical_data* to measure accuracy.

        Parameters
        ----------
        dag : WorkflowDAG
            The candidate workflow to test.
        historical_data : list
            Past alert/event records to replay.

        Returns
        -------
        CanaryResult
            Precision, recall, and a recommended promotion action.
        """
        ...
