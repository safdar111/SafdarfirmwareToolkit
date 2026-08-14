# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : gui/dual_repair_tab.py
# Author  : Safdar Ali
# =====================================================

"""
Dual-BIOS Comparison & Automated Repair Tab.
Provides side-by-side loading of Corrupt and Donor images,
auto-matches Clean ME binaries from local database,
generates colorized delta plans, and executes 1-click repairs.
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
    QMessageBox,
)
import os
from gui.worker import AnalysisWorker
from core.repair_engine import RepairEngine
from core.search import CSMERepositorySearch


class DualRepairTab(QWidget):
    """
    Tab widget for comparing corrupt & donor BIOS dumps, auto-fetching database Clean ME,
    and executing patch repairs.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.dual_results = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # ----------------------------------------------------
        # 1. FILE SELECTION SLOTS
        # ----------------------------------------------------
        slots_layout = QHBoxLayout()

        # Slot A: Original (Corrupt) File
        slot_a_box = QGroupBox("1. Original / Corrupt BIOS File")
        slot_a_layout = QVBoxLayout(slot_a_box)
        self.orig_input = QLineEdit()
        self.orig_input.setPlaceholderText("Select Corrupt Dump...")
        browse_a_btn = QPushButton("Browse Original")
        browse_a_btn.clicked.connect(self.browse_original)
        slot_a_layout.addWidget(self.orig_input)
        slot_a_layout.addWidget(browse_a_btn)

        # Slot B: Donor File
        slot_b_box = QGroupBox("2. Known-Good Donor BIOS File")
        slot_b_layout = QVBoxLayout(slot_b_box)
        self.donor_input = QLineEdit()
        self.donor_input.setPlaceholderText("Select Donor Dump...")
        browse_b_btn = QPushButton("Browse Donor")
        browse_b_btn.clicked.connect(self.browse_donor)
        slot_b_layout.addWidget(self.donor_input)
        slot_b_layout.addWidget(browse_b_btn)

        slots_layout.addWidget(slot_a_box)
        slots_layout.addWidget(slot_b_box)
        layout.addLayout(slots_layout)

        # Slot C: Repository Clean ME File (Auto-Search or Manual)
        repo_me_box = QGroupBox("3. CSME Database Auto-Match / Repository File")
        repo_me_layout = QHBoxLayout(repo_me_box)
        self.clean_me_input = QLineEdit()
        self.clean_me_input.setPlaceholderText("Auto-matched from database or select manually...")

        auto_find_btn = QPushButton("Auto-Match DB")
        auto_find_btn.setStyleSheet("font-weight: bold; background-color: #17A2B8; color: white;")
        auto_find_btn.clicked.connect(self.auto_search_database)

        browse_c_btn = QPushButton("Browse Manual")
        browse_c_btn.clicked.connect(self.browse_clean_me)

        repo_me_layout.addWidget(self.clean_me_input)
        repo_me_layout.addWidget(auto_find_btn)
        repo_me_layout.addWidget(browse_c_btn)
        layout.addWidget(repo_me_box)

        # ----------------------------------------------------
        # 2. ACTION & PROGRESS BAR
        # ----------------------------------------------------
        action_box = QGroupBox("Comparison Engine")
        action_layout = QVBoxLayout(action_box)

        compare_btn = QPushButton("Compare & Analyze Dual BIOS")
        compare_btn.setStyleSheet("font-weight: bold; background-color: #007ACC; color: white; padding: 6px;")
        compare_btn.clicked.connect(self.start_dual_analysis)

        self.status_label = QLabel("Idle - Load files to perform comparison")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        action_layout.addWidget(compare_btn)
        action_layout.addWidget(self.status_label)
        action_layout.addWidget(self.progress_bar)
        layout.addWidget(action_box)

        # ----------------------------------------------------
        # 3. COLORIZED DIAGNOSTIC COMPARISON & REPAIR PLAN VIEWER
        # ----------------------------------------------------
        report_box = QGroupBox("Repair Diagnostic Plan")
        report_layout = QVBoxLayout(report_box)

        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setFontFamily("Courier New")

        report_layout.addWidget(self.report_view)
        layout.addWidget(report_box)

        # ----------------------------------------------------
        # 4. ONE-CLICK REPAIR WIZARD CONTROLS
        # ----------------------------------------------------
        repair_box = QGroupBox("Automated Repair Action")
        repair_layout = QHBoxLayout(repair_box)

        self.repair_btn = QPushButton("Execute Repair & Save OK File")
        self.repair_btn.setEnabled(False)
        self.repair_btn.setStyleSheet("font-weight: bold; background-color: #28A745; color: white; padding: 8px;")
        self.repair_btn.clicked.connect(self.execute_repair)

        repair_layout.addWidget(self.repair_btn)
        layout.addWidget(repair_box)

    def browse_original(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Original Corrupt BIOS File", "", "BIOS Images (*.bin *.rom *.fd);;All Files (*)"
        )
        if file_path:
            self.orig_input.setText(file_path)

    def browse_donor(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Donor BIOS File", "", "BIOS Images (*.bin *.rom *.fd);;All Files (*)"
        )
        if file_path:
            self.donor_input.setText(file_path)

    def browse_clean_me(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Clean CSME / ME Binary", "", "CSME/ME Images (*.bin *.rgn *.me);;All Files (*)"
        )
        if file_path:
            self.clean_me_input.setText(file_path)

    def auto_search_database(self):
        if not self.dual_results:
            QMessageBox.warning(self, "Run Analysis First", "Please run 'Compare & Analyze Dual BIOS' first so the CSME version is identified.")
            return

        version = self.dual_results.get("original", {}).get("csme", {}).get("version", "N/A")
        
        search_engine = CSMERepositorySearch()
        match_path = search_engine.find_matching_clean_me(version)

        if match_path:
            self.clean_me_input.setText(match_path)
            QMessageBox.information(
                self,
                "Database Match Found!",
                f"Found matching Clean CSME binary in database:\n\n{os.path.basename(match_path)}",
            )
        else:
            QMessageBox.warning(
                self,
                "No Match in Database",
                f"Could not find an exact Clean CSME file for version '{version}' in database/csme_repository/.\n\nPlease place the clean region binary into 'database/csme_repository/' folder.",
            )

    def start_dual_analysis(self):
        orig_path = self.orig_input.text().strip()
        donor_path = self.donor_input.text().strip()

        if not orig_path or not donor_path:
            QMessageBox.warning(self, "Missing Files", "Please select both Original and Donor files.")
            return

        self.progress_bar.setValue(0)
        self.status_label.setText("Starting dual comparison...")
        self.repair_btn.setEnabled(False)

        self.worker = AnalysisWorker(primary_path=orig_path, donor_path=donor_path, is_dual=True)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.status_signal.connect(self.status_label.setText)
        self.worker.result_signal.connect(self.on_dual_complete)
        self.worker.error_signal.connect(self.on_dual_error)
        self.worker.start()

    def on_dual_complete(self, results: dict):
        self.dual_results = results
        raw_report = results.get("report_text", "")
        compat = results.get("donor_compatibility", {})
        verdict = compat.get("verdict", "Not assessed")
        score = compat.get("score", 0)

        # Format report with HTML colors
        color_report = raw_report.replace("\n", "<br>")
        color_report = color_report.replace("INITIALIZED/DIRTY", "<span style='color: #FF5555; font-weight: bold;'>INITIALIZED/DIRTY</span>")
        color_report = color_report.replace("CRITICAL WARNING", "<span style='color: #FF5555; font-weight: bold;'>CRITICAL WARNING</span>")
        color_report = color_report.replace("Action:", "<span style='color: #50FA7B; font-weight: bold;'>Action:</span>")
        color_report = color_report.replace("Original DMI data found", "<span style='color: #F1FA8C; font-weight: bold;'>Original DMI data found</span>")
        color_report = color_report + f"<br><br><span style='color: #F1FA8C; font-weight: bold;'>Donor compatibility:</span> {verdict} ({score}/100)"

        self.report_view.setHtml(f"<pre style='color: #CCCCCC; font-size: 13px;'>{color_report}</pre>")
        self.repair_btn.setEnabled(True)

    def on_dual_error(self, error_msg: str):
        QMessageBox.critical(self, "Comparison Failed", f"Dual file analysis failed:\n{error_msg}")
        self.status_label.setText("Dual Analysis Failed")

    def execute_repair(self):
        orig_path = self.orig_input.text().strip()
        donor_path = self.donor_input.text().strip()
        clean_me_path = self.clean_me_input.text().strip()

        if not orig_path or not donor_path:
            return

        default_out = os.path.splitext(orig_path)[0] + "_REPAIRED_OK.bin"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Repaired BIOS Binary", default_out, "BIOS Images (*.bin)"
        )

        if not save_path:
            return

        engine = RepairEngine(
            original_path=orig_path,
            donor_path=donor_path,
            clean_me_path=clean_me_path if clean_me_path else None
        )
        
        res = engine.clean_csme(save_path)

        if res.get("success"):
            QMessageBox.information(
                self,
                "Repair Successful",
                f"{res.get('message')}\n\nRepaired file is verified and ready to flash onto the target BIOS chip!",
            )
        else:
            QMessageBox.warning(self, "Repair Warning", res.get("message", "Patching failed."))