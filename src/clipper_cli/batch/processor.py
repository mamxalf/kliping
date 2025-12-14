"""Batch processing orchestrator."""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from clipper_cli.models import (
    BatchResult,
    VideoResult,
    ProcessingConfig,
    TranscriberType,
    LLMProviderType,
)
from clipper_cli.video.processor import VideoProcessor
from clipper_cli.video.clipper import ClipGenerator
from clipper_cli.transcription import WhisperTranscriber, AssemblyAITranscriber
from clipper_cli.llm.factory import create_llm_provider
from clipper_cli.analysis import ViralDetector
from clipper_cli.utils.console import (
    console,
    print_success,
    print_error,
    print_step,
    format_duration,
)


class BatchProcessor:
    """Process multiple videos in batch."""
    
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
    
    def __init__(
        self,
        config: ProcessingConfig,
        output_dir: str = "./output",
    ):
        """Initialize batch processor.
        
        Args:
            config: Processing configuration.
            output_dir: Base output directory for all clips.
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # State file for resume capability
        self.state_file = self.output_dir / ".batch_state.json"
    
    def find_videos(
        self,
        input_path: str,
        patterns: Optional[list[str]] = None,
        recursive: bool = False,
    ) -> list[Path]:
        """Find video files in directory.
        
        Args:
            input_path: Directory or file path.
            patterns: Optional glob patterns to match.
            recursive: Whether to search recursively.
        
        Returns:
            List of video file paths.
        """
        input_path = Path(input_path)
        
        if input_path.is_file():
            return [input_path]
        
        videos = []
        
        if patterns:
            for pattern in patterns:
                if recursive:
                    videos.extend(input_path.rglob(pattern))
                else:
                    videos.extend(input_path.glob(pattern))
        else:
            # Find all video files
            for ext in self.VIDEO_EXTENSIONS:
                if recursive:
                    videos.extend(input_path.rglob(f"*{ext}"))
                else:
                    videos.extend(input_path.glob(f"*{ext}"))
        
        # Filter to only video files
        videos = [v for v in videos if v.suffix.lower() in self.VIDEO_EXTENSIONS]
        
        return sorted(videos)
    
    def load_state(self) -> dict:
        """Load batch processing state for resume."""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {"completed": [], "failed": {}}
    
    def save_state(self, state: dict) -> None:
        """Save batch processing state."""
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
    
    def clear_state(self) -> None:
        """Clear batch processing state."""
        if self.state_file.exists():
            self.state_file.unlink()
    
    def process_batch(
        self,
        input_path: str,
        patterns: Optional[list[str]] = None,
        max_workers: int = 2,
        resume: bool = False,
    ) -> BatchResult:
        """Process all videos in batch.
        
        Args:
            input_path: Directory containing videos.
            patterns: Optional glob patterns.
            max_workers: Number of parallel workers.
            resume: Whether to resume interrupted batch.
        
        Returns:
            BatchResult with all processing results.
        """
        start_time = time.time()
        
        # Find videos
        videos = self.find_videos(input_path, patterns)
        
        if not videos:
            console.print("[yellow]No video files found.[/yellow]")
            return BatchResult(total_videos=0)
        
        console.print(f"📂 Found [cyan]{len(videos)}[/cyan] videos to process")
        
        # Load state if resuming
        state = self.load_state() if resume else {"completed": [], "failed": {}}
        
        # Filter out already completed videos
        if resume:
            remaining = [v for v in videos if str(v) not in state["completed"]]
            if len(remaining) < len(videos):
                console.print(
                    f"[dim]Resuming: {len(videos) - len(remaining)} already completed[/dim]"
                )
            videos = remaining
        
        # Process videos
        results: list[VideoResult] = []
        errors: dict[str, str] = dict(state.get("failed", {}))
        
        console.print(f"\n🔄 Processing with {max_workers} workers...\n")
        
        if max_workers > 1:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._process_single_video, video, i + 1, len(videos)): video
                    for i, video in enumerate(videos)
                }
                
                for future in as_completed(futures):
                    video = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        if result.success:
                            state["completed"].append(str(video))
                        else:
                            errors[str(video)] = result.error or "Unknown error"
                            state["failed"][str(video)] = result.error or "Unknown error"
                    except Exception as e:
                        errors[str(video)] = str(e)
                        state["failed"][str(video)] = str(e)
                    
                    # Save state after each video
                    self.save_state(state)
        else:
            # Sequential processing
            for i, video in enumerate(videos, 1):
                try:
                    result = self._process_single_video(video, i, len(videos))
                    results.append(result)
                    if result.success:
                        state["completed"].append(str(video))
                    else:
                        errors[str(video)] = result.error or "Unknown error"
                        state["failed"][str(video)] = result.error or "Unknown error"
                except Exception as e:
                    errors[str(video)] = str(e)
                    state["failed"][str(video)] = str(e)
                
                # Save state after each video
                self.save_state(state)
        
        # Calculate totals
        total_clips = sum(
            len([c for c in r.clips if c.success])
            for r in results
        )
        
        processing_time = time.time() - start_time
        
        # Clear state on successful completion
        if not errors:
            self.clear_state()
        
        return BatchResult(
            total_videos=len(videos) + len(state.get("completed", [])) - len(videos),
            successful=len([r for r in results if r.success]),
            failed=len(errors),
            total_clips=total_clips,
            results=results,
            errors=errors,
            processing_time=processing_time,
        )
    
    def _process_single_video(
        self,
        video_path: Path,
        index: int,
        total: int,
    ) -> VideoResult:
        """Process a single video.
        
        Args:
            video_path: Path to video file.
            index: Current video index.
            total: Total number of videos.
        
        Returns:
            VideoResult for this video.
        """
        start_time = time.time()
        
        console.print(f"  [{index}/{total}] [cyan]{video_path.name}[/cyan]")
        
        try:
            # Create output directory for this video
            video_output_dir = self.output_dir / video_path.stem
            video_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Process video
            with VideoProcessor(str(video_path)) as processor:
                metadata = processor.get_metadata()
                print_step(f"Duration: {format_duration(metadata.duration)}", indent=2)
                
                # Extract audio
                audio_path = processor.extract_audio()
                
                # Transcribe
                transcriber = self._create_transcriber()
                transcript = transcriber.transcribe(
                    audio_path,
                    language=self.config.language,
                )
                print_step(f"Segments: {len(transcript.segments)}", indent=2)
                
                # Analyze for viral moments
                llm = create_llm_provider(
                    self.config.llm_provider,
                    model=self.config.llm_model,
                )
                detector = ViralDetector(llm)
                
                potential_clips = detector.detect_viral_moments_sync(
                    transcript,
                    num_clips=self.config.num_clips,
                    min_duration=self.config.min_duration,
                    max_duration=self.config.max_duration,
                )
                
                # Generate clips
                clipper = ClipGenerator(
                    str(video_path),
                    str(video_output_dir),
                )
                
                clip_results = clipper.generate_clips(
                    potential_clips,
                    show_progress=False,
                )
                
                successful_clips = len([c for c in clip_results if c.success])
                print_step(f"Clips: {successful_clips} | ✓ Done", indent=2)
                
                processing_time = time.time() - start_time
                
                return VideoResult(
                    source_file=str(video_path),
                    clips=clip_results,
                    transcript=transcript,
                    transcriber_used=self.config.transcriber,
                    llm_provider_used=self.config.llm_provider,
                    llm_model_used=llm.model,
                    processing_time=processing_time,
                    success=True,
                )
        
        except Exception as e:
            print_step(f"[red]Error: {e}[/red]", indent=2)
            return VideoResult(
                source_file=str(video_path),
                clips=[],
                transcript=None,
                transcriber_used=self.config.transcriber,
                llm_provider_used=self.config.llm_provider,
                llm_model_used=self.config.llm_model or "",
                processing_time=time.time() - start_time,
                success=False,
                error=str(e),
            )
    
    def _create_transcriber(self):
        """Create transcriber based on config."""
        if self.config.transcriber == TranscriberType.WHISPER:
            return WhisperTranscriber(model_name=self.config.whisper_model)
        elif self.config.transcriber == TranscriberType.ASSEMBLYAI:
            return AssemblyAITranscriber()
        else:
            raise ValueError(f"Unknown transcriber: {self.config.transcriber}")
