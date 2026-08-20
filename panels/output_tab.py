"""
Output Tab — Phase 12 QLC+ style: scan panel + IP list + Save button only.
Connect / Disconnect / Blackout / Test / Live buttons moved to header.

v6.9 polish (Phase 12 #40): universe + FPS no longer editable in panel — shown
as read-only labels reading from `manager.artnet_controller`. Edit via config.ini
or via header Art-Net pill tooltip (see main_window.py).
"""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QGroupBox, QListWidget, QListWidgetItem,
)
from threading import Thread

from widgets.toast import show_toast


class ChannelPreviewGrid(QWidget):
    """8x64 grid showing current DMX channel values as red brightness."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = [0] * 512
        self.setMinimumHeight(100)
        self.setObjectName("channelPreviewGrid")
        self.setStyleSheet("background-color: #0a0a0a; border: 1px solid #2a2a2a;")

    def set_values(self, values):
        v = list(values[:512]) if values else []
        v += [0] * max(0, 512 - len(v))
        self.values = v
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cols, rows = 64, 8
        cell_w = w / cols
        cell_h = h / rows
        for i in range(512):
            r, c = i // cols, i % cols
            val = self.values[i]
            color = QColor(val, 0, 0) if val > 0 else QColor(15, 15, 15)
            painter.fillRect(
                int(c * cell_w), int(r * cell_h),
                max(1, int(cell_w) - 1), max(1, int(cell_h) - 1),
                color,
            )


class OutputTab(QWidget):
    """Phase 12: QLC+ style scan panel, save button only.

    - Pre-populated with localhost (127.0.0.1) and ESP32 (192.168.4.1)
    - Custom IP add field
    - Universe + FPS spinboxes inline
    - Connect / Blackout buttons moved to header (per feedback)
    - Single Save button (persists target_ip + universe + fps to config)
    """

    # Phase 12: signal when user selects an IP
    target_changed = Signal(str)  # emits new target IP

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setObjectName("panelContent")
        # Default nodes (always present, even before scan)
        self.nodes: list[dict] = [
            {'ip': '127.0.0.1', 'name': 'localhost'},
            {'ip': '192.168.4.1', 'name': 'ESP32 (default)'},
        ]
        self._build_ui()
        self._populate_list()
        self._select_default()
        # Status polling
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._refresh_status)
        self.status_timer.start(1000)
        # Auto-scan once on open (non-blocking)
        QTimer.singleShot(200, self._scan_async)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)

        title = QLabel("Art-Net DMX Output")  # Phase 18: no emoji
        title.setObjectName("panelTitle")
        root.addWidget(title)

        sub = QLabel(
            "Pick a node from the scan list (or add custom IP). "
            "Click Connect in the header to send DMX. Blackout in header."
        )
        sub.setObjectName("panelDesc")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # ── Scan panel
        scan_box = QGroupBox("Art-Net Nodes")  # Phase 18: no emoji
        scan_box.setObjectName("outputScanBox")
        scan_l = QVBoxLayout(scan_box)
        scan_l.setSpacing(6)

        scan_btn_row = QHBoxLayout()
        self.scan_btn = QPushButton("Scan Network")  # Phase 18: no emoji
        self.scan_btn.setObjectName("headerButton")
        self.scan_btn.clicked.connect(self._scan_async)
        scan_btn_row.addWidget(self.scan_btn)
        scan_btn_row.addStretch()
        scan_l.addLayout(scan_btn_row)

        self.node_list = QListWidget()
        self.node_list.setObjectName("outputNodeList")
        self.node_list.setMinimumHeight(140)
        self.node_list.currentItemChanged.connect(self._on_select)
        self.node_list.setStyleSheet("""
            QListWidget#outputNodeList {
                background-color: #141414; color: #e8e8e8; font-size: 12px;
                border: 1px solid #2a2a2a; border-radius: 4px;
            }
            QListWidget#outputNodeList::item { padding: 6px 10px; }
            QListWidget#outputNodeList::item:selected {
                background-color: #1f1f1f; color: #2ecc71;
                border-left: 3px solid #2ecc71;
            }
        """)
        scan_l.addWidget(self.node_list)

        custom_row = QHBoxLayout()
        self.custom_edit = QLineEdit()
        self.custom_edit.setObjectName("outputCustomIp")
        self.custom_edit.setPlaceholderText("Custom IP e.g. 10.0.0.50")
        self.custom_edit.setStyleSheet(
            "QLineEdit { background-color: #141414; color: #2ecc71; "
            "border: 1px solid #2a2a2a; padding: 4px; font-family: monospace; }"
        )
        custom_row.addWidget(self.custom_edit, 1)
        self.add_btn = QPushButton("Add")
        self.add_btn.setObjectName("headerButton")
        self.add_btn.clicked.connect(self._add_custom)
        custom_row.addWidget(self.add_btn)
        scan_l.addLayout(custom_row)

        root.addWidget(scan_box)

        # ── Selected node (PRD OUT-3: universe/FPS removed from panel;
        #    engine still uses config defaults universe 0 / fps 30)
        sel_box = QGroupBox("Selected Node")
        sel_box.setObjectName("outputSelBox")
        sel_l = QHBoxLayout(sel_box)

        sel_l.addWidget(QLabel("Target:"))
        self.target_label = QLabel("—")
        self.target_label.setObjectName("outputTargetLabel")
        self.target_label.setStyleSheet(
            "color: #2ecc71; font-family: monospace; font-weight: 700; min-width: 140px;"
        )
        sel_l.addWidget(self.target_label)
        sel_l.addStretch()
        root.addWidget(sel_box)

        # ── Status
        self.status = QLabel("● Disconnected")
        self.status.setObjectName("outputStatus")
        self.status.setStyleSheet("color: #707070; font-size: 12px; padding: 4px;")
        root.addWidget(self.status)

        # ── Save button (only button, per feedback)
        save_row = QHBoxLayout()
        save_row.addStretch()
        self.save_btn = QPushButton("Save Connection")  # Phase 18: no emoji
        self.save_btn.setObjectName("headerButton")
        self.save_btn.setProperty("class", "primaryBtn")
        self.save_btn.setToolTip("Persist IP/Universe/FPS to config.ini")
        self.save_btn.clicked.connect(self._save_connection)
        save_row.addWidget(self.save_btn)
        root.addLayout(save_row)

        # ── Channel preview
        preview_label = QLabel("Channel Preview (1-512)")
        preview_label.setObjectName("sectionTitle")
        root.addWidget(preview_label)
        self.channel_grid = ChannelPreviewGrid()
        root.addWidget(self.channel_grid)
        root.addStretch()

    # ── node list
    def _populate_list(self):
        self.node_list.clear()
        for n in self.nodes:
            label = f"{n['name']}  ({n['ip']})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, n['ip'])
            self.node_list.addItem(item)

    def _select_default(self):
        # Pre-select first node (localhost)
        if self.node_list.count() > 0:
            self.node_list.setCurrentRow(0)
            self._on_select(self.node_list.currentItem(), None)

    def _on_select(self, current, _previous):
        if not current:
            self.target_label.setText("—")
            return
        ip = current.data(Qt.ItemDataRole.UserRole)
        self.target_label.setText(ip)
        self.target_changed.emit(ip)

    def _add_custom(self):
        ip = self.custom_edit.text().strip()
        if not ip:
            return
        if any(n['ip'] == ip for n in self.nodes):
            self.custom_edit.clear()
            return
        self.nodes.append({'ip': ip, 'name': 'Custom'})
        self.node_list.addItem(f"Custom  ({ip})")
        self.custom_edit.clear()
        # Auto-select the newly added one
        self.node_list.setCurrentRow(self.node_list.count() - 1)

    # ── scan
    def _scan_async(self):
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Scanning…")  # Phase 18: no emoji

        def _run():
            results: list = []
            try:
                if hasattr(self.manager, 'artnet_controller') and self.manager.artnet_controller:
                    results = self.manager.artnet_controller.scan(timeout_s=2.0)
            except Exception:
                results = []
            QTimer.singleShot(0, lambda: self._apply_scan_results(results))

        Thread(target=_run, daemon=True).start()

    def _apply_scan_results(self, results):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("Scan Network")  # Phase 18: no emoji
        if not results:
            show_toast(self, "No Art-Net nodes found (using fallback list)", "info")
            return
        added = 0
        existing_ips = {n['ip'] for n in self.nodes}
        for r in results:
            if r['ip'] not in existing_ips:
                self.nodes.append(r)
                self.node_list.addItem(f"{r['name']}  ({r['ip']})")
                existing_ips.add(r['ip'])
                added += 1
        if added:
            show_toast(self, f"Found {added} new node(s)", "success")

    # ── save (v6.9: read universe/fps from manager state, not spinbox)
    def _save_connection(self):
        current = self.node_list.currentItem()
        if not current:
            show_toast(self, "Pick a target node first", "warning")
            return
        ip = current.data(Qt.ItemDataRole.UserRole)
        # v6.9: read universe + FPS from manager state
        uni = 0
        fps = 30
        if (hasattr(self.manager, 'artnet_controller')
                and self.manager.artnet_controller):
            uni = int(getattr(self.manager.artnet_controller, 'universe', 0))
            fps = int(getattr(self.manager.artnet_controller, 'fps', 30))
        from config import app_config
        cfg = app_config()
        cfg.set("ArtNet", "default_ip", ip)
        cfg.set("ArtNet", "default_universe", str(uni))
        cfg.set("ArtNet", "default_fps", str(fps))
        show_toast(self, f"Saved: {ip} uni {uni} @ {fps}fps", "success")

    # ── status (v6.9: read universe/FPS from manager, refresh labels)
    def _refresh_status(self):
        if not hasattr(self.manager, 'artnet_controller') or not self.manager.artnet_controller:
            return
        self.channel_grid.set_values(self.manager.artnet_controller.current_dmx)
        status = self.manager.artnet_controller.get_status()
        ctrl = self.manager.artnet_controller
        # Universe/FPS not shown in panel (PRD OUT-3); read for status line only
        uni = int(getattr(ctrl, 'universe', 0))
        fps = int(getattr(ctrl, 'fps', 30))
        if status.get('connected'):
            self.status.setText(
                f"● Connected — {status['target_ip']}:{uni} "
                f"@ {fps}fps | "
                f"frames sent: {status.get('frames_sent', 0)}"
            )
            self.status.setStyleSheet("color: #2ecc71;")
        else:
            self.status.setText("● Disconnected (click Connect in header)")
            self.status.setStyleSheet("color: #707070;")
