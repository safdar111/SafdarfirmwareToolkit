# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.5.0 (Workshop Grade)
# File      : gui/main_window.py
# Author    : Safdar Ali
# =====================================================

"""
Master Application GUI Container Window.
Integrates diagnostic tab, dual repair wizard tab, dual-chip utility tab,
status bar tracking, database initialization, and workshop theme styling.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QStatusBar, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from gui.dashboard_tab import DashboardTab
from gui.dual_repair_tab import DualRepairTab
from gui.dual_chip_tab import DualChipTab
from gui.password_tab import PasswordRemovalTab
from database.db_manager import DatabaseManager


class MainWindow(QMainWindow):
    """
    Main application shell for Safdar Firmware Toolkit Pro.
    """

    def __init__(self):
        super().__init__()
        # Initialize backend databases before GUI loads completely
        self.db_manager = DatabaseManager()
        self.db_stats = self._init_database()
        
        self.init_ui()

    def _init_database(self) -> dict:
        """Hooks into our DB Manager to ensure workshop folders exist."""
        try:
            self.db_manager.initialize_database()
            return self.db_manager.update_index()
        except Exception as e:
            print(f"[-] Database Error: {e}")
            return {"total_me_files": 0, "total_donors": 0}

    def init_ui(self):
        self.setWindowTitle("Safdar Firmware Toolkit Pro v0.5.0 - Hardware Repair Edition")
        self.resize(1150, 780)
        self.setMinimumSize(950, 650)

        # Apply premium dark theme styling
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
                padding-top: 12px;
                font-weight: bold;
                color: #569CD6;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
            QLineEdit, QTextEdit {
                background-color: #252526;
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                padding: 6px;
                color: #DCDCDC;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #007ACC;
            }
            QPushButton {
                background-color: #333333;
                border: 1px solid #454545;
                border-radius: 4px;
                padding: 7px 15px;
                color: #FFFFFF;
                font-weight: 500;
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
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #007ACC;
                border-radius: 3px;
            }
            QTabWidget::pane {
                border: 1px solid #333333;
                border-radius: 4px;
                top: -1px;
            }
            QTabBar::tab {
                background: #2D2D2D;
                border: 1px solid #333333;
                padding: 10px 22px;
                margin-right: 3px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                color: #999999;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #1E1E1E;
                color: #007ACC;
                border-bottom: 2px solid #007ACC;
            }
            QTabBar::tab:hover:!selected {
                background: #333333;
                color: #CCCCCC;
            }
        """)

        # Central Tab Container
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        self.tabs = QTabWidget()
        self.dashboard_tab = DashboardTab()
        self.dual_repair_tab = DualRepairTab()
        self.dual_chip_tab = DualChipTab()
        self.password_tab = PasswordRemovalTab()          # <--- 1. Yahan object banayein

        self.tabs.addTab(self.dashboard_tab, "Single BIOS Diagnostic")
        self.tabs.addTab(self.dual_repair_tab, "Dual-BIOS Repair Wizard")
        self.tabs.addTab(self.dual_chip_tab, "Dual-Chip Utility")
        self.tabs.addTab(self.password_tab, "Password Removal")         # <--- 2. Yahan tab add karein

        layout.addWidget(self.tabs)
        self.setCentralWidget(central_widget)

        # Status Bar with Database Metrics
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background-color: #007ACC; color: white; font-weight: bold;")
        self.setStatusBar(self.status_bar)
        
        me_count = self.db_stats.get("total_me_files", 0)
        status_text = f" Safdar Firmware Toolkit Pro | Component-Level Diagnostics Engine Ready | Local Clean ME Files: {me_count} "
        
        status_info = QLabel(status_text)
        status_info.setStyleSheet("color: #FFFFFF; font-size: 11px;")
        self.status_bar.addWidget(status_info)

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())