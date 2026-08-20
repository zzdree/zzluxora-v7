"""
ColorMixer (v6 Phase 3B) — blend DRGBW from up to 4 analyzed songs.

Modes:
  additive  — weighted average (D_blend = sum(w_i * D_i) / sum(w_i))
  override  — highest-weight slot wins, others ignored
  average   — equal weights across active slots (ignores user weights)

Each slot: song_id (must exist in songs dict) + weight (0.0-1.0).
Slots with weight 0 or empty song_id are inactive.

Returns blended DRGBW as [r, g, b, w, dimmer] (0-255 ints) or None if no active slots.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MixerSlot:
    song_id: str = ""
    weight: float = 0.0  # 0.0 - 1.0


@dataclass
class ColorMixer:
    slots: List[MixerSlot] = field(default_factory=lambda: [MixerSlot() for _ in range(4)])
    mode: str = "additive"  # additive | override | average

    MODE_ADDITIVE = "additive"
    MODE_OVERRIDE = "override"
    MODE_AVERAGE = "average"

    def blend(self, songs: Dict[str, dict]) -> Optional[List[int]]:
        """
        Blend DRGBW from active slots.

        songs: {song_id: result_dict with 'global_color': {rgbw: [r,g,b,w], dimmer: int}}
        Returns [r, g, b, w, dimmer] (0-255 ints) or None if no active slots.
        """
        active = []
        for s in self.slots:
            if not s.song_id or s.weight <= 0:
                continue
            if s.song_id not in songs:
                continue
            active.append((s, songs[s.song_id]))

        if not active:
            return None

        if self.mode == self.MODE_OVERRIDE:
            active.sort(key=lambda x: x[0].weight, reverse=True)
            _, song = active[0]
            gc = song["global_color"]
            rgbw = gc["rgbw"]
            return [int(rgbw[0]), int(rgbw[1]), int(rgbw[2]), int(rgbw[3]), int(gc["dimmer"])]

        if self.mode == self.MODE_AVERAGE:
            n = len(active)
            r = sum(song["global_color"]["rgbw"][0] for _, song in active) / n
            g = sum(song["global_color"]["rgbw"][1] for _, song in active) / n
            b = sum(song["global_color"]["rgbw"][2] for _, song in active) / n
            w = sum(song["global_color"]["rgbw"][3] for _, song in active) / n
            d = sum(song["global_color"]["dimmer"] for _, song in active) / n
            return [int(r), int(g), int(b), int(w), int(d)]

        # additive: weighted average
        total_w = sum(s.weight for s, _ in active)
        if total_w <= 0:
            return None
        r = sum(song["global_color"]["rgbw"][0] * s.weight for s, song in active) / total_w
        g = sum(song["global_color"]["rgbw"][1] * s.weight for s, song in active) / total_w
        b = sum(song["global_color"]["rgbw"][2] * s.weight for s, song in active) / total_w
        w = sum(song["global_color"]["rgbw"][3] * s.weight for s, song in active) / total_w
        d = sum(song["global_color"]["dimmer"] * s.weight for s, song in active) / total_w
        return [int(r), int(g), int(b), int(w), int(d)]

    def active_count(self) -> int:
        return sum(1 for s in self.slots if s.song_id and s.weight > 0)
