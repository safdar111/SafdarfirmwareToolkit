# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.5.0 (Workshop UI Upgrade)
# File      : gui/dual_repair_tab.py
# Author    : Safdar Ali
# =====================================================

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QProgressBar, QTextEdit, QFileDialog, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from gui.worker import AnalysisWorker, RepairWorker
from core.repair_engine import RepairEngine
from core.search import CSMERepositorySearch

class DualRepairTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.repair_worker = None
        self.dual_results = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ---------------------------------------------------------
        # 1. FILE SLOTS (BLUE THEME)
        # ---------------------------------------------------------
        slots_layout = QHBoxLayout()

        slot_a_box = QGroupBox("1. Original / Corrupt BIOS")
        slot_a_box.setStyleSheet("QGroupBox { border: 1px solid #007ACC; color: #007ACC; }")
        slot_a_layout = QVBoxLayout(slot_a_box)
        
        self.orig_input = QLineEdit()
        self.orig_input.setPlaceholderText("Select Corrupt Dump...")
        self.orig_input.setStyleSheet("background-color: #2D2D30; color: #E0E0E0; padding: 5px;")
        
        browse_a_btn = QPushButton("Browse Original")
        browse_a_btn.clicked.connect(lambda: self.browse_file(self.orig_input))
        
        slot_a_layout.addWidget(self.orig_input)
        slot_a_layout.addWidget(browse_a_btn)

        slot_b_box = QGroupBox("2. Known-Good Donor BIOS")
        slot_b_box.setStyleSheet("QGroupBox { border: 1px solid #007ACC; color: #007ACC; }")
        slot_b_layout = QVBoxLayout(slot_b_box)
        
        self.donor_input = QLineEdit()
        self.donor_input.setPlaceholderText("Select Donor Dump...")
        self.donor_input.setStyleSheet("background-color: #2D2D30; color: #E0E0E0; padding: 5px;")
        
        browse_b_btn = QPushButton("Browse Donor")
        browse_b_btn.clicked.connect(lambda: self.browse_file(self.donor_input))
        
        slot_b_layout.addWidget(self.donor_input)
        slot_b_layout.addWidget(browse_b_btn)

        slots_layout.addWidget(slot_a_box)
        slots_layout.addWidget(slot_b_box)
        layout.addLayout(slots_layout)

        # ---------------------------------------------------------
        # 2. CSME DATABASE (GOLD THEME)
        # ---------------------------------------------------------
        repo_me_box = QGroupBox("3. CSME Database Auto-Match / Clean ME")
        repo_me_box.setStyleSheet("QGroupBox { border: 1px solid #D69D30; color: #D69D30; }")
        repo_me_layout = QHBoxLayout(repo_me_box)
        
        self.clean_me_input = QLineEdit()
        self.clean_me_input.setPlaceholderText("Auto-matched from database or manually selected...")
        self.clean_me_input.setStyleSheet("background-color: #2D2D30; color: #E0E0E0; padding: 5px;")
        
        auto_find_btn = QPushButton("Auto-Match DB")
        auto_find_btn.setStyleSheet("""
            QPushButton { background-color: #D69D30; color: #1E1E1E; font-weight: bold; }
            QPushButton:hover { background-color: #E8B44F; }
        """)
        auto_find_btn.clicked.connect(self.auto_search_database)
        
        browse_c_btn = QPushButton("Browse Manual")
        browse_c_btn.clicked.connect(lambda: self.browse_file(self.clean_me_input))
        
        repo_me_layout.addWidget(self.clean_me_input)
        repo_me_layout.addWidget(auto_find_btn)
        repo_me_layout.addWidget(browse_c_btn)
        layout.addWidget(repo_me_box)

        # ---------------------------------------------------------
        # 3. ACTION & PROGRESS (CYAN THEME)
        # ---------------------------------------------------------
        action_box = QGroupBox("4. Comparison Engine")
        action_box.setStyleSheet("QGroupBox { border: 1px solid #00BCD4; color: #00BCD4; }")
        action_layout = QVBoxLayout(action_box)
        
        compare_btn = QPushButton("Compare & Analyze Dual BIOS")
        compare_btn.setStyleSheet("""
            QPushButton { background-color: #00BCD4; color: #1E1E1E; font-weight: bold; font-size: 14px; padding: 10px; }
            QPushButton:hover { background-color: #26C6DA; }
        """)
        compare_btn.clicked.connect(self.start_dual_analysis)
        
        self.status_label = QLabel("Idle - Load files to perform comparison")
        self.status_label.setStyleSheet("color: #00BCD4; font-weight: bold;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #444; border-radius: 4px; text-align: center; color: white; font-weight: bold; }
            QProgressBar::chunk { background-color: #00BCD4; border-radius: 3px; }
        """)
        
        action_layout.addWidget(compare_btn)
        action_layout.addWidget(self.status_label)
        action_layout.addWidget(self.progress_bar)
        layout.addWidget(action_box)

        # ---------------------------------------------------------
        # 4. REPORT VIEWER (TERMINAL THEME)
        # ---------------------------------------------------------
        report_box = QGroupBox("Repair Diagnostic Plan")
        report_layout = QVBoxLayout(report_box)
        
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setFontFamily("Consolas")
        self.report_view.setStyleSheet("""
            QTextEdit {
                background-color: #0C0C0C; 
                color: #00FF00; 
                border: 1px solid #333333; 
                font-size: 13px;
                padding: 8px;
            }
        """)
        report_layout.addWidget(self.report_view)
        layout.addWidget(report_box)

        # ---------------------------------------------------------
        # 5. REPAIR BUTTONS (CUSTOM COLORS)
        # ---------------------------------------------------------
        repair_box = QGroupBox("5. Automated Repair Actions")
        repair_layout = QHBoxLayout(repair_box)
        
        self.repair_csme_btn = QPushButton("Inject Clean CSME")
        self.repair_csme_btn.setEnabled(False)
        self.repair_csme_btn.setStyleSheet("""
            QPushButton:enabled { background-color: #007ACC; color: white; font-weight: bold; padding: 8px; }
            QPushButton:enabled:hover { background-color: #0098FF; }
        """)
        self.repair_csme_btn.clicked.connect(lambda: self.execute_repair("csme"))
        
        self.transfer_dmi_btn = QPushButton("Transfer DMI to Donor")
        self.transfer_dmi_btn.setEnabled(False)
        self.transfer_dmi_btn.setStyleSheet("""
            QPushButton:enabled { background-color: #9B59B6; color: white; font-weight: bold; padding: 8px; }
            QPushButton:enabled:hover { background-color: #AF7AC5; }
        """)
        self.transfer_dmi_btn.clicked.connect(lambda: self.execute_repair("dmi"))
        
        self.frank_btn = QPushButton("Build Frankenstein BIOS (Pro)")
        self.frank_btn.setEnabled(False)
        self.frank_btn.setStyleSheet("""
            QPushButton:enabled { background-color: #28A745; color: white; font-weight: bold; padding: 12px; font-size: 13px; }
            QPushButton:enabled:hover { background-color: #34CE57; }
        """)
        self.frank_btn.clicked.connect(lambda: self.execute_repair("frankenstein"))

        repair_layout.addWidget(self.repair_csme_btn)
        repair_layout.addWidget(self.transfer_dmi_btn)
        repair_layout.addWidget(self.frank_btn)
        layout.addWidget(repair_box)

    # =========================================================
    # CORE FUNCTIONS
    # =========================================================

    def browse_file(self, target_input):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Binary", "", "BIOS Images (*.bin *.rom *.fd);;All Files (*)")
        if file_path:
            target_input.setText(file_path)

    def auto_search_database(self):
        if not self.dual_results:
            QMessageBox.warning(self, "Analysis Needed", "Run Compare & Analyze first.")
            return

        version = self.dual_results.get("original", {}).get("csme", {}).get("version", "N/A")
        sku = self.dual_results.get("original", {}).get("csme", {}).get("sku", "Unknown")
        
        match_path = CSMERepositorySearch().find_matching_clean_me(version, sku)
        if match_path:
            self.clean_me_input.setText(match_path)
            QMessageBox.information(self, "Match Found!", f"Found Clean ME:\n{os.path.basename(match_path)}")
        else:
            QMessageBox.warning(self, "No Match", f"No exact match found for {version} ({sku}).")

    def start_dual_analysis(self):
        orig = self.orig_input.text().strip()
        donor = self.donor_input.text().strip()
        if not orig or not donor:
            QMessageBox.warning(self, "Files Missing", "Select Original and Donor files.")
            return

        self.progress_bar.setValue(0)
        self.status_label.setText("Starting dual comparison...")
        self.status_label.setStyleSheet("color: #00BCD4; font-weight: bold;")
        self.repair_csme_btn.setEnabled(False)
        self.transfer_dmi_btn.setEnabled(False)
        self.frank_btn.setEnabled(False)

        self.worker = AnalysisWorker(primary_path=orig, donor_path=donor, is_dual=True)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.status_signal.connect(self.status_label.setText)
        self.worker.result_signal.connect(self.on_dual_complete)
        self.worker.error_signal.connect(self.on_dual_error)
        self.worker.start()

    def on_dual_complete(self, results: dict):
        self.dual_results = results
        self.report_view.setText(results.get("report_text", "Analysis generated no text."))
        self.status_label.setText("Comparison Complete. Ready for repair.")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        self.repair_csme_btn.setEnabled(True)
        self.transfer_dmi_btn.setEnabled(True)
        self.frank_btn.setEnabled(True)

    def on_dual_error(self, err: str):
        QMessageBox.critical(self, "Error", f"Analysis failed: {err}")
        self.status_label.setText("Analysis Failed")
        self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")

    def execute_repair(self, mode: str):
        orig = self.orig_input.text().strip()
        donor = self.donor_input.text().strip()
        clean = self.clean_me_input.text().strip()

        if mode == "frankenstein" and (not donor or not clean):
            QMessageBox.warning(self, "Files Missing", "Frankenstein rebuild requires both Donor and Clean ME.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Repaired BIOS", f"Repaired_{mode.upper()}.bin", "BIOS Images (*.bin)")
        if not save_path:
            return

        self.progress_bar.setValue(0)
        self.status_label.setText(f"Executing {mode.upper()} repair...")
        self.status_label.setStyleSheet("color: #FFEB3B; font-weight: bold;")
        
        engine = RepairEngine(original_path=orig, donor_path=donor, clean_me_path=clean if clean else None)
        
        dmi_start = None
        dmi_size = None
        
        if mode == "dmi" and self.dual_results:
            dmi_info = self.dual_results.get("original", {}).get("dmi", {})
            dmi_start = dmi_info.get("offset")
            dmi_size = dmi_info.get("size")
            
            if dmi_start and dmi_size:
                print(f"[+] Auto-detected DMI Block -> Offset: {hex(dmi_start)}, Size: {hex(dmi_size)}")
            else:
                print("[-] Warning: Exact DMI boundaries not found in auto-scan, falling back to signature search.")

        self.repair_worker = RepairWorker(mode, engine, save_path, dmi_start, dmi_size)
        self.repair_worker.progress_signal.connect(self.progress_bar.setValue)
        self.repair_worker.status_signal.connect(self.status_label.setText)
        self.repair_worker.result_signal.connect(self.on_repair_complete)
        self.repair_worker.error_signal.connect(self.on_dual_error)
        self.repair_worker.start()
        
    def on_repair_complete(self, res: dict):
        if res.get("success"):
            self.status_label.setText("Repair Successful!")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            QMessageBox.information(self, "Success", f"{res.get('message')}\n\nReady to flash!")
        else:
            self.status_label.setText("Repair Failed")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            QMessageBox.warning(self, "Warning", res.get("message", "Repair failed."))