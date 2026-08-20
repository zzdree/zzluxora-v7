"""
Mixer Tab — 513-channel DMX mixer with master fader on the left.
Layout:
  - Master dimmer on LEFT (full-height vertical fader)
  - 513 sliders total (master + 512 channels)
  - Range 0-255, default 0 (DESIGN.md §3.3 DMX 000-255; feedback baris 26 blackout=0)
  - Refresh button TOP RIGHT (icon button)
  - 24 columns horizontal → 22 rows × 24 cols
  - FIX 1: value button (grandma-style box) per fader — click to edit inline
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea,
    QGridLayout, QSlider, QGroupBox, QInputDialog
)


class MixerTab(QWidget):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.faders = []          # 512 channel faders
        self.value_btns = {}      # ch → QPushButton (value box)
        self.setObjectName("panelContent")
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        # ── Title row: title (left) + refresh icon button (top right)
        title_row = QHBoxLayout()
        title = QLabel("513-Channel DMX Mixer")
        title.setObjectName("panelTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        self.refresh_btn = QPushButton("↻")  # ↻ geometric
        self.refresh_btn.setObjectName("headerButton")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setToolTip("Refresh from Art-Net")
        self.refresh_btn.clicked.connect(self._refresh)
        title_row.addWidget(self.refresh_btn)

        sub = QLabel("Live DMX channel values. Drag faders to override. "
                     "Connect Art-Net in the Output tab to send to hardware.")
        sub.setObjectName("panelDesc")
        sub.setWordWrap(True)

        # ── Main row: master (left, full-height) + 512-channel grid (right, scroll)
        main_row = QHBoxLayout()
        main_row.setSpacing(12)

        # Master group (left, full-height vertical fader)
        self.master_box = QGroupBox("Master")
        self.master_box.setObjectName("mixerMasterBox")
        master_l = QVBoxLayout(self.master_box)
        master_l.setContentsMargins(8, 16, 8, 8)
        master_l.setSpacing(6)
        master_l.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.master_slider = QSlider(Qt.Orientation.Vertical)
        self.master_slider.setRange(0, 255)
        self.master_slider.setValue(255)
        self.master_slider.setMinimumHeight(360)
        self.master_slider.setMaximumWidth(40)
        self.master_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.master_slider.setTickInterval(64)
        self.master_slider.valueChanged.connect(self._on_master)
        master_l.addWidget(self.master_slider, 1, Qt.AlignmentFlag.AlignHCenter)

        # FIX 1: master value button (grandma-style box)
        self.master_value_btn = QPushButton("255")
        self.master_value_btn.setFixedSize(40, 22)
        self.master_value_btn.setToolTip("Click to set master value (0-255)")
        self.master_value_btn.clicked.connect(self._edit_master)
        self.master_value_btn.setStyleSheet(
            "QPushButton { background-color: #1f1f1f; color: #2ecc71; border: 1px solid #2a2a2a;"
            "font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 11px; font-weight: 700;}"
            "QPushButton:hover { border-color: #2ecc71; }"
        )
        master_l.addWidget(self.master_value_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        main_row.addWidget(self.master_box)

        # 512-channel scrollable grid (24 cols × 22 rows)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(400)
        grid_widget = QWidget()
        grid_widget.setObjectName("mixerGridWidget")
        grid = QGridLayout(grid_widget)
        grid.setSpacing(2)
        grid.setContentsMargins(4, 4, 4, 4)

        for ch in range(1, 513):
            fader = QSlider(Qt.Orientation.Vertical)
            fader.setRange(0, 255)
            fader.setValue(0)
            fader.setMinimumHeight(60)
            fader.setMaximumWidth(28)
            fader.setObjectName(f"ch{ch}")
            fader.valueChanged.connect(lambda v, c=ch: self._on_channel(c, v))
            self.faders.append(fader)

            # FIX 1: value button per channel (grandma-style box)
            value_btn = QPushButton("0")
            value_btn.setFixedSize(28, 20)
            value_btn.setToolTip(f"Click to set ch {ch} (0-255)")
            value_btn.clicked.connect(lambda _checked=False, c=ch: self._edit_channel(c))
            value_btn.setStyleSheet(
                "QPushButton { background-color: #1f1f1f; color: #e8e8e8; border: 1px solid #2a2a2a;"
                "font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 10px; font-weight: 600; padding: 0;}"
                "QPushButton:hover { border-color: #2ecc71; color: #2ecc71; }"
            )
            self.value_btns[ch] = value_btn

            label = QLabel(str(ch))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #707070; font-size: 9px;")

            cell_w = QWidget()
            cell_l = QVBoxLayout(cell_w)
            cell_l.setContentsMargins(0, 0, 0, 0)
            cell_l.setSpacing(1)
            cell_l.addWidget(fader, 1)
            cell_l.addWidget(value_btn, 0, Qt.AlignmentFlag.AlignHCenter)
            cell_l.addWidget(label)
            row = (ch - 1) // 24
            col = (ch - 1) % 24
            grid.addWidget(cell_w, row, col)

        scroll.setWidget(grid_widget)
        main_row.addWidget(scroll, 1)

        # ── Root assembly
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)
        root.addLayout(title_row)
        root.addWidget(sub)
        root.addLayout(main_row, 1)

    def _on_channel(self, ch, val):
        """Slider moved → update DMX value + sync value button text."""
        val = max(0, min(255, val))
        if hasattr(self.manager, 'artnet_controller') and self.manager.artnet_controller:
            if ch - 1 < len(self.manager.artnet_controller.current_dmx):
                self.manager.artnet_controller.current_dmx[ch - 1] = val
        # Sync value button text
        if ch in self.value_btns:
            self.value_btns[ch].setText(str(val))

    def _on_master(self, val):
        """Master slider moved → sync value button text."""
        self.master_value_btn.setText(str(val))

    def _refresh(self):
        """Sync faders + value buttons from Art-Net DMX state."""
        if not hasattr(self.manager, 'artnet_controller') or not self.manager.artnet_controller:
            return
        if not self.manager.artnet_controller.is_running:
            return
        dmx = self.manager.artnet_controller.current_dmx
        for i, val in enumerate(dmx[:512]):
            if i < len(self.faders):
                v = max(0, min(255, val))
                self.faders[i].blockSignals(True)
                self.faders[i].setValue(v)
                self.faders[i].blockSignals(False)
                ch = i + 1
                if ch in self.value_btns:
                    self.value_btns[ch].setText(str(v))

    # ── FIX 1: Click-to-edit value handlers (grandma-style) ──

    def _edit_channel(self, ch: int):
        """Click value box → open dialog to set channel value 0-255."""
        current = 0
        if ch - 1 < len(self.faders):
            current = self.faders[ch - 1].value()
        val, ok = QInputDialog.getInt(
            self, f"Channel {ch}", f"Value (0-255):", current, 0, 255, 1
        )
        if ok and ch - 1 < len(self.faders):
            self.faders[ch - 1].setValue(val)  # triggers _on_channel → sync button + DMX

    def _edit_master(self):
        """Click master value box → open dialog to set master value 0-255."""
        current = self.master_slider.value()
        val, ok = QInputDialog.getInt(
            self, "Master", "Value (0-255):", current, 0, 255, 1
        )
        if ok:
            self.master_slider.setValue(val)  # triggers _on_master → sync button
