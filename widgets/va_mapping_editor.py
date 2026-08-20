"""
VAMappingEditor — visual editor for V-A → HSV preset.

Sliders:
  - 4 quadrant hue bases (Q1/Q2/Q3/Q4) with color-coded chips
  - 4 hue range sliders (V variation per quadrant)
  - Chroma offset (-30° to +30°)
  - α (S from A) — 0-100%
  - β (V from rms) — 0-100%
  - V_min (floor brightness) — 0-50%

Live preview: 4 swatches showing the 4 quadrant center colors
              (V=0.75/0.25 × A=0.75/0.25).

Preset list: built-in "Default Praise" + user-saved presets from %APPDATA%.
Save / Delete buttons. Combo selection triggers load.

Emits `presetChanged(name)` on:
  - load from combo
  - save
  - delete
  - any slider change (so audio_tab can re-render live)
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QSlider, QLabel,
    QPushButton, QGroupBox, QFrame, QComboBox,
)

from engines.va_presets import (
    VAPreset, save_preset, load_preset, list_presets,
    delete_preset, DEFAULT_PRESET_NAME, apply_preset,
)
from engines.color_mapping import hsv_to_drgbw


class VAMappingEditor(QWidget):
    presetChanged = Signal(str)  # emits preset name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.preset = VAPreset()
        self._suppress_signals = False
        self.setObjectName("vaMappingEditor")
        self._build_ui()
        self._refresh_preset_list()
        self._apply_preset_to_ui()
        self._update_preview()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Preset selector row
        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(160)
        self.preset_combo.currentTextChanged.connect(self._on_preset_load)
        preset_row.addWidget(self.preset_combo, 1)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._on_save)
        preset_row.addWidget(self.save_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete)
        preset_row.addWidget(self.delete_btn)

        root.addLayout(preset_row)

        # 4 quadrant hue groups
        hue_group = QGroupBox("Quadrant Hue Base  (V variation 0.5 → 1.0)")
        hue_layout = QFormLayout()
        hue_layout.setSpacing(4)

        self.q1_hue = self._make_hue_slider()
        self.q2_hue = self._make_hue_slider()
        self.q3_hue = self._make_hue_slider()
        self.q4_hue = self._make_hue_slider()
        self.q1_range = self._make_range_slider()
        self.q2_range = self._make_range_slider()
        self.q3_range = self._make_range_slider()
        self.q4_range = self._make_range_slider()

        hue_layout.addRow("Q1 Praise  (warm):",
                          self._wrap_slider(self.q1_hue, "#f39c12"))
        hue_layout.addRow("  range:",
                          self._wrap_slider(self.q1_range))
        hue_layout.addRow("Q2 Intens  (purple):",
                          self._wrap_slider(self.q2_hue, "#8e44ad"))
        hue_layout.addRow("  range:",
                          self._wrap_slider(self.q2_range))
        hue_layout.addRow("Q3 Kontemplatif  (blue):",
                          self._wrap_slider(self.q3_hue, "#2980b9"))
        hue_layout.addRow("  range:",
                          self._wrap_slider(self.q3_range))
        hue_layout.addRow("Q4 Damai  (cyan/green):",
                          self._wrap_slider(self.q4_hue, "#16a085"))
        hue_layout.addRow("  range:",
                          self._wrap_slider(self.q4_range))
        hue_group.setLayout(hue_layout)
        root.addWidget(hue_group)

        # S/V blend + offset
        blend_group = QGroupBox("S / V Blend & Chroma")
        blend_layout = QFormLayout()
        blend_layout.setSpacing(4)

        self.chroma_offset = self._make_slider(-30, 30, 5)
        self.alpha_sat = self._make_slider(0, 100, 60)
        self.beta_val = self._make_slider(0, 100, 50)
        self.v_min = self._make_slider(0, 50, 10)

        blend_layout.addRow("Chroma offset (°/step):",
                            self._wrap_slider(self.chroma_offset))
        blend_layout.addRow("α — S from A  (0-100%):",
                            self._wrap_slider(self.alpha_sat))
        blend_layout.addRow("β — V from rms  (0-100%):",
                            self._wrap_slider(self.beta_val))
        blend_layout.addRow("V_min  (floor, 0-50%):",
                            self._wrap_slider(self.v_min))
        blend_group.setLayout(blend_layout)
        root.addWidget(blend_group)

        # Live preview
        preview_label = QLabel("Live preview  (4 quadrants)")
        preview_label.setStyleSheet(
            "color: #707070; font-size: 11px; padding: 4px 0;"
        )
        root.addWidget(preview_label)

        self.preview_widgets = []
        preview_row = QHBoxLayout()
        preview_row.setSpacing(4)
        # Q1, Q2, Q3, Q4 sample points
        for _ in range(4):
            swatch = QFrame()
            swatch.setFixedSize(70, 50)
            swatch.setStyleSheet(
                "background-color: #2a2a2a; border: 1px solid #3a3a3a;"
                " border-radius: 4px;"
            )
            preview_row.addWidget(swatch)
            self.preview_widgets.append(swatch)
        root.addLayout(preview_row)

        # Connect sliders for live update
        all_sliders = [
            self.q1_hue, self.q2_hue, self.q3_hue, self.q4_hue,
            self.q1_range, self.q2_range, self.q3_range, self.q4_range,
            self.chroma_offset, self.alpha_sat, self.beta_val, self.v_min,
        ]
        for s in all_sliders:
            s.valueChanged.connect(self._on_slider_change)

    def _make_hue_slider(self) -> QSlider:
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(0, 359)
        return s

    def _make_range_slider(self) -> QSlider:
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(0, 180)
        return s

    def _make_slider(self, lo: int, hi: int, default: int) -> QSlider:
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(lo, hi)
        s.setValue(default)
        return s

    def _wrap_slider(self, slider: QSlider, color_label: str = "") -> QHBoxLayout:
        layout = QHBoxLayout()
        if color_label:
            chip = QLabel()
            chip.setFixedSize(14, 14)
            chip.setStyleSheet(
                f"background-color: {color_label}; border-radius: 2px;"
            )
            layout.addWidget(chip)
        layout.addWidget(slider, 1)
        return layout

    def _refresh_preset_list(self):
        current = self.preset_combo.currentText() or self.preset.name
        self._suppress_signals = True
        self.preset_combo.clear()
        self.preset_combo.addItem(DEFAULT_PRESET_NAME)
        for n in list_presets():
            if n != DEFAULT_PRESET_NAME:
                self.preset_combo.addItem(n)
        idx = self.preset_combo.findText(current)
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)
        self._suppress_signals = False

    def _on_preset_load(self, name: str):
        if self._suppress_signals or not name:
            return
        self.preset = load_preset(name)
        self._apply_preset_to_ui()
        self._update_preview()
        self.presetChanged.emit(name)

    def _on_save(self):
        self._read_ui_to_preset()
        if self.preset.name == DEFAULT_PRESET_NAME:
            # prompt user for new name
            from PySide6.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(
                self, "Save Preset",
                "Preset name (cannot be 'Default Praise'):",
                text="My Preset",
            )
            if not ok or not name.strip():
                return
            self.preset.name = name.strip()
        save_preset(self.preset)
        self._refresh_preset_list()
        self.presetChanged.emit(self.preset.name)

    def _on_delete(self):
        if self.preset.name == DEFAULT_PRESET_NAME:
            return
        from PySide6.QtWidgets import QMessageBox
        confirm = QMessageBox.question(
            self, "Delete Preset",
            f"Delete preset '{self.preset.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        delete_preset(self.preset.name)
        self.preset = VAPreset()
        self._apply_preset_to_ui()
        self._refresh_preset_list()
        self._update_preview()
        self.presetChanged.emit(DEFAULT_PRESET_NAME)

    def _on_slider_change(self):
        if self._suppress_signals:
            return
        self._read_ui_to_preset()
        self._update_preview()
        # Live notify for audio_tab re-render
        self.presetChanged.emit(self.preset.name + "*")

    def _read_ui_to_preset(self):
        self.preset.q1_hue_base = float(self.q1_hue.value())
        self.preset.q2_hue_base = float(self.q2_hue.value())
        self.preset.q3_hue_base = float(self.q3_hue.value())
        self.preset.q4_hue_base = float(self.q4_hue.value())
        self.preset.q1_hue_range = float(self.q1_range.value())
        self.preset.q2_hue_range = float(self.q2_range.value())
        self.preset.q3_hue_range = float(self.q3_range.value())
        self.preset.q4_hue_range = float(self.q4_range.value())
        self.preset.chroma_offset_deg = float(self.chroma_offset.value())
        self.preset.alpha_sat = self.alpha_sat.value() / 100.0
        self.preset.beta_val = self.beta_val.value() / 100.0
        self.preset.v_min = self.v_min.value() / 100.0

    def _apply_preset_to_ui(self):
        self._suppress_signals = True
        self.q1_hue.setValue(int(self.preset.q1_hue_base))
        self.q2_hue.setValue(int(self.preset.q2_hue_base))
        self.q3_hue.setValue(int(self.preset.q3_hue_base))
        self.q4_hue.setValue(int(self.preset.q4_hue_base))
        self.q1_range.setValue(int(self.preset.q1_hue_range))
        self.q2_range.setValue(int(self.preset.q2_hue_range))
        self.q3_range.setValue(int(self.preset.q3_hue_range))
        self.q4_range.setValue(int(self.preset.q4_hue_range))
        self.chroma_offset.setValue(int(self.preset.chroma_offset_deg))
        self.alpha_sat.setValue(int(self.preset.alpha_sat * 100))
        self.beta_val.setValue(int(self.preset.beta_val * 100))
        self.v_min.setValue(int(self.preset.v_min * 100))
        self._suppress_signals = False

    def _update_preview(self):
        # Sample 4 points: Q1 (0.75, 0.75), Q2 (0.25, 0.75), Q3 (0.25, 0.25), Q4 (0.75, 0.25)
        for i, (v, a) in enumerate(
            [(0.75, 0.75), (0.25, 0.75), (0.25, 0.25), (0.75, 0.25)]
        ):
            H, S, V_hsv = apply_preset(self.preset, v, a, chroma_peak=6, rms_norm=0.5)
            drgbw = hsv_to_drgbw(H, S, V_hsv)
            r, g, b = drgbw['rgb_255']
            self.preview_widgets[i].setStyleSheet(
                f"background-color: rgb({r}, {g}, {b}); "
                f"border: 1px solid #3a3a3a; border-radius: 4px;"
            )

    # ── Public API
    def get_preset(self) -> VAPreset:
        return self.preset

    def set_preset(self, preset: VAPreset) -> None:
        self.preset = preset
        self._apply_preset_to_ui()
        self._update_preview()
