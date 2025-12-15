"""Screen components for interactive mode.

This module contains the visual components for the CLI interface,
including the welcome screen, menus, and status displays.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

console = Console()


CLIPPER_LOGO = """
     ██████╗██╗     ██╗██████╗ ██████╗ ███████╗██████╗ 
    ██╔════╝██║     ██║██╔══██╗██╔══██╗██╔════╝██╔══██╗
    ██║     ██║     ██║██████╔╝██████╔╝█████╗  ██████╔╝
    ██║     ██║     ██║██╔═══╝ ██╔═══╝ ██╔══╝  ██╔══██╗
    ╚██████╗███████╗██║██║     ██║     ███████╗██║  ██║
     ╚═════╝╚══════╝╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝
"""


def show_welcome(version: str, license_status: str) -> None:
    """Display the welcome screen with logo."""
    console.clear()
    
    # Logo
    logo_text = Text(CLIPPER_LOGO, style="bold cyan")
    
    # Subtitle
    subtitle = Text()
    subtitle.append("[VIDEO] Cut Long Videos into Viral Clips using AI\n\n", style="dim")
    subtitle.append(f"Version: ", style="dim")
    subtitle.append(f"v{version}", style="cyan")
    subtitle.append(" | ", style="dim")
    subtitle.append(f"License: ", style="dim")
    subtitle.append(license_status, style="green" if "[OK]" in license_status else "red")
    
    panel = Panel(
        Text.assemble(logo_text, "\n", subtitle),
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 2),
    )
    
    console.print(panel)


def show_activation_screen() -> None:
    """Display the license activation screen."""
    console.clear()
    
    # Logo
    logo_text = Text(CLIPPER_LOGO, style="bold cyan")
    
    # Activation message
    message = Text()
    message.append("\n\n")
    message.append("[KEY] LICENSE ACTIVATION\n\n", style="bold yellow")
    message.append("Please enter your license key to activate Clipper CLI.\n", style="dim")
    message.append("Format: CLIPPER-XXXX-XXXX-XXXX-XXXX\n\n", style="dim italic")
    message.append("-" * 50 + "\n", style="dim")
    message.append("Don't have a license? Contact the seller.\n", style="dim")
    
    panel = Panel(
        Text.assemble(logo_text, message),
        border_style="yellow",
        box=box.DOUBLE,
        padding=(1, 2),
    )
    
    console.print(panel)


def show_main_menu_header() -> None:
    """Display main menu header."""
    console.print("\n[bold cyan][MENU] Main Menu[/bold cyan]\n")


def show_processing_header(video_name: str) -> None:
    """Display processing header."""
    console.print(f"\n[bold cyan][VIDEO] Processing: [white]{video_name}[/white][/bold cyan]\n")


def show_success_message(message: str) -> None:
    """Display a success message."""
    console.print(f"[green][OK] {message}[/green]")


def show_error_message(message: str) -> None:
    """Display an error message."""
    console.print(f"[red][ERROR] {message}[/red]")


def show_warning_message(message: str) -> None:
    """Display a warning message."""
    console.print(f"[yellow][WARN] {message}[/yellow]")


def show_info_message(message: str) -> None:
    """Display an info message."""
    console.print(f"[blue][INFO] {message}[/blue]")


def show_goodbye() -> None:
    """Display goodbye message."""
    console.print("\n[cyan]Thanks for using Clipper CLI! Goodbye.[/cyan]\n")


def show_settings_header() -> None:
    """Display settings header."""
    console.print("\n[bold cyan][SETTINGS][/bold cyan]\n")


def show_license_info(license_info: dict) -> None:
    """Display license information."""
    table = Table(
        title="[KEY] License Information",
        box=box.ROUNDED,
        show_header=False,
        padding=(0, 2),
    )
    
    table.add_column("Field", style="dim")
    table.add_column("Value", style="cyan")
    
    if license_info:
        table.add_row("Status", "[green][OK] Activated[/green]")
        table.add_row("License Key", license_info.get("masked_key", "****-****-****-****"))
        table.add_row("Activated On", license_info.get("activated_at", "N/A")[:10])
    else:
        table.add_row("Status", "[red][X] Not Activated[/red]")
    
    console.print(table)


def show_providers_status(transcribers: list, llm_providers: list) -> None:
    """Display available providers and their status."""
    
    # Transcription providers
    console.print("\n[bold]Transcription Providers:[/bold]\n")
    
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Provider")
    table.add_column("Type")
    table.add_column("Status")
    
    for provider in transcribers:
        status = "[green]Ready[/green]" if provider["available"] else "[red]Not available[/red]"
        table.add_row(provider["name"], provider["type"], status)
    
    console.print(table)
    
    # LLM providers
    console.print("\n[bold]LLM Providers:[/bold]\n")
    
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Provider")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Model")
    
    for provider in llm_providers:
        status = "[green]Ready[/green]" if provider["available"] else "[red]Not configured[/red]"
        table.add_row(provider["name"], provider["type"], status, provider.get("model", "-"))
    
    console.print(table)


def show_clip_results(clips: list, output_dir: str) -> None:
    """Display generated clips results."""
    if not clips:
        show_warning_message("No clips were generated.")
        return
    
    console.print("\n[bold cyan][CLIPS] Generated Clips[/bold cyan]\n")
    
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("File", style="green")
    table.add_column("Time", style="yellow")
    table.add_column("Duration", style="blue")
    table.add_column("Score", style="magenta")
    
    for i, clip in enumerate(clips, 1):
        start_time = _format_time(clip.clip.start)
        end_time = _format_time(clip.clip.end)
        duration = f"{clip.clip.duration:.1f}s"
        score = f"{clip.clip.score.total_score:.1f}"
        filename = clip.output_file.split("/")[-1].split("\\")[-1]
        
        table.add_row(
            str(i),
            filename,
            f"{start_time} - {end_time}",
            duration,
            score,
        )
    
    console.print(table)
    console.print(f"\n[green][OK] Clips saved to:[/green] [cyan]{output_dir}[/cyan]\n")


def _format_time(seconds: float) -> str:
    """Format seconds as MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"
