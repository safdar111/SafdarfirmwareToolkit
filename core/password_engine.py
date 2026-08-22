# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.6.0 (Honest Rewrite - Workshop Safety)
# File      : core/password_engine.py
# Author    : Safdar Ali
# =====================================================

"""
NVRAM Variable Store Locator & Password Removal Engine.

IMPORTANT HISTORY NOTE FOR SAFDAR:
The previous version of this file (_patch_dell / _patch_lenovo / _patch_hp)
only checked whether a brand name STRING existed anywhere in the binary
(e.g. b"Dell" in data) and then reported "Success - password cleared"
WITHOUT EVER WRITING ANY BYTES TO THE OUTPUT FILE. That was dangerous:
a technician could hand back a chip that still had its original password.

This rewrite does NOT auto-patch blindly. It structurally locates the
UEFI NVRAM variable store region (EVSA / NVAR / VSS) using the same
signatures already proven in core/constants.py and core/uefi.py, reports
exactly what it found and where (offset, size, confidence), and is honest
when it CANNOT safely identify a patchable password block. Blind-patching
an NVRAM store without knowing the exact variable layout risks corrupting
boot variables, MAC address storage, or BitLocker/TPM state - so this
engine's job is DETECTION + REPORTING, not silent auto-write.

Actual byte-level clearing (once a real offset is confirmed - by you,
manually, via HxD comparison against a known-clean donor, or via the
dmi_engine/csme_engine heuristics) should go through
core.repair_engine.RepairEngine.clear_password(), which already does
real, tested, offset-based overwriting.
"""

import os
from typing import Optional
from core.constants import NVAR_SIGNATURE, VSS_SIGNATURE, EVSA_SIGNATURE


class NVRAMStoreResult:
    def __init__(self, store_type: str, offset: int, confidence: str, note: str):
        self.store_type = store_type
        self.offset = offset
        self.confidence = confidence
        self.note = note

    def offset_hex(self) -> str:
        return f"0x{self.offset:08X}"


class PasswordRemovalEngine:
    """
    Brand-aware NVRAM store locator. Honest by design: never reports
    "Success" unless it can point to a real, structurally-identified
    offset. Does not modify the file on disk.
    """

    def __init__(self, file_path: str, brand: str):
        self.file_path = file_path
        self.brand = (brand or "").lower()
        self.data: bytes = b""

    def _load(self) -> bool:
        if not os.path.exists(self.file_path):
            return False
        with open(self.file_path, "rb") as f:
            self.data = f.read()
        return True

    def _find_nvram_stores(self):
        """Structurally locates EVSA/NVAR/VSS store headers. These are
        real, documented UEFI variable-store signatures (already used
        elsewhere in this codebase, e.g. core/uefi.py NVRAM_HINTS)."""
        found = []
        for sig, label in (
            (EVSA_SIGNATURE, "EVSA (Phoenix/Dell style)"),
            (NVAR_SIGNATURE, "NVAR (Insyde/AMI style)"),
            (VSS_SIGNATURE, "VSS (Insyde/Apple style)"),
        ):
            start = 0
            while True:
                pos = self.data.find(sig, start)
                if pos == -1:
                    break
                found.append(NVRAMStoreResult(
                    store_type=label,
                    offset=pos,
                    confidence="Structural (signature match, layout not verified)",
                    note="Store location found. Exact password-variable "
                         "offset inside this store is model-specific and "
                         "NOT determined by signature alone."
                ))
                start = pos + 4
        return found

    def process_removal(self) -> tuple[bool, str]:
        """
        Returns (False, message) in almost all cases by design - this
        engine reports findings, it does not silently claim success.
        Use the offsets it reports with RepairEngine.clear_password()
        after manually confirming the correct one (e.g. via HxD diff
        against a known-clean donor of the same board).
        """
        if not self._load():
            return False, "File not found!"

        if self.brand not in ("dell", "lenovo", "hp"):
            return False, f"Unsupported brand '{self.brand}'. Supported: dell, lenovo, hp."

        stores = self._find_nvram_stores()

        if not stores:
            return False, (
                f"No EVSA/NVAR/VSS NVRAM variable store signature found in this "
                f"{self.brand.upper()} dump. This tool cannot safely locate a "
                f"password block automatically on this file - a manual hex "
                f"comparison against a known-clean donor is required."
            )

        lines = [
            f"Found {len(stores)} NVRAM variable store candidate(s) in this "
            f"{self.brand.upper()} dump. NONE have been modified - this is a "
            f"detection report only:",
        ]
        for s in stores:
            lines.append(f"  - {s.store_type} at {s.offset_hex()} [{s.confidence}]")
        lines.append(
            "Next step: use HxD to compare against a known-clean donor of the "
            "SAME board to find the exact password-hash bytes inside one of "
            "these stores, then clear it with RepairEngine.clear_password() "
            "at that confirmed offset."
        )

        return False, "\n".join(lines)


if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - Password Engine (Honest Detection Mode) Ready.")