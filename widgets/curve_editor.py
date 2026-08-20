"""
CurveEditor (v6 Phase 3C) — visual editor for a 1D piecewise-linear LUT.

Layout:
  - Black canvas with white gridlines
  - 11 control points (circles)
  - Left-click + drag to move a point
  - Right-click on a point to remove it (or do nothing if < 3 points)
  - "Reset" button restores identity line
  - Y-axis label, X-axis label (input, output)

Public API:
  curveChanged = Signal()       fired on every point change
  get_curve() -> CurveLUT
  set_curve(curve: CurveLUT)
  reset()
"""
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

from engines.curve_lut import CurveLUT, identity_points


class CurveEditor(QWidget):
    curveChanged = Signal()

    POINT_RADIUS = 6
    DRAG_RADIUS = 14  # larger hit area for easier clicking

    def __init__(self, title: str = "Curve", parent=None):
        super().__init__(parent)
        self.title = title
        self.points: list = list(identity_points(11))
        self.dragging_idx: int = -1
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        # Title row
        title_row = QHBoxLayout()
        title_lbl = QLabel(self.title)
        title_lbl.setStyleSheet("color: #c8c8c8; font-size: 11px; font-weight: 700;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedHeight(22)
        self.reset_btn.setStyleSheet(
            "QPushButton { background-color: #2a2a2a; color: #c8c8c8; "
            "border: 1px solid #2a2a2a; padding: 0 8px; font-size: 10px; }"
            "QPushButton:hover { background-color: #3a3a3a; }"
        )
        self.reset_btn.clicked.connect(self.reset)
        title_row.addWidget(self.reset_btn)
        root.addLayout(title_row)

        # Canvas
        self.canvas = _CurveCanvas(self)
        self.canvas.setMinimumHeight(160)
        self.canvas.setMinimumWidth(220)
        self.canvas.setStyleSheet("background-color: #0a0a0a; border: 1px solid #2a2a2a;")
        root.addWidget(self.canvas, 1)

    # ── Public
    def get_curve(self) -> CurveLUT:
        return CurveLUT(name=self.title, points=list(self.points))

    def set_curve(self, curve: CurveLUT) -> None:
        self.points = [tuple(p) for p in curve.points]
        self.canvas.update()
        self.curveChanged.emit()

    def reset(self) -> None:
        self.points = list(identity_points(11))
        self.canvas.update()
        self.curveChanged.emit()

    # ── Internals (forward to canvas)
    def update(self):
        if hasattr(self, "canvas"):
            self.canvas.points = self.points
            self.canvas.update()
        super().update()


class _CurveCanvas(QWidget):
    def __init__(self, editor: CurveEditor):
        super().__init__(editor)
        self.editor = editor
        self.points: list = editor.points
        self.setMouseTracking(True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        # Padding for axis labels
        pad_l, pad_r, pad_t, pad_b = 24, 8, 8, 18
        cw, ch = w - pad_l - pad_r, h - pad_t - pad_b

        # Gridlines
        grid_pen = QPen(QColor("#1a1a1a"), 1)
        p.setPen(grid_pen)
        for i in range(1, 10):
            x = pad_l + cw * i / 10
            p.drawLine(int(x), pad_t, int(x), pad_t + ch)
            y = pad_t + ch * i / 10
            p.drawLine(pad_l, int(y), pad_l + cw, int(y))

        # Axis box
        p.setPen(QPen(QColor("#3a3a3a"), 1))
        p.drawRect(pad_l, pad_t, cw, ch)

        # Axis labels
        p.setPen(QColor("#707070"))
        font = QFont("Consolas", 8)
        p.setFont(font)
        p.drawText(pad_l, h - 4, "0")
        p.drawText(pad_l + cw - 8, h - 4, "1")
        p.drawText(2, pad_t + 8, "1")
        p.drawText(2, pad_t + ch - 2, "0")

        # Curve (polyline)
        curve_pen = QPen(QColor("#2ecc71"), 2)
        p.setPen(curve_pen)
        prev = None
        for x, y in self.points:
            px = pad_l + x * cw
            py = pad_t + (1 - y) * ch
            if prev is not None:
                p.drawLine(int(prev[0]), int(prev[1]), int(px), int(py))
            prev = (px, py)

        # Points
        for i, (x, y) in enumerate(self.points):
            px = pad_l + x * cw
            py = pad_t + (1 - y) * ch
            # Hovering/dragging highlight
            if i == self.editor.dragging_idx:
                p.setBrush(QBrush(QColor("#27ae60")))
            else:
                p.setBrush(QBrush(QColor("#e8e8e8")))
            p.setPen(QPen(QColor("#0d0d0d"), 1))
            p.drawEllipse(QPointF(px, py), CurveEditor.POINT_RADIUS, CurveEditor.POINT_RADIUS)

        p.end()

    def _to_norm(self, mx: int, my: int) -> tuple:
        pad_l, pad_r, pad_t, pad_b = 24, 8, 8, 18
        cw = self.width() - pad_l - pad_r
        ch = self.height() - pad_t - pad_b
        if cw <= 0 or ch <= 0:
            return 0.0, 0.0
        x_norm = (mx - pad_l) / cw
        y_norm = 1 - (my - pad_t) / ch
        x_norm = max(0.0, min(1.0, x_norm))
        y_norm = max(0.0, min(1.0, y_norm))
        return x_norm, y_norm

    def _nearest_point(self, mx: int, my: int) -> int:
        pad_l, pad_r, pad_t, pad_b = 24, 8, 8, 18
        cw = self.width() - pad_l - pad_r
        ch = self.height() - pad_t - pad_b
        min_dist = float("inf")
        idx = -1
        for i, (x, y) in enumerate(self.points):
            px = pad_l + x * cw
            py = pad_t + (1 - y) * ch
            dist = ((mx - px) ** 2 + (my - py) ** 2) ** 0.5
            if dist < min_dist and dist < CurveEditor.DRAG_RADIUS:
                min_dist = dist
                idx = i
        return idx

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self._nearest_point(event.x(), event.y())
            if idx >= 0:
                self.editor.dragging_idx = idx
                self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            idx = self._nearest_point(event.x(), event.y())
            # Right-click does nothing special for now (could remove point)

    def mouseMoveEvent(self, event):
        if self.editor.dragging_idx < 0:
            return
        # First and last points are clamped on x
        i = self.editor.dragging_idx
        x_norm, y_norm = self._to_norm(event.x(), event.y())
        if i == 0:
            x_norm = 0.0
        elif i == len(self.editor.points) - 1:
            x_norm = 1.0
        else:
            # Clamp between neighbors
            left_x = self.editor.points[i - 1][0] + 0.01
            right_x = self.editor.points[i + 1][0] - 0.01
            x_norm = max(left_x, min(right_x, x_norm))
        self.editor.points[i] = (x_norm, y_norm)
        self.points = self.editor.points
        self.update()
        self.editor.curveChanged.emit()

    def mouseReleaseEvent(self, event):
        if self.editor.dragging_idx >= 0:
            self.editor.dragging_idx = -1
            self.update()
