# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.2.0
# File    : descriptor.py
# =====================================================

from core.constants import INTEL_DESCRIPTOR_SIGNATURE


class IntelDescriptor:

    def __init__(self, data: bytes):

        self.data = data

        self.present = False
        self.offset = -1

    def analyze(self):

        self.offset = self.data.find(INTEL_DESCRIPTOR_SIGNATURE)

        if self.offset != -1:
            self.present = True

        return self

    def status(self):

        return "FOUND" if self.present else "NOT FOUND"

    def offset_hex(self):

        if self.offset == -1:
            return "N/A"

        return f"0x{self.offset:08X}"