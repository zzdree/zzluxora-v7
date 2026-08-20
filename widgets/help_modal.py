"""
Help Modal — keyboard shortcut reference dialog (F1).
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDialogButtonBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton
)


class HelpDialog(QDialog):
    SHORTCUTS = [
        ("Ctrl+1..5", "Switch sidebar panel (1=Program, 2=Fixtures, etc.)"),
        ("Ctrl+O", "Open project (.zlx)"),
        ("Ctrl+S", "Save project (.zlx)"),
        ("Ctrl+Shift+S", "Save project as..."),
        ("Space", "Play / Stop chase (Program -> Chase tab)"),
        ("B", "Blackout all DMX"),
        ("Esc", "Emergency stop (chase + blackout)"),
        ("F1", "Show this help"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        # Phase 9: renamed to match new menu label
        self.setWindowTitle("zzluxora — Shortcuts")
        self.resize(600, 400)
        self.setStyleSheet("background-color: #0d0d0d; color: #e8e8e8;")
        layout = QVBoxLayout(self)
        # feedback baris 23: tombol close di atas (X pojok) + bawah (tengah)
        header_row = QHBoxLayout()
        title = QLabel("Shortcuts")
        title.setStyleSheet("color: #2ecc71; font-size: 18px; font-weight: 700;")
        header_row.addWidget(title)
        header_row.addStretch()
        close_x = QPushButton("✕")
        close_x.setFixedSize(28, 28)
        close_x.setToolTip("Close")
        close_x.clicked.connect(self.reject)
        close_x.setStyleSheet("""
            QPushButton { background-color: transparent; color: #707070;
                border: none; font-size: 16px; font-weight: 700; }
            QPushButton:hover { color: #e74c3c; }
        """)
        header_row.addWidget(close_x, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header_row)

        table = QTableWidget(len(self.SHORTCUTS), 2)
        table.setHorizontalHeaderLabels(["Shortcut", "Action"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setStyleSheet("""
            QTableWidget { background-color: #141414; gridline-color: #2a2a2a;
                border: 1px solid #2a2a2a; }
            QTableWidget::item { color: #e8e8e8; padding: 6px 10px; }
            QHeaderView::section { background-color: #1a1a1a; color: #2ecc71;
                padding: 8px; border: none; font-weight: 700; }
        """)
        for i, (sc, action) in enumerate(self.SHORTCUTS):
            sc_item = QTableWidgetItem(sc)
            sc_item.setForeground(Qt.GlobalColor.green)
            action_item = QTableWidgetItem(action)
            sc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # v6: center shortcut col
            table.setItem(i, 0, sc_item)
            table.setItem(i, 1, action_item)
        layout.addWidget(table, 1)

        # feedback baris 23: tombol close bawah taruh tengah
        close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn.setCenterButtons(True)
        close_btn.rejected.connect(self.reject)
        close_btn.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: #0d0d0d;
                border: 1px solid #2ecc71; padding: 6px 14px; font-weight: 700; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        layout.addWidget(close_btn)
