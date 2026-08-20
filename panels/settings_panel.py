"""Settings panel placeholder (M1)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QFormLayout, QSpinBox, QLineEdit
from panels import BasePanel


class SettingsPanel(BasePanel):
    PANEL_NAME = "Settings"  # Phase 18: no emoji (was ⚙️  Settings)
    PANEL_DESC = "Application configuration (Art-Net target, default fixtures)."

    def _build_ui(self):
        super()._build_ui()
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.target_ip = QLineEdit("127.0.0.1")
        self.universe = QSpinBox()
        self.universe.setRange(0, 15)
        self.universe.setValue(0)
        self.fps = QSpinBox()
        self.fps.setRange(1, 60)
        self.fps.setValue(30)
        self.fixture_count = QSpinBox()
        self.fixture_count.setRange(1, 64)
        self.fixture_count.setValue(4)

        form.addRow("Art-Net Target IP:", self.target_ip)
        form.addRow("Universe:", self.universe)
        form.addRow("FPS:", self.fps)
        form.addRow("Default Fixtures:", self.fixture_count)

        self.add_widget(self._wrap_form(form))
        # Phase 18: no emoji (was 💡 Settings persist...)
        note = QLabel("Settings persist via QSettings on app close.")
        note.setObjectName("dim")
        note.setWordWrap(True)
        self.add_widget(note)

    @staticmethod
    def _wrap_form(form):
        from PySide6.QtWidgets import QWidget
        w = QWidget()
        w.setLayout(form)
        return w
