"""
Chase (v6 Phase 5) — multi-step chase with per-step direction + pattern.

A Chase is distinct from a Program:
  - Program = whole-song timeline (each step is a color state for the room)
  - Chase = multi-fixture sequence (each step has a direction for the pattern)

Data model:
  - Chase: named container of ChaseSteps
  - ChaseStep: one color/pattern state with start/duration + direction

Storage: %APPDATA%/zzluxora/chases/<name>.json
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional
import os
import json
import time


DIRECTIONS = ["forward", "reverse", "ping_pong"]


@dataclass
class ChaseStep:
    index: int
    start: float          # seconds within the chase
    duration: float       # seconds
    drgbw: dict           # {r, g, b, w, dimmer} each 0-255
    pattern: str = "all_on"
    direction: str = "forward"  # forward | reverse | ping_pong
    label: str = ""

    def end(self) -> float:
        return self.start + self.duration

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ChaseStep":
        return cls(
            index=d.get("index", 0),
            start=float(d.get("start", 0)),
            duration=float(d.get("duration", 1.0)),
            drgbw=dict(d.get("drgbw", {"r": 0, "g": 0, "b": 0, "w": 0, "dimmer": 0})),
            pattern=d.get("pattern", "all_on"),
            direction=d.get("direction", "forward"),
            label=d.get("label", ""),
        )


@dataclass
class Chase:
    name: str
    steps: List[ChaseStep] = field(default_factory=list)
    loop: bool = True
    default_direction: str = "forward"
    song_id: str = ""
    created: str = ""
    modified: str = ""
    notes: str = ""

    def total_duration(self) -> float:
        if not self.steps:
            return 0.0
        return max(s.end() for s in self.steps)

    def step_at(self, t: float) -> Optional[ChaseStep]:
        for s in self.steps:
            if s.start <= t < s.end():
                return s
        return None

    def add_step(self, start: float, duration: float, drgbw: dict,
                 pattern: str = "all_on", direction: str = "forward",
                 label: str = "") -> ChaseStep:
        idx = len(self.steps)
        step = ChaseStep(
            index=idx,
            start=start,
            duration=duration,
            drgbw=dict(drgbw),
            pattern=pattern,
            direction=direction,
            label=label or f"Step {idx + 1}",
        )
        self.steps.append(step)
        self._touch()
        return step

    def remove_step(self, index: int) -> bool:
        if index < 0 or index >= len(self.steps):
            return False
        del self.steps[index]
        for i, s in enumerate(self.steps):
            s.index = i
        self._touch()
        return True

    def move_step(self, index: int, new_start: float, new_duration: float = None) -> bool:
        if index < 0 or index >= len(self.steps):
            return False
        self.steps[index].start = new_start
        if new_duration is not None:
            self.steps[index].duration = new_duration
        self._touch()
        return True

    def sort_steps(self) -> None:
        self.steps.sort(key=lambda s: s.start)
        for i, s in enumerate(self.steps):
            s.index = i
        self._touch()

    def _touch(self) -> None:
        self.modified = time.strftime("%Y-%m-%dT%H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "loop": self.loop,
            "default_direction": self.default_direction,
            "song_id": self.song_id,
            "created": self.created,
            "modified": self.modified,
            "notes": self.notes,
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Chase":
        return cls(
            name=d.get("name", "Untitled"),
            steps=[ChaseStep.from_dict(s) for s in d.get("steps", [])],
            loop=d.get("loop", True),
            default_direction=d.get("default_direction", "forward"),
            song_id=d.get("song_id", ""),
            created=d.get("created", ""),
            modified=d.get("modified", ""),
            notes=d.get("notes", ""),
        )


# ── Storage ──────────────────────────────────────────────
def _chases_dir() -> str:
    d = os.path.join(os.path.expandvars("%APPDATA%"), "zzluxora", "chases")
    os.makedirs(d, exist_ok=True)
    return d


def list_chases() -> List[str]:
    d = _chases_dir()
    if not os.path.isdir(d):
        return []
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(d)
        if f.endswith(".json")
    )


def save_chase(chase: Chase) -> None:
    if not chase.created:
        chase.created = time.strftime("%Y-%m-%dT%H:%M:%S")
    chase._touch()
    path = os.path.join(_chases_dir(), f"{chase.name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chase.to_dict(), f, indent=2)


def load_chase(name: str) -> Optional[Chase]:
    path = os.path.join(_chases_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return Chase.from_dict(json.load(f))


def delete_chase(name: str) -> bool:
    path = os.path.join(_chases_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return False
    os.remove(path)
    return True


# ── Auto-generate from song scenes ──────────────────────
def chase_from_song_scenes(song_id: str, song_result: dict,
                            chase_name: str = None,
                            default_direction: str = "forward",
                            loop: bool = True) -> Chase:
    """Convert an analyzed song's scenes into a Chase (one step per scene)."""
    name = chase_name or f"{song_result.get('filename', song_id)} (chase)"
    c = Chase(
        name=name,
        loop=loop,
        default_direction=default_direction,
        song_id=song_id,
    )
    for scene in song_result.get("scenes", []):
        dmx = scene.get("dmx", {})
        r = int(dmx.get("r", 0))
        g = int(dmx.get("g", 0))
        b = int(dmx.get("b", 0))
        w = int(dmx.get("w", 0))
        # Dimmer from scene intensity, fallback to 200
        dim = int(scene.get("intensity", 200))
        start = float(scene.get("start", 0))
        end = float(scene.get("end", start + 1))
        c.add_step(
            start=start,
            duration=max(0.1, end - start),
            drgbw={"r": r, "g": g, "b": b, "w": w, "dimmer": dim},
            pattern=scene.get("pattern", "all_on"),
            direction=default_direction,
            label=scene.get("type", "") or scene.get("label", ""),
        )
    return c
