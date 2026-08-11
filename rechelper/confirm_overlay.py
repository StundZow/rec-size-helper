from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .overlay_base import ModalOverlay


class ConfirmOverlay(ModalOverlay):
    """In-window Yes/No confirmation — used instead of QMessageBox so
    destructive prompts match the rest of the app instead of looking like
    a plain Windows dialog."""

    def __init__(
        self,
        main_window,
        title: str,
        message: str,
        on_confirm: Callable[[], None],
        confirm_text: str = "Confirmer",
        cancel_text: str = "Annuler",
        icon: str = "⚠️",
        danger: bool = True,
    ):
        super().__init__(main_window)
        self._on_confirm = on_confirm

        card = QFrame()
        card.setObjectName("modalCard")
        card.setFixedWidth(460)
        root = QVBoxLayout(card)
        root.setContentsMargins(26, 24, 26, 22)
        root.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(14)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        header.addWidget(icon_label)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 17px; font-weight: 700;")
        title_label.setWordWrap(True)
        header.addWidget(title_label, stretch=1)
        root.addLayout(header)

        msg_frame = QFrame()
        msg_frame.setObjectName("card")
        msg_layout = QVBoxLayout(msg_frame)
        msg_layout.setContentsMargins(20, 16, 20, 16)
        msg_label = QLabel(message)
        msg_label.setTextFormat(Qt.RichText)
        msg_label.setWordWrap(True)
        msg_label.setObjectName("mutedText")
        msg_layout.addWidget(msg_label)
        root.addWidget(msg_frame)

        button_row = QHBoxLayout()
        button_row.addStretch()
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setObjectName("pathButton")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.close_overlay)
        button_row.addWidget(cancel_btn)

        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setObjectName("deleteButton" if danger else "updateButton")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.clicked.connect(self._confirm_and_close)
        button_row.addWidget(confirm_btn)
        root.addLayout(button_row)

        self.set_card(card)

    def _confirm_and_close(self):
        self._on_confirm()
        self.close_overlay()
