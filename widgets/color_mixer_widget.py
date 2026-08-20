"""
ColorMixerWidget (v6 Phase 3B) — 4-slot multi-song DRGBW blend UI.

Layout:
  ┌─ Mode: ◉ Additive  ○ Override  ○ Average ─┐
  ├─ Slot 1: [song combo] [weight slider] [color swatch] [×] ─┤
  ├─ Slot 2: ...                                                ┤
  ├─ Slot 3: ...                                                ┤
  ├─ Slot 4: ...                                                ┤
  ├─ Blend preview: [large swatch]  R/G/B/W/D: ...              ┤
  └──────────────────────────────────────────────────────────────┘

Public API:
  set_songs(songs: Dict[str, dict])  — populate dropdown options
  get_mixer() -> ColorMixer          — read current state
  set_mixer(mixer)                   — restore from preset
  blendChanged = Signal()             — fires on slot/weight/mode change
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider,
    QPushButton, QButtonGroup, QRadioButton, QFrame, QGridLayout,
)

from engines.color_mixer import ColorMixer, MixerSlot


class _SlotRow(QWidget):
    """One slot: combo + weight slider + color swatch + clear button."""

    changed = Signal()
    cleared = Signal(int)  # slot index

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setObjectName(f"mixerSlot_{index}")
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        # Index label
        idx_lbl = QLabel(f"Slot {self.index + 1}:")
        idx_lbl.setFixedWidth(60)
        idx_lbl.setStyleSheet("color: #909090; font-size: 11px;")
        layout.addWidget(idx_lbl)

        # Song combo
        self.combo = QComboBox()
        self.combo.setMinimumWidth(140)
        self.combo.addItem("(empty)", "")
        self.combo.currentIndexChanged.connect(self._on_change)
        layout.addWidget(self.combo, 1)

        # Weight slider
        self.weight = QSlider(Qt.Orientation.Horizontal)
        self.weight.setRange(0, 100)
        self.weight.setValue(0)
        self.weight.setFixedWidth(120)
        self.weight.valueChanged.connect(self._on_change)
        layout.addWidget(self.weight)

        self.w_lbl = QLabel("0%")
        self.w_lbl.setFixedWidth(36)
        self.w_lbl.setStyleSheet("color: #909090; font-size: 10px; font-family: monospace;")
        layout.addWidget(self.w_lbl)

        # Color swatch
        self.swatch = QFrame()
        self.swatch.setFixedSize(36, 22)
        self.swatch.setStyleSheet(
            "background-color: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 3px;"
        )
        layout.addWidget(self.swatch)

        # Clear button
        self.clear_btn = QPushButton("×")
        self.clear_btn.setFixedSize(22, 22)
        self.clear_btn.setToolTip("Clear this slot")
        self.clear_btn.setStyleSheet(
            "QPushButton { background-color: #2a2a2a; color: #707070; "
            "border: 1px solid #2a2a2a; border-radius: 3px; }"
            "QPushButton:hover { background-color: #3a3a3a; color: #e74c3c; }"
        )
        self.clear_btn.clicked.connect(self._on_clear)
        layout.addWidget(self.clear_btn)

    def set_songs(self, songs: dict) -> None:
        """Populate combo with available song filenames."""
        current = self.combo.currentData()
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItem("(empty)", "")
        for song_id, data in songs.items():
            label = data.get("filename", song_id)
            self.combo.addItem(label, song_id)
        # Restore selection
        idx = self.combo.findData(current)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)
        self.combo.blockSignals(False)

    def set_slot(self, slot: MixerSlot) -> None:
        self.combo.blockSignals(True)
        self.weight.blockSignals(True)
        idx = self.combo.findData(slot.song_id) if slot.song_id else 0
        if idx < 0:
            idx = 0
        self.combo.setCurrentIndex(idx)
        self.weight.setValue(int(slot.weight * 100))
        self.w_lbl.setText(f"{int(slot.weight * 100)}%")
        self.combo.blockSignals(False)
        self.weight.blockSignals(False)

    def get_slot(self) -> MixerSlot:
        song_id = self.combo.currentData() or ""
        return MixerSlot(song_id=song_id, weight=self.weight.value() / 100.0)

    def set_swatch(self, rgb: tuple) -> None:
        r, g, b = rgb
        self.swatch.setStyleSheet(
            f"background-color: rgb({r}, {g}, {b}); "
            f"border: 1px solid #3a3a3a; border-radius: 3px;"
        )

    def _on_change(self):
        self.w_lbl.setText(f"{self.weight.value()}%")
        self.changed.emit()

    def _on_clear(self):
        self.combo.setCurrentIndex(0)
        self.weight.setValue(0)
        self.w_lbl.setText("0%")
        self.cleared.emit(self.index)


class ColorMixerWidget(QWidget):
    blendChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mixer = ColorMixer()
        self.songs: dict = {}
        self.slot_rows: list = []  # init BEFORE _build_ui (radio toggle fires _on_mode_change)
        self.setObjectName("colorMixerWidget")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Header
        header = QLabel("4-Slot Color Mixer")
        header.setStyleSheet(
            "color: #e8e8e8; font-size: 13px; font-weight: 700; padding: 4px 0;"
        )
        root.addWidget(header)

        sub = QLabel(
            "Blend up to 4 analyzed songs by weight. Additive = weighted average. "
            "Override = highest weight wins. Average = equal mix."
        )
        sub.setStyleSheet("color: #707070; font-size: 11px;")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Mode radios
        mode_row = QHBoxLayout()
        mode_row.setSpacing(12)
        mode_row.addWidget(QLabel("Mode:"))
        self.mode_group = QButtonGroup(self)
        for mode, label in [
            (ColorMixer.MODE_ADDITIVE, "Additive"),
            (ColorMixer.MODE_OVERRIDE, "Override"),
            (ColorMixer.MODE_AVERAGE, "Average"),
        ]:
            rb = QRadioButton(label)
            rb.setStyleSheet("color: #c8c8c8; font-size: 11px;")
            rb.toggled.connect(self._on_mode_change)
            self.mode_group.addButton(rb)
            mode_row.addWidget(rb)
            if mode == self.mixer.mode:
                rb.setChecked(True)
        mode_row.addStretch()
        root.addLayout(mode_row)

        # Slots
        self.slot_rows = []
        for i in range(4):
            row = _SlotRow(i)
            row.changed.connect(self._on_change)
            row.cleared.connect(self._on_change)
            self.slot_rows.append(row)
            root.addWidget(row)

        # Blend preview
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a2a;")
        root.addWidget(sep)

        preview_row = QHBoxLayout()
        preview_row.addWidget(QLabel("Blend:"))
        self.blend_swatch = QFrame()
        self.blend_swatch.setFixedSize(80, 50)
        self.blend_swatch.setStyleSheet(
            "background-color: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 4px;"
        )
        preview_row.addWidget(self.blend_swatch)

        self.blend_label = QLabel("— no active slots —")
        self.blend_label.setStyleSheet(
            "color: #c8c8c8; font-family: 'Consolas', monospace; font-size: 11px;"
        )
        preview_row.addWidget(self.blend_label, 1)
        root.addLayout(preview_row)

        root.addStretch()
        self._update_preview()

    def set_songs(self, songs: dict) -> None:
        """Populate song dropdowns from manager.songs dict."""
        self.songs = songs
        for row in self.slot_rows:
            row.set_songs(songs)
        self._update_preview()

    def get_mixer(self) -> ColorMixer:
        # Read current slot states into mixer
        for i, row in enumerate(self.slot_rows):
            self.mixer.slots[i] = row.get_slot()
        return self.mixer

    def set_mixer(self, mixer: ColorMixer) -> None:
        self.mixer = mixer
        for rb in self.mode_group.buttons():
            rb.blockSignals(True)
        for rb in self.mode_group.buttons():
            rb.setChecked(False)
        for rb in self.mode_group.buttons():
            if rb.text().lower() == mixer.mode:
                rb.setChecked(True)
        for rb in self.mode_group.buttons():
            rb.blockSignals(False)
        for i, row in enumerate(self.slot_rows):
            row.set_slot(mixer.slots[i])
        self._update_preview()

    def _on_mode_change(self, checked: bool):
        if not checked:
            return
        if not hasattr(self, "blend_swatch"):  # init order guard
            return
        for rb in self.mode_group.buttons():
            if rb.isChecked():
                self.mixer.mode = rb.text().lower()
                break
        self._on_change()

    def _on_change(self, *_args):
        if not hasattr(self, "blend_swatch"):
            return
        # Refresh swatches from current song data
        for row in self.slot_rows:
            slot = row.get_slot()
            if slot.song_id and slot.song_id in self.songs:
                gc = self.songs[slot.song_id].get("global_color", {})
                rgbw = gc.get("rgbw", [128, 128, 128, 0])
                row.set_swatch(tuple(rgbw[:3]))
            else:
                row.set_swatch((42, 42, 42))
        self._update_preview()
        self.blendChanged.emit()

    def _update_preview(self):
        mixer = self.get_mixer()
        result = mixer.blend(self.songs)
        if result is None:
            self.blend_swatch.setStyleSheet(
                "background-color: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 4px;"
            )
            self.blend_label.setText("— no active slots —")
        else:
            r, g, b, w, d = result
            self.blend_swatch.setStyleSheet(
                f"background-color: rgb({r}, {g}, {b}); "
                f"border: 1px solid #3a3a3a; border-radius: 4px;"
            )
            self.blend_label.setText(
                f"R={r:3d}  G={g:3d}  B={b:3d}  W={w:3d}  D={d:3d}  "
                f"({mixer.active_count()} active)"
            )
