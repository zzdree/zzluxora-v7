"""
Color Mixer tab (v6 Phase 3) — sidebar panel hosting:
  - Phase 3A: V-A mapping editor (4 quadrant hue bases, S/V blends, chroma)
  - Phase 3B: 4-slot color mixer (additive/override/average blend)
  - Phase 3C: S + V curve editors (1D LUT piecewise-linear, 11 control points)
  - Phase 3D: Preview test mode (scrubber + live DRGBW + fixture grid + curves apply)

Public API:
  set_songs(songs: Dict[str, dict])   populate mixer + preview
  activePresetChanged = Signal(str)    fired when 'Set as Active' clicked
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QInputDialog,
    QFrame, QTabWidget, QMessageBox,
)

from widgets.va_mapping_editor import VAMappingEditor
from widgets.color_mixer_widget import ColorMixerWidget
from widgets.curve_editor import CurveEditor
from widgets.preview_widget import PreviewWidget
from engines.va_presets import save_preset, DEFAULT_PRESET_NAME
from config import app_config


class ColorMixerTab(QWidget):
    activePresetChanged = Signal(str)

    def __init__(self, manager=None, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setObjectName("colorMixerTab")
        self._build_ui()
        self._sync_active_label()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        title = QLabel("Color Mixer")
        title.setObjectName("panelTitle")
        root.addWidget(title)

        sub = QLabel(
            "Custom V-A mapping presets, 4-slot multi-song blend, "
            "S/V curve shaping, and live preview test mode."
        )
        sub.setObjectName("panelDesc")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Active preset row (always visible)
        active_row = QHBoxLayout()
        active_row.addWidget(QLabel("Active Mapping:"))
        self.active_label = QLabel(DEFAULT_PRESET_NAME)
        self.active_label.setStyleSheet(
            "color: #2ecc71; font-weight: 700; font-size: 12px;"
        )
        active_row.addWidget(self.active_label, 1)

        self.set_active_btn = QPushButton("Set as Active")
        self.set_active_btn.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: #0d0d0d; "
            "border: 1px solid #2ecc71; font-weight: 700; padding: 4px 12px; }"
            "QPushButton:hover { background-color: #27ae60; }"
        )
        self.set_active_btn.clicked.connect(self._on_set_active)
        active_row.addWidget(self.set_active_btn)
        root.addLayout(active_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a2a;")
        root.addWidget(sep)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #2a2a2a; border-radius: 4px; }
            QTabBar::tab {
                background-color: #1a1a1a;
                color: #909090;
                padding: 6px 16px;
                border: 1px solid #2a2a2a;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0f0f0f;
                color: #2ecc71;
                font-weight: 700;
            }
        """)

        # Tab 1: Mapping (3A)
        self.editor = VAMappingEditor()
        self.editor.presetChanged.connect(self._on_editor_preset_changed)
        self.tabs.addTab(self.editor, "Mapping")

        # Tab 2: Mixer (3B)
        self.mixer = ColorMixerWidget()
        self.tabs.addTab(self.mixer, "Mixer")

        # Tab 3: Curves (3C) — S curve + V curve
        curves_widget = QWidget()
        curves_layout = QVBoxLayout(curves_widget)
        curves_layout.setContentsMargins(8, 8, 8, 8)
        curves_layout.setSpacing(8)

        curves_sub = QLabel(
            "S curve: scales Saturation. V curve: scales Brightness (DRGBW dimmer). "
            "Drag points to shape. Curves auto-apply in Preview tab."
        )
        curves_sub.setStyleSheet("color: #707070; font-size: 11px;")
        curves_sub.setWordWrap(True)
        curves_layout.addWidget(curves_sub)

        self.s_curve = CurveEditor("Saturation (S)")
        self.s_curve.curveChanged.connect(self._on_curve_changed)
        curves_layout.addWidget(self.s_curve, 1)

        self.v_curve = CurveEditor("Brightness (V)")
        self.v_curve.curveChanged.connect(self._on_curve_changed)
        curves_layout.addWidget(self.v_curve, 1)

        self.tabs.addTab(curves_widget, "Curves")

        # Tab 4: Preview (3D) — real preview widget
        self.preview = PreviewWidget()
        self.tabs.addTab(self.preview, "Preview")

        root.addWidget(self.tabs, 1)

        # Initial curve feed to preview
        self._feed_curves_to_preview()

    # ── Public
    def set_songs(self, songs: dict) -> None:
        self.mixer.set_songs(songs or {})
        self.preview.set_songs(songs or {})

    # ── Mapping tab
    def _on_editor_preset_changed(self, name: str):
        if name.endswith("*"):
            self.active_label.setText(f"{self._current_preset_name()} (unsaved)")
            self.active_label.setStyleSheet(
                "color: #f1c40f; font-weight: 700; font-size: 12px;"
            )
        else:
            self._sync_active_label()

    def _current_preset_name(self) -> str:
        return self.editor.get_preset().name

    def _sync_active_label(self):
        active = app_config().active_va_preset
        self.active_label.setText(active)
        self.active_label.setStyleSheet(
            "color: #2ecc71; font-weight: 700; font-size: 12px;"
        )

    def _on_set_active(self):
        preset = self.editor.get_preset()
        if preset.name == DEFAULT_PRESET_NAME:
            name, ok = QInputDialog.getText(
                self, "Set as Active",
                "Preset name (cannot be 'Default Praise'):",
                text="My Preset",
            )
            if not ok or not name.strip():
                return
            preset.name = name.strip()
        save_preset(preset)
        app_config().active_va_preset = preset.name
        self.editor._refresh_preset_list()
        idx = self.editor.preset_combo.findText(preset.name)
        if idx >= 0:
            self.editor.preset_combo.setCurrentIndex(idx)
        self._sync_active_label()
        self.activePresetChanged.emit(preset.name)
        QMessageBox.information(
            self, "Preset Active",
            f"'{preset.name}' is now the active V-A mapping preset.\n"
            f"It will apply to the next audio analysis.",
        )

    # ── Curves tab
    def _on_curve_changed(self):
        self._feed_curves_to_preview()

    def _feed_curves_to_preview(self):
        # If a curve is at identity, send None (no shaping).
        # For now, always send the curve so user can see the effect.
        s = self.s_curve.get_curve()
        v = self.v_curve.get_curve()
        from engines.curve_lut import identity_points
        s_identity = all(
            abs(p[0] - p[1]) < 0.001 for p in s.points
        )
        v_identity = all(
            abs(p[0] - p[1]) < 0.001 for p in v.points
        )
        self.preview.set_s_curve(None if s_identity else s)
        self.preview.set_v_curve(None if v_identity else v)
