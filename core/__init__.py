"""
Titan Core — Central building blocks of the Titan super-agent framework.

Exports the primary classes that every Titan-based product depends on:
  - AgentBrain: the TAOR-loop engine that drives the product
  - SubAgent / AgentRegistry: specialised sub-agents and their registry
  - FactoryAgent family: schema-constrained artifact production
  - SolidifyEngine: experience solidification (the learning flywheel)
  - Schema / SchemaRegistry / ArtifactStore: artifact definitions & storage
  - TrustLevel / TrustHook: human-in-the-loop trust hierarchy
  - VerificationPipeline: 5-gate artifact verification
"""

from .brain.engine import AgentBrain, BrainResponse
from .agents.base import SubAgent, AgentRegistry
from .factory.base import (
    FactoryAgent,
    RuleFactory,
    AgentFactory,
    WorkflowFactory,
    CorpusFactory,
)
from .solidify.engine import SolidifyEngine, ActionTrace
from .schema.registry import Schema, SchemaRegistry, ArtifactStore
from .trust.model import TrustLevel, TrustHook
from .verify.pipeline import VerificationPipeline, VerificationGate

__all__ = [
    "AgentBrain",
    "BrainResponse",
    "SubAgent",
    "AgentRegistry",
    "FactoryAgent",
    "RuleFactory",
    "AgentFactory",
    "WorkflowFactory",
    "CorpusFactory",
    "SolidifyEngine",
    "ActionTrace",
    "Schema",
    "SchemaRegistry",
    "ArtifactStore",
    "TrustLevel",
    "TrustHook",
    "VerificationPipeline",
    "VerificationGate",
]
