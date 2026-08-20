"""
ArtNetStatusPill — header-right status indicator.

States:
  - "connected"    green dot + green text   (--ok)
  - "disconnected" red dot + red text      (--err)
  - "connecting"   blue dot + blue text     (--info)

QSS uses dynamic property `state` to swap colours (see styles.py).
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel


class ArtNetStatusPill(QFrame):
    """Compact status indicator: [dot] Art-Net: Connected/Disconnected/Connecting…"""

    clicked = Signal()  # future: open Output tab

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("artnetPill")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 10, 2)
        layout.setSpacing(0)

        self._dot = QLabel()
        self._dot.setObjectName("artnetDot")
        self._dot.setProperty("state", "disconnected")
        self._dot.setFixedSize(10, 10)
        layout.addWidget(self._dot)

        self._text = QLabel("Art-Net: Disconnected")
        self._text.setObjectName("artnetText")
        self._text.setProperty("state", "disconnected")
        layout.addWidget(self._text)

        self._state: str = "disconnected"

    # ── public API
    def set_state(self, state: str) -> None:
        """state ∈ {"connected", "disconnected", "connecting"}"""
        if state not in ("connected", "disconnected", "connecting"):
            state = "disconnected"

        self._state = state
        labels = {
            "connected":    "Art-Net: Connected",
            "disconnected": "Art-Net: Disconnected",
            "connecting":   "Art-Net: Connecting…",
        }
        self._text.setText(labels[state])
        # Update dynamic property → QSS re-applies
        self._dot.setProperty("state", state)
        self._text.setProperty("state", state)
        # Force re-style
        self._dot.style().unpolish(self._dot)
        self._dot.style().polish(self._dot)
        self._text.style().unpolish(self._text)
        self._text.style().polish(self._text)

    def state(self) -> str:
        return self._state

    # ── click → open Output tab (wired by parent)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
