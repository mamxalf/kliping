"""Ollama LLM provider (local/offline)."""

from typing import Optional

from clipper_cli.llm.base import BaseLLMProvider
from clipper_cli.config import settings


class OllamaProvider(BaseLLMProvider):
    """LLM provider using Ollama (local/offline)."""
    
    DEFAULT_MODEL = "llama3.2"
    
    def __init__(
        self,
        model: Optional[str] = None,
        host: Optional[str] = None,
    ):
        """Initialize Ollama provider.
        
        Args:
            model: Model name to use.
            host: Ollama server host URL.
        """
        self._model = model or settings.default_ollama_model or self.DEFAULT_MODEL
        self._host = host or settings.ollama_host
        self._client = None
    
    @property
    def name(self) -> str:
        return "Ollama"
    
    @property
    def model(self) -> str:
        return self._model
    
    @property
    def is_offline(self) -> bool:
        return True
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            import ollama
            # Try to list models to check connection
            client = ollama.Client(host=self._host)
            client.list()
            return True
        except Exception:
            return False
    
    def _get_client(self):
        """Get or create Ollama client."""
        if self._client is None:
            import ollama
            self._client = ollama.AsyncClient(host=self._host)
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate response using Ollama.
        
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
        
        response = await client.chat(
            model=self._model,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )
        
        return response["message"]["content"]
