"""
zzluxora v6.0 — Native PySide6 Desktop App (skripsi-final)
Realigned to the original concept brief (prompt_v4.docx).

Major v6 changes from v5:
  - 8-stage audio analysis pipeline (engines/analyze_pipeline.py)
  - Color mapping modular (engines/color_mapping.py)
  - Splash screen 3 detik dengan logo + progress (skipable)
  - Empty state saat belum ada project di-load
  - Branding: lowercase "zzluxora"
  - Reordered About panel fields (prodi → jurusan → fakultas → universitas)
  - Math model verification tests (tests/test_math_model.py — RELEASE BLOCKER)

Source of truth: skripsi BAB 3 + markdowns/script_math_model.md.

Run:    python main.py
Build:  python build.py
"""
import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from font_loader import load_windows_fonts
from main_window import MainWindow
from widgets.splash_screen import SplashScreen
from config import app_config


def main():
    # High-DPI support (must be set before QApplication)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("zzluxora")
    app.setOrganizationName("UNNES")
    app.setApplicationVersion("7.0.0")

    # Load app config (creates config.ini next to exe on first run)
    cfg = app_config()

    # Explicitly load Windows system fonts (no-op on real display, fixes tofu offscreen)
    load_windows_fonts()
    app.setFont(QFont("Segoe UI", 10))

    # App icon (logo white lightbulb on black)
    assets_dir = Path(__file__).parent / "assets"
    icon_path = assets_dir / "logo_256.png"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Splash (3 detik, skipable)
    splash = SplashScreen(logo_path=str(icon_path) if icon_path.is_file() else None)
    splash.show()
    app.processEvents()

    # Build main window (may take ~1-2s untuk onboarding + panel init)
    window = MainWindow()

    def _on_splash_done():
        window.show()
    splash.finished.connect(_on_splash_done)
    splash.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
