"""
Generate assets/zzluxora.ico from assets/logo_256.png (multi-size icon).

Run once before building the installer:
    python tools/make_ico.py

Needs Pillow (pip install pillow). The .ico bundles 16/32/48/64/128/256 px so
Windows picks the right size for taskbar, Alt-Tab, and Explorer.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "logo_256.png"
OUT = ROOT / "assets" / "zzluxora.ico"
SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main():
    if not SRC.is_file():
        raise SystemExit(f"source not found: {SRC}")
    img = Image.open(SRC).convert("RGBA")
    img.save(OUT, format="ICO", sizes=SIZES)
    print(f"[make_ico] wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
