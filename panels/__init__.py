"""Panel base class + registry."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class BasePanel(QWidget):
    """
    Base class for all sidebar panels.
    Subclasses must call _build_ui() in __init__.
    """
    PANEL_NAME = "Base"
    PANEL_DESC = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panelContent")
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(20, 20, 20, 20)
        self._root.setSpacing(8)
        self._build_ui()

    def _build_ui(self):
        # Default header
        title = QLabel(self.PANEL_NAME)
        title.setObjectName("panelTitle")
        self._root.addWidget(title)

        if self.PANEL_DESC:
            desc = QLabel(self.PANEL_DESC)
            desc.setObjectName("panelDesc")
            desc.setWordWrap(True)
            self._root.addWidget(desc)

        self._root.addStretch()

    def add_widget(self, widget):
        """Add a custom widget above the stretch."""
        self._root.insertWidget(self._root.count() - 1, widget)
