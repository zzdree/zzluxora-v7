# Architecture — zzluxora v7.0

Native PySide6 desktop app, no webview, no Electron. Three-layer architecture: **core** (state), **UI** (panels), **engines** (audio/color/scene/chase/Art-Net). 12 engines · 16 panels · 14 widgets.

---

## Module Graph

```
┌──────────────────────────────────────────────────────────────┐
│ main.py (entry)                                              │
│   └─ MainWindow ───┬─ HeaderBar (brand + project + Art-Net)  │
│                    │    ├─ BrandTitle (painted gradient)     │
│                    │    ├─ project_label                     │
│                    │    ├─ ArtNetStatusPill                  │
│                    │    └─ Start / Stop                      │
│                    ├─ Sidebar (collapsible, ☰ toggle)        │
│                    ├─ Stacked panels                         │
│                    │    ├─ panels/program_panel.py           │
│                    │    │    ├─ AddressTab                   │
│                    │    │    ├─ AudioTab (Analyze)           │
│                    │    │    ├─ ScenesTab                    │
│                    │    │    ├─ ChaseTab                     │
│                    │    │    ├─ MixerTab                     │
│                    │    │    ├─ PreviewTab                   │
│                    │    │    ├─ OutputTab                    │
│                    │    │    └─ ProgramsTab                  │
│                    │    ├─ panels/fixture_list_panel.py      │
│                    │    ├─ panels/fixture_editor_panel.py    │
│                    │    ├─ panels/color_mixer_tab.py         │
│                    │    ├─ panels/settings_panel.py          │
│                    │    ├─ panels/about_panel.py             │
│                    │    └─ panels/project_io.py              │
│                    ├─ widgets/onboarding.py                  │
│                    ├─ widgets/help_modal.py                  │
│                    ├─ widgets/toast.py                       │
│                    └─ widgets/splash_screen.py               │
│                                                              │
│ FixtureManager (global state singleton)                      │
│   ├─ fixtures: list[Fixture]                                 │
│   ├─ address_map: dict[(univ, ch) → FixtureIndex]            │
│   ├─ songs: dict[song_id → AudioFeatures]                    │
│   ├─ artnet_controller: ArtNetController                     │
│   ├─ programs: list[Program]                                 │
│   ├─ chases: list[Chase]                                     │
│   └─ project_name: str                                       │
│                                                              │
│ Engines (pure logic, no Qt) — 12 modules                     │
│   ├─ engines/audio_engine.py                                 │
│   ├─ engines/analyze_pipeline.py        ← skripsi math       │
│   ├─ engines/color_mapping.py                                │
│   ├─ engines/curve_lut.py                                    │
│   ├─ engines/color_mixer.py                                  │
│   ├─ engines/va_presets.py                                   │
│   ├─ engines/scene_generator.py                              │
│   ├─ engines/program.py                                      │
│   ├─ engines/chase.py                                        │
│   ├─ engines/fixture_types.py       ← 10 templates          │
│   ├─ engines/artnet_sender.py         ← ArtNetController     │
│   └─ engines/__init__.py                                     │
│                                                              │
│ Widgets (reusable UX) — 14 modules                           │
│   ├─ widgets/splash_screen.py                                │
│   ├─ widgets/onboarding.py                                   │
│   ├─ widgets/help_modal.py                                   │
│   ├─ widgets/header_bar.py                                   │
│   ├─ widgets/artnet_pill.py                                  │
│   ├─ widgets/toast.py                                        │
│   ├─ widgets/address_grid.py        ← 8×64 DMX grid          │
│   ├─ widgets/fixture_grid.py                                 │
│   ├─ widgets/color_mixer_widget.py                           │
│   ├─ widgets/curve_editor.py                                 │
│   ├─ widgets/preview_widget.py                               │
│   ├─ widgets/segment_color_widget.py                         │
│   ├─ widgets/va_mapping_editor.py                            │
│   └─ widgets/empty_state.py                                  │
│                                                              │
│ Tests (RELEASE BLOCKER)                                      │
│   └─ tests/test_math_model.py        ← 19/19 tests           │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Audio → Color (skripsi math)
```
WAV file
  → engines/audio_engine.extract_features()       # librosa: tempo, RMS, V/A, MFCC, chroma
  → engines/audio_engine.segment_song()           # intro/verse/chorus/bridge
  → engines/analyze_pipeline.compute_valence_arousal()  # V, A in [0, 1]
  → engines/analyze_pipeline.va_to_hsv()          # V/A → HSV
  → engines/analyze_pipeline.hsv_to_rgb()         # HSV → RGB
  → engines/analyze_pipeline.rgb_to_rgbw()        # extract W
  → engines/color_mapping.apply_curve()           # LUT curve (linear/exp/log)
  → fixture_manager.songs[song_id] = {features, segments, va, rgbw, scene}
```

### Scenes → Chase → Output
```
song segments (from segment_song())
  → engines/scene_generator.generate_scenes()     # segment → Scene objects
  → panels/scenes_tab.py: user picks scene, sets fade
  → engines/chase.add_scene(scene)                # build chase
  → engines/chase.tick()                          # QTimer at fixture.fps
  → fixture_manager.broadcast(scene)              # scene → all patched fixtures
  → engines/artnet_sender.ArtNetController.send_frame(current_dmx)
  → UDP packet → Art-Net node
  → engines/artnet_sender.frames_sent += 1        # frame counter
```

### Fixture Editor → Address
```
fixtures/<name>.json
  → engines/fixture_types.match_template(name)    # 10 built-in templates
  → panels/fixture_editor_panel.py                # UI: form + channel table
  → fixture_manager.save_fixture(data)            # write to library
  → AddressTab: drag fixture → grid cell          # patch to DMX channel
  → fixture_manager.patch(address, fixture_name)  # store in address_map
```

### Save/Load
```
fixture_manager state
  → panels/project_io.save_zlx(path)              # JSON (version "3.0")
  → *.zlx file

*.zlx file
  → panels/project_io.load_zlx(path)              # validate version, migrate
  → fixture_manager state restored
```

---

## Threading

- **Main thread** — All Qt UI. Single-threaded Qt requirement.
- **Audio analysis** — Synchronous (librosa is fast for typical WAV lengths, <2s for 3min song on modern CPU). Runs in main thread, blocks UI briefly with a spinner.
- **Art-Net send** — Called from main thread, non-blocking (stupidArtnet uses UDP socket internally).
- **Chase playback** — QTimer at fixture.fps (default 30 fps), sends frames to Art-Net.
- **Live mode** — OutputTab QTimer at `1000/fps` ms interval, sends `current_dmx` continuously.
- **Preview polling** — PreviewTab QTimer at 200 ms, refreshes channel values.
- **Onboarding/Help/Toast/Splash** — Non-modal overlays on main thread.

No QThread / QRunnable usage — keeps the code simple. Heavy compute (librosa) could be moved to QThread in future if needed.

---

## State Management

`fixture_manager.FixtureManager` is the global state holder. Panels read/write to it directly (no MVC, no signals). This is pragmatic for a single-user desktop app — keeps code simple.

Tradeoffs:
- ✅ Easy to refactor, no signal/slot boilerplate
- ✅ Panels are self-contained, can be tested in isolation
- ❌ Tight coupling between panels and FixtureManager
- ❌ No undo/redo stack (planned for v7+)

---

## Math Model (RELEASE BLOCKER)

`tests/test_math_model.py` — 19 tests across 6 sections, derived from skripsi BAB 3:

1. **10k Reasons validation** — audio features → RGBW
2. **Quadrant** — V/A → HSV mapping
3. **HSV→RGB** — color conversion correctness
4. **RGB→RGBW** — white channel extraction
5. **Chase timing** — frame rate + fade math
6. **Pattern selection** — scene selection logic

All 19 tests must pass before any release. Run with:
```powershell
python tests/test_math_model.py
```

---

## Why Native Qt (not Electron/webview)?

v2.1 used `pywebview` + HTML/CSS/JS. v3.0 went native Qt for:
- **Performance** — Native rendering, no DOM overhead
- **Distribution** — Single folder + .exe (`--onedir` mode, PyInstaller default), no Chromium bundle (no extra ~150 MB Electron)
- **Type safety** — Python types instead of JS dynamic typing
- **Threading** — Qt's threading model is mature vs web workers
- **DMX latency** — Lower latency for real-time Art-Net output

Cost: No HTML/CSS flexibility. QSS is limited but enough for a "dark theme + grandma3-style panels" UX.

---

## Module Responsibilities

| Module | Owns | Doesn't own |
| ------ | ---- | ----------- |
| `main.py` | QApplication setup, splash, icon, font | UI logic |
| `main_window.py` | QMainWindow lifecycle, menubar, status bar, shortcuts, closeEvent | Panel content |
| `sidebar.py` | Left collapsible navigation (200/56 px) | Panel rendering |
| `fixture_manager.py` | Global state, persistence | UI |
| `panels/audio_tab.py` | WAV loader, librosa invoke, progress | Scene generation |
| `panels/scenes_tab.py` | Scene list, fade slider, Apply button | Audio analysis |
| `panels/chase_tab.py` | Timeline, play/stop, frame send, direction + loop | Scene generation |
| `panels/mixer_tab.py` | 512-channel fader grid + master dimmer | Live DMX polling |
| `panels/preview_tab.py` | Live DMX values (200 ms poll) | Sending |
| `panels/output_tab.py` | Art-Net node scan (QLC+ style) + Save; connect/blackout in header | Scene display |
| `panels/page_tab.py` | Custom button pad — trigger saved scenes + chases | Scene/chase authoring |
| `panels/address_tab.py` | DMX address grid (drag fixture) | Patching logic (in FixtureManager) |
| `panels/fixture_list_panel.py` | Fixture library (drag n drop) | Fixture editing |
| `panels/fixture_editor_panel.py` | New / save fixtures, type templates | Library scan |
| `panels/color_mixer_tab.py` | HSV mixer with curves | Audio color |
| `panels/about_panel.py` | Author + thesis metadata | Other content |
| `panels/project_io.py` | .zlx save/load (JSON, version "3.0") | UI prompts |
| `engines/*` | Pure logic, no Qt imports | UI |
| `widgets/*` | Reusable UX components | Business logic |
| `styles.py` | DARK_QSS string | Per-widget styling |
| `tests/*` | Math model regression (19/19) | UI tests |

---

## Adding a New Panel

1. Create `panels/my_panel.py` with a QWidget subclass
2. Register in `panels/__init__.py`
3. Add sidebar entry in `sidebar.py` `SIDEBAR_ITEMS`
4. Add to stacked widget in `MainWindow`
5. Update keyboard shortcut in `main_window.py` if needed

---

## Adding a New Engine

1. Create `engines/my_engine.py` with **no Qt imports**
2. Add pure-Python functions / classes
3. Wire into `fixture_manager` if it needs state
4. If UI needed, create panel + widget pair
5. Add to API.md

---

## Adding a New Fixture Type Template

1. Edit `engines/fixture_types.py`
2. Add entry to `FIXTURE_TYPES` dict (name → list of channel labels)
3. Restart app — template appears in Fixture Editor type combo
4. Channels auto-populate when user picks template

---

## Adding a New Shortcut

In `main_window.py`, find the `QShortcut` block near bottom of class, add:
```python
QShortcut(QKeySequence("Ctrl+X"), self, activated=self.my_action)
```

Update [README.md shortcuts table](README.md#keyboard-shortcuts) + [help_modal.py](widgets/help_modal.py).

---

## See Also

- [BUILD.md](BUILD.md) — how to build .exe
- [DEVELOPMENT.md](DEVELOPMENT.md) — dev workflow
- [API.md](API.md) — module reference
- [markdowns/app_feedback.md](../markdowns/app_feedback.md) — feedback audit (Phase 9+ roadmap)
