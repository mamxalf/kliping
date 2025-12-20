"""
Clipper CLI - Interactive Video Clipper for Viral Content
Main entry point with TUI menu using questionary.
"""
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional

import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from .transcriber import Transcriber, TranscriptResult, MODEL_DESCRIPTIONS, ModelSize
from .llm_providers import (
    LLMProvider, 
    get_provider, 
    get_available_providers,
    OllamaProvider
)
from .analyzer import ViralAnalyzer, ViralClip
from .clipper import VideoClipper
from .utils import validate_video_file, format_time_display
from .license import is_licensed, activate_license, get_license_info, deactivate_license

console = Console()

# Custom style for questionary
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:green'),
])

# Global config
app_config = {
    "max_clips": 5,
    "min_duration": 15,
    "max_duration": 60,
    "whisper_model": "base",
    "language": "id",
    "output_dir": "./clips"
}


def display_banner():
    """Display welcome banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║    ██████╗██╗     ██╗██████╗ ██████╗ ███████╗██████╗          ║
║   ██╔════╝██║     ██║██╔══██╗██╔══██╗██╔════╝██╔══██╗         ║
║   ██║     ██║     ██║██████╔╝██████╔╝█████╗  ██████╔╝         ║
║   ██║     ██║     ██║██╔═══╝ ██╔═══╝ ██╔══╝  ██╔══██╗         ║
║   ╚██████╗███████╗██║██║     ██║     ███████╗██║  ██║         ║
║    ╚═════╝╚══════╝╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝         ║
║                                                               ║
║           🎬 Viral Video Clipper - Free & Local 🎬            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="cyan")


def clear_screen():
    """Clear terminal screen."""
    console.clear()


def display_current_config():
    """Display current configuration."""
    console.print("\n[bold]📋 Konfigurasi Saat Ini:[/bold]")
    console.print(f"  • Whisper Model: [cyan]{app_config['whisper_model']}[/cyan]")
    console.print(f"  • Bahasa: [cyan]{app_config['language']}[/cyan]")
    console.print(f"  • Jumlah Clips: [cyan]{app_config['max_clips']}[/cyan]")
    console.print(f"  • Durasi: [cyan]{app_config['min_duration']}-{app_config['max_duration']}s[/cyan]")
    console.print(f"  • Output: [cyan]{app_config['output_dir']}[/cyan]")


def main_menu() -> str:
    """Display main menu and get user choice."""
    clear_screen()
    display_banner()
    
    choices = [
        "🎬 Mulai Clip Video",
        "⚙️  Pengaturan",
        "🤖 Kelola Ollama (AI Lokal)",
        "🔐 Status Lisensi",
        "❓ Bantuan",
        "ℹ️  Tentang Aplikasi",
        "🚪 Keluar"
    ]
    
    choice = questionary.select(
        "Pilih menu:",
        choices=choices,
        style=custom_style
    ).ask()
    
    return choice


def browse_directory(start_path: str = ".") -> Optional[str]:
    """Interactive directory/file browser."""
    current_path = Path(start_path).resolve()
    
    while True:
        console.print(f"\n[dim]📂 {current_path}[/dim]")
        
        # Get directories and video files
        items = []
        
        # Add parent directory option
        if current_path.parent != current_path:
            items.append("📁 ..")
        
        # List directories first
        try:
            for item in sorted(current_path.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    items.append(f"📁 {item.name}")
        except PermissionError:
            console.print("[red]Tidak ada akses ke folder ini[/red]")
            return None
        
        # Then video files
        video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.m4v', '.mp3', '.wav', '.m4a'}
        for item in sorted(current_path.iterdir()):
            if item.is_file() and item.suffix.lower() in video_extensions:
                items.append(f"🎬 {item.name}")
        
        if not items:
            console.print("[yellow]Folder kosong atau tidak ada video[/yellow]")
            items = ["📁 .."]
        
        items.append("❌ Batal")
        items.append("✏️  Ketik path manual")
        
        selected = questionary.select(
            "Pilih file atau folder:",
            choices=items,
            style=custom_style
        ).ask()
        
        if not selected or selected == "❌ Batal":
            return None
        
        if selected == "✏️  Ketik path manual":
            manual_path = questionary.text(
                "Masukkan path lengkap:",
                style=custom_style
            ).ask()
            if manual_path and validate_video_file(manual_path):
                return manual_path
            console.print("[red]Path tidak valid[/red]")
            continue
        
        if selected == "📁 ..":
            current_path = current_path.parent
            continue
        
        # Extract name from selection
        name = selected.split(" ", 1)[1]
        full_path = current_path / name
        
        if selected.startswith("📁"):
            # It's a directory, navigate into it
            current_path = full_path
        else:
            # It's a file, return it
            return str(full_path)


def menu_settings():
    """Settings menu."""
    while True:
        clear_screen()
        console.print("[bold cyan]⚙️  PENGATURAN[/bold cyan]")
        display_current_config()
        
        choices = [
            "🤖 Model Whisper",
            "🌐 Bahasa",
            "📊 Jumlah Clips",
            "⏱️  Durasi Clips",
            "📁 Folder Output",
            "🔙 Kembali"
        ]
        
        choice = questionary.select(
            "\nAtur yang mana?",
            choices=choices,
            style=custom_style
        ).ask()
        
        if not choice or choice == "🔙 Kembali":
            break
        
        if "Model Whisper" in choice:
            model_choices = [f"{size} - {desc}" for size, desc in MODEL_DESCRIPTIONS.items()]
            selected = questionary.select(
                "Pilih model:",
                choices=model_choices,
                style=custom_style
            ).ask()
            if selected:
                app_config["whisper_model"] = selected.split(" - ")[0]
                console.print(f"[green]✓ Model diubah ke {app_config['whisper_model']}[/green]")
        
        elif "Bahasa" in choice:
            languages = ["id - Indonesian", "en - English", "auto - Auto-detect"]
            selected = questionary.select(
                "Pilih bahasa:",
                choices=languages,
                style=custom_style
            ).ask()
            if selected:
                lang = selected.split(" - ")[0]
                app_config["language"] = None if lang == "auto" else lang
                console.print(f"[green]✓ Bahasa diubah ke {lang}[/green]")
        
        elif "Jumlah Clips" in choice:
            selected = questionary.select(
                "Jumlah clips maksimal:",
                choices=["3", "5", "7", "10", "15"],
                style=custom_style
            ).ask()
            if selected:
                app_config["max_clips"] = int(selected)
                console.print(f"[green]✓ Jumlah clips diubah ke {selected}[/green]")
        
        elif "Durasi Clips" in choice:
            presets = {
                "TikTok/Reels (15-60s)": (15, 60),
                "YouTube Shorts (30-60s)": (30, 60),
                "Twitter/X (15-45s)": (15, 45),
                "Long Clips (60-120s)": (60, 120),
                "Custom": None
            }
            selected = questionary.select(
                "Pilih preset durasi:",
                choices=list(presets.keys()),
                style=custom_style
            ).ask()
            if selected:
                if selected == "Custom":
                    min_d = questionary.text("Durasi minimum (detik):", default="15", style=custom_style).ask()
                    max_d = questionary.text("Durasi maksimum (detik):", default="60", style=custom_style).ask()
                    app_config["min_duration"] = int(min_d) if min_d else 15
                    app_config["max_duration"] = int(max_d) if max_d else 60
                else:
                    app_config["min_duration"], app_config["max_duration"] = presets[selected]
                console.print(f"[green]✓ Durasi diubah ke {app_config['min_duration']}-{app_config['max_duration']}s[/green]")
        
        elif "Folder Output" in choice:
            new_path = questionary.text(
                "Folder output:",
                default=app_config["output_dir"],
                style=custom_style
            ).ask()
            if new_path:
                app_config["output_dir"] = new_path
                console.print(f"[green]✓ Output folder diubah ke {new_path}[/green]")


def menu_ollama():
    """Manage Ollama (local AI)."""
    clear_screen()
    console.print("[bold cyan]🤖 KELOLA OLLAMA[/bold cyan]\n")
    
    ollama = OllamaProvider()
    is_running = ollama.is_available()
    
    if is_running:
        console.print("[green]✓ Ollama sedang berjalan[/green]")
        models = ollama.list_models()
        if models:
            console.print(f"\n[bold]Model tersedia:[/bold]")
            for m in models:
                console.print(f"  • {m}")
        else:
            console.print("[yellow]Tidak ada model. Install dengan: ollama pull llama3.2[/yellow]")
    else:
        console.print("[red]✗ Ollama tidak berjalan[/red]")
    
    choices = []
    if not is_running:
        choices.append("▶️  Jalankan Ollama")
    else:
        choices.append("⏹️  Stop Ollama")
    choices.append("📥 Download Model Baru")
    choices.append("🔙 Kembali")
    
    choice = questionary.select(
        "\nPilih aksi:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if not choice or choice == "🔙 Kembali":
        return
    
    if "Jalankan Ollama" in choice:
        console.print("[cyan]Menjalankan Ollama...[/cyan]")
        try:
            # Start Ollama in background
            if sys.platform == "win32":
                subprocess.Popen(["ollama", "serve"], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE,
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["ollama", "serve"], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL,
                               start_new_session=True)
            
            # Wait for it to start
            console.print("[dim]Menunggu Ollama siap...[/dim]")
            for _ in range(10):
                time.sleep(1)
                if OllamaProvider().is_available():
                    console.print("[green]✓ Ollama berhasil dijalankan![/green]")
                    break
            else:
                console.print("[yellow]Ollama mungkin butuh waktu lebih lama. Coba lagi nanti.[/yellow]")
        except FileNotFoundError:
            console.print("[red]❌ Ollama tidak terinstall. Download dari: https://ollama.ai[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
    
    elif "Stop Ollama" in choice:
        console.print("[yellow]Untuk stop Ollama, tutup terminal Ollama atau gunakan Task Manager[/yellow]")
    
    elif "Download Model" in choice:
        console.print("\n[bold]Model yang direkomendasikan:[/bold]")
        console.print("  • llama3.2 - Model terbaru, bagus untuk bahasa Indonesia")
        console.print("  • mistral - Cepat dan akurat")
        console.print("  • gemma2 - Dari Google, ringan")
        
        model_name = questionary.text(
            "\nNama model untuk didownload:",
            default="llama3.2",
            style=custom_style
        ).ask()
        
        if model_name:
            console.print(f"[cyan]Downloading {model_name}...[/cyan]")
            console.print("[dim]Ini mungkin memakan waktu beberapa menit...[/dim]")
            try:
                result = subprocess.run(
                    ["ollama", "pull", model_name],
                    capture_output=False
                )
                if result.returncode == 0:
                    console.print(f"[green]✓ {model_name} berhasil didownload![/green]")
                else:
                    console.print(f"[red]❌ Gagal download {model_name}[/red]")
            except FileNotFoundError:
                console.print("[red]❌ Ollama tidak terinstall[/red]")


def menu_help():
    """Display help information."""
    clear_screen()
    console.print("[bold cyan]❓ BANTUAN[/bold cyan]\n")
    
    help_text = """
[bold]Cara Pakai:[/bold]
1. Pastikan FFmpeg terinstall (untuk memotong video)
2. Opsional: Install Ollama untuk AI gratis lokal
3. Pilih "Mulai Clip Video" dari menu utama
4. Pilih file video yang ingin dianalisis
5. AI akan menemukan momen viral dan memotong otomatis

[bold]Requirement:[/bold]
• FFmpeg - [cyan]brew install ffmpeg[/cyan] (Mac) atau [cyan]choco install ffmpeg[/cyan] (Windows)
• Ollama (opsional) - Download dari [cyan]https://ollama.ai[/cyan]

[bold]Tips:[/bold]
• Gunakan model Whisper "small" atau "medium" untuk akurasi lebih baik
• Untuk video panjang (>30 menit), gunakan model "tiny" atau "base" untuk kecepatan
• Ollama gratis dan berjalan 100% di komputer Anda

[bold]Keyboard Shortcuts:[/bold]
• ↑↓ : Navigasi menu
• Enter : Pilih
• Ctrl+C : Batal/Keluar
    """
    console.print(help_text)
    
    questionary.press_any_key_to_continue(
        "Tekan Enter untuk kembali...",
        style=custom_style
    ).ask()


def menu_about():
    """Display about information."""
    clear_screen()
    console.print("[bold cyan]ℹ️  TENTANG APLIKASI[/bold cyan]\n")
    
    about_text = """
[bold]Clipper CLI[/bold]
Version 1.0.0

[bold cyan]Deskripsi:[/bold cyan]
Tool untuk menganalisis video podcast, menemukan momen-momen
yang berpotensi viral, dan memotongnya otomatis menjadi
short-form content untuk TikTok, Instagram Reels, YouTube Shorts.

[bold cyan]Fitur Utama:[/bold cyan]
• Transcription otomatis dengan Whisper AI
• Analisis viral menggunakan AI (Ollama/OpenAI/Gemini)
• Pemotongan video otomatis dengan FFmpeg
• Interface TUI yang mudah digunakan

[bold cyan]Tech Stack:[/bold cyan]
• [dim]Speech-to-Text:[/dim] Faster Whisper
• [dim]AI Analysis:[/dim] Ollama, OpenAI, Google Gemini
• [dim]Video Processing:[/dim] FFmpeg
• [dim]TUI Framework:[/dim] Rich, Questionary

[bold cyan]Dikembangkan oleh:[/bold cyan]
FPK Creative

[bold cyan]Website:[/bold cyan]
https://fpkcreative.space

[bold cyan]Dukungan:[/bold cyan]
Hubungi admin untuk bantuan teknis
    """
    console.print(about_text)
    
    questionary.press_any_key_to_continue(
        "Tekan Enter untuk kembali...",
        style=custom_style
    ).ask()


def run_clip_video():
    """Main video clipping workflow."""
    clear_screen()
    console.print("[bold cyan]🎬 CLIP VIDEO[/bold cyan]")
    display_current_config()
    
    # Step 1: Select video with browser
    console.print("\n[bold]📁 Pilih Video[/bold]")
    video_path = browse_directory()
    
    if not video_path:
        console.print("[yellow]Dibatalkan.[/yellow]")
        return
    
    if not validate_video_file(video_path):
        console.print(f"[red]❌ File tidak valid: {video_path}[/red]")
        return
    
    console.print(f"[green]✓ Video: {video_path}[/green]")
    
    # Ask to use current config or change
    use_current = questionary.confirm(
        "Gunakan konfigurasi saat ini?",
        default=True,
        style=custom_style
    ).ask()
    
    if not use_current:
        menu_settings()
    
    # Step 2: Transcribe
    console.print("\n[bold]🎤 Transcription[/bold]")
    console.print("[dim]Proses ini mungkin memakan waktu beberapa menit...[/dim]\n")
    
    try:
        transcriber = Transcriber(model_size=app_config["whisper_model"])
        transcript = transcriber.transcribe(video_path, language=app_config["language"])
        
        console.print(f"\n[green]✓ Transcription selesai![/green]")
        console.print(f"  • Durasi: {format_time_display(transcript.duration)}")
        console.print(f"  • Segments: {len(transcript.segments)}")
        console.print(f"  • Bahasa: {transcript.language} ({transcript.language_probability:.0%})")
    except Exception as e:
        console.print(f"[red]❌ Error transcription: {e}[/red]")
        return
    
    # Step 3: Select LLM
    console.print("\n[bold]🧠 Pilih AI untuk Analisis[/bold]")
    
    providers = get_available_providers()
    choices = [desc for _, desc in providers]
    
    selected = questionary.select(
        "Pilih AI provider:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if not selected:
        console.print("[yellow]Dibatalkan.[/yellow]")
        return
    
    # Find selected provider
    provider = None
    provider_kwargs = {}
    
    for p, desc in providers:
        if desc == selected:
            provider = p
            break
    
    if provider == LLMProvider.OLLAMA:
        ollama = OllamaProvider()
        if not ollama.is_available():
            start_ollama = questionary.confirm(
                "Ollama tidak berjalan. Jalankan sekarang?",
                default=True,
                style=custom_style
            ).ask()
            
            if start_ollama:
                menu_ollama()
                if not OllamaProvider().is_available():
                    console.print("[red]Ollama masih tidak berjalan. Dibatalkan.[/red]")
                    return
            else:
                return
        
        models = ollama.list_models()
        if not models:
            console.print("[red]❌ Tidak ada model. Download dulu di menu Ollama.[/red]")
            return
        
        model = questionary.select(
            "Pilih model:",
            choices=models,
            style=custom_style
        ).ask()
        if model:
            provider_kwargs["model"] = model
        else:
            return
    
    elif provider == LLMProvider.OPENAI:
        if not os.getenv("OPENAI_API_KEY"):
            api_key = questionary.password(
                "Masukkan OpenAI API key:",
                style=custom_style
            ).ask()
            if api_key:
                provider_kwargs["api_key"] = api_key
            else:
                return
    
    elif provider == LLMProvider.GEMINI:
        if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            api_key = questionary.password(
                "Masukkan Google API key:",
                style=custom_style
            ).ask()
            if api_key:
                provider_kwargs["api_key"] = api_key
            else:
                return
    
    # Step 4: Analyze
    console.print("\n[bold]📊 Analisis Viral[/bold]")
    console.print("[dim]AI sedang mencari momen viral...[/dim]\n")
    
    try:
        llm = get_provider(provider, **provider_kwargs)
        analyzer = ViralAnalyzer(llm)
        clips = analyzer.analyze(
            transcript,
            max_clips=app_config["max_clips"],
            min_duration=app_config["min_duration"],
            max_duration=app_config["max_duration"]
        )
        
        if not clips:
            console.print("[yellow]⚠️ Tidak ditemukan momen viral yang signifikan[/yellow]")
            return
    except Exception as e:
        console.print(f"[red]❌ Error analisis: {e}[/red]")
        return
    
    # Display clips
    console.print("\n[bold green]🎯 Momen Viral yang Ditemukan:[/bold green]\n")
    
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("#", width=3)
    table.add_column("Title", width=25)
    table.add_column("Waktu", width=13)
    table.add_column("Score", width=6)
    table.add_column("Alasan", width=50)
    
    for i, clip in enumerate(clips, 1):
        score_color = "green" if clip.viral_score >= 7 else "yellow" if clip.viral_score >= 5 else "red"
        score_display = f"[{score_color}]{clip.viral_score}/10[/{score_color}]"
        
        # Truncate reason if too long
        reason_text = clip.reason[:48] + ".." if len(clip.reason) > 50 else clip.reason
        
        table.add_row(
            str(i),
            clip.title[:23] + ".." if len(clip.title) > 25 else clip.title,
            f"{format_time_display(clip.start_time)}-{format_time_display(clip.end_time)}",
            score_display,
            reason_text
        )
    
    console.print(table)
    
    # Show detailed info for each clip
    console.print("\n[bold]📋 Detail Clips:[/bold]")
    for i, clip in enumerate(clips, 1):
        console.print(f"\n[cyan]#{i}. {clip.title}[/cyan]")
        console.print(f"   ⏱️  {format_time_display(clip.start_time)} - {format_time_display(clip.end_time)} ({clip.duration:.0f}s)")
        console.print(f"   ⭐ Score: {clip.viral_score}/10")
        console.print(f"   💡 Alasan: {clip.reason}")
        if clip.hook:
            console.print(f"   🎣 Hook: {clip.hook}")
    
    # Step 5: Select clips to export
    console.print("\n[bold]✂️ Pilih Clips untuk Export[/bold]")
    console.print("[dim]Gunakan SPACE untuk toggle, ENTER untuk confirm[/dim]\n")
    
    clip_choices = [
        f"{i+1}. {clip.title} ({format_time_display(clip.start_time)}-{format_time_display(clip.end_time)}) - Score: {clip.viral_score}/10"
        for i, clip in enumerate(clips)
    ]
    
    selected_names = questionary.checkbox(
        "Pilih clips:",
        choices=clip_choices,
        style=custom_style
    ).ask()
    
    if not selected_names:
        console.print("[yellow]Tidak ada clip yang dipilih.[/yellow]")
        return
    
    # Map back to clips
    selected_clips = []
    for name in selected_names:
        idx = int(name.split(".")[0]) - 1
        selected_clips.append(clips[idx])
    
    console.print(f"[green]✓ {len(selected_clips)} clips dipilih[/green]")
    
    # Step 6: Export
    console.print(f"\n[bold]🎥 Export ke {app_config['output_dir']}[/bold]\n")
    
    clipper = VideoClipper(output_dir=app_config["output_dir"])
    results = clipper.clip_multiple(video_path, selected_clips)
    
    # Show results
    console.print("\n[bold green]✅ Export Selesai![/bold green]\n")
    
    result_table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    result_table.add_column("Clip", width=35)
    result_table.add_column("File", width=50)
    
    for clip, path in results:
        result_table.add_row(clip.title, path)
    
    console.print(result_table)
    console.print(f"\n[green]Total: {len(results)} clips berhasil di-export![/green]")
    
    questionary.press_any_key_to_continue(
        "\nTekan Enter untuk kembali ke menu...",
        style=custom_style
    ).ask()


def show_activation_screen() -> bool:
    """Show license activation screen. Returns True if activated."""
    clear_screen()
    console.print("[bold cyan]🔐 AKTIVASI LISENSI[/bold cyan]\n")
    console.print("Software ini membutuhkan lisensi untuk digunakan.")
    console.print("Hubungi admin untuk mendapatkan serial key.\n")
    
    serial_key = questionary.text(
        "Masukkan Serial Key (XXXX-XXXX-XXXX-XXXX):",
        style=custom_style
    ).ask()
    
    if not serial_key:
        return False
    
    success, message = activate_license(serial_key)
    
    if success:
        console.print(f"\n[green]✓ {message}[/green]")
        questionary.press_any_key_to_continue(
            "Tekan Enter untuk melanjutkan...",
            style=custom_style
        ).ask()
        return True
    else:
        console.print(f"\n[red]❌ {message}[/red]")
        questionary.press_any_key_to_continue(
            "Tekan Enter untuk coba lagi...",
            style=custom_style
        ).ask()
        return False


def menu_license():
    """License management menu."""
    clear_screen()
    console.print("[bold cyan]🔐 STATUS LISENSI[/bold cyan]\n")
    
    license_info = get_license_info()
    
    if license_info:
        console.print("[green]✓ Lisensi Aktif[/green]\n")
        console.print(f"Serial Key: [cyan]{license_info.serial_key}[/cyan]")
        console.print(f"Diaktivasi: [dim]{license_info.activated_at}[/dim]")
        console.print(f"Machine ID: [dim]{license_info.machine_id}[/dim]")
    else:
        console.print("[red]✗ Tidak ada lisensi aktif[/red]")
    
    console.print("")
    questionary.press_any_key_to_continue(
        "Tekan Enter untuk kembali...",
        style=custom_style
    ).ask()


def main():
    """Main entry point."""
    # Check license on startup
    if not is_licensed():
        console.print("")
        display_banner()
        console.print("\n[yellow]⚠️  Software ini memerlukan lisensi.[/yellow]\n")
        
        # Keep asking for activation until success or user quits
        while True:
            if show_activation_screen():
                break
            
            retry = questionary.confirm(
                "Coba aktivasi lagi?",
                default=True,
                style=custom_style
            ).ask()
            
            if not retry:
                console.print("\n[red]Keluar tanpa lisensi.[/red]")
                sys.exit(1)
    
    try:
        while True:
            choice = main_menu()
            
            if not choice or "Keluar" in choice:
                console.print("\n[cyan]Terima kasih! Sampai jumpa! 👋[/cyan]\n")
                break
            
            if "Clip Video" in choice:
                run_clip_video()
            
            elif "Pengaturan" in choice:
                menu_settings()
            
            elif "Ollama" in choice:
                menu_ollama()
            
            elif "Bantuan" in choice:
                menu_help()
            
            elif "Lisensi" in choice:
                menu_license()
            
            elif "Tentang" in choice:
                menu_about()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Dibatalkan.[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
