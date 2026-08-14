# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : main.py
# Author  : Safdar Ali
# =====================================================

"""
Application Entry Point.
Initializes the PyQt6 event loop, configures high-DPI scaling,
and displays the primary GUI window.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow


def main():
    """
    Main application bootstrap function.
    """
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Safdar Firmware Toolkit Pro")
    app.setOrganizationName("Safdar Firmware Labs")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()