# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : core/hash_utils.py
# Author  : Safdar Ali
# =====================================================

"""
Streamed Hashing Engine.
Calculates MD5, SHA1, SHA256, and CRC32 checksums for firmware verification.
"""

import hashlib
import zlib
from typing import Dict


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