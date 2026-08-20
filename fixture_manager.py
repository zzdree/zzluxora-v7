"""
FixtureManager — shared state for fixtures and DMX address map.
Used by Address grid, Fixture List, and Fixture Editor panels.
Persists to fixtures/*.json and can serialize to .zlx (M5).

PyInstaller support:
  - dev mode:  fixtures/ next to main.py
  - frozen:    fixtures/ in %APPDATA%/zzluxora (install dir is read-only),
               seeded from the bundle on first run
"""
import json
import os
import shutil
import sys
from pathlib import Path


from engines.artnet_sender import ArtNetController


def get_app_base() -> Path:
    """Writable base path — for user fixtures in dev and frozen modes.

    Frozen: %APPDATA%/zzluxora (install dir under Program Files is read-only).
    Dev:    project folder next to this file.
    """
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("APPDATA") or Path.home()) / "zzluxora"
        base.mkdir(parents=True, exist_ok=True)
        return base
    return Path(__file__).parent


def get_bundle_base() -> Path | None:
    """Read-only PyInstaller bundle path (_MEIPASS), or None in dev."""
    meipass = getattr(sys, "_MEIPASS", None)
    return Path(meipass) if meipass else None


FIXTURES_DIR = get_app_base() / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)


def _seed_fixtures_from_bundle():
    """On first run in frozen mode, copy bundled fixtures to writable dir."""
    if any(FIXTURES_DIR.glob("*.json")):
        return
    bundle = get_bundle_base()
    if not bundle:
        return
    src = bundle / "fixtures"
    if not src.exists():
        return
    for f in src.glob("*.json"):
        try:
            shutil.copy(f, FIXTURES_DIR / f.name)
        except Exception as e:
            print(f"[FixtureManager] Seed copy failed for {f.name}: {e}")


_seed_fixtures_from_bundle()


class FixtureManager:
    """In-memory store for fixture definitions and DMX address map."""

    def __init__(self):
        self.fixtures: dict = {}
        self.address_map: dict = {}
        # M3+: analyzed songs keyed by song_id
        #   {song_id: {filepath, filename, features, segments, scenes, global_color, waveform, sr}}
        self.songs: dict = {}
        self.current_song_id: str | None = None
        self.song_counter: int = 0
        # M5: project file save/load
        self.project_filepath: str | None = None
        self.project_name: str = "Untitled.zlx"
        # M4: Art-Net controller (shared across chase/preview/output/mixer tabs)
        self.artnet_controller = ArtNetController()
        self.load_all()

    # ─────────────────────────────────────
    # Fixtures
    # ─────────────────────────────────────
    def load_all(self) -> list:
        self.fixtures.clear()
        for path in FIXTURES_DIR.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("name") or path.stem
                data.setdefault("filename", path.name)
                # Phase 10: default stage position for 2D preview
                data.setdefault("x", 0.5)
                data.setdefault("y", 0.5)
                self.fixtures[name] = data
            except Exception as e:
                print(f"[FixtureManager] Failed to load {path.name}: {e}")
        return sorted(self.fixtures.keys())

    def save_fixture(self, data: dict) -> tuple[bool, str]:
        name = data.get("name", "").strip()
        if not name:
            return False, "Name is required"
        if not isinstance(data.get("channels"), int) or data["channels"] < 1:
            return False, "Channels must be a positive integer"
        if not isinstance(data.get("channel_map"), list):
            return False, "channel_map must be a list"

        safe = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
        if not safe:
            return False, "Name has no valid filename characters"
        path = FIXTURES_DIR / f"{safe}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.fixtures[name] = {**data, "filename": path.name}
        return True, f"Saved: {path.name}"

    def delete_fixture(self, name: str) -> tuple[bool, str]:
        if name not in self.fixtures:
            return False, f"Not found: {name}"
        fname = self.fixtures[name].get("filename")
        if fname:
            path = FIXTURES_DIR / fname
            if path.exists():
                path.unlink()
        del self.fixtures[name]
        self.address_map = {
            k: v for k, v in self.address_map.items()
            if v.get("fixture_name") != name
        }
        return True, f"Deleted: {name}"

    def get_fixture(self, name: str) -> dict | None:
        return self.fixtures.get(name)

    def list_fixtures(self) -> list:
        return sorted(self.fixtures.keys())

    # ─────────────────────────────────────
    # Address map
    # ─────────────────────────────────────
    def patch(self, address: int, fixture_name: str) -> tuple[bool, str]:
        if address < 1 or address > 512:
            return False, "Address must be 1-512"
        if fixture_name not in self.fixtures:
            return False, f"Unknown fixture: {fixture_name}"
        fx = self.fixtures[fixture_name]
        ch_count = fx.get("channels", 1)
        for offset in range(ch_count):
            addr = address + offset
            if addr > 512:
                return False, f"Exceeds 512 at channel {offset + 1}"
            if addr in self.address_map:
                existing = self.address_map[addr]["fixture_name"]
                if existing == fixture_name and offset == 0:
                    continue
                return False, f"Address {addr} already patched to '{existing}'"
        for offset in range(ch_count):
            addr = address + offset
            self.address_map[addr] = {
                "fixture_name": fixture_name,
                "fixture_data": fx,
                "start_address": address,
            }
        return True, f"Patched '{fixture_name}' at {address}-{address + ch_count - 1}"

    def unpatch(self, address: int) -> tuple[bool, str]:
        if address not in self.address_map:
            return False, "Address not patched"
        start = self.address_map[address]["start_address"]
        fx_name = self.address_map[address]["fixture_name"]
        ch_count = self.fixtures[fx_name]["channels"]
        for offset in range(ch_count):
            self.address_map.pop(start + offset, None)
        return True, f"Unpatched '{fx_name}' from {start}-{start + ch_count - 1}"

    def get_address_map(self) -> dict:
        return self.address_map

    def clear_all(self):
        self.address_map.clear()
