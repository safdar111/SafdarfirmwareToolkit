# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.1 Alpha
# File    : main_window.py
# Author  : Safdar Ali
# =====================================================

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QFileDialog,
)

from PySide6.QtCore import Qt
from core.analyzer import FirmwareAnalyzer


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.current_file = None

        self.setWindowTitle("Safdar Firmware Toolkit Pro v0.1 Alpha")
        self.resize(1000, 700)

        self.setup_ui()

    def setup_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        central.setLayout(layout)

        title = QLabel("Safdar Firmware Toolkit Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
            color:#00FF99;
        """)

        layout.addWidget(title)

        self.open_button = QPushButton("Open BIOS File")
        self.open_button.clicked.connect(self.open_file)
        layout.addWidget(self.open_button)

        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.setEnabled(False)
        self.analyze_button.clicked.connect(self.analyze_file)
        layout.addWidget(self.analyze_button)

        self.report = QTextEdit()
        self.report.setReadOnly(True)
        layout.addWidget(self.report)

    def open_file(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open BIOS File",
            "",
            "BIOS Files (*.bin *.rom *.fd);;All Files (*.*)"
        )

        if filename:

            self.current_file = filename

            self.report.clear()
            self.report.append("Firmware Loaded Successfully\n")
            self.report.append(f"File:\n{filename}\n")
            self.report.append("Ready for analysis...")

            self.analyze_button.setEnabled(True)

    def analyze_file(self):

        if not self.current_file:
            return

        try:

            analyzer = FirmwareAnalyzer(self.current_file)

            result = analyzer.analyze()

            self.report.clear()
            self.report.setPlainText(result)

        except Exception as e:

            self.report.clear()
            self.report.append("Analysis Failed!\n")
            self.report.append(str(e))