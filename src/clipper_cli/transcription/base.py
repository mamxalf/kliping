"""Base transcriber interface."""

from abc import ABC, abstractmethod
from typing import Optional

from clipper_cli.models import TranscriptResult


class BaseTranscriber(ABC):
    """Abstract base class for transcription services."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the transcription service."""
        pass
    
    @property
    @abstractmethod
    def is_offline(self) -> bool:
        """Whether this transcriber works offline."""
        pass
    
    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: str = "auto",
    ) -> TranscriptResult:
        """Transcribe audio file.
        
        Args:
            audio_path: Path to audio file.
            language: Language code or 'auto' for detection.
        
        Returns:
            TranscriptResult with segments and metadata.
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the transcriber is available and configured.
        
        Returns:
            True if ready to use.
        """
        pass
    
    def format_transcript_for_llm(self, result: TranscriptResult) -> str:
        """Format transcript for LLM analysis.
        
        Args:
            result: Transcription result.
        
        Returns:
            Formatted string with timestamps.
        """
        lines = []
        for segment in result.segments:
            timestamp = self._format_timestamp(segment.start)
            speaker = f"[{segment.speaker}] " if segment.speaker else ""
            lines.append(f"[{timestamp}] {speaker}{segment.text}")
        
        return "\n".join(lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
