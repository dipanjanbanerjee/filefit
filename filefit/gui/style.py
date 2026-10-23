# Same look as the phone app: deep ink background, violet-to-teal accents.
INK = "#0D0B1E"
SURFACE = "#17152E"
SURFACE_2 = "#211E3F"
LINE = "#2E2A55"
TEXT = "#F3F1FF"
MUTED = "#A39FC9"
VIOLET = "#7C5CFF"
TEAL = "#19D3B4"
PINK = "#FF5CA8"
OK = "#34D399"
WARN = "#FBBF24"
ERR = "#FB7185"

GRAD = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {VIOLET}, stop:1 {TEAL})"
GRAD_HOVER = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8E72FF, stop:1 #3BE0C4)"

STYLESHEET = f"""
* {{ font-family: "Segoe UI Variable Text", "Segoe UI", "Inter", "Noto Sans", sans-serif;
     font-size: 10pt; color: {TEXT}; }}
QMainWindow {{ background: {INK}; }}
QToolTip {{ background: {SURFACE_2}; color: {TEXT}; border: 1px solid {LINE}; border-radius: 8px; padding: 6px; }}

QLabel {{ background: transparent; }}
QLabel#title {{ font-size: 22pt; font-weight: 800; }}
QLabel#subtitle {{ color: {MUTED}; font-size: 10.5pt; }}
QLabel#section {{ color: {MUTED}; font-weight: 700; font-size: 8.5pt; letter-spacing: 1.5px; }}
QLabel#hint, QLabel#muted {{ color: {MUTED}; font-size: 9pt; }}
QLabel#badge {{ background: {GRAD}; border-radius: 16px; font-size: 20pt; font-weight: 800; color: white; }}

QFrame#card {{ background: rgba(23, 21, 46, 215); border: 1px solid {LINE}; border-radius: 22px; }}

QFrame#dropzone {{
    background: rgba(23, 21, 46, 200); border: 2px dashed #4A4380; border-radius: 22px;
}}
QFrame#dropzone[hover="true"] {{ background: rgba(124, 92, 255, 40); border-color: {TEAL}; }}
QLabel#dropIcon {{ background: {GRAD}; border-radius: 18px; color: white; font-size: 22pt; font-weight: 700; }}
QLabel#dropTitle {{ font-size: 14pt; font-weight: 700; }}

QListWidget {{
    background: rgba(23, 21, 46, 215); border: 1px solid {LINE}; border-radius: 18px; padding: 8px; outline: 0;
}}
QListWidget::item {{ padding: 9px 8px; border-radius: 12px; margin: 2px 0; }}
QListWidget::item:selected {{ background: {SURFACE_2}; color: {TEXT}; }}
QListWidget::item:hover {{ background: {SURFACE_2}; }}

QPushButton {{
    background: {SURFACE_2}; border: 1px solid {LINE}; border-radius: 14px;
    padding: 8px 16px; min-height: 22px; font-weight: 600;
}}
QPushButton:hover {{ border-color: {VIOLET}; }}
QPushButton:pressed {{ background: {LINE}; }}
QPushButton:disabled {{ color: #6C6894; border-color: {LINE}; background: {SURFACE}; }}

QPushButton#format {{ min-height: 30px; padding: 6px 0; font-size: 10.5pt; font-weight: 700; border-radius: 15px; }}
QPushButton#format:checked {{ background: {GRAD}; border: none; color: white; }}

QPushButton#chip {{ min-height: 20px; padding: 5px 8px; border-radius: 15px; font-size: 9pt; }}
QPushButton#chip:checked {{ background: {GRAD}; border: none; color: white; }}

QPushButton#support {{ background: transparent; border: 1px solid {PINK}; color: {PINK};
    border-radius: 18px; padding: 7px 16px; }}
QPushButton#support:hover {{ background: rgba(255, 92, 168, 40); }}

QPushButton#ghost {{ background: transparent; border: 1px solid {LINE}; color: {MUTED};
    border-radius: 18px; padding: 7px 14px; }}
QPushButton#ghost:hover {{ border-color: {TEAL}; color: {TEXT}; }}

QFrame#banner {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(124, 92, 255, 70),
    stop:1 rgba(25, 211, 180, 50)); border: 1px solid {VIOLET}; border-radius: 18px; }}
QLabel#bannerText {{ font-size: 10.5pt; }}
QPushButton#bannerBtn {{ background: {GRAD}; color: white; border: none; border-radius: 15px; padding: 8px 18px; }}
QPushButton#bannerBtn:hover {{ background: {GRAD_HOVER}; }}

QProgressDialog QProgressBar {{ min-height: 10px; max-height: 10px; }}

QPushButton#primary {{
    background: {GRAD}; color: white; border: none; border-radius: 20px;
    min-height: 30px; padding: 12px; font-size: 12.5pt; font-weight: 800;
}}
QPushButton#primary:hover {{ background: {GRAD_HOVER}; }}
QPushButton#primary:disabled {{ background: {SURFACE_2}; color: #6C6894; }}

QDoubleSpinBox, QSpinBox, QComboBox {{
    background: {SURFACE_2}; border: 1px solid {LINE}; border-radius: 12px; padding: 3px 10px; min-height: 28px;
}}
QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {VIOLET}; }}
QDoubleSpinBox:disabled, QSpinBox:disabled, QComboBox:disabled {{ color: #6C6894; background: {SURFACE}; }}
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border; width: 0px; border: none;
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {SURFACE_2}; border: 1px solid {LINE}; selection-background-color: {VIOLET}; }}

QCheckBox, QRadioButton {{ spacing: 9px; background: transparent; }}
QCheckBox::indicator, QRadioButton::indicator {{ width: 16px; height: 16px; }}
QCheckBox::indicator {{ border: 2px solid #5A5490; border-radius: 6px; background: {SURFACE}; }}
QCheckBox::indicator:checked {{ background: {GRAD}; border-color: {VIOLET}; }}
QRadioButton::indicator {{ border: 2px solid #5A5490; border-radius: 10px; background: {SURFACE}; }}
QRadioButton::indicator:checked {{ background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
    stop:0 {TEAL}, stop:0.5 {TEAL}, stop:0.6 {SURFACE}, stop:1 {SURFACE}); border-color: {TEAL}; }}
QCheckBox:disabled, QRadioButton:disabled {{ color: #6C6894; }}

QProgressBar {{ background: {SURFACE_2}; border: none; border-radius: 4px; max-height: 8px; min-height: 8px; }}
QProgressBar::chunk {{ background: {GRAD}; border-radius: 4px; }}

QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: {LINE}; border-radius: 3px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ height: 0; background: none; }}

QDialog, QMessageBox {{ background: {SURFACE}; }}
"""


def dark_palette():
    """Palette for parts the style sheet does not reach (menus, message boxes)."""
    from PySide6.QtGui import QColor, QPalette

    p = QPalette()
    for role, color in [
        (QPalette.Window, SURFACE), (QPalette.WindowText, TEXT), (QPalette.Base, SURFACE_2),
        (QPalette.AlternateBase, SURFACE), (QPalette.Text, TEXT), (QPalette.Button, SURFACE_2),
        (QPalette.ButtonText, TEXT), (QPalette.Highlight, VIOLET), (QPalette.HighlightedText, "#FFFFFF"),
        (QPalette.ToolTipBase, SURFACE_2), (QPalette.ToolTipText, TEXT), (QPalette.Link, TEAL),
        (QPalette.PlaceholderText, MUTED),
    ]:
        p.setColor(role, QColor(color))
    return p
