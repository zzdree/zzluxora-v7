"""
Page Tab (PRD PG-1) — custom button pad for triggering saved chases + scenes.

A Page is a grid of buttons. Each button is one of:
  - chase:    references a saved chase by name → play_chase()
  - scene:    stores a DRGBW snapshot → send single frame
  - blackout: all channels to 0

Pages persist to %APPDATA%/zzluxora/pages/<name>.json (same storage style as
chases/programs).

ponytail: page stored in appdata, not embedded in .zlx — add .zlx embedding when
projects need to carry their pages between machines.
"""
import os
import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
    QComboBox, QSpinBox, QInputDialog, QMessageBox, QScrollArea,
)

from engines.chase import list_chases, load_chase


def _pages_dir() -> str:
    d = os.path.join(os.path.expandvars("%APPDATA%"), "zzluxora", "pages")
    os.makedirs(d, exist_ok=True)
    return d


class PageTab(QWidget):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.buttons: list[dict] = []   # [{kind, label, ref?, dmx?}]
        self.cols = 4
        self.setObjectName("panelContent")
        self._build_ui()
        self._rebuild_grid()

    # ── UI ────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)

        title = QLabel("Page")
        title.setObjectName("panelTitle")
        root.addWidget(title)
        sub = QLabel(
            "Custom button pad. Add buttons for saved chases and scenes, then "
            "click to trigger them live. Connect Art-Net in the Output tab first."
        )
        sub.setObjectName("panelDesc")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # ── Toolbar
        tb = QHBoxLayout()
        add_chase = QPushButton("+ Chase")
        add_chase.clicked.connect(self._add_chase)
        tb.addWidget(add_chase)
        add_scene = QPushButton("+ Scene")
        add_scene.clicked.connect(self._add_scene)
        tb.addWidget(add_scene)
        add_bo = QPushButton("+ Blackout")
        add_bo.clicked.connect(self._add_blackout)
        tb.addWidget(add_bo)

        tb.addSpacing(16)
        tb.addWidget(QLabel("Columns:"))
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 8)
        self.cols_spin.setValue(self.cols)
        self.cols_spin.valueChanged.connect(self._on_cols_changed)
        tb.addWidget(self.cols_spin)

        tb.addStretch()
        save_btn = QPushButton("Save Page")
        save_btn.clicked.connect(self._save_page)
        tb.addWidget(save_btn)
        load_btn = QPushButton("Load Page")
        load_btn.clicked.connect(self._load_page)
        tb.addWidget(load_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear)
        tb.addWidget(clear_btn)
        root.addLayout(tb)

        self.hint = QLabel("Right-click a button to remove it.")
        self.hint.setObjectName("dim")
        root.addWidget(self.hint)

        # ── Button grid (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(8)
        self.grid.setContentsMargins(4, 4, 4, 4)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self.grid_host)
        root.addWidget(scroll, 1)

        self.status = QLabel("Idle")
        self.status.setObjectName("dim")
        root.addWidget(self.status)

    # ── Grid build ────────────────────────────────────────
    def _rebuild_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for i, btn in enumerate(self.buttons):
            b = QPushButton(btn["label"])
            b.setMinimumSize(110, 72)
            b.setStyleSheet(self._btn_style(btn["kind"]))
            b.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            b.customContextMenuRequested.connect(
                lambda _pos, idx=i: self._remove_button(idx)
            )
            b.clicked.connect(lambda _checked=False, idx=i: self._trigger(idx))
            self.grid.addWidget(b, i // self.cols, i % self.cols)

    def _btn_style(self, kind: str) -> str:
        bg = {"chase": "#2a4a6a", "scene": "#2a6a4a", "blackout": "#3a1a1a"}.get(kind, "#2a2a2a")
        return (
            f"QPushButton {{ background-color: {bg}; color: #e8e8e8; "
            f"border: 1px solid #2a2a2a; border-radius: 6px; font-weight: 600; }}"
            f"QPushButton:hover {{ border-color: #2ecc71; }}"
        )

    def _on_cols_changed(self, val: int):
        self.cols = val
        self._rebuild_grid()

    # ── Add / remove ──────────────────────────────────────
    def _add_chase(self):
        names = list_chases()
        if not names:
            QMessageBox.information(self, "No Chases", "Build a chase first (Chase tab).")
            return
        name, ok = QInputDialog.getItem(self, "Add Chase", "Chase:", names, 0, False)
        if not ok or not name:
            return
        self.buttons.append({"kind": "chase", "label": name, "ref": name})
        self._rebuild_grid()

    def _add_scene(self):
        song = self.manager.songs.get(self.manager.current_song_id, {}) if self.manager else {}
        scenes = song.get("scenes", [])
        if not scenes:
            QMessageBox.information(self, "No Scenes", "Analyze a song first (Analyze tab).")
            return
        labels = [
            f"#{i+1} {s.get('type', 'scene')} {s.get('start', 0):.1f}s"
            for i, s in enumerate(scenes)
        ]
        label, ok = QInputDialog.getItem(self, "Add Scene", "Scene:", labels, 0, False)
        if not ok or not label:
            return
        scene = scenes[labels.index(label)]
        dmx = scene.get("dmx", {})
        self.buttons.append({
            "kind": "scene",
            "label": f"{scene.get('type', 'scene')} #{labels.index(label)+1}",
            "dmx": {k: int(dmx.get(k, 0)) for k in ("r", "g", "b", "w")},
            "intensity": int(scene.get("intensity", 200)),
        })
        self._rebuild_grid()

    def _add_blackout(self):
        self.buttons.append({"kind": "blackout", "label": "BLACKOUT"})
        self._rebuild_grid()

    def _remove_button(self, idx: int):
        if 0 <= idx < len(self.buttons):
            del self.buttons[idx]
            self._rebuild_grid()

    def _clear(self):
        if not self.buttons:
            return
        if QMessageBox.question(
            self, "Clear Page", "Remove all buttons?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.buttons = []
            self._rebuild_grid()

    # ── Trigger ───────────────────────────────────────────
    def _ctrl(self):
        ctrl = getattr(self.manager, "artnet_controller", None)
        if not ctrl or not ctrl.is_running:
            self.status.setText("Connect Art-Net in the Output tab first")
            return None
        return ctrl

    def _trigger(self, idx: int):
        if not (0 <= idx < len(self.buttons)):
            return
        btn = self.buttons[idx]
        kind = btn["kind"]
        if kind == "blackout":
            ctrl = self._ctrl()
            if ctrl:
                ctrl.blackout()
                self.status.setText("Blackout")
            return
        if kind == "scene":
            ctrl = self._ctrl()
            if ctrl:
                ctrl.send_frame(self._scene_frame(btn))
                self.status.setText(f"Scene: {btn['label']}")
            return
        if kind == "chase":
            ctrl = self._ctrl()
            if not ctrl:
                return
            chase = load_chase(btn["ref"])
            if not chase or not chase.steps:
                self.status.setText(f"Chase '{btn['ref']}' empty or missing")
                return
            ctrl.play_chase(self._chase_frames(chase))
            self.status.setText(f"Playing chase: {btn['ref']} ({len(chase.steps)} steps)")

    # ── Frame builders (address-mapped DRGBW) ─────────────
    def _addr_map(self) -> dict:
        return self.manager.get_address_map() if self.manager else {}

    def _paint(self, frame: list, r: int, g: int, b: int, w: int, dim: int):
        scale = lambda v: v * dim // 255
        for addr in self._addr_map().keys():
            if 0 <= addr - 1 < 512: frame[addr - 1] = scale(r)
            if 0 <= addr < 512:     frame[addr] = scale(g)
            if 0 <= addr + 1 < 512: frame[addr + 1] = scale(b)
            if 0 <= addr + 2 < 512: frame[addr + 2] = scale(w)

    def _scene_frame(self, btn: dict) -> list:
        frame = [0] * 512
        d = btn["dmx"]
        self._paint(frame, d.get("r", 0), d.get("g", 0), d.get("b", 0),
                    d.get("w", 0), btn.get("intensity", 200))
        return frame

    def _chase_frames(self, chase) -> list:
        frames = []
        for step in chase.steps:
            frame = [0] * 512
            d = step.drgbw
            self._paint(frame, int(d.get("r", 0)), int(d.get("g", 0)),
                        int(d.get("b", 0)), int(d.get("w", 0)),
                        int(d.get("dimmer", 200)))
            frames.append({
                "dmx": frame,
                "hold_ms": max(100, int(step.duration * 1000)),
                "fade_ms": 200,
                "label": step.label,
            })
        return frames

    # ── Persistence ───────────────────────────────────────
    def _save_page(self):
        name, ok = QInputDialog.getText(self, "Save Page", "Page name:", text="Page 1")
        if not ok or not name.strip():
            return
        path = os.path.join(_pages_dir(), f"{name.strip()}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"cols": self.cols, "buttons": self.buttons}, f, indent=2)
        self.status.setText(f"Saved page: {name.strip()}")

    def _load_page(self):
        d = _pages_dir()
        names = sorted(os.path.splitext(f)[0] for f in os.listdir(d) if f.endswith(".json"))
        if not names:
            QMessageBox.information(self, "No Pages", "No saved pages yet.")
            return
        name, ok = QInputDialog.getItem(self, "Load Page", "Page:", names, 0, False)
        if not ok or not name:
            return
        with open(os.path.join(d, f"{name}.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        self.cols = int(data.get("cols", 4))
        self.cols_spin.setValue(self.cols)
        self.buttons = data.get("buttons", [])
        self._rebuild_grid()
        self.status.setText(f"Loaded page: {name}")

    # ── called by main_window refresh sweep ───────────────
    def _refresh(self):
        pass
