"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the provider name for display."""
        pass
    
    @property
    @abstractmethod
    def model(self) -> str:
        """Get the model name being used."""
        pass
    
    @property
    @abstractmethod
    def is_offline(self) -> bool:
        """Whether this provider works offline."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured.
        
        Returns:
            True if ready to use.
        """
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a response from the LLM.
        
        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt for context.
            temperature: Sampling temperature (0-1).
            max_tokens: Maximum tokens in response.
        
        Returns:
            Generated text response.
        """
        pass
    
    def generate_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Synchronous wrapper for generate.
        
        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt for context.
            temperature: Sampling temperature (0-1).
            max_tokens: Maximum tokens in response.
        
        Returns:
            Generated text response.
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate(prompt, system_prompt, temperature, max_tokens)
        )
