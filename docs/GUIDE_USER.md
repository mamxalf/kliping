# 🎬 Clipper CLI - Panduan User

Panduan lengkap untuk menggunakan Clipper CLI - tool untuk memotong video podcast menjadi clips viral.

---

## 📋 Daftar Isi

1. [Instalasi](#instalasi)
2. [Aktivasi Lisensi](#aktivasi-lisensi)
3. [Cara Pakai](#cara-pakai)
4. [Pengaturan](#pengaturan)
5. [Setup AI (Ollama)](#setup-ai-ollama)
6. [FAQ](#faq)

---

## Instalasi

### Prasyarat

Sebelum menggunakan Clipper CLI, pastikan sudah terinstall:

1. **FFmpeg** (wajib) - untuk memotong video
   ```bash
   # Windows (dengan Chocolatey)
   choco install ffmpeg
   
   # Mac
   brew install ffmpeg
   
   # Linux
   sudo apt install ffmpeg
   ```

2. **Ollama** (opsional) - untuk AI gratis di komputer lokal
   - Download dari [https://ollama.ai](https://ollama.ai)
   - Gratis dan 100% offline

### Menjalankan Clipper

```bash
# Masuk ke folder clipper-cli
cd clipper-cli

# Jalankan
./clipper.exe          # Windows
./clipper              # Mac/Linux
```

---

## Aktivasi Lisensi

Saat pertama kali menjalankan, Anda akan diminta memasukkan serial key.

```
🔐 AKTIVASI LISENSI

Software ini membutuhkan lisensi untuk digunakan.
Hubungi admin untuk mendapatkan serial key.

? Masukkan Serial Key (XXXX-XXXX-XXXX-XXXX): _
```

### Langkah-langkah:
1. Hubungi seller/admin untuk mendapatkan serial key
2. Masukkan serial key dalam format `XXXX-XXXX-XXXX-XXXX`
3. Tekan Enter
4. Jika berhasil, lisensi akan tersimpan otomatis

> ⚠️ **Penting:** Serial key hanya bisa digunakan di 1 komputer.

---

## Cara Pakai

### Menu Utama

Setelah aktivasi, Anda akan melihat menu utama:

```
? Pilih menu:
  🎬 Mulai Clip Video
  ⚙️  Pengaturan
  🤖 Kelola Ollama (AI Lokal)
  🔐 Status Lisensi
  ❓ Bantuan
  🚪 Keluar
```

### Langkah Memotong Video

1. **Pilih "🎬 Mulai Clip Video"**

2. **Pilih file video**
   - Gunakan ↑↓ untuk navigasi folder
   - Pilih file video (mp4, mkv, avi, dll)

3. **Proses Transcription**
   - Tunggu proses speech-to-text
   - Waktu tergantung panjang video dan model yang dipilih

4. **Pilih AI untuk analisis**
   - Ollama (gratis, lokal)
   - OpenAI (berbayar, butuh API key)
   - Google Gemini (berbayar, butuh API key)

5. **Review hasil analisis**
   - AI akan menemukan momen-momen viral
   - Lihat skor, alasan, dan hook untuk setiap clip

6. **Pilih clips untuk export**
   - Gunakan SPACE untuk toggle pilihan
   - Tekan ENTER untuk confirm

7. **Selesai!**
   - Clips tersimpan di folder `./clips`

---

## Pengaturan

Akses dari menu: **⚙️ Pengaturan**

| Setting | Deskripsi | Rekomendasi |
|---------|-----------|-------------|
| Model Whisper | Akurasi transcription | `small` untuk bahasa Indonesia |
| Bahasa | Bahasa video | `id` untuk Indonesia |
| Jumlah Clips | Maksimal clips yang dicari | `5-7` clips |
| Durasi Clips | Panjang setiap clip | TikTok: 15-60s |
| Folder Output | Lokasi simpan clips | `./clips` |

### Model Whisper

| Model | Ukuran | Kecepatan | Akurasi |
|-------|--------|-----------|---------|
| tiny | 75MB | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| base | 150MB | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| small | 500MB | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| medium | 1.5GB | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| large-v3 | 3GB | ⭐ | ⭐⭐⭐⭐⭐ |

---

## Setup AI (Ollama)

Ollama adalah AI gratis yang berjalan di komputer Anda.

### Instalasi Ollama

1. Download dari [https://ollama.ai](https://ollama.ai)
2. Install seperti aplikasi biasa
3. Jalankan Ollama

### Download Model

Di menu **🤖 Kelola Ollama**, pilih "Download Model Baru":

| Model | Ukuran | Kasus Penggunaan |
|-------|--------|------------------|
| llama3.2 | ~2GB | Terbaik untuk Indonesia |
| mistral | ~4GB | Cepat dan akurat |
| gemma2 | ~1.5GB | Ringan |

### Menjalankan Ollama

Ollama harus berjalan saat menggunakan Clipper:
- **Otomatis:** Pilih "▶️ Jalankan Ollama" di menu
- **Manual:** Buka terminal, ketik `ollama serve`

---

## FAQ

### ❓ Serial key tidak berfungsi?
- Pastikan format benar: `XXXX-XXXX-XXXX-XXXX`
- Gunakan huruf kapital
- Hubungi admin untuk konfirmasi

### ❓ Transcription sangat lambat?
- Gunakan model `tiny` atau `base` untuk video panjang
- Pastikan tidak ada aplikasi berat lain berjalan

### ❓ Tidak ada momen viral ditemukan?
- Coba tingkatkan "Jumlah Clips" di Pengaturan
- Gunakan model AI yang lebih besar (llama3.2 bukan gemma:1b)
- Pastikan video memiliki konten pembicaraan yang jelas

### ❓ Error saat memotong video?
- Pastikan FFmpeg terinstall: `ffmpeg -version`
- Pastikan ada ruang disk yang cukup

### ❓ Ollama tidak berjalan?
- Jalankan manual: `ollama serve`
- Pastikan Ollama terinstall dengan benar
- Restart komputer jika perlu

---

## 💬 Dukungan

Hubungi seller untuk bantuan lebih lanjut.
