# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : uefi.py
# =====================================================

FVH_SIGNATURE = b"_FVH"


class FirmwareVolume:

    def __init__(self, offset):

        self.offset = offset
        self.valid = False
        self.length = 0

    def offset_hex(self):

        return f"0x{self.offset:08X}"


class UEFIParser:

    def __init__(self, data: bytes):

        self.data = data
        self.volumes = []

    def parse(self):

        start = 0

        while True:

            pos = self.data.find(FVH_SIGNATURE, start)

            if pos == -1:
                break

            header = pos - 40

            if header >= 0:

                try:

                    length = int.from_bytes(
                        self.data[header + 32:header + 40],
                        "little"
                    )

                    fv = FirmwareVolume(header)

                    fv.length = length

                    if 0 < length < len(self.data):
                        fv.valid = True

                    self.volumes.append(fv)

                except Exception:
                    pass

            start = pos + 1

        return self.volumes