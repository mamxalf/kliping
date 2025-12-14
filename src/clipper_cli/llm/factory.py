"""LLM provider factory."""

from typing import Optional
from enum import Enum

from clipper_cli.llm.base import BaseLLMProvider
from clipper_cli.llm.ollama_provider import OllamaProvider
from clipper_cli.llm.openai_provider import OpenAIProvider
from clipper_cli.llm.gemini_provider import GeminiProvider
from clipper_cli.llm.claude_provider import ClaudeProvider
from clipper_cli.config import settings


class LLMProviderType(str, Enum):
    """Available LLM provider types."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"


# Default models for each provider
DEFAULT_MODELS = {
    LLMProviderType.OLLAMA: "llama3.2",
    LLMProviderType.OPENAI: "gpt-4o-mini",
    LLMProviderType.GEMINI: "gemini-2.0-flash-exp",
    LLMProviderType.CLAUDE: "claude-3-5-sonnet-20241022",
}


def create_llm_provider(
    provider_type: LLMProviderType,
    model: Optional[str] = None,
    **kwargs,
) -> BaseLLMProvider:
    """Create an LLM provider instance.
    
    Args:
        provider_type: Type of provider to create.
        model: Optional model name override.
        **kwargs: Additional provider-specific arguments.
    
    Returns:
        Configured LLM provider instance.
    
    Raises:
        ValueError: If provider type is unknown.
    """
    providers = {
        LLMProviderType.OLLAMA: OllamaProvider,
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.GEMINI: GeminiProvider,
        LLMProviderType.CLAUDE: ClaudeProvider,
    }
    
    if provider_type not in providers:
        raise ValueError(f"Unknown provider type: {provider_type}")
    
    provider_class = providers[provider_type]
    
    # Use default model if not specified
    if model is None:
        model = DEFAULT_MODELS.get(provider_type)
    
    return provider_class(model=model, **kwargs)


def get_available_providers() -> dict[str, dict]:
    """Get information about available LLM providers.
    
    Returns:
        Dict with provider info including availability status.
    """
    providers_info = {}
    
    for provider_type in LLMProviderType:
        try:
            provider = create_llm_provider(provider_type)
            providers_info[provider_type.value] = {
                "name": provider.name,
                "type": "offline" if provider.is_offline else "cloud",
                "available": provider.is_available(),
                "default_model": DEFAULT_MODELS.get(provider_type, ""),
                "model": provider.model,
            }
        except Exception as e:
            providers_info[provider_type.value] = {
                "name": provider_type.value.title(),
                "type": "unknown",
                "available": False,
                "default_model": DEFAULT_MODELS.get(provider_type, ""),
                "error": str(e),
            }
    
    return providers_info
