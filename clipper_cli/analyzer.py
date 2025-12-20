"""
Viral content analyzer using LLM.
Analyzes transcript to find potentially viral moments.
"""
import json
import re
from dataclasses import dataclass
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .llm_providers import BaseLLMProvider, LLMProvider
from .transcriber import TranscriptResult, TranscriptSegment

console = Console()


@dataclass
class ViralClip:
    """A potentially viral clip."""
    start_time: float
    end_time: float
    title: str
    reason: str
    viral_score: int  # 1-10
    hook: str  # Opening hook/caption
    transcript: str  # Text content
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


SYSTEM_PROMPT_TEMPLATE = """Kamu adalah ahli content creator yang sangat memahami konten viral di TikTok, Instagram Reels, dan YouTube Shorts.

Tugasmu adalah menganalisis transkrip podcast/video dan menemukan bagian-bagian yang berpotensi viral untuk dipotong menjadi short-form content.

Kriteria konten viral:
1. Hook yang kuat di awal (3 detik pertama harus menarik)
2. Cerita yang emosional atau surprising
3. Tips/insight yang actionable
4. Kontroversi atau opini yang berani
5. Humor atau momen lucu
6. Quotes yang memorable
7. Behind-the-scenes atau rahasia

Untuk setiap clip yang kamu rekomendasikan, berikan:
- start_time: waktu mulai dalam detik
- end_time: waktu selesai dalam detik
- title: judul pendek untuk clip
- reason: alasan kenapa ini berpotensi viral
- viral_score: skor 1-10 (10 = pasti viral)
- hook: kalimat pembuka/caption yang menarik

PENTING:
- Durasi clip harus antara {min_duration}-{max_duration} detik
- Maksimal rekomendasikan {max_clips} clip terbaik
- Urutkan dari viral_score tertinggi
- Response dalam format JSON array"""

USER_PROMPT_TEMPLATE = """Analisis transkrip berikut dan temukan bagian yang berpotensi viral:

TRANSKRIP:
{transcript}

---

Berikan response dalam format JSON seperti ini:
```json
[
  {{
    "start_time": 120.5,
    "end_time": 165.2,
    "title": "Judul Clip",
    "reason": "Alasan kenapa viral",
    "viral_score": 8,
    "hook": "Kalimat pembuka yang menarik"
  }}
]
```

Hanya berikan JSON array, tanpa penjelasan tambahan."""


class ViralAnalyzer:
    """Analyzes transcripts to find viral moments."""
    
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
    
    def _format_transcript_with_timestamps(self, result: TranscriptResult) -> str:
        """Format transcript with timestamps for LLM analysis."""
        lines = []
        for seg in result.segments:
            minutes = int(seg.start // 60)
            seconds = int(seg.start % 60)
            lines.append(f"[{minutes:02d}:{seconds:02d}] {seg.text}")
        return "\n".join(lines)
    
    def _parse_response(self, response: str, transcript: TranscriptResult) -> list[ViralClip]:
        """Parse LLM response to extract viral clips."""
        # Try to extract JSON from response
        json_match = re.search(r'\[[\s\S]*\]', response)
        if not json_match:
            console.print("[yellow]Warning: Could not parse LLM response as JSON[/yellow]")
            return []
        
        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            console.print(f"[yellow]Warning: JSON parse error: {e}[/yellow]")
            return []
        
        clips = []
        for item in data:
            try:
                # Get transcript text for this clip
                clip_text = transcript.get_text_in_range(
                    item.get("start_time", 0),
                    item.get("end_time", 0)
                )
                
                clips.append(ViralClip(
                    start_time=float(item.get("start_time", 0)),
                    end_time=float(item.get("end_time", 0)),
                    title=item.get("title", "Untitled"),
                    reason=item.get("reason", ""),
                    viral_score=int(item.get("viral_score", 5)),
                    hook=item.get("hook", ""),
                    transcript=clip_text
                ))
            except (KeyError, ValueError) as e:
                console.print(f"[yellow]Warning: Skipping invalid clip: {e}[/yellow]")
                continue
        
        # Sort by viral score
        clips.sort(key=lambda x: x.viral_score, reverse=True)
        return clips
    
    def analyze(
        self, 
        transcript: TranscriptResult,
        max_clips: int = 5,
        min_duration: int = 15,
        max_duration: int = 60
    ) -> list[ViralClip]:
        """
        Analyze transcript and find viral moments.
        
        Args:
            transcript: TranscriptResult from transcriber
            max_clips: Maximum number of clips to recommend
            min_duration: Minimum clip duration in seconds
            max_duration: Maximum clip duration in seconds
        
        Returns:
            List of ViralClip objects sorted by viral_score
        """
        console.print(f"[cyan]Analyzing transcript for viral moments...[/cyan]")
        console.print(f"[dim]Config: {max_clips} clips, {min_duration}-{max_duration}s per clip[/dim]")
        
        # Build system prompt with config
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            min_duration=min_duration,
            max_duration=max_duration,
            max_clips=max_clips
        )
        
        # Format transcript for LLM
        formatted_transcript = self._format_transcript_with_timestamps(transcript)
        
        # Build prompt
        prompt = USER_PROMPT_TEMPLATE.format(transcript=formatted_transcript)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("[cyan]AI sedang menganalisis...", total=None)
            
            # Get LLM response
            response = self.llm.generate(prompt, system_prompt=system_prompt)
        
        # Parse response
        clips = self._parse_response(response.content, transcript)
        
        # Limit to max_clips
        clips = clips[:max_clips]
        
        console.print(f"[green]✓ Found {len(clips)} potential viral clips![/green]")
        
        return clips

