"""
Font loader — explicitly load Windows system fonts into Qt.

The offscreen Qt platform on Windows reports 0 fonts available,
which makes all text render as tofu (□). This module fixes that
by loading the system fonts directly from C:\\Windows\\Fonts.

In normal (non-offscreen) mode, this is a no-op (Qt already has
access to the system font DB).
"""
import os
import sys
from pathlib import Path
from PySide6.QtGui import QFontDatabase, QFont


WIN_FONTS_DIR = Path("C:/Windows/Fonts")

# (relative filename, family name to expect after load)
REQUIRED_FONTS = [
    ("segoeui.ttf",   "Segoe UI"),
    ("segoeuib.ttf",  "Segoe UI"),       # bold
    ("segoeuii.ttf",  "Segoe UI"),       # italic
    ("seguisb.ttf",   "Segoe UI Semibold"),
    ("seguiemj.ttf",  "Segoe UI Emoji"),
    ("arial.ttf",     "Arial"),
    ("arialbd.ttf",   "Arial"),
]


def load_windows_fonts() -> dict:
    """
    Load Windows system fonts into the Qt application font DB.
    Returns a dict of {family_name: True/False} indicating load success.
    """
    results = {}
    if sys.platform != "win32" or not WIN_FONTS_DIR.exists():
        return results

    for filename, family in REQUIRED_FONTS:
        font_path = WIN_FONTS_DIR / filename
        if not font_path.exists():
            results[family] = False
            continue
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id != -1:
            fams = QFontDatabase.applicationFontFamilies(font_id)
            if family in fams:
                results[family] = True
                continue
        results[family] = False

    return results


def set_default_font() -> QFont:
    """Set Segoe UI as the default application font."""
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    QFontDatabase.setApplicationFontFamilies
    return font


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    results = load_windows_fonts()
    print("Font load results:")
    for fam, ok in results.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {fam}")
    print(f"\nTotal families now available: {len(QFontDatabase.families())}")
    print("Has 'Segoe UI':", "Segoe UI" in QFontDatabase.families())
    print("Has 'Segoe UI Emoji':", "Segoe UI Emoji" in QFontDatabase.families())
