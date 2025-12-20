"""
Video clipper using FFmpeg.
Cuts video segments based on timestamps.
"""
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .analyzer import ViralClip
from .utils import ensure_output_dir, get_output_filename

console = Console()


class VideoClipper:
    """Clips video segments using FFmpeg."""
    
    def __init__(self, output_dir: str = "./clips"):
        self.output_dir = ensure_output_dir(output_dir)
    
    def clip_video(
        self, 
        input_path: str, 
        start_time: float, 
        end_time: float,
        output_path: Optional[str] = None,
        index: int = 1
    ) -> str:
        """
        Cut a segment from video.
        
        Args:
            input_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Optional output path (auto-generated if None)
            index: Clip index for naming
        
        Returns:
            Path to output clip
        """
        if output_path is None:
            output_filename = get_output_filename(input_path, index)
            output_path = str(self.output_dir / output_filename)
        
        duration = end_time - start_time
        
        cmd = [
            "ffmpeg",
            "-ss", str(start_time),  # Seek before input (faster)
            "-i", input_path,
            "-t", str(duration),
            "-c:v", "libx264",  # Re-encode video
            "-c:a", "aac",      # Re-encode audio
            "-preset", "fast",   # Encoding speed
            "-crf", "23",        # Quality (lower = better)
            "-y",                # Overwrite
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error clipping video: {e.stderr.decode()}[/red]")
            raise
    
    def clip_multiple(
        self, 
        input_path: str, 
        clips: list[ViralClip],
        show_progress: bool = True
    ) -> list[tuple[ViralClip, str]]:
        """
        Clip multiple segments from video.
        
        Args:
            input_path: Path to source video
            clips: List of ViralClip objects
            show_progress: Whether to show progress bar
        
        Returns:
            List of (ViralClip, output_path) tuples
        """
        results = []
        
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Clipping videos...", total=len(clips))
                
                for i, clip in enumerate(clips, 1):
                    progress.update(task, description=f"[cyan]Clipping: {clip.title[:30]}...")
                    
                    try:
                        output_path = self.clip_video(
                            input_path,
                            clip.start_time,
                            clip.end_time,
                            index=i
                        )
                        results.append((clip, output_path))
                    except Exception as e:
                        console.print(f"[red]Failed to clip '{clip.title}': {e}[/red]")
                    
                    progress.advance(task)
        else:
            for i, clip in enumerate(clips, 1):
                try:
                    output_path = self.clip_video(
                        input_path,
                        clip.start_time,
                        clip.end_time,
                        index=i
                    )
                    results.append((clip, output_path))
                except Exception as e:
                    console.print(f"[red]Failed to clip '{clip.title}': {e}[/red]")
        
        console.print(f"[green]✓ Successfully created {len(results)} clips![/green]")
        return results
