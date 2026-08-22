# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.5.0 (Dynamic Workshop Engine)
# File      : gui/worker.py
# Author    : Safdar Ali
# =====================================================

"""
Background Threading Worker Module (PyQt6).
Runs heavy binary analysis, forensic hex-hunting, & surgical repair tasks 
asynchronously to keep the UI smooth, responsive, and crash-free during heavy I/O.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from core.analyzer import Analyzer
from core.repair_engine import RepairEngine


class AnalysisWorker(QThread):
    """
    Background worker thread for single and dual BIOS file analysis.
    Emits progress signals (0-100%), status messages, and result dictionaries.
    """

    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, primary_path: str, donor_path: str = None, is_dual: bool = False):
        super().__init__()
        self.primary_path = primary_path
        self.donor_path = donor_path
        self.is_dual = is_dual

    def run(self):
        try:
            self.status_signal.emit("Initializing Advanced Heuristics Engine...")
            self.progress_signal.emit(10)

            analyzer = Analyzer(self.primary_path, self.donor_path)

            if not self.is_dual:
                self.status_signal.emit("Scanning Flash Descriptor, CSME Partition, & NVRAM...")
                self.progress_signal.emit(35)

                self.status_signal.emit("Hunting exact hex boundaries for MSDM & BitLocker signatures...")
                self.progress_signal.emit(65)

                results = analyzer.analyze_single()

                self.status_signal.emit("Diagnostic Scan Complete!")
                self.progress_signal.emit(100)
                self.result_signal.emit(results)

            else:
                self.status_signal.emit("Analyzing Corrupt & Donor Binaries...")
                self.progress_signal.emit(40)

                self.status_signal.emit("Comparing CSME Versions & validating Frankenstein safety...")
                self.progress_signal.emit(75)

                results = analyzer.analyze_dual()

                self.status_signal.emit("Dual Analysis Complete!")
                self.progress_signal.emit(100)
                self.result_signal.emit(results)

        except Exception as e:
            self.error_signal.emit(f"Analysis Thread Error: {str(e)}")


class RepairWorker(QThread):
    """
    Workshop Addition: Background worker for executing surgical repairs, 
    password hash clearing, and building Frankenstein BIOS securely.
    """
    
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, mode: str, engine: RepairEngine, save_path: str, dmi_start: str = None, dmi_size: str = None, pwd_offset: str = None):
        super().__init__()
        self.mode = mode
        self.engine = engine
        self.save_path = save_path
        self.dmi_start = dmi_start
        self.dmi_size = dmi_size
        self.pwd_offset = pwd_offset

    def run(self):
        try:
            self.progress_signal.emit(20)
            res = {}

            if self.mode == "csme":
                self.status_signal.emit("Surgically Injecting Clean CSME Region (Padding applied if needed)...")
                res = self.engine.clean_csme(self.save_path)
                
            elif self.mode == "dmi":
                if self.dmi_start and self.dmi_size:
                    self.status_signal.emit("Executing Manual DMI/NVRAM Block Transfer to Donor...")
                else:
                    self.status_signal.emit("Executing Precision Auto-MSDM (Windows Key) Transfer...")
                res = self.engine.transfer_dmi(self.save_path, self.dmi_start, self.dmi_size)
                
            elif self.mode == "frankenstein":
                self.status_signal.emit("Building Frankenstein BIOS (Protecting Original GbE/MAC & MSDM)...")
                self.progress_signal.emit(60)
                res = self.engine.build_frankenstein_bios(self.save_path)

            elif self.mode == "password":
                self.status_signal.emit("Overwriting OEM Supervisor Password Hash securely...")
                self.progress_signal.emit(75)
                res = self.engine.clear_password(self.save_path, self.pwd_offset)

            self.progress_signal.emit(100)
            self.status_signal.emit("Surgical Repair Operation Finished!")
            self.result_signal.emit(res)
            
        except Exception as e:
            self.error_signal.emit(f"Repair Thread Error: {str(e)}")

if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - Worker Threads Module Ready.")