# 🔐 Clipper CLI - Panduan Seller/Admin

Panduan untuk seller/admin dalam mengelola lisensi dan distribusi Clipper CLI.

---

## 📋 Daftar Isi

1. [Generate Serial Key](#generate-serial-key)
2. [Memahami Sistem Lisensi](#memahami-sistem-lisensi)
3. [Distribusi ke User](#distribusi-ke-user)
4. [Kustomisasi](#kustomisasi)
5. [Build Executable](#build-executable)
6. [FAQ Seller](#faq-seller)

---

## Generate Serial Key

### Command Line

```bash
cd clipper-cli
poetry run python generate_keys.py <email_user>
```

### Contoh

```bash
# Generate 1 key
poetry run python generate_keys.py john@example.com

# Generate multiple keys
poetry run python generate_keys.py user1@mail.com user2@mail.com user3@mail.com
```

### Output

```
🔑 Generated Serial Keys:
--------------------------------------------------
  john@example.com: VKFP-HN68-4Z2L-R4DX
  user1@mail.com: KCLS-3CSG-S2EB-J6YK
  user2@mail.com: E2DV-ZHDJ-C7CB-5FDN
--------------------------------------------------

Total: 3 keys generated
```

### Dari Python Code

```python
from clipper_cli.license import generate_serial_key

# Generate key untuk user
key = generate_serial_key("user@email.com")
print(key)  # XXXX-XXXX-XXXX-XXXX
```

---

## Memahami Sistem Lisensi

### Cara Kerja

1. **Serial Key Generation**
   - Key di-generate dari `user_id` + `SECRET_SALT`
   - Menggunakan SHA-256 hashing
   - Format: `XXXX-XXXX-XXXX-XXXX`

2. **Aktivasi**
   - User memasukkan serial key
   - Key disimpan di `~/.clipper/license.json`
   - Machine ID di-record untuk binding

3. **Machine Binding**
   - License terikat ke 1 komputer
   - Machine ID = hash dari (hostname + architecture + MAC address)
   - Key tidak bisa dipindah ke komputer lain

### File License

Lokasi: `~/.clipper/license.json`

```json
{
  "serial_key": "VKFP-HN68-4Z2L-R4DX",
  "activated_at": "2024-01-15T10:30:00",
  "machine_id": "a1b2c3d4e5f6g7h8"
}
```

### Keamanan

| Aspek | Implementasi |
|-------|--------------|
| Key Format | XXXX-XXXX-XXXX-XXXX |
| Hashing | SHA-256 + Secret Salt |
| Storage | Local JSON file |
| Binding | Machine-bound |

---

## Distribusi ke User

### Yang Diberikan ke User

1. **Executable file** (`clipper.exe` / `clipper`)
2. **Serial Key** yang sudah di-generate
3. **Link download FFmpeg** (jika belum punya)
4. **Panduan User** (`GUIDE_USER.md`)

### Template Pesan ke User

```
🎬 Selamat! Anda telah membeli Clipper CLI.

📦 File yang disertakan:
- clipper.exe (Windows) / clipper (Mac/Linux)
- GUIDE_USER.md (Panduan penggunaan)

🔑 Serial Key Anda:
XXXX-XXXX-XXXX-XXXX

📋 Langkah instalasi:
1. Install FFmpeg: https://ffmpeg.org/download.html
2. Jalankan clipper.exe
3. Masukkan serial key saat diminta
4. Selesai!

❓ Bantuan: [contact info]
```

---

## Kustomisasi

### Mengganti Secret Salt (WAJIB untuk Production!)

Edit file `clipper_cli/license.py`:

```python
# Ganti ini dengan string random yang panjang
SECRET_SALT = "YOUR_UNIQUE_SECRET_SALT_HERE_MAKE_IT_LONG_AND_RANDOM"
```

> ⚠️ **PENTING:** Setelah mengganti salt, semua key lama menjadi invalid. Generate key baru untuk semua user.

### Mengganti Branding

Edit file `clipper_cli/main.py`:

```python
def display_banner():
    banner = """
    [Logo dan nama produk Anda]
    """
    console.print(banner, style="cyan")
```

---

## Build Executable

### Prerequisites

```bash
cd clipper-cli
poetry add pyinstaller --group dev
```

### Build Command

```bash
# Windows
poetry run pyinstaller build.spec

# Mac/Linux
poetry run pyinstaller build.spec
```

### Output

Executable di: `dist/clipper.exe` (Windows) atau `dist/clipper` (Mac/Linux)

### Build untuk Platform Lain

- Build Windows: Jalankan di Windows
- Build Mac: Jalankan di Mac
- Build Linux: Jalankan di Linux

> ⚠️ PyInstaller membuat executable untuk OS yang sama dengan tempat build.

---

## FAQ Seller

### ❓ Bagaimana jika user kehilangan key?
- Generate ulang dengan email yang sama
- Key akan identik karena menggunakan hash yang sama

### ❓ Bisakah 1 key untuk banyak komputer?
- Tidak, key machine-bound
- Jika user ganti komputer, perlu key baru dengan email/ID berbeda

### ❓ Bagaimana mencegah sharing key?
- Machine binding sudah mencegah ini
- Key hanya bisa diaktivasi di 1 komputer

### ❓ User minta reset license?
User bisa hapus manual:
```bash
# Windows
del %USERPROFILE%\.clipper\license.json

# Mac/Linux
rm ~/.clipper/license.json
```

### ❓ Bagaimana track siapa yang sudah beli?
- Simpan mapping email → serial key di database/spreadsheet Anda
- User ID (email) yang digunakan untuk generate key adalah identifier

---

## 📊 Tracking & Analytics

Untuk tracking lebih advanced, Anda bisa:

1. **Database online** untuk validasi key
2. **Expiry date** pada lisensi
3. **Usage analytics**

Hubungi developer untuk implementasi fitur tambahan.
