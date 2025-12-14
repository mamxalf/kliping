"""Data models for Clipper CLI."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TranscriberType(str, Enum):
    """Available transcription providers."""
    WHISPER = "whisper"
    ASSEMBLYAI = "assemblyai"


class LLMProviderType(str, Enum):
    """Available LLM providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"


class TranscriptSegment(BaseModel):
    """A single segment of transcribed text with timing."""
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text")
    speaker: Optional[str] = Field(None, description="Speaker label if available")
    sentiment: Optional[str] = Field(None, description="Sentiment: positive/negative/neutral")


class TranscriptResult(BaseModel):
    """Complete transcription result."""
    segments: list[TranscriptSegment] = Field(default_factory=list)
    language: str = Field(..., description="Detected or specified language")
    duration: float = Field(..., description="Total duration in seconds")
    full_text: str = Field(..., description="Complete transcript as single string")
    summary: Optional[str] = Field(None, description="Summary if available")
    chapters: Optional[list[dict]] = Field(None, description="Auto-detected chapters")


class ViralScore(BaseModel):
    """Viral potential scoring."""
    hook_strength: int = Field(..., ge=0, le=10, description="Hook strength 0-10")
    emotional_impact: int = Field(..., ge=0, le=10, description="Emotional impact 0-10")
    shareability: int = Field(..., ge=0, le=10, description="Shareability 0-10")
    completeness: int = Field(..., ge=0, le=10, description="Story completeness 0-10")
    
    @property
    def total_score(self) -> float:
        """Calculate weighted total score."""
        weights = {
            "hook_strength": 0.30,
            "emotional_impact": 0.25,
            "shareability": 0.25,
            "completeness": 0.20,
        }
        return (
            self.hook_strength * weights["hook_strength"] +
            self.emotional_impact * weights["emotional_impact"] +
            self.shareability * weights["shareability"] +
            self.completeness * weights["completeness"]
        )


class PotentialClip(BaseModel):
    """A potential viral clip identified from the video."""
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    transcript: str = Field(..., description="Text content of the clip")
    score: ViralScore = Field(..., description="Viral potential scores")
    reason: str = Field(..., description="Why this clip is potentially viral")
    viral_factor: str = Field(..., description="Primary viral factor")
    suggested_caption: Optional[str] = Field(None, description="Suggested social media caption")
    
    @property
    def duration(self) -> float:
        """Get clip duration in seconds."""
        return self.end - self.start


class VideoMetadata(BaseModel):
    """Video file metadata."""
    path: str = Field(..., description="Path to video file")
    duration: float = Field(..., description="Duration in seconds")
    width: int = Field(..., description="Video width in pixels")
    height: int = Field(..., description="Video height in pixels")
    fps: float = Field(..., description="Frames per second")
    audio_path: Optional[str] = Field(None, description="Path to extracted audio")


class ClipResult(BaseModel):
    """Result of clip generation."""
    source_file: str = Field(..., description="Source video path")
    output_file: str = Field(..., description="Output clip path")
    clip: PotentialClip = Field(..., description="Clip details")
    success: bool = Field(True, description="Whether generation succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")


class VideoResult(BaseModel):
    """Complete result for a single video processing."""
    source_file: str = Field(..., description="Source video path")
    clips: list[ClipResult] = Field(default_factory=list)
    transcript: Optional[TranscriptResult] = Field(None)
    transcriber_used: TranscriberType = Field(...)
    llm_provider_used: LLMProviderType = Field(...)
    llm_model_used: str = Field(...)
    processing_time: float = Field(..., description="Processing time in seconds")
    success: bool = Field(True)
    error: Optional[str] = Field(None)


class BatchResult(BaseModel):
    """Result of batch processing multiple videos."""
    total_videos: int = Field(0)
    successful: int = Field(0)
    failed: int = Field(0)
    total_clips: int = Field(0)
    results: list[VideoResult] = Field(default_factory=list)
    errors: dict[str, str] = Field(default_factory=dict)
    processing_time: float = Field(0.0, description="Total processing time in seconds")


class ProcessingConfig(BaseModel):
    """Configuration for video processing."""
    transcriber: TranscriberType = Field(TranscriberType.WHISPER)
    llm_provider: LLMProviderType = Field(LLMProviderType.OLLAMA)
    llm_model: Optional[str] = Field(None, description="Specific model to use")
    whisper_model: str = Field("base", description="Whisper model size")
    min_duration: int = Field(15, ge=5, description="Minimum clip duration in seconds")
    max_duration: int = Field(60, le=180, description="Maximum clip duration in seconds")
    num_clips: int = Field(5, ge=1, le=20, description="Number of clips to generate")
    language: str = Field("auto", description="Language code or 'auto' for detection")
    output_dir: str = Field("./output", description="Output directory for clips")
