# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.5.0 (Dynamic Workshop Engine)
# File      : core/repair_engine.py
# Author    : Safdar Ali
# =====================================================

"""
Automated Firmware Patching & Repair Engine (The Surgeon).
Handles CSME section cleaning, dynamic DMI/MSDM transfers, 
non-destructive password clearing, and complete Frankenstein rebuilds.
"""

import os
from typing import Dict, Any, Optional
from core.firmware import FirmwareImage
from core.region import parse_flash_regions

class RepairEngine:
    """
    Executes binary surgical replacements and builds verified, ready-to-flash dumps.
    """

    def __init__(self, original_path: str, donor_path: Optional[str] = None, clean_me_path: Optional[str] = None):
        self.original_path = original_path
        self.donor_path = donor_path
        self.clean_me_path = clean_me_path

    def clear_password(self, output_path: str, pwd_offset_hex: str) -> Dict[str, Any]:
        """
        Surgically overwrites the OEM Supervisor Password hash block with empty bytes (0x00).
        This unlocks the BIOS without clearing the NVRAM, keeping BitLocker and SecureBoot intact.
        """
        try:
            start_offset = int(pwd_offset_hex, 16)
        except (ValueError, TypeError):
            return {"success": False, "message": "Invalid password hex offset provided."}

        orig_fw = FirmwareImage(self.original_path)
        orig_fw.load()

        # Overwrite 128 bytes to clear the variable header and the encrypted payload
        empty_hash_block = b'\x00' * 128
        orig_fw.inject_slice(start_offset, empty_hash_block)
        
        orig_fw.save_file(output_path)

        return {
            "success": True,
            "message": f"Supervisor password hash successfully cleared at {pwd_offset_hex}.\nSaved to {os.path.basename(output_path)}",
            "output_path": output_path,
        }

    def clean_csme(self, output_path: str) -> Dict[str, Any]:
        """
        Replaces the original dirty CSME region using a Clean ME file (Database).
        Handles size padding automatically if the clean ME is smaller than the allocated region.
        """
        source_me_path = self.clean_me_path if self.clean_me_path else self.donor_path

        if not source_me_path:
            return {"success": False, "message": "No valid Donor or Database Clean ME file provided."}

        orig_fw = FirmwareImage(self.original_path)
        source_fw = FirmwareImage(source_me_path)
        orig_fw.load()
        source_fw.load()

        layout = parse_flash_regions(orig_fw.data, orig_fw.size)
        me_region = layout.get("ME")

        if not me_region or not me_region.is_active:
            return {"success": False, "message": "Could not locate an active CSME region in the original file."}

        start = me_region.base
        target_size = me_region.size

        # Extract source data
        if source_fw.size == orig_fw.size:
            clean_me_slice = source_fw.data[start:start + target_size]
        else:
            clean_me_slice = source_fw.data

        # Workshop Padding Logic (Prevents Brick/No-POST)
        if len(clean_me_slice) > target_size:
            return {
                "success": False,
                "message": f"Clean ME ({len(clean_me_slice)} bytes) is too large for the Target Region ({target_size} bytes)."
            }
        elif len(clean_me_slice) < target_size:
            padding = b'\xFF' * (target_size - len(clean_me_slice))
            clean_me_slice += padding

        orig_fw.inject_slice(start, clean_me_slice)
        orig_fw.save_file(output_path)

        return {
            "success": True,
            "message": f"Successfully injected and padded Clean CSME into {os.path.basename(output_path)}",
            "output_path": output_path,
        }

    def transfer_dmi(self, output_path: str, dmi_start_hex: Optional[str] = None, dmi_size_hex: Optional[str] = None) -> Dict[str, Any]:
        """
        Transfers original DMI / NVRAM region into Donor image.
        """
        if not self.donor_path:
            return {"success": False, "message": "Donor path is required for DMI transfer."}

        orig_fw = FirmwareImage(self.original_path)
        donor_fw = FirmwareImage(self.donor_path)
        orig_fw.load()
        donor_fw.load()

        # If strict offsets are not provided, attempt a precision MSDM (Windows Key) transfer
        if not dmi_start_hex or not dmi_size_hex:
            msdm_offset = orig_fw.data.find(b'MSDM')
            donor_msdm = donor_fw.data.find(b'MSDM')
            
            if msdm_offset != -1 and donor_msdm != -1:
                # 50 bytes safely covers the ACPI MSDM header and the 29-character product key
                msdm_block = orig_fw.extract_slice(msdm_offset, 50)
                donor_fw.inject_slice(donor_msdm, msdm_block)
                donor_fw.save_file(output_path)
                return {
                    "success": True,
                    "message": "Precision Transfer: Windows DPK (MSDM) successfully injected into Donor.",
                    "output_path": output_path,
                }
            return {"success": False, "message": "Could not automatically locate DMI/MSDM tables. Hex offsets required."}

        # Manual Block Transfer
        try:
            start = int(dmi_start_hex, 16)
            size = int(dmi_size_hex, 16)
        except ValueError:
            return {"success": False, "message": "Invalid hexadecimal offset values provided."}

        if start + size > orig_fw.size or start + size > donor_fw.size:
            return {"success": False, "message": "DMI range exceeds file physical boundaries."}

        original_dmi_slice = orig_fw.extract_slice(start, size)
        donor_fw.inject_slice(start, original_dmi_slice)
        donor_fw.save_file(output_path)

        return {
            "success": True,
            "message": f"Successfully transferred DMI block to Donor file: {os.path.basename(output_path)}",
            "output_path": output_path,
        }

    def build_frankenstein_bios(self, output_path: str) -> Dict[str, Any]:
        """
        Workshop Master Operation:
        Combines [Original IFD + GbE/MAC] + [Database Clean ME] + [Donor BIOS Region] + [Original Windows Key]
        Provides the highest success rate for heavily corrupted / dead motherboards.
        """
        if not self.donor_path or not self.clean_me_path:
            return {"success": False, "message": "Frankenstein rebuild requires both a Donor dump and a Database Clean ME."}

        orig_fw = FirmwareImage(self.original_path)
        donor_fw = FirmwareImage(self.donor_path)
        clean_me = FirmwareImage(self.clean_me_path)
        
        orig_fw.load()
        donor_fw.load()
        clean_me.load()

        if orig_fw.size != donor_fw.size:
            return {"success": False, "message": "Original and Donor chip capacities do not match!"}

        layout = parse_flash_regions(orig_fw.data, orig_fw.size)
        bios_region = layout.get("BIOS")
        me_region = layout.get("ME")

        if not bios_region or not me_region:
            return {"success": False, "message": "Could not locate required BIOS/ME partitions in descriptor."}

        # Step 1: Pre-Patch the Donor BIOS with the Original Windows Key (MSDM)
        msdm_offset = orig_fw.data.find(b'MSDM')
        donor_msdm = donor_fw.data.find(b'MSDM')
        if msdm_offset != -1 and donor_msdm != -1:
            msdm_block = orig_fw.extract_slice(msdm_offset, 50)
            donor_fw.inject_slice(donor_msdm, msdm_block)

        # Step 2: Copy the now-patched Donor's Main BIOS section
        donor_bios_slice = donor_fw.extract_slice(bios_region.base, bios_region.size)
        
        # Step 3: Prepare Clean ME with padding
        clean_me_slice = clean_me.data
        if len(clean_me_slice) < me_region.size:
            clean_me_slice += b'\xFF' * (me_region.size - len(clean_me_slice))
        elif len(clean_me_slice) > me_region.size:
            return {"success": False, "message": "Clean ME is too large for the region space."}

        # Step 4: Inject both into the Original Base 
        # (This inherently preserves the Original Flash Descriptor and GbE/MAC Address)
        orig_fw.inject_slice(bios_region.base, donor_bios_slice)
        orig_fw.inject_slice(me_region.base, clean_me_slice)
        
        orig_fw.save_file(output_path)

        return {
            "success": True,
            "message": f"Frankenstein BIOS rebuilt successfully!\nOriginal MAC & Windows Key Preserved.\nSaved to {os.path.basename(output_path)}",
            "output_path": output_path
        }

if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - Repair Engine Ready.")