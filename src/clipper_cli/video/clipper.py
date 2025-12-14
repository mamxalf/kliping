"""Clip generation from video files."""

import os
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from moviepy import VideoFileClip, concatenate_videoclips

from clipper_cli.models import PotentialClip, ClipResult
from clipper_cli.utils.console import console, print_step


class ClipGenerator:
    """Generate video clips from identified segments."""
    
    def __init__(
        self,
        video_path: str,
        output_dir: str = "./output",
        fade_duration: float = 0.3,
    ):
        """Initialize clip generator.
        
        Args:
            video_path: Path to source video.
            output_dir: Directory to save clips.
            fade_duration: Duration of fade in/out in seconds.
        """
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir)
        self.fade_duration = fade_duration
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_clip(
        self,
        clip_info: PotentialClip,
        index: int,
        apply_fade: bool = True,
    ) -> ClipResult:
        """Generate a single clip from the video.
        
        Args:
            clip_info: Information about the clip to generate.
            index: Clip index for naming.
            apply_fade: Whether to apply fade in/out effects.
        
        Returns:
            ClipResult with success status and output path.
        """
        output_name = f"{self.video_path.stem}_clip_{index:03d}.mp4"
        output_path = self.output_dir / output_name
        
        try:
            with VideoFileClip(str(self.video_path)) as video:
                # Extract subclip
                start = max(0, clip_info.start)
                end = min(video.duration, clip_info.end)
                
                subclip = video.subclip(start, end)
                
                # Apply fade effects if requested
                if apply_fade and self.fade_duration > 0:
                    subclip = subclip.fadein(self.fade_duration).fadeout(self.fade_duration)
                
                # Write clip
                subclip.write_videofile(
                    str(output_path),
                    codec="libx264",
                    audio_codec="aac",
                    temp_audiofile=str(self.output_dir / f"temp_audio_{index}.m4a"),
                    remove_temp=True,
                    verbose=False,
                    logger=None,
                )
                
                return ClipResult(
                    source_file=str(self.video_path),
                    output_file=str(output_path),
                    clip=clip_info,
                    success=True,
                )
        
        except Exception as e:
            return ClipResult(
                source_file=str(self.video_path),
                output_file=str(output_path),
                clip=clip_info,
                success=False,
                error=str(e),
            )
    
    def generate_clips(
        self,
        clips: list[PotentialClip],
        parallel: bool = False,
        max_workers: int = 2,
        show_progress: bool = True,
    ) -> list[ClipResult]:
        """Generate multiple clips from the video.
        
        Args:
            clips: List of clips to generate.
            parallel: Whether to process in parallel.
            max_workers: Number of parallel workers.
            show_progress: Whether to show progress.
        
        Returns:
            List of ClipResults.
        """
        results: list[ClipResult] = []
        
        if parallel and len(clips) > 1:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.generate_clip, clip, i + 1): (clip, i + 1)
                    for i, clip in enumerate(clips)
                }
                
                for future in as_completed(futures):
                    clip, index = futures[future]
                    result = future.result()
                    results.append(result)
                    
                    if show_progress:
                        status = "✓" if result.success else "✗"
                        console.print(
                            f"  [{index}/{len(clips)}] "
                            f"{result.output_file.split('/')[-1]} "
                            f"Score: {clip.score.total_score:.1f} {status}"
                        )
        else:
            # Sequential processing
            for i, clip in enumerate(clips, 1):
                result = self.generate_clip(clip, i)
                results.append(result)
                
                if show_progress:
                    status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
                    time_range = f"({self._format_time(clip.start)} - {self._format_time(clip.end)})"
                    console.print(
                        f"  [dim][{i}/{len(clips)}][/dim] "
                        f"[cyan]{result.output_file.split('/')[-1]}[/cyan] "
                        f"[yellow]{time_range}[/yellow] "
                        f"Score: [magenta]{clip.score.total_score:.1f}[/magenta] {status}"
                    )
        
        # Sort by index (clip number)
        results.sort(key=lambda r: r.output_file)
        
        return results
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def create_compilation(
        self,
        clips: list[ClipResult],
        output_name: str = "compilation.mp4",
        transition_duration: float = 0.5,
    ) -> Optional[str]:
        """Create a compilation video from multiple clips.
        
        Args:
            clips: List of successfully generated clips.
            output_name: Name for the compilation file.
            transition_duration: Duration of crossfade between clips.
        
        Returns:
            Path to compilation video, or None if failed.
        """
        successful_clips = [c for c in clips if c.success]
        if len(successful_clips) < 2:
            return None
        
        try:
            video_clips = []
            for clip_result in successful_clips:
                video_clip = VideoFileClip(clip_result.output_file)
                video_clips.append(video_clip)
            
            # Concatenate with crossfade
            final = concatenate_videoclips(
                video_clips,
                method="compose",
                padding=-transition_duration,
            )
            
            output_path = self.output_dir / output_name
            final.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                verbose=False,
                logger=None,
            )
            
            # Clean up
            for clip in video_clips:
                clip.close()
            final.close()
            
            return str(output_path)
        
        except Exception as e:
            console.print(f"[red]Failed to create compilation: {e}[/red]")
            return None
