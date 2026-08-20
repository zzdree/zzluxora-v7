"""
Program panel — QTabWidget with 8 sub-tabs (PRD §4.5–4.12):
Address, Analyze, Scenes, Chase, Page, Mixer, Preview, Output.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from panels import BasePanel
from panels.address_tab import AddressTab
from fixture_manager import FixtureManager


SUBTABS = [
    ("Address",   "address"),
    ("Analyze",   "analyze"),
    ("Scenes",    "scenes"),
    ("Chase",     "chase"),
    ("Page",      "page"),
    ("Mixer",     "mixer"),
    ("Preview",   "preview"),
    ("Output",    "output"),
]


class ProgramPanel(BasePanel):
    PANEL_NAME = "Program"  # Phase 18: no emoji (was 🎛️  Program)
    PANEL_DESC = (
        "Audio analysis, scene generation, and chase sequencing. "
        "8 sub-tabs: Address, Analyze, Scenes, Chase, Page, Mixer, Preview, Output."
    )

    def __init__(self, manager: FixtureManager, parent=None):
        self.manager = manager
        super().__init__(parent)

    def _build_ui(self):
        # Replace base header with our own + tabs
        while self._root.count():
            item = self._root.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # Title
        title = QLabel(self.PANEL_NAME)
        title.setObjectName("panelTitle")
        self._root.addWidget(title)

        desc = QLabel(self.PANEL_DESC)
        desc.setObjectName("panelDesc")
        desc.setWordWrap(True)
        self._root.addWidget(desc)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setObjectName("programTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        for label, key in SUBTABS:
            if key == "address":
                tab = AddressTab(self.manager)
            elif key == "analyze":
                from panels.audio_tab import AudioTab
                tab = AudioTab(self.manager)
            elif key == "scenes":
                from panels.scenes_tab import ScenesTab
                tab = ScenesTab(self.manager)
            elif key == "chase":
                from panels.chase_tab import ChaseTab
                tab = ChaseTab(self.manager)
            elif key == "mixer":
                from panels.mixer_tab import MixerTab
                tab = MixerTab(self.manager)
            elif key == "preview":
                from panels.preview_tab import PreviewTab
                tab = PreviewTab(self.manager)
            elif key == "output":
                from panels.output_tab import OutputTab
                tab = OutputTab(self.manager)
            elif key == "page":
                from panels.page_tab import PageTab
                tab = PageTab(self.manager)
            else:
                tab = self._placeholder(key, label)
            self.tabs.addTab(tab, f"  {label}  ")

        self._root.addWidget(self.tabs, 1)

    def _placeholder(self, key: str, label: str) -> QWidget:
        w = QWidget()
        w.setObjectName("panelContent")
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 20, 20, 20)
        msg = QLabel(f"{label} — coming in a later milestone")
        msg.setObjectName("dim")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addStretch()
        v.addWidget(msg)
        v.addStretch()
        return w
