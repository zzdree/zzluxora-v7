"""
Sidebar — collapsible navigation list, v5.0.

Structure:
  QFrame (Sidebar)
    ├── QPushButton  collapse_btn  (☰ /  ›  toggle)
    └── QListWidget  list_widget   (panels, icons + labels)

The wrapper is a QWidget (not QListWidget) so it can own the collapse button
without polluting the QListWidget item API. Callers proxy to list_widget
via the public `setCurrentRow` / `currentRow` / `panel_changed` shims.
"""
from PySide6.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPolygon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
    QStyledItemDelegate, QStyle, QStyleOptionViewItem, QVBoxLayout,
)

from icons import sidebar_icon


# (key, label) — Phase 13: dropped "Fixture List" (converted to dropdown)
# Phase 18: dropped "Color" (4 items now, per feedback #9)
SIDEBAR_ITEMS = [
    ("program",         "Program"),
    ("fixture_list",    "Fixture List"),
    ("fixture_editor",  "Fixture Editor"),
    ("settings",        "Settings"),
    ("about",           "About"),
]

# Phase 14: active row marker (green triangle at left edge)
class _ActiveItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        super().paint(painter, option, index)
        if option.state & QStyle.StateFlag.State_Selected:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor("#2ecc71"))
            painter.setPen(Qt.PenStyle.NoPen)
            r = option.rect
            poly = QPolygon([
                r.topLeft(),
                r.bottomLeft(),
                QPoint(r.left() + 6, r.center().y())
            ])
            painter.drawPolygon(poly)
            painter.restore()

EXPANDED_WIDTH = 200
COLLAPSED_WIDTH = 48  # v6.9: was 56, slimmer for icon-only feel
ANIM_MS = 200


class Sidebar(QFrame):
    """Collapsible navigation panel."""

    panel_changed = Signal(str)        # forwarded from list_widget
    collapsed_changed = Signal(bool)   # emitted on toggle

    def __init__(self, parent=None, collapsed: bool = False):
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self._collapsed = collapsed
        self._build_ui()
        self._apply_width(animated=False)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── collapse toggle row
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 4, 0, 4)
        header_row.setSpacing(0)
        self.collapse_btn = QPushButton("☰")
        self.collapse_btn.setObjectName("sidebarCollapseBtn")
        self.collapse_btn.setToolTip("Toggle sidebar")
        self.collapse_btn.clicked.connect(self.toggle)
        header_row.addWidget(self.collapse_btn)
        header_row.addStretch()
        layout.addLayout(header_row)

        # ── panel list
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("sidebar")
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        for key, label in SIDEBAR_ITEMS:
            item = QListWidgetItem(sidebar_icon(key, 18), f"  {label}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setSizeHint(item.sizeHint().expandedTo(item.sizeHint() * 1.2))
            self.list_widget.addItem(item)

        self.list_widget.setCurrentRow(0)
        self.list_widget.currentItemChanged.connect(self._on_list_change)

        # Phase 14: custom delegate paints a green triangle marker on the active row
        self.list_widget.setItemDelegate(_ActiveItemDelegate(self.list_widget))

        layout.addWidget(self.list_widget, 1)

    # ── public API (back-compat with old QListWidget usage)
    def setCurrentRow(self, row: int) -> None:  # noqa: N802 (Qt casing)
        self.list_widget.setCurrentRow(row)

    def currentRow(self) -> int:  # noqa: N802
        return self.list_widget.currentRow()

    # ── collapse
    def toggle(self) -> None:
        self._collapsed = not self._collapsed
        self._apply_width(animated=True)
        self.collapsed_changed.emit(self._collapsed)

    def set_collapsed(self, collapsed: bool, animated: bool = False) -> None:
        if collapsed == self._collapsed:
            return
        self._collapsed = collapsed
        self._apply_width(animated=animated)
        self.collapsed_changed.emit(self._collapsed)

    def is_collapsed(self) -> bool:
        return self._collapsed

    def _apply_width(self, animated: bool) -> None:
        target = COLLAPSED_WIDTH if self._collapsed else EXPANDED_WIDTH
        # v6: hamburger always ☰ (no flip to ›) — user feedback
        self.collapse_btn.setText("☰")
        # v6.9 Phase 14 #22: auto-hide text labels when collapsed (icon-only mode)
        self._toggle_item_text(self._collapsed)

        if not animated:
            self.setFixedWidth(target)
            return

        anim = QPropertyAnimation(self, b"minimumWidth")
        anim.setDuration(ANIM_MS)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(self.width())
        anim.setEndValue(target)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        # Also animate maximumWidth in parallel
        anim_max = QPropertyAnimation(self, b"maximumWidth")
        anim_max.setDuration(ANIM_MS)
        anim_max.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_max.setStartValue(self.width())
        anim_max.setEndValue(target)
        anim_max.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        # Keep references alive
        self._anim_min, self._anim_max = anim, anim_max
        # Final size set at end of animation
        anim.finished.connect(lambda: self.setMinimumWidth(0))  # free the min

    # ── internal
    def _on_list_change(self, current, _previous) -> None:
        if current:
            key = current.data(Qt.ItemDataRole.UserRole)
            self.panel_changed.emit(key)

    def _toggle_item_text(self, hide: bool) -> None:
        """v6.9 Phase 14 #22: hide/restore item text labels (icon-only when collapsed)."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item:
                continue
            key = item.data(Qt.ItemDataRole.UserRole)
            label = next((lbl for k, lbl in SIDEBAR_ITEMS if k == key), "")
            if hide:
                item.setText("")
                # Add tooltip so icon-only items still show their name on hover
                item.setToolTip(label)
            else:
                item.setText(f"  {label}")
                item.setToolTip("")
