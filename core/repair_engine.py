# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : core/repair_engine.py
# Author  : Safdar Ali
# =====================================================

"""
Automated Firmware Patching & Repair Engine.
Handles CSME section cleaning (via Donor or Repository Clean ME),
DMI/NVRAM transfers, and post-repair binary verification.
"""

import os
from typing import Dict, Any, Optional
from core.firmware import FirmwareImage
from core.descriptor import IntelDescriptor


class RepairEngine:
    """
    Executes binary surgical replacements (CSME swap, Repository ME clean, DMI injection)
    and saves output repaired firmware dumps.
    """

    def __init__(self, original_path: str, donor_path: Optional[str] = None, clean_me_path: Optional[str] = None):
        self.original_path = original_path
        self.donor_path = donor_path
        self.clean_me_path = clean_me_path

    def clean_csme(self, output_path: str) -> Dict[str, Any]:
        """
        Replaces original dirty CSME region using either a Repository Clean ME file
        or a clean CSME region extracted from the Donor file.
        """
        # Determine source of Clean ME: Repository clean file takes priority
        source_me_path = self.clean_me_path if self.clean_me_path else self.donor_path

        if not source_me_path:
            return {"success": False, "message": "No valid Donor or Repository Clean ME file provided."}

        orig_fw = FirmwareImage(self.original_path)
        source_fw = FirmwareImage(source_me_path)
        orig_fw.load()
        source_fw.load()

        # Analyze Descriptor on original binary to locate CSME region bounds
        desc = IntelDescriptor(orig_fw.data).analyze()
        me_region = desc.regions.get("Intel ME / CSME Region")

        if not me_region:
            return {"success": False, "message": "Could not locate CSME region bounds in Intel Flash Descriptor."}

        start = me_region["start"]
        size = me_region["size"]

        # Case A: Source is a full Donor binary matching chip size
        if source_fw.size == orig_fw.size:
            clean_me_slice = source_fw.data[start:start + size]
        
        # Case B: Source is a standalone Clean CSME/ME partition file (e.g. 2MB - 8MB)
        elif source_fw.size == size:
            clean_me_slice = source_fw.data
        else:
            return {
                "success": False,
                "message": f"Clean ME size mismatch! ME region requires {size:,} bytes, but provided file is {source_fw.size:,} bytes."
            }

        # Build repaired buffer
        repaired_data = (
            orig_fw.data[:start] +
            clean_me_slice +
            orig_fw.data[start + size:]
        )

        with open(output_path, "wb") as f:
            f.write(repaired_data)

        repaired_fw = FirmwareImage(output_path)
        repaired_fw.load()

        return {
            "success": True,
            "message": f"Successfully injected clean CSME region into {os.path.basename(output_path)}",
            "output_path": output_path,
            "output_size": repaired_fw.size,
        }

    def transfer_dmi(self, output_path: str, dmi_start_hex: str, dmi_size_hex: str) -> Dict[str, Any]:
        """
        Transfers original DMI / NVRAM region bytes into Donor image base.
        """
        if not self.donor_path:
            return {"success": False, "message": "Donor path is missing."}

        orig_fw = FirmwareImage(self.original_path)
        donor_fw = FirmwareImage(self.donor_path)
        orig_fw.load()
        donor_fw.load()

        try:
            start = int(dmi_start_hex, 16)
            size = int(dmi_size_hex, 16)
        except ValueError:
            return {"success": False, "message": "Invalid hexadecimal offset/size values."}

        if start + size > orig_fw.size:
            return {"success": False, "message": "DMI range exceeds file boundaries."}

        original_dmi_slice = orig_fw.data[start:start + size]
        
        repaired_data = (
            donor_fw.data[:start] +
            original_dmi_slice +
            donor_fw.data[start + size:]
        )

        with open(output_path, "wb") as f:
            f.write(repaired_data)

        return {
            "success": True,
            "message": f"Successfully transferred DMI/NVRAM section to {os.path.basename(output_path)}",
            "output_path": output_path,
        }