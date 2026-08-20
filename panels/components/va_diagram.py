"""
V-A Diagram — Valence-Arousal scatter plot with quadrants.
Quadrants:
  Top-left  (V<0.5, A>0.5): Anxious/Tense
  Top-right (V>0.5, A>0.5): Happy/Energetic
  Bot-left  (V<0.5, A<0.5): Sad/Calm
  Bot-right (V>0.5, A<0.5): Content/Relaxed
"""
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget


class VADiagram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.V = None
        self.A = None
        self.setMinimumSize(280, 280)
        self.setObjectName("vaDiagram")

    def set_point(self, V: float, A: float):
        self.V = float(V)
        self.A = float(A)
        self.update()

    def clear(self):
        self.V = None
        self.A = None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        margin = 30
        plot_w = w - 2 * margin
        plot_h = h - 2 * margin

        # Background
        p.fillRect(self.rect(), QColor("#0d0d0d"))

        # Plot area
        plot_rect = QRectF(margin, margin, plot_w, plot_h)
        p.fillRect(plot_rect, QColor("#141414"))
        p.setPen(QPen(QColor("#2a2a2a"), 1))
        p.drawRect(plot_rect)

        # Grid (4x4)
        p.setPen(QPen(QColor("#1f1f1f"), 1))
        for i in range(1, 4):
            x = margin + plot_w * i / 4
            y = margin + plot_h * i / 4
            p.drawLine(int(x), margin, int(x), margin + plot_h)
            p.drawLine(margin, int(y), margin + plot_w, int(y))

        # Crosshair at 0.5, 0.5
        cx = margin + plot_w * 0.5
        cy = margin + plot_h * 0.5
        p.setPen(QPen(QColor("#3a3a3a"), 1, Qt.PenStyle.DashLine))
        p.drawLine(int(cx), margin, int(cx), margin + plot_h)
        p.drawLine(margin, int(cy), margin + plot_w, int(cy))

        # Axis numbers
        p.setPen(QPen(QColor("#707070")))
        font = QFont("Segoe UI", 8)
        p.setFont(font)
        p.drawText(margin - 18, int(cy) + 4, "0.5")
        p.drawText(margin + plot_w + 4, int(cy) + 4, "0.5")
        p.drawText(int(cx) - 8, margin + plot_h + 15, "0.5")
        p.drawText(int(cx) - 8, margin - 5, "0.5")
        p.drawText(margin - 18, margin + 10, "1.0")
        p.drawText(margin - 14, margin + plot_h - 2, "0.0")
        p.drawText(margin + plot_w - 12, margin + 10, "1.0")
        p.drawText(margin + plot_w - 12, margin + plot_h - 2, "0.0")

        # Axis labels
        font_b = QFont("Segoe UI", 9, QFont.Weight.Bold)
        p.setFont(font_b)
        p.drawText(margin + plot_w // 2 - 35, h - 5, "Valence →")
        p.save()
        p.translate(15, margin + plot_h // 2 + 30)
        p.rotate(-90)
        p.drawText(0, 0, "← Arousal")
        p.restore()

        # Quadrant labels
        font_q = QFont("Segoe UI", 7, QFont.Weight.Bold)
        p.setFont(font_q)
        p.setPen(QPen(QColor("#3a3a3a")))
        p.drawText(margin + 6, margin + 14, "ANXIOUS")
        p.drawText(margin + plot_w - 50, margin + 14, "HAPPY")
        p.drawText(margin + 6, margin + plot_h - 6, "SAD")
        p.drawText(margin + plot_w - 65, margin + plot_h - 6, "CONTENT")

        # Point with glow
        if self.V is not None and self.A is not None:
            px = margin + plot_w * self.V
            py = margin + plot_h * (1.0 - self.A)
            for r, alpha in [(16, 40), (11, 80), (6, 140)]:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(46, 204, 113, alpha)))
                p.drawEllipse(QPointF(px, py), r, r)
            p.setBrush(QBrush(QColor("#2ecc71")))
            p.setPen(QPen(QColor("#ffffff"), 2))
            p.drawEllipse(QPointF(px, py), 5, 5)
