# 🎛️ zzluxora v7.0.0

> **Native PySide6 (Qt6) + Art-Net DMX512 Lighting Control with Audio-Reactive Scene Generation.**  
> An audio engineer's lighting desk at 3 AM — grandMA3 ergonomics meets QLC+ agility. Edisi rilis baseline skripsi dengan tema visual *Emerald Green Accent* (`#2ecc71`) dan integrasi Windows Inno Setup Installer.

---

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-41CD52?style=flat-square&logo=qt&logoColor=white)
![Protocol](https://img.shields.io/badge/Protocol-Art--Net_4_DMX512_(UDP_6454)-orange?style=flat-square)
![Audio](https://img.shields.io/badge/Audio-Librosa_%2B_NumPy_%2B_SciPy-blue?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows_10%2F11-0078D6?style=flat-square&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📑 Daftar Isi
1. [Gambaran Umum Proyek](#-1-gambaran-umum-proyek)
2. [Fitur Unggulan v7.0.0](#-2-fitur-unggulan-v700)
3. [Arsitektur Sistem & Modul Core](#-3-arsitektur-sistem--modul-core)
4. [Katalog Direktori](#-4-katalog-direktori)
5. [Panduan Instalasi & Menjalankan](#-5-panduan-instalasi--menjalankan)
6. [Kompilasi Standalone .EXE & Installer](#-6-kompilasi-standalone-exe--installer)
7. [Pengujian Matematis Model (Unit Tests)](#-7-pengujian-matematis-model-unit-tests)
8. [Lisensi & Hak Cipta](#-8-lisensi--hak-cipta)

---

## 📖 1. Gambaran Umum Proyek

**zzluxora v7.0.0** adalah perangkat lunak desktop native Windows untuk pengendalian pencahayaan panggung cerdas (*intelligent stage lighting controller*). Aplikasi ini dirancang tanpa *webview* maupun Electron, menggunakan murni **PySide6 / Qt6 C++ bindings** untuk mencapai performa rendering 60 FPS yang ringan dan deterministik.

Sistem bekerja dengan mengekstrak parameter akustikal musik secara komputasional (*Music Information Retrieval / MIR*), memetakannya ke ruang afektif emosi **Valence-Arousal (Russell Circumplex Model)**, mengonversi koordinat emosi ke ruang warna fisik **HSV ➔ RGB ➔ Physical 4-Channel RGBW**, dan mentransmisikan paket frame DMX512 secara *real-time* melalui protokol jaringan **Art-Net UDP (Port 6454)**.

---

## ✨ 2. Fitur Unggulan v7.0.0

- 🎧 **8-Stage Audio Analysis Pipeline:** Ekstraksi fitur akustik menyeluruh via **Librosa** (RMS Energy / Loudness, Tempo / BPM, Onset Strength, Spectral Centroid, Chroma STFT Mayor vs Minor, dan 13 Koefisien MFCC).
- 🧠 **Russell Circumplex Mood Visualizer:** Plot visual interaktif koordinat 2D *Valence-Arousal* yang memperlihatkan spektrum suasana lagu rohani (*Praise vs Worship*).
- 🎨 **Physical RGBW Color Mapping Engine:** Algoritma konversi warna *cross-modal* yang memaksimalkan emisi kanal *White* fisik lampu PAR LED panggung tanpa distorsi warna.
- 🎚️ **Precision DMX512 Channel Mixer:** Fader mixer kontrol kanal 0–255 dengan indikator numerik presisi dan *Master Dimmer Blackout Safety*.
- 💡 **Fixture Manager & Auto-Patch:** Pengaturan profil fixture lampu (Moving Head Beam 16-Channel, PAR LED RGBW 8/4-Channel) dengan dialog cerdas auto-patching DMX.
- 🔘 **Live Performance Page Pad (`PageTab`):** Grid tombol kustom untuk memicu (*trigger*) adegan pencahayaan (*Scenes*) dan sekuens ritmis (*Chases*) secara instan saat *live show*.
- 🖥️ **Interactive 2D Stage Canvas:** Pratinjau visual posisi lampu di atas panggung dengan simulasi sorot berkas cahaya dan *pan/tilt*.
- 📦 **Windows Inno Setup Installer:** Skrip installer wizard profesional (`installer/zzluxora.iss`) yang mendukung instalasi bersih ke Program Files dan manajemen AppData.

---

## 🏗️ 3. Arsitektur Sistem & Modul Core

Aplikasi dibangun dengan arsitektur 3 lapis (*Three-Layer Architecture*): **Core State**, **UI Panels**, dan **Computational Engines**:

```text
+-----------------------------------------------------------------------------------------+
|                                ARSITEKTUR ZZLUXORA v7.0                                 |
+-----------------------------------------------------------------------------------------+
  [1] USER INTERFACE (PySide6 / Qt6):
      • HeaderBar       : Brand Title, Project Status, Art-Net Pill Indicator, Start/Stop
      • Collapsible Sidebar : Navigasi ikonik panel dengan toggle state
      • ProgramPanel    : Container tab multi-fungsi (Address, Audio, Scenes, Chase, Mixer, Page)
      • SettingsPanel   : Konfigurasi broadcast IP, port, interface jaringan, dan universe
          │
          ▼
  [2] COMPUTATIONAL ENGINES (Python / NumPy / SciPy / Librosa):
      • audio_engine.py      : Ekstraksi fitur akustik & segmentasi beat
      • mood_engine.py       : Pemodelan afektif koordinat Valence-Arousal
      • color_mapping.py     : Transformasi ruang warna HSV ke RGBW
      • scene_generator.py   : Pembangkit sekuens & palet warna dinamis
      • scene_player.py      : Playback loop sinkron 40 FPS
          │
          ▼
  [3] NETWORK PROTOCOL LAYER:
      • artnet_sender.py     : Penyusun paket biner ArtDmx UDP (OpCode 0x5000)
      • Target Receiver      : Node Mikrokontroler ESP32 DevKit V1 + MAX485 DMX512
+-----------------------------------------------------------------------------------------+
```

---

## 📁 4. Katalog Direktori

```text
zzluxora_v7/
├── main.py                  <- Titik masuk aplikasi (Entry Point PySide6)
├── main_window.py           <- Jendela utama dengan sistem navigasi sidebar & multi-panel
├── config.py / config.ini   <- Pengaturan default, universe Art-Net, & konfigurasi jaringan
├── fixture_manager.py       <- Pengelola database lampu panggung & DMX patch map
├── styles.py                <- Desain tema antarmuka Emerald Green (#2ecc71) & QSS tokens
├── font_loader.py           <- Pemuat tipografi Windows native
├── icons.py                 <- Koleksi ikon vektor UI
├── requirements.txt         <- Daftar pustaka dependensi Python
├── zzluxora.spec            <- Konfigurasi PyInstaller Onedir Build
│
├── 📂 engines/              <- Core computational engines:
│   ├── analyze_pipeline.py  <- 8-stage pipeline orchestrator
│   ├── artnet_sender.py     <- Art-Net UDP socket packet broadcaster
│   ├── audio_engine.py      <- Ekstraksi fitur Librosa & deteksi tempo
│   ├── chase.py             <- Logika chase sequence ritmis
│   ├── color_mapping.py     <- Konversi ruang warna HSV ke RGBW
│   ├── color_mixer.py       <- Utilitas pencampur warna & Curve LUT
│   ├── fixture_types.py     <- Definisi profil kanal DMX
│   ├── mood_engine.py       <- Model Valence-Arousal mood classifier
│   ├── scene_generator.py   <- Pembangkit scene pencahayaan otomatis
│   └── va_presets.py        <- Preset koordinat afektif emosi musik
│
├── 📂 panels/               <- Panel antarmuka pengguna:
│   ├── address_tab.py       <- Manajemen alamat patch DMX
│   ├── audio_tab.py         <- Visualizer spektrum & parameter audio
│   ├── chase_tab.py         <- Pengaturan sekuens chase lampu
│   ├── color_mixer_tab.py   <- Pemilih palet warna manual
│   ├── fixture_editor_panel.py <- Editor profil lampu DMX
│   ├── fixture_list_panel.py   <- Daftar lampu yang terpasang
│   ├── mixer_tab.py         <- Fader kontrol kanal DMX512
│   ├── output_tab.py        <- Monitor data kanal live
│   ├── page_tab.py          <- Button pad pemicu adegan live show
│   ├── preview_tab.py       <- Pratinjau panggung visual 2D
│   ├── program_panel.py     <- Tab host utama
│   ├── settings_panel.py    <- Konfigurasi jaringan & Art-Net
│   └── about_panel.py       <- Informasi lisensi & metadata akademik
│
├── 📂 widgets/              <- Komponen UI kustom (ArtNet pill, Curve editor, Toast, dll)
├── 📂 fixtures/             <- Profil lampu Generic PAR RGBW 8ch (.json)
├── 📂 assets/               <- Ikon aplikasi, logo vektor, dan file .ico
├── 📂 installer/            <- Skrip Inno Setup Compiler (zzluxora.iss)
└── 📂 tests/                <- Unit tests verifikasi model matematika
```

---

## 🚀 5. Panduan Instalasi & Menjalankan

### Persyaratan Sistem:
- **Sistem Operasi:** Windows 10 / 11 (64-bit)
- **Python:** Versi 3.10 atau lebih baru

### Langkah Menjalankan:
1. **Clone Repositori:**
   ```powershell
   git clone https://github.com/zzdree/zzluxora-v7.git
   cd zzluxora-v7
   ```

2. **Install Dependensi:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Jalankan Aplikasi:**
   ```powershell
   python main.py
   ```

---

## 🛠️ 6. Kompilasi Standalone .EXE & Installer

### 1. Build Portable Executable (PyInstaller):
```powershell
python build.py
```
Hasil build akan tersimpan di direktori `dist/zzluxora/` (`zzluxora.exe` + folder `_internal/`).

### 2. Build Windows Setup Wizard (Inno Setup):
Buka berkas `installer/zzluxora.iss` menggunakan **Inno Setup Compiler**, lalu klik **Compile (Ctrl + F9)**. Installer mandiri `zzluxora-setup-v7.0.0.exe` akan dihasilkan secara otomatis.

---

## 🧪 7. Pengujian Matematis Model (Unit Tests)

Proyek ini dilengkapi dengan modul pengujian unit untuk memvalidasi akurasi formula matematika konversi ruang warna dan ekstraksi parameter audio:

```powershell
pytest tests/ -v
```

---

## 📜 8. Lisensi & Hak Cipta

Proyek ini dilisensikan di bawah **MIT License**.  
Hak Cipta (c) 2026 **Andreas Restuawanta Christwara ([@zzdree](https://github.com/zzdree))** — Universitas Negeri Semarang.
