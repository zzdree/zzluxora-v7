"""
About panel — full author/project info, native Qt version of the
v2.1 webview About panel. All academic details preserved.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from panels import BasePanel


APP_VERSION = "7.0.0"  # v7: installer release


class AboutPanel(BasePanel):
    PANEL_NAME = "About"  # v6: no emoji (clean)
    PANEL_DESC = "Application information and academic context."  # v6: removed "bug"-worded desc

    def _build_ui(self):
        # FIX 5: BasePanel.__init__ already injected QLabel("About") + desc
        # into self._root. Clear it so only our card content appears.
        while self._root.count():
            item = self._root.takeAt(0)
            if (w := item.widget()):
                w.deleteLater()

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)

        # ─── Card ───
        card = QWidget()
        card.setObjectName("aboutCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(10)

        # Logo block (gradient header)
        logo_box = QWidget()
        logo_box.setObjectName("aboutLogo")
        logo_layout = QVBoxLayout(logo_box)
        logo_layout.setContentsMargins(16, 20, 16, 20)
        logo_layout.setSpacing(2)

        logo_text = QLabel("zzluxora")
        logo_text.setObjectName("aboutLogoText")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_text)

        version = QLabel(f"v{APP_VERSION}  •  Audio-Reactive Lighting Design System")
        version.setObjectName("aboutVersion")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(version)

        card_layout.addWidget(logo_box)

        # ─── Divider ───
        div1 = QFrame()
        div1.setObjectName("aboutDivider")
        div1.setFrameShape(QFrame.Shape.HLine)
        card_layout.addWidget(div1)

        # ─── Info rows ───
        def row(label, value):
            h = QHBoxLayout()
            h.setSpacing(12)
            l = QLabel(label)
            l.setObjectName("aboutLabel")
            l.setMinimumWidth(110)
            h.addWidget(l)
            v = QLabel(value)
            v.setObjectName("aboutValue")
            v.setWordWrap(True)
            h.addWidget(v, 1)
            return h

        # v6: ordered prodi → jurusan → fakultas → universitas (sesuai spec)
        card_layout.addLayout(row("Application", "zzluxora"))
        card_layout.addLayout(row("Description", "Audio-Reactive Lighting Design System"))
        card_layout.addLayout(row("Author", "Andreas Restuawanta Christwara"))
        card_layout.addLayout(row("NIM", "5312422036"))
        card_layout.addLayout(row("Program Studi", "Teknik Komputer"))
        card_layout.addLayout(row("Jurusan", "Teknik Elektro"))
        card_layout.addLayout(row("Fakultas", "Fakultas Teknik"))
        card_layout.addLayout(row("Universitas", "Universitas Negeri Semarang (UNNES)"))

        # ─── Divider ───
        div2 = QFrame()
        div2.setObjectName("aboutDivider")
        div2.setFrameShape(QFrame.Shape.HLine)
        card_layout.addWidget(div2)

        # ─── Thesis ───
        thesis_label = QLabel("JUDUL SKRIPSI")
        thesis_label.setObjectName("aboutLabel")
        card_layout.addWidget(thesis_label)

        thesis_text = QLabel(
            "\"Implementasi Rule-Based Audio Feature Mapping untuk "
            "Sistem Lighting Design RGBW Otomatis dengan Protokol Art-Net DMX512\""
        )
        thesis_text.setObjectName("aboutThesis")
        thesis_text.setWordWrap(True)
        card_layout.addWidget(thesis_text)

        # ─── Divider ───
        div3 = QFrame()
        div3.setObjectName("aboutDivider")
        div3.setFrameShape(QFrame.Shape.HLine)
        card_layout.addWidget(div3)

        # ─── Copyright ───
        cr = QLabel("© 2024 Andreas Restuawanta Christwara  |  Built with PySide6")
        cr.setObjectName("aboutCopyright")
        cr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(cr)

        card_layout.addStretch()

        outer.addWidget(card)
        self.layout().addLayout(outer)
        self.layout().addStretch()
