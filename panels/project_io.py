"""
Project I/O — save/load .zlx project files.
Schema v4.0 — JSON, reuses v2.2 structure.
"""
import json
from datetime import datetime, timezone
from pathlib import Path


def serialize_project(manager) -> dict:
    """Collect all manager state into a dict."""
    return {
        "version": "3.0",
        "project_name": manager.project_name,
        "fixtures": manager.fixtures,
        "address_map": manager.address_map,
        "songs": manager.songs,
        "artnet": {
            "target_ip": getattr(manager.artnet_controller, "target_ip", "127.0.0.1"),
            "universe": getattr(manager.artnet_controller, "universe", 0),
            "fps": getattr(manager.artnet_controller, "fps", 30),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def save_project(manager, filepath: str) -> bool:
    """Save manager state to a .zlx file. Returns True on success."""
    try:
        data = serialize_project(manager)
        Path(filepath).write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        manager.project_filepath = filepath
        manager.project_name = Path(filepath).name
        return True
    except Exception as e:
        print(f"save_project failed: {e}")
        return False


def load_project(manager, filepath: str) -> bool:
    """Load manager state from a .zlx file. Returns True on success."""
    try:
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        manager.project_name = data.get("project_name", "Untitled.zlx")
        manager.project_filepath = filepath
        manager.fixtures = data.get("fixtures", [])
        manager.address_map = data.get("address_map", {})
        manager.songs = data.get("songs", {})
        artnet = data.get("artnet", {})
        if hasattr(manager, "artnet_controller") and manager.artnet_controller:
            manager.artnet_controller.target_ip = artnet.get("target_ip", "127.0.0.1")
            manager.artnet_controller.universe = artnet.get("universe", 0)
            manager.artnet_controller.fps = artnet.get("fps", 30)
        # Best-effort persist to user fixtures dir (non-fatal if save_all missing)
        try:
            manager.save_all()
        except AttributeError:
            pass
        return True
    except Exception as e:
        print(f"load_project failed: {e}")
        return False
