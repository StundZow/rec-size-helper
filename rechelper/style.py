def build_stylesheet(p: dict) -> str:
    return f"""
QWidget {{
    background-color: {p['bg']};
    color: {p['text']};
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
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
    background-color: {p['card_bg']};
    border-radius: 14px;
    border: 1px solid {p['card_border']};
}}

QFrame#summaryCard {{
    background-color: {p['summary_bg']};
    border: 1px solid {p['summary_border']};
    border-radius: 14px;
}}
QLabel#summaryText {{
    color: {p['summary_text']};
    font-size: 19px;
    font-weight: 700;
}}

QScrollArea#pinnedScroll {{
    background: transparent;
    border: none;
}}

QFrame#pinChip {{
    background-color: {p['input_bg']};
    border: 1px solid {p['input_border']};
    border-radius: 15px;
}}
QFrame#pinChip:hover {{
    border-color: {p['input_border_hover']};
}}
QPushButton#pinChipLabel {{
    background: transparent;
    border: none;
    color: {p['text']};
    font-size: 12px;
    padding: 4px 2px;
    text-align: left;
}}
QPushButton#pinChipLabel:hover {{
    color: {p['text']};
    font-weight: 600;
}}
QPushButton#pinChipRemove, QPushButton#pinChipMove {{
    background: transparent;
    border: none;
    color: {p['text_muted']};
    font-size: 11px;
    border-radius: 10px;
}}
QPushButton#pinChipRemove:hover {{
    background-color: #3a2030;
    color: #ff9db0;
}}
QPushButton#pinChipMove:hover:!disabled {{
    background-color: {p['input_border_hover']};
    color: {p['text']};
}}
QPushButton#pinChipMove:disabled {{
    color: {p['text_dim']};
}}

QPushButton#pinToggle {{
    background-color: {p['input_bg']};
    border: 1px solid {p['input_border']};
    border-radius: 8px;
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

QPushButton#pathButton {{
    background-color: {p['input_bg']};
    border: 1px solid {p['input_border']};
    border-radius: 8px;
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
    border-radius: 12px;
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
    border-radius: 10px;
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
    height: 8px;
    background: {p['groove_bg']};
    border-radius: 4px;
}}

QSlider#deleteSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff5f6d, stop:1 #ff9966);
    border-radius: 4px;
}}
QSlider#deleteSlider::handle:horizontal {{
    background: #ffffff;
    border: 3px solid #ff7a52;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}}

QSlider#bufferSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22d3ee, stop:1 #5eead4);
    border-radius: 4px;
}}
QSlider#bufferSlider::handle:horizontal {{
    background: #ffffff;
    border: 3px solid #22d3ee;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
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
