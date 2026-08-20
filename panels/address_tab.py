"""
Address tab — embeds AddressGrid + a small toolbar (Clear, Auto-patch).
"""
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QDialog, QFormLayout, QSpinBox, QCheckBox, QDialogButtonBox
)
from widgets import AddressGrid
from fixture_manager import FixtureManager
from engines.fixture_types import infer_role


# FIX 3: type/label → color mapping (feedback b61: warna sesuai channel type)
# Keys are lowercase. Checked against ch_map[offset]["type"] and ch_map[offset]["label"].
TYPE_COLOR_MAP = {
    "dimmer":  QColor("#f1c40f"),  # yellow
    "red":     QColor("#e74c3c"),
    "green":   QColor("#2ecc71"),
    "blue":    QColor("#3498db"),
    "white":   QColor("#e8e8e8"),
    "amber":   QColor("#f39c12"),
    "uv":      QColor("#9b59b6"),
    "strobe":  QColor("#95a5a6"),
    "program": QColor("#7f8c8d"),
    "speed":   QColor("#95a5a6"),
    # High-level roles (from infer_role fallback)
    "intensity": QColor("#f1c40f"),
    "color":     QColor("#ff6b6b"),
    "position":  QColor("#1abc9c"),
    "beam":      QColor("#e67e22"),
    "effect":    QColor("#9b59b6"),
    "function":  QColor("#34495e"),
}

# Cyclic fallback for channels without a recognizable type/label
_FALLBACK_COLORS = [
    QColor("#e74c3c"), QColor("#ff6b6b"), QColor("#2ecc71"),
    QColor("#3498db"), QColor("#f1c40f"), QColor("#9b59b6"),
    QColor("#1abc9c"), QColor("#e67e22"), QColor("#34495e"),
    QColor("#7f8c8d"),
]


def _channel_color(ch_entry: dict, offset: int) -> QColor:
    """Lookup color for a channel: type → label → infer_role → cyclic fallback."""
    # 1. Try explicit type field
    t = (ch_entry.get("type") or "").strip().lower()
    if t in TYPE_COLOR_MAP:
        return TYPE_COLOR_MAP[t]
    # 2. Try label as-is
    lbl = (ch_entry.get("label") or "").strip().lower()
    if lbl in TYPE_COLOR_MAP:
        return TYPE_COLOR_MAP[lbl]
    # 3. Try infer_role (returns role name like "Intensity", "Color", etc.)
    role = infer_role(ch_entry.get("label", "")).lower()
    if role in TYPE_COLOR_MAP:
        return TYPE_COLOR_MAP[role]
    # 4. Cyclic fallback
    return _FALLBACK_COLORS[offset % len(_FALLBACK_COLORS)]


class AddressTab(QWidget):
    def __init__(self, manager: FixtureManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setObjectName("panelContent")
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel("DMX Address Patch")
        title.setObjectName("panelTitle")
        header.addWidget(title)
        header.addStretch()

        self.status_label = QLabel("0 fixtures patched")
        self.status_label.setObjectName("dim")
        header.addWidget(self.status_label)
        root.addLayout(header)

        sub = QLabel("Drag fixtures from the Fixture List panel to a cell. "
                     "Click a patched cell to unpatch.")
        sub.setObjectName("panelDesc")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Toolbar — Phase 17: more buttons (random, group-by-type)
        tb = QHBoxLayout()
        clear_btn = QPushButton("Clear")  # Phase 18: no emoji
        clear_btn.clicked.connect(self._on_clear)
        tb.addWidget(clear_btn)

        auto_btn = QPushButton("Auto-Sequential")  # Phase 18: no emoji
        auto_btn.clicked.connect(self._on_auto)
        tb.addWidget(auto_btn)

        random_btn = QPushButton("Random")  # Phase 18: no emoji
        random_btn.setToolTip("Patch each fixture at a random start address")
        random_btn.clicked.connect(self._on_random)
        tb.addWidget(random_btn)

        group_btn = QPushButton("Group by Type")  # Phase 18: no emoji
        group_btn.setToolTip("Patch fixtures in groups (one type contiguously)")
        group_btn.clicked.connect(self._on_group_by_type)
        tb.addWidget(group_btn)
        tb.addStretch()
        root.addLayout(tb)

        # Grid + right-hand keterangan panel (PRD AD-3)
        body = QHBoxLayout()
        self.grid = AddressGrid()
        self.grid.address_clicked.connect(self._on_cell_clicked)
        self.grid.fixture_dropped.connect(self._on_drop)
        body.addWidget(self.grid, 1)

        info_box = QVBoxLayout()
        info_box.setSpacing(8)
        info_title = QLabel("Patch Info")
        info_title.setStyleSheet("color:#2ecc71; font-size:15px; font-weight:700;")
        info_box.addWidget(info_title)
        self.info_fixtures = QLabel("Fixtures: 0")
        self.info_channels = QLabel("Channels: 0 / 512")
        self.info_free = QLabel("Free: 512")
        for lbl in (self.info_fixtures, self.info_channels, self.info_free):
            lbl.setStyleSheet("color:#e8e8e8; font-size:14px;")
            info_box.addWidget(lbl)
        info_box.addStretch()
        info_host = QWidget()
        info_host.setLayout(info_box)
        info_host.setFixedWidth(180)
        body.addWidget(info_host)
        root.addLayout(body, 1)

    # ─────────────────────────────────────
    def _refresh(self):
        self.grid.clear_paint()
        # Paint each patched fixture's cells
        for addr, info in self.manager.get_address_map().items():
            fx = info["fixture_data"]
            ch_map = fx.get("channel_map", [])
            offset = addr - info["start_address"]
            label = ch_map[offset]["label"] if offset < len(ch_map) else "?"
            color = CHANNEL_COLORS[offset % len(CHANNEL_COLORS)]
            self.grid.paint_cell(addr, label, color, position=info["start_address"])
        # Status + right-hand info panel (PRD AD-3)
        amap = self.manager.get_address_map()
        unique_starts = {info["start_address"] for info in amap.values()}
        used = len(amap)
        self.status_label.setText(f"{len(unique_starts)} fixture(s) patched, "
                                  f"{used}/512 channels used")
        self.info_fixtures.setText(f"Fixtures: {len(unique_starts)}")
        self.info_channels.setText(f"Channels: {used} / 512")
        self.info_free.setText(f"Free: {512 - used}")

    # ─────────────────────────────────────
    def _on_drop(self, fixture_name: str, address: int):
        ok, msg = self.manager.patch(address, fixture_name)
        if ok:
            self._refresh()
        else:
            QMessageBox.warning(self, "Patch Failed", msg)

    def _on_cell_clicked(self, address: int):
        if address in self.manager.get_address_map():
            ok, msg = self.manager.unpatch(address)
            if ok:
                self._refresh()
            else:
                QMessageBox.warning(self, "Unpatch Failed", msg)

    def _on_clear(self):
        if not self.manager.get_address_map():
            return
        reply = QMessageBox.question(
            self, "Clear All", "Remove all DMX patches?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.clear_all()
            self._refresh()

    def _on_auto(self):
        """Auto-patch sequential — feedback baris 54: popup menu tersendiri."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Auto-Patch Sequential")
        form = QFormLayout(dlg)

        start_spin = QSpinBox()
        start_spin.setRange(1, 512)
        start_spin.setValue(1)
        form.addRow("Start address:", start_spin)

        gap_spin = QSpinBox()
        gap_spin.setRange(0, 64)
        gap_spin.setValue(0)
        form.addRow("Gap between fixtures:", gap_spin)

        clear_chk = QCheckBox("Clear existing patches first")
        clear_chk.setChecked(True)
        form.addRow(clear_chk)

        n = len(self.manager.list_fixtures())
        preview = QLabel(f"{n} fixture(s) in library will be patched.")
        preview.setStyleSheet("color:#707070;")
        form.addRow(preview)

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        if clear_chk.isChecked():
            self.manager.clear_all()
        addr = start_spin.value()
        gap = gap_spin.value()
        for name in self.manager.list_fixtures():
            if addr > 512:
                break
            ok, _ = self.manager.patch(addr, name)
            if ok:
                addr += self.manager.get_fixture(name)["channels"] + gap
        self._refresh()

    # Phase 17: more patch modes
    def _on_random(self):
        """Patch each fixture at a random start address (32 retries per slot)."""
        import random
        self.manager.clear_all()
        used_ranges: list[tuple[int, int]] = []
        for name in self.manager.list_fixtures():
            ch = self.manager.get_fixture(name)["channels"]
            for _ in range(32):
                start = random.randint(1, 512 - ch + 1)
                end = start + ch - 1
                if all(end < s or start > e for s, e in used_ranges):
                    used_ranges.append((start, end))
                    self.manager.patch(start, name)
                    break
        self._refresh()

    def _on_group_by_type(self):
        """Patch fixtures of the same type contiguously (sorted by type)."""
        self.manager.clear_all()
        by_type: dict[str, list[str]] = {}
        for name in self.manager.list_fixtures():
            fx = self.manager.get_fixture(name)
            t = fx.get("type", "Other")
            by_type.setdefault(t, []).append(name)
        addr = 1
        for t in sorted(by_type.keys()):
            for name in by_type[t]:
                if addr > 512:
                    break
                self.manager.patch(addr, name)
                addr += self.manager.get_fixture(name)["channels"]
        self._refresh()
