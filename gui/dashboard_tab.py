# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : gui/dashboard_tab.py
# Author  : Safdar Ali
# =====================================================

"""
Single BIOS File Diagnostic Dashboard Tab.
Renders file selection, smooth progress bar updates,
quick metadata summary widgets, and full report outputs.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QGroupBox,
    QGridLayout,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt
from gui.worker import AnalysisWorker


class DashboardTab(QWidget):
    """
    Tab widget for loading and analyzing individual SPI BIOS binary dumps.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # ----------------------------------------------------
        # 1. FILE SELECTION BAR
        # ----------------------------------------------------
        file_box = QGroupBox("Select Target BIOS Binary (.bin / .rom / .fd)")
        file_layout = QHBoxLayout(file_box)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select or drop a BIOS dump file here...")
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)

        analyze_btn = QPushButton("Analyze BIOS")
        analyze_btn.setStyleSheet("font-weight: bold; background-color: #007ACC; color: white;")
        analyze_btn.clicked.connect(self.start_analysis)

        file_layout.addWidget(self.path_input)
        file_layout.addWidget(browse_btn)
        file_layout.addWidget(analyze_btn)
        layout.addWidget(file_box)

        # ----------------------------------------------------
        # 2. PROGRESS BAR & STATUS LABEL
        # ----------------------------------------------------
        progress_box = QGroupBox("Analysis Status")
        progress_layout = QVBoxLayout(progress_box)

        self.status_label = QLabel("Idle - Ready to load binary")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_box)

        # ----------------------------------------------------
        # 3. QUICK METADATA CARDS
        # ----------------------------------------------------
        cards_box = QGroupBox("Quick Hardware Metrics")
        cards_layout = QGridLayout(cards_box)

        self.lbl_size = QLabel("Flash Capacity: N/A")
        self.lbl_csme = QLabel("CSME Boot State: N/A")
        self.lbl_role = QLabel("Chip Role: N/A")
        self.lbl_dmi = QLabel("Service Tag / BID: N/A")
        self.lbl_dpk = QLabel("Windows Key: N/A")

        cards_layout.addWidget(self.lbl_size, 0, 0)
        cards_layout.addWidget(self.lbl_csme, 0, 1)
        cards_layout.addWidget(self.lbl_role, 1, 0)
        cards_layout.addWidget(self.lbl_dmi, 1, 1)
        cards_layout.addWidget(self.lbl_dpk, 2, 0)

        layout.addWidget(cards_box)

        # ----------------------------------------------------
        # 4. FULL ASCII REPORT VIEWER
        # ----------------------------------------------------
        report_box = QGroupBox("Full Diagnostic Report")
        report_layout = QVBoxLayout(report_box)

        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setFontFamily("Courier New")

        copy_btn = QPushButton("Copy Report to Clipboard")
        copy_btn.clicked.connect(self.copy_report)

        report_layout.addWidget(self.report_view)
        report_layout.addWidget(copy_btn)
        layout.addWidget(report_box)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select BIOS File", "", "BIOS Images (*.bin *.rom *.fd *.wph);;All Files (*)"
        )
        if file_path:
            self.path_input.setText(file_path)

    def start_analysis(self):
        file_path = self.path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Missing File", "Please select a BIOS binary file first.")
            return

        self.progress_bar.setValue(0)
        self.status_label.setText("Starting analysis...")

        # Instantiate worker thread
        self.worker = AnalysisWorker(primary_path=file_path, is_dual=False)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.status_signal.connect(self.status_label.setText)
        self.worker.result_signal.connect(self.on_analysis_complete)
        self.worker.error_signal.connect(self.on_analysis_error)
        self.worker.start()

    def on_analysis_complete(self, results: dict):
        fw = results.get("firmware")
        csme = results.get("csme", {})
        dmi = results.get("dmi", {})
        chip_role = results.get("chip_role", {})
        report_text = results.get("report_text", "")

        # Update Summary Cards
        if fw:
            self.lbl_size.setText(f"Flash Capacity: {fw.get_flash_label()}")

        self.lbl_csme.setText(f"CSME Boot State: {csme.get('state', 'N/A')}")
        self.lbl_role.setText(f"Chip Role: {chip_role.get('role', 'N/A')}")

        # Safe extraction for Dell Service Tag
        tag_data = dmi.get("dell_service_tag", {})
        tag_val = tag_data.get("value", "N/A") if isinstance(tag_data, dict) else str(tag_data)

        # Safely handle both string and dict formats for hp_bid
        hp_bid_data = dmi.get("hp_bid", "N/A")
        if isinstance(hp_bid_data, dict):
            bid_val = hp_bid_data.get("value", hp_bid_data.get("bid", "N/A"))
        else:
            bid_val = str(hp_bid_data)

        display_dmi = tag_val if tag_val not in ("Not Found", "N/A") else bid_val
        self.lbl_dmi.setText(f"Service Tag / BID: {display_dmi}")

        key_data = dmi.get("windows_dpk", {})
        key_val = key_data.get("value", "N/A") if isinstance(key_data, dict) else str(key_data)
        self.lbl_dpk.setText(f"Windows Key: {key_val}")

        # Update Text Report
        self.report_view.setText(report_text)

    def on_analysis_error(self, error_msg: str):
        QMessageBox.critical(self, "Analysis Failed", f"An error occurred during analysis:\n{error_msg}")
        self.status_label.setText("Analysis Failed")

    def copy_report(self):
        text = self.report_view.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Diagnostic report copied to clipboard.")