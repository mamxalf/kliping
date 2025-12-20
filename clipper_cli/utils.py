"""
Utility functions for Clipper CLI.
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        console.print(f"[red]Error getting video duration: {e}[/red]")
        return 0.0


def extract_audio(video_path: str, output_path: Optional[str] = None) -> str:
    """Extract audio from video file to WAV format for Whisper."""
    if output_path is None:
        # Create temp file
        fd, output_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
    
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # PCM 16-bit
        "-ar", "16000",  # 16kHz sample rate (optimal for Whisper)
        "-ac", "1",  # Mono
        "-y",  # Overwrite
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error extracting audio: {e.stderr.decode()}[/red]")
        raise


def format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_time_display(seconds: float) -> str:
    """Format seconds to display format (MM:SS)."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def validate_video_file(file_path: str) -> bool:
    """Validate if file exists and is a supported video format."""
    path = Path(file_path)
    if not path.exists():
        return False
    
    supported_extensions = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".mp3", ".wav", ".m4a"}
    return path.suffix.lower() in supported_extensions


def ensure_output_dir(output_dir: str) -> Path:
    """Ensure output directory exists."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_filename(input_path: str, index: int, suffix: str = "") -> str:
    """Generate output filename for clips."""
    input_name = Path(input_path).stem
    return f"{input_name}_clip_{index:02d}{suffix}.mp4"
