"""Google Gemini LLM provider (cloud)."""

from typing import Optional

from clipper_cli.llm.base import BaseLLMProvider
from clipper_cli.config import settings


class GeminiProvider(BaseLLMProvider):
    """LLM provider using Google Gemini API."""
    
    DEFAULT_MODEL = "gemini-2.0-flash-exp"
    
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize Gemini provider.
        
        Args:
            model: Model name to use.
            api_key: Google AI API key.
        """
        self._model = model or settings.default_gemini_model or self.DEFAULT_MODEL
        self._api_key = api_key or settings.gemini_api_key
        self._client = None
        self._configured = False
    
    @property
    def name(self) -> str:
        return "Google Gemini"
    
    @property
    def model(self) -> str:
        return self._model
    
    @property
    def is_offline(self) -> bool:
        return False
    
    def is_available(self) -> bool:
        """Check if Gemini is available and configured."""
        if not self._api_key:
            return False
        
        try:
            import google.generativeai
            return True
        except ImportError:
            return False
    
    def _configure(self):
        """Configure the Gemini API."""
        if not self._configured:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._configured = True
    
    def _get_client(self):
        """Get or create Gemini client."""
        if self._client is None:
            import google.generativeai as genai
            self._configure()
            self._client = genai.GenerativeModel(self._model)
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate response using Gemini.
        
        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
        
        Returns:
            Generated text.
        """
        import google.generativeai as genai
        
        self._configure()
        
        # Build generation config
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # Create model with system instruction if provided
        if system_prompt:
            model = genai.GenerativeModel(
                self._model,
                system_instruction=system_prompt,
                generation_config=generation_config,
            )
        else:
            model = genai.GenerativeModel(
                self._model,
                generation_config=generation_config,
            )
        
        # Generate response
        response = await model.generate_content_async(prompt)
        
        return response.text
