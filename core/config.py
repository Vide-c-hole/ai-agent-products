"""Configuration management for agents."""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml


@dataclass
class AgentConfig:
    """Base configuration for all agents."""
    
    # LLM settings
    provider: str = "groq"  # groq (free), anthropic, openai
    model: str = "llama-3.3-70b-versatile"  # Groq default (free)
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # Rate limiting
    requests_per_minute: int = 50
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Caching
    cache_enabled: bool = True
    cache_dir: str = ".cache"
    cache_ttl: int = 3600  # seconds
    
    # Output
    output_dir: str = "output"
    verbose: bool = False
    
    # Custom settings
    custom: dict = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, path: str | Path) -> "AgentConfig":
        """Load config from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load config from environment variables."""
        return cls(
            provider=os.getenv("AGENT_PROVIDER", "groq"),
            model=os.getenv("AGENT_MODEL", "llama-3.3-70b-versatile"),
            max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
            verbose=os.getenv("AGENT_VERBOSE", "").lower() == "true",
        )
    
    def to_yaml(self, path: str | Path) -> None:
        """Save config to YAML file."""
        with open(path, "w") as f:
            yaml.dump(self.__dict__, f, default_flow_style=False)
