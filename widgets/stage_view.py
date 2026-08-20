"""
Stage View (Phase 10) — 2D top-down PAR-LED stage for live Art-Net preview.

Three classes:
- ParLed: 24×24 PAR-LED dot (QWidget). Paints a 4-channel tinted circle
  (dimmer + RGBW additive overlay + W indicator). Draggable when parented
  to a Canvas2D.
- Canvas2D: dark 16:9 QFrame hosting ParLed widgets. Handles hit-test, drag,
  background grid, and per-fixture color/position updates. Coordinates are
  stored as **normalized floats** (0..1) so layout is resolution-independent.
- XySidebar: right-side panel (200 px) with two QDoubleSpinBox (X, Y in
  0.000–1.000) and Center/Reset buttons for the selected fixture.

Signals:
- ParLed.position_changed(fixture_id, x_norm, y_norm)
- Canvas2D.fixture_moved(fixture_id, x_norm, y_norm)
- Canvas2D.fixture_selected(fixture_id)
- XySidebar.xy_changed(fixture_id, x_norm, y_norm)
- XySidebar.center_requested(fixture_id)
- XySidebar.reset_requested(fixture_id)
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QSizePolicy,
)


# ── PAR LED ──────────────────────────────────────────────────────────────
class ParLed(QWidget):
    """24×24 PAR-LED dot. Draggable when parent is a Canvas2D."""

    position_changed = Signal(str, float, float)  # fixture_id, x_norm, y_norm

    DIAMETER = 24
    PAD = 6  # extra hit-target around the dot

    def __init__(self, fixture_id: str, name: str, parent: "Canvas2D | None" = None):
        super().__init__(parent)
        self.fixture_id = fixture_id
        self.name = name
        self._x_norm = 0.5
        self._y_norm = 0.5
        self._d = 0
        self._r = 0
        self._g = 0
        self._b = 0
        self._w = 0
        self._selected = False
        self._dragging = False
        self._drag_offset = QPointF(0, 0)
        self.setFixedSize(self.DIAMETER + 2 * self.PAD, self.DIAMETER + 2 * self.PAD)
        self.setMouseTracking(True)
        self.setToolTip(f"{name}")

    # ── public API
    def set_position(self, x_norm: float, y_norm: float) -> None:
        self._x_norm = max(0.0, min(1.0, x_norm))
        self._y_norm = max(0.0, min(1.0, y_norm))
        parent = self.parent()
        if parent is not None and isinstance(parent, Canvas2D):
            parent.place_led(self)

    def set_drgbw(self, d: int, r: int, g: int, b: int, w: int) -> None:
        self._d, self._r, self._g, self._b, self._w = d, r, g, b, w
        self.update()

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        if selected:
            self.raise_()
        self.update()

    def position(self) -> tuple[float, float]:
        return self._x_norm, self._y_norm

    # ── events
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            parent = self.parent()
            if isinstance(parent, Canvas2D):
                parent.select(self.fixture_id)
            self._dragging = True
            self._drag_offset = event.position() - QPointF(
                self.width() / 2, self.height() / 2
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and isinstance(self.parent(), Canvas2D):
            self.parent().drag_led(self, event.globalPosition() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            if isinstance(self.parent(), Canvas2D):
                self.parent().end_drag(self)
            event.accept()

    # ── paint
    def paintEvent(self, event):  # noqa: ARG002
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        r = self.DIAMETER / 2

        # outer glow (only when at least one channel is on)
        if self._d > 0 or self._r + self._g + self._b + self._w > 0:
            glow_r = min(255, self._r + self._d)
            glow_g = min(255, self._g + self._d)
            glow_b = min(255, self._b + self._d)
            glow = QColor(glow_r, glow_g, glow_b, 70)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(glow)
            p.drawEllipse(QPointF(cx, cy), r + 4, r + 4)

        # LED body — dim grey base tinted by DRGBW
        base_v = min(255, max(40, self._d * 2))
        body_r = min(255, base_v + self._r)
        body_g = min(255, base_v + self._g)
        body_b = min(255, base_v + self._b)
        p.setBrush(QColor(body_r, body_g, body_b))
        p.setPen(QPen(QColor(20, 20, 20), 1))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # white W indicator (inner small circle)
        if self._w > 0:
            w_alpha = min(255, self._w * 4)
            p.setBrush(QColor(255, 255, 255, w_alpha))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(cx, cy), r * 0.45, r * 0.45)

        # selection ring (green)
        if self._selected:
            p.setPen(QPen(QColor("#2ecc71"), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r + 3, r + 3)


# ── CANVAS 2D ────────────────────────────────────────────────────────────
class Canvas2D(QFrame):
    """Dark 16:9 frame hosting ParLed widgets. Hit-test + drag handling."""

    fixture_moved = Signal(str, float, float)  # fixture_id, x_norm, y_norm
    fixture_selected = Signal(str)              # fixture_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("previewCanvas")
        self.setMinimumSize(400, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            "QFrame#previewCanvas { background: #0a0a0a; border: 1px solid #2a2a2a; }"
        )
        self._leds: dict[str, ParLed] = {}

    # ── public API
    def add_fixture(
        self, fixture_id: str, name: str, x: float, y: float,
        drgbw: tuple[int, int, int, int, int] = (0, 0, 0, 0, 0),
    ) -> ParLed:
        led = ParLed(fixture_id, name, self)
        led.set_position(x, y)
        led.set_drgbw(*drgbw)
        led.show()
        self._leds[fixture_id] = led
        return led

    def remove_fixture(self, fixture_id: str) -> None:
        led = self._leds.pop(fixture_id, None)
        if led:
            led.deleteLater()

    def clear(self) -> None:
        for led in list(self._leds.values()):
            led.deleteLater()
        self._leds.clear()

    def set_fixture_drgbw(
        self, fixture_id: str, d: int, r: int, g: int, b: int, w: int,
    ) -> None:
        led = self._leds.get(fixture_id)
        if led:
            led.set_drgbw(d, r, g, b, w)

    def set_selected(self, fixture_id: str) -> None:
        for fid, led in self._leds.items():
            led.set_selected(fid == fixture_id)

    def fixture_ids(self) -> list[str]:
        return list(self._leds.keys())

    def get_led(self, fixture_id: str) -> ParLed | None:
        return self._leds.get(fixture_id)

    # ── layout helpers
    def place_led(self, led: ParLed) -> None:
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return
        cx = int(led._x_norm * w)  # noqa: SLF001 — internal coord handoff
        cy = int(led._y_norm * h)  # noqa: SLF001
        led.move(cx - led.width() // 2, cy - led.height() // 2)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for led in self._leds.values():
            self.place_led(led)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        # Faint 10×10 grid
        p.setPen(QPen(QColor(40, 40, 40), 1))
        w, h = self.width(), self.height()
        for i in range(1, 10):
            x = int(w * i / 10)
            y = int(h * i / 10)
            p.drawLine(x, 0, x, h)
            p.drawLine(0, y, w, y)
        # Center crosshair (subtle dashed)
        p.setPen(QPen(QColor(60, 60, 60), 1, Qt.PenStyle.DashLine))
        p.drawLine(w // 2, 0, w // 2, h)
        p.drawLine(0, h // 2, w, h // 2)

    # ── drag (called by ParLed)
    def select(self, fixture_id: str) -> None:
        self.set_selected(fixture_id)
        self.fixture_selected.emit(fixture_id)

    def drag_led(self, led: ParLed, global_pos: QPointF) -> None:
        local = self.mapFromGlobal(global_pos.toPoint())
        w, h = self.width(), self.height()
        x = max(0, min(w, local.x()))
        y = max(0, min(h, local.y()))
        new_x = round(x / w, 4) if w else 0.0
        new_y = round(y / h, 4) if h else 0.0
        if (new_x, new_y) != (led._x_norm, led._y_norm):  # noqa: SLF001
            led._x_norm = new_x  # noqa: SLF001
            led._y_norm = new_y  # noqa: SLF001
            self.place_led(led)

    def end_drag(self, led: ParLed) -> None:
        x, y = led.position()
        self.fixture_moved.emit(led.fixture_id, x, y)


# ── XY SIDEBAR ───────────────────────────────────────────────────────────
class XySidebar(QFrame):
    """Right panel: X/Y spinboxes + Center/Reset for the selected fixture."""

    xy_changed = Signal(str, float, float)  # fixture_id, x_norm, y_norm
    center_requested = Signal(str)
    reset_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("xySidebar")
        self.setFixedWidth(200)
        self.setStyleSheet(
            "QFrame#xySidebar { background: #141414; border-left: 1px solid #2a2a2a; }"
        )
        self._current_id: str | None = None
        self._suppress = False
        self._build()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        title = QLabel("Selected Fixture")
        title.setStyleSheet("color: #2ecc71; font-weight: 700; font-size: 12px;")
        v.addWidget(title)

        self.name_lbl = QLabel("—")
        self.name_lbl.setStyleSheet("color: #e8e8e8; font-size: 11px;")
        self.name_lbl.setWordWrap(True)
        v.addWidget(self.name_lbl)

        self.addr_lbl = QLabel("")
        self.addr_lbl.setStyleSheet("color: #707070; font-size: 10px;")
        v.addWidget(self.addr_lbl)

        v.addSpacing(8)

        x_lbl = QLabel("X (0.000 – 1.000)")
        x_lbl.setStyleSheet("color: #707070; font-size: 10px;")
        v.addWidget(x_lbl)
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(0.0, 1.0)
        self.x_spin.setSingleStep(0.001)
        self.x_spin.setDecimals(3)
        self.x_spin.setEnabled(False)
        self.x_spin.valueChanged.connect(self._on_x_changed)
        v.addWidget(self.x_spin)

        y_lbl = QLabel("Y (0.000 – 1.000)")
        y_lbl.setStyleSheet("color: #707070; font-size: 10px;")
        v.addWidget(y_lbl)
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(0.0, 1.0)
        self.y_spin.setSingleStep(0.001)
        self.y_spin.setDecimals(3)
        self.y_spin.setEnabled(False)
        self.y_spin.valueChanged.connect(self._on_y_changed)
        v.addWidget(self.y_spin)

        v.addSpacing(8)

        self.center_btn = QPushButton("Center")
        self.center_btn.setEnabled(False)
        self.center_btn.clicked.connect(self._on_center)
        v.addWidget(self.center_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setEnabled(False)
        self.reset_btn.clicked.connect(self._on_reset)
        v.addWidget(self.reset_btn)

        v.addStretch(1)

    # ── public API
    def set_fixture(
        self, fixture_id: str, name: str, start: int, x: float, y: float,
    ) -> None:
        self._current_id = fixture_id
        self.name_lbl.setText(name)
        self.addr_lbl.setText(f"start: {start}")
        self._suppress = True
        self.x_spin.setValue(x)
        self.y_spin.setValue(y)
        self._suppress = False
        self.x_spin.setEnabled(True)
        self.y_spin.setEnabled(True)
        self.center_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)

    def clear(self) -> None:
        self._current_id = None
        self.name_lbl.setText("—")
        self.addr_lbl.setText("")
        self._suppress = True
        self.x_spin.setValue(0.0)
        self.y_spin.setValue(0.0)
        self._suppress = False
        self.x_spin.setEnabled(False)
        self.y_spin.setEnabled(False)
        self.center_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)

    # ── slots
    def _on_x_changed(self, val: float) -> None:
        if self._suppress or not self._current_id:
            return
        self.xy_changed.emit(self._current_id, val, self.y_spin.value())

    def _on_y_changed(self, val: float) -> None:
        if self._suppress or not self._current_id:
            return
        self.xy_changed.emit(self._current_id, self.x_spin.value(), val)

    def _on_center(self) -> None:
        if self._current_id:
            self.center_requested.emit(self._current_id)

    def _on_reset(self) -> None:
        if self._current_id:
            self.reset_requested.emit(self._current_id)
