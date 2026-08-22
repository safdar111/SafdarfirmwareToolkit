# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.4.0 (Workshop Grade)
# File      : database/db_manager.py
# Author    : Safdar Ali
# =====================================================

"""
Local File-System Database Manager.
Initializes the required folder structure for CSME clean files, 
donor BIOS dumps, and generated diagnostic reports.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any

class DatabaseManager:
    def __init__(self, base_path: str = "Safdar_DB"):
        self.base_path = base_path
        self.csme_repo = os.path.join(self.base_path, "CSME_Repository")
        self.donor_repo = os.path.join(self.base_path, "Donor_Bios")
        self.reports_dir = os.path.join(self.base_path, "Reports_and_Logs")
        self.output_dir = os.path.join(self.base_path, "Repaired_Outputs")
        
        # Meta index for fast GUI loading
        self.index_file = os.path.join(self.base_path, "db_index.json")

    def initialize_database(self) -> None:
        """Creates the full directory tree if it doesn't exist."""
        directories = [
            self.base_path,
            self.csme_repo,
            self.donor_repo,
            self.reports_dir,
            self.output_dir
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"[+] Database Directory Created: {directory}")

        if not os.path.exists(self.index_file):
            self._save_index({"last_updated": str(datetime.now()), "total_me_files": 0, "total_donors": 0})

    def _save_index(self, data: Dict[str, Any]) -> None:
        """Saves metadata to a JSON file for quick GUI dashboard stats."""
        try:
            with open(self.index_file, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[-] Failed to write DB index: {e}")

    def update_index(self) -> dict:
        """Scans directories and updates the JSON index with current file counts."""
        me_count = sum([len(files) for r, d, files in os.walk(self.csme_repo) if any(f.endswith(('.bin', '.rgn')) for f in files)])
        donor_count = sum([len(files) for r, d, files in os.walk(self.donor_repo) if any(f.endswith(('.bin', '.rom')) for f in files)])
        
        stats = {
            "last_updated": str(datetime.now()),
            "total_me_files": me_count,
            "total_donors": donor_count
        }
        self._save_index(stats)
        return stats

if __name__ == "__main__":
    db = DatabaseManager()
    db.initialize_database()
    stats = db.update_index()
    print(f"[*] Database Initialized & Indexed: {stats['total_me_files']} CSME files, {stats['total_donors']} Donors.")