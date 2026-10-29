from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from .overlay_base import ModalOverlay
from .widgets import button, note, panel_header


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
        icon: str = "trash",
        danger: bool = True,
    ):
        super().__init__(main_window)
        self._on_confirm = on_confirm

        card = QFrame()
        card.setObjectName("modalCard")
        card.setFixedWidth(470)
        root = QVBoxLayout(card)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(16)

        root.addLayout(panel_header(title, None, icon, "f_pink" if danger else "f_violet"))
        root.addWidget(note(message))

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(button(cancel_text, on_click=self.close_overlay))
        confirm_btn = button(confirm_text, icon, "destructive" if danger else "primary", self._confirm_and_close)
        button_row.addWidget(confirm_btn)
        root.addLayout(button_row)

        self.set_card(card)

    def _confirm_and_close(self):
        self._on_confirm()
        self.close_overlay()
