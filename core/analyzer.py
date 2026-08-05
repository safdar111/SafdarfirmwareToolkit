# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.2.0
# File    : analyzer.py
# =====================================================

from core.firmware import FirmwareImage
from core.hash_utils import calculate_hashes
from core.report import Report
from core.descriptor import IntelDescriptor
from core.search import find_all, hex_offset
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

        # ------------------------------------------------
        # FILE INFORMATION
        # ------------------------------------------------

        report.title("Safdar Firmware Toolkit Pro")
        report.add("Firmware Analysis Report")
        report.separator()

        report.add("FILE INFORMATION")
        report.separator()

        report.add(f"File Name : {fw.name}")
        report.add(f"File Size : {fw.size:,} bytes")
        report.add(
            f"Flash Size : {FLASH_SIZES.get(fw.size, 'Unknown')}"
        )

        report.add("")

        # ------------------------------------------------
        # HASHES
        # ------------------------------------------------

        hashes = calculate_hashes(data)

        report.add("HASHES")
        report.separator()

        report.add(f"MD5    : {hashes['md5']}")
        report.add(f"SHA1   : {hashes['sha1']}")
        report.add(f"SHA256 : {hashes['sha256']}")

        report.add("")

        # ------------------------------------------------
        # DESCRIPTOR
        # ------------------------------------------------

        descriptor = IntelDescriptor(data).analyze()

        report.add("INTEL FLASH DESCRIPTOR")
        report.separator()

        report.add(f"Status : {descriptor.status()}")
        report.add(f"Offset : {descriptor.offset_hex()}")

        report.add("")

        # ------------------------------------------------
        # STRUCTURE SEARCH
        # ------------------------------------------------

        structures = [
            ("Intel ME Partition", ME_PARTITION_SIGNATURE),
            ("UEFI Firmware Volume", UEFI_VOLUME_SIGNATURE),
            ("NVAR Store", NVAR_SIGNATURE),
            ("VSS Store", VSS_SIGNATURE),
            ("EVSA Store", EVSA_SIGNATURE),
        ]

        report.add("STRUCTURE ANALYSIS")
        report.separator()

        for name, sig in structures:

            offsets = find_all(data, sig)

            report.add(name)

            if offsets:

                report.add(f"Occurrences : {len(offsets)}")

                for i, off in enumerate(offsets, start=1):
                    report.add(f"  {i}. {hex_offset(off)}")

            else:

                report.add("Occurrences : 0")

            report.add("")

        # ------------------------------------------------
        # FLASH CONTENT
        # ------------------------------------------------

        report.add("FLASH CONTENT")
        report.separator()

        report.add(f"0xFF Percentage : {fw.blank_percentage():.2f}%")
        report.add(f"0x00 Percentage : {fw.zero_percentage():.2f}%")

        report.add("")

        # ------------------------------------------------
        # DIAGNOSIS
        # ------------------------------------------------

        report.add("DIAGNOSIS")
        report.separator()

        if fw.blank_percentage() > 95:

            report.add("STATUS : BLANK FIRMWARE")
            report.add("")

            report.add("Suggested Action:")
            report.add("Firmware appears mostly erased.")

        elif descriptor.present:

            report.add("STATUS : VALID INTEL FIRMWARE")
            report.add("")
            report.add("Suggested Action:")
            report.add("Continue with advanced validation.")

        else:

            report.add("STATUS : UNKNOWN")
            report.add("")
            report.add("Suggested Action:")
            report.add("Descriptor not detected.")

        report.add("")
        report.separator()
        report.add("End Of Report")

        return report.build()