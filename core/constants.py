# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.4.0 (Workshop Grade)
# File      : core/constants.py
# Author    : Safdar Ali
# =====================================================

"""
Central Database of Flash Offsets, Binary Signatures,
Flash Capacities, and Platform Constants for Universal
Laptop Motherboard Firmware Analysis & Repair.
"""

# ----------------------------------------------------
# 1. SPI FLASH CHIP CAPACITIES (Bytes to Label)
# ----------------------------------------------------
FLASH_SIZES = {
    524288: "512 KB (4 Mbit)",
    1048576: "1 MB (8 Mbit)",
    2097152: "2 MB (16 Mbit)",
    4194304: "4 MB (32 Mbit)",
    8388608: "8 MB (64 Mbit)",
    16777216: "16 MB (128 Mbit)",
    33554432: "32 MB (256 Mbit)",
    67108864: "64 MB (512 Mbit)",
    134217728: "128 MB (1024 Mbit)",  # Added for newest motherboards
}

# ----------------------------------------------------
# 2. HARDWARE PLATFORM & BINARY SIGNATURES (Magic Bytes)
# ----------------------------------------------------

# Intel Flash Descriptor (Located at offset 0x10)
INTEL_DESCRIPTOR_SIGNATURE = b"\x5A\xA5\xF0\x0F"

# Intel Management Engine (ME / CSME / TXE / SPS)
ME_PARTITION_SIGNATURE = b"$FPT"         # Flash Partition Table
ME_MANIFEST_SIGNATURE = b"$MN2"          # Manifest Header (CSME v11+)
ME_CPD_SIGNATURE = b"$CPD"               # Code Partition Directory (CSME v12+)
ME_PCH_SIGNATURE = b"$PCH"               # PCH Descriptor Block
ME_PADDING_SIG = b"$SKU"                 # SKU Information Header

# Intel Boot Guard & Security
INTEL_BKM_SIG = b"$BKM"                  # Boot Guard Key Manifest
INTEL_BPM_SIG = b"$BPM"                  # Boot Guard Boot Policy Manifest
INTEL_HAP_SIG = b"$HAP"                  # High Assurance Platform (ME Disable Bit)

# UEFI Firmware Volumes & Variable Stores (NVRAM)
UEFI_VOLUME_SIGNATURE = b"_FVH"          # UEFI Firmware Volume Header
NVAR_SIGNATURE = b"NVAR"                 # Standard NVAR Store (Used for Passwords & Boot options)
VSS_SIGNATURE = b"$VSS"                  # Insyde / Apple VSS Variable Store
EVSA_SIGNATURE = b"EVSA"                 # Phoenix / Dell EVSA Store
FDC_SIGNATURE = b"FDC"                   # Often used in modern Dell NVRAM structures

# ACPI Tables (Windows OEM Digital Product Key storage)
MSDM_SIGNATURE = b"MSDM"                 # Microsoft Data Management Table (Contains Win 8/10/11 DPK)
SLIC_SIGNATURE = b"SLIC"                 # Software Licensing Description Table

# AMD Platform Structures
AMD_PSP_SIGNATURE = b"$PSP"              # AMD Platform Security Processor
AMD_BIOS_HEADER = b"$AMD"                # AMD BIOS Signature Header

# Apple Specific Firmware
APPLE_ROM_SIG = b"$APPLE"                # Apple EFI Header Signature

# ----------------------------------------------------
# 3. INTEL FLASH DESCRIPTOR REGION MAP
# ----------------------------------------------------
REGION_DESCRIPTOR = 0
REGION_BIOS = 1
REGION_ME = 2
REGION_GBE = 3
REGION_PDR = 4
REGION_EC = 8

REGION_NAMES = {
    REGION_DESCRIPTOR: "Descriptor Region",
    REGION_BIOS: "BIOS / Host Region (Main UEFI)",
    REGION_ME: "Intel ME / CSME Region",
    REGION_GBE: "Gigabit Ethernet (GbE) Region",
    REGION_PDR: "Platform Data Region (PDR)",
    REGION_EC: "Embedded Controller (EC) Region",
}

# Default GbE MAC Address Offsets relative to Flash Start
GBE_MAC_OFFSET_1 = 0x1000
GBE_MAC_OFFSET_2 = 0x2000

# ----------------------------------------------------
# 4. BRAND SPECIFIC SEARCH STRINGS & CONSTANTS
# ----------------------------------------------------
DELL_TAG_KEYS = [b"Service Tag:", b"Service Tag", b"ST:"]
HP_BID_KEYS = [b"BID", b"System Board ID", b"Feature Byte"]
LENOVO_MTM_KEYS = [b"INVALID", b"LNV", b"Lenovo", b"ThinkPad", b"IdeaPad"]

# Modern Dell Password Suffixes that require NVRAM clearing (No online master password)
DELL_RSA_PASSWORD_SUFFIXES = ["E7A8", "8FC8", "BF97", "6FF1", "1D3B"]

# ----------------------------------------------------
# 5. CSME / ME HEALTH STATES
# ----------------------------------------------------
CSME_STATE_UNINITIALIZED = "Configured / Uninitialized (Clean)"
CSME_STATE_INITIALIZED = "Initialized / Booted (Dirty)"
CSME_STATE_CORRUPT = "Corrupt / Damaged Manifest Header"
CSME_STATE_UNKNOWN = "Unknown / Non-Intel Platform"