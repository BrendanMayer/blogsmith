from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


def apply_theme(app: QApplication) -> None:
    app.setFont(QFont("Segoe UI", 10))

    app.setStyleSheet(
        """
        QWidget {
            background-color: #0f172a;
            color: #e5e7eb;
            font-family: "Segoe UI";
            font-size: 10pt;
        }

        QMainWindow {
            background-color: #0f172a;
        }

        QFrame#Sidebar {
            background-color: #020617;
            border-right: 1px solid #1e293b;
        }

        QFrame#Panel {
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 16px;
        }

        QFrame#TopBar {
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 16px;
        }

        QLabel#AppTitle {
            color: #f8fafc;
            font-size: 22px;
            font-weight: 700;
        }

        QLabel#AppSubtitle {
            color: #94a3b8;
            font-size: 12px;
        }

        QLabel#SectionTitle {
            color: #f8fafc;
            font-size: 13px;
            font-weight: 700;
        }

        QLabel#MutedLabel {
            color: #94a3b8;
            font-size: 12px;
        }

        QLabel#FileLabel {
            color: #f8fafc;
            font-size: 13px;
            font-weight: 600;
        }

        QLabel#Pill {
            background-color: #1e293b;
            color: #cbd5e1;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 5px 10px;
            font-size: 12px;
        }

        QListWidget {
            background-color: #0b1120;
            border: 1px solid #1e293b;
            border-radius: 14px;
            padding: 8px;
            outline: none;
        }

        QListWidget::item {
            background-color: transparent;
            color: #cbd5e1;
            padding: 10px;
            border-radius: 10px;
            margin: 2px;
        }

        QListWidget::item:hover {
            background-color: #1e293b;
            color: #f8fafc;
        }

        QListWidget::item:selected {
            background-color: #2563eb;
            color: #ffffff;
        }

        QTextEdit, QTextBrowser {
            background-color: #020617;
            color: #e5e7eb;
            border: 1px solid #1e293b;
            border-radius: 16px;
            padding: 16px;
            selection-background-color: #2563eb;
            selection-color: white;
            font-family: Consolas, "Cascadia Mono", monospace;
            font-size: 14px;
            line-height: 1.5;
        }

        QLineEdit {
            background-color: #020617;
            color: #e5e7eb;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 9px 11px;
        }

        QLineEdit:focus {
            border: 1px solid #60a5fa;
        }

        QTextEdit:focus {
            border: 1px solid #60a5fa;
        }

        QPushButton {
            background-color: #1e293b;
            color: #f8fafc;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 9px 12px;
            font-weight: 600;
        }

        QPushButton:hover {
            background-color: #334155;
            border: 1px solid #475569;
        }

        QPushButton:pressed {
            background-color: #0f172a;
        }

        QPushButton:disabled {
            background-color: #111827;
            color: #64748b;
            border: 1px solid #1f2937;
        }

        QPushButton#PrimaryButton {
            background-color: #2563eb;
            border: 1px solid #3b82f6;
            color: white;
        }

        QPushButton#PrimaryButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton#DangerButton {
            background-color: #7f1d1d;
            border: 1px solid #991b1b;
            color: white;
        }

        QPushButton#SidebarButton {
            text-align: left;
            padding: 10px 12px;
            background-color: transparent;
            border: 1px solid transparent;
            color: #cbd5e1;
        }

        QPushButton#SidebarButton:hover {
            background-color: #111827;
            border: 1px solid #1f2937;
            color: #ffffff;
        }

        QTabWidget::pane {
            border: 1px solid #1e293b;
            border-radius: 14px;
            background-color: #111827;
            top: -1px;
        }

        QTabBar::tab {
            background-color: #020617;
            color: #94a3b8;
            padding: 10px 16px;
            border: 1px solid #1e293b;
            border-bottom: none;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            margin-right: 4px;
        }

        QTabBar::tab:selected {
            background-color: #111827;
            color: #f8fafc;
            border-color: #334155;
        }

        QSplitter::handle {
            background-color: #0f172a;
        }

        QSplitter::handle:horizontal {
            width: 8px;
        }

        QStatusBar {
            background-color: #020617;
            color: #94a3b8;
            border-top: 1px solid #1e293b;
        }

        QDialog {
            background-color: #0f172a;
        }

        QCheckBox {
            color: #cbd5e1;
            spacing: 8px;
        }

        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 5px;
            border: 1px solid #475569;
            background-color: #020617;
        }

        QCheckBox::indicator:checked {
            background-color: #2563eb;
            border: 1px solid #60a5fa;
        }

        QDialogButtonBox QPushButton {
            min-width: 90px;
        }
        """
    )