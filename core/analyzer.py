# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.1.1
# File    : analyzer.py
# =====================================================

from core.firmware import FirmwareImage
from core.hash_utils import calculate_hashes
from core.report import Report
from core.constants import (
    FLASH_SIZES,
    INTEL_DESCRIPTOR_SIGNATURE,
    ME_PARTITION_SIGNATURE,
    UEFI_VOLUME_SIGNATURE,
    NVAR_SIGNATURE,
    VSS_SIGNATURE,
    EVSA_SIGNATURE,
)


class FirmwareAnalyzer:

    def __init__(self, filename):
        self.filename = filename

    def analyze(self):

        fw = FirmwareImage(self.filename)
        fw.load()

        data = fw.data

        report = Report()

        report.title("Safdar Firmware Toolkit Pro")
        report.add("Firmware Analysis Report")
        report.separator()

        # --------------------------------------------------
        # File Information
        # --------------------------------------------------

        report.add("FILE INFORMATION")
        report.separator()

        report.add(f"File Name : {fw.name}")
        report.add(f"File Size : {fw.size:,} bytes")

        if fw.size in FLASH_SIZES:
            report.add(f"Flash Size : {FLASH_SIZES[fw.size]}")
        else:
            report.add("Flash Size : Unknown")

        report.add("")

        # --------------------------------------------------
        # Hashes
        # --------------------------------------------------

        hashes = calculate_hashes(data)

        report.add("HASHES")
        report.separator()

        report.add(f"MD5    : {hashes['md5']}")
        report.add(f"SHA1   : {hashes['sha1']}")
        report.add(f"SHA256 : {hashes['sha256']}")

        report.add("")

        # --------------------------------------------------
        # Signature Detection
        # --------------------------------------------------

        report.add("STRUCTURE DETECTION")
        report.separator()

        report.add(
            f"Intel Flash Descriptor : {'FOUND' if INTEL_DESCRIPTOR_SIGNATURE in data else 'NOT FOUND'}"
        )

        report.add(
            f"Intel ME Partition     : {'FOUND' if ME_PARTITION_SIGNATURE in data else 'NOT FOUND'}"
        )

        report.add(
            f"UEFI Firmware Volume   : {'FOUND' if UEFI_VOLUME_SIGNATURE in data else 'NOT FOUND'}"
        )

        report.add(
            f"NVAR Store             : {'FOUND' if NVAR_SIGNATURE in data else 'NOT FOUND'}"
        )

        report.add(
            f"VSS Store              : {'FOUND' if VSS_SIGNATURE in data else 'NOT FOUND'}"
        )

        report.add(
            f"EVSA Store             : {'FOUND' if EVSA_SIGNATURE in data else 'NOT FOUND'}"
        )

        report.add("")

        # --------------------------------------------------
        # Flash Statistics
        # --------------------------------------------------

        report.add("FLASH CONTENT")
        report.separator()

        report.add(f"0xFF Percentage : {fw.blank_percentage():.2f}%")
        report.add(f"0x00 Percentage : {fw.zero_percentage():.2f}%")

        report.add("")

        # --------------------------------------------------
        # Diagnosis
        # --------------------------------------------------

        report.add("DIAGNOSIS")
        report.separator()

        if fw.blank_percentage() > 95:

            report.add("STATUS : NEEDS REPAIR")
            report.add("")
            report.add("Reason:")
            report.add("Firmware appears mostly blank.")
            report.add("")
            report.add("Suggested Action:")
            report.add("Import a matching donor BIOS.")

        elif INTEL_DESCRIPTOR_SIGNATURE in data:

            report.add("STATUS : ANALYSIS COMPLETED")
            report.add("")
            report.add("Suggested Action:")
            report.add("Proceed with advanced firmware validation.")

        else:

            report.add("STATUS : UNKNOWN")
            report.add("")
            report.add("Suggested Action:")
            report.add("Intel Flash Descriptor not detected.")
            report.add("Further inspection required.")

        report.add("")
        report.separator()
        report.add("End Of Report")

        return report.build()