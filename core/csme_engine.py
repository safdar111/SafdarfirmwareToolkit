import struct
from typing import Dict, Any, Optional, List


class CSMEEngine:
    """
    Safdar Firmware Toolkit Pro - Intel ME/CSME Diagnostic Engine
    -------------------------------------------------------------
    Parses Flash Partition Tables ($FPT), Manifest Headers ($MN2/$HDR),
    and evaluates clean vs dirty configuration states using struct unpacking.
    """

    # Intel ME / CSME Magic Signatures
    SIGNATURE_FPT = b"$FPT"
    SIGNATURE_MN2 = b"$MN2"
    SIGNATURE_HDR = b"$HDR"

    def __init__(self, bios_data: Optional[bytes] = None):
        self.data: bytes = bios_data if bios_data is not None else b""
        self.file_size_mb: float = len(self.data) / (1024 * 1024) if self.data else 0.0

    def analyze_file(self, bios_bytes: Optional[bytes] = None, file_size_mb: Optional[float] = None) -> Dict[str, Any]:
        """
        Main entry point. Evaluates ME presence, SKU, version triple, and initialization state.
        Uses self.data if bios_bytes is not explicitly passed.
        """
        if bios_bytes is not None:
            self.data = bios_bytes
            self.file_size_mb = len(bios_bytes) / (1024 * 1024)

        if file_size_mb is not None:
            self.file_size_mb = file_size_mb

        # 1. Locate Flash Partition Table ($FPT) - search for multiple occurrences and pick the best match
        fpt_offset = self._find_best_fpt_offset()

        # --- PREVENT FALSE CLEANS ON 16 MB / BIOS-ONLY DUMPS ---
        if fpt_offset == -1:
            return {
                "has_me_region": False,
                "status_text": "No ME Region Found",
                "status_color": "gray",
                "version": "N/A",
                "sku": "N/A",
                "is_clean": False,
                "description": (
                    f"This binary ({self.file_size_mb:.1f} MB) contains no Intel CSME/ME partition ($FPT missing). "
                    "On dual-chip boards, the ME region resides on the primary (e.g., 32 MB) SPI chip."
                )
            }

        # 2. Parse $FPT Header
        fpt_info = self._parse_fpt_header(fpt_offset)

        # 3. Locate Manifest ($MN2 / $HDR) & Extract Version
        version_str = self._extract_me_version(fpt_offset)

        # 4. Evaluate Health & Configuration Flags
        health_info = self._evaluate_health_flags(fpt_offset)

        # Detect Boot Guard / manifest indicators in the whole image for safety checks
        boot_guard_detected = any(x in self.data for x in (b"$BKM", b"$HAP", b"$BPT"))

        return {
            "has_me_region": True,
            "fpt_offset": hex(fpt_offset),
            "header_revision": fpt_info.get("revision", "N/A"),
            "version": version_str,
            "sku": health_info.get("sku", "CSME/ME Firmware"),
            "status_text": health_info["status_text"],
            "status_color": health_info["status_color"],
            "is_clean": health_info["is_clean"],
            "description": health_info["description"]
            ,"boot_guard": boot_guard_detected
        }

    # --- METHOD ALIAS FOR ANALYZER.PY ---
    def inspect(self, bios_bytes: Optional[bytes] = None, file_size_mb: Optional[float] = None) -> Dict[str, Any]:
        """Wrapper to satisfy existing calls to CSMEInspector.inspect() in analyzer.py."""
        return self.analyze_file(bios_bytes, file_size_mb)

    def _parse_fpt_header(self, offset: int) -> Dict[str, Any]:
        """Unpacks $FPT 32-byte header fields using struct."""
        if (offset + 32) > len(self.data):
            return {}

        try:
            sig, header_len, entry_ver, header_rev = struct.unpack("<4sHBB", self.data[offset:offset + 8])
            entries_count = self.data[offset + 0x0B]
            return {
                "header_length": header_len,
                "revision": header_rev,
                "entry_count": entries_count
            }
        except struct.error:
            return {}

    def _find_best_fpt_offset(self) -> int:
        """Search all $FPT occurrences and pick the most plausible one using FIT fields validation."""
        positions: List[int] = []
        start = 0
        while True:
            pos = self.data.find(self.SIGNATURE_FPT, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 4

        if not positions:
            return -1

        plausible = []
        for pos in positions:
            # Read FIT fields at pos+0x18 if present
            fit_off = pos + 0x18
            if fit_off + 8 <= len(self.data):
                try:
                    vals = struct.unpack("<HHHH", self.data[fit_off:fit_off + 8])
                except struct.error:
                    continue
                major, minor, hotfix, build = vals
                # Basic plausibility checks for FIT version numbers
                if 1 <= major <= 30 and 0 <= minor <= 200 and 0 <= hotfix <= 2000 and 0 <= build <= 65535:
                    plausible.append((pos, (major, minor, hotfix, build)))

        # Prefer the earliest plausible FIT-containing FPT; otherwise fall back to the first found
        if plausible:
            plausible.sort(key=lambda x: x[0])
            return plausible[0][0]

        return positions[0]

    def _extract_me_version(self, fpt_offset: int) -> str:
        """Read the version from the Intel FPT header and nearby manifest data."""
        candidates = []

        # Intel FPT header stores FIT version at offsets 0x18..0x1F.
        fpt_fit_start = fpt_offset + 0x18
        if fpt_fit_start + 8 <= len(self.data):
            try:
                values = struct.unpack("<HHHH", self.data[fpt_fit_start:fpt_fit_start + 8])
                if 1 <= values[0] <= 30 and 0 <= values[1] <= 200 and 0 <= values[2] <= 2000 and 0 <= values[3] <= 65535:
                    candidates.append(f"{values[0]}.{values[1]}.{values[2]}.{values[3]}")
            except struct.error:
                pass

        # Fallback: scan a larger nearby manifest window for real $MN2 / $HDR headers
        search_window = self.data[max(0, fpt_offset): min(len(self.data), fpt_offset + 0x40000)]
        for sig in (self.SIGNATURE_MN2, self.SIGNATURE_HDR):
            pos = search_window.find(sig)
            while pos != -1:
                abs_offset = fpt_offset + pos
                # try a dense set of offsets after the signature where version fields may live
                for rel_offset in (0x10, 0x14, 0x18, 0x1C, 0x20, 0x24, 0x28, 0x2C, 0x30, 0x34, 0x38, 0x3C, 0x40, 0x44):
                    start = abs_offset + rel_offset
                    end = start + 8
                    if end > len(self.data):
                        continue
                    try:
                        values = struct.unpack("<HHHH", self.data[start:end])
                    except struct.error:
                        continue
                    if 1 <= values[0] <= 30 and 0 <= values[1] <= 200 and 0 <= values[2] <= 2000 and 0 <= values[3] <= 65535:
                        candidates.append(f"{values[0]}.{values[1]}.{values[2]}.{values[3]}")
                pos = search_window.find(sig, pos + 4)

        # Prefer the most likely real version numbers; drop invalid placeholders.
        for candidate in candidates:
            if candidate not in {"0.0.0.0", "1.0.0.0"}:
                return candidate

        return "Version Unidentified"

    def _evaluate_health_flags(self, fpt_offset: int) -> Dict[str, Any]:
        """Evaluates initialization state flags and distinguishes Clean vs Dirty."""
        is_initialized = False
        if (fpt_offset + 0x18) <= len(self.data):
            flags = self.data[fpt_offset + 0x14]
            if (flags & 0x03) != 0:
                is_initialized = True

        if not is_initialized:
            return {
                "status_text": "Clean / Configured",
                "status_color": "green",
                "is_clean": True,
                "sku": "CSME Unconfigured Base",
                "description": "Firmware is in fresh factory state. Unpaired with CPU/PCH."
            }
        else:
            return {
                "status_text": "Dirty / Initialized",
                "status_color": "red",
                "is_clean": False,
                "sku": "CSME Hardware-Paired",
                "description": "Firmware contains system-specific pairing, Boot Guard, or committed system data."
            }

    def get_version_string(self) -> str:
        """Compatibility wrapper expected by the analyzer and GUI."""
        info = self.analyze_file()
        return info.get("version", "Unknown")

    def get_health_status(self) -> str:
        """Compatibility wrapper expected by the analyzer and GUI."""
        info = self.analyze_file()
        return info.get("status_text", "Unknown State")


# --- BACKWARD COMPATIBILITY ALIASES FOR ANALYZER.PY ---
CSMEInspector = CSMEEngine
CSMEManager = CSMEEngine

if __name__ == "__main__":
    print("[*] CSMEEngine module loaded successfully.")