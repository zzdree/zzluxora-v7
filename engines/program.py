"""
Program (v6 Phase 4) — sequence of Steps with DRGBW + pattern + transition.

Data model:
  - Program: named container of Steps (flat, no sequence hierarchy)
  - Step: one color/pattern state with start/end time and transition

Storage: %APPDATA%/zzluxora/programs/<name>.json
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional
import os
import json
import time


@dataclass
class Step:
    index: int
    start: float          # seconds
    end: float            # seconds
    drgbw: dict           # {r, g, b, w, dimmer} each 0-255
    pattern: str = "all_on"
    transition_ms: int = 0
    label: str = ""

    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Step":
        return cls(
            index=d.get("index", 0),
            start=float(d.get("start", 0)),
            end=float(d.get("end", 0)),
            drgbw=dict(d.get("drgbw", {"r": 0, "g": 0, "b": 0, "w": 0, "dimmer": 0})),
            pattern=d.get("pattern", "all_on"),
            transition_ms=int(d.get("transition_ms", 0)),
            label=d.get("label", ""),
        )


@dataclass
class Program:
    name: str
    steps: List[Step] = field(default_factory=list)
    song_id: str = ""
    created: str = ""
    modified: str = ""
    notes: str = ""

    def total_duration(self) -> float:
        if not self.steps:
            return 0.0
        return self.steps[-1].end

    def step_at(self, t: float) -> Optional[Step]:
        for s in self.steps:
            if s.start <= t < s.end:
                return s
        return None

    def add_step(self, start: float, end: float, drgbw: dict,
                 pattern: str = "all_on", label: str = "") -> Step:
        idx = len(self.steps)
        step = Step(
            index=idx,
            start=start,
            end=end,
            drgbw=dict(drgbw),
            pattern=pattern,
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

    def move_step(self, index: int, new_start: float, new_end: float) -> bool:
        if index < 0 or index >= len(self.steps):
            return False
        if new_end <= new_start:
            return False
        self.steps[index].start = new_start
        self.steps[index].end = new_end
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
            "song_id": self.song_id,
            "created": self.created,
            "modified": self.modified,
            "notes": self.notes,
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Program":
        return cls(
            name=d.get("name", "Untitled"),
            steps=[Step.from_dict(s) for s in d.get("steps", [])],
            song_id=d.get("song_id", ""),
            created=d.get("created", ""),
            modified=d.get("modified", ""),
            notes=d.get("notes", ""),
        )


# ── Storage ──────────────────────────────────────────────
def _appdata_base() -> str:
    return os.path.join(os.path.expandvars("%APPDATA%"), "zzluxora")


def _programs_dir() -> str:
    d = os.path.join(_appdata_base(), "programs")
    os.makedirs(d, exist_ok=True)
    return d


def list_programs() -> List[str]:
    d = _programs_dir()
    if not os.path.isdir(d):
        return []
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(d)
        if f.endswith(".json")
    )


def save_program(program: Program) -> None:
    if not program.created:
        program.created = time.strftime("%Y-%m-%dT%H:%M:%S")
    program._touch()
    path = os.path.join(_programs_dir(), f"{program.name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(program.to_dict(), f, indent=2)


def load_program(name: str) -> Optional[Program]:
    path = os.path.join(_programs_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return Program.from_dict(json.load(f))


def delete_program(name: str) -> bool:
    path = os.path.join(_programs_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return False
    os.remove(path)
    return True


# ── Program from analyzed song (auto-generate) ──────────
def program_from_song(song_id: str, song_result: dict,
                       program_name: str = None) -> Program:
    """Convert an analyzed song's segments into a Program."""
    name = program_name or f"{song_result.get('filename', song_id)} (auto)"
    p = Program(name=name, song_id=song_id)
    for seg in song_result.get("segments", []):
        drgbw = seg.get("drgbw", {"r": 0, "g": 0, "b": 0, "w": 0, "dimmer": 0})
        if hasattr(drgbw, "r"):
            drgbw = {"r": drgbw.r, "g": drgbw.g, "b": drgbw.b,
                     "w": drgbw.w, "dimmer": drgbw.dimmer}
        p.add_step(
            start=float(seg.get("start", 0)),
            end=float(seg.get("end", 0)),
            drgbw=dict(drgbw),
            pattern=seg.get("pattern", "all_on"),
            label=seg.get("label", ""),
        )
    return p
