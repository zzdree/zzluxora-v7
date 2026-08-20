"""
Preview Tab — 2D top-down stage view of patched fixtures (Phase 10).

Layout: title + status row + (Canvas2D | XySidebar).
Polls artnet_controller.current_dmx every 200 ms and updates each
ParLed's DRGBW in real time. Drag a fixture to reposition; the right
sidebar shows X/Y spinboxes for the selected fixture.

Persists x/y on the fixture dict (`manager.fixtures[name]["x"|"y"]`).
"""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
)

from widgets.stage_view import Canvas2D, XySidebar


class PreviewTab(QWidget):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._selected_id: str | None = None
        self._canvas = Canvas2D(self)
        self._sidebar = XySidebar(self)
        self.setObjectName("panelContent")
        self._build_ui()
        self._wire()
        self._refresh_fixtures()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(200)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)

        title = QLabel("Live Preview")  # Phase 18: no emoji
        title.setObjectName("panelTitle")
        root.addWidget(title)
        sub = QLabel(
            "2D top-down stage. Drag fixtures to position them. "
            "X/Y sidebar updates live. Positions persist on save."
        )
        sub.setObjectName("panelDesc")
        sub.setWordWrap(True)
        root.addWidget(sub)

        self.status = QLabel("Disconnected — connect Art-Net in the Output tab")
        self.status.setStyleSheet("color: #707070;")
        root.addWidget(self.status)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._canvas, 1)
        body.addWidget(self._sidebar, 0)
        root.addLayout(body, 1)

    def _wire(self):
        self._canvas.fixture_selected.connect(self._on_selected)
        self._canvas.fixture_moved.connect(self._on_moved)
        self._sidebar.xy_changed.connect(self._on_xy_changed)
        self._sidebar.center_requested.connect(self._on_center)
        self._sidebar.reset_requested.connect(self._on_reset)

    # ── fixture population
    def _refresh_fixtures(self):
        self._canvas.clear()
        self._sidebar.clear()
        self._selected_id = None
        address_map = self.manager.get_address_map()
        # Dedupe by fixture_name (each fixture may occupy N addresses)
        seen: set[str] = set()
        fixtures_to_add: list[tuple[str, int, float, float]] = []
        for addr, info in address_map.items():
            name = info.get("fixture_name", "?")
            if name in seen:
                continue
            seen.add(name)
            start = info.get("start_address", addr)
            fx_data = info.get("fixture_data", {}) or {}
            x = float(fx_data.get("x", 0.5))
            y = float(fx_data.get("y", 0.5))
            fixtures_to_add.append((name, start, x, y))

        # Spread default positions on a 4-col grid if at default (0.5, 0.5)
        for idx, (name, start, x, y) in enumerate(fixtures_to_add):
            if x == 0.5 and y == 0.5:
                col = idx % 4
                row = idx // 4
                x = 0.15 + (col * 0.233)
                y = 0.20 + (row * 0.20)
            self._canvas.add_fixture(name, name, x, y)

    # ── DMX polling
    def _poll(self):
        if not hasattr(self.manager, "artnet_controller") or not self.manager.artnet_controller:
            return
        ctrl = self.manager.artnet_controller
        if not ctrl.is_running:
            self.status.setText("Disconnected")
            self.status.setStyleSheet("color: #707070;")
            for fid in self._canvas.fixture_ids():
                self._canvas.set_fixture_drgbw(fid, 0, 0, 0, 0, 0)
            return
        self.status.setText(
            f"● Connected — {ctrl.target_ip}:{ctrl.universe} @ {ctrl.fps}fps"
        )
        self.status.setStyleSheet("color: #2ecc71; font-weight: 700;")
        dmx = ctrl.current_dmx
        address_map = self.manager.get_address_map()
        # Aggregate DMX values per fixture name (max dimmer across channels)
        per_fix: dict[str, list[int]] = {}
        for addr, info in address_map.items():
            name = info.get("fixture_name", "?")
            if addr - 1 < len(dmx):
                per_fix.setdefault(name, [0, 0, 0, 0, 0])
                per_fix[name][0] = max(per_fix[name][0], dmx[addr - 1])
        for fid, vals in per_fix.items():
            self._canvas.set_fixture_drgbw(fid, *vals)

    # ── selection / movement
    def _on_selected(self, fixture_id: str) -> None:
        self._selected_id = fixture_id
        self._sync_sidebar()

    def _on_moved(self, fixture_id: str, x: float, y: float) -> None:
        self._persist_xy(fixture_id, x, y)
        if fixture_id == self._selected_id:
            self._sync_sidebar()

    def _on_xy_changed(self, fixture_id: str, x: float, y: float) -> None:
        led = self._canvas.get_led(fixture_id)
        if led:
            led.set_position(x, y)
        self._persist_xy(fixture_id, x, y)

    def _on_center(self, fixture_id: str) -> None:
        led = self._canvas.get_led(fixture_id)
        if led:
            led.set_position(0.5, 0.5)
            x, y = led.position()
            self._persist_xy(fixture_id, x, y)
            self._sync_sidebar()

    def _on_reset(self, fixture_id: str) -> None:
        # Reset to a default grid position based on fixture list order
        ids = self._canvas.fixture_ids()
        if fixture_id in ids:
            idx = ids.index(fixture_id)
            col = idx % 4
            row = idx // 4
            x = 0.15 + (col * 0.233)
            y = 0.20 + (row * 0.20)
            led = self._canvas.get_led(fixture_id)
            if led:
                led.set_position(x, y)
                self._persist_xy(fixture_id, x, y)
                self._sync_sidebar()

    def _sync_sidebar(self) -> None:
        if not self._selected_id:
            self._sidebar.clear()
            return
        led = self._canvas.get_led(self._selected_id)
        if not led:
            self._sidebar.clear()
            return
        x, y = led.position()
        address_map = self.manager.get_address_map()
        start = next(
            (info.get("start_address", 0)
             for info in address_map.values()
             if info.get("fixture_name") == self._selected_id),
            0,
        )
        self._sidebar.set_fixture(self._selected_id, self._selected_id, start, x, y)

    def _persist_xy(self, fixture_id: str, x: float, y: float) -> None:
        fx = self.manager.fixtures.get(fixture_id)
        if isinstance(fx, dict):
            fx["x"] = float(round(x, 4))
            fx["y"] = float(round(y, 4))

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_fixtures()
