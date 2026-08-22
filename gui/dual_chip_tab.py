# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.5.0 (Workshop Grade)
# File      : gui/dual_chip_tab.py
# Author    : Safdar Ali
# =====================================================

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QFileDialog, QGroupBox, QMessageBox
)
from core.dual_chip_handler import DualChipHandler

class DualChipTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.handler = DualChipHandler()
        self.cached_split_point = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # ---------------------------------------------------------
        # 1. MERGE OPERATIONS (PURPLE THEME)
        # ---------------------------------------------------------
        merge_box = QGroupBox("1. Merge Dual Chips (Create Single Logical Drive)")
        merge_box.setStyleSheet("QGroupBox { border: 1px solid #9B59B6; color: #9B59B6; }")
        merge_layout = QVBoxLayout(merge_box)

        # Chip 1 Input
        row1 = QHBoxLayout()
        self.chip1_input = QLineEdit()
        self.chip1_input.setPlaceholderText("Select Chip 1 (Main / Larger Chip)...")
        self.chip1_input.setStyleSheet("background-color: #2D2D30; color: #E0E0E0;")
        btn_chip1 = QPushButton("Browse Chip 1")
        btn_chip1.clicked.connect(lambda: self.browse_file(self.chip1_input))
        row1.addWidget(self.chip1_input)
        row1.addWidget(btn_chip1)

        # Chip 2 Input
        row2 = QHBoxLayout()
        self.chip2_input = QLineEdit()
        self.chip2_input.setPlaceholderText("Select Chip 2 (Sub / EC / Smaller Chip)...")
        self.chip2_input.setStyleSheet("background-color: #2D2D30; color: #E0E0E0;")
        btn_chip2 = QPushButton("Browse Chip 2")
        btn_chip2.clicked.connect(lambda: self.browse_file(self.chip2_input))
        row2.addWidget(self.chip2_input)
        row2.addWidget(btn_chip2)

        # Merge Action
        btn_merge = QPushButton("Merge Chips for Analysis")
        btn_merge.setStyleSheet("""
            QPushButton { background-color: #9B59B6; color: white; font-weight: bold; padding: 10px; }
            QPushButton:hover { background-color: #AF7AC5; }
        """)
        btn_merge.clicked.connect(self.execute_merge)

        merge_layout.addLayout(row1)
        merge_layout.addLayout(row2)
        merge_layout.addWidget(btn_merge)
        layout.addWidget(merge_box)

        # ---------------------------------------------------------
        # 2. SPLIT OPERATIONS (ORANGE THEME)
        # ---------------------------------------------------------
        split_box = QGroupBox("2. Split Repaired File (Slice for Hardware Flashing)")
        split_box.setStyleSheet("QGroupBox { border: 1px solid #E67E22; color: #E67E22; }")
        split_layout = QVBoxLayout(split_box)

        # Repaired File Input
        row3 = QHBoxLayout()
        self.repaired_input = QLineEdit()
        self.repaired_input.setPlaceholderText("Select the successfully repaired Merged BIOS...")
        self.repaired_input.setStyleSheet("background-color: #2D2D30; color: #E0E0E0;")
        btn_repaired = QPushButton("Browse Repaired")
        btn_repaired.clicked.connect(lambda: self.browse_file(self.repaired_input))
        row3.addWidget(self.repaired_input)
        row3.addWidget(btn_repaired)

        # Split Point Info
        self.lbl_split_point = QLabel("Split Point: Not Set (Merge chips first to auto-calculate)")
        self.lbl_split_point.setStyleSheet("color: #CCCCCC; font-style: italic;")

        # Split Action
        btn_split = QPushButton("Slice into Two Flashable Binaries")
        btn_split.setStyleSheet("""
            QPushButton { background-color: #E67E22; color: white; font-weight: bold; padding: 10px; }
            QPushButton:hover { background-color: #F39C12; }
        """)
        btn_split.clicked.connect(self.execute_split)

        split_layout.addLayout(row3)
        split_layout.addWidget(self.lbl_split_point)
        split_layout.addWidget(btn_split)
        layout.addWidget(split_box)

        layout.addStretch()

    def browse_file(self, target_input):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Binary", "", "BIOS Images (*.bin *.rom *.fd);;All Files (*)")
        if file_path:
            target_input.setText(file_path)

    def execute_merge(self):
        c1 = self.chip1_input.text().strip()
        c2 = self.chip2_input.text().strip()

        if not c1 or not c2:
            QMessageBox.warning(self, "Missing Files", "Please select both Chip 1 and Chip 2.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged File", "Merged_Dual_BIOS.bin", "BIOS Images (*.bin)")
        if not save_path:
            return

        res = self.handler.merge_chips(c1, c2, save_path)
        if res.get("success"):
            self.cached_split_point = res.get("chip1_original_size", 0)
            self.lbl_split_point.setText(f"Split Point: {self.cached_split_point} Bytes (Auto-Calculated)")
            self.lbl_split_point.setStyleSheet("color: #4CAF50; font-weight: bold;")
            QMessageBox.information(self, "Success", f"Chips merged successfully!\n\nYou can now load this merged file into the Single or Dual repair tabs.")
        else:
            QMessageBox.critical(self, "Error", res.get("message", "Merge failed."))

    def execute_split(self):
        repaired = self.repaired_input.text().strip()
        if not repaired:
            QMessageBox.warning(self, "Missing File", "Please select the repaired merged file to split.")
            return

        if self.cached_split_point <= 0:
            QMessageBox.warning(self, "No Split Point", "Split point is unknown. You must merge the original files in this session first so the software knows exactly where to cut.")
            return

        out_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder for Split Chips")
        if not out_dir:
            return

        base_name = os.path.basename(repaired).replace(".bin", "")
        out1 = os.path.join(out_dir, f"{base_name}_Repaired_Chip1.bin")
        out2 = os.path.join(out_dir, f"{base_name}_Repaired_Chip2.bin")

        res = self.handler.split_chips(repaired, self.cached_split_point, out1, out2)
        if res.get("success"):
            QMessageBox.information(self, "Success", f"Repaired file successfully sliced!\n\nReady to flash:\n1. {os.path.basename(out1)}\n2. {os.path.basename(out2)}")
        else:
            QMessageBox.critical(self, "Error", res.get("message", "Split failed."))