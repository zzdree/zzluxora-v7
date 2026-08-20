"""
Onboarding — first-run checklist overlay.
5 steps: fixtures → patch → analyze → connect Art-Net → test chase.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QFrame
)


class OnboardingOverlay(QWidget):
    def __init__(self, parent=None, manager=None):
        super().__init__(parent)
        self.manager = manager
        self.setStyleSheet("background-color: rgba(0, 0, 0, 220);")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setMaximumSize(620, 540)
        card.setStyleSheet("""
            QFrame {
                background-color: #141414; border: 1px solid #2ecc71;
                border-radius: 8px; padding: 24px;
            }
        """)
        card_l = QVBoxLayout(card)
        card_l.setSpacing(10)

        title = QLabel("Welcome to zzluxora v6.0")
        title.setStyleSheet("color: #2ecc71; font-size: 18px; font-weight: 700; border: none;")
        card_l.addWidget(title)
        sub = QLabel("Complete these steps before your first show:")
        sub.setStyleSheet("color: #707070; font-size: 11px; border: none;")
        sub.setWordWrap(True)
        card_l.addWidget(sub)

        steps = [
            ("Define your fixtures", "Fixtures → New (1+ fixtures)"),
            ("Patch fixtures to DMX addresses", "Program → Address tab → drag fixtures"),
            ("Analyze a song", "Program → Analyze tab → load WAV"),
            ("Connect Art-Net output", "Program → Output tab → set IP + Connect"),
            ("Test a chase", "Program → Chase tab → Play"),
        ]
        for step_title, step_desc in steps:
            row = QHBoxLayout()
            chk = QCheckBox()
            chk.setStyleSheet("""
                QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #2a2a2a; }
                QCheckBox::indicator:checked { background-color: #2ecc71; border: 1px solid #2ecc71; }
            """)
            row.addWidget(chk)
            col = QVBoxLayout()
            t = QLabel(step_title)
            t.setStyleSheet("color: #e8e8e8; font-size: 12px; font-weight: 600; border: none;")
            d = QLabel(step_desc)
            d.setStyleSheet("color: #707070; font-size: 10px; border: none;")
            col.addWidget(t)
            col.addWidget(d)
            row.addLayout(col, 1)
            card_l.addLayout(row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        dismiss = QPushButton("Got it — let's go")
        dismiss.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: #0d0d0d;
                border: 1px solid #2ecc71; padding: 8px 16px; font-weight: 700; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        dismiss.clicked.connect(self.close)
        btn_row.addWidget(dismiss)
        card_l.addLayout(btn_row)

        root.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            self.resize(self.parent().size())
