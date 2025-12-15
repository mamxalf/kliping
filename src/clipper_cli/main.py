"""Clipper CLI - Main entry point."""

import time
from pathlib import Path
from typing import Optional, Annotated

import typer
from rich.table import Table
from rich import box

from clipper_cli import __version__
from clipper_cli.models import (
    ProcessingConfig,
    TranscriberType,
    LLMProviderType,
)
from clipper_cli.config import (
    settings,
    save_config_value,
    get_config_value,
    get_env_file_path,
)
from clipper_cli.utils.console import (
    console,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_step,
    create_providers_table,
    print_result_summary,
    format_duration,
)
from clipper_cli.video.processor import VideoProcessor
from clipper_cli.video.clipper import ClipGenerator
from clipper_cli.transcription import WhisperTranscriber, AssemblyAITranscriber
from clipper_cli.llm.factory import create_llm_provider, get_available_providers, LLMProviderType as LLMType
from clipper_cli.analysis import ViralDetector
from clipper_cli.batch.processor import BatchProcessor
from clipper_cli.batch.reporter import BatchReporter


# Create Typer app
app = typer.Typer(
    name="clipper",
    help="🎬 Cut long videos into viral clips using AI",
    add_completion=False,
    rich_markup_mode="rich",
)


# Config subcommand
config_app = typer.Typer(help="Manage configuration")
app.add_typer(config_app, name="config")


@app.command()
def process(
    video_path: Annotated[Path, typer.Argument(help="Path to video file")],
    output_dir: Annotated[str, typer.Option("--output-dir", "-o", help="Output directory")] = "./output",
    transcribe: Annotated[str, typer.Option("--transcribe", "-t", help="Transcription provider: whisper, assemblyai")] = "whisper",
    llm: Annotated[str, typer.Option("--llm", "-l", help="LLM provider: ollama, openai, gemini, claude")] = "ollama",
    llm_model: Annotated[Optional[str], typer.Option("--llm-model", help="Specific LLM model to use")] = None,
    whisper_model: Annotated[str, typer.Option("--whisper-model", help="Whisper model size")] = "base",
    num_clips: Annotated[int, typer.Option("--num-clips", "-n", help="Number of clips to generate")] = 5,
    min_duration: Annotated[int, typer.Option("--min-duration", help="Minimum clip duration (seconds)")] = 15,
    max_duration: Annotated[int, typer.Option("--max-duration", help="Maximum clip duration (seconds)")] = 60,
    language: Annotated[str, typer.Option("--language", "-L", help="Video language (auto for detection)")] = "auto",
):
    """Process a single video and generate viral clips."""
    
    # Validate video path
    if not video_path.exists():
        print_error(f"Video file not found: {video_path}")
        raise typer.Exit(1)
    
    # Parse provider types
    try:
        transcriber_type = TranscriberType(transcribe.lower())
    except ValueError:
        print_error(f"Invalid transcriber: {transcribe}. Use: whisper, assemblyai")
        raise typer.Exit(1)
    
    try:
        llm_provider_type = LLMProviderType(llm.lower())
    except ValueError:
        print_error(f"Invalid LLM provider: {llm}. Use: ollama, openai, gemini, claude")
        raise typer.Exit(1)
    
    # Print header
    subtitle = f"Transcribe: {transcriber_type.value.title()} | LLM: {llm_provider_type.value.title()}"
    print_header("Video Clipper CLI", subtitle)
    
    console.print(f"\n📁 Processing: [cyan]{video_path.name}[/cyan]\n")
    
    start_time = time.time()
    
    try:
        # Load video
        with VideoProcessor(str(video_path)) as processor:
            metadata = processor.get_metadata()
            
            # Extract audio
            console.print("🔊 Extracting audio...", end=" ")
            audio_path = processor.extract_audio()
            console.print("[green]✓[/green]")
            
            # Transcribe
            console.print(f"📝 Transcribing with {transcriber_type.value.title()}...")
            
            if transcriber_type == TranscriberType.WHISPER:
                transcriber = WhisperTranscriber(model_name=whisper_model)
            else:
                transcriber = AssemblyAITranscriber()
            
            if not transcriber.is_available():
                if transcriber_type == TranscriberType.ASSEMBLYAI:
                    print_error("AssemblyAI API key not configured. Run: clipper config set ASSEMBLYAI_API_KEY your_key")
                else:
                    print_error("Whisper not available. Install: pip install openai-whisper")
                raise typer.Exit(1)
            
            transcript = transcriber.transcribe(audio_path, language=language)
            
            print_step(f"Detected language: {transcript.language}", indent=1)
            print_step(f"Duration: {format_duration(transcript.duration)}", indent=1)
            print_step(f"Segments: {len(transcript.segments)}", indent=1)
            
            # Analyze for viral moments
            console.print(f"\n🔍 Analyzing for viral moments...")
            
            llm_provider = create_llm_provider(llm_provider_type, model=llm_model)
            
            if not llm_provider.is_available():
                print_error(f"{llm_provider.name} not available. Check configuration.")
                raise typer.Exit(1)
            
            print_step(f"Using model: {llm_provider.model}", indent=1)
            
            detector = ViralDetector(llm_provider)
            potential_clips = detector.detect_viral_moments_sync(
                transcript,
                num_clips=num_clips,
                min_duration=min_duration,
                max_duration=max_duration,
            )
            
            print_step(f"Found {len(potential_clips)} potential clips", indent=1)
            
            if not potential_clips:
                print_warning("No potential viral clips found in the video.")
                raise typer.Exit(0)
            
            # Generate clips
            console.print(f"\n✂️  Generating clips...")
            
            clipper = ClipGenerator(str(video_path), output_dir)
            clip_results = clipper.generate_clips(potential_clips, show_progress=True)
            
            # Create result object for summary
            from clipper_cli.models import VideoResult
            result = VideoResult(
                source_file=str(video_path),
                clips=clip_results,
                transcript=transcript,
                transcriber_used=transcriber_type,
                llm_provider_used=llm_provider_type,
                llm_model_used=llm_provider.model,
                processing_time=time.time() - start_time,
                success=True,
            )
            
            # Print summary
            print_result_summary(result, output_dir)
    
    except Exception as e:
        print_error(f"Processing failed: {e}")
        raise typer.Exit(1)


@app.command()
def batch(
    input_path: Annotated[Path, typer.Argument(help="Directory containing videos")],
    output_dir: Annotated[str, typer.Option("--output-dir", "-o", help="Output directory")] = "./output",
    pattern: Annotated[Optional[list[str]], typer.Option("--pattern", "-p", help="File patterns to match")] = None,
    transcribe: Annotated[str, typer.Option("--transcribe", "-t", help="Transcription provider")] = "whisper",
    llm: Annotated[str, typer.Option("--llm", "-l", help="LLM provider")] = "ollama",
    llm_model: Annotated[Optional[str], typer.Option("--llm-model", help="Specific LLM model")] = None,
    whisper_model: Annotated[str, typer.Option("--whisper-model", help="Whisper model size")] = "base",
    num_clips: Annotated[int, typer.Option("--num-clips", "-n", help="Clips per video")] = 5,
    min_duration: Annotated[int, typer.Option("--min-duration", help="Min clip duration")] = 15,
    max_duration: Annotated[int, typer.Option("--max-duration", help="Max clip duration")] = 60,
    language: Annotated[str, typer.Option("--language", "-L", help="Video language")] = "auto",
    workers: Annotated[int, typer.Option("--workers", "-w", help="Parallel workers")] = 2,
    resume: Annotated[bool, typer.Option("--resume", help="Resume interrupted batch")] = False,
    report_format: Annotated[str, typer.Option("--report-format", help="Report format: json, csv, html")] = "json",
):
    """Process multiple videos in batch."""
    
    # Validate input path
    if not input_path.exists():
        print_error(f"Path not found: {input_path}")
        raise typer.Exit(1)
    
    # Parse provider types
    try:
        transcriber_type = TranscriberType(transcribe.lower())
    except ValueError:
        print_error(f"Invalid transcriber: {transcribe}")
        raise typer.Exit(1)
    
    try:
        llm_provider_type = LLMProviderType(llm.lower())
    except ValueError:
        print_error(f"Invalid LLM provider: {llm}")
        raise typer.Exit(1)
    
    # Print header
    subtitle = f"Transcribe: {transcriber_type.value.title()} | LLM: {llm_provider_type.value.title()}"
    print_header("Video Clipper CLI - BATCH", subtitle)
    
    # Create config
    config = ProcessingConfig(
        transcriber=transcriber_type,
        llm_provider=llm_provider_type,
        llm_model=llm_model,
        whisper_model=whisper_model,
        min_duration=min_duration,
        max_duration=max_duration,
        num_clips=num_clips,
        language=language,
        output_dir=output_dir,
    )
    
    # Process batch
    processor = BatchProcessor(config, output_dir)
    result = processor.process_batch(
        str(input_path),
        patterns=pattern,
        max_workers=workers,
        resume=resume,
    )
    
    # Generate and print report
    reporter = BatchReporter(output_dir)
    report_path = reporter.generate_report(result, format=report_format)
    reporter.print_summary(result)
    
    console.print(f"\n📄 Report saved: [cyan]{report_path}[/cyan]")


@app.command()
def providers():
    """List available LLM providers and their status."""
    print_header("Available Providers")
    
    providers_info = get_available_providers()
    console.print(create_providers_table(providers_info))
    
    # Also show transcription providers
    console.print("\n[bold]Transcription Providers:[/bold]\n")
    
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Provider")
    table.add_column("Type")
    table.add_column("Status")
    
    # Whisper
    try:
        whisper = WhisperTranscriber()
        whisper_status = "[green]✓ Ready[/green]" if whisper.is_available() else "[red]✗ Not available[/red]"
    except Exception:
        whisper_status = "[red]✗ Not available[/red]"
    table.add_row("Whisper", "Offline", whisper_status)
    
    # AssemblyAI
    try:
        aai = AssemblyAITranscriber()
        aai_status = "[green]✓ Ready[/green]" if aai.is_available() else "[red]✗ Not configured[/red]"
    except Exception:
        aai_status = "[red]✗ Not configured[/red]"
    table.add_row("AssemblyAI", "Cloud", aai_status)
    
    console.print(table)


@app.command()
def check():
    """Check system requirements and configuration."""
    print_header("System Check")
    
    console.print("\n[bold]Dependencies:[/bold]\n")
    
    checks = []
    
    # FFmpeg
    import subprocess
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        ffmpeg_ok = result.returncode == 0
    except Exception:
        ffmpeg_ok = False
    
    checks.append(("FFmpeg", ffmpeg_ok, "Required for video processing"))
    
    # Whisper
    try:
        import whisper
        whisper_ok = True
    except ImportError:
        whisper_ok = False
    checks.append(("Whisper", whisper_ok, "For offline transcription"))
    
    # MoviePy
    try:
        import moviepy
        moviepy_ok = True
    except ImportError:
        moviepy_ok = False
    checks.append(("MoviePy", moviepy_ok, "For video processing"))
    
    # Ollama
    try:
        import ollama
        client = ollama.Client()
        client.list()
        ollama_ok = True
    except Exception:
        ollama_ok = False
    checks.append(("Ollama", ollama_ok, "For local LLM (optional)"))
    
    # Print results
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Component")
    table.add_column("Status")
    table.add_column("Notes")
    
    for name, ok, notes in checks:
        status = "[green]✓ OK[/green]" if ok else "[red]✗ Missing[/red]"
        table.add_row(name, status, notes)
    
    console.print(table)
    
    # Check API keys
    console.print("\n[bold]API Keys:[/bold]\n")
    
    api_keys = [
        ("ASSEMBLYAI_API_KEY", settings.assemblyai_api_key),
        ("OPENAI_API_KEY", settings.openai_api_key),
        ("GEMINI_API_KEY", settings.gemini_api_key),
        ("ANTHROPIC_API_KEY", settings.anthropic_api_key),
    ]
    
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Key")
    table.add_column("Status")
    
    for name, value in api_keys:
        if value:
            status = f"[green]✓ Set[/green] ({value[:8]}...)"
        else:
            status = "[dim]Not set[/dim]"
        table.add_row(name, status)
    
    console.print(table)
    
    # Config file location
    console.print(f"\n📁 Config file: [cyan]{get_env_file_path()}[/cyan]")


@app.command()
def report(
    report_path: Annotated[Path, typer.Argument(help="Path to report file")],
):
    """View a batch processing report."""
    
    if not report_path.exists():
        print_error(f"Report file not found: {report_path}")
        raise typer.Exit(1)
    
    import json
    
    with open(report_path, "r") as f:
        data = json.load(f)
    
    print_header("Batch Report")
    
    # Summary
    summary = data.get("summary", {})
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Total Videos: {summary.get('total_videos', 0)}")
    console.print(f"  Successful: [green]{summary.get('successful', 0)}[/green]")
    console.print(f"  Failed: [red]{summary.get('failed', 0)}[/red]")
    console.print(f"  Total Clips: [cyan]{summary.get('total_clips', 0)}[/cyan]")
    console.print(f"  Processing Time: {summary.get('processing_time_formatted', 'N/A')}")
    
    # Top clips
    top_clips = data.get("top_clips", [])
    if top_clips:
        console.print("\n[bold]🏆 Top Clips:[/bold]")
        for i, clip in enumerate(top_clips[:5], 1):
            console.print(f"  {i}. [cyan]{Path(clip['file']).name}[/cyan] (Score: {clip['score']:.1f})")
    
    # Errors
    errors = data.get("errors", {})
    if errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for path, error in errors.items():
            console.print(f"  [red]✗[/red] {Path(path).name}: {error}")


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Configuration key")],
    value: Annotated[str, typer.Argument(help="Configuration value")],
):
    """Set a configuration value."""
    save_config_value(key, value)
    print_success(f"Set {key}")


@config_app.command("get")
def config_get(
    key: Annotated[str, typer.Argument(help="Configuration key")],
):
    """Get a configuration value."""
    value = get_config_value(key)
    if value:
        # Mask sensitive values
        if "KEY" in key.upper() or "SECRET" in key.upper():
            display_value = value[:8] + "..." if len(value) > 8 else "***"
        else:
            display_value = value
        console.print(f"{key}={display_value}")
    else:
        console.print(f"[dim]{key} is not set[/dim]")


@config_app.command("show")
def config_show():
    """Show all configuration values."""
    env_file = get_env_file_path()
    
    console.print(f"[bold]Config file:[/bold] {env_file}\n")
    
    if env_file.exists():
        with open(env_file, "r") as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    # Mask sensitive values
                    if "KEY" in key.upper() or "SECRET" in key.upper():
                        display_value = value[:8] + "..." if len(value) > 8 else "***"
                    else:
                        display_value = value
                    console.print(f"  {key}=[cyan]{display_value}[/cyan]")
    else:
        console.print("[dim]No configuration file found.[/dim]")


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold]Clipper CLI[/bold] v{__version__}")


@app.command(name="interactive")
def interactive_mode():
    """Start interactive mode."""
    from clipper_cli.interactive import start_interactive
    start_interactive()


def main():
    """Main entry point with license check and interactive default."""
    import sys
    from clipper_cli.license import get_license_manager
    
    # Check license first
    license_mgr = get_license_manager()
    if not license_mgr.is_activated():
        from clipper_cli.interactive import activate_license
        if not activate_license():
            sys.exit(1)
    
    # If no arguments, run interactive mode
    if len(sys.argv) == 1:
        from clipper_cli.interactive import start_interactive
        start_interactive()
    else:
        app()


if __name__ == "__main__":
    main()

