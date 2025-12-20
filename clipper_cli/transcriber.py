"""
Transcriber module using faster-whisper for speech-to-text.
"""
from dataclasses import dataclass
from typing import Generator, Literal, Optional

from faster_whisper import WhisperModel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

# Available Whisper model sizes
ModelSize = Literal["tiny", "base", "small", "medium", "large-v3"]

MODEL_DESCRIPTIONS = {
    "tiny": "Tercepat, akurasi rendah (~75MB)",
    "base": "Seimbang untuk testing (~150MB)",
    "small": "Bagus untuk bahasa Indonesia (~500MB)",
    "medium": "Akurasi tinggi (~1.5GB)",
    "large-v3": "Akurasi terbaik (~3GB)"
}


@dataclass
class TranscriptSegment:
    """A segment of transcribed text with timing."""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Transcribed text
    
    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class TranscriptResult:
    """Complete transcription result."""
    segments: list[TranscriptSegment]
    language: str
    language_probability: float
    duration: float
    
    @property
    def full_text(self) -> str:
        return " ".join(seg.text for seg in self.segments)
    
    def get_text_in_range(self, start: float, end: float) -> str:
        """Get text within a time range."""
        return " ".join(
            seg.text for seg in self.segments 
            if seg.start >= start and seg.end <= end
        )


class Transcriber:
    """Wrapper for faster-whisper transcription."""
    
    def __init__(self, model_size: ModelSize = "base", device: str = "auto"):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Size of Whisper model to use
            device: "auto", "cpu", or "cuda"
        """
        self.model_size = model_size
        self.device = device
        self.model: Optional[WhisperModel] = None
    
    def load_model(self) -> None:
        """Load the Whisper model."""
        console.print(f"[cyan]Loading Whisper model: {self.model_size}...[/cyan]")
        
        # Determine compute type based on device
        if self.device == "cpu" or self.device == "auto":
            compute_type = "int8"  # Faster on CPU
        else:
            compute_type = "float16"  # Better for GPU
        
        self.model = WhisperModel(
            self.model_size,
            device="cpu",  # Use CPU for compatibility
            compute_type=compute_type
        )
        console.print(f"[green]✓ Model loaded successfully![/green]")
    
    def transcribe(
        self, 
        audio_path: str,
        language: Optional[str] = None,
        show_progress: bool = True
    ) -> TranscriptResult:
        """
        Transcribe audio/video file.
        
        Args:
            audio_path: Path to audio or video file
            language: Language code (e.g., "id" for Indonesian, "en" for English)
                     None for auto-detection
            show_progress: Whether to show progress bar
        
        Returns:
            TranscriptResult with segments and metadata
        """
        if self.model is None:
            self.load_model()
        
        console.print(f"[cyan]Transcribing: {audio_path}[/cyan]")
        
        # Run transcription
        segments_generator, info = self.model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
            vad_filter=True,  # Filter out silence
        )
        
        console.print(f"[dim]Detected language: {info.language} (probability: {info.language_probability:.2%})[/dim]")
        
        # Collect segments with progress
        segments: list[TranscriptSegment] = []
        
        if show_progress:
            from rich.live import Live
            from rich.spinner import Spinner
            from rich.text import Text
            
            segments: list[TranscriptSegment] = []
            
            with Live(console=console, refresh_per_second=4) as live:
                for segment in segments_generator:
                    segments.append(TranscriptSegment(
                        start=segment.start,
                        end=segment.end,
                        text=segment.text.strip()
                    ))
                    
                    # Format current time position
                    current_time = segment.end
                    mins = int(current_time // 60)
                    secs = int(current_time % 60)
                    
                    # Create status display
                    status = Text()
                    status.append("⏳ ", style="cyan")
                    status.append(f"Processing: ", style="bold")
                    status.append(f"{len(segments)} segments ", style="green")
                    status.append(f"| Position: {mins:02d}:{secs:02d}", style="dim")
                    
                    live.update(status)
        else:
            for segment in segments_generator:
                segments.append(TranscriptSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip()
                ))
        
        # Calculate total duration
        duration = segments[-1].end if segments else 0.0
        
        console.print(f"[green]✓ Transcription complete! {len(segments)} segments found.[/green]")
        
        return TranscriptResult(
            segments=segments,
            language=info.language,
            language_probability=info.language_probability,
            duration=duration
        )


def get_model_choices() -> list[dict]:
    """Get list of model choices for questionary."""
    return [
        {"name": f"{size} - {desc}", "value": size}
        for size, desc in MODEL_DESCRIPTIONS.items()
    ]
