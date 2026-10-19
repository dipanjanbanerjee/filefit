ACCENT = "#4F46E5"
ACCENT_HOVER = "#4338CA"
ACCENT_SOFT = "#EEF2FF"
BG = "#F5F6FA"
CARD = "#FFFFFF"
BORDER = "#E3E5EC"
TEXT = "#1F2330"
MUTED = "#6B7080"
OK = "#15803D"
WARN = "#B45309"
ERR = "#B91C1C"

STYLESHEET = f"""
* {{ font-family: "Segoe UI", "Inter", "Noto Sans", sans-serif; font-size: 10pt; color: {TEXT}; }}
QMainWindow, QWidget#root {{ background: {BG}; }}
QLabel#title {{ font-size: 20pt; font-weight: 700; }}
QLabel#subtitle {{ color: {MUTED}; font-size: 10pt; }}
QLabel#section {{ font-weight: 600; font-size: 10.5pt; margin-top: 4px; }}
QLabel#hint, QLabel#muted {{ color: {MUTED}; font-size: 9pt; }}

QFrame#card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; }}

QFrame#dropzone {{
    background: {CARD}; border: 2px dashed #C7CAD6; border-radius: 14px;
}}
QFrame#dropzone[hover="true"] {{ background: {ACCENT_SOFT}; border-color: {ACCENT}; }}
QLabel#dropIcon {{ font-size: 30pt; color: {ACCENT}; }}
QLabel#dropTitle {{ font-size: 13pt; font-weight: 600; }}

QListWidget {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; padding: 6px; outline: 0;
}}
QListWidget::item {{ padding: 8px 6px; border-radius: 8px; }}
QListWidget::item:selected {{ background: {ACCENT_SOFT}; color: {TEXT}; }}
QListWidget::item:hover {{ background: #F3F4F8; }}

QPushButton {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 9px; padding: 7px 14px;
}}
QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton:disabled {{ color: #A9ADBA; border-color: {BORDER}; }}

QPushButton#format {{ padding: 10px 0; font-weight: 600; border-radius: 10px; }}
QPushButton#format:checked {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}

QPushButton#chip {{ padding: 4px 10px; border-radius: 12px; font-size: 9pt; }}
QPushButton#chip:checked {{ background: {ACCENT_SOFT}; border-color: {ACCENT}; color: {ACCENT}; }}

QPushButton#primary {{
    background: {ACCENT}; color: white; border: none; border-radius: 11px;
    padding: 13px; font-size: 11.5pt; font-weight: 700;
}}
QPushButton#primary:hover {{ background: {ACCENT_HOVER}; color: white; }}
QPushButton#primary:disabled {{ background: #A5A8E8; color: white; }}

QDoubleSpinBox, QSpinBox, QComboBox {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px; padding: 2px 8px; min-height: 28px;
}}
QDoubleSpinBox:disabled, QSpinBox:disabled, QComboBox:disabled {{ color: #A9ADBA; background: #F7F7FA; }}
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border; width: 0px; border: none;
}}
QComboBox::drop-down {{ border: none; width: 22px; }}

QCheckBox, QRadioButton {{ spacing: 8px; }}

QProgressBar {{
    background: #E8E9F0; border: none; border-radius: 5px; height: 10px; text-align: center; color: transparent;
}}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 5px; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
"""
