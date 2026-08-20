"""
Smoke screenshot — run MainWindow in offscreen mode, exercise M2, save PNG.
Usage: QT_QPA_PLATFORM=offscreen python screenshot.py
"""
import os
import sys
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from font_loader import load_windows_fonts
from main_window import MainWindow

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "previews")
os.makedirs(OUT_DIR, exist_ok=True)


def grab(window, filename, panel_key=None, patch_first=False):
    if panel_key:
        window._show_panel(panel_key)
    if patch_first:
        # Pre-patch a fixture for the screenshot
        from fixture_manager import FixtureManager
        # Already wired via window.manager
        names = window.manager.list_fixtures()
        if names:
            window.manager.patch(1, names[0])
            if len(names) > 1:
                window.manager.patch(9, names[0])  # second instance
            # Trigger address tab refresh
            program = window.panels["program"]
            for i in range(program.tabs.count()):
                tab = program.tabs.widget(i)
                if hasattr(tab, "_refresh"):
                    tab._refresh()
    QApplication.processEvents()
    out = os.path.join(OUT_DIR, filename)
    window.grab().save(out, "PNG")
    print(f"Saved: {out}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    load_windows_fonts()
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.resize(1280, 800)
    window.show()

    def run_shots():
        grab(window, "v3_milestone1.png", "about")
        grab(window, "v3_milestone2_program.png", "program", patch_first=True)
        grab(window, "v3_milestone2_fixtures.png", "fixture_list")
        grab(window, "v3_milestone2_editor.png", "fixture_editor")
        app.quit()

    QTimer.singleShot(500, run_shots)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
