import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFileDialog, QGroupBox, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

# Import Backend Analyzer
from core.analyzer import BIOSAnalyzer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Safdar Firmware Toolkit - Laptop BIOS & CSME Diagnostic Tools")
        self.setGeometry(100, 100, 950, 700)
        self.setAcceptDrops(True)  # Enable Drag and Drop

        self.selected_file_path = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # Header Title
        title_label = QLabel("SAFDAR FIRMWARE TOOLKIT")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #1E88E5; margin: 10px;")
        main_layout.addWidget(title_label)

        # File Drop / Selection Area
        drop_group = QGroupBox("1. Load BIOS Firmware Dump (.bin / .rom)")
        drop_layout = QHBoxLayout()

        self.file_label = QLabel("Drag & Drop BIOS File Here  OR  Click 'Browse' Button")
        self.file_label.setStyleSheet("border: 2px dashed #9E9E9E; padding: 20px; font-size: 14px; background: #F5F5F5;")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.file_label, stretch=3)

        btn_browse = QPushButton("Browse File")
        btn_browse.setStyleSheet("padding: 15px; font-weight: bold; font-size: 14px; background-color: #1E88E5; color: white;")
        btn_browse.clicked.connect(self.browse_file)
        drop_layout.addWidget(btn_browse, stretch=1)

        drop_group.setLayout(drop_layout)
        main_layout.addWidget(drop_group)

        # Quick Summary Cards (Board Model, Serial, CSME Status)
        summary_group = QGroupBox("2. Extracted Hardware Metadata")
        grid_layout = QGridLayout()

        grid_layout.addWidget(QLabel("<b>Motherboard Part #:</b>"), 0, 0)
        self.lbl_board = QLabel("N/A")
        self.lbl_board.setStyleSheet("font-size: 14px; color: #D32F2F; font-weight: bold;")
        grid_layout.addWidget(self.lbl_board, 0, 1)

        grid_layout.addWidget(QLabel("<b>Laptop Model:</b>"), 0, 2)
        self.lbl_model = QLabel("N/A")
        self.lbl_model.setStyleSheet("font-size: 14px; color: #1976D2; font-weight: bold;")
        grid_layout.addWidget(self.lbl_model, 0, 3)

        grid_layout.addWidget(QLabel("<b>Serial / Service Tag:</b>"), 1, 0)
        self.lbl_serial = QLabel("N/A")
        self.lbl_serial.setStyleSheet("font-size: 14px; color: #388E3C; font-weight: bold;")
        grid_layout.addWidget(self.lbl_serial, 1, 1)

        grid_layout.addWidget(QLabel("<b>CSME Region State:</b>"), 1, 2)
        self.lbl_csme = QLabel("N/A")
        self.lbl_csme.setStyleSheet("font-size: 14px; color: #E65100; font-weight: bold;")
        grid_layout.addWidget(self.lbl_csme, 1, 3)

        summary_group.setLayout(grid_layout)
        main_layout.addWidget(summary_group)

        # Full Report Text Output
        report_group = QGroupBox("3. Diagnostic Report & Solutions")
        report_layout = QVBoxLayout()

        self.txt_report = QTextEdit()
        self.txt_report.setReadOnly(True)
        self.txt_report.setStyleSheet("font-family: Consolas, Monospace; font-size: 13px; background-color: #263238; color: #ECEFF1;")
        report_layout.addWidget(self.txt_report)

        report_group.setLayout(report_layout)
        main_layout.addWidget(report_group)

        central_widget.setLayout(main_layout)

    # File Drag & Drop Events
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.bin', '.rom', '.fd')):
                self.process_firmware(file_path)
                break
            else:
                QMessageBox.warning(self, "Invalid File", "Aap sirf .bin, .rom ya .fd extension wali BIOS files load kar sakte hain.")

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select BIOS Dump File", "", "BIOS Files (*.bin *.rom *.fd);;All Files (*)"
        )
        if file_path:
            self.process_firmware(file_path)

    def process_firmware(self, file_path):
        self.selected_file_path = file_path
        file_name = os.path.basename(file_path)
        self.file_label.setText(f"Loaded: <b>{file_name}</b>")

        # Run Backend Diagnostic Analyzer
        try:
            analyzer = BIOSAnalyzer(file_path)
            report_text = analyzer.run_full_analysis()

            # Update Metadata Cards
            self.lbl_board.setText(analyzer.board_number)
            self.lbl_model.setText(analyzer.model_name)
            self.lbl_serial.setText(analyzer.serial_number)
            
            csme_state = analyzer.csme_info.get("CSME State", "Unknown")
            self.lbl_csme.setText(csme_state)

            # Update Main Text Report
            self.txt_report.setText(report_text)

        except Exception as e:
            QMessageBox.critical(self, "Analysis Error", f"File process karne mein error aaya:\n{str(e)}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.argv.append("")