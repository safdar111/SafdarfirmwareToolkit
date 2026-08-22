# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.4.0 (Workshop Grade)
# File      : core/hash_utils.py
# Author    : Safdar Ali
# =====================================================

"""
Streamed Hashing Engine.
Calculates MD5, SHA1, SHA256, and CRC32 checksums for firmware verification,
including specific block/region hashing for Donor vs Original comparison.
"""

import hashlib
import zlib
from typing import Dict, Optional


def calculate_hashes(data: bytes) -> Dict[str, str]:
    """
    Generates cryptographic hashes and CRC32 checksum for raw binary data.
    """
    if not data:
        return {
            "md5": "N/A",
            "sha1": "N/A",
            "sha256": "N/A",
            "crc32": "N/A",
        }

    md5 = hashlib.md5(data).hexdigest()
    sha1 = hashlib.sha1(data).hexdigest()
    sha256 = hashlib.sha256(data).hexdigest()
    crc32 = f"{zlib.crc32(data) & 0xFFFFFFFF:08X}"

    return {
        "md5": md5,
        "sha1": sha1,
        "sha256": sha256,
        "crc32": crc32,
    }


def calculate_region_hashes(data: bytes, start_offset: int, length: int) -> Dict[str, str]:
    """
    Workshop Feature: Hashes a specific region (like NVRAM or ME block).
    Extremely useful for comparing Donor and Original sections byte-by-byte 
    without saving them to disk first.
    """
    if not data or start_offset < 0 or start_offset + length > len(data):
        return {
            "md5": "Error", "sha1": "Error", "sha256": "Error", "crc32": "Error"
        }
    
    region_slice = data[start_offset:start_offset + length]
    return calculate_hashes(region_slice)


def calculate_file_hashes(file_path: str) -> Dict[str, str]:
    """
    Calculates hashes by streaming chunks directly from file storage.
    Optimized for high performance on large BIOS dumps.
    """
    md5_hash = hashlib.md5()
    sha1_hash = hashlib.sha1()
    sha256_hash = hashlib.sha256()
    crc32_val = 0

    chunk_size = 65536  # 64 KB chunk size

    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)
                sha1_hash.update(chunk)
                sha256_hash.update(chunk)
                crc32_val = zlib.crc32(chunk, crc32_val)

        return {
            "md5": md5_hash.hexdigest(),
            "sha1": sha1_hash.hexdigest(),
            "sha256": sha256_hash.hexdigest(),
            "crc32": f"{crc32_val & 0xFFFFFFFF:08X}",
        }
    except Exception:
        return {
            "md5": "Error Reading File",
            "sha1": "Error Reading File",
            "sha256": "Error Reading File",
            "crc32": "Error Reading File",
        }


def verify_file_integrity(file_path: str, expected_hash: str, algo: str = "sha256") -> bool:
    """
    Workshop Feature: Checks if a downloaded/donor file matches its known good hash.
    Helps prevent writing corrupted donor files to the motherboard.
    """
    hashes = calculate_file_hashes(file_path)
    actual_hash = hashes.get(algo.lower(), "")
    return actual_hash.lower() == expected_hash.lower()

if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - Hashing Engine Loaded.")