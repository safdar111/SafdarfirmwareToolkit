# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.1.1
# File    : constants.py
# =====================================================

# Known SPI flash capacities (bytes)

FLASH_SIZES = {

    1 * 1024 * 1024: "1 MB",

    2 * 1024 * 1024: "2 MB",

    4 * 1024 * 1024: "4 MB",

    8 * 1024 * 1024: "8 MB",

    16 * 1024 * 1024: "16 MB",

    32 * 1024 * 1024: "32 MB",

    64 * 1024 * 1024: "64 MB",

}


# Intel Flash Descriptor Signature

INTEL_DESCRIPTOR_SIGNATURE = bytes([0x5A, 0xA5, 0xF0, 0x0F])


# Intel ME

ME_PARTITION_SIGNATURE = b"$FPT"


# UEFI

UEFI_VOLUME_SIGNATURE = b"_FVH"


# NVRAM

NVAR_SIGNATURE = b"NVAR"

VSS_SIGNATURE = b"VSS "

EVSA_SIGNATURE = b"EVSA"