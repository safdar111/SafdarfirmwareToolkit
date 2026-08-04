# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.1.1
# File    : firmware.py
# =====================================================

from pathlib import Path


class FirmwareImage:
    """
    Handles loading and basic information about a firmware image.
    """

    def __init__(self, filename):

        self.filename = filename
        self.path = Path(filename)

        self.data = b""
        self.size = 0

    def load(self):

        self.data = self.path.read_bytes()
        self.size = len(self.data)

    @property
    def name(self):

        return self.path.name

    def flash_size(self):

        flash_sizes = {
            1 * 1024 * 1024: "1 MB",
            2 * 1024 * 1024: "2 MB",
            4 * 1024 * 1024: "4 MB",
            8 * 1024 * 1024: "8 MB",
            16 * 1024 * 1024: "16 MB",
            32 * 1024 * 1024: "32 MB",
            64 * 1024 * 1024: "64 MB",
        }

        return flash_sizes.get(self.size, "Unknown")

    def count_ff(self):

        return self.data.count(0xFF)

    def count_zero(self):

        return self.data.count(0x00)

    def blank_percentage(self):

        if self.size == 0:
            return 0

        return round((self.count_ff() / self.size) * 100, 2)

    def zero_percentage(self):

        if self.size == 0:
            return 0

        return round((self.count_zero() / self.size) * 100, 2)