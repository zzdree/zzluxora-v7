"""
Waveform View — static display of audio waveform.
Renders min/max envelope per pixel column from raw audio samples.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import QWidget


class WaveformView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.y_data = None
        self.sr = 22050
        self.setMinimumHeight(80)
        self.setObjectName("waveformView")

    def set_data(self, y_data, sr: int = 22050):
        self.y_data = y_data
        self.sr = sr
        self.update()

    def clear(self):
        self.y_data = None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        mid = h / 2.0

        # Background
        p.fillRect(self.rect(), QColor("#0d0d0d"))

        if self.y_data is None or len(self.y_data) == 0:
            p.setPen(QPen(QColor("#3a3a3a")))
            p.setFont(QFont("Segoe UI", 9))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No waveform")
            return

        # Center line
        p.setPen(QPen(QColor("#1f1f1f"), 1))
        p.drawLine(0, int(mid), w, int(mid))

        # Downsample to width pixels
        n = len(self.y_data)
        samples_per_pixel = max(1, n // w)
        max_amp = max(abs(v) for v in self.y_data[:min(n, 100000)]) or 1.0

        # Waveform
        p.setPen(QPen(QColor("#3498db"), 1))
        for x in range(w):
            start = x * samples_per_pixel
            end = min(start + samples_per_pixel, n)
            if start >= end:
                break
            chunk = self.y_data[start:end]
            y_min = min(chunk) / max_amp
            y_max = max(chunk) / max_amp
            y1 = mid - y_max * mid * 0.9
            y2 = mid - y_min * mid * 0.9
            p.drawLine(x, int(y1), x, int(y2))

        # Label
        p.setPen(QPen(QColor("#707070")))
        p.setFont(QFont("Segoe UI", 8))
        duration = n / self.sr if self.sr else 0
        p.drawText(5, 12, f"Waveform — {duration:.1f}s @ {self.sr} Hz")
