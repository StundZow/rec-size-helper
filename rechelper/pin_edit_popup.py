from __future__ import annotations

import ctypes

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from .overlay_base import ModalOverlay

_VK_LWIN = 0x5B
_VK_OEM_PERIOD = 0xBE
_KEYEVENTF_KEYUP = 0x0002


def _open_windows_emoji_panel():
    """Simulates Win+. — the OS-native emoji picker types straight into
    whichever text field currently has focus, so no custom picker needed."""
    user32 = ctypes.windll.user32
    user32.keybd_event(_VK_LWIN, 0, 0, 0)
    user32.keybd_event(_VK_OEM_PERIOD, 0, 0, 0)
    user32.keybd_event(_VK_OEM_PERIOD, 0, _KEYEVENTF_KEYUP, 0)
    user32.keybd_event(_VK_LWIN, 0, _KEYEVENTF_KEYUP, 0)


class _EmojiLineEdit(QLineEdit):
    """A QLineEdit that opens the Windows emoji panel whenever it's clicked.

    Selects all existing text first so the panel's insertion (which types
    like a keystroke) replaces the old emoji instead of appending to it —
    this field only ever holds one icon at a time.
    """

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.selectAll()
        _open_windows_emoji_panel()


class PinEditOverlay(ModalOverlay):
    """In-window popup for editing a pinned folder's display name/icon/path
    and reordering it.

    This used to be a Qt.Popup floating window, but Qt.Popup auto-closes
    the instant it loses OS focus/activation — which happens the moment the
    Windows emoji panel opens, or the moment QFileDialog opens, breaking
    both. An in-window overlay isn't a real top-level window, so neither
    can knock it out.
    """

    saved = Signal(str, str, str)  # name, icon, path
    move_left_requested = Signal()
    move_right_requested = Signal()

    def __init__(self, main_window, name: str, path: str, icon: str, is_first: bool, is_last: bool):
        super().__init__(main_window)
        self.current_path = path

        card = QFrame()
        card.setObjectName("modalCard")
        card.setFixedWidth(340)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        left_btn = QPushButton("◀")
        left_btn.setObjectName("iconButton")
        left_btn.setFixedSize(32, 32)
        left_btn.setCursor(Qt.PointingHandCursor)
        left_btn.setEnabled(not is_first)
        left_btn.clicked.connect(self._on_move_left)
        top_row.addWidget(left_btn)
        top_row.addStretch()

        confirm_btn = QPushButton("✓")
        confirm_btn.setObjectName("pinConfirmButton")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.clicked.connect(self._on_confirm)
        top_row.addWidget(confirm_btn)
        top_row.addStretch()

        right_btn = QPushButton("▶")
        right_btn.setObjectName("iconButton")
        right_btn.setFixedSize(32, 32)
        right_btn.setCursor(Qt.PointingHandCursor)
        right_btn.setEnabled(not is_last)
        right_btn.clicked.connect(self._on_move_right)
        top_row.addWidget(right_btn)
        layout.addLayout(top_row)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.icon_edit = _EmojiLineEdit(icon)
        self.icon_edit.setObjectName("pinIconEdit")
        self.icon_edit.setFixedWidth(44)
        self.icon_edit.setMaxLength(4)
        self.icon_edit.setAlignment(Qt.AlignCenter)
        self.icon_edit.setToolTip("Cliquer pour ouvrir la galerie d'émojis")
        bottom_row.addWidget(self.icon_edit)

        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("Nom affiché")
        self.name_edit.setToolTip(path)
        self.name_edit.returnPressed.connect(self._on_confirm)
        bottom_row.addWidget(self.name_edit, stretch=1)

        change_path_btn = QPushButton("⋯")
        change_path_btn.setObjectName("iconButton")
        change_path_btn.setFixedSize(30, 30)
        change_path_btn.setCursor(Qt.PointingHandCursor)
        change_path_btn.setToolTip("Changer le dossier lié à ce raccourci")
        change_path_btn.clicked.connect(self._on_change_path)
        bottom_row.addWidget(change_path_btn)

        layout.addLayout(bottom_row)
        self.set_card(card)

        self.name_edit.setFocus()
        self.name_edit.selectAll()

    def _on_move_left(self):
        self.move_left_requested.emit()
        self.close_overlay()

    def _on_move_right(self):
        self.move_right_requested.emit()
        self.close_overlay()

    def _on_change_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir le dossier", self.current_path)
        if folder:
            self.current_path = folder
            self.name_edit.setToolTip(folder)

    def _on_confirm(self):
        name = self.name_edit.text().strip() or self.name_edit.placeholderText()
        icon = self.icon_edit.text().strip() or "📁"
        self.saved.emit(name, icon, self.current_path)
        self.close_overlay()
