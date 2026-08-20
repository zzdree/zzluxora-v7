"""
Fixture Types (v6 Phase 6) — channel layout templates for the Fixture Editor.

Each template is a list of channel labels in order. Selecting a template in
the Fixture Editor auto-fills the channel_map with these labels.

Templates cover the most common worship/venue fixtures:
  - PAR (4/5/6/7 channels)
  - Bar (4/8 channels)
  - Moving Head (8/12 channels)
  - Strobe (2 channels)
  - Custom (user defines all channels manually)
"""
from __future__ import annotations
from typing import Dict, List


FIXTURE_TYPES: Dict[str, List[str]] = {
    "PAR 4ch (RGBW)":      ["Red", "Green", "Blue", "White"],
    "PAR 5ch (DRGBW)":     ["Dimmer", "Red", "Green", "Blue", "White"],
    "PAR 6ch (RGBWAU)":    ["Red", "Green", "Blue", "White", "Amber", "UV"],
    "PAR 7ch (DRGBWAU)":   ["Dimmer", "Red", "Green", "Blue", "White", "Amber", "UV"],
    "Bar 4ch (RGBW)":      ["Red", "Green", "Blue", "White"],
    "Bar 8ch (DRGBW+Strobe)": ["Dimmer", "Red", "Green", "Blue", "White", "Strobe", "Program", "Speed"],
    "Moving 8ch":          ["Red", "Green", "Blue", "White", "Dimmer", "Strobe", "Pan", "Tilt"],
    "Moving 12ch":         ["Red", "Green", "Blue", "White", "Dimmer", "Strobe",
                            "Pan", "Pan_fine", "Tilt", "Tilt_fine", "Function", "Reset"],
    "Strobe 2ch":          ["Dimmer", "Strobe"],
    "Custom":              [],  # user defines all channels manually
}


# Built-in labels considered "default" — used to detect non-default user edits
# when prompting to overwrite on type change.
BUILTIN_CHANNEL_LABELS: List[str] = [
    "Dimmer", "Red", "Green", "Blue", "White",
    "Amber", "UV", "Program", "Speed", "Strobe",
    "Pan", "Tilt", "Pan_fine", "Tilt_fine", "Function", "Reset",
]


# Phase 16: high-level role per channel — used as 3rd column in Fixture Editor.
# Maps each channel to a DMX concept (intensity vs color vs position vs beam, etc).
CHANNEL_ROLES: List[str] = [
    "Intensity",   # dimmer, strobe
    "Color",       # red, green, blue, white, amber, uv
    "Position",    # pan, tilt (and fine variants)
    "Beam",        # zoom, focus, iris
    "Effect",      # gobo, prism, program, speed, macro
    "Function",    # reset, mode
    "Other",
]


def infer_role(label: str) -> str:
    """Map a channel label to its high-level role (case-insensitive)."""
    if not label:
        return "Other"
    l = label.lower()
    if l in ("dimmer", "strobe", "intensity"):
        return "Intensity"
    if l in ("red", "green", "blue", "white", "amber", "uv", "color"):
        return "Color"
    if "pan" in l or "tilt" in l:
        return "Position"
    if any(k in l for k in ("zoom", "focus", "iris")):
        return "Beam"
    if any(k in l for k in ("gobo", "prism", "program", "speed", "macro")):
        return "Effect"
    if any(k in l for k in ("reset", "function", "mode")):
        return "Function"
    return "Other"


def get_type_channels(type_name: str) -> List[str]:
    """Return the channel label list for a given type name, or empty list."""
    return list(FIXTURE_TYPES.get(type_name, []))


def get_type_count() -> int:
    """Return the total number of fixture types (excluding Custom)."""
    return sum(1 for k in FIXTURE_TYPES if k != "Custom")
