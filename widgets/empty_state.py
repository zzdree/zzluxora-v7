"""
widgets/empty_state.py — zzluxora v6.0

Empty state shown di main area saat belum ada .zlx yang di-load.
- Logo brand samar (opacity 0.3)
- "Silahkan buka project untuk memulai"
- Tombol "Open Project" (large, centered)
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy


class EmptyState(QWidget):
    """
    Empty state shown sebelum project di-load.
    """

    open_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("emptyState")
        self.setStyleSheet("background-color: #0d0d0d;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Spacer top
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Brand logo (samar)
        self.logo_label = QLabel("zzluxora")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet(
            "color: #2ecc71;"
            "font-size: 64px;"
            "font-weight: 900;"
            "font-style: italic;"
            "letter-spacing: 6px;"
            "opacity: 0.3;"
        )
        layout.addWidget(self.logo_label)

        # Subtitle (samar)
        self.sub_label = QLabel("Audio-Reactive Lighting Design System")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet(
            "color: #707070; font-size: 13px; opacity: 0.5;"
        )
        layout.addWidget(self.sub_label)

        # Spacer
        layout.addSpacing(60)

        # Prompt
        self.prompt_label = QLabel("Silahkan buka project untuk memulai")
        self.prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prompt_label.setStyleSheet("color: #b0b0b0; font-size: 15px;")
        layout.addWidget(self.prompt_label)

        # Spacer
        layout.addSpacing(20)

        # Open Project button
        self.open_btn = QPushButton("Open Project")
        self.open_btn.setMinimumSize(180, 44)
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: #0d0d0d;
                border: none;
                border-radius: 4px;
                padding: 12px 28px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.open_btn.clicked.connect(self.open_clicked.emit)
        layout.addWidget(self.open_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Spacer bottom
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
