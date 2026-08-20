"""
Scenes Tab — v6.4 (Phase 15)
- Removed "🔄 Regenerate Scenes" button (feedback #29: redundant with Analyze).
- Group scenes by type (chorus/verse/bridge/etc) in the list.
- Added "→ Convert to Chase" button (emits convert_to_chase_requested).

Reads from manager.songs[current_song_id]['scenes'].
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QSlider, QFormLayout, QGroupBox
)


class ScenesTab(QWidget):
    scene_applied = Signal(dict)
    # Phase 15: emit list of scenes to be turned into a chase sequence
    convert_to_chase_requested = Signal(list)

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.current_scene = None
        self.setObjectName("panelContent")
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)

        title = QLabel("Scene Generator")  # Phase 18: no emoji
        title.setObjectName("panelTitle")
        root.addWidget(title)
        sub = QLabel("Auto-generated scenes from audio segments. Click a scene to apply to preview.")
        sub.setObjectName("panelDesc")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Phase 15: no more "Regenerate" — Analyze button is the single source.
        # Toolbar: scene count + Convert-to-Chase
        tb = QHBoxLayout()
        self.count_label = QLabel("")
        self.count_label.setObjectName("dim")
        tb.addWidget(self.count_label)
        tb.addStretch()
        self.convert_btn = QPushButton("→  Convert to Chase")
        self.convert_btn.setToolTip("Convert all scenes of current song into a Chase sequence")
        self.convert_btn.clicked.connect(self._on_convert_to_chase)
        self.convert_btn.setEnabled(False)
        tb.addWidget(self.convert_btn)
        root.addLayout(tb)

        main = QHBoxLayout()

        _list_qss = """
            QListWidget {
                background-color: #141414; border: 1px solid #2a2a2a;
                color: #e8e8e8; font-size: 11px;
            }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #1a1a1a; }
            QListWidget::item:selected { background-color: #1f1f1f; color: #2ecc71; }
        """

        # PRD SC-3: song list on the left
        song_col = QVBoxLayout()
        song_hdr = QLabel("Songs")
        song_hdr.setStyleSheet("color:#2ecc71; font-weight:700;")
        song_col.addWidget(song_hdr)
        self.song_list = QListWidget()
        self.song_list.setMaximumWidth(200)
        self.song_list.currentItemChanged.connect(self._on_song_select)
        self.song_list.setStyleSheet(_list_qss)
        song_col.addWidget(self.song_list)
        main.addLayout(song_col)

        self.scene_list = QListWidget()
        self.scene_list.setMaximumWidth(280)
        self.scene_list.currentItemChanged.connect(self._on_scene_select)
        self.scene_list.setStyleSheet(_list_qss)
        main.addWidget(self.scene_list)

        self.controls_box = QGroupBox("Scene Controls")
        self.controls_box.setStyleSheet("""
            QGroupBox {
                color: #2ecc71; font-weight: 700;
                border: 1px solid #2a2a2a; border-radius: 4px;
                margin-top: 10px; padding: 15px 10px 10px 10px;
            }
        """)
        ctl = QFormLayout()
        self.lbl_song = QLabel("—")
        self.lbl_type = QLabel("—")
        self.lbl_range = QLabel("—")
        self.lbl_color = QLabel("—")
        self.lbl_dmx = QLabel("—")
        self.fade_slider = QSlider(Qt.Orientation.Horizontal)
        self.fade_slider.setRange(0, 5000)
        self.fade_slider.setValue(500)
        self.fade_slider.valueChanged.connect(self._on_fade_change)
        self.fade_label = QLabel("500 ms")
        for lbl in [self.lbl_song, self.lbl_type, self.lbl_range, self.lbl_dmx]:
            lbl.setStyleSheet("color: #e8e8e8; font-family: monospace; font-size: 11px;")
        ctl.addRow("Song:", self.lbl_song)
        ctl.addRow("Type:", self.lbl_type)
        ctl.addRow("Time:", self.lbl_range)
        ctl.addRow("Color:", self.lbl_color)
        ctl.addRow("DMX (R,G,B,W):", self.lbl_dmx)
        ctl.addRow("Fade (ms):", self.fade_slider)
        ctl.addRow("", self.fade_label)
        self.apply_btn = QPushButton("▶  Apply to Preview / Output")
        self.apply_btn.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: #0d0d0d; "
            "border: 1px solid #2ecc71; font-weight: 700; padding: 6px; }"
            "QPushButton:hover { background-color: #27ae60; }"
            "QPushButton:disabled { background-color: #2a2a2a; color: #707070; }"
        )
        self.apply_btn.clicked.connect(self._apply_scene)
        self.apply_btn.setEnabled(False)
        ctl.addRow(self.apply_btn)
        self.controls_box.setLayout(ctl)
        main.addWidget(self.controls_box, 1)
        root.addLayout(main, 1)

    def _populate_songs(self):
        self.song_list.blockSignals(True)
        self.song_list.clear()
        for sid, data in self.manager.songs.items():
            item = QListWidgetItem(data.get("filename", sid))
            item.setData(Qt.ItemDataRole.UserRole, sid)
            self.song_list.addItem(item)
            if sid == self.manager.current_song_id:
                self.song_list.setCurrentItem(item)
        self.song_list.blockSignals(False)

    def _on_song_select(self, current, _previous):
        if not current:
            return
        sid = current.data(Qt.ItemDataRole.UserRole)
        if sid:
            self.manager.current_song_id = sid
            self._refresh()

    def _refresh(self):
        self._populate_songs()
        self.scene_list.clear()
        song = self.manager.songs.get(self.manager.current_song_id)
        if not song:
            self.count_label.setText("No song loaded")
            self.convert_btn.setEnabled(False)
            return
        scenes = song.get('scenes', [])
        # Phase 15: group scenes by type
        by_type: dict[str, list[tuple[int, dict]]] = {}
        for i, scene in enumerate(scenes):
            t = scene.get('type', 'scene')
            by_type.setdefault(t, []).append((i, scene))

        for t in sorted(by_type.keys()):
            items = by_type[t]
            hdr = QListWidgetItem(f"▼ {t.upper()}  ({len(items)})")
            hdr.setFlags(Qt.ItemFlag.NoItemFlags)  # not selectable
            hdr.setForeground(QColor("#2ecc71"))
            self.scene_list.addItem(hdr)
            for i, scene in items:
                label = f"   #{i+1}  {scene.get('start', 0):.1f}s → {scene.get('end', 0):.1f}s"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.scene_list.addItem(item)

        # Update toolbar status
        type_count = len(by_type)
        self.count_label.setText(
            f"{len(scenes)} scenes · {type_count} type{'s' if type_count != 1 else ''}"
        )
        self.convert_btn.setEnabled(len(scenes) > 0)

    def _on_scene_select(self, current, previous):
        if not current:
            return
        idx = current.data(Qt.ItemDataRole.UserRole)
        if idx is None:
            return  # header row
        song = self.manager.songs.get(self.manager.current_song_id, {})
        scenes = song.get('scenes', [])
        if idx is not None and 0 <= idx < len(scenes):
            self.current_scene = scenes[idx]
            self._display_scene(song, self.current_scene)
            self.apply_btn.setEnabled(True)

    def _display_scene(self, song, scene):
        self.lbl_song.setText(song.get('filename', '—'))
        self.lbl_type.setText(scene.get('type', '—'))
        self.lbl_range.setText(f"{scene.get('start', 0):.1f}s → {scene.get('end', 0):.1f}s")
        c = scene.get('color', {})
        hex_c = c.get('hex', '#000000')
        self.lbl_color.setText(f"  {hex_c}  ")
        self.lbl_color.setStyleSheet(
            f"background-color: {hex_c}; color: #0d0d0d; padding: 4px 8px; "
            f"font-weight: 700; font-family: monospace; border: 1px solid #0d0d0d;"
        )
        dmx = scene.get('dmx', {})
        self.lbl_dmx.setText(
            f"[{dmx.get('r', 0)}, {dmx.get('g', 0)}, {dmx.get('b', 0)}, {dmx.get('w', 0)}]"
        )
        self.fade_slider.setValue(int(scene.get('fade_ms', 500)))

    def _on_fade_change(self, val):
        self.fade_label.setText(f"{val} ms")
        if self.current_scene:
            self.current_scene['fade_ms'] = val

    def _apply_scene(self):
        if not self.current_scene:
            return
        dmx = self.current_scene.get('dmx', {})
        if not dmx:
            return
        if hasattr(self.manager, 'artnet_controller') and self.manager.artnet_controller:
            frame = [0] * 512
            r, g, b, w = dmx.get('r', 0), dmx.get('g', 0), dmx.get('b', 0), dmx.get('w', 0)
            for addr in self.manager.get_address_map().keys():
                if 0 <= addr - 1 < 512: frame[addr - 1] = r
                if 0 <= addr < 512:     frame[addr] = g
                if 0 <= addr + 1 < 512: frame[addr + 1] = b
                if 0 <= addr + 2 < 512: frame[addr + 2] = w
            self.manager.artnet_controller.send_frame(frame)
        self.scene_applied.emit(self.current_scene)

    def _on_convert_to_chase(self):
        """Phase 15: emit all current scenes for chase conversion."""
        song = self.manager.songs.get(self.manager.current_song_id)
        if not song:
            return
        scenes = song.get('scenes', [])
        if not scenes:
            return
        self.convert_to_chase_requested.emit(scenes)
