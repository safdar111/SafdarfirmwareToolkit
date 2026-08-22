# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.4.0 (Workshop Grade)
# File      : core/region.py
# Author    : Safdar Ali
# =====================================================

"""
Intel Flash Descriptor (IFD) Region Parser Engine.
Accurately maps BIOS, ME, GbE, and EC boundaries using bitwise shifts.
Includes structural sanity checks to prevent crashes on heavily corrupted dumps.
"""

from typing import List, Optional

REGION_NAMES = [
    "Descriptor",
    "BIOS",
    "ME",
    "GbE",
    "PDR",
    "DeviceExpansion",
    "SecondaryBIOS",
    "CPUReserve",
    "EC",          # Embedded Controller (Modern Boards)
    "IE"           # Innovation Engine (Server/High-end)
]

class FlashRegion:
    def __init__(self, name: str, base: int = 0, limit: int = 0, is_active: bool = False):
        self.name = name
        self.base = base
        self.limit = limit
        self.is_active = is_active  # Tells us if the region actually exists on this chip

    @property
    def size(self) -> int:
        if not self.is_active or self.limit <= self.base:
            return 0
        return self.limit - self.base + 1

    def size_string(self) -> str:
        s = self.size
        if s == 0:
            return "Unused / Empty"
        if s >= 1024 * 1024:
            return f"{s / (1024*1024):.2f} MB"
        if s >= 1024:
            return f"{s / 1024:.2f} KB"
        return f"{s} Bytes"

    def base_hex(self) -> str:
        return f"0x{self.base:08X}"

    def limit_hex(self) -> str:
        return f"0x{self.limit:08X}"

    def sanity_check(self, max_file_size: int) -> bool:
        """Workshop Safety: Verifies if region boundaries make physical sense."""
        if not self.is_active:
            return True # Empty regions are physically fine
        if self.base > max_file_size or self.limit > max_file_size:
            return False
        if self.size > max_file_size or self.size < 0:
            return False
        return True


class FlashLayout:
    def __init__(self):
        self.regions: List[FlashRegion] = []

    def add(self, region: FlashRegion):
        self.regions.append(region)

    def count(self) -> int:
        return len(self.regions)

    def get(self, name: str) -> Optional[FlashRegion]:
        for region in self.regions:
            if region.name.lower() == name.lower():
                return region
        return None

    def validate_all_regions(self, max_file_size: int) -> bool:
        """Checks if the entire layout is within the chip's physical limits."""
        for region in self.regions:
            if not region.sanity_check(max_file_size):
                return False
        return True


def parse_flash_regions(descriptor_bytes: bytes, file_size: int = 0) -> FlashLayout:
    """
    Parses the Intel Flash Descriptor Region Section safely.
    
    Args:
        descriptor_bytes: The first 4KB (0x1000) of the SPI image.
        file_size: Total size of the ROM to prevent out-of-bounds corruption errors.
    """
    layout = FlashLayout()

    if len(descriptor_bytes) < 0x1000:
        return layout  # Too small to be a valid IFD

    # Region Section Base Address (FLMAP1)
    flmap1 = int.from_bytes(descriptor_bytes[0x14:0x18], "little")
    region_base = ((flmap1 >> 16) & 0xFF) * 0x10

    if region_base == 0 or region_base >= len(descriptor_bytes):
        return layout # IFD is likely completely corrupted

    for index, name in enumerate(REGION_NAMES):
        entry = region_base + (index * 4)
        
        if entry + 4 > len(descriptor_bytes):
            break

        value = int.from_bytes(descriptor_bytes[entry:entry + 4], "little")

        base = (value & 0x0FFF) << 12
        limit = ((value >> 16) & 0x0FFF) << 12

        # In Intel IFD, if limit < base, the region is unused (e.g., limit=0x000, base=0x7FFF)
        is_active = False
        if limit >= base and value != 0x00007FFF:
            limit |= 0xFFF
            is_active = True

        region = FlashRegion(name=name, base=base, limit=limit, is_active=is_active)
        
        # Auto-correct out of bounds limit if file size is provided (Workshop corruption fix)
        if is_active and file_size > 0 and region.limit > file_size:
            region.limit = file_size - 1

        layout.add(region)

    return layout

if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - IFD Region Parser Ready.")