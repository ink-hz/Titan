"""
Titan Model Adapter — Unified interface for multiple LLM providers.

Supports OpenAI, Anthropic, DeepSeek, and local models through a single API.
Handles streaming, retries, fallback, and response parsing.

Usage:
    adapter = ModelAdapter.create("deepseek-r1")
    async for chunk in adapter.stream_chat(messages):
        if chunk.thinking:
            yield emitter.thinking(chunk.thinking)
        if chunk.content:
            content_buffer += chunk.content
"""

from dataclasses import dataclass
from typing import AsyncGenerator, Optional, List, Dict
from enum import Enum


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    LOCAL = "local"  # Ollama, vLLM, etc.


@dataclass
class ChatMessage:
    """A message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class StreamChunk:
    """A single chunk from streaming model response."""
    content: Optional[str] = None      # Assistant's response content
    thinking: Optional[str] = None      # Reasoning/thinking content (DeepSeek-R1, Claude)
    finish_reason: Optional[str] = None  # "stop", "tool_use", etc.
    raw: Optional[dict] = None           # Raw provider response


@dataclass
class ModelConfig:
    """Configuration for a model."""
    provider: ModelProvider
    model_id: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120  # seconds


class ModelAdapter:
    """
    Unified model adapter with streaming support.

    Automatically detects provider from model name and configures accordingly.
    """

    def __init__(self, config: ModelConfig):
        self.config = config

    @classmethod
    def create(cls, model: str, **kwargs) -> "ModelAdapter":
        """
        Create adapter from model name string.

        Auto-detects provider:
            "gpt-4o" → OpenAI
            "claude-sonnet-4-20250514" → Anthropic
            "deepseek-reasoner" → DeepSeek
            "deepseek-r1" → DeepSeek
            "qwen-72b" → Local (Ollama)
            "ollama:llama3" → Local
        """
        provider = cls._detect_provider(model)
        config = ModelConfig(provider=provider, model_id=model, **kwargs)
        return cls(config)

    @staticmethod
    def _detect_provider(model: str) -> ModelProvider:
        model_lower = model.lower()
        if model_lower.startswith(("gpt-", "o1-", "o3-")):
            return ModelProvider.OPENAI
        elif model_lower.startswith(("claude-",)):
            return ModelProvider.ANTHROPIC
        elif model_lower.startswith(("deepseek",)):
            return ModelProvider.DEEPSEEK
        else:
            return ModelProvider.LOCAL

    async def stream_chat(self, messages: List[ChatMessage]) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a chat completion.

        Yields StreamChunk objects with content and/or thinking.
        Handles provider-specific differences transparently.
        """
        if self.config.provider == ModelProvider.OPENAI:
            async for chunk in self._stream_openai(messages):
                yield chunk
        elif self.config.provider == ModelProvider.ANTHROPIC:
            async for chunk in self._stream_anthropic(messages):
                yield chunk
        elif self.config.provider == ModelProvider.DEEPSEEK:
            async for chunk in self._stream_deepseek(messages):
                yield chunk
        else:
            async for chunk in self._stream_local(messages):
                yield chunk

    async def _stream_openai(self, messages: List[ChatMessage]) -> AsyncGenerator[StreamChunk, None]:
        """Stream from OpenAI-compatible API."""
        ...

    async def _stream_anthropic(self, messages: List[ChatMessage]) -> AsyncGenerator[StreamChunk, None]:
        """Stream from Anthropic API (supports extended thinking)."""
        ...

    async def _stream_deepseek(self, messages: List[ChatMessage]) -> AsyncGenerator[StreamChunk, None]:
        """Stream from DeepSeek API (supports reasoning_content for R1)."""
        ...

    async def _stream_local(self, messages: List[ChatMessage]) -> AsyncGenerator[StreamChunk, None]:
        """Stream from local model (Ollama, vLLM, etc.)."""
        ...
