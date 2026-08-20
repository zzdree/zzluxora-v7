"""
QSS stylesheet - zzluxora v6 dark theme (skripsi-final).
Mirrors the v2.1 webview design tokens:
  --bg-1: #0d0d0d  (root)
  --bg-2: #141414  (panels)
  --bg-3: #1a1a1a  (cards)
  --bg-4: #1f1f1f  (hover)
  --border: #2a2a2a
  --text: #e8e8e8
  --text-3: #707070
  --green: #2ecc71  (accent)
  --red: #e74c3c

v6 additions:
  - QSplashScreen background
  - EmptyState widget
  - QMdiArea / sub-window styling
  - aboutLogoBox: black background (was green in v5)
"""

DARK_QSS = """
* {
    font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
}

QMainWindow, QWidget#centralWidget {
    background-color: #0d0d0d;
    color: #e8e8e8;
}

/* ─── Menubar ─── */
QMenuBar {
    background-color: #141414;
    color: #e8e8e8;
    border-bottom: 1px solid #2a2a2a;
    padding: 4px 8px;
    font-size: 12px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background: #1f1f1f;
}
QMenu {
    background-color: #1a1a1a;
    border: 1px solid #2a2a2a;
    color: #e8e8e8;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #2ecc71;
    color: #0d0d0d;
}
QMenu::separator {
    height: 1px;
    background: #2a2a2a;
    margin: 4px 8px;
}

/* ─── Toolbar ─── */
QToolBar {
    background-color: #141414;
    border-bottom: 1px solid #2a2a2a;
    spacing: 4px;
    padding: 4px 8px;
}
QToolButton {
    background: transparent;
    color: #e8e8e8;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 600;
}
QToolButton:hover {
    background: #1f1f1f;
    border-color: #2ecc71;
}
QToolButton:pressed {
    background: #2ecc71;
    color: #0d0d0d;
}

/* ─── Statusbar ─── */
QStatusBar {
    background-color: #141414;
    border-top: 1px solid #2a2a2a;
    color: #707070;
    font-size: 11px;
    padding: 2px 8px;
}
QStatusBar::item {
    border: none;
}

/* ─── Sidebar ─── */
QListWidget#sidebar {
    background-color: #141414;
    border: none;
    border-right: 1px solid #2a2a2a;
    outline: 0;
    padding: 8px 0;
    font-size: 12px;
}
QListWidget#sidebar::item {
    color: #b0b0b0;
    padding: 10px 14px;
    border-left: 3px solid transparent;
    border-radius: 0;
}
QListWidget#sidebar::item:hover {
    background-color: #1f1f1f;
    color: #e8e8e8;
}
QListWidget#sidebar::item:selected {
    background-color: #1a1a1a;
    color: #2ecc71;
    border-left: 3px solid #2ecc71;
}

/* ─── Panels ─── */
QWidget#panelContainer {
    background-color: #0d0d0d;
}
QWidget#panelContent {
    background-color: #0d0d0d;
}
QLabel#panelTitle {
    color: #e8e8e8;
    font-size: 18px;
    font-weight: 700;
    padding: 0 0 4px 0;
}
QLabel#panelDesc {
    color: #707070;
    font-size: 12px;
    padding: 0 0 16px 0;
}
QLabel#sectionTitle {
    color: #e8e8e8;
    font-size: 13px;
    font-weight: 700;
    padding: 8px 0 4px 0;
}
QLabel.dim, QLabel#dim {
    color: #707070;
    font-size: 11px;
}

/* ─── Cards (About rows) ─── */
QWidget#aboutCard {
    background-color: #141414;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
}
QWidget#aboutLogo {
    background-color: #0d0d0d;  /* v6: pure black (was green gradient in v5) */
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 24px;
}
QLabel#aboutLogoText {
    color: #ffffff;  /* v6: white brand (was #0d0d0d on green in v5) */
    font-size: 26px;
    font-weight: 900;
    font-style: italic;
    letter-spacing: 3px;
}
QLabel#aboutVersion {
    color: #707070;
    font-size: 11px;
    font-weight: 600;
    padding-top: 4px;
}
QLabel#aboutLabel {
    color: #707070;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QLabel#aboutValue {
    color: #e8e8e8;
    font-size: 12px;
    font-weight: 500;
}
QFrame#aboutDivider {
    background-color: #2a2a2a;
    max-height: 1px;
    min-height: 1px;
}
QLabel#aboutThesis {
    color: #b0b0b0;
    font-size: 12px;
    font-style: italic;
    line-height: 1.5;
    padding: 8px 0;
}
QLabel#aboutCopyright {
    color: #707070;
    font-size: 10px;
    padding-top: 8px;
}

/* ─── Scrollbars ─── */
QScrollBar:vertical {
    background: #0d0d0d;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #2a2a2a;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #2ecc71;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ─── Misc ─── */
QPushButton {
    background-color: #1a1a1a;
    color: #e8e8e8;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton:hover {
    border-color: #2ecc71;
    color: #2ecc71;
}
QPushButton:pressed {
    background-color: #2ecc71;
    color: #0d0d0d;
}

/* ─── QTabWidget (Program panel sub-tabs) ─── */
QTabWidget#programTabs::pane {
    border: 1px solid #2a2a2a;
    background: #0d0d0d;
    border-radius: 0 0 4px 4px;
    top: -1px;
}
QTabBar {
    background: transparent;
}
QTabBar::tab {
    background: #141414;
    color: #b0b0b0;
    padding: 8px 18px;
    border: 1px solid #2a2a2a;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
    font-size: 12px;
    font-weight: 600;
}
QTabBar::tab:hover:!selected {
    background: #1f1f1f;
    color: #e8e8e8;
}
QTabBar::tab:selected {
    background: #2ecc71;
    color: #0d0d0d;
    font-weight: 700;
}
QTabBar::tab:!selected {
    margin-top: 2px;
}

/* ─── Header (used by QHeaderView sections) ─── */
/* ─── Header bar (v5) ─── */
QFrame#headerBar {
    background-color: #141414;
    border-bottom: 1px solid #2a2a2a;
    min-height: 48px;
    max-height: 48px;
}
QFrame#headerBar QLabel {
    color: #e8e8e8;
    font-size: 12px;
}
/* v6: brandTitle now uses white per design spec (was green in v5).
   Gradient is painted in paintEvent using QLinearGradient. */
QLabel#brandTitle {
    color: #ffffff;
    font-size: 20px;
    font-weight: 900;
    font-style: italic;
    letter-spacing: 1.5px;
    padding: 0 16px;
}

/* ─── v6: Empty State ─── */
QWidget#emptyState {
    background-color: #0d0d0d;
}

/* ─── v6: Splash Screen ─── */
QSplashScreen {
    background-color: #000000;
    color: #ffffff;
    border: 1px solid #1a1a1a;
}

/* ─── v6: MDI Sub-window (Program panel multi-document) ─── */
QMdiSubWindow {
    background-color: #141414;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
}
QMdiSubWindow > QWidget {
    background-color: #141414;
}
QMdiArea {
    background-color: #0d0d0d;
}
QScrollArea#mdiScroll {
    background-color: #0d0d0d;
    border: none;
}
QFrame#artnetPill {
    background-color: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    padding: 4px 10px;
    max-height: 28px;
}
QLabel#artnetDot {
    min-width: 10px;
    max-width: 10px;
    min-height: 10px;
    max-height: 10px;
    border-radius: 5px;
    background-color: #707070;
    margin-right: 8px;
}
QLabel#artnetDot[state="connected"]    { background-color: #2ecc71; }
QLabel#artnetDot[state="disconnected"] { background-color: #e74c3c; }
QLabel#artnetDot[state="connecting"]   { background-color: #4aa3ff; }
QLabel#artnetText                     { color: #b0b0b0; font-weight: 600; font-size: 11px; }
QLabel#artnetText[state="connected"]    { color: #2ecc71; }
QLabel#artnetText[state="disconnected"] { color: #e74c3c; }
QLabel#artnetText[state="connecting"]   { color: #4aa3ff; }
QPushButton#headerButton {
    background-color: transparent;
    color: #e8e8e8;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
    min-height: 28px;
}
QPushButton#headerButton:hover { border-color: #2ecc71; color: #2ecc71; }
QPushButton#headerButton:pressed { background-color: #2ecc71; color: #0d0d0d; }
QPushButton#headerButton#startBtn { border-color: #2ecc71; color: #2ecc71; }
QPushButton#headerButton#startBtn:hover { background-color: #2ecc71; color: #0d0d0d; }
QPushButton#headerButton#stopBtn { border-color: #e74c3c; color: #e74c3c; }
QPushButton#headerButton#stopBtn:hover { background-color: #e74c3c; color: #0d0d0d; }
QPushButton#sidebarCollapseBtn {
    background: transparent;
    border: none;
    color: #b0b0b0;
    font-size: 16px;
    padding: 8px;
    min-width: 32px;
    min-height: 32px;
}
QPushButton#sidebarCollapseBtn:hover { color: #2ecc71; }

/* ─── Sidebar collapse variants (v5) ─── */
QListWidget#sidebarCollapsed {
    background-color: #141414;
    border: none;
    border-right: 1px solid #2a2a2a;
    outline: 0;
    padding: 4px 0;
}
QListWidget#sidebarCollapsed::item {
    color: #b0b0b0;
    padding: 10px 14px;
    border-left: 3px solid transparent;
    border-radius: 0;
    text-align: center;
}
QListWidget#sidebarCollapsed::item:hover { background-color: #1f1f1f; color: #e8e8e8; }
QListWidget#sidebarCollapsed::item:selected { background-color: #1a1a1a; color: #2ecc71; border-left: 3px solid #2ecc71; }

/* ─── Analyze progress bar (v5) ─── */
QProgressBar#analyzeProgress {
    background-color: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    text-align: center;
    color: #e8e8e8;
    font-size: 10px;
    min-height: 16px;
    max-height: 16px;
}
QProgressBar#analyzeProgress::chunk {
    background-color: #2ecc71;
    border-radius: 3px;
}
"""
