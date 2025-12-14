"""Anthropic Claude LLM provider (cloud)."""

from typing import Optional

from clipper_cli.llm.base import BaseLLMProvider
from clipper_cli.config import settings


class ClaudeProvider(BaseLLMProvider):
    """LLM provider using Anthropic Claude API."""
    
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize Claude provider.
        
        Args:
            model: Model name to use.
            api_key: Anthropic API key.
        """
        self._model = model or settings.default_claude_model or self.DEFAULT_MODEL
        self._api_key = api_key or settings.anthropic_api_key
        self._client = None
    
    @property
    def name(self) -> str:
        return "Anthropic Claude"
    
    @property
    def model(self) -> str:
        return self._model
    
    @property
    def is_offline(self) -> bool:
        return False
    
    def is_available(self) -> bool:
        """Check if Claude is available and configured."""
        if not self._api_key:
            return False
        
        try:
            import anthropic
            return True
        except ImportError:
            return False
    
    def _get_client(self):
        """Get or create Anthropic client."""
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate response using Claude.
        
        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
        
        Returns:
            Generated text.
        """
        client = self._get_client()
        
        kwargs = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = await client.messages.create(**kwargs)
        
        # Extract text from response
        return response.content[0].text
