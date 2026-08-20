# Building zzluxora.exe (v7.0)

> For the full installer (setup.exe), see **`installer/BUILD_INSTALLER.md`**.
> This file covers the PyInstaller app build only.

---

## Quick Build

```powershell
cd C:\ANDREAS\SCRIPT\zzluxora2
python tools/make_ico.py   # once — generates assets/zzluxora.ico for the exe icon
python build.py
```

Output: `dist/zzluxora/` (onedir folder: `zzluxora.exe` + `_internal/` deps),
also copied to `../results/zzluxora-v7/`.

---

## What `build.py` Does

Runs PyInstaller with these flags:
- `--noconfirm` — overwrite previous build without prompt
- `--clean` — clear PyInstaller cache
- `--windowed` — no console window
- `--noconsole` — alias of `--windowed` (Windows-specific)
- `--name zzluxora` — output exe name
- `--add-data "fixtures;fixtures"` — bundle default fixtures
- `--add-data "assets;assets"` — bundle logo + icons
- `--add-data "tests;tests"` — bundle math tests (optional, for diagnostics)
- `--collect-submodules PySide6` — bundle all Qt6 modules
- `--collect-data PySide6` — bundle Qt6 data files
- `--hidden-import engines.audio_engine`
- `--hidden-import engines.analyze_pipeline`
- `--hidden-import engines.color_mapping`
- `--hidden-import engines.curve_lut`
- `--hidden-import engines.color_mixer`
- `--hidden-import engines.va_presets`
- `--hidden-import engines.scene_generator`
- `--hidden-import engines.program`
- `--hidden-import engines.chase`
- `--hidden-import engines.fixture_types`
- `--hidden-import engines.artnet_sender`
- `main.py` — entry point

---

## Pre-Build Checklist (RELEASE BLOCKER)

Before running `build.py`:

1. **Run math tests** — must be 19/19:
   ```powershell
   ..\.venv\Scripts\python.exe tests\test_math_model.py
   ```
2. **Smoke test** — `python main.py` from source, verify all 8 panels work
3. **Save+reload test** — open a `.zlx`, save it, reload it, verify state
4. **Art-Net roundtrip** — connect to a node (or `QLC+ Virtual Art-Net`), send a frame, verify it arrives

If all 4 pass, run `build.py`.

---

## Why a folder (--onedir)?

PyInstaller bundles Python + PySide6 + librosa + numpy + scipy + stupidArtnet into a folder.
The `zzluxora.exe` itself is ~19 MB; the `_internal/` subfolder holds Python runtime + all deps.

To reduce size:
- We already use `--onedir` (PyInstaller default). To make a single .exe, add `--onefile` (slower startup, no `_internal/` folder).
- Use UPX compression (already enabled in `zzluxora.spec`)
- Strip debug symbols with `--strip` (Windows only)
- Exclude unused modules in `zzluxora.spec`:
  ```python
  excludes=['tkinter', 'unittest', 'pydoc', 'doctest']
  ```

---

## Manual Build (without `build.py`)

If you want to customize flags:

```powershell
cd C:\Users\andre\OneDrive\Documents\SCRIPT\zzluxora
..\.venv\Scripts\pyinstaller.exe --windowed --name "zzluxora" --add-data "fixtures;fixtures" --add-data "assets;assets" --collect-submodules PySide6 --collect-data PySide6 main.py
```

---

## Distributing

The `dist/zzluxora.exe` is fully self-contained. No Python install required on target machine.

For internal use: just copy the .exe.

For external distribution: add a license file + readme + tests bundle (so the user can re-run math tests if needed).

---

## Build Output Locations

| Path | Contents |
| ---- | -------- |
| `dist/zzluxora.exe` | The release executable |
| `build/` | PyInstaller working directory (can be deleted) |
| `SCRIPT/results/zzluxora-v7/` | Auto-archive (build.py copies dist here after build) |
| `installer/Output/zzluxora-setup-v7.0.0.exe` | Final installer (after compiling `installer/zzluxora.iss`) |

---

## Troubleshooting Build

**"PyInstaller not found"**
```powershell
pip install pyinstaller
```

**"Permission denied" on output**
Close any running `zzluxora.exe` process first.

**"RecursionError" or import errors**
Add the missing module to `hiddenimports` in `zzluxora.spec`:
```python
hiddenimports += ['your_missing_module']
```

**"librosa not found" at runtime**
Add to spec:
```python
hiddenimports += ['librosa', 'soundfile']
```

**Build is slow (>5 min)**
Normal. PyInstaller analyzes all imports. Use `--onedir` for faster incremental builds.

**"DLL load failed" on target machine**
PyInstaller missed a Qt DLL. Run:
```powershell
--collect-submodules PySide6 --collect-data PySide6
```

---

## See Also

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — runtime issues
- [DEVELOPMENT.md](DEVELOPMENT.md) — dev workflow
- [CHANGELOG.md](CHANGELOG.md) — version history
