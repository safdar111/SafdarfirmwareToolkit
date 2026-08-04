# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.1.1
# File    : hash_utils.py
# =====================================================

import hashlib


def calculate_md5(data: bytes) -> str:
    """Return MD5 hash of firmware."""
    return hashlib.md5(data).hexdigest()


def calculate_sha1(data: bytes) -> str:
    """Return SHA1 hash of firmware."""
    return hashlib.sha1(data).hexdigest()


def calculate_sha256(data: bytes) -> str:
    """Return SHA256 hash of firmware."""
    return hashlib.sha256(data).hexdigest()


def calculate_hashes(data: bytes) -> dict:
    """Return all hashes in one dictionary."""
    return {
        "md5": calculate_md5(data),
        "sha1": calculate_sha1(data),
        "sha256": calculate_sha256(data),
    }