from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from . import settings
from .overlay_base import ModalOverlay
from .toggle_switch import ToggleSwitch


class SettingsOverlay(ModalOverlay):
    """An in-window settings panel — the rest of the app dims/blurs behind
    it instead of opening a separate OS window."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.settings_data = settings.load_settings()

        card = QFrame()
        card.setObjectName("modalCard")
        card.setFixedWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26, 24, 26, 22)
        card_layout.setSpacing(20)

        title = QLabel("⚙️  Paramètres")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        card_layout.addWidget(title)

        self.theme_switch = ToggleSwitch()
        card_layout.addLayout(self._setting_row("Basculer de thème", None, self.theme_switch))
        self.theme_switch.setChecked(main_window.palette.get("name") == "dark")
        self.theme_switch.toggled.connect(self.on_theme_toggled)

        self.lock_switch = ToggleSwitch(icon_off="🔓", icon_on="🔒")
        card_layout.addLayout(self._setting_row(
            "Auto Lock MKV",
            "Verrouiller l'écart MKV/MP4 dès l'ouverture de l'application",
            self.lock_switch,
        ))
        self.lock_switch.setChecked(bool(self.settings_data.get("auto_lock_mkv", True)))
        self.lock_switch.toggled.connect(self.on_lock_toggled)

        button_row = QHBoxLayout()
        button_row.addStretch()
        close_button = QPushButton("Fermer")
        close_button.setObjectName("pathButton")
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.close_overlay)
        button_row.addWidget(close_button)
        card_layout.addLayout(button_row)

        self.set_card(card)

    def _setting_row(self, title: str, subtitle: str | None, switch: ToggleSwitch) -> QHBoxLayout:
        row = QHBoxLayout()
        label_box = QVBoxLayout()
        label_box.setSpacing(2)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        label_box.addWidget(title_label)
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setObjectName("mutedText")
            sub_label.setStyleSheet("font-size: 12px;")
            sub_label.setWordWrap(True)
            label_box.addWidget(sub_label)
        row.addLayout(label_box, stretch=1)
        row.addWidget(switch)
        return row

    def on_theme_toggled(self, checked: bool):
        name = "dark" if checked else "light"
        self.settings_data["theme"] = name
        settings.save_settings(self.settings_data)
        self._main_window.apply_theme(name)
        self.set_theme(self._main_window.palette)

    def on_lock_toggled(self, checked: bool):
        self.settings_data["auto_lock_mkv"] = checked
        settings.save_settings(self.settings_data)
