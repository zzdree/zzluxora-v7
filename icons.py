"""
Icon helper — render a glyph into a QIcon.

DESIGN.md §5.3 forbids pictographic emoji in chrome. Sidebar icons use
non-emoji geometric/technical Unicode glyphs (monochrome, render consistently
across OS) instead of the old colour emoji.
"""
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont, QPainter, QColor


def make_glyph_icon(glyph: str, size: int = 18, color: str = "#e8e8e8") -> QIcon:
    """Render a glyph string into a QIcon of the given pixel size."""
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    font = QFont("Segoe UI Symbol", int(size * 0.75))
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, glyph)
    painter.end()

    return QIcon(pixmap)


# Sidebar icon set — DESIGN.md §5.3/§5.4: geometric glyphs, no colour emoji.
# Keys match SIDEBAR_ITEMS in sidebar.py (program/fixture_editor/settings/about).
SIDEBAR_ICONS = {
    "program":        "▦",   # console grid
    "fixture_list":   "⋮",   # vertical dots / list dropdown
    "fixture_editor": "▤",   # rows / channel table
    "settings":       "⚙",   # gear (mono Symbol glyph, not the emoji variant)
    "about":          "ⓘ",   # info
}


def sidebar_icon(key: str, size: int = 18) -> QIcon:
    return make_glyph_icon(SIDEBAR_ICONS.get(key, "•"), size=size)
