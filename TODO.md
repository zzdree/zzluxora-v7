# Roadmap — zzluxora

**Current**: v7.0.0 (feedback-literal polish + Windows installer, 2026-06-22)
**Math model**: 18/18 tests pass (RELEASE BLOCKER)

All v6.1/v6.2 UX-polish items from the feedback audit are **done** (see "Done in v7").
Roadmap below is the remaining major-feature backlog.

---

## v8.0 (next major — features)

Major architectural changes. Likely a breaking `.zlx` schema bump — migration code in `project_io.py::load_zlx()`.

### Multi-universe
- [ ] **N universes** — currently limited to 1 universe (512 ch). Support 4-16 universes via universe selector
- [ ] **Universe routing** — patch fixture to (universe, start_channel)
- [ ] **Per-universe FPS** — different fps per universe (e.g. moving heads at 60 fps, dimmers at 30)

### Undo/Redo
- [ ] **Command stack** — for fixture edits, scene edits, address patches
- [ ] **Ctrl+Z / Ctrl+Y** — global undo/redo
- [ ] **Action log** — sidebar shows recent actions

### Input
- [ ] **MIDI input** — MIDI clock + note triggers for scene sync
- [ ] **OSC input** — OSC messages from Ableton/TouchOSC/etc
- [ ] **DMX input** — in addition to output (for grandmaster-style apps)
- [ ] **Real-time audio reactive** — live mic input → live scenes (no WAV file needed)

### Sync
- [ ] **Timecode sync** — MTC/SMPTE for video sync
- [ ] **Auto-save** — every 30s during edit
- [ ] **Recording** — record DMX output to .dlm for replay
- [ ] **Cloud sync** — sync .zlx files between machines (optional, opt-in)

---

## Long-term

- [ ] **Web companion** — tablet/phone remote via local web server
- [ ] **3D fixture viz** — WebGL preview of room layout with fixture positions
- [ ] **Multi-project workspaces** — open multiple .zlx files, switch between
- [ ] **Plugin system** — load custom viz/effects from `plugins/` folder
- [ ] **Multi-user collab** — multiple operators on one show
- [ ] **AI-assisted** — auto-patch, auto-chase from audio (already mostly there with scene_generator)
- [ ] **Code signing** — sign .exe for distribution
- [ ] **Auto-update** — check for new versions, prompt to update

---

## Done in v7.0 (feedback-literal + installer)

- [x] **Header** — 1 play/pause toggle, drop "Project: " prefix, project path + Fixtures ▾ button
- [x] **Help menu** — `Help → Shortcuts (F1)`; modal subtitle dropped; close button top (✕) + bottom (centered)
- [x] **Sidebar** — active marker, 4 items, faded empty state when no project, geometric (non-emoji) icons
- [x] **Mixer** — master left, 513 sliders, range 0–255 default 0, refresh top-right
- [x] **Fixture list** — header dropdown (`Fixtures ▾`) instead of sidebar item
- [x] **Fixture editor** — MDI windows, 3-col table (ch/label/type), Open + New
- [x] **Address** — max 24 cols, position in corner, random + group-by-type buttons, auto-patch popup, Patch Info panel
- [x] **Scenes** — Regenerate removed, song list on left
- [x] **Page tab** — custom button pad for scenes + chases (replaced Programs editor)
- [x] **Preview** — PAR LED circles, drag, x/y sidebar
- [x] **Output** — QLC+ node scan, universe/FPS removed, Save only (connect/blackout in header)
- [x] **Analyze** — opposite-side caption enlarged (15px)
- [x] **Chrome emoji removed** — DESIGN.md §5.3 compliance (header, mixer, toast, sidebar icons)
- [x] **Windows installer** — Inno Setup, clean install/uninstall, AppData keep/delete options
- [x] **Data → `%APPDATA%\zzluxora`** — config + fixtures moved off the read-only install dir
- [x] **Version** — bumped to 7.0.0

## Done in v6.0

- [x] 8-phase rollout (Phase 1-8)
- [x] Math model regression (19/19 tests, skripsi BAB 3)
- [x] 12 engines, 16 panels, 14 widgets
- [x] Color mixer + curves
- [x] Program editor
- [x] Chase builder (direction + loop + auto-gen from song scenes)
- [x] Fixture editor with 10 type templates
- [x] Output tab with test frame + live mode + channel preview grid
- [x] Safe exit (closeEvent confirmation if Art-Net still connected)
- [x] Branding: lowercase "zzluxora"
- [x] Modern minimalis (grandma3 + qlc+)
- [x] Comprehensive docs (README, ARCHITECTURE, API, BUILD, DEVELOPMENT, TROUBLESHOOTING)

---

## Backlog

- [ ] **Localization** — English / Indonesian toggle
- [ ] **Theme variants** — light theme, high-contrast, custom
- [ ] **Audio stem separation** — Demucs/spleeter for vocal/instrument isolation
- [ ] **MIDI file export** — export chase as .mid for external playback
- [ ] **Video sync** — sync lighting to video timeline (Premiere/Resolve export)
- [ ] **Fixture library import** — import from Carallon, ETC, MA Lighting libraries

---

## See Also

- [CHANGELOG.md](CHANGELOG.md) — version history
- [README.md](README.md) — overview
- [markdowns/app_feedback.md](../markdowns/app_feedback.md) — original feedback audit
- [markdowns/app_prd.md](../markdowns/app_prd.md) — PRD (v7, includes installer §7c)
