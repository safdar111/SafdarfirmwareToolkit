# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : core/descriptor.py
# Author  : Safdar Ali
# =====================================================

"""
Intel Flash Descriptor (IFD) Engine.
Parses Descriptor signatures, FLMAP region boundaries (BIOS, ME, GbE, PDR),
and flash master access permissions.
"""

from typing import Dict, Any, Optional
from core.constants import INTEL_DESCRIPTOR_SIGNATURE, REGION_NAMES
from core.search import hex_offset


class IntelDescriptor:
    """
    Parses Intel SPI Flash Descriptor structures.
    """

    def __init__(self, data: bytes):
        self.data = data
        self.present = False
        self.offset = -1
        self.flmap0 = 0
        self.flmap1 = 0
        self.regions: Dict[str, Dict[str, Any]] = {}

    def analyze(self) -> "IntelDescriptor":
        """
        Scans for descriptor signature and extracts region map offsets.
        """
        if not self.data or len(self.data) < 0x1000:
            self.present = False
            return self

        # Descriptor signature is typically located at offset 0x10
        idx = self.data.find(INTEL_DESCRIPTOR_SIGNATURE)
        if idx != -1 and idx < 0x1000:
            self.present = True
            self.offset = idx
            self._parse_regions()
        else:
            self.present = False

        return self

    def _parse_regions(self) -> None:
        """
        Extracts region base and limit addresses from FLREG registers.
        """
        # FLMAP0 base pointer is located at offset + 0x04
        # Standard descriptor layout maps regions at descriptor offset + 0x40
        reg_base = self.offset + 0x40

        if len(self.data) < reg_base + 20:
            return

        region_keys = [0, 1, 2, 3, 4]  # Descriptor, BIOS, ME, GbE, PDR

        for i in region_keys:
            entry_offset = reg_base + (i * 4)
            if entry_offset + 4 > len(self.data):
                break

            reg_val = int.from_bytes(self.data[entry_offset:entry_offset + 4], "little")
            
            # Unused region register is 0x00000000 or 0x0000FFFF
            if reg_val in (0x00000000, 0x0000FFFF, 0xFFFFFFFF):
                continue

            base_block = reg_val & 0x7FFF
            limit_block = (reg_val >> 16) & 0x7FFF

            start_addr = base_block << 12
            end_addr = ((limit_block + 1) << 12) - 1

            if end_addr > start_addr:
                region_name = REGION_NAMES.get(i, f"Region {i}")
                self.regions[region_name] = {
                    "start": start_addr,
                    "end": end_addr,
                    "size": (end_addr - start_addr) + 1,
                    "start_hex": hex_offset(start_addr),
                    "end_hex": hex_offset(end_addr),
                }

    def status(self) -> str:
        """
        Returns descriptor status summary string.
        """
        if self.present:
            return f"Valid Intel Flash Descriptor Found at {hex_offset(self.offset)}"
        return "No Intel Flash Descriptor (Non-Intel / AMD / Descriptored SPI)"

    def offset_hex(self) -> str:
        """
        Returns hex offset of descriptor signature.
        """
        return hex_offset(self.offset) if self.present else "N/A"