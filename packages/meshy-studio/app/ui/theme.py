from __future__ import annotations

BG = "#14121b"
CARD = "#1e1a29"
CARD_ALT = "#231e31"
BORDER = "#2f2942"
TEXT = "#f2effa"
MUTED = "#9d96b4"
ACCENT = "#8055d6"
ACCENT_HOVER = "#9468ee"
DANGER = "#d32f2f"
OK = "#4cc38a"
WARN = "#ffb347"

STYLE = f"""
* {{ font-family: "Segoe UI", sans-serif; font-size: 13px; color: {TEXT}; }}
QMainWindow, QWidget#root {{ background: {BG}; }}
QFrame#sidebar {{ background: {CARD}; border-right: 1px solid {BORDER}; }}
QLabel#brand {{ font-size: 19px; font-weight: 700; }}
QLabel#tagline, QLabel#muted {{ color: {MUTED}; }}
QLabel#pageTitle {{ font-size: 22px; font-weight: 700; }}
QLabel#alert {{ color: {WARN}; font-weight: 600; }}
QLabel#footer {{ color: {MUTED}; padding: 6px 2px; }}
QLabel#summary {{ color: {MUTED}; padding: 2px 4px; }}
QFrame#card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; }}
QListWidget#nav {{ background: transparent; border: none; outline: none; }}
QListWidget#nav::item {{ padding: 11px 14px; border-radius: 8px; margin: 2px 0; color: {MUTED}; }}
QListWidget#nav::item:hover {{ background: {CARD_ALT}; color: {TEXT}; }}
QListWidget#nav::item:selected {{ background: {ACCENT}; color: white; font-weight: 600; }}
QPushButton {{ background: {ACCENT}; color: white; border: none; border-radius: 8px; padding: 8px 16px; font-weight: 600; }}
QPushButton:hover {{ background: {ACCENT_HOVER}; }}
QPushButton:pressed {{ background: #6a46b8; }}
QPushButton:disabled {{ background: {BORDER}; color: {MUTED}; }}
QPushButton#secondary {{ background: transparent; border: 1px solid {BORDER}; color: {TEXT}; }}
QPushButton#secondary:hover {{ border-color: {ACCENT}; background: {CARD_ALT}; }}
QPushButton#danger {{ background: {DANGER}; padding: 11px 16px; letter-spacing: 0.5px; }}
QPushButton#danger:hover {{ background: #e53935; }}
QPushButton#dropzone {{ background: {CARD}; border: 2px dashed {ACCENT}; border-radius: 14px; padding: 38px;
    font-size: 16px; font-weight: 600; color: {TEXT}; }}
QPushButton#dropzone:hover {{ background: {CARD_ALT}; border-color: {ACCENT_HOVER}; }}
QLineEdit {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 10px; selection-background-color: {ACCENT}; }}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QTableWidget {{ background: {CARD}; alternate-background-color: {CARD_ALT}; border: 1px solid {BORDER}; border-radius: 10px;
    gridline-color: transparent; selection-background-color: #3a2d63; selection-color: {TEXT}; outline: none; }}
QTableWidget::item {{ padding: 4px 8px; border: none; }}
QHeaderView::section {{ background: {CARD}; color: {MUTED}; border: none; border-bottom: 1px solid {BORDER};
    padding: 8px; font-weight: 600; }}
QTableCornerButton::section {{ background: {CARD}; border: none; }}
QPlainTextEdit {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 8px;
    font-family: Consolas, monospace; font-size: 12px; }}
QListWidget {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 4px; outline: none; }}
QListWidget::item {{ padding: 8px 10px; border-radius: 6px; }}
QListWidget::item:selected {{ background: #3a2d63; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QToolTip {{ background: {CARD_ALT}; color: {TEXT}; border: 1px solid {BORDER}; padding: 6px; }}
"""

STATUS_COLORS = {
    "completed": OK, "failed": "#ff6b6b", "canceled": MUTED, "paused": WARN, "cancel requested": WARN,
    "generating": "#6ab7ff", "uploading": "#6ab7ff", "checking account": "#6ab7ff", "downloading": "#6ab7ff",
    "queued": TEXT, "pending": TEXT,
}


def status_color(text: str) -> str:
    lowered = text.lower()
    for key, color in STATUS_COLORS.items():
        if lowered.startswith(key):
            return color
    return TEXT
