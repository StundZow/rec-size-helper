"""Feuille de style de l'appli, de la même famille que son icône : aplats nets et contrastés,
panneaux pleins à fine bordure, contrôles segmentés sur rail gris, et le dégradé rose → violet
du logo réservé à l'action principale. Aucune transparence givrée, aucun halo."""

from .resources import resource_path

_CHECK_ICON = resource_path("assets/check.png").replace("\\", "/")


def _grad(a: str, b: str) -> str:
    return f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {a}, stop:1 {b})"


def build_stylesheet(p: dict) -> str:
    primary = _grad(p["grad_a"], p["grad_b"])
    primary_hover = _grad(p["grad_a_hover"], p["grad_b_hover"])
    progress = _grad(p["progress_a"], p["progress_b"])
    return f"""
QWidget {{
    background-color: transparent;
    color: {p['text']};
    /* Une seule famille, sans générique (sans-serif) en secours : dès qu'une règle donne une
       liste, Qt construit toute sa chaîne de polices de repli au premier affichage, police
       emoji comprise — ~1 s pour rien, Segoe UI étant toujours présente sous Windows. */
    font-family: 'Segoe UI';
    font-size: 13px;
}}

QDialog {{
    background-color: {p['bg']};
}}

QToolTip {{
    background-color: {p['panel']};
    color: {p['text']};
    border: 1px solid {p['line2']};
    border-radius: 6px;
    padding: 5px 8px;
}}

/* ---------- textes ---------- */
QLabel#title {{
    font-size: 22px;
    font-weight: 700;
    color: {p['text']};
}}
QLabel#subtitle, QLabel#mutedText {{
    color: {p['text_muted']};
}}
QLabel#subtitle {{
    font-size: 12px;
}}
QLabel#sectionTitle {{
    font-size: 15px;
    font-weight: 700;
    color: {p['text']};
}}
QLabel#panelTitle {{
    font-size: 17px;
    font-weight: 700;
    color: {p['text']};
}}
QLabel#rowTitle {{
    font-size: 14px;
    font-weight: 600;
    color: {p['text']};
}}
QLabel#legendText {{
    color: {p['text_muted']};
    font-size: 12px;
    font-weight: 600;
}}
QLabel#freeFigure {{
    font-size: 14px;
    font-weight: 700;
    color: {p['text']};
}}
QLabel#freeFigure[preview="true"] {{
    color: {p['accent']};
}}
QLabel#statusOk {{
    color: {p['success']};
    font-weight: 600;
}}
QLabel#statusError {{
    color: {p['warn']};
    font-weight: 600;
}}

/* ---------- surfaces ---------- */
QFrame#card {{
    background-color: {p['panel']};
    border: 1px solid {p['line']};
    border-radius: 12px;
}}
QFrame#modalCard {{
    background-color: {p['panel']};
    border: 1px solid {p['line']};
    border-radius: 14px;
}}
QFrame#note {{
    background-color: {p['soft2']};
    border: none;
    border-radius: 10px;
}}

/* ---------- navigation des dossiers (rail segmenté) ---------- */
QScrollArea#pinnedScroll {{
    background: transparent;
    border: none;
}}
QFrame#segmentPill {{
    background-color: {p['soft2']};
    border: none;
    border-radius: 12px;
}}
QPushButton#segmentItem {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 7px 14px;
    color: {p['text_muted']};
    font-weight: 600;
    font-size: 13px;
}}
QPushButton#segmentItem:hover:!disabled {{
    color: {p['text']};
}}
QPushButton#segmentItem:disabled {{
    color: {p['text_dim']};
}}
QWidget#pinSegment[active="true"] {{
    background-color: {p['panel']};
    border: 1px solid {p['line']};
    border-radius: 9px;
}}
QWidget#pinSegment[active="true"] QPushButton#segmentItem {{
    color: {p['text']};
    font-weight: 700;
}}
QPushButton#segMini {{
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 0px;
}}
QPushButton#segMini:hover:!disabled {{
    background-color: {p['hover']};
}}

/* ---------- interrupteurs à deux icônes ---------- */
QFrame#segmentIconPill {{
    background-color: {p['soft2']};
    border: none;
    border-radius: 10px;
}}
QPushButton#segmentIconItem {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 0px;
}}
QFrame#segmentIconThumb {{
    background-color: {p['panel']};
    border: 1px solid {p['line']};
    border-radius: 8px;
}}

/* ---------- boutons ---------- */
QPushButton#iconButton {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 0px;
}}
QPushButton#iconButton:hover:!disabled {{
    background-color: {p['hover']};
}}
QPushButton#iconButton:pressed {{
    background-color: {p['soft2']};
}}

QPushButton#pathButton, QPushButton#pinToggle {{
    background-color: {p['panel']};
    border: 1px solid {p['line2']};
    border-radius: 9px;
    padding: 8px 15px;
    color: {p['text']};
    font-weight: 600;
}}
QPushButton#pathButton:hover:!disabled, QPushButton#pinToggle:hover:!disabled {{
    background-color: {p['soft']};
    border-color: {p['accent_line']};
}}
QPushButton#pathButton:disabled, QPushButton#pinToggle:disabled {{
    color: {p['text_dim']};
    border-color: {p['line']};
}}
QPushButton#pinToggle:checked {{
    background-color: {p['accent_bg']};
    border-color: {p['accent_line']};
    color: {p['accent']};
}}

QPushButton#lockToggle {{
    background-color: {p['panel']};
    border: 1px solid {p['line2']};
    border-radius: 9px;
    padding: 0px;
}}
QPushButton#lockToggle:hover {{
    border-color: {p['accent_line']};
}}
QPushButton#lockToggle:checked {{
    background-color: {p['accent_bg']};
    border-color: {p['accent_line']};
}}

/* action principale : le dégradé du logo, un cran plus sombre au repos pour que le texte
   blanc reste lisible, le dégradé exact du logo au survol */
QPushButton#deleteButton, QPushButton#updateButton {{
    background: {primary};
    color: #ffffff;
    border: none;
    font-weight: 700;
}}
QPushButton#deleteButton {{
    font-size: 14.5px;
    border-radius: 11px;
    padding: 12px 26px;
}}
QPushButton#updateButton {{
    font-size: 13.5px;
    border-radius: 10px;
    padding: 9px 20px;
}}
QPushButton#deleteButton:hover:!disabled, QPushButton#updateButton:hover:!disabled {{
    background: {primary_hover};
}}
QPushButton#deleteButton:disabled, QPushButton#updateButton:disabled {{
    background: {p['soft2']};
    color: {p['text_dim']};
}}

/* ---------- champs ---------- */
QLineEdit {{
    background-color: {p['soft']};
    border: 1px solid {p['line']};
    border-radius: 8px;
    padding: 7px 11px;
    color: {p['text']};
    font-size: 13px;
    selection-background-color: {p['accent2']};
    selection-color: #ffffff;
}}
QLineEdit:hover {{
    border-color: {p['line2']};
}}
QLineEdit:focus {{
    border-color: {p['accent2']};
    background-color: {p['panel']};
}}
QLineEdit:disabled {{
    color: {p['text_dim']};
}}
QLineEdit#pinIconEdit {{
    padding: 5px 2px;
    font-size: 17px;
}}

QTextEdit#updateNotes {{
    background-color: {p['soft']};
    border: 1px solid {p['line']};
    border-radius: 8px;
    padding: 8px;
    font-size: 12px;
    color: {p['text2']};
}}

/* ---------- curseurs : chacun dans la couleur de la série qu'il coupe ---------- */
QSlider::groove:horizontal {{
    height: 6px;
    background: {p['soft2']};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {p['panel']};
    border: 1px solid {p['line2']};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    border-color: {p['accent2']};
}}
QSlider#deleteSlider::sub-page:horizontal {{
    background: {p['mp4']};
    border-radius: 3px;
}}
QSlider#bufferSlider::sub-page:horizontal {{
    background: {p['mkv']};
    border-radius: 3px;
}}

/* ---------- progression ---------- */
QProgressBar {{
    background-color: {p['soft2']};
    border: none;
    border-radius: 8px;
    min-height: 16px;
    max-height: 16px;
    text-align: center;
    color: {p['text']};
    font-size: 11px;
    font-weight: 600;
}}
QProgressBar::chunk {{
    background: {progress};
    border-radius: 8px;
}}

/* ---------- cases à cocher ---------- */
QCheckBox {{
    color: {p['text']};
    font-weight: 600;
    font-size: 13px;
    spacing: 11px;
}}
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 6px;
    background-color: {p['soft']};
    border: 1px solid {p['line2']};
}}
QCheckBox::indicator:hover {{
    border-color: {p['accent2']};
}}
QCheckBox::indicator:checked {{
    background: {primary};
    border: none;
    image: url("{_CHECK_ICON}");
}}

/* ---------- défilement ---------- */
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: {p['line2']};
    border-radius: 3px;
    min-height: 28px;
    min-width: 28px;
}}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background: {p['text_dim']};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
}}
QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
}}
"""
