# Clipper CLI - Panduan Pengguna (Windows)

Panduan lengkap untuk menggunakan Clipper CLI di Windows.

---

## Persyaratan Sistem

| Komponen | Minimum | Rekomendasi |
|----------|---------|-------------|
| OS | Windows 10 | Windows 11 |
| RAM | 8 GB | 16 GB |
| Storage | 5 GB free | 20 GB free |
| FFmpeg | Required | Required |

---

## Instalasi

### 1. Download Clipper CLI

Download file `clipper-X.X.X-windows.exe` dari:
- GitHub Releases: `https://github.com/[repo]/releases`
- Atau link yang diberikan seller

### 2. Install FFmpeg (WAJIB)

FFmpeg diperlukan untuk memproses video.

**Cara Install:**

1. Download dari: https://www.gyan.dev/ffmpeg/builds/
2. Pilih `ffmpeg-release-essentials.zip`
3. Extract ke `C:\ffmpeg`
4. Tambahkan ke PATH:
   - Buka **Settings** → **System** → **About** → **Advanced system settings**
   - Klik **Environment Variables**
   - Di **System variables**, cari `Path` dan klik **Edit**
   - Klik **New** dan tambahkan: `C:\ffmpeg\bin`
   - Klik **OK**

5. Verifikasi dengan membuka Command Prompt:
   ```cmd
   ffmpeg -version
   ```

### 3. Install Ollama (Untuk LLM Lokal - Opsional)

Jika ingin menggunakan AI lokal tanpa internet:

1. Download dari: https://ollama.ai/download
2. Install dan jalankan Ollama
3. Download model:
   ```cmd
   ollama pull llama3.2
   ```

---

## Aktivasi License

Saat pertama kali menjalankan Clipper CLI, Anda akan diminta memasukkan license key.

```
[KEY] LICENSE ACTIVATION

Please enter your license key to activate Clipper CLI.
Format: CLIPPER-XXXX-XXXX-XXXX-XXXX
```

1. Masukkan license key yang Anda terima dari seller
2. Tekan Enter
3. Jika valid, aplikasi akan aktif dan siap digunakan

> **Note:** License akan disimpan dan tidak perlu dimasukkan lagi.

---

## Penggunaan

### Menjalankan Aplikasi

Double-click `clipper.exe` atau jalankan dari Command Prompt:

```cmd
clipper.exe
```

### Menu Utama

```
? What would you like to do?
  [1] Process Single Video
  [2] Batch Process Videos
  ──────────────────────────────
  [3] Settings
  [4] View Providers
  [5] System Check
  [6] License Info
  ──────────────────────────────
  [X] Exit
```

### Memproses Video

1. Pilih **[1] Process Single Video**
2. Pilih video dari file browser
3. Pilih transcription provider:
   - **Whisper (Offline)** - Gratis, hasil bagus
   - **AssemblyAI (Cloud)** - Lebih cepat, butuh API key
4. Pilih LLM provider:
   - **Ollama (Local)** - Gratis, butuh install Ollama
   - **OpenAI/Gemini/Claude** - Butuh API key
5. Atur pengaturan clip:
   - Jumlah clip yang diinginkan
   - Durasi minimum/maksimum
   - Bahasa video
6. Pilih output directory
7. Konfirmasi dan mulai proses

### Hasil

Clips akan disimpan di folder output dengan nama format:
```
clip_001_0m30s-1m15s.mp4
clip_002_5m20s-6m05s.mp4
...
```

---

## Pengaturan API Keys

Untuk menggunakan cloud providers, Anda perlu API keys.

### Cara Mendapatkan API Keys

| Provider | Link | Gratis? |
|----------|------|---------|
| AssemblyAI | https://www.assemblyai.com | Free tier tersedia |
| OpenAI | https://platform.openai.com | Berbayar |
| Gemini | https://aistudio.google.com | Gratis (terbatas) |
| Claude | https://console.anthropic.com | Berbayar |

### Cara Setting

1. Pilih **[3] Settings** dari menu utama
2. Pilih **[1] API Keys**
3. Pilih provider yang ingin di-setting
4. Masukkan API key
5. Key akan disimpan di `~/.clipper-cli/.env`

---

## Troubleshooting

### Error: FFmpeg not found

**Solusi:** Install FFmpeg dan pastikan sudah ada di PATH.

### Error: Ollama not available

**Solusi:**
1. Pastikan Ollama sudah terinstall dan berjalan
2. Download model: `ollama pull llama3.2`

### Error: API key not set

**Solusi:** Masuk ke Settings → API Keys dan masukkan key yang valid.

### Aplikasi hang saat transcribing

**Info:** Transcription memerlukan waktu, terutama untuk video panjang. Loading spinner akan berputar selama proses berjalan.

### Video tidak terdeteksi

**Solusi:** Pastikan format video adalah: `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`

---

## Tips

1. **Video pendek = proses cepat** - Untuk testing, gunakan video < 5 menit
2. **Whisper Tiny = paling cepat** - Gunakan untuk testing
3. **Gunakan Ollama untuk hemat biaya** - Tidak perlu bayar API
4. **Backup video asli** - Clipper tidak mengubah video asli

---

## Support

Jika ada masalah atau pertanyaan, hubungi seller Anda.
