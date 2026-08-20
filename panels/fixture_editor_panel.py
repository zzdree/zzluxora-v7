"""
Fixture Editor panel — MDI host (feedback baris 142).

Each "New" or "Open" spawns a draggable QMdiSubWindow containing a
FixtureEditorForm. QMdiArea natively clamps windows inside the box, lets them
stack/overlap, and gives each a title bar with min/max/close.

Form: name / manufacturer / channels (< >) / type + 3-col channel table
(Ch | Label | Type) + Save. Save writes to fixtures/<name>.json via
FixtureManager.
"""
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QMessageBox, QAbstractItemView, QComboBox, QFileDialog,
    QMdiArea, QMdiSubWindow,
)
from panels import BasePanel
from fixture_manager import FixtureManager
from engines.fixture_types import (
    FIXTURE_TYPES, BUILTIN_CHANNEL_LABELS, CHANNEL_ROLES, infer_role,
)


class FixtureEditorForm(QWidget):
    """Single fixture-edit form. Lives inside a QMdiSubWindow.

    Emits `saved` after a successful write so the host can refresh lists.
    """
    saved = Signal()

    def __init__(self, manager: FixtureManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setObjectName("panelContent")
        self._build_ui()
        self._sync_table()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Generic PAR RGBW 4ch")
        self.mfr_edit = QLineEdit("Generic")
        self.ch_spin = QSpinBox()              # feedback baris 144: channel dengan < >
        self.ch_spin.setRange(1, 64)
        self.ch_spin.setValue(4)
        self.ch_spin.valueChanged.connect(self._sync_table)

        form.addRow("Name *:", self.name_edit)
        form.addRow("Manufacturer:", self.mfr_edit)
        form.addRow("Channels:", self.ch_spin)
        self.type_combo = QComboBox()
        for t in FIXTURE_TYPES.keys():
            self.type_combo.addItem(t)
        self.type_combo.setCurrentText("Custom")
        self.type_combo.currentTextChanged.connect(self._on_type_change)
        form.addRow("Type:", self.type_combo)
        fw = QWidget()
        fw.setLayout(form)
        root.addWidget(fw)

        lbl = QLabel("Channel Map")
        lbl.setObjectName("sectionTitle")
        root.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setObjectName("channelTable")
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Ch", "Label", "Type"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget#channelTable {
                background-color: #141414; gridline-color: #2a2a2a;
                border: 1px solid #2a2a2a; border-radius: 4px;
                color: #e8e8e8; font-size: 12px;
            }
            QTableWidget#channelTable::item { padding: 4px; }
            QTableWidget#channelTable::item:selected {
                background-color: #1f1f1f; color: #2ecc71;
            }
            QHeaderView::section {
                background-color: #1a1a1a; color: #707070; padding: 6px;
                border: none; border-bottom: 1px solid #2a2a2a;
                font-size: 11px; font-weight: 700;
            }
        """)
        root.addWidget(self.table, 1)

        # feedback baris 151: tombol save di bawah
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("Save Fixture")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: #0d0d0d; "
            "border: 1px solid #2ecc71; font-weight: 700; padding: 4px 14px; }"
            "QPushButton:hover { background-color: #27ae60; }"
        )
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

    def _sync_table(self):
        n = self.ch_spin.value()
        self.table.setRowCount(n)
        defaults = ["Dimmer", "Red", "Green", "Blue", "White",
                    "Amber", "UV", "Program", "Speed", "Strobe", "Pan", "Tilt"]
        for i in range(n):
            ch_item = QTableWidgetItem(str(i + 1))
            ch_item.setFlags(ch_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            ch_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            ch_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(i, 0, ch_item)

            existing = self.table.item(i, 1)
            label = existing.text() if existing and existing.text() else (
                defaults[i] if i < len(defaults) else f"Ch {i+1}"
            )
            self.table.setItem(i, 1, QTableWidgetItem(label))

            existing_combo = self.table.cellWidget(i, 2)
            if existing_combo is None:
                combo = QComboBox()
                combo.addItems(CHANNEL_ROLES)
                self.table.setCellWidget(i, 2, combo)
            else:
                existing_combo.blockSignals(True)
                cur = existing_combo.currentText()
                existing_combo.clear()
                existing_combo.addItems(CHANNEL_ROLES)
                if cur in CHANNEL_ROLES:
                    existing_combo.setCurrentText(cur)
                existing_combo.blockSignals(False)

    def load_data(self, data: dict):
        """Populate the form from a parsed fixture dict (used by Open)."""
        self.name_edit.setText(str(data.get("name", "")))
        self.mfr_edit.setText(str(data.get("manufacturer", "Generic")))
        if data.get("type"):
            idx = self.type_combo.findText(str(data["type"]))
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        ch = int(data.get("channels", 4))
        self.ch_spin.setValue(ch)
        for i, entry in enumerate(data.get("channel_map", [])[:ch]):
            label = str(entry.get("label", f"Ch {i+1}"))
            self.table.setItem(i, 1, QTableWidgetItem(label))
            combo = self.table.cellWidget(i, 2)
            if combo is None:
                combo = QComboBox()
                combo.addItems(CHANNEL_ROLES)
                self.table.setCellWidget(i, 2, combo)
            explicit = entry.get("type")
            combo.setCurrentText(explicit if explicit in CHANNEL_ROLES else infer_role(label))

    def _on_save(self):
        ch_map = []
        for i in range(self.table.rowCount()):
            label_item = self.table.item(i, 1)
            label = label_item.text().strip() if label_item else ""
            if not label:
                label = f"Ch {i + 1}"
            combo = self.table.cellWidget(i, 2)
            ch_type = combo.currentText() if combo else infer_role(label)
            ch_map.append({"ch": i + 1, "label": label, "type": ch_type})

        data = {
            "name": self.name_edit.text().strip(),
            "manufacturer": self.mfr_edit.text().strip() or "Generic",
            "type": self.type_combo.currentText(),
            "channels": self.ch_spin.value(),
            "channel_map": ch_map,
        }
        ok, msg = self.manager.save_fixture(data)
        if ok:
            QMessageBox.information(self, "Saved", msg)
            self.saved.emit()
        else:
            QMessageBox.warning(self, "Save Failed", msg)

    def _on_type_change(self, type_name: str) -> None:
        if type_name not in FIXTURE_TYPES:
            return
        ch_labels = FIXTURE_TYPES[type_name]
        if not ch_labels:
            return  # Custom — leave channels alone
        existing = []
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 1)
            existing.append(item.text() if item else "")
        defaults_set = set(BUILTIN_CHANNEL_LABELS)
        non_default = [l for l in existing if l and l not in defaults_set]
        if non_default:
            preview = ", ".join(ch_labels[:6])
            if len(ch_labels) > 6:
                preview += "..."
            reply = QMessageBox.question(
                self, "Overwrite Channels?",
                f"Type '{type_name}' will overwrite current channel labels with:\n"
                f"{preview}\n\nContinue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.type_combo.blockSignals(True)
                self.type_combo.setCurrentText("Custom")
                self.type_combo.blockSignals(False)
                return
        self.ch_spin.setValue(len(ch_labels))
        self.table.setRowCount(len(ch_labels))
        for i, label in enumerate(ch_labels):
            ch_item = QTableWidgetItem(str(i + 1))
            ch_item.setFlags(ch_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            ch_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            ch_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(i, 0, ch_item)
            self.table.setItem(i, 1, QTableWidgetItem(label))
            role_combo = self.table.cellWidget(i, 2)
            if role_combo is None:
                role_combo = QComboBox()
                role_combo.addItems(CHANNEL_ROLES)
                self.table.setCellWidget(i, 2, role_combo)
            role_combo.setCurrentText(infer_role(label))


class FixtureEditorPanel(BasePanel):
    PANEL_NAME = "Fixture Editor"
    PANEL_DESC = ("Create a new fixture or open one to edit. Each opens a movable "
                  "window inside the box (drag, stack, min/max/close).")

    fixture_saved = Signal()

    def __init__(self, manager: FixtureManager, parent=None):
        self.manager = manager
        self._win_count = 0
        super().__init__(parent)

    def _build_ui(self):
        super()._build_ui()

        # Toolbar — feedback baris 136: tombol Open dan New
        btn_row = QHBoxLayout()
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self._on_new)
        btn_row.addWidget(new_btn)
        open_btn = QPushButton("Open…")
        open_btn.setToolTip("Load a fixture .json file")
        open_btn.clicked.connect(self._on_open)
        btn_row.addWidget(open_btn)
        btn_row.addStretch()
        self.add_widget(self._wrap(btn_row))

        # feedback baris 142: kotak besar tempat window editor (MDI)
        self.mdi = QMdiArea()
        self.mdi.setObjectName("fixtureMdi")
        self.mdi.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdi.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdi.setStyleSheet("QMdiArea#fixtureMdi { background-color: #0d0d0d; }")
        self.mdi.setMinimumHeight(420)
        self.add_widget(self.mdi)

    def _wrap(self, layout):
        w = QWidget()
        w.setLayout(layout)
        return w

    def _spawn(self, title: str) -> FixtureEditorForm:
        form = FixtureEditorForm(self.manager)
        form.saved.connect(self.fixture_saved.emit)
        sub = QMdiSubWindow()
        sub.setWidget(form)
        sub.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        sub.setWindowTitle(title)
        sub.resize(460, 480)
        self.mdi.addSubWindow(sub)
        # cascade so stacked windows don't fully overlap
        offset = (self._win_count % 6) * 26
        sub.move(20 + offset, 20 + offset)
        self._win_count += 1
        sub.show()
        return form

    def _on_new(self):
        self._spawn(f"New Fixture {self._win_count + 1}")

    def _on_open(self):
        fixtures_dir = Path("fixtures")
        start_dir = fixtures_dir if fixtures_dir.is_dir() else Path.home()
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Fixture", str(start_dir),
            "Fixture JSON (*.json);;All files (*.*)"
        )
        if not path:
            return
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Open Failed", f"Could not parse JSON:\n{e}")
            return
        form = self._spawn(Path(path).name)
        form.load_data(data)
