# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.2
# File    : search.py
# =====================================================

def find_all(data: bytes, signature: bytes):
    """
    Return all offsets where a signature is found.
    """

    offsets = []

    start = 0

    while True:

        pos = data.find(signature, start)

        if pos == -1:
            break

        offsets.append(pos)

        start = pos + 1

    return offsets


def hex_offset(offset: int):

    return f"0x{offset:08X}"