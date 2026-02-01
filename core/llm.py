"""LLM provider abstraction - supports Anthropic, OpenAI, Groq (free tier)."""
import os
import time
import hashlib
import json
from pathlib import Path
from typing import Any, Generator
from dataclasses import dataclass

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None

try:
    from groq import Groq
except ImportError:
    Groq = None


@dataclass
class Message:
    """Unified message format."""
    role: str  # user, assistant, system
    content: str


@dataclass 
class LLMResponse:
    """Unified response format."""
    content: str
    model: str
    usage: dict[str, int]
    cached: bool = False


class LLMProvider:
    """Unified interface for LLM providers."""
    
    def __init__(
        self,
        provider: str = "anthropic",
        model: str | None = None,
        cache_dir: str | None = None,
        cache_ttl: int = 3600,
    ):
        self.provider = provider
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.cache_ttl = cache_ttl
        
        if provider == "groq":
            # FREE TIER - Recommended for testing
            if not Groq:
                raise ImportError("pip install groq")
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError(
                    "GROQ_API_KEY not set. Get FREE key at https://console.groq.com\n"
                    "  export GROQ_API_KEY='your-key-here'"
                )
            self.client = Groq(api_key=api_key)
            self.model = model or "llama-3.3-70b-versatile"  # Fast & free
        elif provider == "anthropic":
            if not anthropic:
                raise ImportError("pip install anthropic")
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set. Run:\n"
                    "  export ANTHROPIC_API_KEY='your-key-here'\n"
                    "Or add to .env file and source it."
                )
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model or "claude-sonnet-4-20250514"
        elif provider == "openai":
            if not openai:
                raise ImportError("pip install openai")
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY not set. Run:\n"
                    "  export OPENAI_API_KEY='your-key-here'\n"
                    "Or add to .env file and source it."
                )
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model or "gpt-4o"
        else:
            raise ValueError(f"Unknown provider: {provider}. Use: groq (free), anthropic, openai")
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _cache_key(self, messages: list[Message], **kwargs) -> str:
        """Generate cache key from request."""
        data = {
            "messages": [(m.role, m.content) for m in messages],
            "model": self.model,
            **kwargs
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def _get_cached(self, key: str) -> LLMResponse | None:
        """Get cached response if valid."""
        if not self.cache_dir:
            return None
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None
        data = json.loads(cache_file.read_text())
        if time.time() - data["timestamp"] > self.cache_ttl:
            cache_file.unlink()
            return None
        return LLMResponse(
            content=data["content"],
            model=data["model"],
            usage=data["usage"],
            cached=True
        )
    
    def _set_cached(self, key: str, response: LLMResponse) -> None:
        """Cache a response."""
        if not self.cache_dir:
            return
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps({
            "content": response.content,
            "model": response.model,
            "usage": response.usage,
            "timestamp": time.time()
        }))
    
    def complete(
        self,
        messages: list[Message],
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Get completion from LLM."""
        # Check cache
        cache_key = self._cache_key(messages, system=system, max_tokens=max_tokens, temperature=temperature)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        if self.provider == "anthropic":
            response = self._anthropic_complete(messages, system, max_tokens, temperature)
        elif self.provider == "groq":
            response = self._groq_complete(messages, system, max_tokens, temperature)
        else:
            response = self._openai_complete(messages, system, max_tokens, temperature)
        
        self._set_cached(cache_key, response)
        return response
    
    def _anthropic_complete(
        self,
        messages: list[Message],
        system: str | None,
        max_tokens: int,
        temperature: float
    ) -> LLMResponse:
        """Anthropic API call."""
        msg_list = [{"role": m.role, "content": m.content} for m in messages]
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": msg_list,
        }
        if system:
            kwargs["system"] = system
        
        response = self.client.messages.create(**kwargs)
        
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        )
    
    def _openai_complete(
        self,
        messages: list[Message],
        system: str | None,
        max_tokens: int,
        temperature: float
    ) -> LLMResponse:
        """OpenAI API call."""
        msg_list = []
        if system:
            msg_list.append({"role": "system", "content": system})
        msg_list.extend([{"role": m.role, "content": m.content} for m in messages])
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=msg_list,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
        )

    def _groq_complete(
        self,
        messages: list[Message],
        system: str | None,
        max_tokens: int,
        temperature: float
    ) -> LLMResponse:
        """Groq API call (FREE tier available)."""
        msg_list = []
        if system:
            msg_list.append({"role": "system", "content": system})
        msg_list.extend([{"role": m.role, "content": m.content} for m in messages])

        response = self.client.chat.completions.create(
            model=self.model,
            messages=msg_list,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
        )
