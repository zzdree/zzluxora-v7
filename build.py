"""
Build script for zzluxora v6 — PyInstaller.
Run:  python build.py
Out:  ../results/zzluxora-v6/   (moved from dist/zzluxora/ automatically)

v6 changes from v5:
- Auto-renames dist/zzluxora/ → ../results/zzluxora-v6/
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_NAME = "zzluxora"
ENTRY = "main.py"
THIS_DIR = Path(__file__).resolve().parent
RESULTS_DIR = THIS_DIR.parent / "results"
TARGET_DIR = RESULTS_DIR / f"{APP_NAME}-v7"


def main():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name", APP_NAME,
        # Bundle the default fixtures
        "--add-data", f"{THIS_DIR / 'fixtures'}{os.pathsep}fixtures",
        # Qt-related collections
        "--collect-submodules", "PySide6",
        "--collect-data", "PySide6",
        # Don't show console on Windows
        "--noconsole",
    ]
    # App icon (run tools/make_ico.py first to generate it)
    ico = THIS_DIR / "assets" / "zzluxora.ico"
    if ico.is_file():
        cmd += ["--icon", str(ico)]
    else:
        print(f"[build] NOTE: {ico} not found — run 'python tools/make_ico.py' for a branded icon")
    cmd.append(ENTRY)
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=str(THIS_DIR))

    # Post-build: copy dist/zzluxora/ → results/zzluxora-v5/.
    # Use copytree, not move: the OneDrive sync daemon briefly locks newly
    # written files in dist/, so shutil.move's rmtree-of-source fails with
    # PermissionError. Copy is safe; dist/ gets reaped by --clean next run.
    src = THIS_DIR / "dist" / APP_NAME
    if src.exists():
        if TARGET_DIR.exists():
            shutil.rmtree(TARGET_DIR)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(src), str(TARGET_DIR))
        print(f"\n[build] Copied -> {TARGET_DIR}")
        # Also drop a copy of config.ini next to the exe (first-run will create if missing)
        if not (TARGET_DIR / "config.ini").exists():
            shutil.copy(THIS_DIR.parent / "config.ini", TARGET_DIR / "config.ini") \
                if (THIS_DIR.parent / "config.ini").exists() else None
    else:
        print(f"[build] WARNING: {src} not found — PyInstaller output unexpected")


if __name__ == "__main__":
    main()
