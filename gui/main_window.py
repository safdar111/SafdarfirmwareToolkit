# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : gui/main_window.py
# Author  : Safdar Ali
# =====================================================

"""
Master Application GUI Container Window.
Integrates single diagnostic tab, dual repair wizard tab,
status bar tracking, and workshop theme styling.
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QStatusBar,
    QLabel,
)
from PyQt6.QtCore import Qt
from gui.dashboard_tab import DashboardTab
from gui.dual_repair_tab import DualRepairTab


class MainWindow(QMainWindow):
    """
    Main application shell for Safdar Firmware Toolkit Pro.
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Safdar Firmware Toolkit Pro v0.3.0 - Hardware Repair Edition")
        self.resize(1100, 750)
        self.setMinimumSize(900, 600)

        # Apply dark theme styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
            QWidget {
                background-color: #1E1E1E;
                color: #CCCCCC;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #333333;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #569CD6;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
            QLineEdit, QTextEdit {
                background-color: #252526;
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                padding: 5px;
                color: #DCDCDC;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #007ACC;
            }
            QPushButton {
                background-color: #333333;
                border: 1px solid #454545;
                border-radius: 4px;
                padding: 6px 14px;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #3E3E42;
                border-color: #007ACC;
            }
            QPushButton:pressed {
                background-color: #007ACC;
            }
            QPushButton:disabled {
                background-color: #2D2D2D;
                color: #656565;
                border-color: #2D2D2D;
            }
            QProgressBar {
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                text-align: center;
                background-color: #252526;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #007ACC;
                width: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #333333;
                top: -1px;
            }
            QTabBar::tab {
                background: #2D2D2D;
                border: 1px solid #333333;
                padding: 8px 18px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: #999999;
            }
            QTabBar::tab:selected {
                background: #1E1E1E;
                color: #007ACC;
                font-weight: bold;
                border-bottom: 2px solid #007ACC;
            }
        """)

        # Central Tab Container
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.dashboard_tab = DashboardTab()
        self.dual_repair_tab = DualRepairTab()

        self.tabs.addTab(self.dashboard_tab, "Single BIOS Diagnostic")
        self.tabs.addTab(self.dual_repair_tab, "Dual-BIOS Repair Wizard")

        layout.addWidget(self.tabs)
        self.setCentralWidget(central_widget)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        status_info = QLabel("Safdar Firmware Toolkit Pro | Component-Level Diagnostics Engine Ready")
        status_info.setStyleSheet("color: #888888; font-size: 11px;")
        self.status_bar.addWidget(status_info)