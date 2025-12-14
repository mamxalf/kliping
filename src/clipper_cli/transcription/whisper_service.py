"""Whisper transcription service (offline)."""

from typing import Optional

from clipper_cli.models import TranscriptResult, TranscriptSegment
from clipper_cli.transcription.base import BaseTranscriber


class WhisperTranscriber(BaseTranscriber):
    """Transcribe audio using OpenAI Whisper (offline)."""
    
    VALID_MODELS = {"tiny", "base", "small", "medium", "large", "large-v2", "large-v3"}
    
    def __init__(self, model_name: str = "base"):
        """Initialize Whisper transcriber.
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large).
        """
        if model_name not in self.VALID_MODELS:
            raise ValueError(f"Invalid model: {model_name}. Valid: {self.VALID_MODELS}")
        
        self.model_name = model_name
        self._model = None
    
    @property
    def name(self) -> str:
        return f"Whisper ({self.model_name})"
    
    @property
    def is_offline(self) -> bool:
        return True
    
    def is_available(self) -> bool:
        """Check if Whisper is available."""
        try:
            import whisper
            return True
        except ImportError:
            return False
    
    def _load_model(self):
        """Lazy load the Whisper model."""
        if self._model is None:
            import whisper
            self._model = whisper.load_model(self.model_name)
        return self._model
    
    def transcribe(
        self,
        audio_path: str,
        language: str = "auto",
    ) -> TranscriptResult:
        """Transcribe audio using Whisper.
        
        Args:
            audio_path: Path to audio file.
            language: Language code or 'auto' for detection.
        
        Returns:
            TranscriptResult with segments and metadata.
        """
        model = self._load_model()
        
        # Prepare transcription options
        options = {
            "task": "transcribe",
            "verbose": False,
        }
        
        if language != "auto":
            options["language"] = language
        
        # Transcribe
        result = model.transcribe(audio_path, **options)
        
        # Convert to our format
        segments = []
        for seg in result.get("segments", []):
            segments.append(TranscriptSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"].strip(),
                speaker=None,  # Whisper doesn't do speaker diarization
                sentiment=None,
            ))
        
        # Build full text
        full_text = " ".join(seg.text for seg in segments)
        
        # Calculate total duration
        duration = segments[-1].end if segments else 0.0
        
        # Detect language if auto
        detected_language = result.get("language", language)
        
        return TranscriptResult(
            segments=segments,
            language=detected_language,
            duration=duration,
            full_text=full_text,
            summary=None,
            chapters=None,
        )
