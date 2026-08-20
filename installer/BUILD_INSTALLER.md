# Build zzluxora v7 Installer

Langkah bikin installer Windows (.exe) untuk zzluxora.

## Prasyarat (sekali saja)
- Python + venv project (`C:\ANDREAS\SCRIPT\.venv`)
- **Pillow** untuk generate icon: `pip install pillow`
- **Inno Setup 6** (gratis): https://jrsoftware.org/isdl.php — sediakan `ISCC.exe`

## Langkah build

```powershell
cd C:\ANDREAS\SCRIPT\zzluxora2

# 1. Generate icon .ico dari logo (sekali, atau saat logo berubah)
python tools/make_ico.py
#   → assets/zzluxora.ico

# 2. Build app jadi folder onedir (PyInstaller)
python build.py
#   → dist/zzluxora/  (berisi zzluxora.exe + _internal + fixtures)
#   (juga disalin ke ../results/zzluxora-v7/)

# 3. Compile installer (Inno Setup)
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\zzluxora.iss
#   → installer/Output/zzluxora-setup-v7.0.0.exe
```

Kalau `ISCC.exe` tak di PATH, buka `installer/zzluxora.iss` lewat **Inno Setup Compiler** (GUI) lalu klik **Build → Compile**.

## Perilaku installer

**Saat install:**
- Terinstal ke `C:\Program Files\zzluxora` (64-bit) / `Program Files (x86)` (32-bit) — otomatis.
- Folder app **dihapus dulu** sebelum copy → selalu fresh, tidak ketumpuk (`[InstallDelete]`).
- Masuk **Add/Remove Programs** Windows.
- Shortcut Start Menu (+ Desktop kalau dicentang).
- Checkbox **"Clean install — remove existing settings & data in AppData"**:
  - Tidak dicentang (default) → data lama di `%APPDATA%\zzluxora` dipertahankan.
  - Dicentang → `%APPDATA%\zzluxora` dihapus dulu (clean install penuh).

**Saat uninstall:**
- Folder app di Program Files dibersihkan total.
- Muncul prompt: **"Also delete your settings and data?"**
  - **No** → data `%APPDATA%\zzluxora` tetap (untuk reinstall nanti).
  - **Yes** → data ikut dihapus.

## Lokasi data user

Semua data (writable) ada di **`%APPDATA%\zzluxora\`** (Roaming):
- `config.ini` — pengaturan
- `fixtures/` — fixture user (seed dari bundle saat pertama run)
- `chases/`, `programs/`, `pages/`, `presets/` — data show

Install dir (Program Files) **read-only** — app tidak menulis ke sana. Inilah kenapa data dipisah ke AppData (kalau tidak, app gagal di Program Files).

## Testing cepat (tanpa installer)
Untuk cek data-path fix sebelum bikin installer:
```powershell
python build.py
.\dist\zzluxora\zzluxora.exe
```
Lalu pastikan `%APPDATA%\zzluxora\config.ini` + `fixtures\` tercipta (BUKAN di dalam `dist\zzluxora\`).
