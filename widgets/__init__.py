"""
AddressGrid — 22 rows × 24 cols = 528 DMX cells (Phase 17: 24 horizontal density).
Cells 1-512 are active; cells 513-528 are greyed-out "out of range" placeholders.
Cells are color-coded when patched, hover-highlight on empty.
Emits address_clicked(int) when a cell is clicked.
Phase 17: position number rendered in the top-right corner of patched cells.
"""
from PySide6.QtCore import Qt, Signal, QRect, QSize
from PySide6.QtGui import QColor, QBrush, QFont, QPainter
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QStyledItemDelegate, QStyleOptionViewItem,
)


# Phase 17: 24 columns (was 32). 22 rows to cover 512 channels (24*22=528).
COLS = 24
ROWS = 22
DMX_MAX = 512


class _PositionCornerDelegate(QStyledItemDelegate):
    """FIX 2: paint address number in top-right corner for ALL cells.

    Dual-mode:
      - Empty cell (text == address): subtle muted address number
      - Patched cell (text != address): bold position badge (existing behavior)

    Reads Qt.ItemDataRole.UserRole+1 set by _populate_empty() or paint_cell().
    """

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        super().paint(painter, option, index)
        addr = index.row() * COLS + index.column() + 1
        if addr > DMX_MAX:
            return  # skip out-of-range placeholders
        pos = index.data(Qt.ItemDataRole.UserRole + 1)
        if pos is None:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        rect = option.rect

        # Detect: empty cell (text == str(addr)) vs patched cell (text = label)
        item_text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        is_empty = (item_text == str(addr))

        if is_empty:
            # Empty cell: address number in top-right corner, subtle/muted
            text = str(addr)
            font = QFont("Segoe UI", 6)
            painter.setFont(font)
            painter.setPen(QColor("#505050"))
        else:
            # Patched cell: fixture start position badge (white on dark)
            text = str(pos)
            font = QFont("Segoe UI", 6, QFont.Weight.Bold)
            painter.setFont(font)
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(text) + 4
            th = fm.height()
            pad = 2
            bg = QRect(rect.right() - tw - pad, rect.top() + pad, tw, th)
            painter.fillRect(bg, QColor(0, 0, 0, 160))
            painter.setPen(QColor("#ffffff"))

        # Draw at top-right corner
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text) + 4
        th = fm.height()
        pad = 2
        text_rect = QRect(rect.right() - tw - pad, rect.top() + pad, tw, th)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()


class AddressGrid(QTableWidget):
    address_clicked = Signal(int)  # 1-based DMX address
    fixture_dropped = Signal(str, int)  # fixture_name, address

    def __init__(self, parent=None):
        super().__init__(ROWS, COLS, parent)
        self.setObjectName("addressGrid")

        # Layout — Phase 17: smaller cells for 24-col density
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(22)
        self.horizontalHeader().setDefaultSectionSize(22)
        self.setShowGrid(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAcceptDrops(True)

        # Default style
        self.setStyleSheet("""
            QTableWidget#addressGrid {
                background-color: #0d0d0d;
                gridline-color: #2a2a2a;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
            }
            QTableWidget#addressGrid::item {
                color: #707070;
                font-size: 7px;
            }
            QTableWidget#addressGrid::item:selected {
                background-color: #2ecc71;
                color: #0d0d0d;
            }
        """)

        # Make cells drop targets
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)

        # Phase 17: install delegate that paints position corner
        self.setItemDelegate(_PositionCornerDelegate(self))

        # Populate empty labels
        self._populate_empty()

        # Click → emit address
        self.cellClicked.connect(self._on_cell_clicked)

    def _populate_empty(self):
        font = QFont("Segoe UI", 7)
        for row in range(ROWS):
            for col in range(COLS):
                addr = row * COLS + col + 1
                item = QTableWidgetItem(str(addr) if addr <= DMX_MAX else "—")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFont(font)
                if addr > DMX_MAX:
                    # Out-of-range: dark grey
                    item.setForeground(QBrush(QColor("#2a2a2a")))
                    item.setBackground(QBrush(QColor("#0a0a0a")))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                else:
                    item.setForeground(QBrush(QColor("#404040")))
                    item.setBackground(QBrush(QColor("#0d0d0d")))
                    # FIX 2: stash address so delegate can render corner number
                    item.setData(Qt.ItemDataRole.UserRole + 1, addr)
                self.setItem(row, col, item)

    def paint_cell(self, address: int, label: str, color: QColor, position: int = 0):
        """Color a patched cell with a channel label.

        Phase 17: `position` is the start address of the fixture, shown in the
        top-right corner of the cell (and all sibling cells of the same fixture).
        """
        if address < 1 or address > DMX_MAX:
            return
        row, col = divmod(address - 1, COLS)
        item = self.item(row, col)
        if not item:
            return
        item.setText(label[:3])
        item.setBackground(QBrush(color))
        item.setForeground(QBrush(QColor("#0d0d0d")))
        font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        item.setFont(font)
        # Phase 17: stash position for the corner delegate
        item.setData(Qt.ItemDataRole.UserRole + 1, position)

    def clear_paint(self):
        """Reset all cells to default."""
        self._populate_empty()

    def _on_cell_clicked(self, row: int, col: int):
        addr = row * COLS + col + 1
        if addr > DMX_MAX:
            return  # ignore clicks on out-of-range placeholders
        self.address_clicked.emit(addr)

    # ─────────────────────────────────────
    # Drag & drop
    # ─────────────────────────────────────
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not event.mimeData().hasText():
            return
        fixture_name = event.mimeData().text()
        index = self.indexAt(event.pos())
        if not index.isValid():
            return
        row, col = index.row(), index.column()
        addr = row * COLS + col + 1
        if addr > DMX_MAX:
            return  # can't drop on out-of-range cells
        self.fixture_dropped.emit(fixture_name, addr)
        event.acceptProposedAction()
