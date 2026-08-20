"""
Audio Tab v6 — wires to AnalyzePipeline (8-stage), shows per-segment DRGBW + 2D fixture grid.

Pipeline integration:
  File → AnalyzePipeline.run() with progress callback
       → 8 stages emit (percent, message) via signal
       → on done: populate AnalyzeResult, render segments + fixture grid

Per-segment display:
  - Horizontal scroll of SegmentColorChip (click to select)
  - Selected segment's color applied to FixtureGrid via pattern
  - Multi-fixture patterns: all_on, running, gradient, center_out

Back-compat:
  - manager.songs[song_id]["scenes"] still populated (for scenes_tab.py)
  - features dict structure unchanged (for back-compat consumers)
"""
import os
import traceback

from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QListWidget, QListWidgetItem, QMessageBox, QFormLayout,
    QGroupBox, QProgressBar, QScrollArea,
)

from engines.analyze_pipeline import AnalyzePipeline
from engines.color_mapping import hsv_to_drgbw
from engines.va_presets import VAPreset, load_preset
from panels.components.va_diagram import VADiagram
from panels.components.rms_chart import RMSChart
from panels.components.waveform_view import WaveformView
from widgets.segment_color_widget import SegmentColorChip
from widgets.fixture_grid import FixtureGrid
from config import app_config
from widgets.toast import show_toast


# ─────────────────────────────────────────────
# Background analysis worker (QThread) — v6
# ─────────────────────────────────────────────
class AnalyzeWorker(QThread):
    """Run the v6 8-stage pipeline off the UI thread."""
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(int, str)  # percent, message

    def __init__(
        self, filepath: str, fixture_count: int = 4,
        va_preset: VAPreset = None,
    ):
        super().__init__()
        self.filepath = filepath
        self.fixture_count = fixture_count
        self.va_preset = va_preset

    def run(self):
        try:
            import librosa

            def _on_progress(pct, msg):
                self.progress.emit(pct, msg)

            # v6: 8-stage pipeline + Phase 3 VAPreset override
            pipeline = AnalyzePipeline()
            result = pipeline.run(
                self.filepath, progress=_on_progress,
                va_preset=self.va_preset,
            )

            # Downsample for chart + waveform
            rms_times = result.features.rms_times
            rms_values = result.features.rms_values
            if len(rms_times) > 500:
                step = max(1, len(rms_times) // 500)
                rms_times = rms_times[::step]
                rms_values = rms_values[::step]

            # Load raw waveform for display
            y, sr = librosa.load(self.filepath, sr=22050, mono=True)
            waveform = y[::100].tolist()

            # Back-compat: build scenes dict for scenes_tab.py
            scenes = []
            for seg in result.segments:
                if seg.drgbw is None or seg.hsv is None:
                    continue
                d, r, g, b, w = (seg.drgbw.dimmer, seg.drgbw.r,
                                 seg.drgbw.g, seg.drgbw.b, seg.drgbw.w)
                drgbw_dict = hsv_to_drgbw(seg.hsv.h, seg.hsv.s, seg.hsv.v)
                fixtures = []
                for f in range(self.fixture_count):
                    fixtures.append({
                        'fixture': f + 1, 'd': d, 'r': r,
                        'g': g, 'b': b, 'w': w,
                    })
                scenes.append({
                    'index': seg.index,
                    'label': seg.label,
                    'start': seg.start,
                    'end': seg.end,
                    'duration': seg.duration,
                    'fade_ms': 1000,
                    'color': '#%02x%02x%02x' % drgbw_dict['rgb_255'],
                    'valence': seg.va.valence if seg.va else 0.0,
                    'arousal': seg.va.arousal if seg.va else 0.0,
                    'hue': seg.hsv.h,
                    'pattern': seg.pattern,
                    'fixtures': fixtures,
                })

            # Result dict: v6 + back-compat
            r_dict = {
                'filepath': self.filepath,
                'filename': os.path.basename(self.filepath),
                'v6_result': result,
                'features': {
                    'duration': result.features.duration,
                    'tempo': result.features.tempo,
                    'rms_mean': result.features.rms_mean,
                    'sc_mean': result.features.sc_mean,
                    'mfcc1_mean': result.features.mfcc1_mean,
                    'chroma_major': result.features.chroma_major,
                    'chroma_peak': result.features.chroma_peak,
                    'onset_rate': result.features.onset_rate,
                    'rms_times': rms_times,
                    'rms_values': rms_values,
                },
                'segments': [
                    {
                        'index': seg.index, 'label': seg.label,
                        'start': seg.start, 'end': seg.end,
                        'duration': seg.duration,
                        'rms': seg.rms, 'sc': seg.sc,
                        'va': seg.va, 'hsv': seg.hsv,
                        'drgbw': seg.drgbw, 'pattern': seg.pattern,
                    } for seg in result.segments
                ],
                'scenes': scenes,
                'global_color': {
                    'valence': result.va.valence,
                    'arousal': result.va.arousal,
                    'quadrant': result.va.quadrant,
                    'quadrant_name': result.va.quadrant_name,
                    'hue': result.hsv.h,
                    'saturation': result.hsv.s,
                    'dimmer': result.drgbw.dimmer,
                    'rgbw': [result.drgbw.r, result.drgbw.g,
                             result.drgbw.b, result.drgbw.w],
                    'hex': '#%02x%02x%02x' % tuple(
                        hsv_to_drgbw(result.hsv.h, result.hsv.s, result.hsv.v)['rgb_255']
                    ),
                },
                'waveform': waveform,
                'sr': sr,
            }
            self.finished.emit(r_dict)
        except Exception:
            self.error.emit(traceback.format_exc())


# ─────────────────────────────────────────────
# Audio tab widget
# ─────────────────────────────────────────────
class AudioTab(QWidget):
    export_to_scene = Signal()  # emitted when user clicks "Export to Scene"

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.current_filepath: str | None = None
        self.worker: AnalyzeWorker | None = None
        self.selected_segment_index: int | None = None
        self.setObjectName("panelContent")
        self._build_ui()

    # ── UI build
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel("Audio Analysis")
        title.setObjectName("panelTitle")
        header.addWidget(title)
        header.addStretch()
        self.status_label = QLabel("No file analyzed")
        # feedback baris 64: keterangan seberang lebih gede
        self.status_label.setStyleSheet("color: #c8c8c8; font-size: 15px; font-weight: 600;")
        header.addWidget(self.status_label)
        root.addLayout(header)

        sub = QLabel(
            "Load a WAV/MP3/FLAC/OGG file to extract features, segment the song, "
            "and compute per-segment color (8-stage v6 pipeline)."
        )
        sub.setObjectName("panelDesc")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Toolbar
        tb = QHBoxLayout()
        self.load_btn = QPushButton("Load Audio File…")
        self.load_btn.clicked.connect(self._on_load)
        tb.addWidget(self.load_btn)

        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.analyze_btn.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: #0d0d0d; "
            "border: 1px solid #2ecc71; font-weight: 700; padding: 4px 12px; }"
            "QPushButton:hover { background-color: #27ae60; }"
            "QPushButton:disabled { background-color: #2a2a2a; color: #707070; border: 1px solid #2a2a2a; }"
        )
        tb.addWidget(self.analyze_btn)

        self.remove_btn = QPushButton("Remove Song")
        self.remove_btn.setEnabled(False)  # v6: disabled until song selected
        self.remove_btn.clicked.connect(self._on_remove_song)
        tb.addWidget(self.remove_btn)

        self.export_btn = QPushButton("→ Export to Scene")
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.setEnabled(False)  # v6: disabled until analysis done
        self.export_btn.setToolTip("Switch to the Scenes tab with the current song's scenes")
        self.export_btn.clicked.connect(self.export_to_scene)
        tb.addWidget(self.export_btn)

        tb.addStretch()
        root.addLayout(tb)

        # Progress bar (v6: determinate 0-100, rotating stage text)
        self.progress = QProgressBar()
        self.progress.setObjectName("analyzeProgress")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        # v6.9 #28: show "Stage X/3" prefix in progress bar text
        self.progress.setFormat("Ready")
        self.progress.hide()
        root.addWidget(self.progress)

        # Main content (3 columns)
        main = QHBoxLayout()
        main.setSpacing(10)

        # Left: song list
        self.song_list = QListWidget()
        self.song_list.setMaximumWidth(220)
        self.song_list.currentItemChanged.connect(self._on_song_select)
        self.song_list.setStyleSheet("""
            QListWidget {
                background-color: #141414;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                color: #e8e8e8;
                font-size: 11px;
            }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #1a1a1a; }
            QListWidget::item:selected {
                background-color: #1f1f1f;
                color: #2ecc71;
            }
        """)
        main.addWidget(self.song_list)

        # Center: visualizations + fixture grid
        center = QVBoxLayout()
        center.setSpacing(8)
        self.va_diagram = VADiagram()
        center.addWidget(self.va_diagram)
        self.rms_chart = RMSChart()
        center.addWidget(self.rms_chart, 1)
        self.waveform = WaveformView()
        center.addWidget(self.waveform)
        # v6: 2D fixture grid (NEW)
        self.fixture_grid = FixtureGrid(cols=4, rows=4, cell_size=44)
        center.addWidget(self.fixture_grid)
        main.addLayout(center, 2)

        # Right: features panel
        self.features_box = QGroupBox("Features")
        self.features_box.setStyleSheet("""
            QGroupBox {
                color: #2ecc71;
                font-weight: 700;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                margin-top: 10px;
                padding: 12px 8px 8px 8px;
                background-color: #0f0f0f;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        fl = QFormLayout()
        fl.setSpacing(6)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_filename = self._mk_label()
        self.lbl_duration = self._mk_label()
        self.lbl_tempo = self._mk_label()
        self.lbl_rms = self._mk_label()
        self.lbl_sc = self._mk_label()
        self.lbl_mfcc = self._mk_label()
        self.lbl_chroma = self._mk_label()
        self.lbl_onset = self._mk_label()
        self.lbl_segments = self._mk_label()
        sep = QLabel("")
        sep.setStyleSheet("color: #3a3a3a;")
        fl.addRow("File:", self.lbl_filename)
        fl.addRow("Duration:", self.lbl_duration)
        fl.addRow("Tempo (BPM):", self.lbl_tempo)
        fl.addRow("RMS Mean:", self.lbl_rms)
        fl.addRow("Spectral Centroid:", self.lbl_sc)
        fl.addRow("MFCC1:", self.lbl_mfcc)
        fl.addRow("Chroma Major:", self.lbl_chroma)
        fl.addRow("Onset Rate:", self.lbl_onset)
        fl.addRow("Segments:", self.lbl_segments)
        fl.addRow(sep)
        self.lbl_valence = self._mk_label()
        self.lbl_arousal = self._mk_label()
        self.lbl_hue = self._mk_label()
        self.lbl_saturation = self._mk_label()
        self.lbl_dimmer = self._mk_label()
        self.lbl_rgbw = self._mk_label()
        self.lbl_color = self._mk_label(bold=True)
        fl.addRow("Valence:", self.lbl_valence)
        fl.addRow("Arousal:", self.lbl_arousal)
        fl.addRow("Hue:", self.lbl_hue)
        fl.addRow("Saturation:", self.lbl_saturation)
        fl.addRow("Dimmer:", self.lbl_dimmer)
        fl.addRow("RGBW:", self.lbl_rgbw)
        fl.addRow("Color:", self.lbl_color)
        self.features_box.setLayout(fl)
        self.features_box.setMaximumWidth(280)
        main.addWidget(self.features_box)

        root.addLayout(main, 1)

        # v6: Per-segment color chips strip
        seg_label = QLabel("Segments  (click chip → apply to fixture grid)")
        seg_label.setStyleSheet("color: #707070; font-size: 11px; padding: 4px 0;")
        root.addWidget(seg_label)

        self.segments_strip = QScrollArea()
        self.segments_strip.setWidgetResizable(True)
        self.segments_strip.setFixedHeight(140)
        self.segments_strip.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.segments_strip.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.segments_strip.setStyleSheet("""
            QScrollArea {
                background-color: #0d0d0d;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
            }
        """)

        self.segments_container = QWidget()
        self.segments_layout = QHBoxLayout(self.segments_container)
        self.segments_layout.setContentsMargins(8, 8, 8, 8)
        self.segments_layout.setSpacing(8)
        self.segments_layout.addStretch()
        self.segments_strip.setWidget(self.segments_container)
        root.addWidget(self.segments_strip)

        # Bottom: filepath
        self.filepath_label = QLabel("No file loaded")
        self.filepath_label.setObjectName("dim")
        self.filepath_label.setWordWrap(True)
        self.filepath_label.setStyleSheet("color: #707070; font-size: 10px;")
        root.addWidget(self.filepath_label)

        self._refresh_song_list()

    def _mk_label(self, bold: bool = False) -> QLabel:
        lbl = QLabel("—")
        weight = "font-weight: 700;" if bold else ""
        lbl.setStyleSheet(
            f"color: #e8e8e8; font-family: 'Consolas', 'Courier New', monospace; "
            f"font-size: 11px; {weight}"
        )
        return lbl

    # ── Actions
    def _on_load(self):
        cfg = app_config()
        start_dir = cfg.last_audio_dir or ""

        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", start_dir,
            "Audio Files (*.mp3 *.wav *.flac *.ogg);;All Files (*.*)"
        )
        if not filepath:
            return
        self.current_filepath = filepath
        self.filepath_label.setText(filepath)
        self.analyze_btn.setEnabled(True)
        self.status_label.setText("Ready to analyze")
        cfg.last_audio_dir = os.path.dirname(filepath)

    def _on_analyze(self):
        if not self.current_filepath:
            return
        if self.worker and self.worker.isRunning():
            return

        self.analyze_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        self.status_label.setText("Analyzing…")
        self.progress.show()
        self.progress.setValue(0)
        self.progress.setFormat("Starting…")

        fixture_count = 4
        # Phase 3: load active VAPreset from app_config (v6)
        active_preset_name = app_config().active_va_preset
        active_preset = (
            load_preset(active_preset_name) if active_preset_name else None
        )
        self.worker = AnalyzeWorker(
            self.current_filepath, fixture_count,
            va_preset=active_preset,
        )
        self.worker.finished.connect(self._on_analyze_done)
        self.worker.error.connect(self._on_analyze_error)
        self.worker.progress.connect(self._on_analyze_progress)
        self.worker.start()

    def _on_analyze_progress(self, percent: int, message: str) -> None:
        """v6: rotating stage text in progress bar."""
        self.progress.setValue(percent)
        self.progress.setFormat(f"{message}  ({percent}%)")

    def _on_analyze_done(self, result: dict):
        self.analyze_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self.progress.hide()
        self.worker = None

        # Add to manager's song state
        self.manager.song_counter += 1
        song_id = f"song_{self.manager.song_counter}"
        self.manager.songs[song_id] = result
        self.manager.current_song_id = song_id

        n_scenes = len(result.get("scenes", []))
        self.export_btn.setEnabled(n_scenes > 0)
        self.remove_btn.setEnabled(True)

        # Update list
        self._refresh_song_list()
        self._display_song(result)
        # Phase 3B: refresh ColorMixerTab song dropdowns
        main_window = self.window()
        if hasattr(main_window, "panels") and "color" in main_window.panels:
            main_window.panels["color"].set_songs(self.manager.songs)
        self.status_label.setText(
            f"Done — {result['filename']} ({n_scenes} scenes)"
        )
        show_toast(self, f"Analyzed {result['filename']} — {n_scenes} scenes", "success")

    def _on_analyze_error(self, err: str):
        self.analyze_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self.progress.hide()
        self.worker = None
        self.status_label.setText("Analysis failed")
        show_toast(self, "Analysis failed — see log for details", "error")

    def _on_remove_song(self):
        if not self.manager.songs:
            self.export_btn.setEnabled(False)
            self.remove_btn.setEnabled(False)
        item = self.song_list.currentItem()
        if not item:
            return
        song_id = item.data(Qt.ItemDataRole.UserRole)
        if song_id in self.manager.songs:
            del self.manager.songs[song_id]
        if self.manager.current_song_id == song_id:
            self.manager.current_song_id = None
        self._refresh_song_list()
        self._clear_display()
        if not self.manager.songs:
            self.remove_btn.setEnabled(False)
            self.export_btn.setEnabled(False)

    def _on_song_select(self, current, previous):
        if not current:
            return
        song_id = current.data(Qt.ItemDataRole.UserRole)
        if song_id in self.manager.songs:
            self._display_song(self.manager.songs[song_id])

    def _refresh_song_list(self):
        self.song_list.clear()
        for sid, data in self.manager.songs.items():
            label = f"{data.get('filename', sid)}\n"
            label += f"  {data['features']['duration']:.1f}s · "
            label += f"{data['features']['tempo']:.0f} BPM · "
            label += f"{len(data.get('scenes', []))} scenes"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, sid)
            self.song_list.addItem(item)
            if sid == self.manager.current_song_id:
                self.song_list.setCurrentItem(item)

    def _display_song(self, song: dict):
        f = song["features"]
        c = song["global_color"]
        segments_data = song.get("segments", [])

        self.lbl_filename.setText(song.get("filename", "—"))
        self.lbl_duration.setText(f"{f['duration']:.1f} s")
        self.lbl_tempo.setText(f"{f['tempo']:.1f}")
        self.lbl_rms.setText(f"{f['rms_mean']:.4f}")
        self.lbl_sc.setText(f"{f['sc_mean']:.0f} Hz")
        self.lbl_mfcc.setText(f"{f['mfcc1_mean']:.2f}")
        self.lbl_chroma.setText(f"{f['chroma_major']:.3f}")
        self.lbl_onset.setText(f"{f['onset_rate']:.2f} /s")
        self.lbl_segments.setText(
            f"{len(segments_data)} ({', '.join(set(s['label'] for s in segments_data))})"
        )

        self.lbl_valence.setText(f"{c['valence']:.3f}")
        self.lbl_arousal.setText(f"{c['arousal']:.3f}")
        self.lbl_hue.setText(f"{c['hue']:.1f}°")
        self.lbl_saturation.setText(f"{c['saturation']:.3f}")
        self.lbl_dimmer.setText(f"{c['dimmer']} / 255")
        self.lbl_rgbw.setText(
            f"[{c['rgbw'][0]}, {c['rgbw'][1]}, {c['rgbw'][2]}, {c['rgbw'][3]}]"
        )
        self.lbl_color.setText(f"  {c['hex']}  ")
        self.lbl_color.setStyleSheet(
            f"background-color: {c['hex']}; color: #0d0d0d; padding: 4px 8px; "
            f"font-weight: 700; font-family: 'Consolas', monospace; font-size: 12px; "
            f"border: 1px solid #0d0d0d;"
        )

        # Visualizations
        self.va_diagram.set_point(c["valence"], c["arousal"])
        self.rms_chart.set_data(f.get("rms_times", []), f.get("rms_values", []))
        self.waveform.set_data(song.get("waveform", []), song.get("sr", 22050))

        # v6: Populate segment chips + fixture grid
        self._populate_segments(segments_data)

        self.filepath_label.setText(song.get('filepath', '—'))

    def _populate_segments(self, segments_data: list) -> None:
        """Clear + rebuild segment chip strip."""
        while self.segments_layout.count() > 0:
            item = self.segments_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self.segments_layout.addStretch()

        for seg in segments_data:
            drgbw_obj = seg.get('drgbw')
            hsv_obj = seg.get('hsv')
            if drgbw_obj is None or hsv_obj is None:
                continue

            drgbw_dict = hsv_to_drgbw(hsv_obj.h, hsv_obj.s, hsv_obj.v)
            quadrant = seg['va'].quadrant if seg.get('va') else ""

            chip = SegmentColorChip(
                index=seg['index'],
                label=seg['label'],
                start=seg['start'],
                end=seg['end'],
                drgbw=drgbw_dict,
                pattern=seg['pattern'],
                hue=hsv_obj.h,
                quadrant=quadrant,
            )
            chip.clicked.connect(self._on_segment_clicked)
            self.segments_layout.insertWidget(
                self.segments_layout.count() - 1, chip
            )

        # Auto-select first segment
        if segments_data:
            self._on_segment_clicked(0)

    def _on_segment_clicked(self, index: int) -> None:
        """Apply selected segment's color + pattern to fixture grid."""
        # Update chip selected state
        for i in range(self.segments_layout.count() - 1):
            item = self.segments_layout.itemAt(i)
            if item is None:
                continue
            chip = item.widget()
            if isinstance(chip, SegmentColorChip):
                chip.set_selected(chip.index == index)

        self.selected_segment_index = index

        song = self.manager.songs.get(self.manager.current_song_id)
        if not song:
            return
        segments = song.get('segments', [])
        if index >= len(segments):
            return
        seg = segments[index]

        hsv = seg.get('hsv')
        drgbw = seg.get('drgbw')
        if hsv is None or drgbw is None:
            return

        drgbw_dict = hsv_to_drgbw(hsv.h, hsv.s, hsv.v)
        rgb_255 = drgbw_dict['rgb_255']

        self.fixture_grid.set_pattern(
            pattern=seg['pattern'],
            rgb_255=rgb_255,
            dimmer=drgbw.dimmer,
            segment_name=seg['label'],
            quadrant=seg['va'].quadrant if seg.get('va') else "",
        )

    def _clear_display(self):
        for lbl in [self.lbl_filename, self.lbl_duration, self.lbl_tempo, self.lbl_rms,
                    self.lbl_sc, self.lbl_mfcc, self.lbl_chroma, self.lbl_onset, self.lbl_segments,
                    self.lbl_valence, self.lbl_arousal, self.lbl_hue, self.lbl_saturation,
                    self.lbl_dimmer, self.lbl_rgbw]:
            lbl.setText("—")
        self.lbl_color.setText("—")
        self.lbl_color.setStyleSheet(
            "color: #e8e8e8; font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700;"
        )
        self.va_diagram.clear()
        self.rms_chart.clear()
        self.waveform.clear()
        self.fixture_grid.clear()
        self.filepath_label.setText("No file loaded")
        # Clear segment chips
        while self.segments_layout.count() > 0:
            item = self.segments_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self.segments_layout.addStretch()
