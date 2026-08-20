"""
widgets/splash_screen.py — zzluxora v6.0

Splash screen 3 detik dengan:
- Logo (lampu putih di BG hitam)
- Brand "zzluxora" gradient
- Subtitle "Audio-Reactive Lighting Design System"
- Progress bar
- Skipable: click / ESC / Space
"""
from __future__ import annotations
import time
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QBrush, QFont, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen, QProgressBar, QLabel, QWidget, QVBoxLayout


SPLASH_DURATION_MS = 3000
SPLASH_WIDTH = 600
SPLASH_HEIGHT = 400


class SplashScreen(QSplashScreen):
    """
    Frameless splash dengan logo + brand + progress bar.
    3 detik, skipable.
    """

    finished = Signal()  # emitted saat splash selesai (timeout atau skip)

    def __init__(self, logo_path: str | None = None, parent=None):
        # Render pixmap
        pixmap = QPixmap(SPLASH_WIDTH, SPLASH_HEIGHT)
        pixmap.fill(QColor("#000000"))

        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        # Center on primary screen
        if QApplication.primaryScreen():
            screen_geo = QApplication.primaryScreen().geometry()
            self.move(
                screen_geo.center().x() - SPLASH_WIDTH // 2,
                screen_geo.center().y() - SPLASH_HEIGHT // 2,
            )

        self._logo_path = logo_path
        self._progress_value = 0
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_finish)

        # Internal progress timer (tick setiap ~30ms)
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._tick_progress)
        self._start_time_ms = 0

    def start(self) -> None:
        """Start 3-detik countdown."""
        self._start_time_ms = int(time.monotonic() * 1000)
        self._tick_timer.start(30)
        self._timer.start(SPLASH_DURATION_MS)

    def _tick_progress(self) -> None:
        """Update progress bar (0-100% linear selama 3 detik)."""
        if not self._start_time_ms:
            return
        elapsed_ms = int(time.monotonic() * 1000) - self._start_time_ms
        if elapsed_ms < 0:
            elapsed_ms = 0
        pct = min(100, int(elapsed_ms / SPLASH_DURATION_MS * 100))
        if pct != self._progress_value:
            self._progress_value = pct
            self.repaint()

    def _on_finish(self) -> None:
        """Timer selesai — emit finished signal."""
        self._tick_timer.stop()
        self._progress_value = 100
        self.repaint()
        self.finished.emit()

    def mousePressEvent(self, event) -> None:
        """Click = skip."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._skip()

    def keyPressEvent(self, event) -> None:
        """ESC / Space = skip."""
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Space, Qt.Key.Key_Return):
            self._skip()
        super().keyPressEvent(event)

    def _skip(self) -> None:
        self._timer.stop()
        self._tick_timer.stop()
        self._on_finish()

    def drawContents(self, painter: QPainter) -> None:
        """Custom paint untuk logo + brand + progress bar."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = SPLASH_WIDTH, SPLASH_HEIGHT

        # ── Logo (lampu putih, BG hitam)
        logo_size = 120
        logo_x = (w - logo_size) // 2
        logo_y = 70
        self._draw_lightbulb(painter, logo_x, logo_y, logo_size)

        # ── Brand "zzluxora" gradient
        brand_font = QFont("Segoe UI", 36)
        brand_font.setBold(True)
        brand_font.setItalic(True)
        brand_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3.0)
        painter.setFont(brand_font)

        brand_rect_y = logo_y + logo_size + 20
        gradient = QLinearGradient(0, brand_rect_y, w, brand_rect_y)
        gradient.setColorAt(0.0, QColor("#ffffff"))
        gradient.setColorAt(0.5, QColor("#cccccc"))
        gradient.setColorAt(1.0, QColor("#ffffff"))
        painter.setPen(QPen(QBrush(gradient), 1))

        from PySide6.QtCore import QRect
        brand_rect = QRect(0, brand_rect_y, w, 50)
        painter.drawText(brand_rect, Qt.AlignmentFlag.AlignCenter, "zzluxora")

        # ── Subtitle
        sub_font = QFont("Segoe UI", 11)
        painter.setFont(sub_font)
        painter.setPen(QColor("#707070"))
        sub_rect = QRect(0, brand_rect_y + 50, w, 20)
        painter.drawText(
            sub_rect,
            Qt.AlignmentFlag.AlignCenter,
            "Audio-Reactive Lighting Design System",
        )

        # ── Progress bar
        bar_w = 240
        bar_h = 4
        bar_x = (w - bar_w) // 2
        bar_y = h - 60
        # BG
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1a1a1a"))
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 2, 2)
        # Fill
        fill_w = max(1, int(bar_w * self._progress_value / 100))
        bar_gradient = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
        bar_gradient.setColorAt(0.0, QColor("#2ecc71"))
        bar_gradient.setColorAt(1.0, QColor("#27ae60"))
        painter.setBrush(bar_gradient)
        painter.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 2, 2)

        # ── Hint text
        hint_font = QFont("Segoe UI", 8)
        painter.setFont(hint_font)
        painter.setPen(QColor("#505050"))
        hint_rect = QRect(0, h - 40, w, 16)
        painter.drawText(
            hint_rect,
            Qt.AlignmentFlag.AlignCenter,
            "Click or press ESC to skip",
        )

    def _draw_lightbulb(self, painter: QPainter, x: int, y: int, size: int) -> None:
        """Gambar ikon lampu putih di background hitam."""
        painter.save()

        # Bulb (lingkaran utama)
        from PySide6.QtCore import QPoint, QRect
        from PySide6.QtGui import QPolygon

        bulb_size = int(size * 0.65)
        bulb_x = x + (size - bulb_size) // 2
        bulb_y = y
        bulb_rect = QRect(bulb_x, bulb_y, bulb_size, bulb_size)
        painter.setPen(QPen(QColor("#e0e0e0"), 2))
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(bulb_rect)

        # Filament (X di dalam bulb)
        center_x = bulb_x + bulb_size // 2
        center_y = bulb_y + bulb_size // 2
        filament_size = int(bulb_size * 0.25)
        painter.setPen(QPen(QColor("#909090"), 1))
        painter.drawLine(
            center_x - filament_size, center_y - filament_size,
            center_x + filament_size, center_y + filament_size,
        )
        painter.drawLine(
            center_x - filament_size, center_y + filament_size,
            center_x + filament_size, center_y - filament_size,
        )

        # Base/socket (3 garis horizontal)
        base_x = x + (size - int(size * 0.4)) // 2
        base_y = bulb_y + bulb_size
        base_w = int(size * 0.4)
        base_h = int(size * 0.3)
        painter.setPen(QPen(QColor("#cccccc"), 2))
        for i in range(3):
            line_y = base_y + (i + 1) * (base_h // 4)
            painter.drawLine(base_x, line_y, base_x + base_w, line_y)

        painter.restore()
