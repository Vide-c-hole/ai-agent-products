"""Base agent class with common functionality."""
import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable

from .config import AgentConfig
from .llm import LLMProvider, Message, LLMResponse


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self.llm = LLMProvider(
            provider=self.config.provider,
            model=self.config.model,
            cache_dir=self.config.cache_dir if self.config.cache_enabled else None,
            cache_ttl=self.config.cache_ttl,
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()
        
        # Rate limiting
        self._request_times: list[float] = []
        
        # Output directory
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> None:
        """Configure logging."""
        level = logging.DEBUG if self.config.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        now = time.time()
        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if now - t < 60]
        
        if len(self._request_times) >= self.config.requests_per_minute:
            sleep_time = 60 - (now - self._request_times[0])
            if sleep_time > 0:
                self.logger.debug(f"Rate limited, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        self._request_times.append(time.time())
    
    def _retry(self, fn: Callable, *args, **kwargs) -> Any:
        """Retry a function with exponential backoff."""
        last_error = None
        for attempt in range(self.config.retry_attempts):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_error = e
                wait = self.config.retry_delay * (2 ** attempt)
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {wait}s")
                time.sleep(wait)
        raise last_error
    
    def ask(
        self,
        prompt: str,
        system: str | None = None,
        context: list[Message] | None = None,
    ) -> str:
        """Send a prompt to the LLM and get a response."""
        self._rate_limit()
        
        messages = context or []
        messages.append(Message(role="user", content=prompt))
        
        response = self._retry(
            self.llm.complete,
            messages=messages,
            system=system or self.system_prompt,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        
        if self.config.verbose:
            self.logger.debug(f"Tokens: {response.usage}")
            if response.cached:
                self.logger.debug("(cached)")
        
        return response.content
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt for this agent."""
        pass
    
    @abstractmethod
    def run(self, **kwargs) -> Any:
        """Main entry point for the agent."""
        pass
    
    def save_output(self, content: str, filename: str) -> Path:
        """Save output to file."""
        path = self.output_dir / filename
        path.write_text(content)
        self.logger.info(f"Saved: {path}")
        return path
