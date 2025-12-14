# Clipper CLI

🎬 CLI tool to cut long videos into viral clips using AI.

## Features

- **Dual Transcription Mode**
  - 🔒 **Offline**: Whisper (free, private, requires good hardware)
  - ☁️ **Cloud**: AssemblyAI (fast, speaker diarization, sentiment analysis)

- **Multi-Provider LLM Support**
  - 🦙 **Ollama** - Local/offline, free
  - 🤖 **OpenAI** - GPT-4o, GPT-4o-mini
  - 💎 **Google Gemini** - Gemini 2.0 Flash (generous free tier!)
  - 🧠 **Anthropic Claude** - Claude 3.5 Sonnet

- **Batch Processing**
  - Process entire directories
  - Parallel workers
  - Resume interrupted batches
  - Detailed reports

## Installation

```bash
# Install dependencies
poetry install

# Install FFmpeg (required)
brew install ffmpeg  # macOS

# For offline mode, install Ollama
brew install ollama
ollama serve
ollama pull llama3.2
```

## Configuration

```bash
# Set API keys (as needed)
clipper config set ASSEMBLYAI_API_KEY your_key
clipper config set OPENAI_API_KEY your_key
clipper config set GEMINI_API_KEY your_key
clipper config set ANTHROPIC_API_KEY your_key
```

## Usage

### Single Video Processing

```bash
# Fully offline (Whisper + Ollama)
clipper process video.mp4 --transcribe whisper --llm ollama

# Cloud mode - lightweight (AssemblyAI + Gemini)
clipper process video.mp4 --transcribe assemblyai --llm gemini

# With options
clipper process video.mp4 \
  --transcribe assemblyai \
  --llm gemini \
  --num-clips 5 \
  --min-duration 15 \
  --max-duration 60 \
  --output-dir ./clips
```

### Batch Processing

```bash
# Process all videos in directory
clipper batch ./videos/ --transcribe assemblyai --llm gemini

# With parallel workers
clipper batch ./videos/ --workers 4

# Resume interrupted batch
clipper batch ./videos/ --resume
```

### Utilities

```bash
# Check system requirements
clipper check

# List available providers
clipper providers

# View batch report
clipper report ./output/batch_report.json
```

## Recommended Configurations

| Use Case | Command |
|----------|---------|
| 🔒 Full Privacy | `--transcribe whisper --llm ollama` |
| 💰 Budget Friendly | `--transcribe whisper --llm gemini` |
| 💻 Light Device | `--transcribe assemblyai --llm gemini` |
| ⭐ Best Quality | `--transcribe assemblyai --llm openai` |

## License

MIT
