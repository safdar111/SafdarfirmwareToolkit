# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.2.1
# File    : region.py
# =====================================================


class FlashRegion:

    def __init__(self, name, base=0, limit=0):

        self.name = name
        self.base = base
        self.limit = limit

    @property
    def size(self):

        if self.limit <= self.base:
            return 0

        return self.limit - self.base + 1

    def size_string(self):

        size = self.size

        if size >= 1024 * 1024:
            return f"{size / (1024*1024):.2f} MB"

        if size >= 1024:
            return f"{size / 1024:.2f} KB"

        return f"{size} Bytes"

    def base_hex(self):

        return f"0x{self.base:08X}"

    def limit_hex(self):

        return f"0x{self.limit:08X}"


class FlashLayout:

    def __init__(self):

        self.regions = []

    def add(self, region):

        self.regions.append(region)

    def count(self):

        return len(self.regions)

    def get(self, name):

        for region in self.regions:

            if region.name == name:
                return region

        return None# =====================================================
# Intel Flash Region Parser
# Version : 0.3.1
# =====================================================

REGION_NAMES = [
    "Descriptor",
    "BIOS",
    "ME",
    "GbE",
    "PDR",
]


def parse_flash_regions(descriptor_bytes):
    """
    Parse Intel Flash Descriptor Region Section.

    descriptor_bytes:
        First 0x1000 bytes of the SPI image.

    Returns:
        FlashLayout
    """

    layout = FlashLayout()

    # Region Section Base Address
    flmap1 = int.from_bytes(descriptor_bytes[0x14:0x18], "little")

    region_base = ((flmap1 >> 16) & 0xFF) * 0x10

    if region_base == 0:
        return layout

    for index, name in enumerate(REGION_NAMES):

        entry = region_base + (index * 4)

        value = int.from_bytes(
            descriptor_bytes[entry:entry + 4],
            "little"
        )

        base = (value & 0x0FFF) << 12
        limit = ((value >> 16) & 0x0FFF) << 12

        if limit >= base:
            limit |= 0xFFF

        layout.add(
            FlashRegion(
                name=name,
                base=base,
                limit=limit,
            )
        )

    return layout