"""
HeaderBar — top shell of the v5 MainWindow.

Layout (height 48 px):
  [ BRAND: zzluxora ]  ······ [ project label ] ······ [ Art-Net pill ]
  [ Play/Pause ] [ Connect ] [ Blackout ]

The brand title uses QPainter with a white gradient (italic + bold) — QSS
background-clip:text is unreliable on older Qt builds, so we paint it ourselves.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QLinearGradient, QPainter, QPen, QColor, QBrush
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from widgets.artnet_pill import ArtNetStatusPill


BRAND_TEXT = "zzluxora"  # v6: lowercase (was ZZLIGHT-LUXORA in v5)


class BrandTitle(QLabel):
    """Italic + bold brand title with white horizontal gradient."""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(BRAND_TEXT, parent)
        self.setObjectName("brandTitle")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(180)
        # We paint the gradient ourselves in paintEvent, so the QSS colour
        # is irrelevant — leave the label transparent.
        self.setStyleSheet("background: transparent; padding: 0 16px;")

    def sizeHint(self):
        # Slightly wider than default for the gradient spread
        fm = self.fontMetrics()
        from PySide6.QtCore import QMargins
        return fm.size(0, BRAND_TEXT).grownBy(QMargins(16, 0, 16, 0))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = QFont(self.font())
        font.setItalic(True)
        font.setBold(True)
        font.setPointSize(18)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        painter.setFont(font)

        # v6: white gradient (sesuai design spec — bukan green lagi)
        gradient = QLinearGradient(0, 0, max(1, self.width()), 0)
        gradient.setColorAt(0.0, QColor("#ffffff"))
        gradient.setColorAt(0.5, QColor("#cccccc"))
        gradient.setColorAt(1.0, QColor("#ffffff"))
        pen = QPen(QBrush(gradient), 1)
        painter.setPen(pen)

        # Vertically centered, left-aligned, leave 16 px gutter
        rect = self.rect().adjusted(16, 0, -16, 0)
        painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, BRAND_TEXT)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class HeaderBar(QFrame):
    """Top-of-window header: brand | project | artnet pill | play | connect | blackout."""

    # Phase 9: single toggle signal (replaces start_clicked / stop_clicked)
    play_toggled = Signal(bool)  # emits True when starting, False when stopping
    # Phase 12: connect + blackout moved to header
    connect_clicked = Signal()
    blackout_clicked = Signal()
    # Phase 13: fixture list dropdown trigger
    fixture_dropdown_clicked = Signal()
    brand_clicked = Signal()
    artnet_pill_clicked = Signal()

    def __init__(self, project_name: str = "Untitled.zlx", parent=None):
        super().__init__(parent)
        self.setObjectName("headerBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(8)

        # ── Left: brand title
        self.brand = BrandTitle(self)
        self.brand.clicked.connect(self.brand_clicked)
        layout.addWidget(self.brand)

        # Fixtures dropdown trigger (feedback baris 132-133: buka ke bawah)
        self.fixtures_btn = QPushButton("Fixtures  ▾")
        self.fixtures_btn.setObjectName("headerButton")
        self.fixtures_btn.setToolTip("Show fixture library — drag a fixture onto the Address grid")
        self.fixtures_btn.clicked.connect(self.fixture_dropdown_clicked)
        layout.addWidget(self.fixtures_btn)

        # ── Center: project label (italic, muted) — Phase 9: drop "Project: " prefix,
        #    full path surfaced as tooltip on hover.
        self.project_label = QLabel(f"<i>{project_name}</i>")
        self.project_label.setStyleSheet(
            "color:#707070;font-size:11px;padding:0 8px;"
        )
        self.project_label.setToolTip("")
        layout.addWidget(self.project_label, 1)  # stretch to push right side

        # ── Right: Art-Net pill + Play/Connect/Blackout (Phase 12: 3 buttons)
        self.pill = ArtNetStatusPill(self)
        self.pill.clicked.connect(self.artnet_pill_clicked)
        layout.addWidget(self.pill)

        self.play_btn = QPushButton("▶  Play")
        self.play_btn.setObjectName("headerButton")
        self.play_btn.setProperty("class", "playBtn")
        self.play_btn.setCheckable(True)
        self.play_btn.setChecked(False)
        self.play_btn.clicked.connect(self._on_play_clicked)
        layout.addWidget(self.play_btn)

        # Phase 12: Connect button (was in Output tab, moved to header)
        self.connect_btn = QPushButton("Connect")  # DESIGN.md §5.3: no emoji
        self.connect_btn.setObjectName("headerButton")
        self.connect_btn.setProperty("class", "connectBtn")
        self.connect_btn.setToolTip("Connect to selected Art-Net node")
        self.connect_btn.clicked.connect(self.connect_clicked)
        layout.addWidget(self.connect_btn)

        # Phase 12: Blackout button (was in Output tab, moved to header)
        self.blackout_btn = QPushButton("Blackout")  # DESIGN.md §5.3: no emoji
        self.blackout_btn.setObjectName("headerButton")
        self.blackout_btn.setProperty("class", "blackoutBtn")
        self.blackout_btn.setToolTip("Send 0 to all 512 channels (B)")
        self.blackout_btn.clicked.connect(self.blackout_clicked)
        layout.addWidget(self.blackout_btn)

    # ── public API
    def set_project_name(self, name: str) -> None:
        # Phase 9: drop "Project: " prefix — just the filename, italic.
        self.project_label.setText(f"<i>{name}</i>")

    def set_artnet_state(self, state: str) -> None:
        self.pill.set_state(state)

    def set_playing(self, playing: bool) -> None:
        """Sync button label + checked state from outside (Space / Esc / Blackout)."""
        self.play_btn.blockSignals(True)
        self.play_btn.setChecked(playing)
        self.play_btn.setText("■  Stop" if playing else "▶  Play")
        self.play_btn.blockSignals(False)

    def set_connected(self, connected: bool, target_ip: str = "") -> None:
        """Sync connect button label."""
        self.connect_btn.blockSignals(True)
        if connected:
            self.connect_btn.setText(f"Disconnect {target_ip}")
        else:
            self.connect_btn.setText("Connect")
        self.connect_btn.blockSignals(False)

    def set_tooltip(self, path: str) -> None:
        """Show full file path on hover (empty = no tooltip)."""
        self.project_label.setToolTip(path or "")

    def _on_play_clicked(self) -> None:
        playing = self.play_btn.isChecked()
        self.play_btn.setText("■  Stop" if playing else "▶  Play")
        self.play_toggled.emit(playing)
