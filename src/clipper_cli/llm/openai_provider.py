"""OpenAI LLM provider (cloud)."""

from typing import Optional

from clipper_cli.llm.base import BaseLLMProvider
from clipper_cli.config import settings


class OpenAIProvider(BaseLLMProvider):
    """LLM provider using OpenAI API."""
    
    DEFAULT_MODEL = "gpt-4o-mini"
    
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize OpenAI provider.
        
        Args:
            model: Model name to use.
            api_key: OpenAI API key.
        """
        self._model = model or settings.default_openai_model or self.DEFAULT_MODEL
        self._api_key = api_key or settings.openai_api_key
        self._client = None
    
    @property
    def name(self) -> str:
        return "OpenAI"
    
    @property
    def model(self) -> str:
        return self._model
    
    @property
    def is_offline(self) -> bool:
        return False
    
    def is_available(self) -> bool:
        """Check if OpenAI is available and configured."""
        if not self._api_key:
            return False
        
        try:
            import openai
            return True
        except ImportError:
            return False
    
    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self._api_key)
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate response using OpenAI.
        
        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
        
        Returns:
            Generated text.
        """
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content or ""
