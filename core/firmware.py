# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.4.0 (Workshop Grade)
# File      : core/firmware.py
# Author    : Safdar Ali
# =====================================================

"""
Firmware Buffer & Image Handling Engine.
Handles safe binary reading, flash entropy/density metrics,
bad-programmer-read detection, and byte slice extraction/injection.
"""

import os
from typing import Optional
from core.constants import FLASH_SIZES

class FirmwareImage:
    """
    Encapsulates raw SPI BIOS binary buffers and provides
    low-level memory inspection, density metrics, and data injection.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.name = os.path.basename(file_path)
        self.size = 0
        self.data = bytearray()  # Changed to bytearray for mutable operations (Injection)
        self.is_loaded = False

    def load(self) -> bool:
        """Loads binary file data into memory buffer safely."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Firmware binary not found: {self.file_path}")

        self.size = os.path.getsize(self.file_path)
        
        with open(self.file_path, "rb") as f:
            self.data = bytearray(f.read()) # Load as mutable bytearray

        self.is_loaded = True
        return True

    def get_flash_label(self) -> str:
        """Returns human-readable SPI chip capacity string."""
        return FLASH_SIZES.get(self.size, f"Custom Dump ({self.size / (1024*1024):.2f} MB)")

    def blank_percentage(self) -> float:
        """Calculates percentage of erased 0xFF bytes."""
        if not self.data:
            return 0.0
        ff_count = self.data.count(b"\xff")
        return (ff_count / self.size) * 100.0

    def zero_percentage(self) -> float:
        """Calculates percentage of 0x00 bytes."""
        if not self.data:
            return 0.0
        zero_count = self.data.count(b"\x00")
        return (zero_count / self.size) * 100.0

    def evaluate_read_quality(self) -> dict:
        """
        Workshop Diagnostic: Detects bad reads caused by programmer clip slips (e.g., CH341A).
        """
        ff_perc = self.blank_percentage()
        zero_perc = self.zero_percentage()

        if ff_perc > 95.0:
            return {
                "status": "CRITICAL",
                "message": f"Dump is {ff_perc:.1f}% Blank (0xFF). Bad programmer clip connection or empty chip!"
            }
        elif zero_perc > 95.0:
            return {
                "status": "CRITICAL",
                "message": f"Dump is {zero_perc:.1f}% Zeros (0x00). Programmer voltage issue or chip failure!"
            }
        elif ff_perc > 70.0:
            return {
                "status": "WARNING",
                "message": f"Dump contains {ff_perc:.1f}% empty space. This is unusually high but might be a partial update."
            }
        else:
            return {
                "status": "OK",
                "message": "Dump entropy looks normal. Good programmer read."
            }

    def extract_slice(self, start_offset: int, length: int) -> Optional[bytes]:
        """Extracts a safe byte slice from the firmware buffer."""
        if start_offset < 0 or start_offset >= self.size:
            return None
        
        end_offset = start_offset + length
        if end_offset > self.size:
            end_offset = self.size

        return bytes(self.data[start_offset:end_offset])

    def inject_slice(self, start_offset: int, payload: bytes) -> bool:
        """
        Injects a payload (e.g., Clean ME or patched DMI) directly into the firmware buffer.
        Overwrites existing data without changing the total file size.
        """
        if start_offset < 0 or start_offset >= self.size:
            print(f"[-] Injection Failed: Invalid start offset {hex(start_offset)}")
            return False

        payload_length = len(payload)
        if start_offset + payload_length > self.size:
            print(f"[-] Injection Failed: Payload extends beyond chip size!")
            return False

        # Overwrite the section in the bytearray
        self.data[start_offset:start_offset + payload_length] = payload
        return True

    def save_file(self, output_path: str) -> bool:
        """Saves the modified firmware buffer to a new binary file."""
        try:
            with open(output_path, "wb") as f:
                f.write(self.data)
            print(f"[+] Firmware successfully saved to: {output_path}")
            return True
        except IOError as e:
            print(f"[-] Failed to save firmware: {e}")
            return False

if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - Firmware Engine Loaded.")