"""
FixtureGrid — v6 2D floor-plan grid with multi-fixture pattern visualization.

Renders N×M PAR LED cells dengan color + pattern dari current segment.
Patterns (math model §[8] Pola Multi-Fixture):
  - all_on      : semua cell sama
  - running     : satu cell nyala, berotasi (QTimer animation)
  - gradient    : linear color dari cell 0 → cell N
  - center_out  : radial dari tengah, fade ke luar

Click cell → select (green border).
"""
from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import QWidget, QSizePolicy
import math


class FixtureGrid(QWidget):
    """2D floor-plan grid showing per-fixture color per current segment."""

    cellClicked = Signal(int, int)  # row, col

    def __init__(self, cols: int = 4, rows: int = 4, cell_size: int = 48, parent=None):
        super().__init__(parent)
        self.cols = cols
        self.rows = rows
        self.cell_size = cell_size
        self.padding = 8
        self.selected_cell = None  # (row, col)

        # Current segment state
        self.rgb_255 = (128, 128, 128)
        self.dimmer = 128
        self.pattern = "all_on"
        self.running_pos = 0
        self.segment_name = "—"
        self.quadrant = ""

        # Animation timer (for running pattern)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_running)
        self._timer.setInterval(500)

        self.setMinimumSize(self._calc_min_size())
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setObjectName("fixtureGrid")

    def _calc_min_size(self) -> QSize:
        w = self.cols * self.cell_size + 2 * self.padding
        h = self.rows * self.cell_size + 2 * self.padding
        return QSize(w, h)

    def set_pattern(self, pattern: str, rgb_255: tuple, dimmer: int,
                    segment_name: str = "—", quadrant: str = "") -> None:
        self.pattern = pattern
        self.rgb_255 = rgb_255
        self.dimmer = dimmer
        self.segment_name = segment_name
        self.quadrant = quadrant

        if pattern == "running" and not self._timer.isActive():
            self._timer.start()
        elif pattern != "running" and self._timer.isActive():
            self._timer.stop()

        self.update()

    def _advance_running(self) -> None:
        self.running_pos = (self.running_pos + 1) % (self.cols * self.rows)
        self.update()

    def clear(self) -> None:
        self.rgb_255 = (40, 40, 40)
        self.dimmer = 0
        self.pattern = "all_on"
        self.segment_name = "—"
        self.quadrant = ""
        if self._timer.isActive():
            self._timer.stop()
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cs = min((w - 2 * self.padding) // self.cols,
                 (h - 2 * self.padding) // self.rows,
                 self.cell_size)

        grid_w = cs * self.cols
        grid_h = cs * self.rows
        start_x = (w - grid_w) // 2
        start_y = (h - grid_h) // 2

        p.fillRect(self.rect(), QColor("#0d0d0d"))

        for r in range(self.rows):
            for c in range(self.cols):
                idx = r * self.cols + c
                x = start_x + c * cs
                y = start_y + r * cs

                color, brightness = self._cell_color(idx, r, c)
                cell_color = QColor(
                    min(255, int(color[0] * brightness)),
                    min(255, int(color[1] * brightness)),
                    min(255, int(color[2] * brightness)),
                )

                p.setBrush(QBrush(cell_color))
                p.setPen(QPen(QColor("#2a2a2a"), 1))
                p.drawRoundedRect(x + 2, y + 2, cs - 4, cs - 4, 4, 4)

                if self.selected_cell == (r, c):
                    p.setPen(QPen(QColor("#2ecc71"), 2))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawRoundedRect(x + 2, y + 2, cs - 4, cs - 4, 4, 4)

                # Fixture number
                text_color = QColor("#ffffff") if brightness > 0.4 else QColor("#707070")
                p.setPen(QPen(text_color, 1))
                font = p.font()
                font.setPointSize(8)
                font.setBold(True)
                p.setFont(font)
                p.drawText(x + 4, y + 12, f"F{idx+1}")

        p.end()

    def _cell_color(self, idx: int, row: int, col: int) -> tuple:
        """Return (rgb_255, brightness_factor 0-1) for this cell based on pattern."""
        base = self.rgb_255
        if self.dimmer == 0 or base == (0, 0, 0):
            return ((40, 40, 40), 1.0)

        if self.pattern == "all_on":
            return (base, 1.0)
        elif self.pattern == "running":
            if idx == self.running_pos:
                return (base, 1.0)
            return (base, 0.15)
        elif self.pattern == "gradient":
            total = self.cols * self.rows
            factor = 1.0 - (idx / max(total - 1, 1)) * 0.5
            return (base, factor)
        elif self.pattern == "center_out":
            cr = (self.rows - 1) / 2
            cc = (self.cols - 1) / 2
            dist = math.sqrt((row - cr) ** 2 + (col - cc) ** 2)
            max_dist = math.sqrt(cr ** 2 + cc ** 2) if cr > 0 and cc > 0 else 1
            factor = 1.0 - (dist / max_dist) * 0.6
            return (base, max(0.3, factor))

        return (base, 1.0)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        w, h = self.width(), self.height()
        cs = min((w - 2 * self.padding) // self.cols,
                 (h - 2 * self.padding) // self.rows,
                 self.cell_size)
        grid_w = cs * self.cols
        grid_h = cs * self.rows
        start_x = (w - grid_w) // 2
        start_y = (h - grid_h) // 2

        mx, my = event.x(), event.y()
        if (mx < start_x or my < start_y or
                mx > start_x + grid_w or my > start_y + grid_h):
            return
        col = (mx - start_x) // cs
        row = (my - start_y) // cs
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.selected_cell = (row, col)
            self.cellClicked.emit(row, col)
            self.update()
