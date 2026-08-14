# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : gui/worker.py
# Author  : Safdar Ali
# =====================================================

"""
Background Threading Worker Module.
Runs heavy binary analysis & repair tasks asynchronously
to keep the PyQt6 UI smooth and responsive with progress updates.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from core.analyzer import Analyzer


class AnalysisWorker(QThread):
    """
    Background worker thread for single and dual BIOS file analysis.
    Emits progress signals (0-100%), status messages, and result dictionaries.
    """

    # Signals to communicate with the main GUI thread
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
        """
        Executes analysis tasks in the background.
        """
        try:
            self.status_signal.emit("Initializing Analysis Engine...")
            self.progress_signal.emit(10)

            analyzer = Analyzer(self.primary_path, self.donor_path)

            if not self.is_dual:
                self.status_signal.emit("Scanning Flash Descriptor & CSME Partition...")
                self.progress_signal.emit(35)

                self.status_signal.emit("Extracting DMI Metadata & Windows Product Key...")
                self.progress_signal.emit(65)

                self.status_signal.emit("Computing Cryptographic Checksums (CRC32/MD5/SHA256)...")
                self.progress_signal.emit(85)

                results = analyzer.analyze_single()

                self.status_signal.emit("Analysis Complete!")
                self.progress_signal.emit(100)
                self.result_signal.emit(results)

            else:
                self.status_signal.emit("Analyzing Corrupt & Donor Binaries...")
                self.progress_signal.emit(40)

                self.status_signal.emit("Comparing CSME Versions & DMI Boundaries...")
                self.progress_signal.emit(75)

                results = analyzer.analyze_dual()

                self.status_signal.emit("Dual Analysis Complete!")
                self.progress_signal.emit(100)
                self.result_signal.emit(results)

        except Exception as e:
            self.error_signal.emit(str(e))