from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QPushButton, QWidget


class ToggleSwitch(QWidget):
    """Two-icon segmented switch (e.g. sun/moon) — an explicit either/or
    pick rather than an unlabeled sliding knob, styled like the app's
    existing segmented pill nav so the active side is clearly highlighted.
    """

    toggled = Signal(bool)

    def __init__(self, icon_off: str = "☀", icon_on: str = "🌙", parent=None):
        super().__init__(parent)
        self._checked = False

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        frame = QFrame()
        frame.setObjectName("segmentIconPill")
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(3, 3, 3, 3)
        frame_layout.setSpacing(0)

        self.off_button = QPushButton(icon_off)
        self.on_button = QPushButton(icon_on)
        for b in (self.off_button, self.on_button):
            b.setObjectName("segmentIconItem")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            frame_layout.addWidget(b)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._group.addButton(self.off_button)
        self._group.addButton(self.on_button)

        self.off_button.clicked.connect(lambda: self._set_checked(False))
        self.on_button.clicked.connect(lambda: self._set_checked(True))

        self._apply_active_state()
        outer.addWidget(frame)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        self._set_checked(checked, emit=False)

    def set_theme(self, palette: dict):
        # styling comes entirely from the global app stylesheet
        # (segmentIconPill/segmentIconItem rules) — nothing to repaint here.
        pass

    def _set_checked(self, checked: bool, emit: bool = True):
        changed = checked != self._checked
        self._checked = checked
        self._apply_active_state()
        if emit and changed:
            self.toggled.emit(checked)

    def _apply_active_state(self):
        self.on_button.setChecked(self._checked)
        self.off_button.setChecked(not self._checked)
        self.on_button.setProperty("active", "true" if self._checked else "false")
        self.off_button.setProperty("active", "false" if self._checked else "true")
        for b in (self.on_button, self.off_button):
            b.style().unpolish(b)
            b.style().polish(b)
