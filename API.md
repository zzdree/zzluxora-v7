# API Reference — zzluxora v7.0

Public API for engines, fixture manager, and project I/O. UI panels are not part of the public API.

**12 engine modules** · `engines.audio_engine`, `engines.analyze_pipeline`, `engines.color_mapping`, `engines.curve_lut`, `engines.color_mixer`, `engines.va_presets`, `engines.scene_generator`, `engines.program`, `engines.chase`, `engines.fixture_types`, `engines.artnet_sender`, `engines.__init__`.

---

## `engines.audio_engine`

### `extract_features(audio_path: str) -> dict`
Extract audio features using librosa.

**Returns:**
```python
{
    'duration': float,           # seconds
    'tempo': float,              # BPM
    'beat_times': list[float],   # seconds
    'rms_mean': float,           # 0-1
    'rms_times': list[float],
    'rms_values': list[float],
    'sc_mean': float,            # spectral centroid (Hz)
    'sc_times': list[float],
    'sc_values': list[float],
    'mfcc1_mean': float,
    'chroma_major': float,       # 0-1 (chroma major key energy ratio)
    'chroma_peak': int,          # 0-11 (chroma bin)
    'chroma_mean': list[float],  # 12 bins
    'onset_rate': float,         # onsets per second
    'sb_mean': float,            # spectral bandwidth (Hz)
}
```

### `segment_song(audio_path: str, num_segments: int = None) -> list[dict]`
Segment song into structural sections using self-similarity matrix.

**Returns:** list of `Segment`:
```python
{
    'index': int,
    'label': str,    # 'intro' | 'verse' | 'chorus' | 'bridge' | 'outro'
    'start': float,  # seconds
    'end': float,
    'duration': float,
    'rms': float,
    'sc': float,
}
```

### `compute_valence_arousal(features: dict) -> tuple[float, float]`
Compute (V, A) from normalized features. Returns (V, A) in [0, 1].

### `va_to_hsv(V: float, A: float, chroma_peak: int = 6, rms_norm: float = 0.5) -> tuple[float, float, float]`
Map (V, A) to (H, S, V) in HSV color space.

### `hsv_to_rgb(H: float, S: float, V: float) -> tuple[float, float, float]`
Standard HSV → RGB conversion.

### `rgb_to_rgbw(R: float, G: float, B: float) -> tuple[float, float, float, float]`
Extract white channel from RGB. Returns (R', G', B', W) in [0, 1].

### `full_pipeline(features: dict) -> dict`
Run full audio → RGBW pipeline. Returns:
```python
{
    'valence': float,
    'arousal': float,
    'hue': float, 'saturation': float, 'value': float,
    'rgb': list[float],     # 3 elements
    'rgbw': list[int],      # 4 elements (0-255)
    'dimmer': int,          # 0-255
    'drgbw': list[int],     # 5 elements (Dimmer + RGBW)
    'hex': str,             # '#rrggbb'
}
```

---

## `engines.analyze_pipeline` (skripsi math — RELEASE BLOCKER)

### `class AnalyzePipeline`
Encapsulates the full audio → RGBW pipeline as a stateful object. Used by `tests/test_math_model.py`.

#### `__init__(preset: str = "default")`
Initialize with a V/A preset (see `va_presets.py`).

#### `process(audio_features: dict) -> dict`
Run pipeline on features. Returns the `full_pipeline()` output (above).

#### `validate_10k_reasons(features: dict) -> bool`
Validate pipeline against the "10,000 Reasons (Bless the Lord)" reference song (used in skripsi).

### `quick_analyze(audio_path: str) -> dict`
One-shot convenience: `extract_features()` + `AnalyzePipeline.process()`.

---

## `engines.color_mapping`

### `class ColorMapping`
HSV → RGB → RGBW with curve LUT.

#### `apply_curve(value: float, curve: str = "linear") -> float`
Apply lookup-table curve. Curves: `linear` | `exp` | `log` | `s-curve` (see `curve_lut.py`).

#### `map_hsv_to_rgbw(H: float, S: float, V: float, dimmer: int = 255) -> dict`
HSV → RGB → RGBW with dimmer applied. Returns:
```python
{'r': int, 'g': int, 'b': int, 'w': int, 'dimmer': int, 'hex': str}
```

#### `map_scene_to_fixtures(scene: dict, fixture_manager) -> list[list[int]]`
Map a Scene to DMX frames for all patched fixtures. Returns list of 512-channel frames.

---

## `engines.curve_lut`

### `class CurveLUT`
Lookup-table for value curves.

#### `linear(x: float) -> float`
#### `exp(x: float, k: float = 2.0) -> float`
#### `log(x: float, k: float = 2.0) -> float`
#### `s_curve(x: float) -> float`

All take x in [0, 1], return y in [0, 1].

---

## `engines.color_mixer`

### `mix(rgbw_a: list[int], rgbw_b: list[int], weight: float = 0.5) -> list[int]`
Linear blend of two RGBW colors. `weight=0` → a, `weight=1` → b.

### `shift_hue(rgbw: list[int], delta: int) -> list[int]`
Shift hue by `delta` degrees (0-360).

### `dim(rgbw: list[int], dimmer: int) -> list[int]`
Apply dimmer (0-255) to RGBW.

---

## `engines.va_presets`

### `PRESETS: dict[str, dict]`
Available presets:
- `default` — neutral V/A mapping
- `energetic` — high arousal
- `calm` — low arousal
- `worship` — skripsi preset (for "10,000 Reasons")

Each preset is `{ 'v_bias': float, 'a_bias': float, 's_min': float, ... }`.

---

## `engines.scene_generator`

### `generate_scenes(segments: list[dict], audio_features: dict, max_scenes: int = 4) -> list[dict]`
Generate scenes from audio segments. Each scene has fade_in, fade_out, color palette.

**Returns:** list of `Scene`:
```python
{
    'id': int,
    'segment_index': int,
    'label': str,        # 'intro' | 'verse' | etc
    'start': float,
    'end': float,
    'fade_in': float,    # ms
    'fade_out': float,   # ms
    'fade_ms': int,      # current fade (overridable via UI)
    'color': {'r': int, 'g': int, 'b': int, 'w': int, 'hex': str},
    'dmx': {'r': int, 'g': int, 'b': int, 'w': int},
    'type': str,         # segment label
}
```

### `apply_to_fixtures(scene: dict, fixture_manager) -> None`
Broadcast a scene to all patched fixtures via `fixture_manager.broadcast()`.

---

## `engines.program`

### `class Program`
Multi-track cue sequencer.

#### `__init__(name: str)`
#### `add_cue(time_ms: int, target: str, action: str, color: dict) -> int`
Add a cue. Returns cue_id.

#### `remove_cue(cue_id: int) -> None`
#### `get_cues_at(time_ms: int) -> list[dict]`
Get all cues that fire at a given time (with ±50 ms tolerance).
#### `to_dict() / from_dict(...)` for serialization

---

## `engines.chase`

### `class Chase`
Chase sequencer with direction + loop.

#### `__init__(name: str, direction: str = "forward", loop: bool = True)`
- `direction`: `forward` | `backward` | `ping-pong` | `random`
- `loop`: `True` to loop at end

#### `add_scene(scene: dict, hold_ms: int = 500) -> None`
#### `tick() -> dict | None`
Advance chase by 1 frame. Returns current scene or None at end (or wraps if `loop`).

#### `reset() -> None`
#### `play() / pause() / stop() -> None`
#### `is_running -> bool`
#### `current_scene -> dict | None`

---

## `engines.fixture_types`

### `FIXTURE_TYPES: dict[str, list[str]]`
10 built-in type templates (name → channel labels):

| Key | Channels | Typical use |
| --- | -------- | ----------- |
| `PAR 4ch` | 4 | `R`, `G`, `B`, `W` |
| `PAR 5ch` | 5 | `Dimmer`, `R`, `G`, `B`, `W` |
| `PAR 6ch` | 6 | `R`, `G`, `B`, `W`, `Amber`, `UV` |
| `PAR 7ch` | 7 | `Dimmer`, `R`, `G`, `B`, `W`, `Strobe`, `Macro` |
| `Bar 4ch` | 4 | `R`, `G`, `B`, `W` (LED bar) |
| `Bar 8ch` | 8 | `Dimmer`, `R`, `G`, `B`, `W`, `Strobe`, `Macro`, `Speed` |
| `Moving 8ch` | 8 | `Pan`, `Tilt`, `Dimmer`, `R`, `G`, `B`, `W`, `Gobo` |
| `Moving 12ch` | 12 | `Pan`, `Tilt`, `Pan_Fine`, `Tilt_Fine`, `Dimmer`, `R`, `G`, `B`, `W`, `Strobe`, `Gobo`, `Speed` |
| `Strobe 2ch` | 2 | `Dimmer`, `Rate` |
| `Custom` | dynamic | user-defined |

### `match_template(name: str) -> list[str] | None`
Look up channel labels by fixture name (case-insensitive substring match).

---

## `engines.artnet_sender`

### `class ArtNetController`
Wrapper around `stupidArtnet` with frame counter + Live mode.

#### `__init__(target_ip: str = "127.0.0.1", universe: int = 0, fps: int = 30)`
#### `connect(target_ip: str, universe: int, fps: int) -> dict`
Connect. Returns `{'ok': bool, 'error': str | None}`. Also `reset_counter()`.

#### `disconnect() -> None`
Close socket.

#### `send_frame(channel_data: list[int]) -> None`
Send 512-channel DMX frame. Increments `frames_sent`.

#### `blackout() -> None`
Send all-zero frame.

#### `reset_counter() -> None`
Reset `frames_sent` to 0.

#### `get_status() -> dict`
Returns:
```python
{
    'connected': bool,
    'target_ip': str,
    'universe': int,
    'fps': int,
    'frames_sent': int,
}
```

#### Properties
- `is_running: bool` — socket state
- `current_dmx: list[int]` — last sent frame (or last received?)
- `frames_sent: int` — read-only

---

## `fixture_manager`

### `class FixtureManager`
Global state singleton.

#### Attributes
- `fixtures: list[Fixture]`
- `address_map: dict[tuple[int, int], FixtureIndex]`  # (universe, channel) → fixture
- `songs: dict[str, AudioFeatures]`
- `artnet_controller: ArtNetController`
- `programs: list[Program]`
- `chases: list[Chase]`
- `project_name: str`
- `project_path: str | None`
- `current_song_id: str | None`

#### Fixture / address methods
- `add_fixture(name, channels, type="Custom", manufacturer="") -> int`
- `remove_fixture(name) -> bool`
- `list_fixtures() -> list[str]`
- `get_fixture(name) -> dict`
- `patch(address: int, fixture_name: str) -> tuple[bool, str]`
- `unpatch(address: int) -> tuple[bool, str]`
- `clear_all() -> None`
- `get_address_map() -> dict[int, dict]`

#### Library methods
- `save_fixture(data: dict) -> tuple[bool, str]`
- `load_fixture(name: str) -> dict | None`
- `list_library() -> list[str]`

#### Song methods
- `load_song(path: str) -> str`  # returns song_id
- `remove_song(song_id: str) -> None`
- `set_current_song(song_id: str) -> None`

#### Output methods
- `broadcast(scene: dict) -> None`  # sends to all patched fixtures
- `blackout() -> None`
- `set_dmx_value(channel: int, value: int) -> None`

#### Serialization
- `to_dict() -> dict`
- `from_dict(data: dict) -> None`

---

## `panels.project_io`

### `save_zlx(fixture_manager: FixtureManager, path: str) -> tuple[bool, str]`
Save state to `.zlx` file (JSON). Returns `(ok, message)`.

### `load_zlx(fixture_manager: FixtureManager, path: str) -> tuple[bool, str]`
Load state from `.zlx` file. Validates schema version, migrates from older versions if needed.

### `get_save_path(parent: QWidget, default_name: str = "show.zlx") -> str | None`
Show QFileDialog.getSaveFileName. Returns path or None.

### `get_open_path(parent: QWidget) -> str | None`
Show QFileDialog.getOpenFileName. Returns path or None.

---

## `.zlx` File Schema

```json
{
  "version": "3.0",
  "project_name": "MyShow",
  "fixtures": [
    {
      "id": 1,
      "name": "Front Left",
      "type": "PAR 5ch",
      "manufacturer": "Generic",
      "channels": 5,
      "channel_map": [
        {"index": 0, "label": "Dimmer", "type": "dimmer"},
        {"index": 1, "label": "R", "type": "color"},
        {"index": 2, "label": "G", "type": "color"},
        {"index": 3, "label": "B", "type": "color"},
        {"index": 4, "label": "W", "type": "color"}
      ]
    }
  ],
  "address_map": {
    "1": {"fixture_name": "Front Left", "start_address": 1}
  },
  "songs": {
    "song_1": {
      "path": "C:/music/song.wav",
      "filename": "song.wav",
      "features": { /* extract_features() output */ },
      "segments": [ /* segment_song() output */ ],
      "va": [0.6, 0.7],
      "rgbw": [255, 0, 0, 0],
      "scenes": [ /* generate_scenes() output */ ]
    }
  },
  "artnet": {"target_ip": "127.0.0.1", "universe": 0, "fps": 30},
  "programs": [],
  "chases": [],
  "created_at": "2026-06-14T01:00:00Z",
  "updated_at": "2026-06-14T01:00:00Z"
}
```

**Backward compat**: loaders accept v3.0+ and migrate on load.

---

## `tests.test_math_model`

19/19 tests as **RELEASE BLOCKER** (derived from skripsi BAB 3). Run with:
```powershell
python tests/test_math_model.py
```

Sections:
1. 10k Reasons validation (audio → RGBW)
2. V/A quadrant mapping
3. HSV → RGB conversion
4. RGB → RGBW extraction
5. Chase timing
6. Pattern selection

All must pass before any release.

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) — module structure
- [DEVELOPMENT.md](DEVELOPMENT.md) — how to extend
- [markdowns/app_feedback.md](../markdowns/app_feedback.md) — feedback audit
