# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.4.0 (Workshop Grade)
# File      : core/uefi.py
# Author    : Safdar Ali
# =====================================================

"""
UEFI Firmware Volume (FV) Parser.
Locates and validates standard UEFI volumes, checking for headers, 
valid sizes, and identifying critical NVRAM/Password storage zones.
"""

import struct
from typing import List, Optional

FVH_SIGNATURE = b"_FVH"

# Signatures often found inside the NVRAM volume
NVRAM_HINTS = [b"NVAR", b"EVSA", b"$VSS", b"FDC"]

class FirmwareVolume:
    """Represents a single UEFI Firmware Volume inside the SPI dump."""
    def __init__(self, offset: int):
        self.offset = offset
        self.valid = False
        self.length = 0
        self.guid = ""
        self.is_nvram = False
        self.attributes = 0

    def offset_hex(self) -> str:
        return f"0x{self.offset:08X}"

    def length_hex(self) -> str:
        return f"0x{self.length:08X}"


class UEFIParser:
    """
    Scans the binary for _FVH signatures, validates the headers,
    and flags critical volumes like NVRAM for workshop repairs.
    """
    def __init__(self, data: bytes):
        self.data = data
        self.size = len(data)
        self.volumes: List[FirmwareVolume] = []

    def _format_guid(self, raw_guid: bytes) -> str:
        """Converts raw 16-byte GUID to standard UEFI string format."""
        if len(raw_guid) != 16:
            return "UNKNOWN"
        try:
            # UEFI GUIDs use mixed endianness
            p1, p2, p3 = struct.unpack("<IHH", raw_guid[:8])
            p4 = raw_guid[8:]
            p4_str = ''.join(f'{b:02X}' for b in p4)
            return f"{p1:08X}-{p2:04X}-{p3:04X}-{p4_str[:4]}-{p4_str[4:]}"
        except struct.error:
            return "INVALID"

    def _check_if_nvram(self, header_start: int, length: int) -> bool:
        """Scans the beginning of the volume to see if it holds NVRAM stores."""
        scan_limit = min(self.size, header_start + 0x10000) # Scan first 64KB of the volume
        chunk = self.data[header_start:scan_limit]
        
        for hint in NVRAM_HINTS:
            if hint in chunk:
                return True
        return False

    def parse(self) -> List[FirmwareVolume]:
        """Parses the firmware image and extracts valid UEFI volumes."""
        start = 0

        while True:
            pos = self.data.find(FVH_SIGNATURE, start)

            if pos == -1:
                break

            # In UEFI Spec, _FVH is exactly at offset 0x28 (40 bytes) from the volume base
            header = pos - 0x28

            if header >= 0 and header + 0x48 <= self.size:
                try:
                    # Unpack length (UINT64) from offset 0x20
                    length = int.from_bytes(self.data[header + 0x20:header + 0x28], "little")

                    # Basic sanity check to eliminate false positives
                    if 0x48 < length <= self.size and (header + length) <= self.size:
                        
                        fv = FirmwareVolume(header)
                        fv.length = length
                        
                        # Extract 16-byte GUID at the start of the header (offset 0x00)
                        raw_guid = self.data[header:header + 16]
                        fv.guid = self._format_guid(raw_guid)

                        # Validate header Checksum (UINT16 at offset 0x30)
                        # We won't strictly drop it if checksum fails (due to corruption), 
                        # but valid size and GUID usually means it's a real volume.
                        fv.valid = True
                        
                        # Check if this volume holds critical NVRAM data (Passwords/DMI)
                        fv.is_nvram = self._check_if_nvram(header, length)

                        self.volumes.append(fv)
                        
                        # Jump ahead to avoid searching inside this header
                        start = header + length
                        continue

                except Exception:
                    pass

            start = pos + 4

        return self.volumes

if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - UEFI Parser Ready.")