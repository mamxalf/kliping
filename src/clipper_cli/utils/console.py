"""Rich console utilities for beautiful terminal output."""

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from contextlib import contextmanager
from typing import Generator, Optional

# Global console instance
console = Console()


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """Print a styled header."""
    header_text = Text()
    header_text.append("📹 ", style="bold")
    header_text.append(title, style="bold cyan")
    
    if subtitle:
        content = f"{header_text}\n{subtitle}"
    else:
        content = header_text
    
    console.print(Panel(
        content,
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 2),
    ))


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✅ {message}[/green]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]❌ {message}[/red]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]⚠️  {message}[/yellow]")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]ℹ️  {message}[/blue]")


def print_step(message: str, indent: int = 0) -> None:
    """Print a step in the process."""
    prefix = "  " * indent + "└─ " if indent > 0 else ""
    console.print(f"[dim]{prefix}[/dim]{message}")


@contextmanager
def create_progress() -> Generator[Progress, None, None]:
    """Create a progress bar context."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    with progress:
        yield progress


@contextmanager
def create_spinner(message: str) -> Generator[Progress, None, None]:
    """Create a spinner context."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )
    with progress:
        progress.add_task(description=message, total=None)
        yield progress


def create_clips_table(clips: list, show_caption: bool = True) -> Table:
    """Create a table showing clip results."""
    table = Table(
        title="Generated Clips",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    
    table.add_column("#", style="dim", width=3)
    table.add_column("File", style="green")
    table.add_column("Time", style="yellow")
    table.add_column("Duration", style="blue")
    table.add_column("Score", style="magenta")
    if show_caption:
        table.add_column("Caption", style="dim", max_width=30)
    
    for i, clip in enumerate(clips, 1):
        start_time = format_time(clip.clip.start)
        end_time = format_time(clip.clip.end)
        duration = f"{clip.clip.duration:.1f}s"
        score = f"{clip.clip.score.total_score:.1f}"
        
        row = [
            str(i),
            clip.output_file.split("/")[-1],
            f"{start_time} - {end_time}",
            duration,
            score,
        ]
        
        if show_caption and clip.clip.suggested_caption:
            row.append(clip.clip.suggested_caption[:30] + "...")
        elif show_caption:
            row.append("-")
        
        table.add_row(*row)
    
    return table


def create_providers_table(providers: dict) -> Table:
    """Create a table showing available providers."""
    table = Table(
        title="Available Providers",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    
    table.add_column("Provider", style="green")
    table.add_column("Type", style="blue")
    table.add_column("Status", style="yellow")
    table.add_column("Default Model", style="dim")
    
    for name, info in providers.items():
        status = "[green]✓ Ready[/green]" if info["available"] else "[red]✗ Not configured[/red]"
        table.add_row(
            name,
            info["type"],
            status,
            info.get("default_model", "-"),
        )
    
    return table


def create_batch_summary_panel(result) -> Panel:
    """Create a panel showing batch processing summary."""
    content = Text()
    content.append(f"Total Videos:     {result.total_videos}\n", style="white")
    content.append(f"Successful:       {result.successful}\n", style="green")
    content.append(f"Failed:           {result.failed}\n", style="red" if result.failed > 0 else "dim")
    content.append(f"Total Clips:      {result.total_clips}\n", style="cyan")
    content.append(f"Processing Time:  {format_duration(result.processing_time)}\n", style="yellow")
    
    return Panel(
        content,
        title="📊 Batch Summary",
        box=box.ROUNDED,
        border_style="cyan",
    )


def format_time(seconds: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def print_result_summary(result, output_dir: str) -> None:
    """Print a summary of processing results."""
    if not result.clips:
        print_warning("No clips were generated.")
        return
    
    console.print()
    console.print(create_clips_table(result.clips))
    console.print()
    
    # Top clip highlight
    if result.clips:
        top_clip = max(result.clips, key=lambda c: c.clip.score.total_score)
        content = Text()
        content.append(f"✅ Successfully created {len(result.clips)} clips in {output_dir}\n\n", style="green")
        content.append(f"🏆 Top Clip: ", style="bold")
        content.append(f"{top_clip.output_file.split('/')[-1]}\n", style="cyan")
        content.append(f"📌 Viral Factor: ", style="bold")
        content.append(f"{top_clip.clip.viral_factor}\n", style="yellow")
        if top_clip.clip.suggested_caption:
            content.append(f"💬 Caption: ", style="bold")
            content.append(f'"{top_clip.clip.suggested_caption}"', style="dim italic")
        
        console.print(Panel(
            content,
            box=box.ROUNDED,
            border_style="green",
        ))
