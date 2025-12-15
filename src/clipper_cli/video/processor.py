"""Video processing and metadata extraction."""

import os
import tempfile
from pathlib import Path
from typing import Optional

from moviepy import VideoFileClip

from clipper_cli.models import VideoMetadata


class VideoProcessor:
    """Process video files and extract metadata."""
    
    SUPPORTED_FORMATS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv"}
    
    def __init__(self, video_path: str):
        """Initialize processor with video path.
        
        Args:
            video_path: Path to the video file.
        """
        self.video_path = Path(video_path)
        self._clip: Optional[VideoFileClip] = None
        self._metadata: Optional[VideoMetadata] = None
        self._audio_path: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate that the video file exists and is supported.
        
        Returns:
            True if valid, raises exception otherwise.
        
        Raises:
            FileNotFoundError: If video file doesn't exist.
            ValueError: If video format is not supported.
        """
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")
        
        if self.video_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported video format: {self.video_path.suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        return True
    
    def load(self) -> "VideoProcessor":
        """Load the video file.
        
        Returns:
            Self for chaining.
        """
        self.validate()
        self._clip = VideoFileClip(str(self.video_path))
        return self
    
    def get_metadata(self) -> VideoMetadata:
        """Get video metadata.
        
        Returns:
            VideoMetadata object with video information.
        """
        if self._metadata is not None:
            return self._metadata
        
        if self._clip is None:
            self.load()
        
        self._metadata = VideoMetadata(
            path=str(self.video_path),
            duration=self._clip.duration,
            width=self._clip.w,
            height=self._clip.h,
            fps=self._clip.fps,
            audio_path=self._audio_path,
        )
        
        return self._metadata
    
    def extract_audio(self, output_path: Optional[str] = None) -> str:
        """Extract audio from video for transcription.
        
        Args:
            output_path: Optional path for audio file. If not provided,
                        creates a temp file.
        
        Returns:
            Path to the extracted audio file.
        """
        if self._clip is None:
            self.load()
        
        if output_path is None:
            # Create temp file that persists
            fd, output_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
        
        # Extract audio
        audio = self._clip.audio
        if audio is None:
            raise ValueError("Video has no audio track")
        
        audio.write_audiofile(
            output_path,
            fps=16000,  # Whisper expects 16kHz
            nbytes=2,
            codec="pcm_s16le",
        )
        
        self._audio_path = output_path
        return output_path
    
    def get_subclip(self, start: float, end: float) -> VideoFileClip:
        """Get a subclip from the video.
        
        Args:
            start: Start time in seconds.
            end: End time in seconds.
        
        Returns:
            VideoFileClip of the subclip.
        """
        if self._clip is None:
            self.load()
        
        # Clamp to video bounds
        start = max(0, start)
        end = min(self._clip.duration, end)
        
        return self._clip.subclip(start, end)
    
    def close(self) -> None:
        """Close the video file and clean up resources."""
        if self._clip is not None:
            self._clip.close()
            self._clip = None
        
        # Clean up temp audio file if created
        if self._audio_path and os.path.exists(self._audio_path):
            try:
                os.remove(self._audio_path)
            except OSError:
                pass
            self._audio_path = None
    
    def __enter__(self) -> "VideoProcessor":
        """Context manager entry."""
        return self.load()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
