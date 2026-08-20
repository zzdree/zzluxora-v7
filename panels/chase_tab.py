"""
Chase Tab — v6 Phase 5: Chase Builder + Play.

Combines:
  - Existing visual timeline (ChaseTimeline QFrame) — shows steps as colored bars
  - Existing play/stop (Art-Net output)
  - NEW: Chase list (combo) + load/save/delete
  - NEW: Auto-generate chase from current song's scenes
  - NEW: Loop checkbox + Default direction combo
  - NEW: Chase status display
"""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QComboBox, QCheckBox, QInputDialog, QMessageBox, QSpinBox, QFormLayout,
    QDialog, QDialogButtonBox,
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from engines.chase import (
    Chase, ChaseStep, DIRECTIONS,
    save_chase, load_chase, list_chases, delete_chase,
    chase_from_song_scenes,
)


class ChaseTimeline(QFrame):
    """Custom paintEvent timeline showing chase steps as colored bars."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.steps = []
        self.duration_ms = 30000
        self.setMinimumHeight(90)
        self.setStyleSheet("background-color: #0d0d0d; border: 1px solid #2a2a2a;")

    def set_steps(self, steps, duration_ms):
        self.steps = steps or []
        self.duration_ms = max(1, duration_ms)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#0d0d0d"))
        if not self.steps:
            p.setPen(QPen(QColor("#3a3a3a")))
            p.setFont(QFont("Segoe UI", 9))
            msg = "No chase — build one or analyze a song first"
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, msg)
            return
        p.setPen(QPen(QColor("#3a3a3a"), 1))
        p.drawLine(0, h - 20, w, h - 20)
        for step in self.steps:
            s = step.get('start_ms', 0)
            e = step.get('end_ms', 0)
            color = QColor(step.get('color_hex', '#2ecc71'))
            x1 = int((s / self.duration_ms) * w)
            x2 = int((e / self.duration_ms) * w)
            if x2 <= x1:
                x2 = x1 + 2
            bar_h = h - 30
            p.fillRect(x1, 5, x2 - x1, bar_h, color)
            p.setPen(QPen(QColor("#0d0d0d")))
            p.drawRect(x1, 5, x2 - x1, bar_h)
            p.setPen(QPen(QColor("#ffffff")))
            p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            label = step.get('label', '')
            if label and (x2 - x1) > 30:
                p.drawText(x1 + 4, 18, label[:6])
        p.setPen(QPen(QColor("#707070")))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(5, h - 5, "0:00")
        p.drawText(w - 35, h - 5, f"{int(self.duration_ms / 1000)}s")


class ChaseTab(QWidget):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.current_chase: Chase | None = None
        self.setObjectName("panelContent")
        self._build_ui()
        self._refresh_chase_list()
        self._refresh_from_song()

    # ── UI ────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)

        # Title
        title = QLabel("Chase Builder")
        title.setObjectName("panelTitle")
        root.addWidget(title)
        sub = QLabel(
            "Build multi-step chase patterns. Auto-gen from analyzed song scenes, "
            "or design custom sequences with per-step direction."
        )
        sub.setObjectName("panelDesc")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # ── Chase control row
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Chase:"))
        self.chase_combo = QComboBox()
        self.chase_combo.setMinimumWidth(180)
        self.chase_combo.currentIndexChanged.connect(self._on_chase_select)
        ctrl.addWidget(self.chase_combo, 1)
        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self._on_new_chase)
        ctrl.addWidget(self.new_btn)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: #0d0d0d; "
            "border: 1px solid #2ecc71; font-weight: 700; padding: 4px 12px; }"
            "QPushButton:hover { background-color: #27ae60; }"
        )
        ctrl.addWidget(self.save_btn)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete)
        ctrl.addWidget(self.delete_btn)
        root.addLayout(ctrl)

        # ── Properties row
        prop_row = QHBoxLayout()
        prop_row.addWidget(QLabel("Direction:"))
        self.dir_combo = QComboBox()
        for d in DIRECTIONS:
            self.dir_combo.addItem(d)
        self.dir_combo.currentTextChanged.connect(self._on_props_change)
        prop_row.addWidget(self.dir_combo)
        self.loop_check = QCheckBox("Loop")
        self.loop_check.setChecked(True)
        self.loop_check.toggled.connect(self._on_props_change)
        prop_row.addWidget(self.loop_check)
        prop_row.addStretch()
        self.steps_label = QLabel("0 steps | 0:00.0 total")
        self.steps_label.setStyleSheet(
            "color: #c8c8c8; font-family: 'Consolas', monospace; font-size: 11px;"
        )
        prop_row.addWidget(self.steps_label)
        root.addLayout(prop_row)

        # ── Auto-gen row
        auto_row = QHBoxLayout()
        self.auto_btn = QPushButton("Build from current song scenes")
        self.auto_btn.clicked.connect(self._on_auto_gen)
        auto_row.addWidget(self.auto_btn)
        auto_row.addStretch()
        root.addLayout(auto_row)

        # ── Timeline (visual)
        self.timeline = ChaseTimeline()
        root.addWidget(self.timeline)

        # ── Transport row (play/stop)
        tb = QHBoxLayout()
        self.play_btn = QPushButton("Play Chase")
        self.play_btn.clicked.connect(self._play)
        self.play_btn.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: #0d0d0d; "
            "border: 1px solid #2ecc71; font-weight: 700; padding: 6px 14px; }"
            "QPushButton:hover { background-color: #27ae60; }"
        )
        tb.addWidget(self.play_btn)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop)
        tb.addWidget(self.stop_btn)
        tb.addStretch()
        self.bpm_label = QLabel("BPM: --")
        self.bpm_label.setStyleSheet("color: #707070; font-size: 12px;")
        tb.addWidget(self.bpm_label)
        root.addLayout(tb)

        # ── Status
        self.status = QLabel("Idle")
        self.status.setObjectName("dim")
        root.addWidget(self.status)

    # ── Refresh ───────────────────────────────────────────
    def _refresh_chase_list(self) -> None:
        current = self.chase_combo.currentData()
        self.chase_combo.blockSignals(True)
        self.chase_combo.clear()
        for name in list_chases():
            self.chase_combo.addItem(name, name)
        if current:
            idx = self.chase_combo.findData(current)
            if idx >= 0:
                self.chase_combo.setCurrentIndex(idx)
        self.chase_combo.blockSignals(False)

    def _refresh_from_song(self) -> None:
        """Display current song's BPM."""
        song = self.manager.songs.get(self.manager.current_song_id, {}) if self.manager else {}
        features = song.get("features", {}) if song else {}
        bpm = features.get("tempo", 0) if features else 0
        self.bpm_label.setText(f"BPM: {bpm:.1f}" if bpm else "BPM: --")

    def _refresh_timeline(self) -> None:
        """Render current_chase onto the timeline widget."""
        if not self.current_chase or not self.current_chase.steps:
            self.timeline.set_steps([], 30000)
            self.steps_label.setText("0 steps | 0:00.0 total")
            return
        steps = []
        for s in self.current_chase.steps:
            r = s.drgbw.get("r", 0)
            g = s.drgbw.get("g", 0)
            b = s.drgbw.get("b", 0)
            color_hex = f"#{r:02x}{g:02x}{b:02x}"
            steps.append({
                "start_ms": int(s.start * 1000),
                "end_ms": int(s.end() * 1000),
                "color_hex": color_hex,
                "label": s.label,
            })
        duration_ms = int(self.current_chase.total_duration() * 1000)
        self.timeline.set_steps(steps, duration_ms)
        n = len(self.current_chase.steps)
        d = self.current_chase.total_duration()
        m = int(d // 60)
        sec = d - m * 60
        self.steps_label.setText(f"{n} steps | {m}:{sec:04.1f} total")

    # ── Handlers ──────────────────────────────────────────
    def _on_chase_select(self, idx: int) -> None:
        name = self.chase_combo.currentData()
        if not name:
            return
        c = load_chase(name)
        if c is None:
            return
        self.current_chase = c
        idx_d = self.dir_combo.findText(c.default_direction)
        if idx_d >= 0:
            self.dir_combo.setCurrentIndex(idx_d)
        self.loop_check.setChecked(c.loop)
        self._refresh_timeline()
        self.status.setText(f"Loaded: {c.name}")

    def _on_props_change(self, *_args) -> None:
        if not self.current_chase:
            return
        self.current_chase.default_direction = self.dir_combo.currentText()
        self.current_chase.loop = self.loop_check.isChecked()

    def _on_new_chase(self) -> None:
        name, ok = QInputDialog.getText(
            self, "New Chase", "Chase name:", text="Untitled Chase",
        )
        if not ok or not name.strip():
            return
        c = Chase(name=name.strip())
        c.add_step(0, 1.0, {"r": 255, "g": 0, "b": 0, "w": 0, "dimmer": 200}, label="Step 1")
        save_chase(c)
        self._refresh_chase_list()
        idx = self.chase_combo.findText(c.name)
        if idx >= 0:
            self.chase_combo.setCurrentIndex(idx)
        self.status.setText(f"Created: {c.name}")

    def _on_save(self) -> None:
        if not self.current_chase:
            return
        if self.dir_combo.currentText():
            self.current_chase.default_direction = self.dir_combo.currentText()
        self.current_chase.loop = self.loop_check.isChecked()
        save_chase(self.current_chase)
        self._refresh_chase_list()
        idx = self.chase_combo.findText(self.current_chase.name)
        if idx >= 0:
            self.chase_combo.setCurrentIndex(idx)
        self.status.setText(f"Saved: {self.current_chase.name}")

    def _on_delete(self) -> None:
        if not self.current_chase:
            return
        reply = QMessageBox.question(
            self, "Delete Chase",
            f"Delete chase '{self.current_chase.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        delete_chase(self.current_chase.name)
        self.current_chase = None
        self._refresh_chase_list()
        self._refresh_timeline()
        self.status.setText("Chase deleted")

    def _on_auto_gen(self) -> None:
        if not self.manager or not self.manager.current_song_id:
            QMessageBox.warning(self, "No Song", "Analyze a song first.")
            return
        result = self.manager.songs.get(self.manager.current_song_id, {})
        scenes = result.get("scenes", [])
        if not scenes:
            QMessageBox.warning(self, "No Scenes", "Current song has no scenes to build from.")
            return
        base_name = f"{result.get('filename', self.manager.current_song_id)} (chase)"
        name, ok = QInputDialog.getText(
            self, "Chase Name", "Name for auto-generated chase:",
            text=base_name,
        )
        if not ok or not name.strip():
            return
        c = chase_from_song_scenes(
            self.manager.current_song_id, result,
            chase_name=name.strip(),
            default_direction=self.dir_combo.currentText(),
            loop=self.loop_check.isChecked(),
        )
        save_chase(c)
        self._refresh_chase_list()
        idx = self.chase_combo.findText(c.name)
        if idx >= 0:
            self.chase_combo.setCurrentIndex(idx)
        self.current_chase = c
        self._refresh_timeline()
        self.status.setText(
            f"Built '{c.name}' with {len(c.steps)} steps from {len(scenes)} scenes"
        )

    # ── Play/Stop ─────────────────────────────────────────
    def _build_frames(self):
        if self.current_chase and self.current_chase.steps:
            return self._build_frames_from_chase(self.current_chase)
        song = self.manager.songs.get(self.manager.current_song_id, {}) if self.manager else {}
        scenes = song.get("scenes", [])
        return self._build_frames_from_scenes(scenes)

    def _build_frames_from_chase(self, chase: Chase) -> list:
        addr_map = self.manager.get_address_map() if self.manager else {}
        frames = []
        for step in chase.steps:
            dmx_list = [0] * 512
            r = int(step.drgbw.get("r", 0))
            g = int(step.drgbw.get("g", 0))
            b = int(step.drgbw.get("b", 0))
            w = int(step.drgbw.get("w", 0))
            dim = int(step.drgbw.get("dimmer", 200))
            for addr in addr_map.keys():
                if 0 <= addr - 1 < 512: dmx_list[addr - 1] = r * dim // 255
                if 0 <= addr < 512:     dmx_list[addr] = g * dim // 255
                if 0 <= addr + 1 < 512: dmx_list[addr + 1] = b * dim // 255
                if 0 <= addr + 2 < 512: dmx_list[addr + 2] = w * dim // 255
            hold_ms = max(100, int(step.duration * 1000))
            frames.append({
                "dmx": dmx_list,
                "hold_ms": hold_ms,
                "fade_ms": 200,
                "label": step.label,
                "direction": step.direction,
            })
        return frames

    def _build_frames_from_scenes(self, scenes: list) -> list:
        addr_map = self.manager.get_address_map() if self.manager else {}
        frames = []
        for scene in scenes:
            dmx = scene.get("dmx", {})
            r, g, b, w = dmx.get("r", 0), dmx.get("g", 0), dmx.get("b", 0), dmx.get("w", 0)
            dim = int(scene.get("intensity", 200))
            frame_dmx = [0] * 512
            for addr in addr_map.keys():
                if 0 <= addr - 1 < 512: frame_dmx[addr - 1] = r * dim // 255
                if 0 <= addr < 512:     frame_dmx[addr] = g * dim // 255
                if 0 <= addr + 1 < 512: frame_dmx[addr + 1] = b * dim // 255
                if 0 <= addr + 2 < 512: frame_dmx[addr + 2] = w * dim // 255
            duration_ms = max(100, int((scene.get("end", 1) - scene.get("start", 0)) * 1000))
            frames.append({
                "dmx": frame_dmx,
                "hold_ms": duration_ms,
                "fade_ms": int(scene.get("fade_ms", 500)),
            })
        return frames

    def _play(self) -> None:
        if not hasattr(self.manager, "artnet_controller") or not self.manager.artnet_controller:
            self.status.setText("No artnet controller — connect in Output tab")
            return
        if not self.manager.artnet_controller.is_running:
            self.status.setText("Connect Art-Net in Output tab first")
            return
        frames = self._build_frames()
        if not frames:
            self.status.setText("No frames to play")
            return
        self.manager.artnet_controller.play_chase(frames)
        self.status.setText(f"Playing {len(frames)} steps")

    def _stop(self) -> None:
        if hasattr(self.manager, "artnet_controller") and self.manager.artnet_controller:
            self.manager.artnet_controller.stop_chase()
        self.status.setText("Stopped")
