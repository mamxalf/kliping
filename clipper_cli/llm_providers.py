"""
LLM Providers for viral analysis.
Supports Ollama (local, free), OpenAI, and Google Gemini.
"""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from rich.console import Console

console = Console()


class LLMProvider(str, Enum):
    """Available LLM providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"


PROVIDER_DESCRIPTIONS = {
    LLMProvider.OLLAMA: "Ollama (Local, Gratis) - Perlu install Ollama",
    LLMProvider.OPENAI: "OpenAI GPT-4 (Cloud) - Perlu API key",
    LLMProvider.GEMINI: "Google Gemini (Cloud) - Perlu API key"
}


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    provider: LLMProvider


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate response from LLM."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama provider for local LLM inference."""
    
    def __init__(self, model: str = "llama3.2"):
        self.model = model
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            import ollama
            self._client = ollama
        return self._client
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            client = self._get_client()
            client.list()
            return True
        except Exception:
            return False
    
    def list_models(self) -> list[str]:
        """List available models."""
        try:
            client = self._get_client()
            response = client.list()
            return [model.model for model in response.models]
        except Exception:
            return []
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate response using Ollama."""
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat(
            model=self.model,
            messages=messages
        )
        
        return LLMResponse(
            content=response.message.content,
            model=self.model,
            provider=LLMProvider.OLLAMA
        )


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider."""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client
    
    def is_available(self) -> bool:
        """Check if API key is available."""
        return bool(self.api_key)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate response using OpenAI."""
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider=LLMProvider.OPENAI
        )


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""
    
    def __init__(self, model: str = "gemini-2.0-flash", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client
    
    def is_available(self) -> bool:
        """Check if API key is available."""
        return bool(self.api_key)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate response using Gemini."""
        client = self._get_client()
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = client.generate_content(full_prompt)
        
        return LLMResponse(
            content=response.text,
            model=self.model,
            provider=LLMProvider.GEMINI
        )


def get_provider(provider: LLMProvider, **kwargs) -> BaseLLMProvider:
    """Factory function to get LLM provider instance."""
    providers = {
        LLMProvider.OLLAMA: OllamaProvider,
        LLMProvider.OPENAI: OpenAIProvider,
        LLMProvider.GEMINI: GeminiProvider
    }
    return providers[provider](**kwargs)


def get_available_providers() -> list[tuple[LLMProvider, str]]:
    """Get list of available providers with their status."""
    result = []
    
    # Check Ollama
    ollama_provider = OllamaProvider()
    ollama_status = "✓ Ready" if ollama_provider.is_available() else "✗ Not running"
    result.append((LLMProvider.OLLAMA, f"{PROVIDER_DESCRIPTIONS[LLMProvider.OLLAMA]} [{ollama_status}]"))
    
    # Check OpenAI
    openai_provider = OpenAIProvider()
    openai_status = "✓ API key found" if openai_provider.is_available() else "✗ No API key"
    result.append((LLMProvider.OPENAI, f"{PROVIDER_DESCRIPTIONS[LLMProvider.OPENAI]} [{openai_status}]"))
    
    # Check Gemini
    gemini_provider = GeminiProvider()
    gemini_status = "✓ API key found" if gemini_provider.is_available() else "✗ No API key"
    result.append((LLMProvider.GEMINI, f"{PROVIDER_DESCRIPTIONS[LLMProvider.GEMINI]} [{gemini_status}]"))
    
    return result
