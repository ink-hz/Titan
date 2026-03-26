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

import os
import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Optional, List, Dict
from enum import Enum

logger = logging.getLogger(__name__)


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


# ── Provider-specific defaults ──────────────────────────────────────────────

_PROVIDER_DEFAULTS: Dict[ModelProvider, Dict] = {
    ModelProvider.OPENAI: {
        "api_key_env": "OPENAI_API_KEY",
        "base_url": None,  # OpenAI SDK default
    },
    ModelProvider.ANTHROPIC: {
        "api_key_env": "ANTHROPIC_API_KEY",
        "base_url": None,
    },
    ModelProvider.DEEPSEEK: {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
    },
    ModelProvider.LOCAL: {
        "api_key_env": None,
        "base_url": "http://localhost:11434/v1",
    },
}

# Model name aliases → canonical model IDs used in API calls
_MODEL_ALIASES: Dict[str, str] = {
    "deepseek-r1": "deepseek-reasoner",
    "deepseek-v3": "deepseek-chat",
}


class ModelAdapter:
    """
    Unified model adapter with streaming support.

    Automatically detects provider from model name and configures accordingly.
    """

    def __init__(self, config: ModelConfig):
        self.config = config
        self._client = None  # Lazy-initialized OpenAI client

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
        defaults = _PROVIDER_DEFAULTS[provider]

        # Resolve API key from environment if not explicitly provided
        if "api_key" not in kwargs and defaults.get("api_key_env"):
            kwargs.setdefault("api_key", os.getenv(defaults["api_key_env"]))

        # Resolve base_url from defaults if not explicitly provided
        if "base_url" not in kwargs and defaults.get("base_url"):
            kwargs.setdefault("base_url", defaults["base_url"])

        # Resolve model alias (e.g., "deepseek-r1" → "deepseek-reasoner")
        canonical = _MODEL_ALIASES.get(model.lower(), model)

        config = ModelConfig(provider=provider, model_id=canonical, **kwargs)
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

    def _get_openai_client(self):
        """Lazily create and return an OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            client_kwargs = {}
            if self.config.api_key:
                client_kwargs["api_key"] = self.config.api_key
            if self.config.base_url:
                client_kwargs["base_url"] = self.config.base_url
            client_kwargs["timeout"] = self.config.timeout
            self._client = OpenAI(**client_kwargs)
        return self._client

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

    def _format_messages(self, messages: List[ChatMessage]) -> List[dict]:
        """Convert ChatMessage list to dicts for the API."""
        return [{"role": m.role, "content": m.content} for m in messages]

    async def _stream_openai(self, messages: List[ChatMessage]) -> AsyncGenerator[StreamChunk, None]:
        """Stream from OpenAI-compatible API."""
        client = self._get_openai_client()
        msg_dicts = self._format_messages(messages)

        try:
            response = client.chat.completions.create(
                model=self.config.model_id,
                messages=msg_dicts,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
            )

            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue

                finish = chunk.choices[0].finish_reason if chunk.choices else None

                content_text = None
                if hasattr(delta, "content") and delta.content:
                    content_text = delta.content

                yield StreamChunk(
                    content=content_text,
                    finish_reason=finish,
                )

        except Exception as e:
            logger.error("OpenAI streaming error: %s", e)
            yield StreamChunk(content=f"[Error: {e}]", finish_reason="error")

    async def _stream_anthropic(self, messages: List[ChatMessage]) -> AsyncGenerator[StreamChunk, None]:
        """Stream from Anthropic API (supports extended thinking).

        Uses the OpenAI-compatible interface. For native Anthropic SDK with
        extended thinking, this would need a separate implementation.
        Currently falls back to the OpenAI-compatible path since many
        Anthropic proxy services expose an OpenAI-compatible endpoint.
        """
        # Anthropic models through an OpenAI-compatible proxy (e.g., openrouter)
        # For native Anthropic SDK, a dedicated implementation would be needed.
        client = self._get_openai_client()
        msg_dicts = self._format_messages(messages)

        try:
            response = client.chat.completions.create(
                model=self.config.model_id,
                messages=msg_dicts,
                max_tokens=self.config.max_tokens,
                stream=True,
            )

            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue

                finish = chunk.choices[0].finish_reason if chunk.choices else None

                content_text = None
                thinking_text = None

                if hasattr(delta, "content") and delta.content:
                    content_text = delta.content

                # Some Anthropic proxies expose thinking as reasoning_content
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    thinking_text = delta.reasoning_content

                yield StreamChunk(
                    content=content_text,
                    thinking=thinking_text,
                    finish_reason=finish,
                )

        except Exception as e:
            logger.error("Anthropic streaming error: %s", e)
            yield StreamChunk(content=f"[Error: {e}]", finish_reason="error")

    async def _stream_deepseek(self, messages: List[ChatMessage]) -> AsyncGenerator[StreamChunk, None]:
        """Stream from DeepSeek API (supports reasoning_content for R1).

        DeepSeek R1 models emit both reasoning_content (thinking) and content
        (final answer) in the streaming delta, mirroring the AEGIS demo pattern.
        """
        client = self._get_openai_client()
        msg_dicts = self._format_messages(messages)

        try:
            response = client.chat.completions.create(
                model=self.config.model_id,
                messages=msg_dicts,
                stream=True,
            )

            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue

                finish = chunk.choices[0].finish_reason if chunk.choices else None

                thinking_text = None
                content_text = None

                # DeepSeek R1 reasoning stream
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    thinking_text = delta.reasoning_content

                # DeepSeek content stream
                if hasattr(delta, "content") and delta.content:
                    content_text = delta.content

                yield StreamChunk(
                    content=content_text,
                    thinking=thinking_text,
                    finish_reason=finish,
                )

        except Exception as e:
            logger.error("DeepSeek streaming error: %s", e)
            yield StreamChunk(content=f"[Error: {e}]", finish_reason="error")

    async def _stream_local(self, messages: List[ChatMessage]) -> AsyncGenerator[StreamChunk, None]:
        """Stream from local model (Ollama, vLLM, etc.).

        Local models expose an OpenAI-compatible API at localhost.
        Ollama default: http://localhost:11434/v1
        vLLM default:  http://localhost:8000/v1
        """
        client = self._get_openai_client()
        msg_dicts = self._format_messages(messages)

        try:
            response = client.chat.completions.create(
                model=self.config.model_id,
                messages=msg_dicts,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
            )

            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue

                finish = chunk.choices[0].finish_reason if chunk.choices else None

                content_text = None
                if hasattr(delta, "content") and delta.content:
                    content_text = delta.content

                yield StreamChunk(
                    content=content_text,
                    finish_reason=finish,
                )

        except Exception as e:
            logger.error("Local model streaming error: %s", e)
            yield StreamChunk(content=f"[Error: {e}]", finish_reason="error")
