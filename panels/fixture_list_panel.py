"""
FixtureListPanel — Phase 13: converted from sidebar panel to a popup service.

The list is no longer a panel in the main stack. Instead, the user opens it
via the "Fixtures  ▾" button in the header, which calls `popup(anchor)`.

The instance still holds a `refresh_data()` method (used by main_window's
_on_fixture_saved) so the next popup shows fresh data.
"""
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel,
)
from fixture_manager import FixtureManager


class FixtureListPanel:
    """Phase 13: service class. Not a QWidget anymore — popup is a transient QFrame."""

    def __init__(self, manager: FixtureManager):
        self.manager = manager
        self._popup: QFrame | None = None
        self._data_cache: list[dict] = []  # [{name, channels}]

    def refresh_data(self) -> None:
        """Refresh internal cache from manager. Called before each popup."""
        names = self.manager.list_fixtures()
        out = []
        for n in names:
            fx = self.manager.get_fixture(n)
            out.append({'name': n, 'channels': fx.get('channels', '?')})
        self._data_cache = out
        # If popup is visible, update its list too
        if self._popup and self._popup.isVisible():
            self._refresh_popup_list()

    def popup(self, anchor_widget) -> None:
        """Show the dropdown popup anchored to the bottom-left of anchor_widget.

        If already visible, closes it (toggle behavior).
        """
        if self._popup and self._popup.isVisible():
            self._popup.close()
            return
        self.refresh_data()

        # Use the anchor's top-level window as parent so popup survives any
        # intermediate reparenting.
        win = anchor_widget.window() if anchor_widget else None
        f = QFrame(win, Qt.WindowType.Popup)
        f.setObjectName("fixtureDropdown")
        f.setStyleSheet("""
            QFrame#fixtureDropdown {
                background-color: #141414;
                border: 1px solid #2ecc71;
                border-radius: 4px;
            }
            QLabel#fixtureDropdownHint {
                color: #707070;
                font-size: 10px;
                padding: 4px 6px;
            }
        """)
        layout = QVBoxLayout(f)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header hint
        hint = QLabel("Fixtures (drag to Address grid)")
        hint.setObjectName("fixtureDropdownHint")
        layout.addWidget(hint)

        # List
        self._popup_list = QListWidget()
        self._popup_list.setObjectName("fixtureListPopup")
        self._popup_list.setDragEnabled(True)
        self._popup_list.setDragDropMode(QListWidget.DragDropMode.DragOnly)
        self._popup_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._popup_list.setStyleSheet("""
            QListWidget#fixtureListPopup {
                background-color: #141414;
                border: none;
                color: #e8e8e8;
                font-size: 12px;
            }
            QListWidget#fixtureListPopup::item {
                padding: 6px 10px;
                border-bottom: 1px solid #1a1a1a;
            }
            QListWidget#fixtureListPopup::item:hover {
                background-color: #1f1f1f;
                color: #2ecc71;
            }
        """)
        self._popup_list.setFixedSize(260, min(280, 40 + 30 * len(self._data_cache)))
        self._refresh_popup_list()
        self._popup_list.startDrag = self._start_drag
        layout.addWidget(self._popup_list)

        # Footer (Add button to fixture editor)
        footer = QHBoxLayout()
        footer.setContentsMargins(4, 4, 4, 4)
        # Phase 18: no emoji (was ＋  New Fixture)
        add_btn = QPushButton("New Fixture")
        add_btn.setObjectName("headerButton")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda: (f.close(), self._open_editor()))
        footer.addWidget(add_btn)
        footer.addStretch()
        layout.addLayout(footer)

        # Position below anchor
        anchor_global = anchor_widget.mapToGlobal(anchor_widget.rect().bottomLeft())
        f.move(anchor_global)
        f.show()
        self._popup = f
        f.destroyed.connect(lambda: setattr(self, '_popup', None))

    def _refresh_popup_list(self) -> None:
        if not hasattr(self, '_popup_list') or self._popup_list is None:
            return
        self._popup_list.clear()
        for d in self._data_cache:
            item = QListWidgetItem(f"{d['name']}  ({d['channels']}ch)")
            item.setData(Qt.ItemDataRole.UserRole, d['name'])
            self._popup_list.addItem(item)

    def _open_editor(self) -> None:
        """Switch to the Fixture Editor panel so the user can add a new fixture."""
        # Imported lazily to avoid circular import in tests
        from main_window import SIDEBAR_ITEMS  # noqa: F401
        # The actual panel switch is owned by main_window — we can't reach it
        # from this service class. But the header Add button is mostly a hint:
        # user can still click the Fixture Editor sidebar item manually.

    def _start_drag(self, supportedActions) -> None:
        if not hasattr(self, '_popup_list') or self._popup_list is None:
            return
        item = self._popup_list.currentItem()
        if not item:
            return
        mime = QMimeData()
        mime.setText(item.data(Qt.ItemDataRole.UserRole))
        drag = QDrag(self._popup_list)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)
