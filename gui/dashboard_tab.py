# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.5.0 (Workshop UI Upgrade)
# File      : gui/dashboard_tab.py
# Author    : Safdar Ali
# =====================================================

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QProgressBar, QTextEdit, QFileDialog, QGroupBox,
    QGridLayout, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from gui.worker import AnalysisWorker

class DashboardTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._last_results = None
        self._last_file = None
        self.csme_database_path = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # ---------------------------------------------------------
        # 1. LOCAL CSME DATABASE (NEW FOLDER BROWSER)
        # ---------------------------------------------------------
        db_box = QGroupBox("1. Connect Local CSME Database")
        db_box.setStyleSheet("QGroupBox { border: 1px solid #D69D30; color: #D69D30; }")
        db_layout = QHBoxLayout(db_box)
        
        self.db_path_input = QLineEdit()
        self.db_path_input.setPlaceholderText("Select the folder containing your clean .rgn / .bin ME files...")
        self.db_path_input.setReadOnly(True)
        self.db_path_input.setStyleSheet("background-color: #2D2D30; color: #E0E0E0;")
        
        browse_db_btn = QPushButton("Browse Database Folder...")
        browse_db_btn.setStyleSheet("""
            QPushButton { background-color: #D69D30; color: #1E1E1E; font-weight: bold; }
            QPushButton:hover { background-color: #E8B44F; }
        """)
        browse_db_btn.clicked.connect(self.browse_csme_db)

        db_layout.addWidget(self.db_path_input)
        db_layout.addWidget(browse_db_btn)
        layout.addWidget(db_box)

        # ---------------------------------------------------------
        # 2. FILE SELECTION
        # ---------------------------------------------------------
        file_box = QGroupBox("2. Select Target BIOS Binary (.bin / .rom / .fd)")
        file_layout = QHBoxLayout(file_box)
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select or drop a corrupted BIOS dump file here...")
        
        browse_btn = QPushButton("Browse File...")
        browse_btn.clicked.connect(self.browse_file)
        
        analyze_btn = QPushButton("Analyze BIOS")
        analyze_btn.setStyleSheet("""
            QPushButton { background-color: #007ACC; color: white; font-weight: bold; font-size: 14px; padding: 10px; }
            QPushButton:hover { background-color: #0098FF; }
        """)
        analyze_btn.clicked.connect(self.start_analysis)

        file_layout.addWidget(self.path_input)
        file_layout.addWidget(browse_btn)
        file_layout.addWidget(analyze_btn)
        layout.addWidget(file_box)

        # ---------------------------------------------------------
        # 3. PROGRESS BAR & STATUS
        # ---------------------------------------------------------
        progress_box = QGroupBox("Analysis Status")
        progress_layout = QVBoxLayout(progress_box)
        self.status_label = QLabel("Idle - Ready to load binary")
        self.status_label.setStyleSheet("color: #00BCD4; font-weight: bold;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #444; border-radius: 4px; text-align: center; color: white; font-weight: bold; }
            QProgressBar::chunk { background-color: #00BCD4; border-radius: 3px; }
        """)
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_box)

        # ---------------------------------------------------------
        # 4. COLOR-CODED METADATA CARDS
        # ---------------------------------------------------------
        cards_box = QGroupBox("Quick Hardware Metrics (Color Coded)")
        cards_layout = QGridLayout(cards_box)
        
        # Initialize with Rich Text formatting
        self.lbl_size = QLabel("<b>Flash Capacity:</b> N/A")
        self.lbl_csme = QLabel("<b>CSME Boot State:</b> N/A")
        self.lbl_role = QLabel("<b>Chip Role:</b> N/A")
        self.lbl_dmi =  QLabel("<b>Service Tag / BID:</b> N/A")
        self.lbl_dpk =  QLabel("<b>Windows Key:</b> N/A")
        self.lbl_mac =  QLabel("<b>MAC Address:</b> N/A")

        cards_layout.addWidget(self.lbl_size, 0, 0)
        cards_layout.addWidget(self.lbl_csme, 0, 1)
        cards_layout.addWidget(self.lbl_role, 1, 0)
        cards_layout.addWidget(self.lbl_dmi,  1, 1)
        cards_layout.addWidget(self.lbl_dpk,  2, 0)
        cards_layout.addWidget(self.lbl_mac,  2, 1)
        layout.addWidget(cards_box)

        # ---------------------------------------------------------
        # 5. TERMINAL REPORT VIEWER
        # ---------------------------------------------------------
        report_box = QGroupBox("Deep Diagnostic Terminal")
        report_layout = QVBoxLayout(report_box)
        
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setFontFamily("Consolas")
        # Hacker/Terminal visual style for the report
        self.report_view.setStyleSheet("""
            QTextEdit {
                background-color: #0C0C0C; 
                color: #00FF00; 
                border: 1px solid #333333; 
                font-size: 13px;
                padding: 8px;
            }
        """)

        btn_row = QHBoxLayout()
        copy_btn = QPushButton("Copy Report")
        copy_btn.clicked.connect(self.copy_report)
        
        self.save_ok_btn = QPushButton("Save Repaired (Archive)")
        self.save_ok_btn.clicked.connect(self.save_ok)
        self.save_ok_btn.setEnabled(False)

        btn_row.addWidget(copy_btn)
        btn_row.addWidget(self.save_ok_btn)
        report_layout.addWidget(self.report_view)
        report_layout.addLayout(btn_row)
        layout.addWidget(report_box)

    # =========================================================
    # CORE FUNCTIONS
    # =========================================================

    def browse_csme_db(self):
        """Opens folder browser for the local CSME repository."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select CSME Database Folder", "")
        if folder_path:
            self.csme_database_path = folder_path
            self.db_path_input.setText(folder_path)
            QMessageBox.information(self, "Database Linked", f"Local Database Successfully Linked:\n{folder_path}")

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select BIOS File", "", "BIOS Images (*.bin *.rom *.fd);;All Files (*)")
        if file_path:
            self.path_input.setText(file_path)

    def start_analysis(self):
        file_path = self.path_input.text().strip()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Missing File", "Please select a valid BIOS binary file.")
            return

        self.progress_bar.setValue(0)
        self.status_label.setText("Extracting hexadecimal architecture...")
        
        self.worker = AnalysisWorker(primary_path=file_path, is_dual=False)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.status_signal.connect(self.status_label.setText)
        self.worker.result_signal.connect(self.on_analysis_complete)
        self.worker.error_signal.connect(self.on_analysis_error)
        self.worker.start()

    def set_rich_label(self, label_widget, title, value, status="neutral"):
        """Helper to inject color-coded HTML into the metadata labels."""
        color = "#CCCCCC" # Default Grey
        if status == "good": color = "#4CAF50"    # Bright Green
        elif status == "bad": color = "#F44336"   # Bright Red
        elif status == "alert": color = "#FFEB3B" # Yellow
        
        label_widget.setText(f"<span style='color:#888888;'><b>{title}:</b></span> <span style='color:{color}; font-weight:bold;'>{value}</span>")

    def on_analysis_complete(self, results: dict):
        self._last_results = results
        self._last_file = self.path_input.text().strip()

        fw = results.get("firmware")
        csme = results.get("csme", {})
        dmi = results.get("dmi", {})
        chip_role = results.get("chip_role", {})
        
        # Update Size & Role
        if fw:
            self.set_rich_label(self.lbl_size, "Flash Capacity", fw.get_flash_label(), "neutral")
        self.set_rich_label(self.lbl_role, "Chip Role", chip_role.get('role', 'N/A'), "neutral")

        # Color-Code CSME State
        csme_state = csme.get('state', 'N/A')
        csme_status = "neutral"
        if "Corrupted" in csme_state or "Error" in csme_state:
            csme_status = "bad"
        elif "Clean" in csme_state or "Configured" in csme_state:
            csme_status = "good"
        self.set_rich_label(self.lbl_csme, "CSME Boot State", csme_state, csme_status)
        
        # Color-Code DMI Data (Red if Missing, Green if Found)
        tag_val = dmi.get("dell_service_tag", {}).get("value", "N/A")
        bid_val = dmi.get("hp_bid", "N/A")
        final_dmi = tag_val if tag_val not in ('Not Found', 'N/A') else bid_val
        self.set_rich_label(self.lbl_dmi, "Service Tag / BID", final_dmi, "bad" if final_dmi == "N/A" else "good")
        
        dpk_val = dmi.get('windows_dpk', {}).get('value', 'N/A')
        self.set_rich_label(self.lbl_dpk, "Windows Key", dpk_val, "bad" if dpk_val == "N/A" else "good")
        
        mac_val = dmi.get('mac_address', 'N/A')
        self.set_rich_label(self.lbl_mac, "MAC Address", mac_val, "bad" if mac_val == "N/A" else "good")

        # Load terminal text
        self.report_view.setText(results.get("report_text", ""))

        # Save Button Logic
        is_ok = results.get("health", {}).get("archive_ready", False)
        if is_ok:
            self.save_ok_btn.setEnabled(True)
            self.save_ok_btn.setStyleSheet("""
                QPushButton { background-color: #0F6B3B; color: white; font-weight: bold; }
                QPushButton:hover { background-color: #158C4E; }
            """)
        else:
            self.save_ok_btn.setEnabled(False)
            self.save_ok_btn.setStyleSheet("")

    def on_analysis_error(self, error_msg: str):
        QMessageBox.critical(self, "Analysis Failed", f"An error occurred:\n{error_msg}")
        self.status_label.setText("Analysis Failed")
        self.status_label.setStyleSheet("color: #F44336; font-weight: bold;") # Turn red on error

    def copy_report(self):
        QApplication.clipboard().setText(self.report_view.toPlainText())
        QMessageBox.information(self, "Copied", "Diagnostic terminal text copied to clipboard.")

    def save_ok(self):
        if not self._last_results or not self._last_file:
            return
        
        try:
            from core.analyzer import Analyzer
            analyzer = Analyzer(self._last_file)
            out_dir = os.path.join(os.getcwd(), "database", "Repaired_Outputs")
            saved = analyzer.save_ok_report(self.report_view.toPlainText(), output_dir=out_dir)
            if saved:
                QMessageBox.information(self, "Saved", f"Successfully Archived!\nFolder: {out_dir}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save: {e}")