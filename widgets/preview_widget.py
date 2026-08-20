"""
PreviewWidget (v6 Phase 3D) — visual scrubber + live DRGBW preview.

Features (MVP, no real audio playback):
  - Song selector (combo of analyzed songs)
  - Time scrubber (drag to seek, 0.1s resolution)
  - Play/Pause (simulated via QTimer, advances scrubber at 1x)
  - Live DRGBW swatch (large, centered) + RGBW readout
  - 2D fixture grid rendering current segment's pattern
  - Per-segment timeline strip (colored bars per segment)
  - S/V curve application to live output (per-segment)

Public API:
  set_songs(songs: Dict[str, dict])   populate song combo
  set_s_curve(curve: CurveLUT | None)
  set_v_curve(curve: CurveLUT | None)
"""
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider,
    QPushButton, QFrame, QGridLayout, QSizePolicy,
)

from widgets.fixture_grid import FixtureGrid
from engines.curve_lut import CurveLUT


class _SegmentTimeline(QWidget):
    """Horizontal strip showing segment ranges as colored bars."""

    segmentClicked = Signal(int)  # segment index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.segments: list = []
        self.setMinimumHeight(28)
        self.setStyleSheet("background-color: #0a0a0a; border: 1px solid #2a2a2a;")

    def set_segments(self, segments: list) -> None:
        self.segments = segments
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if not self.segments:
            p.setPen(QColor("#3a3a3a"))
            p.drawText(w // 2 - 60, h // 2 + 4, "(no segments)")
            p.end()
            return
        total_start = self.segments[0].get("start", 0)
        total_end = self.segments[-1].get("end", total_start + 1)
        span = max(total_end - total_start, 0.01)
        for seg in self.segments:
            x0 = (seg.get("start", 0) - total_start) / span * w
            x1 = (seg.get("end", 0) - total_start) / span * w
            drgbw = seg.get("drgbw")
            if drgbw is None:
                color = QColor("#2a2a2a")
            else:
                if hasattr(drgbw, "r"):
                    color = QColor(drgbw.r, drgbw.g, drgbw.b)
                else:
                    color = QColor(drgbw.get("r", 64), drgbw.get("g", 64), drgbw.get("b", 64))
            p.fillRect(int(x0), 2, max(1, int(x1 - x0)), h - 4, color)
            # Label
            label = seg.get("label", "?")
            p.setPen(QColor("#0d0d0d"))
            font = QFont("Consolas", 8, QFont.Weight.Bold)
            p.setFont(font)
            p.drawText(int(x0) + 4, h - 6, label[:6])
        p.end()


class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.songs: dict = {}
        self.current_result: dict = None
        self.duration: float = 0.0
        self.s_curve: CurveLUT | None = None
        self.v_curve: CurveLUT | None = None
        self._playing = False
        self._timer = QTimer(self)
        self._timer.setInterval(100)  # 0.1s tick
        self._timer.timeout.connect(self._on_tick)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── Song row
        song_row = QHBoxLayout()
        song_row.addWidget(QLabel("Song:"))
        self.song_combo = QComboBox()
        self.song_combo.setMinimumWidth(200)
        self.song_combo.currentIndexChanged.connect(self._on_song_change)
        song_row.addWidget(self.song_combo, 1)
        root.addLayout(song_row)

        # ── Scrubber row
        scrub_row = QHBoxLayout()
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(36, 28)
        self.play_btn.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: #0d0d0d; "
            "border: 1px solid #2ecc71; font-weight: 700; }"
            "QPushButton:hover { background-color: #27ae60; }"
        )
        self.play_btn.clicked.connect(self._on_play_toggle)
        scrub_row.addWidget(self.play_btn)

        self.scrubber = QSlider(Qt.Orientation.Horizontal)
        self.scrubber.setRange(0, 0)
        self.scrubber.setValue(0)
        self.scrubber.valueChanged.connect(self._on_scrub)
        scrub_row.addWidget(self.scrubber, 1)

        self.time_label = QLabel("0:00.0 / 0:00.0")
        self.time_label.setFixedWidth(110)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(
            "color: #c8c8c8; font-family: 'Consolas', monospace; font-size: 11px;"
        )
        scrub_row.addWidget(self.time_label)
        root.addLayout(scrub_row)

        # ── Timeline
        self.timeline = _SegmentTimeline()
        root.addWidget(self.timeline)

        # ── Center: swatch + RGBW readout
        center = QHBoxLayout()
        center.setSpacing(20)

        # Swatch
        swatch_box = QVBoxLayout()
        swatch_box.addStretch()
        self.swatch = QFrame()
        self.swatch.setFixedSize(160, 100)
        self.swatch.setStyleSheet(
            "background-color: #2a2a2a; border: 2px solid #3a3a3a; border-radius: 6px;"
        )
        swatch_box.addWidget(self.swatch, alignment=Qt.AlignmentFlag.AlignCenter)
        swatch_box.addStretch()
        center.addLayout(swatch_box)

        # RGBW readout + segment info
        info_box = QVBoxLayout()
        info_box.setSpacing(4)
        self.seg_label = QLabel("(no segment)")
        self.seg_label.setStyleSheet(
            "color: #2ecc71; font-size: 14px; font-weight: 700;"
        )
        info_box.addWidget(self.seg_label)
        self.time_seg_label = QLabel("")
        self.time_seg_label.setStyleSheet(
            "color: #909090; font-family: 'Consolas', monospace; font-size: 11px;"
        )
        info_box.addWidget(self.time_seg_label)
        self.rgbw_label = QLabel("R=— G=— B=— W=— D=—")
        self.rgbw_label.setStyleSheet(
            "color: #c8c8c8; font-family: 'Consolas', monospace; font-size: 12px;"
        )
        info_box.addWidget(self.rgbw_label)
        self.pattern_label = QLabel("Pattern: —")
        self.pattern_label.setStyleSheet(
            "color: #909090; font-size: 11px;"
        )
        info_box.addWidget(self.pattern_label)
        info_box.addStretch()
        center.addLayout(info_box, 1)
        root.addLayout(center)

        # ── Fixture grid
        self.fixture_grid = FixtureGrid(cols=4, rows=4, cell_size=36)
        root.addWidget(self.fixture_grid, alignment=Qt.AlignmentFlag.AlignCenter)

        # ── Curve apply hint
        hint = QLabel(
            "Live S/V curves applied: "
            + (f"S=on ({len(self.s_curve.points) if self.s_curve else 0} pts)"
               if self.s_curve else "S=off")
            + "  |  "
            + (f"V=on ({len(self.v_curve.points) if self.v_curve else 0} pts)"
               if self.v_curve else "V=off")
        )
        hint.setStyleSheet("color: #707070; font-size: 10px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.curve_hint = hint
        root.addWidget(hint)

        root.addStretch()

    # ── Public
    def set_songs(self, songs: dict) -> None:
        self.songs = songs
        current = self.song_combo.currentData()
        self.song_combo.blockSignals(True)
        self.song_combo.clear()
        self.song_combo.addItem("(select a song)", "")
        for song_id, data in songs.items():
            self.song_combo.addItem(data.get("filename", song_id), song_id)
        # Restore previous selection OR default to first real song
        if current:
            idx = self.song_combo.findData(current)
        else:
            idx = 1 if self.song_combo.count() > 1 else 0
        if idx >= 0:
            self.song_combo.setCurrentIndex(idx)
        self.song_combo.blockSignals(False)
        if self.song_combo.currentData():
            self._on_song_change(self.song_combo.currentIndex())

    def set_s_curve(self, curve: CurveLUT | None) -> None:
        self.s_curve = curve
        self._update_curve_hint()
        self._render_current()

    def set_v_curve(self, curve: CurveLUT | None) -> None:
        self.v_curve = curve
        self._update_curve_hint()
        self._render_current()

    # ── Internals
    def _on_song_change(self, idx: int) -> None:
        song_id = self.song_combo.currentData()
        if not song_id or song_id not in self.songs:
            self.current_result = None
            return
        self.current_result = self.songs[song_id]
        self.duration = self.current_result.get("features", {}).get("duration", 0.0)
        # Scrubber range: 0 to duration*10 (0.1s precision)
        self.scrubber.blockSignals(True)
        self.scrubber.setRange(0, int(self.duration * 10))
        self.scrubber.setValue(0)
        self.scrubber.blockSignals(False)
        # Timeline
        segments = self.current_result.get("segments", [])
        self.timeline.set_segments(segments)
        self._render_current()

    def _on_play_toggle(self) -> None:
        if self._playing:
            self._timer.stop()
            self._playing = False
            self.play_btn.setText("▶")
        else:
            if not self.current_result:
                return
            self._timer.start()
            self._playing = True
            self.play_btn.setText("⏸")

    def _on_tick(self) -> None:
        if not self.current_result:
            return
        new_val = self.scrubber.value() + 1
        if new_val > self.scrubber.maximum():
            self._on_play_toggle()
            return
        self.scrubber.setValue(new_val)

    def _on_scrub(self, value: int) -> None:
        t = value / 10.0
        self._render_at_time(t)
        # Update time label
        m = int(t // 60)
        s = t - m * 60
        total = self.duration
        tm = int(total // 60)
        ts = total - tm * 60
        self.time_label.setText(f"{m}:{s:04.1f} / {tm}:{ts:04.1f}")

    def _find_segment_at(self, t: float) -> dict | None:
        if not self.current_result:
            return None
        for seg in self.current_result.get("segments", []):
            if seg.get("start", 0) <= t < seg.get("end", 0):
                return seg
        return None

    def _apply_curves(self, r, g, b, w, d):
        """Apply S/V curves to DRGBW. S scales saturation, V scales dimmer."""
        if self.s_curve is not None:
            # Saturation: distance from gray
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            sat = (max_c - min_c) / 255.0 if max_c > 0 else 0
            new_sat = self.s_curve.evaluate(sat) * 255
            if max_c > 0 and sat > 0:
                scale = new_sat / sat
                r = int(min(255, r * scale))
                g = int(min(255, g * scale))
                b = int(min(255, b * scale))
        if self.v_curve is not None:
            d_norm = d / 255.0
            new_d = self.v_curve.evaluate(d_norm) * 255
            d = int(min(255, max(0, new_d)))
        return r, g, b, w, d

    def _render_current(self) -> None:
        t = self.scrubber.value() / 10.0
        self._render_at_time(t)

    def _render_at_time(self, t: float) -> None:
        seg = self._find_segment_at(t)
        if not seg:
            self.seg_label.setText("(no segment)")
            self.time_seg_label.setText("")
            self.rgbw_label.setText("R=— G=— B=— W=— D=—")
            self.pattern_label.setText("Pattern: —")
            self.swatch.setStyleSheet(
                "background-color: #2a2a2a; border: 2px solid #3a3a3a; border-radius: 6px;"
            )
            self.fixture_grid.clear()
            return
        drgbw = seg.get("drgbw")
        if drgbw is None:
            self.seg_label.setText(f"{seg.get('label', '?')}")
            self.rgbw_label.setText("(no color)")
            return
        if hasattr(drgbw, "r"):
            r, g, b, w, d = drgbw.r, drgbw.g, drgbw.b, drgbw.w, drgbw.dimmer
        else:
            r = drgbw.get("r", 0)
            g = drgbw.get("g", 0)
            b = drgbw.get("b", 0)
            w = drgbw.get("w", 0)
            d = drgbw.get("dimmer", 0)
        # Apply curves
        r, g, b, w, d = self._apply_curves(r, g, b, w, d)
        self.swatch.setStyleSheet(
            f"background-color: rgb({r}, {g}, {b}); "
            f"border: 2px solid #3a3a3a; border-radius: 6px;"
        )
        self.seg_label.setText(f"{seg.get('label', '?')}  seg #{seg.get('index', 0)}")
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        self.time_seg_label.setText(
            f"{start:.2f}s - {end:.2f}s  (duration {end - start:.2f}s)"
        )
        self.rgbw_label.setText(f"R={r:3d}  G={g:3d}  B={b:3d}  W={w:3d}  D={d:3d}")
        pattern = seg.get("pattern", "all_on")
        self.pattern_label.setText(f"Pattern: {pattern}")
        # Update fixture grid
        if pattern:
            self.fixture_grid.set_pattern(pattern, (r, g, b), d,
                                           segment_name=seg.get("label", "—"))

    def _update_curve_hint(self) -> None:
        s = "on" if self.s_curve else "off"
        v = "on" if self.v_curve else "off"
        self.curve_hint.setText(f"Live S/V curves applied: S={s}  |  V={v}")
