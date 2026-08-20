"""
RMS Energy Chart — line plot of RMS values over time.
Fills under the curve in green for the energy "envelope" visualization.
"""
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF
from PySide6.QtWidgets import QWidget


class RMSChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.times = []
        self.values = []
        self.setMinimumHeight(120)
        self.setObjectName("rmsChart")

    def set_data(self, times, values):
        self.times = list(times) if times else []
        self.values = list(values) if values else []
        self.update()

    def clear(self):
        self.times = []
        self.values = []
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        ml, mr, mt, mb = 50, 12, 10, 25
        plot_w = w - ml - mr
        plot_h = h - mt - mb

        # Background
        p.fillRect(self.rect(), QColor("#0d0d0d"))

        if not self.values or not self.times:
            p.setPen(QPen(QColor("#3a3a3a")))
            p.setFont(QFont("Segoe UI", 9))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "No data — load + analyze an audio file")
            return

        # Plot frame
        plot_rect = QRectF(ml, mt, plot_w, plot_h)
        p.fillRect(plot_rect, QColor("#141414"))
        p.setPen(QPen(QColor("#2a2a2a"), 1))
        p.drawRect(plot_rect)

        # Grid (4 horizontal)
        p.setPen(QPen(QColor("#1f1f1f"), 1))
        for i in range(1, 4):
            y = mt + plot_h * i / 4
            p.drawLine(ml, int(y), ml + plot_w, int(y))

        # Scales
        t_max = max(self.times) if self.times else 1.0
        v_max = max(self.values) * 1.1 if self.values else 1.0
        if v_max <= 0:
            v_max = 1.0

        def to_x(t):
            return ml + (t / t_max) * plot_w

        def to_y(v):
            return mt + plot_h - (v / v_max) * plot_h

        # Filled polygon
        fill = QPolygonF()
        fill.append(QPointF(ml, mt + plot_h))
        for t, v in zip(self.times, self.values):
            fill.append(QPointF(to_x(t), to_y(v)))
        fill.append(QPointF(ml + plot_w, mt + plot_h))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(46, 204, 113, 60)))
        p.drawPolygon(fill)

        # Line
        line = QPolygonF()
        for t, v in zip(self.times, self.values):
            line.append(QPointF(to_x(t), to_y(v)))
        p.setPen(QPen(QColor("#2ecc71"), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolyline(line)

        # Axis labels
        p.setPen(QPen(QColor("#707070")))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(ml, mt + plot_h + 16, "0:00")
        p.drawText(ml + plot_w - 35, mt + plot_h + 16, f"{int(t_max)}s")
        p.drawText(5, mt + 10, f"{v_max:.2f}")
        p.drawText(5, mt + plot_h - 2, "0.00")
        p.drawText(ml, mt - 2, "RMS Energy")
