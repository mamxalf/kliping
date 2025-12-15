"""Interactive prompts for Clipper CLI.

This module contains all the interactive prompt functions using InquirerPy.
"""

import os
from pathlib import Path
from typing import Optional

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from InquirerPy.validator import PathValidator

from clipper_cli.config import settings, save_config_value
from clipper_cli.license import validate_key_format


# Video file extensions
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v"}


def prompt_license_key() -> Optional[str]:
    """Prompt user to enter a license key."""
    key = inquirer.text(
        message="Enter License Key:",
        validate=lambda x: validate_key_format(x) or "Invalid format. Expected: CLIPPER-XXXX-XXXX-XXXX-XXXX",
        transformer=lambda x: x.upper(),
    ).execute()
    
    return key.upper().strip() if key else None


def prompt_main_menu() -> str:
    """Display main menu and get selection."""
    choices = [
        Choice(value="process", name="🎬 Process Single Video"),
        Choice(value="batch", name="📁 Batch Process Videos"),
        Separator(),
        Choice(value="settings", name="⚙️  Settings"),
        Choice(value="providers", name="📋 View Providers"),
        Choice(value="check", name="🔍 System Check"),
        Choice(value="license", name="🔑 License Info"),
        Separator(),
        Choice(value="exit", name="🚪 Exit"),
    ]
    
    return inquirer.select(
        message="What would you like to do?",
        choices=choices,
        default="process",
    ).execute()


def prompt_settings_menu() -> str:
    """Display settings menu and get selection."""
    choices = [
        Choice(value="api_keys", name="🔐 API Keys"),
        Choice(value="defaults", name="📊 Default Settings"),
        Choice(value="providers", name="🔄 Default Providers"),
        Separator(),
        Choice(value="back", name="⬅️  Back to Main Menu"),
    ]
    
    return inquirer.select(
        message="Settings:",
        choices=choices,
        default="api_keys",
    ).execute()


def prompt_video_file(start_path: str = ".") -> Optional[str]:
    """Prompt user to select a video file."""
    # First, let user choose input method
    method = inquirer.select(
        message="How would you like to select the video?",
        choices=[
            Choice(value="browse", name="📁 Browse files"),
            Choice(value="path", name="📝 Enter path manually"),
            Choice(value="back", name="⬅️  Back"),
        ],
    ).execute()
    
    if method == "back":
        return None
    
    if method == "path":
        path = inquirer.filepath(
            message="Enter video file path:",
            validate=PathValidator(is_file=True, message="Please enter a valid file path"),
            only_files=True,
        ).execute()
        return path
    
    # Browse mode - list directory
    current_dir = Path(start_path).resolve()
    
    while True:
        items = []
        
        # Add parent directory option
        if current_dir.parent != current_dir:
            items.append(Choice(value="..", name="📁 .. (Parent Directory)"))
        
        # List directories first
        try:
            for item in sorted(current_dir.iterdir()):
                if item.is_dir() and not item.name.startswith("."):
                    items.append(Choice(value=str(item), name=f"📁 {item.name}"))
        except PermissionError:
            pass
        
        # Then list video files
        try:
            for item in sorted(current_dir.iterdir()):
                if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS:
                    size_mb = item.stat().st_size / (1024 * 1024)
                    items.append(Choice(value=str(item), name=f"🎬 {item.name} ({size_mb:.1f} MB)"))
        except PermissionError:
            pass
        
        if not items:
            items.append(Choice(value="empty", name="(No video files found)"))
        
        items.append(Separator())
        items.append(Choice(value="cancel", name="❌ Cancel"))
        
        selection = inquirer.select(
            message=f"Select video file ({current_dir}):",
            choices=items,
            max_height="70%",
        ).execute()
        
        if selection == "cancel" or selection == "empty":
            return None
        
        if selection == "..":
            current_dir = current_dir.parent
            continue
        
        selected_path = Path(selection)
        
        if selected_path.is_dir():
            current_dir = selected_path
            continue
        
        if selected_path.is_file():
            return str(selected_path)
    
    return None


def prompt_batch_folder(start_path: str = ".") -> Optional[str]:
    """Prompt user to select a folder for batch processing."""
    method = inquirer.select(
        message="How would you like to select the folder?",
        choices=[
            Choice(value="browse", name="📁 Browse folders"),
            Choice(value="path", name="📝 Enter path manually"),
            Choice(value="back", name="⬅️  Back"),
        ],
    ).execute()
    
    if method == "back":
        return None
    
    if method == "path":
        path = inquirer.filepath(
            message="Enter folder path:",
            validate=PathValidator(is_dir=True, message="Please enter a valid directory path"),
            only_directories=True,
        ).execute()
        return path
    
    # Browse mode
    current_dir = Path(start_path).resolve()
    
    while True:
        items = []
        
        # Count video files in current dir
        video_count = sum(1 for f in current_dir.glob("*") 
                         if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS)
        
        items.append(Choice(
            value="select", 
            name=f"✅ Select this folder ({video_count} videos)"
        ))
        items.append(Separator())
        
        # Add parent directory option
        if current_dir.parent != current_dir:
            items.append(Choice(value="..", name="📁 .. (Parent Directory)"))
        
        # List directories
        try:
            for item in sorted(current_dir.iterdir()):
                if item.is_dir() and not item.name.startswith("."):
                    sub_video_count = sum(1 for f in item.glob("*") 
                                         if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS)
                    items.append(Choice(value=str(item), name=f"📁 {item.name} ({sub_video_count} videos)"))
        except PermissionError:
            pass
        
        items.append(Separator())
        items.append(Choice(value="cancel", name="❌ Cancel"))
        
        selection = inquirer.select(
            message=f"Select folder ({current_dir}):",
            choices=items,
            max_height="70%",
        ).execute()
        
        if selection == "cancel":
            return None
        
        if selection == "select":
            return str(current_dir)
        
        if selection == "..":
            current_dir = current_dir.parent
            continue
        
        selected_path = Path(selection)
        if selected_path.is_dir():
            current_dir = selected_path
    
    return None


def prompt_transcriber() -> str:
    """Prompt user to select transcription provider."""
    from clipper_cli.transcription import WhisperTranscriber, AssemblyAITranscriber
    
    # Check availability
    try:
        whisper = WhisperTranscriber()
        whisper_available = whisper.is_available()
    except Exception:
        whisper_available = False
    
    try:
        aai = AssemblyAITranscriber()
        aai_available = aai.is_available()
    except Exception:
        aai_available = False
    
    choices = [
        Choice(
            value="whisper",
            name=f"🎤 Whisper (Offline) {'✓' if whisper_available else '✗ Not installed'}",
            enabled=whisper_available,
        ),
        Choice(
            value="assemblyai",
            name=f"☁️  AssemblyAI (Cloud) {'✓' if aai_available else '✗ No API key'}",
            enabled=aai_available,
        ),
    ]
    
    return inquirer.select(
        message="Select transcription provider:",
        choices=choices,
        default="whisper" if whisper_available else "assemblyai",
    ).execute()


def prompt_llm_provider() -> tuple[str, Optional[str]]:
    """Prompt user to select LLM provider and optionally model."""
    from clipper_cli.llm.factory import get_available_providers
    
    providers = get_available_providers()
    
    choices = []
    default = None
    
    provider_icons = {
        "ollama": "🦙",
        "openai": "🤖",
        "gemini": "✨",
        "claude": "🧠",
    }
    
    for name, info in providers.items():
        icon = provider_icons.get(name.lower(), "🔹")
        status = "✓" if info["available"] else "✗"
        model = info.get("default_model", "")
        
        choice = Choice(
            value=name.lower(),
            name=f"{icon} {name.title()} ({info['type']}) {status} - {model}",
            enabled=info["available"],
        )
        choices.append(choice)
        
        if info["available"] and default is None:
            default = name.lower()
    
    provider = inquirer.select(
        message="Select LLM provider:",
        choices=choices,
        default=default,
    ).execute()
    
    # Ask if user wants to specify a different model
    use_custom = inquirer.confirm(
        message="Use custom model? (default: use provider's default model)",
        default=False,
    ).execute()
    
    model = None
    if use_custom:
        model = inquirer.text(
            message="Enter model name:",
            default=providers[provider.title()].get("default_model", ""),
        ).execute()
    
    return provider, model


def prompt_clip_settings() -> dict:
    """Prompt user for clip generation settings."""
    num_clips = inquirer.number(
        message="Number of clips to generate:",
        default=5,
        min_allowed=1,
        max_allowed=20,
    ).execute()
    
    min_duration = inquirer.number(
        message="Minimum clip duration (seconds):",
        default=15,
        min_allowed=5,
        max_allowed=60,
    ).execute()
    
    max_duration = inquirer.number(
        message="Maximum clip duration (seconds):",
        default=60,
        min_allowed=15,
        max_allowed=180,
    ).execute()
    
    # Ensure max >= min
    if max_duration < min_duration:
        max_duration = min_duration + 30
    
    language = inquirer.select(
        message="Video language:",
        choices=[
            Choice(value="auto", name="🌐 Auto-detect"),
            Choice(value="en", name="🇺🇸 English"),
            Choice(value="id", name="🇮🇩 Indonesian"),
            Choice(value="es", name="🇪🇸 Spanish"),
            Choice(value="fr", name="🇫🇷 French"),
            Choice(value="de", name="🇩🇪 German"),
            Choice(value="ja", name="🇯🇵 Japanese"),
            Choice(value="ko", name="🇰🇷 Korean"),
            Choice(value="zh", name="🇨🇳 Chinese"),
        ],
        default="auto",
    ).execute()
    
    return {
        "num_clips": int(num_clips),
        "min_duration": int(min_duration),
        "max_duration": int(max_duration),
        "language": language,
    }


def prompt_output_directory(default: str = "./output") -> str:
    """Prompt user for output directory."""
    use_custom = inquirer.confirm(
        message=f"Use custom output directory? (default: {default})",
        default=False,
    ).execute()
    
    if not use_custom:
        return default
    
    path = inquirer.filepath(
        message="Enter output directory:",
        default=default,
        only_directories=True,
    ).execute()
    
    return path


def prompt_api_key_setting() -> Optional[tuple[str, str]]:
    """Prompt user to set an API key."""
    choices = [
        Choice(value="ASSEMBLYAI_API_KEY", name="AssemblyAI API Key"),
        Choice(value="OPENAI_API_KEY", name="OpenAI API Key"),
        Choice(value="GEMINI_API_KEY", name="Gemini API Key"),
        Choice(value="ANTHROPIC_API_KEY", name="Anthropic API Key"),
        Separator(),
        Choice(value="back", name="⬅️  Back"),
    ]
    
    key_name = inquirer.select(
        message="Select API key to configure:",
        choices=choices,
    ).execute()
    
    if key_name == "back":
        return None
    
    value = inquirer.secret(
        message=f"Enter {key_name}:",
        transformer=lambda x: "*" * len(x) if x else "",
    ).execute()
    
    if value:
        return key_name, value
    return None


def prompt_confirm_processing(config: dict) -> bool:
    """Confirm processing with current settings."""
    from rich.console import Console
    from rich.table import Table
    from rich import box
    
    console = Console()
    
    table = Table(title="Processing Configuration", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Video", Path(config["video_path"]).name)
    table.add_row("Transcriber", config["transcriber"].title())
    table.add_row("LLM Provider", config["llm_provider"].title())
    if config.get("llm_model"):
        table.add_row("LLM Model", config["llm_model"])
    table.add_row("Num Clips", str(config["num_clips"]))
    table.add_row("Duration", f"{config['min_duration']}s - {config['max_duration']}s")
    table.add_row("Language", config["language"])
    table.add_row("Output Dir", config["output_dir"])
    
    console.print(table)
    console.print()
    
    return inquirer.confirm(
        message="Start processing?",
        default=True,
    ).execute()


def prompt_whisper_model() -> str:
    """Prompt user to select Whisper model size."""
    choices = [
        Choice(value="tiny", name="Tiny (fastest, least accurate)"),
        Choice(value="base", name="Base (balanced) ⭐"),
        Choice(value="small", name="Small (better accuracy)"),
        Choice(value="medium", name="Medium (good accuracy)"),
        Choice(value="large", name="Large (best accuracy, slowest)"),
    ]
    
    return inquirer.select(
        message="Select Whisper model:",
        choices=choices,
        default="base",
    ).execute()


def prompt_continue_or_exit() -> bool:
    """Ask user if they want to continue or go back to menu."""
    return inquirer.confirm(
        message="Process another video?",
        default=True,
    ).execute()
