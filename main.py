"""
=========================================================
 Safdar Firmware Toolkit Pro
 Version : 0.1 Alpha
 Module  : Main Entry
=========================================================
"""

import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()