# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.5.0 (Workshop Grade)
# File      : core/dual_chip_handler.py
# Author    : Safdar Ali
# =====================================================

"""
Dual-Chip Merge and Split Utility.
Seamlessly concatenates two physical SPI dumps (e.g., 32MB Main + 8MB EC) 
into a single continuous logical drive for analysis and repair, 
then slices them perfectly back to their original byte boundaries.
"""

import os
from typing import Dict, Any

class DualChipHandler:
    def __init__(self):
        pass

    def merge_chips(self, chip1_path: str, chip2_path: str, output_path: str) -> Dict[str, Any]:
        """
        Reads both physical chips and merges them into a single file.
        Chip 1 (Main/FPT) must be the first file. Chip 2 (Sub/EC) is appended.
        """
        if not os.path.exists(chip1_path) or not os.path.exists(chip2_path):
            return {"success": False, "message": "One or both chip files are missing."}

        try:
            chip1_size = os.path.getsize(chip1_path)
            chip2_size = os.path.getsize(chip2_path)

            with open(chip1_path, 'rb') as f1, open(chip2_path, 'rb') as f2:
                chip1_data = f1.read()
                chip2_data = f2.read()

            merged_data = chip1_data + chip2_data

            with open(output_path, 'wb') as out_f:
                out_f.write(merged_data)

            return {
                "success": True,
                "message": f"Successfully merged into {os.path.basename(output_path)}",
                "output_path": output_path,
                "chip1_original_size": chip1_size,
                "chip2_original_size": chip2_size,
                "total_size": len(merged_data)
            }

        except Exception as e:
            return {"success": False, "message": f"Merge failed: {str(e)}"}

    def split_chips(self, merged_path: str, split_point_bytes: int, out_chip1: str, out_chip2: str) -> Dict[str, Any]:
        """
        Slices a repaired merged file perfectly back into two flashable binaries 
        based on the exact byte size of the original Chip 1.
        """
        if not os.path.exists(merged_path):
            return {"success": False, "message": "Merged repaired file is missing."}

        try:
            with open(merged_path, 'rb') as f:
                merged_data = f.read()

            if len(merged_data) <= split_point_bytes:
                return {"success": False, "message": "Split point exceeds the total file size."}

            chip1_slice = merged_data[:split_point_bytes]
            chip2_slice = merged_data[split_point_bytes:]

            with open(out_chip1, 'wb') as f1:
                f1.write(chip1_slice)

            with open(out_chip2, 'wb') as f2:
                f2.write(chip2_slice)

            return {
                "success": True,
                "message": "Successfully split the repaired file back into two chips.",
                "chip1_path": out_chip1,
                "chip2_path": out_chip2
            }

        except Exception as e:
            return {"success": False, "message": f"Split failed: {str(e)}"}