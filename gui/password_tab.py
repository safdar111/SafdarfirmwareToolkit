# =====================================================
# Safdar Firmware Toolkit Pro
# File      : gui/password_tab.py
# Author    : Safdar Ali
# Purpose   : BIOS Password Removal & NVRAM Patching Wizard
# =====================================================

import os
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QFileDialog, QGroupBox, QTextEdit, QMessageBox, QComboBox
)
from core.password_engine import PasswordRemovalEngine
from core.dell_modern_patcher import DellModernPasswordPatcher  
from core.hp_modern_patcher import HPModernPasswordPatcher

class PasswordRemovalTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title_label = QLabel("<b>Universal BIOS Password Removal Tool (Dell, HP, Lenovo)</b>")
        title_label.setStyleSheet("color: #E91E63; font-size: 14px;")
        layout.addWidget(title_label)

        # Brand Selector Box
        brand_box = QGroupBox("1. Target Configuration & Brand")
        brand_box.setStyleSheet("QGroupBox { border: 1px solid #E91E63; color: #E91E63; font-weight: bold; }")
        brand_layout = QHBoxLayout(brand_box)
        
        self.brand_combo = QComboBox()
        self.brand_combo.addItems(["Dell", "Lenovo", "HP"])
        self.brand_combo.setStyleSheet("background-color: #2D2D30; color: #E0E0E0; padding: 5px;")
        
        brand_layout.addWidget(QLabel("Select Brand:"))
        brand_layout.addWidget(self.brand_combo)
        layout.addWidget(brand_box)

        # File Selection Box
        file_box = QGroupBox("2. Select BIOS Binary for Analysis")
        file_box.setStyleSheet("QGroupBox { border: 1px solid #E91E63; color: #E91E63; font-weight: bold; }")
        file_layout = QHBoxLayout(file_box)
        
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select BIOS dump (.bin / .rom)...")
        self.file_input.setReadOnly(True)
        self.file_input.setStyleSheet("background-color: #2D2D30; color: #E0E0E0; padding: 5px;")
        
        btn_browse = QPushButton("Browse BIOS")
        btn_browse.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(btn_browse)
        layout.addWidget(file_box)

        # Diagnostic Log / Terminal Area
        log_box = QGroupBox("Password Analysis & HxD Comparison Log")
        log_box.setStyleSheet("QGroupBox { border: 1px solid #E91E63; color: #E91E63; font-weight: bold; }")
        log_layout = QVBoxLayout(log_box)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFontFamily("Consolas")
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color: #0C0C0C; 
                color: #4CAF50; 
                border: 1px solid #333333; 
                font-size: 12px;
                padding: 8px;
            }
        """)
        self.log_view.setText("[*] Engine ready. Load a BIOS binary to scan password flags.")
        log_layout.addWidget(self.log_view)
        layout.addWidget(log_box)

        # Execute Button
        self.btn_execute = QPushButton("Scan & Remove Password (if found)")
        self.btn_execute.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F; 
                color: white; 
                font-weight: bold; 
                padding: 10px; 
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
        """)
        self.btn_execute.clicked.connect(self.run_removal)
        layout.addWidget(self.btn_execute)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select BIOS Binary", "", "BIOS Files (*.bin *.rom *.fd)")
        if path:
            self.file_input.setText(path)
            file_size = os.path.getsize(path)
            self.log_view.append(f"\n[+] Loaded File: {os.path.basename(path)}")
            self.log_view.append(f"[+] File Size: {hex(file_size)} ({file_size / 1024 / 1024:.2f} MB)")

    def run_removal(self):
        file_path = self.file_input.text()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "Please select a valid BIOS file first.")
            return

        brand = self.brand_combo.currentText()
        self.log_view.append(f"\n[~] Scanning {brand} BIOS for password markers...")

        default_name = f"Patched_{os.path.basename(file_path)}"
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Output File for HxD Comparison", default_name, "BIOS Files (*.bin *.rom)")
        if not save_path:
            return

        try:
            shutil.copy(file_path, save_path)

            # Route execution based on selected brand
            if brand == "Dell":
                patcher = DellModernPasswordPatcher(save_path)
                status, message = patcher.auto_scan_and_remove()
                success = (status == "Success")
                if status == "Clean":
                    message = "No active Dell password flags detected. File is already clean."

            elif brand == "HP":
                patcher = HPModernPasswordPatcher(save_path)
                status, message = patcher.auto_scan_and_remove()
                success = (status == "Success")
                if status == "Clean":
                    message = "No active HP password flags detected. File is already clean."

            else:
                # Fallback for Lenovo or legacy models
                engine = PasswordRemovalEngine(save_path, brand)
                success, message = engine.process_removal()

            if success:
                self.log_view.append(f"[SUCCESS] {message}")
                self.log_view.append(f"[+] Password flags cleared successfully!")
                self.log_view.append(f"[+] Output saved to: {save_path}")
                self.log_view.append(f"[i] TIP: Open both files in HxD to inspect modified bytes.")
                QMessageBox.information(self, "Success", f"{message}\n\nFile is ready for HxD comparison:\n{save_path}")
            else:
                self.log_view.append(f"[-] Scan Result: {message}")
                self.log_view.append(f"[-] No password/flags cleared. Original file is clean.")
                if os.path.exists(save_path):
                    os.remove(save_path)
                QMessageBox.information(self, "Analysis Result", message)

        except Exception as e:
            self.log_view.append(f"[-] Exception Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            if os.path.exists(save_path):
                os.remove(save_path)