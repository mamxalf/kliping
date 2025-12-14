"""Viral content detector using LLM analysis."""

import json
import re
from typing import Optional

from clipper_cli.models import (
    TranscriptResult,
    PotentialClip,
    ViralScore,
)
from clipper_cli.llm.base import BaseLLMProvider
from clipper_cli.analysis.prompts import (
    VIRAL_SYSTEM_PROMPT,
    create_viral_analysis_prompt,
)


class ViralDetector:
    """Detect viral moments in video transcripts using LLM."""
    
    def __init__(self, llm_provider: BaseLLMProvider):
        """Initialize viral detector.
        
        Args:
            llm_provider: LLM provider to use for analysis.
        """
        self.llm = llm_provider
    
    async def detect_viral_moments(
        self,
        transcript: TranscriptResult,
        num_clips: int = 5,
        min_duration: int = 15,
        max_duration: int = 60,
    ) -> list[PotentialClip]:
        """Analyze transcript and return potential viral clips.
        
        Args:
            transcript: Transcription result with segments.
            num_clips: Number of clips to identify.
            min_duration: Minimum clip duration in seconds.
            max_duration: Maximum clip duration in seconds.
        
        Returns:
            List of potential viral clips, sorted by score.
        """
        # Format transcript for LLM
        formatted_transcript = self._format_transcript(transcript)
        
        # Create analysis prompt
        prompt = create_viral_analysis_prompt(
            transcript=formatted_transcript,
            num_clips=num_clips,
            min_duration=min_duration,
            max_duration=max_duration,
            language=transcript.language,
        )
        
        # Get LLM response
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=VIRAL_SYSTEM_PROMPT,
            temperature=0.7,
        )
        
        # Parse response
        clips = self._parse_response(response, transcript.duration)
        
        # Validate and adjust clip boundaries
        clips = self._validate_clips(
            clips,
            transcript,
            min_duration,
            max_duration,
        )
        
        # Sort by score descending
        clips.sort(key=lambda c: c.score.total_score, reverse=True)
        
        # Return top clips
        return clips[:num_clips]
    
    def detect_viral_moments_sync(
        self,
        transcript: TranscriptResult,
        num_clips: int = 5,
        min_duration: int = 15,
        max_duration: int = 60,
    ) -> list[PotentialClip]:
        """Synchronous wrapper for detect_viral_moments."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.detect_viral_moments(
                transcript,
                num_clips,
                min_duration,
                max_duration,
            )
        )
    
    def _format_transcript(self, transcript: TranscriptResult) -> str:
        """Format transcript with timestamps for LLM analysis."""
        lines = []
        for segment in transcript.segments:
            timestamp = self._format_timestamp(segment.start)
            speaker = f"[{segment.speaker}] " if segment.speaker else ""
            lines.append(f"[{timestamp}] {speaker}{segment.text}")
        
        return "\n".join(lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def _parse_response(
        self,
        response: str,
        max_duration: float,
    ) -> list[PotentialClip]:
        """Parse LLM response into PotentialClip objects."""
        clips = []
        
        # Try to extract JSON from response
        json_str = self._extract_json(response)
        
        try:
            data = json.loads(json_str)
            
            # Handle both array and object with array
            if isinstance(data, dict):
                data = data.get("clips", [])
            
            for item in data:
                try:
                    clip = self._parse_clip_item(item, max_duration)
                    if clip:
                        clips.append(clip)
                except Exception:
                    continue
        
        except json.JSONDecodeError:
            # Try to parse line by line if JSON fails
            pass
        
        return clips
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON array or object from text."""
        # Try to find JSON array
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            return match.group()
        
        # Try to find JSON object
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return match.group()
        
        return text
    
    def _parse_clip_item(
        self,
        item: dict,
        max_duration: float,
    ) -> Optional[PotentialClip]:
        """Parse a single clip item from LLM response."""
        # Extract required fields
        start = float(item.get("start", 0))
        end = float(item.get("end", 0))
        
        # Validate times
        if start < 0:
            start = 0
        if end > max_duration:
            end = max_duration
        if end <= start:
            return None
        
        # Extract scores
        scores_data = item.get("scores", {})
        score = ViralScore(
            hook_strength=min(10, max(0, int(scores_data.get("hook_strength", 5)))),
            emotional_impact=min(10, max(0, int(scores_data.get("emotional_impact", 5)))),
            shareability=min(10, max(0, int(scores_data.get("shareability", 5)))),
            completeness=min(10, max(0, int(scores_data.get("completeness", 5)))),
        )
        
        return PotentialClip(
            start=start,
            end=end,
            transcript=item.get("transcript", ""),
            score=score,
            viral_factor=item.get("viral_factor", "Unknown"),
            reason=item.get("reason", ""),
            suggested_caption=item.get("suggested_caption"),
        )
    
    def _validate_clips(
        self,
        clips: list[PotentialClip],
        transcript: TranscriptResult,
        min_duration: int,
        max_duration: int,
    ) -> list[PotentialClip]:
        """Validate and adjust clip boundaries."""
        validated = []
        
        for clip in clips:
            # Ensure minimum duration
            if clip.duration < min_duration:
                # Try to extend the clip
                needed = min_duration - clip.duration
                clip = PotentialClip(
                    start=max(0, clip.start - needed / 2),
                    end=min(transcript.duration, clip.end + needed / 2),
                    transcript=clip.transcript,
                    score=clip.score,
                    viral_factor=clip.viral_factor,
                    reason=clip.reason,
                    suggested_caption=clip.suggested_caption,
                )
            
            # Ensure maximum duration
            if clip.duration > max_duration:
                clip = PotentialClip(
                    start=clip.start,
                    end=clip.start + max_duration,
                    transcript=clip.transcript,
                    score=clip.score,
                    viral_factor=clip.viral_factor,
                    reason=clip.reason,
                    suggested_caption=clip.suggested_caption,
                )
            
            # Only add if valid duration
            if min_duration <= clip.duration <= max_duration:
                validated.append(clip)
        
        return validated
