"""
Toast — non-blocking notification that auto-dismisses.
Pinned bottom-right of parent widget.
"""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout


class Toast(QFrame):
    def __init__(self, parent, message: str, toast_type: str = "info", duration_ms: int = 3000):
        super().__init__(parent)
        self.setObjectName("toast")
        color_map = {
            "info": "#2ecc71",
            "success": "#2ecc71",
            "warning": "#f39c12",
            "error": "#e74c3c",
        }
        # DESIGN.md §5.3 + Appendix A.3: geometric markers, no emoji
        icon_map = {"info": "●", "success": "●", "warning": "○", "error": "■"}
        color = color_map.get(toast_type, "#2ecc71")
        icon = icon_map.get(toast_type, "•")
        self.setStyleSheet(
            f"QFrame#toast {{ background-color: #1a1a1a; border: 1px solid {color}; "
            f"border-radius: 6px; padding: 10px 16px; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 700; border: none;")
        layout.addWidget(icon_label)
        msg_label = QLabel(message)
        msg_label.setStyleSheet("color: #e8e8e8; font-size: 11px; border: none;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)
        self.adjustSize()
        if parent:
            pw, ph = parent.width(), parent.height()
            tw = max(200, self.sizeHint().width())
            th = max(40, self.sizeHint().height())
            self.move(pw - tw - 20, ph - th - 60)
        QTimer.singleShot(duration_ms, self.deleteLater)
        self.show()


def show_toast(parent, message, toast_type="info", duration_ms=3000):
    return Toast(parent, message, toast_type, duration_ms)
