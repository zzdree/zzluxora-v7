"""
AppConfig — config.ini wrapper for zzluxora v6.0.

Sections:
  [General]  — version, last project, recent files
  [UI]       — sidebar state, theme (locked to dark in v5)
  [Audio]    — last_audio_dir, default sample rate
  [ArtNet]   — default_ip, default_universe, default_fps
  [Fixtures] — search_paths (comma-separated, fallback chain)

File location:
  - In dev (running as .py): <project root>/config.ini
  - In production (onefile exe): same dir as the .exe
"""
import configparser
import os
import sys
from pathlib import Path
from threading import Lock


def _resolve_config_path() -> Path:
    """Pick config.ini path based on environment.

    Frozen (installed to Program Files): %APPDATA%/zzluxora/config.ini — the
    install dir is read-only, so config MUST live in the user profile. This is
    the same base used by chases/programs/pages/presets.
    Dev: inside the project folder, next to main.py.
    """
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("APPDATA") or Path.home()) / "zzluxora"
        base.mkdir(parents=True, exist_ok=True)
        return base / "config.ini"
    return Path(__file__).resolve().parent / "config.ini"


class AppConfig:
    """Thread-safe wrapper around configparser with sensible v5 defaults."""

    DEFAULTS = {
        "General": {
            "version": "7.0.0",
            "last_project": "",
            "recent_files": "",
        },
        "UI": {
            "sidebar_collapsed": "false",
            "theme": "dark",  # v5: locked to dark
        },
        "Audio": {
            "last_audio_dir": "",
            "sample_rate": "22050",
        },
        "ArtNet": {
            "default_ip": "127.0.0.1",
            "default_universe": "0",
            "default_fps": "30",
        },
        "Color": {
            "active_va_preset": "Default Praise",
        },
        "Fixtures": {
            "search_paths": "program/fixtures,fixtures",
        },
    }

    def __init__(self, path: Path | None = None):
        self._path = path or _resolve_config_path()
        self._cfg = configparser.ConfigParser()
        self._lock = Lock()
        self._load()

    # ── IO
    def _load(self) -> None:
        with self._lock:
            if not self._path.exists():
                # First run — seed with defaults and write
                for section, opts in self.DEFAULTS.items():
                    self._cfg[section] = opts
                self._save_unlocked()
                return
            try:
                self._cfg.read(self._path, encoding="utf-8")
            except (OSError, configparser.Error):
                # Corrupt — fall back to defaults (don't crash)
                self._cfg = configparser.ConfigParser()
                for section, opts in self.DEFAULTS.items():
                    self._cfg[section] = opts
            # Backfill any missing section/key
            for section, opts in self.DEFAULTS.items():
                if not self._cfg.has_section(section):
                    self._cfg[section] = opts
                else:
                    for k, v in opts.items():
                        if not self._cfg.has_option(section, k):
                            self._cfg.set(section, k, v)

    def _save_unlocked(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("w", encoding="utf-8") as f:
                self._cfg.write(f)
        except OSError:
            # Read-only filesystem etc. — fail silently, keep in-memory copy
            pass

    def save(self) -> None:
        with self._lock:
            self._save_unlocked()

    # ── Accessors
    def get(self, section: str, key: str, fallback: str = "") -> str:
        with self._lock:
            return self._cfg.get(section, key, fallback=fallback)

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        raw = self.get(section, key, "").strip().lower()
        if raw in ("true", "1", "yes", "on"):
            return True
        if raw in ("false", "0", "no", "off"):
            return False
        return fallback

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        try:
            return int(self.get(section, key, str(fallback)))
        except ValueError:
            return fallback

    def get_list(self, section: str, key: str, sep: str = ",") -> list[str]:
        raw = self.get(section, key, "")
        return [x.strip() for x in raw.split(sep) if x.strip()]

    def set(self, section: str, key: str, value: str) -> None:
        with self._lock:
            if not self._cfg.has_section(section):
                self._cfg.add_section(section)
            self._cfg.set(section, key, str(value))
            self._save_unlocked()

    # ── Convenience
    @property
    def path(self) -> Path:
        return self._path

    @property
    def sidebar_collapsed(self) -> bool:
        return self.get_bool("UI", "sidebar_collapsed", False)

    @sidebar_collapsed.setter
    def sidebar_collapsed(self, v: bool) -> None:
        self.set("UI", "sidebar_collapsed", "true" if v else "false")

    @property
    def last_audio_dir(self) -> str:
        return self.get("Audio", "last_audio_dir", "")

    @last_audio_dir.setter
    def last_audio_dir(self, v: str) -> None:
        self.set("Audio", "last_audio_dir", v)

    @property
    def fixture_search_paths(self) -> list[Path]:
        """Return fixture search paths relative to project root, with fallbacks."""
        candidates: list[Path] = []
        project_root = Path(__file__).resolve().parent.parent
        for raw in self.get_list("Fixtures", "search_paths"):
            p = Path(raw)
            candidates.append(p if p.is_absolute() else project_root / p)
        return candidates

    @property
    def artnet_default_ip(self) -> str:
        return self.get("ArtNet", "default_ip", "127.0.0.1")

    @property
    def artnet_default_universe(self) -> int:
        return self.get_int("ArtNet", "default_universe", 0)

    @property
    def artnet_default_fps(self) -> int:
        return self.get_int("ArtNet", "default_fps", 30)

    @property
    def active_va_preset(self) -> str:
        """Name of currently active V-A → HSV preset (v6 Phase 3)."""
        return self.get("Color", "active_va_preset", "Default Praise")

    @active_va_preset.setter
    def active_va_preset(self, v: str) -> None:
        self.set("Color", "active_va_preset", v)


# Module-level singleton (lazy)
_singleton: AppConfig | None = None


def app_config() -> AppConfig:
    global _singleton
    if _singleton is None:
        _singleton = AppConfig()
    return _singleton
