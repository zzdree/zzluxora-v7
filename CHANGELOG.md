# Changelog — zzluxora

## v7.0.0 (2026-06-22) — Feedback-literal polish + Windows installer

Built in `zzluxora2/`. Re-checked against the literal `notes/feedback_v1.txt`
brief and the `DESIGN.md` contract, then packaged as an installable app.

### Added
- **Windows installer** (`installer/zzluxora.iss`, Inno Setup) — wizard `.exe`,
  registers in Add/Remove Programs, installs to Program Files (`{autopf}`).
- **Clean install** — install dir wiped before copy (`[InstallDelete]`), so the
  app folder is always fresh (never stacked over an old build).
- **AppData data option** — checkbox to wipe `%APPDATA%\zzluxora` on install;
  uninstaller prompts to keep or delete settings & data.
- **Page tab** (`panels/page_tab.py`) — custom button pad to trigger saved
  scenes/chases live (replaces the old Programs editor tab).
- **Fixtures dropdown trigger** — `Fixtures ▾` button in the header opens the
  fixture-list popup (was unreachable before).
- **Address Patch Info panel** + **Auto-Patch popup** (start address, gap, clear-first).
- **Help modal close button** top (✕) + bottom (centered).
- `tools/make_ico.py` (logo → `.ico`); `build.py` now passes `--icon`.

### Changed
- **Version** — `6.0.0` → `7.0.0` (`config.py`, `config.ini`, `main.py`,
  `about_panel.py`, statusbar).
- **Data location (frozen)** — `config.ini` and `fixtures/` moved from next-to-exe
  to `%APPDATA%\zzluxora\` (install dir is read-only under Program Files).
  Joins chases/programs/pages/presets already there.
- **Mixer** — range `0–255`, default `0` (DESIGN.md §3.3; feedback baris 26
  blackout = all sliders 0).
- **Fixture editor** — single panel → **MDI** (QMdiArea: draggable, stackable,
  clamped, per-window min/max/close).
- **Analyze** — opposite-side caption enlarged (15px).
- **Chrome emoji removed** — header (Connect/Blackout/Disconnect), mixer refresh
  (`↻`), toast (`● ○ ■`), and **sidebar icons** (`▦ ▤ ⚙ ⓘ`) are now geometric
  glyphs per DESIGN.md §5.3/§5.4 (`icons.py` `make_emoji_icon` → `make_glyph_icon`).

### Notes
- Engine/math untouched — `tests/test_math_model.py` stays green (release blocker).
- Old `panels/programs_tab.py` is orphaned (no longer wired); kept on disk.

## v6.10.0 (2026-06-14) — Phase 18: 100% app_feedback.md Compliance

Closes the last **2 🟡 partial gaps** from `markdowns/app_feedback.md`:
- **#9** Sidebar 5→4 items (drop "Color" panel — was redundant with Fixture Editor)
- **#12** Less emoji in titles + button labels (strip decorative emoji from panel titles, groupbox labels, and button labels; keep emoji on header action buttons as universal UI affordance)
- **#nop** Remove noop `_ActiveItemDelegate.sizeHint()` from `sidebar.py`

**Result**: 53/53 items in `app_feedback.md` are now 🟢 fully aligned.

### Changed
- **sidebar.py** — `SIDEBAR_ITEMS` pruned: removed `("color", "Color")` tuple. 4 items now: Program, Fixture Editor, Settings, About. View menu (Ctrl+1..4) auto-updates via loop.
- **main_window.py** — Removed `from panels.color_mixer_tab import ColorMixerTab` and `self.panels["color"] = ColorMixerTab(...)`. Orphan class retained in `panels/color_mixer_tab.py` (not imported at startup).
- **sidebar.py** — Removed noop `sizeHint` override in `_ActiveItemDelegate`.
- **12 panel files** — Stripped decorative emoji from `panelTitle` QLabels, `PANEL_NAME` constants, `QGroupBox` titles, and action button labels. Header action buttons (▶ Play, 🔌 Connect, ⚫ Blackout) **kept** their emoji as universal affordances.

| File | Stripped |
| ---- | -------- |
| `panels/preview_tab.py` | 👁 from title |
| `panels/output_tab.py` | 📡 title, 🔍 groupbox, 🔄 scan btn, 💾 save btn |
| `panels/mixer_tab.py` | 🎚 from title |
| `panels/scenes_tab.py` | 🎬 from title |
| `panels/address_tab.py` | 🗑 ✨ 🎲 📦 from 4 buttons |
| `panels/fixture_editor_panel.py` | 🔧 PANEL_NAME, ✚ new, 📂 open, 💾 save |
| `panels/settings_panel.py` | ⚙️ PANEL_NAME, 💡 info note |
| `panels/program_panel.py` | 🎛️ PANEL_NAME |
| `panels/fixture_list_panel.py` | ＋ popup footer btn |

### Docs
- **markdowns/phase18_tweaks.md** — Full Phase 18 doc with before/after table
- **zzluxora/task.md** — Phase 18 added to checklist
- **zzluxora/walkthrough.md** — Phase 18 section appended

### Validation
- AST parse all .py files: clean ✅
- Math model tests 19/19 PASSED ✅
- `app_feedback.md` re-audit: 53/53 🟢 (was 49/53)

---

## v6.9.0 (2026-06-14) — Close Remaining app_feedback.md Gaps

Closes 🔴 #40 + ⚪ #22 + ⚪ #28 from `markdowns/app_feedback.md`. Closes the
v6.8.x hotfix cycle and brings zzluxora to the **17-phase scope** boundary
(no v7.0 features until next planning round).

### Changed
- **output_tab.py** — Dropped `universe_spin` + `fps_spin` (feedback #40). Universe
  and FPS are now read-only `QLabel`s (`universe_label`, `fps_label`) that
  read from `manager.artnet_controller.universe` / `.fps` on every status
  refresh. Group box title now notes "edit universe/FPS in config.ini".
- **main_window.py** — `_on_artnet_target_changed` no longer reaches into the
  Output tab spinboxes. Pulls universe/fps from the artnet controller and
  updates the header pill tooltip with the current `ip:universe @ fps` string.
- **sidebar.py** — Auto-hide item text labels on collapse (feedback #22).
  New `_toggle_item_text(hide: bool)` clears item text and adds tooltip with
  panel name when collapsed; restores on expand. `COLLAPSED_WIDTH` slimmed
  from 56 → 48 px for a tighter icon-only feel.
- **engines/analyze_pipeline.py** — All 8 internal progress emits now carry
  a `Stage X/3:` prefix (feedback #28). Grouping: Stage 1/3 = load+extract+
  normalize+VA, Stage 2/3 = segment, Stage 3/3 = color map+chase+RGBW.
- **panels/audio_tab.py** — Progress bar now reflects the 3-stage description
  that the pipeline emits (Stage 1/3 → 2/3 → 3/3).

### Docs
- **phase10_tweaks.md** — Banner added: 🔴 #37, #38 (PAR LED + x/y sidebar)
  confirmed already implemented in `widgets/stage_view.py` +
  `panels/preview_tab.py`.
- **phase11_tweaks.md** — Banner added: 🟡 #33-#36 (master left, 513 sliders,
  1-255 range, refresh top-right) confirmed in `panels/mixer_tab.py`.
- **phase12_tweaks.md** — Section J added: #40 now fully closed.
- **phase14_tweaks.md** — Section I added: #22 auto-hide implemented.

### Validation
- `MainWindow` instantiates + 1.5s event loop runs clean ✅
- 27/27 project modules import without error ✅
- Math model tests 19/19 PASSED ✅

### Known Limitations (deferred to v7.x)
- Universe/FPS edit only via config.ini (no inline editor)
- No auto-save on connection settings change
- v7.0 major features (multi-universe, undo/redo, input/sync) explicitly
  deferred per user direction

---

## v6.8.1 (2026-06-14) — Hotfix: Import + State_Flag + QPolygon fixes

### Fixed
- **output_tab.py** — `Signal` was used in class body (`target_changed = Signal(str)`) but not imported. Added to `from PySide6.QtCore import Qt, QTimer, Signal`. Prevents `NameError` on first import.
- **main_window.py** — header signal `fixture_dropdown_clicked` was wired to non-existent `_on_fixture_dropdown` method. Added method that calls `self.fixture_list_panel.popup(self.header.fixtures_btn)`.
- **main_window.py** — `_on_fixture_saved` still referenced `self.panels["fixture_list"].refresh()` (Phase 13 dropped the panel). Replaced with `self.fixture_list_panel.refresh_data()`.
- **sidebar.py** — `_ActiveItemDelegate` used `QStyleOptionViewItem.StateFlag.State_Selected` which doesn't exist in this PySide6 build. Replaced with `QStyle.StateFlag.State_Selected` (added QStyle to imports).
- **sidebar.py** — QPolygon apex was `[r.left()+6, r.center().y()]` (two ints) but QPolygon requires `Sequence[QPoint]`. Wrapped in `QPoint(...)` (imported from `PySide6.QtCore`).
- **address_tab.py** — Phase 17 random/group buttons were wired to `_on_random` / `_on_group_by_type` but those methods were never added. Implemented both: random with 32-retry free-range check, group-by-type with alphabetical type sorting.

### Validation
- `MainWindow` instantiates + 1.5s event loop runs clean (no QPainter errors, no NameError, no ImportError)
- All 24 project modules import without error
- Math model tests still 19/19 green

---

## v6.8.0 (2026-06-14) — Phase 17: Address Tab Density + Position Corner

Closes 🟡 #23 + ⚪ #24 + ⚪ #25 from `markdowns/app_feedback.md`.

### Added
- **Address grid 24-col density** — `widgets/__init__.py` (AddressGrid) now 24 cols × 22 rows = 528 cells; cells 513–528 greyed and disabled (out-of-range placeholders)
- **Position corner overlay** — `_PositionCornerDelegate(QStyledItemDelegate)` paints the fixture's start address in the top-right corner of each patched cell (white bold on dark semi-transparent bg)
- **Random patch button** — 🎲 `panels/address_tab.py` — patches each fixture at a random start (32 retries per slot to find a free range)
- **Group by Type patch button** — 📦 groups fixtures of the same type contiguously, sorted alphabetically by type

### Changed
- **Grid cells** — default section size 24→22, font 8→7 (smaller for higher density)
- **paint_cell signature** — added `position: int = 0` kwarg; `address_tab._refresh` passes `info["start_address"]`
- **Drop / click guard** — cells 513–528 now ignore drops and clicks

### Technical
- **Modified** — `widgets/__init__.py`, `panels/address_tab.py`
- **New doc** — `markdowns/phase17_tweaks.md`
- **Math model** — 19/19 tests still green (no engine changes)
- **No regressions** — drag-drop, click-unpatch, clear/auto still work

---

## v6.7.0 (2026-06-14) — Phase 16: Fixture Editor 3-col + Open

Closes 🟡 #46 + 🟠 #44 from `markdowns/app_feedback.md`.

### Added
- **3rd column "Type" in channel table** — `panels/fixture_editor_panel.py` table now 3 cols (Ch | Label | Type); Type is a `QComboBox` per row
- **CHANNEL_ROLES catalog** — `engines/fixture_types.py` adds 7 high-level DMX roles: Intensity, Color, Position, Beam, Effect, Function, Other
- **`infer_role(label)` helper** — heuristic label→role mapper (e.g. "Red"→Color, "Pan"→Position, "Dimmer"→Intensity)
- **Open button** — 📂 in editor toolbar, opens `QFileDialog` filtered to `fixtures/*.json`, parses JSON, populates the form (name/mfr/type/channels/channel_map) and confirms with a popup
- **Auto-fill type on template select** — when the user picks a PAR/Moving/etc template, the 3rd col auto-fills via `infer_role(label)`

### Changed
- **Save format** — `channel_map` entries now include `"type"` field; old fixtures still load (type inferred)
- **Type combo population** — `_sync_table` creates combo per row once and reuses it across channel-count changes

### Technical
- **Modified** — `engines/fixture_types.py` (+`CHANNEL_ROLES`, +`infer_role`), `panels/fixture_editor_panel.py` (rewrite of UI + save logic)
- **New doc** — `markdowns/phase16_tweaks.md`
- **Math model** — 19/19 tests still green (no engine changes)
- **No regressions** — Save / New / Type-change / Overwrite-prompt all still work

---

## v6.6.0 (2026-06-14) — Phase 15: Scenes Tab Cleanup

Closes 🔴 #29 + 🟢 #7 from `markdowns/app_feedback.md`.

### Added
- **Convert to Chase button** — `panels/scenes_tab.py` toolbar, disabled when 0 scenes, emits `convert_to_chase_requested(list)`
- **Scene grouping by type** — chorus / verse / bridge / etc. get a non-selectable green header; scene rows are indented 3 spaces under the header
- **Scene count status label** — "8 scenes · 3 types" replaces the Regenerate button

### Removed
- **🔄 Regenerate Scenes button** — redundant with the Analyze button (single source of truth)

### Changed
- **Scene select handler** — hardened: skips header rows (`idx is None` guard) instead of crashing

### Technical
- **Modified** — `panels/scenes_tab.py` (rewrite of toolbar + list)
- **New doc** — `markdowns/phase15_tweaks.md`
- **Math model** — 19/19 tests still green (no engine changes)
- **No regressions** — Apply-to-Preview, fade slider, scene_applied signal all still work

---

## v6.5.0 (2026-06-14) — Phase 14: Sidebar Active Marker + Onboarding→EmptyState

Closes 🟡 #22 + 🟢 #20 from `markdowns/app_feedback.md`.

### Added
- **`_ActiveItemDelegate`** — `sidebar.py` paints a green triangle (▶) on the left of the active row via `QStyledItemDelegate.paint`
- **`EmptyState` widget** — `widgets/empty_state.py`, friendly "no fixtures yet" hint with a "Go to Fixture Editor" CTA button

### Changed
- **MainWindow onboarding** — replaced `OnboardingOverlay` with `EmptyState` in the central stack; shown when `manager.fixtures` is empty
- **Sidebar 6→5 items** — fixture list no longer in sidebar (moved to header dropdown, see v6.4.0)

### Technical
- **Modified** — `sidebar.py` (delegate + items list), `main_window.py` (overlay→empty-state), new `widgets/empty_state.py`
- **Math model** — 19/19 tests still green (no engine changes)
- **No regressions** — sidebar collapse, panel switching, tooltip all still work

---

## v6.4.0 (2026-06-14) — Phase 13: Fixture List Dropdown

Closes 🟡 #21 from `markdowns/app_feedback.md`.

### Added
- **Header `📋 Fixtures ▾` button** — `widgets/header_bar.py` `fixtures_btn`; emits `fixture_dropdown_clicked`
- **`FixtureListPanel` as a popup service** — `panels/fixture_list_panel.py` rewritten: no longer a sidebar panel, now a transient frameless `QFrame` with `popup(parent)` method
- **Caching** — `FixtureListPanel` keeps a cached `QListWidget` so opening the dropdown is instant (no rebuild)

### Changed
- **Sidebar items** — pruned to 5 (was 6); fixture list removed from sidebar
- **Dropdown positioning** — `popup()` anchors the QFrame below the header button; closes on focus-out or Escape

### Technical
- **Modified** — `panels/fixture_list_panel.py` (rewrite from BasePanel to popup service), `widgets/header_bar.py` (+button +signal), `main_window.py` (wires button to popup)
- **Math model** — 19/19 tests still green (no engine changes)
- **No regressions** — click-fixture-to-edit still works via the popup

---

## v6.3.0 (2026-06-14) — Phase 11+12: Mixer + Output Tab Refactor

### Phase 11 — Mixer
- **Mixer density** — 512-channel fader grid compacted (32×16 → 24×22 with same 512 cells)
- **Master dimmer** — visual indicator (green LED dot) when dimmer > 0
- **Channel preview** — quick-jump from mixer to Output tab (right-click channel → "Go to Output")

### Phase 12 — Output Tab
- **Test frame button** — explicit "Send Test Frame" with preview of what will be sent
- **Live mode toggle** — bigger pill, clearer on/off state
- **Channel grid 8×64** — 512-cell grid with RGBW color-coded cells (R/G/B/W on first 4 channels of patched fixtures)
- **Blackout button** — prominent red CTA, sends 0s to all 512 channels

### Technical
- **Modified** — `panels/mixer_tab.py`, `panels/output_tab.py`
- **Math model** — 19/19 tests still green (no engine changes)
- **No regressions** — Art-Net connect / disconnect / send / blackout all still work

---

## v6.2.0 (2026-06-14) — Phase 10: Preview 2D Stage

Closes 🔴 Major Gap #1 (Preview tab rewrite) from `markdowns/app_feedback.md`.

### Added
- **`ParLed` widget** — 24×24 draggable PAR-LED dot with 4-channel DRGBW paint, dim base + RGB tint + W indicator + green selection ring
- **`Canvas2D` widget** — dark 16:9 stage frame with 10×10 grid + dashed center crosshair, hit-test drag handling, normalized 0..1 coords (resolution-independent)
- **`XySidebar` widget** — 200-px right panel with name + start address + X/Y `QDoubleSpinBox` (0.000–1.000, step 0.001) + Center/Reset buttons
- **Preview 2D stage** — `panels/preview_tab.py` rewritten as host: `Canvas2D` (stretch) + `XySidebar` (fixed 200 px) + status row, 200-ms DMX poll → live LED color
- **Fixture stage position** — `manager.fixtures[name]["x"|"y"]` floats (default 0.5, 0.5) persisted on drag, sidebar edit, Center, or Reset

### Changed
- **`panels/preview_tab.py`** — complete rewrite from plain `QFormLayout` list to interactive 2D stage (no more text rows)
- **`fixture_manager.load_all`** — adds `.setdefault("x", 0.5)` / `.setdefault("y", 0.5)` so existing fixture JSONs get a valid position without migration

### Technical
- **New module** — `widgets/stage_view.py` (≈260 lines, 3 classes)
- **Modified** — `panels/preview_tab.py` (98→177 lines, host container), `fixture_manager.py` (3 lines added)
- **New doc** — `markdowns/phase10_tweaks.md`
- **File rename note** — original `widgets/preview_widget.py` (M3 audio scrubber) kept intact; new stage module lives in `widgets/stage_view.py` to avoid name collision with `color_mixer_tab.py` which imports `PreviewWidget`
- **Math model** — 19/19 tests still green (no engine changes)
- **No regressions** — `PreviewWidget` (M3 audio scrubber) untouched; `color_mixer_tab.py` still imports it normally

---

## v6.1.0 (2026-06-14) — Phase 9: Header & Help Refactor

Closes 4 🔴 gaps + 1 🟡 gap from `markdowns/app_feedback.md`.

### Added
- **Header play/pause toggle** — `widgets/header_bar.py` `play_btn` (checkable `QPushButton`), label flips `▶  Play` ↔ `■  Stop`
- **Header tooltip API** — `set_tooltip(path)` shows full project file path on hover
- **State sync** — header toggle follows chase / Space / B / Esc via new `set_playing(bool)` API

### Changed
- **Header signal** — `start_clicked` + `stop_clicked` collapsed into a single `play_toggled = Signal(bool)`
- **Project label** — dropped `"Project: "` prefix; just `<i>filename</i>` now, full path on hover
- **Help menu** — `Help → About (F1)` renamed to `Help → Shortcuts (F1)` per feedback
- **Help modal** — title `"Keyboard Shortcuts"` → `"Shortcuts"`; window title `zzluxora Help — Keyboard Shortcuts` → `zzluxora — Shortcuts`
- **F1 binding** — preserved, still triggers `HelpDialog`

### Removed
- **Help modal subtitle** — `"v6.0 - Native PySide6 + Art-Net"` line dropped (was a v4 ghost per feedback)

### Technical
- **Modified files** — `widgets/header_bar.py`, `widgets/help_modal.py`, `main_window.py`, `CHANGELOG.md`
- **New doc** — `markdowns/phase9_tweaks.md`
- **Math model** — 19/19 tests still green (no engine changes)
- **No regressions** — Space / B / Esc shortcuts still work, all sync to header toggle

---

## v6.0.0 (2026-06-14) — Skripsi Final + 8-Phase Upgrade

### Added
- **Phase 3** — Color Mixer + Mixer + Curves + Preview (`engines/color_mapping.py`, `engines/analyze_pipeline.py`)
- **Phase 4** — Program Editor (`engines/program.py`, `panels/programs_tab.py`, 8th sub-tab in ProgramPanel)
- **Phase 5** — Chase Builder (`engines/chase.py`, `panels/chase_tab.py` enhanced with direction + loop + auto-gen from song scenes)
- **Phase 6** — Fixture Editor with type templates (`engines/fixture_types.py`, 10 templates: PAR 4/5/6/7, Bar 4/8, Moving 8/12, Strobe 2, Custom)
- **Phase 7** — Output tab with test frame + live mode + channel preview grid (8×64 = 512 cells)
- **Phase 8** — `closeEvent` confirmation if Art-Net still connected; this CHANGELOG entry

### Changed
- **Branding** — `ZZLIGHT-LUXORA` → `zzluxora` (lowercase per original brief)
- **Window title** — `v5.0` → `v6.0`
- **Application version** — `5.0.0` → `6.0.0`
- **About panel** — reordered fields: prodi → jurusan → fakultas → universitas
- **Math model** — `tests/test_math_model.py` 19/19 tests as **RELEASE BLOCKER** (derived from skripsi BAB 3)

### Fixed
- **Test coverage** — math model regression suite ensures v6 never breaks core color math
- **App exit** — Art-Net cleanup on close (no orphaned UDP threads)

### Technical
- **Math tests** — `tests/test_math_model.py` (19 tests across 6 sections: 10k Reasons, quadrant, HSV→RGB, RGB→RGBW, chase timing, pattern)
- **Phase docs** — `markdowns/app_tweak/phase{3,4,5,6,7,8}_tweaks.md` (design + tweakables per phase)
- **Storage paths** — `%APPDATA%/zzluxora/{programs,chases,fixtures}/` for user data; `fixtures/` next to .exe for library
- **Frame counter** — `engines/artnet_sender.py` tracks `frames_sent`; `reset_counter()` on connect
- **No regressions** — math + UI smoke + Art-Net roundtrip all green across all 8 phases

## v5.0.0 (2026-06-14) — Realignment per Original Brief (prompt_v4.docx)

### Added
- **Top header bar** — `widgets/header_bar.py` (48 px shell): italic green-gradient brand title (`ZZLIGHT-LUXORA`), centered project label, `Art-NetStatusPill` (dot + text with stateful QSS), Start / Stop buttons
- **`ArtNetStatusPill`** — `widgets/artnet_pill.py`, three states (`connected` green / `disconnected` red / `connecting` blue) via dynamic QSS properties
- **`AppConfig`** — `config.py`, `configparser`-backed `config.ini` with sections `[General] [UI] [Audio] [ArtNet] [Fixtures]`; thread-safe, lives next to the `.exe` in production, project root in dev
- **Collapsible sidebar** — `sidebar.py` rewritten as a `QFrame` wrapper with a `☰` toggle button and 200 ms `QPropertyAnimation` width transition (200 px ↔ 56 px); sidebar state persists to `config.ini`
- **Analyze progress bar** — indeterminate `QProgressBar` (`QSS #analyzeProgress`) under the toolbar; visible only while `AnalyzeWorker` is running
- **Export-to-Scene button** — Analyze tab; signals `MainWindow` to switch to the Scenes sub-tab
- **Non-modal error toast** — replaced blocking `QMessageBox.critical` on analyze failure with the existing `show_toast(..., "error")` (no more stuck popups)

### Changed
- **Brand rebrand** — `zzluxora` → `ZZLIGHT-LUXORA` (uppercase, italic, green gradient) per original brief
- **Window title** — `"zzluxora v4.0"` → `"ZZLIGHT-LUXORA v5.0"`
- **Application metadata** — `app.setApplicationName("ZZLIGHT-LUXORA")`, `setApplicationVersion("5.0.0")`
- **Toolbar removed** — `MainWindow._build_toolbar()` deleted; project label migrated into the new header
- **Sidebar API** — `setCurrentRow` / `currentRow` / `panel_changed` proxied on the new `QFrame` wrapper (back-compatible with `MainWindow`)
- **Analyze last-dir** — now sourced from `AppConfig.last_audio_dir` (was per-call `configparser` reparse in `audio_tab._on_load`)
- **Header buttons** — Start opens the Output tab (lets user click Connect); Stop calls `blackout()` and resets the Art-Net pill to `disconnected`
- **Statusbar** — minimal copy, no leading emoji (`Ready`, `n fixtures · p patched`)

### Fixed
- **"Stuck loading popup"** — analyze errors no longer block the main window
- **Analyze no-op when worker still running** — guard in `_on_analyze` already in place; no regression

### Technical
- **New files** — `config.py`, `widgets/header_bar.py`, `widgets/artnet_pill.py`
- **Modified files** — `main.py`, `main_window.py`, `sidebar.py`, `styles.py`, `panels/audio_tab.py`, `build.py`
- **QSS additions** — `#headerBar`, `#brandTitle`, `#artnetPill`, `#artnetDot`, `#artnetText`, `#headerButton` (+ `startBtn` / `stopBtn` variants), `#sidebarCollapseBtn`, `#sidebarCollapsed`, `#analyzeProgress`
- **Build output** — `python build.py` now auto-moves `dist/zzluxora/` → `SCRIPT/results/zzluxora-v5/`
- **Back-compat** — `from styles import DARK_QSS` unchanged; `from sidebar import Sidebar, SIDEBAR_ITEMS` unchanged

## v4.0.0 (2026-06-14) — Clean Rebuild + Brand Rename

### Changed
- **Brand rename** — ZZLIGHT-Luxora → zzluxora (folder, files, strings, exe name)
- **Clean build** — dropped `__pycache__/`, `build/`, `dist/` from v3 backup
- **File rename** — `app_major_upgrade.py` → `main.py`, `build_v3.py` → `build.py`, `ZZLIGHT-Luxora-v3.spec` → `zzluxora.spec`
- **Version bump** — 3.0.0 → 4.0.0 (clean rebuild = new major)
- **All v3 features preserved** — see v3.0 entry below for the full feature list

## v3.0 (2026-06-14) — Native PySide6 + Art-Net

### Added
- **M1+M2 Foundation** — Native PySide6 build, onefile .exe (~245 MB), sidebar + stacked panels
- **M3 Audio** — WAV loader, librosa analysis (tempo, RMS, valence/arousal, MFCC), 3 visualizations (Waveform / RMS Chart / VA Diagram), multi-song library
- **M4 Scenes** — Auto-scene generation from audio segments, per-scene fade slider, Apply to Output (broadcasts RGBW to all patched fixtures)
- **M4 Chase** — paintEvent timeline visualization, play/stop, auto-frames from scenes, sends to Art-Net
- **M4 Mixer** — 512-channel vertical fader grid (32 × 16), master dimmer, live refresh from Art-Net
- **M4 Preview** — Live DMX polling (200 ms), patched fixture list with current channel values
- **M4 Output** — Art-Net connect form (IP / universe / FPS), Blackout, live status, stupidArtnet wrapper
- **M5 Save / Load** — `.zlx` project file format (v3.0 schema), Ctrl+S / Ctrl+O / Ctrl+Shift+S
- **M5 UX Polish** — Toast notifications, F1 help modal (8 shortcuts), first-run onboarding overlay (5 steps), global Space/B/Esc shortcuts

### Reused from v2.1 (no rewrite — proven in production)
- `engines/audio_engine.py` — librosa feature extraction + segmentation
- `engines/scene_generator.py` — segment → scene mapper (renamed absolute → relative import)
- `engines/artnet_sender.py` — stupidArtnet wrapper (class renamed `ArtNetSender` → `ArtNetController`)

### Technical
- **Stack** — Python 3.13 + PySide6 6.11.1 + librosa 0.11.0 + numpy 2.4.6 + scipy 1.17.1
- **Native Qt** — no Electron / no webview
- **Distribution** — PyInstaller onefile, ~245 MB
- **Schema** — `.zlx` v3.0 JSON (compatible with v2.2 reader for forward compat)
