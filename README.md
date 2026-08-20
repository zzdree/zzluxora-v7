# 🎛️ ZZLUXORA v7.0.0: Audio-Reactive Lighting Controller

> **Native PySide6 (Qt6) + Art-Net DMX512 Stage Lighting Control with Audio-Reactive Scene Generation.**  
> Edisi rilis baseline skripsi dengan tema visual *Emerald Green Accent* (#2ecc71) dan integrasi Windows Installer.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-41CD52?style=flat-square&logo=qt&logoColor=white)
![Protocol](https://img.shields.io/badge/Protocol-Art--Net%20DMX512-orange?style=flat-square)
![Audio](https://img.shields.io/badge/Audio-Librosa%20%2B%20NumPy-blue?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows_10%2F11-0078D6?style=flat-square&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📖 Deskripsi Proyek

**ZZLUXORA v7.0.0** adalah sistem kontrol pencahayaan panggung cerdas berbasis desktop Windows. Aplikasi ini mampu menganalisis file audio musik secara komputasional (*Music Information Retrieval / MIR*) dan mengonversinya secara otomatis menjadi sinyal kontrol visual lampu panggung (*Moving Head Beam, PAR LED RGBW, Strobe*) melalui protokol jaringan **Art-Net UDP (Port 6454)**.

---

## ✨ Fitur Utama Versi 7.0.0

- 🎧 **Real-Time Audio Analysis:** Ekstraksi fitur akustik musik meliputi RMS Energy, Tempo (BPM), Onset Detection, MFCC, dan Spectral Centroid menggunakan **Librosa**.
- 🧠 **Mood Classification:** Pemetaan nuansa emosi musik ke dalam koordinat afektif 2D **Valence-Arousal (Russell Circumplex Model)**.
- 🎨 **HSV-RGBW Color Engine:** Algoritma konversi ruang warna dari Hue-Saturation-Value ke 4 kanal warna fisik (*Red, Green, Blue, White*) untuk lampu PAR LED.
- 🎚️ **DMX512 Channel Mixer:** Fader mixer kontrol kanal 0-255 lengkap dengan master intensity blackout safety.
- 📟 **Fixture Manager & Auto-Patch:** Pengaturan profil fixture (Moving Head 16ch, PAR LED 8ch/4ch) dengan dialog auto-patch alamat DMX.
- 🖥️ **2D Stage Canvas:** Pratinjau visual posisi lampu di atas panggung secara interaktif.
- 📦 **Windows Inno Setup Installer:** Skrip pembuatan installer .exe mandiri untuk Program Files dengan konfigurasi AppData.

---

## 📁 Struktur Arsitektur Modul

`	ext
zzluxora_v7/
├── main.py                  <- Titik masuk aplikasi (Entry point PySide6)
├── main_window.py           <- Jendela utama dengan sistem navigasi sidebar & multi-panel
├── config.py / config.ini   <- Pengaturan default, universe Art-Net, & konfigurasi jaringan
├── fixture_manager.py       <- Pengelola database lampu panggung & DMX patch map
├── styles.py                <- Desain tema antarmuka Emerald Green (#2ecc71) & QSS
│
├── engines/                 <- Core computational engines:
│   ├── artnet_engine.py     <- Art-Net UDP packet builder & socket sender
│   ├── audio_engine.py      <- Ekstraksi fitur Librosa & deteksi tempo
│   ├── color_mapping.py     <- Konversi ruang warna HSV ke RGBW
│   ├── mood_engine.py       <- Model Valence-Arousal mood classifier
│   ├── scene_generator.py   <- Pembangkit sequence & cue lighting otomatis
│   └── scene_player.py      <- Playback loop & sinkronisasi frame rate
│
├── panels/                  <- Panel antarmuka pengguna:
│   ├── audio_panel.py       <- Visualizer spektrum & parameter audio
│   ├── dmx_mixer_panel.py   <- Fader kontrol kanal DMX512
│   ├── fixtures_panel.py    <- Patching & manajemen fixture lampu
│   ├── live_mode_panel.py   <- Eksekusi langsung live stage performance
│   ├── mood_panel.py        <- Visualisasi koordinat Valence-Arousal
│   ├── stage_panel.py       <- Canvas 2D pratinjau panggung
│   └── settings_panel.py    <- Konfigurasi IP Broadcast & interface jaringan
│
├── fixtures/                <- Definisi profil kanal lampu (.json)
├── installer/               <- Skrip Inno Setup compiler (zzluxora.iss)
└── tests/                   <- Unit test matematika model & logika engine
`

---

## ⚙️ Panduan Instalasi & Menjalankan

1. **Clone Repositori:**
   `ash
   git clone https://github.com/zzdree/zzluxora-v7.git
   cd zzluxora-v7
   `

2. **Install Dependensi:**
   `ash
   pip install -r requirements.txt
   `

3. **Jalankan Aplikasi:**
   `ash
   python main.py
   `

---

## 📜 Lisensi

Proyek ini dilisensikan di bawah lisensi **MIT License**.  
Hak Cipta (c) 2026 **Andreas Restuawanta Christwara (@zzdree)** - Universitas Negeri Semarang.
