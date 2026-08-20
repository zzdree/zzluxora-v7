"""
CurveLUT (v6 Phase 3C) — 1D piecewise linear LUT with N control points.

Used for Saturation (S) and Brightness (V) curve shaping.
Default = identity line (y = x).

evaluate(x in [0,1]) -> y in [0,1] via piecewise-linear interpolation.

JSON serialization: {"points": [[x, y], ...]} for storage under
%APPDATA%/zzluxora/presets/curves/.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


Point = Tuple[float, float]


def identity_points(n: int = 11) -> List[Point]:
    """Default identity LUT with N points (x = y evenly spaced)."""
    return [(i / (n - 1), i / (n - 1)) for i in range(n)]


@dataclass
class CurveLUT:
    name: str = "Identity"
    points: List[Point] = field(default_factory=lambda: identity_points(11))

    def evaluate(self, x: float) -> float:
        """Piecewise-linear evaluation. x clamped to [0, 1]."""
        if not self.points:
            return x
        x = max(0.0, min(1.0, x))
        pts = self.points
        # If x is before first point, use first y
        if x <= pts[0][0]:
            return pts[0][1]
        # If x is after last point, use last y
        if x >= pts[-1][0]:
            return pts[-1][1]
        # Find segment
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= x <= x1:
                if x1 == x0:
                    return y0
                t = (x - x0) / (x1 - x0)
                return y0 + t * (y1 - y0)
        return pts[-1][1]

    def apply_to_value(self, value: float, in_min: float = 0.0, in_max: float = 1.0) -> float:
        """Normalize value to [0,1], evaluate, return result in same range."""
        if in_max == in_min:
            return value
        norm = (value - in_min) / (in_max - in_min)
        return self.evaluate(norm)

    def to_dict(self) -> dict:
        return {"name": self.name, "points": [list(p) for p in self.points]}

    @classmethod
    def from_dict(cls, d: dict) -> "CurveLUT":
        pts = [tuple(p) for p in d.get("points", identity_points(11))]
        return cls(name=d.get("name", "Identity"), points=pts)


# ── Preset storage (curves/) ──────────────────────────────────────
import os
import json


def _appdata_base() -> str:
    return os.path.join(os.path.expandvars("%APPDATA%"), "zzluxora")


def _curves_dir() -> str:
    d = os.path.join(_appdata_base(), "presets", "curves")
    os.makedirs(d, exist_ok=True)
    return d


def list_curves() -> List[str]:
    """Return sorted list of saved curve preset names (no .json extension)."""
    d = _curves_dir()
    if not os.path.isdir(d):
        return []
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(d)
        if f.endswith(".json")
    )


def save_curve(curve: CurveLUT) -> None:
    path = os.path.join(_curves_dir(), f"{curve.name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(curve.to_dict(), f, indent=2)


def load_curve(name: str) -> Optional[CurveLUT]:
    path = os.path.join(_curves_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return CurveLUT.from_dict(json.load(f))


def delete_curve(name: str) -> bool:
    if name == "Identity":
        return False  # protect default
    path = os.path.join(_curves_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return False
    os.remove(path)
    return True
