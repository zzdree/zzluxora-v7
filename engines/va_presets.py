"""
VAPreset — v6 custom V-A → HSV mapping override.

Default math model §[4] uses fixed hue per quadrant. Presets let user override
per-quadrant hue base + range, chroma offset, and S/V blend weights.

Storage: JSON in %APPDATA%/zzluxora/presets/  (per-user, survives reinstall).
Default preset is implicit (returns VAPreset() defaults, never written to disk).
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, asdict
from typing import List


PRESETS_DIR_NAME = "presets"
DEFAULT_PRESET_NAME = "Default Praise"


@dataclass
class VAPreset:
    """Custom V-A → HSV mapping."""
    name: str = DEFAULT_PRESET_NAME
    # Hue base per quadrant (degrees)
    q1_hue_base: float = 30.0    # Q1 Praise warm (orange-amber)
    q2_hue_base: float = 270.0   # Q2 Intens purple
    q3_hue_base: float = 200.0   # Q3 Kontemplatif blue
    q4_hue_base: float = 150.0   # Q4 Damai cyan/green
    # Hue range (V variation multiplier)
    q1_hue_range: float = 60.0
    q2_hue_range: float = 120.0
    q3_hue_range: float = 120.0
    q4_hue_range: float = 100.0
    # Chroma offset (degrees per chroma_peak index from C)
    chroma_offset_deg: float = 5.0
    # S blend: S = alpha * A + (1 - alpha) * |2V - 1|
    alpha_sat: float = 0.60
    # V blend: V_hsv = beta * rms_norm + (1 - beta) * A
    beta_val: float = 0.50
    # Brightness floor
    v_min: float = 0.10


def get_presets_dir() -> str:
    """User presets dir: %APPDATA%/zzluxora/presets/"""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "zzluxora", PRESETS_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def list_presets() -> List[str]:
    """Return list of saved preset names (without .json)."""
    path = get_presets_dir()
    if not os.path.isdir(path):
        return []
    return sorted([
        f[:-5] for f in os.listdir(path)
        if f.endswith(".json")
    ])


def load_preset(name: str) -> VAPreset:
    """Load preset by name. Returns defaults if name is default or not found."""
    if not name or name == DEFAULT_PRESET_NAME:
        return VAPreset()
    path = os.path.join(get_presets_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return VAPreset(name=name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["name"] = name
        return VAPreset(**data)
    except (OSError, json.JSONDecodeError, TypeError):
        return VAPreset(name=name)


def save_preset(preset: VAPreset) -> None:
    """Save preset to disk. Default preset is implicit (not saved)."""
    if preset.name == DEFAULT_PRESET_NAME:
        return  # never overwrite implicit default
    path = os.path.join(get_presets_dir(), f"{preset.name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(preset), f, indent=2)


def delete_preset(name: str) -> bool:
    """Delete preset file. Returns True if removed."""
    if name == DEFAULT_PRESET_NAME:
        return False
    path = os.path.join(get_presets_dir(), f"{name}.json")
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False


def apply_preset(preset: VAPreset, V: float, A: float,
                 chroma_peak: int = 6, rms_norm: float = 0.5) -> tuple:
    """
    Apply VAPreset to compute HSV. Returns (H, S, V_hsv).

    Mirrors color_mapping.va_to_hsv() but uses preset's hue ranges + offsets.
    """
    # Hue base per quadrant
    if V > 0.5 and A > 0.5:                # Q1
        H_base = preset.q1_hue_base + (V - 0.5) * preset.q1_hue_range
    elif V <= 0.5 and A > 0.5:              # Q2
        H_base = preset.q2_hue_base + (0.5 - V) * preset.q2_hue_range
    elif V <= 0.5 and A <= 0.5:             # Q3
        H_base = preset.q3_hue_base + (0.5 - V) * preset.q3_hue_range
    else:                                   # Q4
        H_base = preset.q4_hue_base + (V - 0.5) * preset.q4_hue_range

    # Chroma offset
    H = (H_base + (chroma_peak - 6) * preset.chroma_offset_deg) % 360

    # Saturation
    S = preset.alpha_sat * A + (1.0 - preset.alpha_sat) * abs(2 * V - 1)
    S = max(0.0, min(1.0, S))

    # Value
    V_hsv = preset.beta_val * rms_norm + (1.0 - preset.beta_val) * A
    V_hsv = max(preset.v_min, min(1.0, V_hsv))

    return round(H, 2), round(S, 4), round(V_hsv, 4)
