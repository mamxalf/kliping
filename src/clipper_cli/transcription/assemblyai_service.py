"""AssemblyAI transcription service (cloud)."""

from typing import Optional

from clipper_cli.models import TranscriptResult, TranscriptSegment
from clipper_cli.transcription.base import BaseTranscriber
from clipper_cli.config import settings


class AssemblyAITranscriber(BaseTranscriber):
    """Transcribe audio using AssemblyAI (cloud)."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize AssemblyAI transcriber.
        
        Args:
            api_key: AssemblyAI API key. Uses config if not provided.
        """
        self.api_key = api_key or settings.assemblyai_api_key
    
    @property
    def name(self) -> str:
        return "AssemblyAI"
    
    @property
    def is_offline(self) -> bool:
        return False
    
    def is_available(self) -> bool:
        """Check if AssemblyAI is available and configured."""
        if not self.api_key:
            return False
        
        try:
            import assemblyai
            return True
        except ImportError:
            return False
    
    def transcribe(
        self,
        audio_path: str,
        language: str = "auto",
        speaker_labels: bool = True,
        auto_chapters: bool = True,
        sentiment_analysis: bool = True,
    ) -> TranscriptResult:
        """Transcribe audio using AssemblyAI.
        
        Args:
            audio_path: Path to audio file.
            language: Language code or 'auto' for detection.
            speaker_labels: Enable speaker diarization.
            auto_chapters: Enable auto chapter detection.
            sentiment_analysis: Enable sentiment analysis.
        
        Returns:
            TranscriptResult with segments and metadata.
        """
        import assemblyai as aai
        
        # Configure API key
        aai.settings.api_key = self.api_key
        
        # Build transcription config
        config_kwargs = {
            "speaker_labels": speaker_labels,
            "auto_chapters": auto_chapters,
            "sentiment_analysis": sentiment_analysis,
        }
        
        if language != "auto":
            config_kwargs["language_code"] = language
        else:
            config_kwargs["language_detection"] = True
        
        config = aai.TranscriptionConfig(**config_kwargs)
        
        # Create transcriber and transcribe
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_path, config=config)
        
        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"Transcription failed: {transcript.error}")
        
        # Convert sentences to our segment format
        segments = []
        
        if sentiment_analysis and transcript.sentiment_analysis:
            # Use sentiment analysis results which have more detail
            for sent in transcript.sentiment_analysis:
                segments.append(TranscriptSegment(
                    start=sent.start / 1000,  # Convert ms to seconds
                    end=sent.end / 1000,
                    text=sent.text,
                    speaker=sent.speaker if speaker_labels else None,
                    sentiment=sent.sentiment.value if sent.sentiment else None,
                ))
        elif transcript.utterances:
            # Use utterances if available (speaker-aware)
            for utt in transcript.utterances:
                segments.append(TranscriptSegment(
                    start=utt.start / 1000,
                    end=utt.end / 1000,
                    text=utt.text,
                    speaker=utt.speaker,
                    sentiment=None,
                ))
        else:
            # Fall back to words grouped into segments
            words = transcript.words or []
            current_segment_words = []
            segment_start = 0
            
            for word in words:
                if not current_segment_words:
                    segment_start = word.start
                
                current_segment_words.append(word.text)
                
                # Create segment every ~10 words or at sentence end
                if len(current_segment_words) >= 10 or word.text.endswith((".", "!", "?")):
                    segments.append(TranscriptSegment(
                        start=segment_start / 1000,
                        end=word.end / 1000,
                        text=" ".join(current_segment_words),
                        speaker=None,
                        sentiment=None,
                    ))
                    current_segment_words = []
            
            # Add remaining words
            if current_segment_words:
                segments.append(TranscriptSegment(
                    start=segment_start / 1000,
                    end=words[-1].end / 1000,
                    text=" ".join(current_segment_words),
                    speaker=None,
                    sentiment=None,
                ))
        
        # Process chapters if available
        chapters = None
        if auto_chapters and transcript.chapters:
            chapters = [
                {
                    "start": ch.start / 1000,
                    "end": ch.end / 1000,
                    "headline": ch.headline,
                    "summary": ch.summary,
                    "gist": ch.gist,
                }
                for ch in transcript.chapters
            ]
        
        # Get audio duration
        duration = (transcript.audio_duration or 0) 
        
        return TranscriptResult(
            segments=segments,
            language=transcript.language_code or "unknown",
            duration=duration,
            full_text=transcript.text or "",
            summary=transcript.summary if hasattr(transcript, 'summary') else None,
            chapters=chapters,
        )
