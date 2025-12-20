# 🎬 Clipper CLI - Viral Video Clipper

Tool untuk menganalisa video podcast/konten panjang, menemukan momen potensial viral, dan memotong secara otomatis.

**100% Gratis dengan opsi Local-only!**

## ✨ Fitur

- 🎤 **Transcription** - Menggunakan faster-whisper (gratis, offline)
- 🤖 **AI Analysis** - Ollama (local) atau OpenAI/Gemini (cloud)
- ✂️ **Auto Clip** - Potong video otomatis dengan FFmpeg
- 🖥️ **User-friendly TUI** - Menu interaktif untuk user awam

## 📋 Prerequisites

### 1. FFmpeg
FFmpeg harus terinstall dan tersedia di PATH.

**Windows:**
```bash
# Menggunakan Chocolatey
choco install ffmpeg

# Atau download dari https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

### 2. Ollama (Opsional - untuk AI local gratis)
```bash
# Install Ollama dari https://ollama.ai
# Kemudian download model:
ollama pull llama3.2
```

## 🚀 Instalasi

```bash
# Clone repo
cd clipper-cli

# Install dependencies dengan Poetry
poetry install
```

## 📖 Penggunaan

### Jalankan Interactive Mode
```bash
poetry run python -m clipper_cli.main
```

### Flow Aplikasi
1. **Pilih Video** - Browse atau ketik path ke video
2. **Pilih Model Whisper** - tiny/base/small/medium/large
3. **Pilih Bahasa** - Indonesian/English/Auto
4. **Transcription** - Proses speech-to-text
5. **Pilih AI** - Ollama (local) atau OpenAI/Gemini (cloud)
6. **Analisis Viral** - AI menemukan momen viral
7. **Review & Pilih Clips** - Pilih clips yang mau di-export
8. **Export** - Video clips disimpan ke folder output

## 🔧 Build ke .exe (Windows)

```bash
# Install PyInstaller
poetry add pyinstaller --group dev

# Build
poetry run pyinstaller build.spec

# Hasil di folder dist/clipper.exe
```

## 🌐 Environment Variables (Opsional)

Untuk AI cloud, set API keys:

```bash
# OpenAI
export OPENAI_API_KEY=sk-xxx

# Google Gemini
export GOOGLE_API_KEY=xxx
# atau
export GEMINI_API_KEY=xxx
```

## 📁 Struktur Output

```
clips/
├── video_clip_01.mp4  # High viral score
├── video_clip_02.mp4
└── video_clip_03.mp4
```

## 🛠️ Tech Stack

| Component | Library |
|-----------|---------|
| Transcription | faster-whisper |
| TUI Menu | questionary |
| Progress UI | rich |
| Video Processing | ffmpeg-python |
| LLM Local | ollama |
| LLM Cloud | openai, google-generativeai |

## 📝 License

MIT License
