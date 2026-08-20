# Troubleshooting — zzluxora v7.0

Common issues and fixes.

---

## App Won't Start

### "DLL load failed" or missing DLLs
Reinstall PySide6:
```powershell
pip install --force-reinstall PySide6
```

### "ImportError: No module named PySide6"
Activate venv or install:
```powershell
..\.venv\Scripts\pip.exe install -r requirements.txt
```

### "Qt platform plugin could not be initialized"
```powershell
set QT_DEBUG_PLUGINS=1
python main.py
```
Look for missing `qwindows.dll` etc. Reinstall PySide6 fixes 99% of cases.

### App opens then immediately closes
Check stdout for traceback. Run from terminal:
```powershell
python main.py
```

### cp1252 encoding error on Windows console
Prints with emoji (`🎵`, `🔌`, etc.) fail because Windows console defaults to cp1252.

Fix in `main.py`:
```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
```

---

## Math Model Test Fails (RELEASE BLOCKER)

### `python tests/test_math_model.py` returns < 19/19

**DO NOT RELEASE.**

Identify which test fails (1-19) and which section:
1. 10k Reasons validation
2. V/A quadrant mapping
3. HSV → RGB conversion
4. RGB → RGBW extraction
5. Chase timing
6. Pattern selection

Common causes:
- Changed `compute_valence_arousal()` math
- Changed `va_to_hsv()` quadrant bounds
- Changed `hsv_to_rgb()` algorithm
- Changed chase frame rate formula

The math model is the academic core (skripsi BAB 3). **Never break it** — fix the engine to pass the test.

---

## Audio Analysis Fails

### "librosa.load() raised NoBackendError"
Install ffmpeg or use WAV files only (librosa falls back to scipy for WAV).

### "Audio analysis is very slow"
- librosa 0.11+ requires numpy 2.x. Check: `pip show numpy`
- For 3-min song, expect ~1-2s on modern CPU

### "Microsoft Visual C++ 14.0 required"
Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) or use prebuilt wheels.

### "V/A output looks wrong (all red/blue)"
Check `va_presets.py` — the active preset might be `energetic` or `calm`, not `default`. The skripsi math expects `worship` preset for "10,000 Reasons".

---

## Art-Net Doesn't Send

### Target IP unreachable
```powershell
ping <target_ip>
```

### Firewall blocking UDP 6454
```powershell
netsh advfirewall firewall add rule name="Art-Net" dir=in action=allow protocol=UDP localport=6454
netsh advfirewall firewall add rule name="Art-Net" dir=out action=allow protocol=UDP localport=6454
```

### No Art-Net node responding
- Verify node IP
- Check node is on same subnet
- Run as administrator if binding to broadcast (`255.255.255.255`)

### "stupidArtnet not installed"
```powershell
pip install stupidArtnet
```

### Frame counter stuck at 0
`ArtNetController.frames_sent` should increment on each `send_frame()`. If stuck:
- Check `is_running` (must be `True` after `connect()`)
- Verify `connect()` returns `{'ok': True}`
- Call `reset_counter()` in `_connect()` (already done — verify `main_window.py`)

### Live Mode doesn't update
`OutputTab` QTimer should fire at `1000/fps` ms. If stuck:
- Check `Live Mode` checkbox is checked
- Verify `_toggle_live()` started the timer
- Check `current_dmx` has values (not all zeros)

---

## Channel Preview Grid Not Showing

Output tab → Channel Preview Grid (8×64 = 512 cells) should show red brightness per channel.

If blank:
- Check `_refresh_status()` is running (1 s QTimer)
- Verify `current_dmx` is being set
- Check `ChannelPreviewGrid.set_values()` is called

---

## QSS / Styling Issues

### Gradient text not showing
`background-clip: text;` is required for gradient text in Qt QSS.

```css
QLabel#brandTitle {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
    -qt-background-clip: text;
    color: transparent;
}
```

### Custom QProperty not animating
Use `QPropertyAnimation` with `setPropertyValue` and a `QSS` selector for the dynamic state.

### Dark theme looks wrong
Verify `styles.DARK_QSS` is loaded in `main.py`:
```python
app.setStyleSheet(DARK_QSS)
```

---

## Bundle Folder is Big (onedir)

Normal for PyInstaller + PySide6 + librosa.

To reduce:
- We already use `--onedir`. To make a single .exe, add `--onefile` flag to pyinstaller (slower startup, no `_internal/` folder).
- Strip debug symbols: `--strip`
- Exclude unused modules in `zzluxora.spec`:
  ```python
  excludes=['tkinter', 'unittest', 'pydoc', 'doctest']
  ```

---

## Font Shows as Tofu (□ □ □)

`font_loader.py` should auto-load Windows system fonts. If still tofu:

1. Check `QApplication.setFont(QFont("Segoe UI", 10))` in `main.py`
2. Manually load font:
   ```python
   from PySide6.QtGui import QFontDatabase
   QFontDatabase.addApplicationFont("C:/Windows/Fonts/segoeui.ttf")
   ```

---

## Keyboard Shortcuts Not Working

Check that the panel is focused. Some shortcuts are panel-scoped.

For global shortcuts, see `main_window.py` for the `QShortcut` block.

`Esc` emergency stop fires globally (in `main_window.py`). `Space` is chase play/stop (only in Chase tab).

---

## Build Issues

### "RecursionError" during build
PyInstaller hitting Python recursion limit. Fix:
```python
# In zzluxora.spec:
import sys
sys.setrecursionlimit(5000)
```

### "Permission denied" on dist/zzluxora.exe
Close any running `zzluxora.exe` first.

### "PyInstaller not found"
```powershell
pip install pyinstaller
```

---

## Project File (.zlx) Won't Load

### "Unsupported schema version"
Your .zlx is from a newer version. Open in that version and re-save.

### "JSON parse error"
File corrupted. Check for manual edits, restore from backup.

### "Migration failed"
Old `.zlx` files need migration. `project_io.load_zlx()` handles it automatically — if it fails, the file may be from v2.x (too old, not supported).

---

## Performance

### UI lags during audio analysis
Expected — librosa is CPU-heavy. Analysis blocks main thread briefly. Spinner shows.

Future: move analysis to QThread (planned v7+).

### Art-Net frame drops at high FPS
Lower fps in Output tab (default 30). Try 20-25 for older nodes.

### Mixer tab slow on 512 faders
Qt repaint is heavy. Limit to 30 fps via QTimer. Lower fixture.fps if needed.

---

## Known Limitations (v7.0)

- **1 universe only** — 512 channels. Multi-universe planned for a later release.
- **No undo/redo** — fixture edits, scene edits, address patches.
- **No MIDI/OSC input** — Art-Net only.
- **No real-time audio** — analyze from WAV file only, no live mic.
- **English only** — no localization. Indonesian labels in some panels are read-only.

## Installed app (v7) — where is my data?

When installed to Program Files, the install dir is **read-only**. All user data
lives in **`%APPDATA%\zzluxora\`** (Roaming): `config.ini`, `fixtures/`,
`chases/`, `programs/`, `pages/`, `presets/`.

- **Settings/fixtures didn't carry over after reinstall?** You likely ticked
  "Clean install — remove existing settings & data" during setup, or chose to
  delete data at uninstall. Re-add fixtures via the Fixture Editor.
- **Want a full reset?** Uninstall and answer **Yes** to "delete settings & data",
  or delete `%APPDATA%\zzluxora\` manually.

---

## Getting Help

1. Check this file
2. Check [API.md](API.md) for module reference
3. Check [DEVELOPMENT.md](DEVELOPMENT.md) for debugging tips
4. Run math tests: `python tests/test_math_model.py`
5. Search the codebase: `grep -r "function_name" zzluxora/`
6. Check [markdowns/app_feedback.md](../markdowns/app_feedback.md) for known feedback gaps (Phase 9+ roadmap)

---

## See Also

- [BUILD.md](BUILD.md) — build issues
- [DEVELOPMENT.md](DEVELOPMENT.md) — debugging
- [CHANGELOG.md](CHANGELOG.md) — version history
