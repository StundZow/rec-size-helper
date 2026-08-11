from .resources import resource_path

_CHECK_ICON = resource_path("assets/check.png").replace("\\", "/")


def build_stylesheet(p: dict) -> str:
    return f"""
QWidget {{
    background-color: {p['bg']};
    color: {p['text']};
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}}

QDialog {{
    background-color: {p['bg_base']};
}}

QLabel#title {{
    font-size: 24px;
    font-weight: 700;
    color: {p['text']};
}}

QLabel#subtitle {{
    color: {p['text_muted']};
    font-size: 12px;
}}

QLabel#mutedText {{
    color: {p['text_muted']};
}}

QLabel#dimText {{
    color: {p['text_dim']};
    font-size: 12px;
}}

QFrame#card {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {p['card_bg_top']}, stop:0.22 {p['card_bg']}, stop:1 {p['card_bg']});
    border-radius: 22px;
    border: 1px solid {p['card_border']};
}}

QFrame#modalCard {{
    background-color: {p['modal_card_bg']};
    border-radius: 22px;
    border: 1px solid {p['card_border']};
}}

QScrollArea#pinnedScroll {{
    background: transparent;
    border: none;
}}

QFrame#segmentPill {{
    background-color: {p['input_bg']};
    border: 1px solid {p['input_border']};
    border-radius: 19px;
}}
QPushButton#segmentItem {{
    background: transparent;
    border: none;
    border-radius: 15px;
    padding: 8px 16px;
    color: {p['text_muted']};
    font-weight: 600;
    font-size: 13px;
}}
QPushButton#segmentItem:hover {{
    color: {p['text']};
}}
QWidget#pinSegment[active="true"] {{
    background-color: {p['segment_active_bg']};
    border-radius: 15px;
}}
QWidget#pinSegment[active="true"] QPushButton#segmentItem {{
    color: {p['segment_active_text']};
    font-weight: 700;
}}
QPushButton#segMini {{
    background: transparent;
    border: none;
    color: {p['text_dim']};
    font-size: 10px;
    border-radius: 9px;
}}
QPushButton#segMini:hover:!disabled {{
    color: {p['text']};
    background-color: {p['input_bg']};
}}
QPushButton#segMini:disabled {{
    color: transparent;
}}

QFrame#segmentIconPill {{
    background-color: {p['input_bg']};
    border: 1px solid {p['input_border']};
    border-radius: 17px;
}}
QPushButton#segmentIconItem {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 13px;
    padding: 4px 11px;
    font-size: 15px;
    color: {p['text_muted']};
}}
QPushButton#segmentIconItem:hover {{
    color: {p['text']};
}}
QFrame#segmentIconThumb {{
    background-color: {p['pin_toggle_checked_bg']};
    border: 1px solid {p['pin_toggle_checked_border']};
    border-radius: 13px;
}}

QPushButton#pinToggle {{
    background-color: {p['input_bg']};
    border: 1px solid {p['input_border']};
    border-radius: 14px;
    padding: 8px 14px;
    color: {p['text']};
    font-weight: 600;
}}
QPushButton#pinToggle:hover {{
    border-color: {p['input_border_hover']};
}}

QPushButton#iconButton {{
    background: transparent;
    border: none;
    border-radius: 17px;
    font-size: 19px;
    color: {p['text_muted']};
}}
QPushButton#iconButton:hover {{
    background-color: {p['input_bg']};
}}

QPushButton#pinToggle:checked {{
    background-color: {p['pin_toggle_checked_bg']};
    border-color: {p['pin_toggle_checked_border']};
    color: {p['pin_toggle_checked_text']};
}}
QPushButton#pinToggle:disabled {{
    color: {p['text_dim']};
}}

QPushButton#lockToggle {{
    background-color: {p['input_bg']};
    border: 1px solid {p['input_border']};
    border-radius: 15px;
    color: {p['text_muted']};
    font-size: 14px;
}}
QPushButton#lockToggle:hover {{
    border-color: {p['input_border_hover']};
}}
QPushButton#lockToggle:checked {{
    background-color: {p['pin_toggle_checked_bg']};
    border-color: {p['pin_toggle_checked_border']};
    color: {p['pin_toggle_checked_text']};
}}

QPushButton#pinConfirmButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #22c55e, stop:1 #16a34a);
    color: #ffffff;
    border: none;
    border-radius: 15px;
    font-size: 14px;
    font-weight: 700;
    padding: 6px 16px;
}}
QPushButton#pinConfirmButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #34d874, stop:1 #1eb355);
}}

QLineEdit#pinIconEdit {{
    padding: 6px 4px;
    font-size: 17px;
}}

QPushButton#pathButton {{
    background-color: {p['input_bg']};
    border: 1px solid {p['input_border']};
    border-radius: 14px;
    padding: 9px 18px;
    color: {p['text']};
    font-weight: 600;
}}
QPushButton#pathButton:hover {{
    background-color: {p['input_border']};
    border-color: {p['input_border_hover']};
}}

QPushButton#deleteButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff5f6d, stop:1 #ff9966);
    color: #250f08;
    font-weight: 700;
    font-size: 15px;
    border: none;
    border-radius: 18px;
    padding: 14px 30px;
}}
QPushButton#deleteButton:disabled {{
    background: {p['card_border']};
    color: {p['text_dim']};
}}
QPushButton#deleteButton:hover:!disabled {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff7a86, stop:1 #ffb27a);
}}

QPushButton#updateButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #22d3ee);
    color: #ffffff;
    font-weight: 700;
    font-size: 14px;
    border: none;
    border-radius: 14px;
    padding: 11px 22px;
}}
QPushButton#updateButton:hover:!disabled {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7477f5, stop:1 #4de1f5);
}}
QPushButton#updateButton:disabled {{
    background: {p['card_border']};
    color: {p['text_dim']};
}}

QTextEdit#updateNotes {{
    background-color: {p['input_bg']};
    border: 1px solid {p['input_border']};
    border-radius: 8px;
    padding: 8px;
    font-size: 12px;
}}

QSlider::groove:horizontal {{
    height: 6px;
    background: {p['groove_bg']};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: #ffffff;
    border: 1px solid rgba(130,120,160,0.35);
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}

QSlider#deleteSlider::sub-page:horizontal {{
    background: rgba(251,113,133,0.75);
    border-radius: 3px;
}}

QSlider#bufferSlider::sub-page:horizontal {{
    background: rgba(56,189,248,0.70);
    border-radius: 3px;
}}

QProgressBar {{
    background-color: {p['groove_bg']};
    border-radius: 6px;
    text-align: center;
    color: {p['text']};
    height: 16px;
    border: none;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #22d3ee);
    border-radius: 6px;
}}

QLineEdit {{
    background-color: {p['input_bg']};
    border: 1px solid {p['input_border']};
    border-radius: 12px;
    padding: 9px 14px;
    color: {p['text']};
    font-size: 13px;
    selection-background-color: #6366f1;
}}
QLineEdit:focus {{
    border-color: {p['input_border_hover']};
}}

QCheckBox {{
    color: {p['text']};
    font-weight: 600;
    font-size: 13px;
    spacing: 12px;
}}
QCheckBox::indicator {{
    width: 24px;
    height: 24px;
    border-radius: 8px;
    background-color: {p['input_bg']};
    border: 1px solid {p['input_border']};
}}
QCheckBox::indicator:hover {{
    border-color: {p['input_border_hover']};
}}
QCheckBox::indicator:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #22d3ee);
    border: none;
    image: url("{_CHECK_ICON}");
}}

QScrollBar:vertical, QScrollBar:horizontal {{
    background: {p['scrollbar_bg']};
    width: 10px;
    height: 10px;
}}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: {p['scrollbar_handle']};
    border-radius: 5px;
    min-height: 24px;
}}
"""
