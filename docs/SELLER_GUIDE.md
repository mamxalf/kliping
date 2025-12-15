# Clipper CLI - Panduan Seller

Panduan untuk seller untuk mengelola license keys dan distribusi Clipper CLI.

---

## Overview

Sebagai seller, Anda bertanggung jawab untuk:
1. Generate license keys untuk customer
2. Distribusi executable ke customer
3. Support customer jika ada masalah

---

## File Penting (JANGAN DISTRIBUSI)

| File | Deskripsi | Distribusi? |
|------|-----------|-------------|
| `keygen.py` | Generator license key | **JANGAN** |
| `license.py` | Core license logic | Sudah include di .exe |
| `clipper.exe` | Aplikasi untuk customer | ✅ Ya |

> **PENTING:** File `keygen.py` TIDAK BOLEH diberikan ke customer. Simpan terpisah!

---

## Generate License Keys

### Setup (Sekali Saja)

1. Clone repository dari GitHub
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # atau
   poetry install
   ```

### Generate Single Key

```bash
python keygen.py generate --email customer@email.com
```

Output:
```
🔑 Generated License Key:

   CLIPPER-M8E9-7QJB-GX2Y-ACC8

   Identifier: customer@email.com
```

### Generate Batch Keys

Untuk generate banyak keys sekaligus:

```bash
python keygen.py batch --count 10 --output keys.txt
```

Output disimpan ke `keys.txt`:
```
CLIPPER-49FD-3ZAN-LM6L-7F32
CLIPPER-YYI0-S41I-FR1L-A0C5
CLIPPER-BF9U-3VYA-CW86-6BEE
...
```

### Validate Key

Untuk mengecek apakah key valid:

```bash
python keygen.py validate CLIPPER-XXXX-XXXX-XXXX-XXXX
```

---

## Distribusi ke Customer

### Apa yang Diberikan ke Customer

1. **File executable:** `clipper-vX.X.X-windows.exe`
2. **License key:** CLIPPER-XXXX-XXXX-XXXX-XXXX (unique per customer)
3. **User Guide:** Link ke `USER_GUIDE.md` atau PDF

### Cara Mengirim

1. Upload `.exe` ke cloud storage (Google Drive, Dropbox, dll)
2. Buat link download
3. Kirim ke customer beserta license key

### Template Pesan ke Customer

```
Halo [Nama Customer],

Terima kasih sudah membeli Clipper CLI!

📥 Download: [Link Download]
🔑 License Key: CLIPPER-XXXX-XXXX-XXXX-XXXX

Langkah instalasi:
1. Download dan extract file
2. Install FFmpeg (lihat panduan)
3. Jalankan clipper.exe
4. Masukkan license key di atas

Panduan lengkap: [Link User Guide]

Jika ada masalah, hubungi saya.

Salam,
[Nama Anda]
```

---

## Build Executable

### Otomatis via GitHub Actions

1. Buat tag baru:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. GitHub Actions akan otomatis build untuk:
   - Windows (.exe)
   - macOS (.zip)
   - Linux (.tar.gz)

3. Download dari **GitHub Releases** atau **Actions Artifacts**

### Manual Build

Untuk build manual di Windows:

```powershell
# Install dependencies
poetry install --with build

# Build
poetry run python build.py --onefile --clean
```

Output: `dist/clipper.exe`

---

## Tracking Customers

Disarankan untuk tracking:

| Customer | Email | License Key | Purchase Date | Status |
|----------|-------|-------------|---------------|--------|
| John Doe | john@email.com | CLIPPER-XXXX-... | 2024-01-15 | Active |

### Tips Tracking

1. Gunakan spreadsheet (Google Sheets/Excel)
2. Satu key = satu customer
3. Catat tanggal pembelian
4. Tandai jika ada issue

---

## Handling Support

### Common Issues & Solutions

| Issue | Solusi untuk Customer |
|-------|----------------------|
| FFmpeg not found | Arahkan ke bagian install FFmpeg di User Guide |
| Invalid license key | Cek apakah key benar, generate ulang jika perlu |
| Ollama not available | Arahkan install Ollama atau suruh pakai cloud provider |
| App crash | Minta screenshot error, report ke developer |

### Jika Customer Minta Key Baru

1. Validate alasan (misalnya: ganti komputer)
2. Bisa generate key baru jika perlu
3. Catat key lama sebagai "revoked" di tracking

---

## Pricing Strategy

### Saran Pricing

| Model | Harga (IDR) | Cocok Untuk |
|-------|-------------|-------------|
| Perpetual License | 250-500K | Lifetime access |
| Monthly Sub | 50-100K/bulan | Recurring revenue |
| Pay per video | 10-25K/video | Casual users |

### Bundling

Bisa bundle dengan:
- Tutorial video cara pakai
- Template prompt untuk viral content
- Support priority

---

## Security Notes

1. **JANGAN share source code** - Hanya distribute .exe
2. **JANGAN share keygen.py** - Keep private
3. **JANGAN share secret key** - Embedded di code
4. **Track all generated keys** - Untuk audit

---

## Contact Developer

Jika ada masalah teknis yang tidak bisa diselesaikan:
- Buka issue di GitHub repository
- Sertakan error message lengkap
- Sertakan langkah-langkah reproduce
