# zzluxora — Design System

> **Vibe**: an audio engineer's lighting desk at 3 AM.
> Modern minimalist on the surface, industrialist under the hood.

---

## 0. How to read this doc

This is the **design contract** for `zzluxora`. Every PR that touches `styles.py`, panel layout, or chrome widgets should be checked against it. Sections are split into:

- **Tokens** — values (color, size, motion) you can copy
- **Components** — reusable building blocks, with anatomy + states
- **Layouts** — page-level composition patterns
- **Voice** — text and emoji rules
- **Appendix** — execution helpers (the emoji migration map)

If a contribution is in tension with the doc, update the doc **first**, then the code.

---

## 1. Design Philosophy

### 1.1 The mix: grandMA3 × QLC+

| Borrow from | What we take | What we skip |
|-------------|--------------|--------------|
| **grandMA3** (MA Lighting) | Multi-pane console grid · mono numerics · executor-row metaphor · status pills · dark hierarchy | Command-line ("MA-Trick") · encoder-wheel metaphors · macro pools (out of scope for MVP) |
| **QLC+** (open source) | Modular panel architecture · channel-grid clarity · drag-to-patch · open file formats | Virtual console drag-palette · "casual" gradients · brand-orange |

**Result**: a serious operator's tool that still feels like a desktop app, not a rack-mounted console.

### 1.2 Modern minimalist, industrialist in production

- **Modern minimalist**: no decoration without function. Borders define surfaces. Type does the work.
- **Industrialist**: built for 8-hour sessions, low light, gloves, sweat. High contrast, large hit targets, no animation that doesn't carry information. Real-time controls (DMX, blackout) react in **0 ms** — operators can't wait for easing curves when a fixture is on fire.

### 1.3 The three rules

1. **Dark mode is the product**, not a theme. Light mode is not on the roadmap.
2. **No emoji in chrome.** Emoji are allowed as content markers (e.g. song titles from user data) — never in our UI strings, icons, or labels.
3. **Color carries meaning, not decoration.** Every accent color must be one of: action, status (ok/warn/err/info), or active state.

---

## 2. Color System

### 2.1 Surface (backgrounds)

| Token | Hex | Use |
|-------|-----|-----|
| `--bg-0` | `#0a0a0a` | App root, deepest layer |
| `--bg-1` | `#121212` | Sidebar, menubar, statusbar |
| `--bg-2` | `#181818` | Panel bodies, content cards |
| `--bg-3` | `#1f1f1f` | Elevated cards, hover surface |
| `--bg-elevated` | `#242424` | Modals, popovers, dropdowns |

> **Rule of thumb**: each step up = +6 to +10 in luminance. Never more. We are not building a Material elevation system.

### 2.2 Border

| Token | Hex | Use |
|-------|-----|-----|
| `--border-subtle` | `#2a2a2a` | Default 1 px dividers |
| `--border-strong` | `#3a3a3a` | Focused card, active tab body, hovered input |

### 2.3 Text

| Token | Hex | Use |
|-------|-----|-----|
| `--text-primary` | `#ededed` | Body text, panel titles, primary labels |
| `--text-secondary` | `#a0a0a0` | Helper text, values in lists, secondary labels |
| `--text-muted` | `#6a6a6a` | Disabled, hint text, status-bar metadata |

### 2.4 Accent + status

| Token | Hex | Use |
|-------|-----|-----|
| `--accent` | `#2ecc71` | Primary action, "active" state, primary button bg |
| `--accent-hover` | `#27ae60` | Accent at hover (slightly darker) |
| `--accent-soft` | `#1d3a2a` | Accent at 12 % alpha — for selected-row backgrounds |
| `--ok` | `#2ecc71` | Success toast, "connected" pill |
| `--warn` | `#f39c12` | Warning toast, "pending" pill |
| `--err` | `#e74c3c` | Error toast, "disconnected" pill, emergency stop |
| `--info` | `#4aa3ff` | Info toast, "syncing" pill |

> [!TIP]
> The same green serves both `--accent` and `--ok`. That's intentional — operators should not have to learn a new color for "go". `--warn` and `--err` are reserved for actual warnings/errors. **Do not** use `--accent` for warnings.

### 2.5 Contrast

| Pair | Ratio | WCAG |
|------|-------|------|
| `--text-primary` on `--bg-0` | 14.4 : 1 | AAA |
| `--text-secondary` on `--bg-1` | 7.5 : 1 | AAA |
| `--text-muted` on `--bg-1` | 3.9 : 1 | AA Large only — use for metadata, never for primary info |
| `--accent` on `--bg-0` | 9.1 : 1 | AAA |

All interactive text targets **≥ 4.5 : 1** (WCAG AA).

---

## 3. Typography

### 3.1 Font stacks

```css
--font-ui:      "Segoe UI Variable", "Segoe UI", "Inter", "Roboto", sans-serif;
--font-mono:    "JetBrains Mono", "Cascadia Code", "Consolas", "Menlo", monospace;
--font-display: var(--font-ui);  /* same family, larger weight */
```

### 3.2 Type scale

| Token | Size / line-height | Weight | Use |
|-------|-------------------|--------|-----|
| `--type-micro` | 10 / 14 | 600 | Status bar metadata, table footer |
| `--type-caption` | 11 / 14 | 500 | Toast body, hint text, table cells |
| `--type-body` | 12 / 16 | 400 | Default body, list items, button labels |
| `--type-body-strong` | 12 / 16 | 600 | Emphasized body, sidebar item, tab label |
| `--type-label` | 13 / 18 | 700 | Section titles, card titles, form labels |
| `--type-h2` | 16 / 22 | 700 | Panel sub-headers |
| `--type-h1` | 20 / 26 | 700 | Panel titles |
| `--type-display` | 28 / 32 | 800 | About card logo, splash |

### 3.3 Mono numerics (DMX values, addresses, BPM, dB, timecode)

```css
.numeric {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;  /* aligned digits */
  letter-spacing: 0;
}
```

**Use mono for**: DMX channel values (0–255, 3-digit padded: `000` / `128` / `255`), DMX addresses (1–512), BPM, time, file sizes, IP addresses, port numbers.

**Never mono for**: prose, button labels, headings, menu items.

### 3.4 Uppercase + tracking

Section labels and status pills are uppercase with +0.4 px tracking. Never use uppercase for sentences.

```css
.label-caps {
  text-transform: uppercase;
  letter-spacing: 0.4px;
  font-size: var(--type-micro);
  font-weight: 600;
}
```

---

## 4. Spacing & Grid

### 4.1 Spacing scale (4 px base)

| Token | Value | Use |
|-------|-------|-----|
| `--space-1` | 4 px | Icon-to-label gap, tight padding |
| `--space-2` | 8 px | Input padding, list-item padding |
| `--space-3` | 12 px | Card inner padding |
| `--space-4` | 16 px | Panel padding, section gap |
| `--space-5` | 24 px | Panel-to-panel gap |
| `--space-6` | 32 px | Major section break |
| `--space-8` | 48 px | (reserved — splash / about only) |

### 4.2 Layout grid

- 12-column main grid, 16 px gutter
- Sidebar: **200 px** fixed (current). Can shrink to 168 px for density.
- Min window: `1024 × 680` (current default), target `1280 × 800`
- Panel body padding: `--space-4` (16 px)
- Card padding: `--space-3` (12 px)
- Hit target minimum: **32 × 32 px** for icon buttons

### 4.3 Radius

| Token | Value | Use |
|-------|-------|-----|
| `--radius-sm` | 2 px | Tags, small badges |
| `--radius-md` | 4 px | Buttons, inputs, list items |
| `--radius-lg` | 8 px | Cards, modals, toasts |

> **Rule**: radius decreases as information density increases. DMX grid cells = 0 px. Faders = 2 px. Buttons = 4 px. Cards = 8 px.

---

## 5. Iconography

### 5.1 Source

**Lucide Icons** (MIT licensed) — line-style, 1.5 px stroke, square viewBox. Bundled as SVG strings in `icons.py`, rendered via `QSvgRenderer` into `QIcon` at sizes 16 / 20 / 24 px.

Fallback for shipping without Lucide bundle: use Unicode geometric / arrow symbols (`▶`, `■`, `●`, `◼`, `→`, `×`).

### 5.2 Sizes

| Token | px | Use |
|-------|----|----|
| `--icon-sm` | 16 | Inside button label, table cell |
| `--icon-md` | 20 | Toolbar action, sidebar item |
| `--icon-lg` | 24 | Page-level action, large button |
| `--icon-xl` | 32 | Splash / about (rare) |

### 5.3 Emoji policy

> [!IMPORTANT]
> **Emoji are forbidden in chrome.** This is not a style preference — it's a design contract.

**Why**: emoji render differently per OS (Windows Segoe UI Emoji vs macOS Apple Color Emoji vs Linux Noto). A consistent industrialist UI cannot depend on system emoji rendering. They also fail at small sizes, on high-DPI displays in production, and on operator consoles with custom font policies.

| Allowed | Forbidden |
|---------|-----------|
| `●` solid dot (status pill) | `📂` `💾` `🗑` `✨` `🎵` `📡` `🔌` `🎚` `🔄` `❌` `⌨` `⚡` `⏳` etc. |
| `▶` `■` `◼` `×` `✓` (geometric) | Any pictographic emoji |
| Emoji **as user data** (e.g. song title typed by user) | Emoji in **our** strings, labels, QAction text, QPushButton text |

**Exception**: the welcome modal may use one decorative icon to mark the version. After that, no exceptions.

### 5.4 The icon set we need

Mapped to current `QAction` / `QPushButton` calls:

| Action | Lucide name | Unicode fallback |
|--------|-------------|------------------|
| Open project | `folder-open` | — |
| Save | `save` | — |
| Save as | `save` + `(as)` label | — |
| Exit | `x` | `×` |
| New (clear) | `plus` | `+` |
| Delete | `trash-2` | — |
| Edit / settings | `settings` | — |
| Help / shortcuts | `keyboard` | — |
| About | `info` | `ⓘ` |
| Load audio | `file-audio` | — |
| Reload / refresh | `refresh-cw` | — |
| Connect | `plug` | — |
| Disconnect | `plug-zap` | — |
| Blackout | `moon` | `●` |
| Emergency stop | `octagon` (filled) | `■` |
| Auto-patch | `wand-2` | — |
| Regenerate | `refresh-cw` | — |

> **Status markers** (replaces `⚡`, `✓`, `✗`, `⚠`, `●`):
> - Live / connected / success: `●` (filled, `--ok`)
> - Pending / analyzing: `○` (open, `--warn`)
> - Failed / disconnected / error: `■` (filled, `--err`)
> - Idle / ready: `·` (middle dot, `--text-muted`)

---

## 6. Components

Each component is documented as: **Anatomy** (parts) · **States** (default/hover/pressed/disabled/active) · **Code class** (where to find it) · **QSS object name** (so contributors can target it).

### 6.1 `Button`

```
[ icon 12px ] [ label ]
   4 px gap
```

**Variants**:
- `primary` — bg `--accent`, text `--bg-0`, weight 600
- `secondary` — bg `--bg-3`, text `--text-primary`, border `--border-subtle`
- `ghost` — bg transparent, text `--text-secondary`, no border
- `danger` — bg `--err`, text `--bg-0`, weight 600
- `icon-only` — 32 × 32 square, no label

**States**:
- default → hover (border +accent, 80 ms) → pressed (inset shadow, 60 ms) → disabled (opacity 0.4, no events)

**Class**: `widgets/components/button.py` → `class ZButton(QPushButton)`
**QSS**: `QPushButton`, `QPushButton[variant="primary"]`, etc.

### 6.2 `SidebarItem`

```
| 3 px bar │ icon 18 │ label 12 px        │
            12 px gap
```

**States**:
- default: text `--text-secondary`, bar transparent
- hover: bg `--bg-3`, text `--text-primary`
- selected: bg `--bg-2`, text `--accent`, bar `--accent` solid (current behavior — keep it)

**Class**: `sidebar.py` → `class Sidebar(QListWidget)`
**QSS**: `QListWidget#sidebar::item`, `::item:hover`, `::item:selected`

### 6.3 `Tab` (segmented)

```
[ selected: bg accent, text bg-0 ] [ hover: bg bg-3 ] [ default: bg bg-1 ]
```

Two styles:
- **Segmented** — used in `ProgramPanel` sub-tabs (current). No underline, full-bg fill on select.
- **Underline** — used in horizontal nav if added later. 2 px underline in `--accent`, 80 ms slide.

### 6.4 `Card`

```
┌─ bg-2, border subtle, radius 8 ─────────┐
│  padding 12 px                            │
│  [ optional title row ]                  │
│  [ body ]                                │
└──────────────────────────────────────────┘
```

Hover: border → `--border-strong`. Selected: border → `--accent`, bg → `--bg-3`.

### 6.5 `Fader`

```
   value
    │
  ╔═╪═╗
  ║ │ ║ ← track 4 px wide, bg-3
  ║ │ ║
  ║█│█║ ← handle 24 × 16 px, bg-elevated, border accent
  ║ │ ║
  ║ │ ║
  ║ │ ║
  ╚═╪═╝
   0   255  ← labels (mono, 10 px)
```

**Vertical** default. Horizontal variant for chase timeline.

- 200 ms ease-out on value change
- Right-click → reset to default (50 %)
- Double-click → enter numeric input
- Value popover on drag: shows `123 / 255` (current / max) in mono, bg `--bg-elevated`

### 6.6 `GridCell` (DMX channel grid)

```
┌────┬────┬────┬────┐
│ 000│ 064│ 128│ 255│  ← row 1
├────┼────┼────┼────┤
│ ...                       32 cols × 16 rows = 512 cells
└────┴────┴────┴────┘
```

- 28 × 22 px cell, 1 px gap
- Mono font, 10 px, 3-digit padded
- Striped every 8 rows: bg `--bg-1` / `--bg-2`
- Active: bg `--accent` (12 % alpha), text `--accent`
- Selected: border `--accent` 1 px

### 6.7 `Toast`

```
┌─ border 1 px color=status, bg bg-elevated ──┐
│  [●]  Message text — 11 px, primary     │
└──────────────────────────────────────────────┘
```

Pinned bottom-right of parent, 20 px from edges.

- Info / success: border + dot `--ok`
- Warning: border + dot `--warn`
- Error: border + dot `--err`
- In: 200 ms slide-up + fade-in
- Out: 150 ms fade-out
- Default duration: 3 s; errors: 5 s

**Class**: `widgets/toast.py` → `class Toast(QFrame)`

### 6.8 `StatusPill`

```
[ ●  LIVE ]    [ ○  PENDING ]    [ ■  ERROR ]    [ ·  IDLE ]
```

- bg `--bg-2`, border `--border-subtle`, radius 4 px, padding 2 px × 8 px
- Dot 8 px diameter, color = status
- Label 11 px caps, `--text-secondary`

Use in: connection status, fixture online/offline, scene playback state.

### 6.9 `ToolbarAction`

```
[ icon 20 ] [ optional label 12 px ]   ← fixed-height 32 px
```

- ghost button variant
- icon + label by default; icon-only at narrow widths

### 6.10 `NumericBadge`

```
┌──┐
│128│   ← mono, 11 px, 3-digit padded
└──┘
```

- bg `--bg-3`, border `--border-subtle`, radius 2 px
- Padding 1 px × 6 px
- Use for: channel values, counts, IDs

---

## 7. Layout Patterns

### 7.1 Main shell (current + minor improvements)

```
┌─ menubar (32 px) ────────────────────────────────────────────┐
├─ toolbar (40 px) ────────────────────────────────────────────┤
├─ sidebar (200 px) ──┬─ panel container (flex) ─────────────┤
│                     │  [ panel title ]                      │
│  Program            │  [ panel description ]                │
│  Fixture List       │  ┌─ card ──────────┐  ┌─ card ──────┐ │
│  Fixture Editor     │  │                 │  │             │ │
│  Settings           │  │                 │  │             │ │
│  About              │  └─────────────────┘  └─────────────┘ │
│                     │  [ 12-col grid continues… ]           │
├─ statusbar (24 px) ──────────────────────────────────────────┤
└──────────────────────────────────────────────────────────────┘
```

### 7.2 Console grid (proposed v5)

For panels with high data density (Mixer, Address), split into three vertical zones:

```
┌─ master (240 px) ──┬─ detail (flex) ─┬─ inspector (280 px) ─┐
│  list / bank       │  grid / timeline │  properties of sel  │
│                    │                  │                     │
│                    │                  │                     │
└────────────────────┴──────────────────┴─────────────────────┘
```

This is the grandMA3 influence. Build it for `MixerTab` and `AddressTab` first; expand from there.

### 7.3 Executor row (proposed v5, footer)

```
┌─ executor row (96 px) ───────────────────────────────────────┐
│ [1]│[2]│[3]│[4]│[5]│[6]│[7]│[8]│[9]│[10]  ← 10 fader slots  │
│  · │  ·│ ▶ │ · │  ·│  ·│  ·│  ·│  ·│  ·                       │
│ 50 │100│128│ 75│  0│200│ 50│  0│100│ 64  ← value (mono)     │
│      < page 1 / 4 >                                          │
└──────────────────────────────────────────────────────────────┘
```

Ten faders per page, four pages (40 cues / chases). Each slot has a Go button (spacebar) and a Flash button (B). This is the operator's "live" surface — keep it always visible.

### 7.4 Modal vs inline

| Use a modal | Use inline |
|-------------|-----------|
| Destructive action (delete project, emergency stop confirm) | Short form (new fixture, edit name) |
| Long form that benefits from focus (project settings) | Filter / search inputs |
| Help (F1) | Status displays |

Modal pattern: 480 px wide, bg `--bg-elevated`, border `--border-strong`, no shadow (flat). Close: Esc, click outside, explicit × button.

---

## 8. Motion & Feedback

### 8.1 Durations

| Token | Value | Use |
|-------|-------|-----|
| `--motion-instant` | 0 ms | DMX value updates, blackout, emergency stop |
| `--motion-fast` | 60 ms | Press feedback, tab swap |
| `--motion-base` | 120 ms | Tab cross-fade, list-item transition |
| `--motion-slow` | 200 ms | Toast slide-in, modal in |
| `--motion-slower` | 300 ms | (reserved for splash / onboarding) |

### 8.2 Easing

- Default: `cubic-bezier(0.4, 0.0, 0.2, 1)` (Material "standard")
- Out: `cubic-bezier(0.0, 0.0, 0.2, 1)`
- In: `cubic-bezier(0.4, 0.0, 1, 1)`

> [!WARNING]
> **No easing on DMX value updates.** Operators need real-time. The instant a slider moves, the fixture must respond. Do not wrap `set_channel_value()` in any animation.

### 8.3 When motion is forbidden

- During active audio playback (audio + animation = input lag)
- During active chase playback (cues are real-time)
- During Art-Net connection state changes (status text updates, no fade)

---

## 9. Data Density (grandMA3 influence)

### 9.1 Tables

- Row height: **24 px** (compact), **32 px** (default), **40 px** (touch)
- Header height: 32 px
- Cell padding: 6 px × 8 px
- Striping: bg `--bg-1` / `--bg-2` on alternate rows
- Selected row: bg `--accent-soft`, left border 2 px `--accent`
- Hover row: bg `--bg-3`

### 9.2 DMX grid specifics

- 3-digit zero-padded values: `000` `064` `128` `192` `255`
- Address shown as 1-based to user (1–512), 0-based internally
- Universe badges: small mono pill, top-left of grid, e.g. `[U1]`
- Channel hover: show fixture name in tooltip
- Right-click cell: context menu (Set to 0, 127, 255, Copy, Paste)

### 9.3 Status displays

- Always mono font for numbers
- Tabular figures (no proportional digits)
- Right-align numerics; left-align labels
- Color a number **only** when the value matters: red for out-of-range, green for in-range, amber for warning threshold

---

## 10. Accessibility

### 10.1 Keyboard

- **All** interactive elements reachable via Tab
- Visible focus ring: 2 px `--accent` outline, 2 px offset, never removed
- Standard shortcuts (current): Ctrl+O, Ctrl+S, Ctrl+Shift+S, Ctrl+1..5 (panels), F1, Esc, Space, B
- Shortcuts always documented in the F1 modal

### 10.2 Color independence

- Status conveyed by **shape + label**, not color alone:
  - `● LIVE` (filled dot) — not just green
  - `○ PENDING` (open dot) — not just amber
  - `■ ERROR` (filled square) — not just red
  - `· IDLE` (middle dot) — not just gray

### 10.3 Contrast

- All body text ≥ 4.5 : 1
- All UI controls (borders, icons) ≥ 3 : 1
- No information conveyed by color alone (see 10.2)

### 10.4 Touch + glove

- All hit targets ≥ 32 × 32 px
- Spacing between hit targets ≥ 8 px
- Faders accept drag from anywhere on the track, not just the handle

---

## 11. Voice & Text

### 11.1 Microcopy rules

- **Sentence case for everything except acronyms.** No Title Case in labels.
- **No exclamation marks** in status messages.
- **Verbs in present tense for actions**: "Save Project", "Open File", "Connect".
- **No emoji in our text** (see §5.3).
- **Truncation allowed**, but full value in tooltip.

### 11.2 Status messages

| State | Message pattern | Example |
|-------|-----------------|---------|
| Loading | `{action}…` | `Analyzing…` |
| Success | `{thing} {past-tense verb}` | `Saved default-show.zlx` |
| Warning | `{issue} — {consequence}` | `Output at 90% — clipping risk` |
| Error | `{thing} failed — {reason}` | `Connect failed — timeout` |
| Info | `{thing} {verb}` | `Loaded 12 fixtures` |

### 11.3 Numbers

- DMX values: `000`–`255`, 3 digits
- Percentages: `0%`–`100%`, no decimals unless `0.1%` precision matters
- Time: `MM:SS.ms` for cues; `H:MM:SS` for session duration
- File sizes: `MB` with 1 decimal (`245.0 MB`)

---

## 12. Anti-Patterns (the "Don'ts")

> [!CAUTION]
> PRs that introduce any of these will be rejected.

- ❌ **Emoji in chrome** — buttons, labels, menubar, statusbar, titles
- ❌ **Neon-on-black** — saturated RGB on pure black (gamer aesthetic)
- ❌ **Drop shadows on cards** — flat surfaces, border-defined
- ❌ **Gradients on interactive surfaces** — only on logos, splash
- ❌ **Icons larger than 24 px in toolbars** — looks childish, eats space
- ❌ **Title Case in labels** — sentence case always
- ❌ **Exclamation marks in status** — operators don't need cheering
- ❌ **Modal for short forms** — use inline editing
- ❌ **Animation on real-time data** — DMX, chase, blackout = 0 ms
- ❌ **Color-only signaling** — always pair with shape/label

---

## 13. Implementation Mapping (token → QSS)

A contributor can implement the design system by updating `styles.py` first, then panels. The mapping:

| Token | QSS selector | Notes |
|-------|--------------|-------|
| `--bg-0` | `QMainWindow`, `QWidget#centralWidget` | Use as `background-color` |
| `--bg-1` | `QMenuBar`, `QListWidget#sidebar`, `QStatusBar`, `QTabBar::tab` | |
| `--bg-2` | `QMenu`, `QListWidget#sidebar::item:selected`, `QHeaderView::section` | |
| `--bg-3` | hover surfaces, `QPushButton`, `QWidget#aboutCard` | |
| `--accent` | `QPushButton:hover` border, `QPushButton:pressed` bg, `QListWidget#sidebar::item:selected` text + bar, `QTabBar::tab:selected` bg | |
| `--warn` | toast warning border | |
| `--err` | toast error border, `QShortcut` for emergency stop | |
| `--text-primary` | body text everywhere | |
| `--text-muted` | `QStatusBar` color, `QLabel#dim` | |
| `--border-subtle` | all default 1 px borders | |

**Migration order**:
1. Update `styles.py` to add new tokens (keep old ones as aliases for one release)
2. Update `toast.py` to use new status dot chars (● ○ ■ ·)
3. Sweep `main_window.py` + `panels/*.py` for emoji → icon migration (Appendix A)
4. Add Lucide SVG pack to `icons.py`
5. Apply mono font class to all DMX / address / numeric displays
6. Add focus-ring QSS

---

## Appendix A — Emoji-to-Glyph Migration Map

> All instances of emoji in `zzluxora/` source as of v4.0. Each row must be removed in the design-system migration PR.

### A.1 `main_window.py`

| Line | Current | Replace with | Reason |
|------|---------|--------------|--------|
| 51 | `"📂  Open Project…"` | `"Open Project…"` + `folder-open` icon | folder glyph forbidden in chrome |
| 56 | `"💾  Save Project…"` | `"Save Project…"` + `save` icon | |
| 60 | `"💾  Save Project As…"` | `"Save Project As…"` + `save` icon | |
| 67 | `"❌  Exit"` | `"Exit"` + `x` icon | `×` unicode is fine as fallback |
| 80 | `"ℹ️  About zzluxora"` | `"About zzluxora"` + `info` icon | |
| 85 | `"⌨  Keyboard Shortcuts"` | `"Keyboard Shortcuts"` + `keyboard` icon | |
| 98 | `"📂 Load"` | `"Load"` + `folder-open` icon | |
| 102 | `"💾 Save"` | `"Save"` + `save` icon | |
| 172 | `"✓ Fixture saved"` | `"Fixture saved"` (success toast handles it) | |
| 179 | `"⚡ Ready"` | `"Ready"` + status pill `· IDLE` | |
| 189 | `"📋 {n} fixture(s)  •  🎛 0 patched"` | `"{n} fixtures · 0 patched"` (status pill for count) | |
| 200 | `f"⚡ {k.replace('_', ' ').title()}"` | `"{k.title()}"` (no prefix marker) | |
| 208 | `"📋 {n} fixture(s)  •  🎛 {p} patched"` | `"{n} fixtures · {p} patched"` | |
| 214 | `f"⏳ {action_name} — coming in a later milestone"` | `"{action_name} — coming soon"` | `…` status toast dot `○` |
| 238 | `f"✓ Loaded {path}"` | `"Loaded {path}"` | |
| 247 | `"✓ Saved"` | `"Saved"` | |
| 298 | `"⚫ Blackout"` | `"Blackout"` (toast already warns) | |

### A.2 `panels/`

| File | Line | Current | Replace with |
|------|------|---------|--------------|
| `address_tab.py` | 61 | `"🗑  Clear All Patches"` | `"Clear All Patches"` + `trash-2` icon |
| `address_tab.py` | 65 | `"✨  Auto-Patch Sequential"` | `"Auto-Patch Sequential"` + `wand-2` icon |
| `audio_tab.py` | 96 | `"🎵  Audio Analysis"` | `"Audio Analysis"` |
| `audio_tab.py` | 113 | `"📂  Load Audio File…"` | `"Load Audio File…"` + `file-audio` icon |
| `audio_tab.py` | 128 | `"🗑  Remove Song"` | `"Remove Song"` + `trash-2` icon |
| `audio_tab.py` | 269 | `f"📁 {filepath}"` | `{filepath}` (in mono) |
| `audio_tab.py` | 281 | `"⏳ Analyzing…"` | `"Analyzing…"` + `○` dot |
| `audio_tab.py` | 304 | `f"✓ {result['filename']} — …"` | `"{filename} — …"` |
| `audio_tab.py` | 311 | `"✗ Analysis failed"` | `"Analysis failed"` + `■` dot |
| `audio_tab.py` | 336 | `f"🎵  {filename}…"` | `"{filename}…"` |
| `audio_tab.py` | 382 | `f"📁 {song…}"` | `{song…}` (in mono) |
| `chase_tab.py` | 146 | `"✗ No artnet controller"` | `"No Art-Net controller"` + `■` dot |
| `chase_tab.py` | 149 | `"✗ Connect Art-Net in Output tab first"` | `"Connect Art-Net in Output tab first"` + `■` dot |
| `fixture_editor_panel.py` | 16 | `PANEL_NAME = "🔧  Fixture Editor"` | `PANEL_NAME = "Fixture Editor"` |
| `fixture_editor_panel.py` | 86 | `"✚  New (Clear)"` | `"New"` + `plus` icon |
| `fixture_editor_panel.py` | 90 | `"💾  Save Fixture"` | `"Save Fixture"` + `save` icon |
| `fixture_list_panel.py` | 16 | `PANEL_NAME = "📋  Fixture List"` | `PANEL_NAME = "Fixture List"` |
| `fixture_list_panel.py` | 28 | `"🔄  Reload"` | `"Reload"` + `refresh-cw` icon |
| `fixture_list_panel.py` | 32 | `"🗑  Delete Selected"` | `"Delete"` + `trash-2` icon |
| `fixture_list_panel.py` | 39 | `"💡 Tip: …"` | `"Tip: …"` |
| `mixer_tab.py` | 26 | `"🎚  512-Channel DMX Mixer"` | `"512-Channel DMX Mixer"` |
| `mixer_tab.py` | 88 | `"🔄  Refresh from Art-Net"` | `"Refresh from Art-Net"` + `refresh-cw` icon |
| `output_tab.py` | 22 | `"📡  Art-Net DMX Output"` | `"Art-Net DMX Output"` |
| `output_tab.py` | 55 | `"🔌  Connect"` | `"Connect"` + `plug` icon |
| `output_tab.py` | 63 | `"⏹  Disconnect"` | `"Disconnect"` + `plug-zap` icon |
| `output_tab.py` | 66 | `"⚫  Blackout"` | `"Blackout"` + `moon` icon |
| `output_tab.py` | 84 | `"✗ No artnet controller"` | `"No Art-Net controller"` + `■` dot |
| `output_tab.py` | 95 | `f"✗ Failed: …"` | `"Failed: …"` + `■` dot |
| `output_tab.py` | 107 | `"⚫ Blackout sent"` | `"Blackout sent"` |
| `preview_tab.py` | 27 | `"👁  Live Preview"` | `"Live Preview"` |
| `program_panel.py` | 24 | `PANEL_NAME = "🎛️  Program"` | `PANEL_NAME = "Program"` |
| `program_panel.py` | 90 | `f"⏳ {label} — coming in a later milestone"` | `"{label} — coming soon"` + `○` dot |
| `scenes_tab.py` | 29 | `"🎬  Scene Generator"` | `"Scene Generator"` |
| `scenes_tab.py` | 38 | `"🔄  Regenerate Scenes"` | `"Regenerate Scenes"` + `refresh-cw` icon |
| `settings_panel.py` | 8 | `PANEL_NAME = "⚙️  Settings"` | `PANEL_NAME = "Settings"` |
| `settings_panel.py` | 34 | `"💡 Settings persist via QSettings on app close."` | `"Settings persist via QSettings on app close."` |

### A.3 `widgets/`

| File | Line | Current | Replace with |
|------|------|---------|--------------|
| `widgets/toast.py` | 19 | `icon_map = {"info":"✓", "success":"✓", "warning":"⚠", "error":"✗"}` | `icon_map = {"info":"●", "success":"●", "warning":"○", "error":"■"}` (filled/outline) |
| `widgets/onboarding.py` | 34 | `"🎬  Welcome to zzluxora v4.0"` | `"Welcome to zzluxora v4.0"` + `sparkles` icon (decorative exception, one-time) |
| `widgets/help_modal.py` | 29 | `"⌨  Keyboard Shortcuts"` | `"Keyboard Shortcuts"` + `keyboard` icon |

### A.4 Other

| File | Line | Current | Replace with |
|------|------|---------|--------------|
| `font_loader.py` | 70 | `status = "✓" if ok else "✗"` | `status = "OK" if ok else "FAIL"` (this is a log, but consistent) |

### A.5 Total

~50 emoji instances across 16 files. Estimated migration effort: **1 PR, ~2 hours**.

---

## Appendix B — Quick Reference Card

```
SURFACE   bg-0 #0a0a0a · bg-1 #121212 · bg-2 #181818 · bg-3 #1f1f1f
BORDER    subtle #2a2a2a · strong #3a3a3a
TEXT      primary #ededed · secondary #a0a0a0 · muted #6a6a6a
ACCENT    #2ecc71 (action + active) · hover #27ae60 · soft #1d3a2a
STATUS    ok #2ecc71 · warn #f39c12 · err #e74c3c · info #4aa3ff
RADIUS    sm 2 · md 4 · lg 8
SPACE     1=4 2=8 3=12 4=16 5=24 6=32 px
MOTION    instant 0 (DMX) · fast 60 · base 120 · slow 200 ms
FONT UI   Segoe UI Variable / Inter
FONT MONO JetBrains Mono / Cascadia Code
ICONS     Lucide 1.5 px stroke · 16/20/24 px
STATUS    ● LIVE · ○ PENDING · ■ ERROR · · IDLE
EMOJI     forbidden in chrome · ●○■· allowed as markers
```

---

*End of `design.md` v1.0. Apply this doc with care — it is the contract.*
