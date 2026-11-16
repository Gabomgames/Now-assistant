from PySide6.QtGui import QFont

STYLESHEET = """
QWidget { color: #ededf4; font-family: 'Segoe UI', 'DejaVu Sans'; font-size: 13px; }
QMainWindow, QWidget#main { background: #0d0d12; }
QWidget#sidebar { background: #13131b; border-right: 1px solid #272733; }
QLabel { background: transparent; border: none; }
QLabel#brand { font-size: 29px; font-weight: 750; color: #faf8ff; }
QLabel#brandSubtitle { color: #a995d4; font-size: 10px; letter-spacing: 3px; }
QLabel#muted, QLabel#hint { color: #9293a6; font-size: 11px; }
QLabel#section { color: #8f90a6; font-size: 10px; font-weight: 600; letter-spacing: 1.2px; }
QLabel#chatTitle { font-size: 17px; font-weight: 600; }
QLabel#badge { color: #bcb0db; background: #221d2e; border-radius: 9px; padding: 5px 10px; font-size: 11px; }
QLabel#engineStatus { color: #66cbd9; font-size: 11px; }
QLabel#welcomeTitle { font-size: 29px; font-weight: 650; }
QLabel#welcomeText { color: #aaaabd; font-size: 14px; }
QPushButton, QToolButton { background: #1c1c27; border: 1px solid #343443; border-radius: 9px; padding: 9px 13px; }
QPushButton:hover, QToolButton:hover { background: #282737; border-color: #665589; }
QPushButton:focus, QToolButton:focus { border-color: #b59ae9; }
QPushButton:disabled, QToolButton:disabled { color: #686879; background: #181820; border-color: #292934; }
QPushButton#primary, QPushButton#sendButton { background: #8d6ad6; border: 1px solid #ad90e6; color: #fff; font-weight: 650; }
QPushButton#primary:hover, QPushButton#sendButton:hover { background: #9d7ae2; }
QPushButton#primary:disabled, QPushButton#sendButton:disabled { background: #393045; color: #8f859e; border-color: #4b4059; }
QPushButton#flat { background: transparent; border-color: transparent; text-align: left; padding-left: 8px; }
QPushButton#copy { background: transparent; border: none; color: #aaa3c3; font-size: 10px; padding: 0 3px; }
QLineEdit, QComboBox, QSpinBox { background: #1a1a25; border: 1px solid #343443; border-radius: 8px; padding: 9px; selection-background-color: #69518d; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #a386d1; }
QComboBox QAbstractItemView { background: #1c1c27; selection-background-color: #423450; }
QListWidget { border: none; background: transparent; outline: 0; }
QListWidget::item { padding: 2px; border: 1px solid transparent; border-radius: 9px; margin-bottom: 5px; }
QListWidget::item:selected { background: #292333; border-color: #59436e; }
QListWidget::item:hover { background: #20202d; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { width: 7px; background: transparent; margin: 2px; }
QScrollBar::handle:vertical { background: #393343; border-radius: 3px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QFrame#userBubble { background: #272033; border: 1px solid #3d2e4c; border-radius: 13px; }
QFrame#assistantBubble { background: #171720; border: 1px solid #292933; border-radius: 13px; }
QLabel#messageBody { font-size: 14px; color: #efedf5; }
QLabel#messageRole { font-size: 11px; font-weight: 600; color: #b8accb; }
QFrame#composer { background: #181820; border: 1px solid #383441; border-radius: 13px; }
QPlainTextEdit { background: transparent; border: none; font-size: 14px; padding: 4px; selection-background-color: #5f457c; }
QFrame#banner { background: #29221c; border: 1px solid #564431; border-radius: 8px; }
QLabel#errorText { color: #e5c19a; font-size: 12px; }
QDialog, QMessageBox, QInputDialog { background: #15151d; }
QMenu { background: #1c1c26; border: 1px solid #3b3545; padding: 5px; }
QMenu::item { padding: 9px 24px 9px 12px; border-radius: 5px; }
QMenu::item:selected { background: #3a2d49; }
QCheckBox { spacing: 9px; }
"""


def apply_theme(application):
    application.setFont(QFont("Segoe UI", 10))
    application.setStyle("Fusion")
    application.setStyleSheet(STYLESHEET)
