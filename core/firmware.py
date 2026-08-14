# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : core/firmware.py
# Author  : Safdar Ali
# =====================================================

"""
Firmware Buffer & Image Handling Engine.
Handles safe binary reading, flash entropy/density metrics,
and byte slice extractions.
"""

import os
from typing import Optional
from core.constants import FLASH_SIZES


class FirmwareImage:
    """
    Encapsulates raw SPI BIOS binary buffers and provides
    low-level memory inspection and density metrics.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.name = os.path.basename(file_path)
        self.size = 0
        self.data = b""
        self.is_loaded = False

    def load(self) -> bool:
        """
        Loads binary file data into memory buffer safely.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Firmware binary not found: {self.file_path}")

        self.size = os.path.getsize(self.file_path)
        
        with open(self.file_path, "rb") as f:
            self.data = f.read()

        self.is_loaded = True
        return True

    def get_flash_label(self) -> str:
        """
        Returns human-readable SPI chip capacity string.
        """
        return FLASH_SIZES.get(self.size, f"Custom Dump ({self.size / (1024*1024):.2f} MB)")

    def blank_percentage(self) -> float:
        """
        Calculates percentage of erased 0xFF bytes (Chip erased / bad dump check).
        """
        if not self.data:
            return 0.0
        ff_count = self.data.count(b"\xff")
        return (ff_count / self.size) * 100.0

    def zero_percentage(self) -> float:
        """
        Calculates percentage of 0x00 bytes (Zero-filled / programmer failure check).
        """
        if not self.data:
            return 0.0
        zero_count = self.data.count(b"\x00")
        return (zero_count / self.size) * 100.0

    def extract_slice(self, start_offset: int, length: int) -> Optional[bytes]:
        """
        Extracts a safe byte slice from the firmware buffer.
        """
        if start_offset < 0 or start_offset >= self.size:
            return None
        
        end_offset = start_offset + length
        if end_offset > self.size:
            end_offset = self.size

        return self.data[start_offset:end_offset]