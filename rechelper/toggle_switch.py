from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, QSize, Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QPushButton, QWidget

_FRAME_MARGIN = 3
# Different icon pairs (☀/🌙, 🔓/🔒...) have different glyph metrics, so
# sizing each button to its own sizeHint() gave the two slots mismatched
# widths and made the sliding highlight look uneven/misaligned depending on
# which pair was in use. A fixed size makes both slots always identical.
_BUTTON_SIZE = QSize(46, 32)


class ToggleSwitch(QWidget):
    """Two-icon segmented switch (e.g. sun/moon) — an explicit either/or
    pick rather than an unlabeled sliding knob, styled like the app's
    existing segmented pill nav. The active side is shown by a highlight
    that glides between the two icons instead of snapping.
    """

    toggled = Signal(bool)

    def __init__(self, icon_off: str = "☀", icon_on: str = "🌙", parent=None):
        super().__init__(parent)
        self._checked = False

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._frame = QFrame()
        self._frame.setObjectName("segmentIconPill")
        frame_layout = QHBoxLayout(self._frame)
        frame_layout.setContentsMargins(_FRAME_MARGIN, _FRAME_MARGIN, _FRAME_MARGIN, _FRAME_MARGIN)
        frame_layout.setSpacing(0)

        # a plain painted rect that glides behind whichever icon is active —
        # created before the buttons so it stays behind them in paint order
        self._thumb = QFrame(self._frame)
        self._thumb.setObjectName("segmentIconThumb")
        self._thumb.lower()

        self.off_button = QPushButton(icon_off)
        self.on_button = QPushButton(icon_on)
        for b in (self.off_button, self.on_button):
            b.setObjectName("segmentIconItem")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedSize(_BUTTON_SIZE)
            frame_layout.addWidget(b)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._group.addButton(self.off_button)
        self._group.addButton(self.on_button)

        self.off_button.clicked.connect(lambda: self._set_checked(False))
        self.on_button.clicked.connect(lambda: self._set_checked(True))

        self._anim = QPropertyAnimation(self._thumb, b"geometry", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self.off_button.setChecked(True)
        outer.addWidget(self._frame)
        # the fixed button size is known immediately, so the thumb lands
        # right on the first paint instead of depending on an actual layout
        # pass (which briefly reports stale geometry on first show)
        self._sync_thumb(animate=False)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        self._set_checked(checked, emit=False)

    def set_theme(self, palette: dict):
        # styling comes entirely from the global app stylesheet
        # (segmentIconPill/segmentIconItem/segmentIconThumb rules) —
        # nothing to repaint here.
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_thumb(animate=False)

    def _target_rect(self, checked: bool) -> QRect:
        x = _FRAME_MARGIN + (_BUTTON_SIZE.width() if checked else 0)
        # the buttons don't sit at a fixed y — when this row is taller than
        # its neighbours (e.g. a two-line subtitle stretches the row), the
        # parent layout centers the fixed-size buttons in the extra height,
        # so the thumb has to track that same centering, not just the
        # frame's top margin, or it ends up floating above the icon
        y = max(_FRAME_MARGIN, (self._frame.height() - _BUTTON_SIZE.height()) // 2)
        return QRect(x, y, _BUTTON_SIZE.width(), _BUTTON_SIZE.height())

    def _sync_thumb(self, animate: bool):
        target = self._target_rect(self._checked)
        if not animate:
            self._anim.stop()
            self._thumb.setGeometry(target)
            return
        self._anim.stop()
        self._anim.setStartValue(self._thumb.geometry())
        self._anim.setEndValue(target)
        self._anim.start()

    def _set_checked(self, checked: bool, emit: bool = True):
        changed = checked != self._checked
        self._checked = checked
        self.on_button.setChecked(checked)
        self.off_button.setChecked(not checked)
        self._sync_thumb(animate=True)
        if emit and changed:
            self.toggled.emit(checked)
