"""Main interactive application for Clipper CLI.

This module provides the interactive mode entry point and main application loop.
"""

import sys
import time
from pathlib import Path
from typing import Optional

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from clipper_cli import __version__
from clipper_cli.license import get_license_manager, LicenseManager
from clipper_cli.config import settings, save_config_value, get_env_file_path
from clipper_cli.models import TranscriberType, LLMProviderType

from clipper_cli.interactive.screens import (
    console,
    show_welcome,
    show_activation_screen,
    show_main_menu_header,
    show_success_message,
    show_error_message,
    show_warning_message,
    show_info_message,
    show_goodbye,
    show_settings_header,
    show_license_info,
    show_providers_status,
    show_clip_results,
)

from clipper_cli.interactive.prompts import (
    prompt_license_key,
    prompt_main_menu,
    prompt_settings_menu,
    prompt_video_file,
    prompt_batch_folder,
    prompt_transcriber,
    prompt_llm_provider,
    prompt_clip_settings,
    prompt_output_directory,
    prompt_api_key_setting,
    prompt_confirm_processing,
    prompt_whisper_model,
    prompt_continue_or_exit,
)


def create_spinner(description: str):
    """Create a spinner progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )


def activate_license() -> bool:
    """
    Handle license activation flow.
    
    Returns:
        True if license is activated successfully, False otherwise.
    """
    license_mgr = get_license_manager()
    
    # Check if already activated
    if license_mgr.is_activated():
        return True
    
    # Show activation screen
    show_activation_screen()
    
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            key = prompt_license_key()
            
            if key is None:
                show_error_message("No key entered. Exiting...")
                return False
            
            success, message = license_mgr.activate(key)
            
            if success:
                show_success_message(message)
                console.print()
                time.sleep(1)
                return True
            else:
                remaining = max_attempts - attempt - 1
                if remaining > 0:
                    show_error_message(f"{message} ({remaining} attempts remaining)")
                else:
                    show_error_message(message)
        
        except KeyboardInterrupt:
            console.print()
            return False
    
    show_error_message("Maximum activation attempts reached. Please contact support.")
    return False


def process_single_video() -> None:
    """Handle single video processing flow."""
    # Select video file
    video_path = prompt_video_file()
    if not video_path:
        return
    
    # Select transcriber
    transcriber = prompt_transcriber()
    
    # If whisper, select model
    whisper_model = "base"
    if transcriber == "whisper":
        whisper_model = prompt_whisper_model()
    
    # Select LLM provider
    llm_provider, llm_model = prompt_llm_provider()
    
    # Clip settings
    clip_settings = prompt_clip_settings()
    
    # Output directory
    output_dir = prompt_output_directory()
    
    # Build config
    config = {
        "video_path": video_path,
        "transcriber": transcriber,
        "whisper_model": whisper_model,
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "output_dir": output_dir,
        **clip_settings,
    }
    
    # Confirm
    if not prompt_confirm_processing(config):
        show_info_message("Processing cancelled.")
        return
    
    # Process video
    _run_video_processing(config)


def _run_video_processing(config: dict) -> None:
    """Execute video processing with the given configuration."""
    from clipper_cli.video.processor import VideoProcessor
    from clipper_cli.video.clipper import ClipGenerator
    from clipper_cli.transcription import WhisperTranscriber, AssemblyAITranscriber
    from clipper_cli.llm.factory import create_llm_provider
    from clipper_cli.analysis import ViralDetector
    from clipper_cli.utils.console import format_duration
    
    video_path = Path(config["video_path"])
    
    console.print(f"\n[VIDEO] Processing: [cyan]{video_path.name}[/cyan]\n")
    
    start_time = time.time()
    
    try:
        with VideoProcessor(str(video_path)) as processor:
            # Extract audio with spinner
            with create_spinner("Extracting audio...") as progress:
                task = progress.add_task("Extracting audio...", total=None)
                audio_path = processor.extract_audio()
            console.print("[green][OK][/green] Audio extracted")
            
            # Transcribe with spinner
            console.print(f"\n[TRANSCRIBE] Using {config['transcriber'].title()}...")
            
            if config["transcriber"] == "whisper":
                transcriber = WhisperTranscriber(model_name=config["whisper_model"])
            else:
                transcriber = AssemblyAITranscriber()
            
            if not transcriber.is_available():
                show_error_message(f"{config['transcriber'].title()} is not available.")
                return
            
            with create_spinner(f"Transcribing video (this may take a while)...") as progress:
                task = progress.add_task("Transcribing...", total=None)
                transcript = transcriber.transcribe(audio_path, language=config["language"])
            
            console.print(f"  [dim]Language:[/dim] {transcript.language}")
            console.print(f"  [dim]Duration:[/dim] {format_duration(transcript.duration)}")
            console.print(f"  [dim]Segments:[/dim] {len(transcript.segments)}")
            console.print("[green][OK][/green] Transcription complete")
            
            # Analyze for viral moments with spinner
            console.print(f"\n[ANALYZE] Finding viral moments...")
            
            llm_type = LLMProviderType(config["llm_provider"])
            llm_provider = create_llm_provider(llm_type, model=config.get("llm_model"))
            
            if not llm_provider.is_available():
                show_error_message(f"{llm_provider.name} is not available.")
                return
            
            console.print(f"  [dim]Using model:[/dim] {llm_provider.model}")
            
            with create_spinner("Analyzing transcript with AI...") as progress:
                task = progress.add_task("Analyzing...", total=None)
                detector = ViralDetector(llm_provider)
                potential_clips = detector.detect_viral_moments_sync(
                    transcript,
                    num_clips=config["num_clips"],
                    min_duration=config["min_duration"],
                    max_duration=config["max_duration"],
                )
            
            console.print(f"  [dim]Found:[/dim] {len(potential_clips)} potential clips")
            console.print("[green][OK][/green] Analysis complete")
            
            if not potential_clips:
                show_warning_message("No potential viral clips found in the video.")
                return
            
            # Generate clips with progress
            console.print(f"\n[CLIPS] Generating {len(potential_clips)} clips...")
            
            clipper = ClipGenerator(str(video_path), config["output_dir"])
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Generating clips...", total=len(potential_clips))
                clip_results = []
                
                for clip in potential_clips:
                    result = clipper.generate_clip(clip)
                    if result:
                        clip_results.append(result)
                    progress.advance(task)
            
            console.print("[green][OK][/green] Clips generated")
            
            # Show results
            elapsed = time.time() - start_time
            console.print(f"\n[TIME] Completed in {format_duration(elapsed)}")
            
            show_clip_results(clip_results, config["output_dir"])
    
    except Exception as e:
        show_error_message(f"Processing failed: {e}")
        console.print_exception()


def process_batch_videos() -> None:
    """Handle batch video processing flow."""
    # Select folder
    folder_path = prompt_batch_folder()
    if not folder_path:
        return
    
    # Select transcriber
    transcriber = prompt_transcriber()
    
    # If whisper, select model
    whisper_model = "base"
    if transcriber == "whisper":
        whisper_model = prompt_whisper_model()
    
    # Select LLM provider
    llm_provider, llm_model = prompt_llm_provider()
    
    # Clip settings
    clip_settings = prompt_clip_settings()
    
    # Output directory
    output_dir = prompt_output_directory()
    
    # Confirm
    from InquirerPy import inquirer
    
    console.print(f"\n[DIR] Folder: [cyan]{folder_path}[/cyan]")
    console.print(f"[CONFIG] Transcriber: {transcriber.title()}")
    console.print(f"[CONFIG] LLM: {llm_provider.title()}")
    console.print()
    
    if not inquirer.confirm("Start batch processing?", default=True).execute():
        show_info_message("Batch processing cancelled.")
        return
    
    # Run batch processing
    from clipper_cli.models import ProcessingConfig
    from clipper_cli.batch.processor import BatchProcessor
    from clipper_cli.batch.reporter import BatchReporter
    
    config = ProcessingConfig(
        transcriber=TranscriberType(transcriber),
        llm_provider=LLMProviderType(llm_provider),
        llm_model=llm_model,
        whisper_model=whisper_model,
        min_duration=clip_settings["min_duration"],
        max_duration=clip_settings["max_duration"],
        num_clips=clip_settings["num_clips"],
        language=clip_settings["language"],
        output_dir=output_dir,
    )
    
    processor = BatchProcessor(config, output_dir)
    
    with create_spinner("Processing batch...") as progress:
        task = progress.add_task("Processing videos...", total=None)
        result = processor.process_batch(folder_path)
    
    # Generate and print report
    reporter = BatchReporter(output_dir)
    report_path = reporter.generate_report(result, format="json")
    reporter.print_summary(result)
    
    console.print(f"\n[REPORT] Report saved: [cyan]{report_path}[/cyan]")


def show_settings() -> None:
    """Handle settings menu."""
    while True:
        show_settings_header()
        
        choice = prompt_settings_menu()
        
        if choice == "back":
            return
        
        if choice == "api_keys":
            result = prompt_api_key_setting()
            if result:
                key_name, value = result
                save_config_value(key_name, value)
                show_success_message(f"Saved {key_name}")
        
        elif choice == "defaults":
            clip_settings = prompt_clip_settings()
            save_config_value("DEFAULT_MIN_DURATION", str(clip_settings["min_duration"]))
            save_config_value("DEFAULT_MAX_DURATION", str(clip_settings["max_duration"]))
            save_config_value("DEFAULT_NUM_CLIPS", str(clip_settings["num_clips"]))
            show_success_message("Default settings saved")
        
        elif choice == "providers":
            from InquirerPy import inquirer
            from InquirerPy.base.control import Choice
            
            transcriber = inquirer.select(
                message="Default transcriber:",
                choices=[
                    Choice(value="whisper", name="Whisper (Offline)"),
                    Choice(value="assemblyai", name="AssemblyAI (Cloud)"),
                ],
            ).execute()
            save_config_value("DEFAULT_TRANSCRIBER", transcriber)
            
            llm = inquirer.select(
                message="Default LLM provider:",
                choices=[
                    Choice(value="ollama", name="Ollama (Local)"),
                    Choice(value="openai", name="OpenAI"),
                    Choice(value="gemini", name="Gemini"),
                    Choice(value="claude", name="Claude"),
                ],
            ).execute()
            save_config_value("DEFAULT_LLM_PROVIDER", llm)
            
            show_success_message("Default providers saved")
        
        console.print()


def show_providers() -> None:
    """Show available providers and their status."""
    from clipper_cli.transcription import WhisperTranscriber, AssemblyAITranscriber
    from clipper_cli.llm.factory import get_available_providers
    
    with create_spinner("Checking providers...") as progress:
        task = progress.add_task("Checking...", total=None)
        
        # Get transcriber status
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
        
        transcribers = [
            {"name": "Whisper", "type": "Offline", "available": whisper_available},
            {"name": "AssemblyAI", "type": "Cloud", "available": aai_available},
        ]
        
        # Get LLM providers
        providers_info = get_available_providers()
        llm_providers = []
        
        for name, info in providers_info.items():
            llm_providers.append({
                "name": name,
                "type": info["type"],
                "available": info["available"],
                "model": info.get("default_model", "-"),
            })
    
    show_providers_status(transcribers, llm_providers)
    
    console.print()
    from InquirerPy import inquirer
    inquirer.confirm("Press Enter to continue...", default=True).execute()


def run_system_check() -> None:
    """Run system check and display results."""
    from clipper_cli.main import check
    check()
    
    console.print()
    from InquirerPy import inquirer
    inquirer.confirm("Press Enter to continue...", default=True).execute()


def show_license() -> None:
    """Show license information."""
    license_mgr = get_license_manager()
    info = license_mgr.get_license_info()
    
    if info:
        license_data = {
            "masked_key": info.masked_key,
            "activated_at": info.activated_at,
        }
    else:
        license_data = None
    
    show_license_info(license_data)
    
    console.print()
    from InquirerPy import inquirer
    inquirer.confirm("Press Enter to continue...", default=True).execute()


def start_interactive() -> None:
    """
    Start the interactive mode application.
    
    This is the main entry point for interactive mode.
    """
    license_mgr = get_license_manager()
    
    # Check license first
    if not license_mgr.is_activated():
        if not activate_license():
            sys.exit(1)
    
    # Main application loop
    while True:
        try:
            # Show welcome screen
            show_welcome(__version__, license_mgr.get_status_display())
            
            # Show main menu
            choice = prompt_main_menu()
            
            if choice == "exit":
                show_goodbye()
                break
            
            elif choice == "process":
                process_single_video()
            
            elif choice == "batch":
                process_batch_videos()
            
            elif choice == "settings":
                show_settings()
            
            elif choice == "providers":
                show_providers()
            
            elif choice == "check":
                run_system_check()
            
            elif choice == "license":
                show_license()
        
        except KeyboardInterrupt:
            console.print()
            show_goodbye()
            break
        
        except Exception as e:
            show_error_message(f"An error occurred: {e}")
            console.print_exception()
            
            from InquirerPy import inquirer
            if not inquirer.confirm("Continue?", default=True).execute():
                break


if __name__ == "__main__":
    start_interactive()
