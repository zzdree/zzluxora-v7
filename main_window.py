"""
MainWindow — QMainWindow with header bar (v6), sidebar, stacked panels, statusbar.

v6 layout (top → bottom):
  HeaderBar (48px) — brand | project | Art-Net pill | Start | Stop
  ──────────────────────────────────────────────────────────────
  Sidebar (200/56 px) | Panel stack
  ──────────────────────────────────────────────────────────────
  Statusbar (24px)

Branding: lowercase "zzluxora" (v6 — was ZZLIGHT-LUXORA in v5).
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel, QFileDialog,
    QMessageBox
)
from sidebar import Sidebar, SIDEBAR_ITEMS
from styles import DARK_QSS
from fixture_manager import FixtureManager
from panels.about_panel import AboutPanel
from panels.program_panel import ProgramPanel
from panels.fixture_list_panel import FixtureListPanel
from panels.fixture_editor_panel import FixtureEditorPanel
from panels.settings_panel import SettingsPanel
from panels import project_io
from panels.audio_tab import AudioTab
from widgets.toast import show_toast
from widgets.help_modal import HelpDialog
from widgets.empty_state import EmptyState
from widgets.header_bar import HeaderBar
from panels.output_tab import OutputTab
from config import app_config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("zzluxora")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 680)
        self.setStyleSheet(DARK_QSS)

        # Shared state
        self.manager = FixtureManager()

        # App config (v5 — config.ini)
        self.cfg = app_config()

        # Panel registry (filled in _build_central)
        self.panels: dict = {}

        # Phase 12: Art-Net target state (IP selected in Output tab)
        self._artnet_target_ip: str = self.cfg.artnet_default_ip
        self._artnet_universe: int = self.cfg.artnet_default_universe
        self._artnet_fps: int = self.cfg.artnet_default_fps

        self._build_menubar()
        self._build_central()
        self._build_statusbar()

    # ─────────────────────────────────────
    # Menubar (File / View / Help)
    # ─────────────────────────────────────
    def _build_menubar(self):
        bar = self.menuBar()

        file_menu = bar.addMenu("&File")

        act_open = QAction("Open Project…", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self._open_project)
        file_menu.addAction(act_open)

        act_save = QAction("Save Project", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self._save_project)
        file_menu.addAction(act_save)

        act_save_as = QAction("Save Project As…", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(self._save_project_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()
        # v6: Exit tanpa shortcut (sesuai spec user)
        act_quit = QAction("Exit", self)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        view_menu = bar.addMenu("&View")
        for idx, (key, label) in enumerate(SIDEBAR_ITEMS):
            act = QAction(label, self)
            act.setShortcut(QKeySequence(f"Ctrl+{idx + 1}"))
            act.triggered.connect(lambda _checked=False, k=key: self._show_panel(k))
            view_menu.addAction(act)

        help_menu = bar.addMenu("&Help")
        # Phase 9: renamed from "About" to "Shortcuts" per feedback
        act_shortcuts = QAction("Shortcuts", self)
        act_shortcuts.setShortcut(QKeySequence("F1"))
        act_shortcuts.triggered.connect(self._show_help)
        help_menu.addAction(act_shortcuts)

    # ─────────────────────────────────────
    # Central: header + sidebar + stacked panels
    # ─────────────────────────────────────
    def _build_central(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header bar (v5 — replaces toolbar)
        self.header = HeaderBar(project_name=self.manager.project_name or "Untitled.zlx")
        # Phase 9: single toggle signal (replaces start_clicked / stop_clicked)
        self.header.play_toggled.connect(self._on_header_play_toggled)
        # Phase 12: Connect + Blackout buttons in header
        self.header.connect_clicked.connect(self._on_header_connect)
        self.header.blackout_clicked.connect(self._blackout)
        self.header.fixture_dropdown_clicked.connect(self._on_fixture_dropdown)
        self.header.brand_clicked.connect(lambda: self._show_panel("about"))
        self.header.artnet_pill_clicked.connect(self._show_output_tab)
        # Seed tooltip with current path (if a project was auto-loaded)
        if self.manager.project_filepath:
            self.header.set_tooltip(self.manager.project_filepath)
        outer.addWidget(self.header)

        # ── Body: sidebar + panel stack
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = Sidebar(collapsed=self.cfg.sidebar_collapsed)
        self.sidebar.panel_changed.connect(self._show_panel)
        self.sidebar.collapsed_changed.connect(self._on_sidebar_collapsed)
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("panelContainer")

        # Phase 13: fixture_list is NOT a panel (dropdown service, not in stack)
        # Phase 18: Color panel removed from sidebar (4 items: program, fixture_editor, settings, about)
        self.panels["program"] = ProgramPanel(self.manager)
        self.panels["fixture_editor"] = FixtureEditorPanel(self.manager)
        self.panels["settings"] = SettingsPanel()
        self.panels["about"] = AboutPanel()
        # Service instance for the header dropdown popup
        self.fixture_list_panel = FixtureListPanel(self.manager)

        for key, _ in SIDEBAR_ITEMS:
            if key == "fixture_list":
                continue  # FIX 6: not a panel — triggers dropdown popup
            self.stack.addWidget(self.panels[key])

        # Wire editor save → list + address grid refresh
        self.panels["fixture_editor"].fixture_saved.connect(self._on_fixture_saved)

        # Wire audio tab export_to_scene signal
        program = self.panels["program"]
        if hasattr(program, "tabs"):
            for i in range(program.tabs.count()):
                tab = program.tabs.widget(i)
                if isinstance(tab, AudioTab):
                    tab.export_to_scene.connect(self._on_export_to_scene)
                    break

        # Phase 12: Wire output tab target_changed → main state
        if hasattr(program, "tabs"):
            for i in range(program.tabs.count()):
                tab = program.tabs.widget(i)
                if isinstance(tab, OutputTab):
                    tab.target_changed.connect(self._on_artnet_target_changed)
                    # Seed initial target from config
                    tab.target_changed.emit(self._artnet_target_ip)
                    break

        # Phase 14: faded empty state instead of onboarding overlay
        if not self.manager.fixtures:
            self._empty_state = EmptyState(self)
            self._empty_state.open_clicked.connect(self._open_project)
            self.stack.addWidget(self._empty_state)
            self.stack.setCurrentWidget(self._empty_state)
            self._no_project_mode = True
        else:
            self._no_project_mode = False

        body.addWidget(self.stack, 1)
        outer.addLayout(body, 1)
        self.setCentralWidget(central)

        # Global shortcuts (Space/B/Esc)
        self._wire_shortcuts()

    # ─────────────────────────────────────
    # Statusbar
    # ─────────────────────────────────────
    def _build_statusbar(self):
        sb = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color:#2ecc71;font-weight:600;")
        sb.addWidget(self.status_label)

        sep = QLabel("  |  ")
        sep.setStyleSheet("color:#2a2a2a;")
        sb.addWidget(sep)

        n = len(self.manager.list_fixtures())
        self.fixture_count_label = QLabel(f"{n} fixtures in library")
        sb.addPermanentWidget(self.fixture_count_label)
        sb.addPermanentWidget(QLabel("  zzluxora v7.0  |  PySide6"))

    # ─────────────────────────────────────
    # Slots
    # ─────────────────────────────────────
    def _on_header_start(self):
        """Open Output tab so user can click Connect (used by play toggle)."""
        self._show_output_tab()

    def _on_header_stop(self):
        """Blackout (used by play toggle + Stop shortcut)."""
        self._blackout()

    def _on_header_play_toggled(self, playing: bool) -> None:
        """Phase 9: single toggle handler. playing=True means user wants to start."""
        if playing:
            self._on_header_start()
        else:
            self._on_header_stop()

    def _on_fixture_dropdown(self) -> None:
        """Phase 13: open the Fixtures dropdown popup anchored to the header button."""
        if hasattr(self, "fixture_list_panel"):
            self.fixture_list_panel.popup(self.header.fixtures_btn)

    def _on_header_connect(self) -> None:
        """Phase 12: header Connect button — toggle connect/disconnect using _artnet_target_ip."""
        if not hasattr(self.manager, 'artnet_controller') or not self.manager.artnet_controller:
            show_toast(self, "No artnet controller", "error")
            return
        ctrl = self.manager.artnet_controller
        if ctrl.is_running:
            ctrl.disconnect()
            self.header.set_connected(False)
            self.header.set_artnet_state("disconnected")
            show_toast(self, "Disconnected", "info")
            self.statusBar().showMessage("Disconnected", 3000)
            return
        result = ctrl.connect(
            self._artnet_target_ip, self._artnet_universe, self._artnet_fps
        )
        if result.get('ok'):
            ctrl.reset_counter()
            self.header.set_connected(True, self._artnet_target_ip)
            self.header.set_artnet_state("connected")
            show_toast(
                self,
                f"Connected → {self._artnet_target_ip}:{self._artnet_universe} @ {self._artnet_fps}fps",
                "success",
            )
            self.statusBar().showMessage(
                f"Connected {self._artnet_target_ip}", 5000
            )
        else:
            self.header.set_connected(False)
            self.header.set_artnet_state("disconnected")
            show_toast(
                self, f"Connect failed: {result.get('error', 'unknown')}", "error"
            )

    def _on_artnet_target_changed(self, ip: str) -> None:
        """Phase 12: Output tab IP selection → main state. v6.9: universe/fps come from manager."""
        self._artnet_target_ip = ip
        # v6.9: universe + fps are managed by artnet_controller; pull from there
        if (hasattr(self.manager, 'artnet_controller')
                and self.manager.artnet_controller):
            ctrl = self.manager.artnet_controller
            self._artnet_universe = int(getattr(ctrl, 'universe', self._artnet_universe))
            self._artnet_fps = int(getattr(ctrl, 'fps', self._artnet_fps))
        # Update header pill tooltip with current connection settings
        self.header.setToolTip(
            f"{self._artnet_target_ip}:{self._artnet_universe} @ {self._artnet_fps}fps"
        )

    def _on_sidebar_collapsed(self, collapsed: bool) -> None:
        self.cfg.sidebar_collapsed = collapsed

    def _on_export_to_scene(self) -> None:
        self._show_panel("program")
        program = self.panels.get("program")
        if program and hasattr(program, "tabs"):
            for i in range(program.tabs.count()):
                if "scenes" in program.tabs.tabText(i).lower():
                    program.tabs.setCurrentIndex(i)
                    break
        show_toast(self, "Scenes ready", "success")

    def _on_fixture_saved(self):
        # Phase 13: fixture_list is a service (popup), not a panel
        if hasattr(self, "fixture_list_panel"):
            self.fixture_list_panel.refresh_data()
        program = self.panels["program"]
        if hasattr(program, "tabs"):
            for i in range(program.tabs.count()):
                tab = program.tabs.widget(i)
                if hasattr(tab, "_refresh"):
                    tab._refresh()
        self.statusBar().showMessage("Fixture saved", 3000)

    def _show_panel(self, key: str):
        # FIX 6: fixture_list is a sidebar item that triggers a dropdown popup,
        # NOT a stacked panel. Intercept it before index math.
        if key == "fixture_list":
            row = next((i for i, (k, _) in enumerate(SIDEBAR_ITEMS) if k == key), 0)
            if self.sidebar.currentRow() != row:
                self.sidebar.setCurrentRow(row)
            self.fixture_list_panel.popup(self.sidebar.list_widget)
            return

        # Build index mapping: panel_key → stack widget position
        # (SIDEBAR_ITEMS has 5 entries, but only 4 have panels in the stack)
        panel_keys = [k for k, _ in SIDEBAR_ITEMS if k != "fixture_list"]
        try:
            idx = panel_keys.index(key)
        except ValueError:
            return
        self.stack.setCurrentIndex(idx)
        self.status_label.setText(key.replace("_", " ").title())
        sidebar_row = next((i for i, (k, _) in enumerate(SIDEBAR_ITEMS) if k == key), 0)
        if self.sidebar.currentRow() != sidebar_row:
            self.sidebar.setCurrentRow(sidebar_row)
        n = len(self.manager.list_fixtures())
        p = len({info["start_address"]
                 for info in self.manager.get_address_map().values()})
        self.fixture_count_label.setText(
            f"{n} fixtures · {p} patched"
        )

    # ─────────────────────────────────────
    # Project I/O + shortcuts + helpers
    # ─────────────────────────────────────
    def _wire_shortcuts(self):
        sc_space = QShortcut(QKeySequence("Space"), self)
        sc_space.activated.connect(self._toggle_chase)
        sc_b = QShortcut(QKeySequence("B"), self)
        sc_b.activated.connect(self._blackout)
        sc_esc = QShortcut(QKeySequence("Esc"), self)
        sc_esc.activated.connect(self._emergency_stop)

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open zzluxora Project", "", "zzluxora Project (*.zlx)"
        )
        if not path:
            return
        if project_io.load_project(self.manager, path):
            self._refresh_all_panels()
            self.header.set_project_name(self.manager.project_name)
            # Phase 9: surface full path as hover tooltip on project label
            self.header.set_tooltip(self.manager.project_filepath or path)
            show_toast(self, f"Loaded {self.manager.project_name}", "success")
            self.statusBar().showMessage(f"Loaded {path}", 5000)
        else:
            show_toast(self, "Load failed — check file format", "error")

    def _save_project(self) -> bool:
        if not self.manager.project_filepath:
            return self._save_project_as()
        if project_io.save_project(self.manager, self.manager.project_filepath):
            self.header.set_project_name(self.manager.project_name)
            # Phase 9: keep tooltip in sync with current path
            self.header.set_tooltip(self.manager.project_filepath)
            show_toast(self, f"Saved {self.manager.project_name}", "success")
            self.statusBar().showMessage("Saved", 3000)
            return True
        show_toast(self, "Save failed", "error")
        return False

    def _save_project_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As",
            self.manager.project_name, "zzluxora Project (*.zlx)"
        )
        if not path:
            return False
        if not path.endswith(".zlx"):
            path += ".zlx"
        if project_io.save_project(self.manager, path):
            self.header.set_project_name(self.manager.project_name)
            # Phase 9: surface new path as tooltip
            self.header.set_tooltip(self.manager.project_filepath or path)
            show_toast(self, f"Saved {self.manager.project_name}", "success")
            return True
        show_toast(self, "Save failed", "error")
        return False

    def _show_output_tab(self):
        self._show_panel("program")
        program = self.panels.get("program")
        if program and hasattr(program, "tabs"):
            for i in range(program.tabs.count()):
                if "output" in program.tabs.tabText(i).lower():
                    program.tabs.setCurrentIndex(i)
                    break

    def _toggle_chase(self):
        if not self.manager.artnet_controller:
            return
        if self.manager.artnet_controller.is_playing:
            self.manager.artnet_controller.stop_chase()
            # Phase 9: keep header play button in sync with chase state
            self.header.set_playing(False)
            show_toast(self, "Chase stopped", "info")
            self.statusBar().showMessage("Chase stopped", 3000)
        else:
            program = self.panels.get("program")
            if program and hasattr(program, "tabs"):
                for i in range(program.tabs.count()):
                    tab = program.tabs.widget(i)
                    if hasattr(tab, "_play"):
                        tab._play()
                        # Phase 9: reflect chase playing in header toggle
                        self.header.set_playing(True)
                        self.statusBar().showMessage("Chase playing\u2026", 0)
                        return
            show_toast(self, "No chase to play", "warning")

    def _blackout(self):
        if self.manager.artnet_controller:
            self.manager.artnet_controller.blackout()
        show_toast(self, "Blackout", "warning")
        self.statusBar().showMessage("Blackout", 3000)
        self.header.set_artnet_state("disconnected")
        # Phase 9: sync header play toggle
        self.header.set_playing(False)

    def _emergency_stop(self):
        if self.manager.artnet_controller:
            self.manager.artnet_controller.stop_chase()
            if self.manager.artnet_controller.is_running:
                self.manager.artnet_controller.blackout()
        show_toast(self, "EMERGENCY STOP", "error")
        self.statusBar().showMessage("Emergency stop activated", 3000)
        self.header.set_artnet_state("disconnected")
        # Phase 9: sync header play toggle
        self.header.set_playing(False)

    def _show_help(self):
        dlg = HelpDialog(self)
        dlg.exec()

    def closeEvent(self, event):
        """Phase 8 — confirm before quit if Art-Net still connected."""
        if (self.manager.artnet_controller
                and self.manager.artnet_controller.is_running):
            reply = QMessageBox.question(
                self, "Disconnect Art-Net?",
                "Art-Net is still connected. Disconnect and quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.manager.artnet_controller.stop_chase()
            if self.manager.artnet_controller.is_running:
                self.manager.artnet_controller.blackout()
                self.manager.artnet_controller.disconnect()
        event.accept()

    def _refresh_all_panels(self):
        for key, panel in self.panels.items():
            if hasattr(panel, "refresh"):
                panel.refresh()
            elif hasattr(panel, "_refresh"):
                panel._refresh()
            if hasattr(panel, "tabs"):
                for i in range(panel.tabs.count()):
                    tab = panel.tabs.widget(i)
                    if hasattr(tab, "_refresh"):
                        tab._refresh()
                    if hasattr(tab, "_refresh_fixtures"):
                        tab._refresh_fixtures()
