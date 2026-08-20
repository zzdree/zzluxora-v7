# Development Workflow — zzluxora v7.0

---

## Dev Loop

```powershell
cd C:\Users\andre\OneDrive\Documents\SCRIPT\zzluxora
..\.venv\Scripts\python.exe main.py
```

Edit a `.py` file → save → close app → re-run `main.py`. No hot reload.

For Qt changes (`styles.py`, `main_window.py`), close + re-run is enough.
For engine changes (`engines/*.py`), same.
For panel changes, same.
For widget changes, same.

---

## Folder Conventions

- **`panels/`** — 16 QWidget subclasses. Self-contained, no cross-panel imports.
- **`widgets/`** — 14 reusable UX components. No business logic.
- **`engines/`** — 12 pure-Python modules, **no Qt imports**. Testable in isolation.
- **`fixtures/`** — JSON fixture definitions (user library). Loaded at startup, editable via UI.
- **`styles.py`** — Single QSS string. Dark theme (`DARK_QSS`).
- **`tests/`** — Math model regression (`test_math_model.py` 19/19 tests, **RELEASE BLOCKER**).
- **`assets/`** — Logo + icons (PNG, ICO).

---

## Math Model Test (RELEASE BLOCKER)

Before any release or commit, run:

```powershell
cd C:\Users\andre\OneDrive\Documents\SCRIPT\zzluxora
..\.venv\Scripts\python.exe tests\test_math_model.py
```

Expected: **19/19 tests pass** across 6 sections:
1. 10k Reasons validation (audio → RGBW)
2. V/A quadrant mapping
3. HSV → RGB conversion
4. RGB → RGBW extraction
5. Chase timing
6. Pattern selection

If any test fails, **DO NOT RELEASE**. Fix the engine module + add a regression test.

The math model is derived from skripsi BAB 3 — it's the academic core of the project. Never break it.

---

## Adding a New Audio Feature

1. Edit `engines/audio_engine.py`
2. Add field to `extract_features()` return dict
3. Update `compute_valence_arousal()` if needed
4. Update `full_pipeline()` return
5. (If UI) update `panels/audio_tab.py` to display new field
6. Add a math test in `tests/test_math_model.py` if it's a math-affecting field

---

## Adding a New Engine

1. Create `engines/my_engine.py` with **no Qt imports** (use only stdlib + numpy + scipy)
2. Add pure-Python functions / classes
3. Wire into `fixture_manager` if it needs state
4. If UI needed, create a panel + widget pair
5. Document in [API.md](API.md)
6. Add a test in `tests/test_math_model.py` if it's math-affecting

---

## Adding a New Panel

1. Create `panels/my_panel.py` with class `MyPanel(QWidget)`
2. Register import in `panels/__init__.py` (optional)
3. Add to `main_window.py`:
   - Import: `from panels.my_panel import MyPanel`
   - Add to stacked widget: `self.stacked.addWidget(MyPanel(manager))`
   - Add to sidebar entries in `sidebar.py`: `SIDEBAR_ITEMS` (icon path + label)
4. Update help modal: `widgets/help_modal.py` (add description)
5. Update onboarding: `widgets/onboarding.py` (add step)
6. Update [README.md](README.md) feature table

---

## Adding a New Widget

1. Create `widgets/my_widget.py` with class `MyWidget(QWidget)`
2. No business logic — only paint + mouse events
3. Wrap state via signals if needed
4. Use `DARK_QSS` from `styles.py` for theme consistency
5. Document usage in [API.md](API.md) if reusable

---

## Adding a New Keyboard Shortcut

In `main_window.py`, find the `QShortcut` block:

```python
QShortcut(QKeySequence("Ctrl+X"), self, activated=self.my_handler)
```

Add `my_handler` method to `MainWindow` class.

Update [README.md shortcuts table](README.md#keyboard-shortcuts) + [help_modal.py](widgets/help_modal.py).

---

## Adding a New Fixture Type Template

1. Edit `engines/fixture_types.py`
2. Add entry to `FIXTURE_TYPES` dict:
   ```python
   "My Fixture 6ch": ["Dimmer", "R", "G", "B", "W", "Strobe"],
   ```
3. Restart app — template appears in Fixture Editor type combo
4. Channels auto-populate when user picks template
5. Document in [API.md](API.md) `FIXTURE_TYPES` table

---

## .zlx Project File Format

JSON schema. Backward compatible with v3.0+ (loaders migrate).

```json
{
  "version": "3.0",
  "project_name": "MyShow.zlx",
  "fixtures": [...],
  "address_map": {...},
  "songs": {...},
  "artnet": {"target_ip": "127.0.0.1", "universe": 0, "fps": 30},
  "programs": [...],
  "chases": [...],
  "created_at": "...",
  "updated_at": "..."
}
```

When adding a new field:
- Bump version to "6.1" or "7.0" if breaking
- Add migration code in `panels/project_io.py::load_zlx()`
- Document in [API.md](API.md)
- Bump `DEFAULT_VERSION` in `project_io.py`

---

## Testing

### Automated
- `tests/test_math_model.py` — 19/19 tests, math model regression. **RELEASE BLOCKER.**

### Manual
1. Run `python main.py`
2. Click through each panel (Program → 8 sub-tabs, Fixtures → Editor + List, Color → Mixer, Settings, About)
3. Try the workflow (define fixture → patch → analyze → connect → chase)
4. Save + reload a project
5. Build .exe + run on clean machine
6. Verify all 8 keyboard shortcuts work (Ctrl+1..5, Ctrl+O, Ctrl+S, Ctrl+Shift+S, Space, B, Esc, F1)
7. Test Art-Net connection with real node or `QLC+ Virtual Art-Net`

---

## Debugging

**Qt prints to stdout but no GUI appears**
- Check if running in headless environment
- Set `QT_QPA_PLATFORM=offscreen` for headless testing

**Audio analysis hangs**
- Add print statements in `engines/audio_engine.py::extract_features()`
- Check librosa version: `pip show librosa`

**Art-Net doesn't send**
- Check firewall (UDP 6454 must be open)
- Verify target IP reachable: `ping <target_ip>`
- Run with `--log-level DEBUG` (PyInstaller)

**Font shows as tofu (□)**
- `font_loader.py` should auto-load Windows system fonts
- If still tofu, check `QApplication.setFont(QFont("Segoe UI", 10))` in `main.py`

**cp1252 encoding error on Windows console**
- `print("emoji 🎵")` fails with cp1252
- Fix in `main.py`:
  ```python
  import sys
  sys.stdout.reconfigure(encoding='utf-8')
  ```

**Math model test fails after engine change**
- DO NOT skip the test
- Check which test fails (1-19) and which section
- Fix the engine to pass the test
- The math model is the academic core — never break it

**Art-Net frame counter not resetting**
- Call `artnet_controller.reset_counter()` in `_connect()` (already done)
- Check `frames_sent` via `artnet_controller.get_status()`

---

## Code Style

- Python 3.13 type hints preferred
- PEP 8 (4-space indent, snake_case, max line 100)
- Docstrings for all public functions
- No global imports inside functions
- Engines: pure Python, no Qt, no side effects (use pure functions)
- Panels: accept `manager` in `__init__`, no direct state outside manager
- Widgets: signals for events, no direct manager access

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) — module structure
- [API.md](API.md) — module reference
- [BUILD.md](BUILD.md) — how to build .exe
- [markdowns/app_feedback.md](../markdowns/app_feedback.md) — feedback audit (Phase 9+ roadmap)
