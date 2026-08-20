"""
SegmentColorChip — v6 per-segment color visualization (math model §[6]).

Clickable card showing per-segment DRGBW + pattern.
Click → emits segment index → audio_tab applies to FixtureGrid.

Display:
  ┌──────────────────┐
  │ ● Intro          │  ← color swatch + label
  │ 0:00 – 0:32      │  ← time range
  │ D=34 R=0 G=6     │  ← DRGBW values (green)
  │ B=4  W=28        │
  │ [all_on]         │  ← pattern badge (yellow)
  └──────────────────┘
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)


class SegmentColorChip(QFrame):
    """Clickable card showing per-segment DRGBW color + pattern."""
    clicked = Signal(int)  # emits segment index

    def __init__(self, index: int, label: str, start: float, end: float,
                 drgbw: dict, pattern: str, hue: float, quadrant: str = "",
                 parent=None):
        super().__init__(parent)
        self.index = index
        self.segment_label = label
        self.setObjectName("segmentChip")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(150, 110)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(2)

        # Row 1: color swatch + label
        color_row = QHBoxLayout()
        color_row.setSpacing(6)

        self.swatch = QFrame()
        self.swatch.setFixedSize(22, 22)
        rgb = drgbw.get("rgb_255", (128, 128, 128))
        self.swatch.setStyleSheet(
            f"background-color: rgb({rgb[0]}, {rgb[1]}, {rgb[2]});"
            f"border: 1px solid #2a2a2a; border-radius: 3px;"
        )
        color_row.addWidget(self.swatch)

        lbl_label = QLabel(label.upper())
        lbl_label.setStyleSheet(
            "color: #e8e8e8; font-weight: 700; font-size: 11px; letter-spacing: 1px;"
        )
        color_row.addWidget(lbl_label)
        color_row.addStretch()
        root.addLayout(color_row)

        # Row 2: time range
        time_text = self._fmt_time(start, end)
        lbl_time = QLabel(time_text)
        lbl_time.setStyleSheet(
            "color: #707070; font-size: 10px; font-family: 'Consolas', monospace;"
        )
        root.addWidget(lbl_time)

        # Row 3: DRGBW
        d, r, g, b, w = (drgbw["dimmer"], drgbw["r"], drgbw["g"],
                         drgbw["b"], drgbw["w"])
        drgbw_text = f"D={d:>3}  R={r:>3}  G={g:>3}"
        lbl_drgbw1 = QLabel(drgbw_text)
        lbl_drgbw1.setStyleSheet(
            "color: #2ecc71; font-size: 10px; font-family: 'Consolas', monospace;"
        )
        root.addWidget(lbl_drgbw1)

        drgbw_text2 = f"B={b:>3}  W={w:>3}  H={hue:>5.1f}°"
        lbl_drgbw2 = QLabel(drgbw_text2)
        lbl_drgbw2.setStyleSheet(
            "color: #2ecc71; font-size: 10px; font-family: 'Consolas', monospace;"
        )
        root.addWidget(lbl_drgbw2)

        # Row 4: pattern badge + quadrant
        badge_row = QHBoxLayout()
        badge_row.setSpacing(4)

        lbl_pattern = QLabel(pattern.upper())
        lbl_pattern.setStyleSheet(
            "color: #0d0d0d; background-color: #f1c40f; font-size: 9px; "
            "font-weight: 700; padding: 1px 5px; border-radius: 2px;"
        )
        lbl_pattern.setMaximumWidth(90)
        badge_row.addWidget(lbl_pattern)

        if quadrant:
            lbl_q = QLabel(quadrant)
            lbl_q.setStyleSheet(
                "color: #1a1a1a; background-color: #4aa3ff; font-size: 9px; "
                "font-weight: 700; padding: 1px 5px; border-radius: 2px;"
            )
            badge_row.addWidget(lbl_q)
        badge_row.addStretch()
        root.addLayout(badge_row)

        # Apply default style
        self.set_selected(False)

    @staticmethod
    def _fmt_time(start: float, end: float) -> str:
        sm, ss = divmod(int(start), 60)
        em, es = divmod(int(end), 60)
        return f"{sm}:{ss:02d} – {em}:{es:02d}"

    def set_selected(self, selected: bool) -> None:
        if selected:
            self.setStyleSheet(
                "QFrame#segmentChip {"
                "background-color: #1f2a24; border: 2px solid #2ecc71; border-radius: 4px;"
                "}"
            )
        else:
            self.setStyleSheet(
                "QFrame#segmentChip {"
                "background-color: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 4px;"
                "}"
                "QFrame#segmentChip:hover { border: 1px solid #2ecc71; }"
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)
        super().mousePressEvent(event)
