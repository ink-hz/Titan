"""
Titan -- Build Super-Intelligent Agent Products

From Agent Framework to Agent Product.  The last mile.

Titan provides the scaffolding to turn a collection of LLM tools and
prompts into a **production-grade super-agent product** with:

* A brain that runs a TAOR loop (Think-Act-Observe-Repeat)
* Specialised sub-agents with scoped permissions
* Factory agents that produce new capabilities under schema constraints
* A solidification engine that learns from experience
* A 5-gate verification pipeline for every AI-produced artifact
* A trust hierarchy that keeps humans in control
* Intent-level collaboration between super-agent products
* One-call deployment with built-in UI

Quick start::

    from titan import AgentBrain, serve

    brain = AgentBrain(model="deepseek-r1")
    brain.register_tools("./tools/")
    brain.enable_solidify()
    serve(brain, port=8086)
"""

from .core.brain.engine import AgentBrain, BrainResponse
from .core.agents.base import SubAgent, AgentRegistry
from .core.factory.base import (
    FactoryAgent,
    RuleFactory,
    AgentFactory,
    WorkflowFactory,
    CorpusFactory,
)
from .core.solidify.engine import SolidifyEngine, ActionTrace
from .core.schema.registry import Schema, SchemaRegistry, ArtifactStore
from .core.trust.model import TrustLevel, TrustHook
from .core.verify.pipeline import VerificationPipeline
from .capability.mcp.tool import MCPTool, ToolRegistry
from .collab.intent.protocol import IntentCollaborator
from .serve import serve

__version__ = "0.1.0"

__all__ = [
    # Brain
    "AgentBrain",
    "BrainResponse",
    # Agents
    "SubAgent",
    "AgentRegistry",
    # Factories
    "FactoryAgent",
    "RuleFactory",
    "AgentFactory",
    "WorkflowFactory",
    "CorpusFactory",
    # Solidification
    "SolidifyEngine",
    "ActionTrace",
    # Schema
    "Schema",
    "SchemaRegistry",
    "ArtifactStore",
    # Trust
    "TrustLevel",
    "TrustHook",
    # Verification
    "VerificationPipeline",
    # MCP Tools
    "MCPTool",
    "ToolRegistry",
    # Collaboration
    "IntentCollaborator",
    # Server
    "serve",
]
