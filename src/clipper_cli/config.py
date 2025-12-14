"""Configuration management for Clipper CLI."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Transcription providers
    assemblyai_api_key: Optional[str] = Field(None, alias="ASSEMBLYAI_API_KEY")
    
    # LLM providers
    ollama_host: str = Field("http://localhost:11434", alias="OLLAMA_HOST")
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    gemini_api_key: Optional[str] = Field(None, alias="GEMINI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    
    # Default settings
    default_transcriber: str = Field("whisper", alias="DEFAULT_TRANSCRIBER")
    default_llm_provider: str = Field("ollama", alias="DEFAULT_LLM_PROVIDER")
    default_whisper_model: str = Field("base", alias="DEFAULT_WHISPER_MODEL")
    default_ollama_model: str = Field("llama3.2", alias="DEFAULT_OLLAMA_MODEL")
    default_openai_model: str = Field("gpt-4o-mini", alias="DEFAULT_OPENAI_MODEL")
    default_gemini_model: str = Field("gemini-2.0-flash-exp", alias="DEFAULT_GEMINI_MODEL")
    default_claude_model: str = Field("claude-3-5-sonnet-20241022", alias="DEFAULT_CLAUDE_MODEL")
    
    # Processing defaults
    default_min_duration: int = Field(15, alias="DEFAULT_MIN_DURATION")
    default_max_duration: int = Field(60, alias="DEFAULT_MAX_DURATION")
    default_num_clips: int = Field(5, alias="DEFAULT_NUM_CLIPS")
    default_output_dir: str = Field("./output", alias="DEFAULT_OUTPUT_DIR")


def get_config_path() -> Path:
    """Get the path to the config directory."""
    config_dir = Path.home() / ".clipper-cli"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_env_file_path() -> Path:
    """Get the path to the .env file."""
    return get_config_path() / ".env"


def load_settings() -> Settings:
    """Load settings from environment and .env file."""
    env_file = get_env_file_path()
    if env_file.exists():
        # Load from user config directory
        return Settings(_env_file=str(env_file))
    return Settings()


def save_config_value(key: str, value: str) -> None:
    """Save a configuration value to the .env file."""
    env_file = get_env_file_path()
    
    # Read existing content
    existing_lines: list[str] = []
    if env_file.exists():
        with open(env_file, "r") as f:
            existing_lines = f.readlines()
    
    # Update or add the key
    key_found = False
    new_lines: list[str] = []
    for line in existing_lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            key_found = True
        else:
            new_lines.append(line)
    
    if not key_found:
        new_lines.append(f"{key}={value}\n")
    
    # Write back
    with open(env_file, "w") as f:
        f.writelines(new_lines)


def get_config_value(key: str) -> Optional[str]:
    """Get a configuration value from environment or .env file."""
    # First check environment
    if key in os.environ:
        return os.environ[key]
    
    # Then check .env file
    env_file = get_env_file_path()
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    return line.strip().split("=", 1)[1]
    
    return None


# Global settings instance
settings = load_settings()
