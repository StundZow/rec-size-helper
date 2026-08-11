from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from . import settings, theme
from .resources import ICON_PATH
from .toggle_switch import ToggleSwitch


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setFixedWidth(420)
        self.setModal(True)

        self.settings_data = settings.load_settings()
        palette = getattr(parent, "palette", None)
        if not isinstance(palette, dict):
            palette = theme.get_palette(theme.detect_windows_theme())

        # plain flat background (the QDialog{background-color} rule in the
        # global stylesheet already matches the current theme) — no glass
        # blobs needed for a small utility window like this one.
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 22)
        root.setSpacing(20)

        title = QLabel("⚙️  Paramètres")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        root.addWidget(title)

        self.theme_switch = ToggleSwitch()
        root.addLayout(self._setting_row(
            "Basculer de thème",
            None,
            self.theme_switch,
        ))
        self.theme_switch.set_theme(palette)
        self.theme_switch.setChecked(palette.get("name") == "dark")
        self.theme_switch.toggled.connect(self.on_theme_toggled)

        self.lock_switch = ToggleSwitch(icon_off="🔓", icon_on="🔒")
        root.addLayout(self._setting_row(
            "Auto Lock MKV",
            "Verrouiller l'écart MKV/MP4 dès l'ouverture de l'application",
            self.lock_switch,
        ))
        self.lock_switch.set_theme(palette)
        self.lock_switch.setChecked(bool(self.settings_data.get("auto_lock_mkv", True)))
        self.lock_switch.toggled.connect(self.on_lock_toggled)

        root.addStretch()

        button_row = QHBoxLayout()
        button_row.addStretch()
        close_button = QPushButton("Fermer")
        close_button.setObjectName("pathButton")
        close_button.clicked.connect(self.accept)
        button_row.addWidget(close_button)
        root.addLayout(button_row)

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
        parent = self.parent()
        if parent is not None and hasattr(parent, "apply_theme"):
            parent.apply_theme(name)
            palette = parent.palette
            self.theme_switch.set_theme(palette)
            self.lock_switch.set_theme(palette)

    def on_lock_toggled(self, checked: bool):
        self.settings_data["auto_lock_mkv"] = checked
        settings.save_settings(self.settings_data)
