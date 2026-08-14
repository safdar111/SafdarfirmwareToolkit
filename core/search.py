# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : core/search.py
# Author  : Safdar Ali
# =====================================================

"""
Local CSME/ME Repository Search Engine & Hex Offset Utilities.
Scans the local database directory to find exact matching Clean CSME binaries
and provides string/sequence search and offset formatting helper functions.
"""

import os
import re
from typing import Optional, List, Dict, Any, Union


def hex_offset(offset: Union[int, str]) -> str:
    """
    Formats integer offsets into standardized uppercase hexadecimal strings (e.g., 0x00010000).
    """
    if isinstance(offset, str):
        return offset
    return f"0x{offset:08X}"


def find_all(data: bytes, pattern: bytes) -> List[int]:
    """
    Finds all byte pattern occurrences inside a binary buffer.
    """
    return [m.start() for m in re.finditer(re.escape(pattern), data)]


def find_sequence(data: bytes, pattern: bytes) -> List[int]:
    """
    Alias for find_all to maintain backwards compatibility.
    """
    return find_all(data, pattern)


class CSMERepositorySearch:
    """
    Searches local database/csme_repository/ directory for matching Clean ME files.
    """

    def __init__(self, repo_dir: str = "database/csme_repository"):
        self.repo_dir = repo_dir

    def ensure_repo_exists(self) -> None:
        """
        Ensures the repository directory exists on disk.
        """
        if not os.path.exists(self.repo_dir):
            os.makedirs(self.repo_dir, exist_ok=True)

    def find_matching_clean_me(self, target_version: str) -> Optional[str]:
        """
        Scans repo directory for filenames containing the target CSME version string.
        Example: Version "11.8.50.3425" matches "11.8.50.3425_CON_LP_C0_PRD_CLR.bin"
        """
        self.ensure_repo_exists()

        if not target_version or target_version in ["N/A", "Detected (Version Header Unparsed)"]:
            return None

        # Clean search version token
        clean_target = target_version.strip()

        for root, _, files in os.walk(self.repo_dir):
            for file in files:
                if file.lower().endswith((".bin", ".rgn", ".me")):
                    if clean_target in file:
                        return os.path.join(root, file)

        return None

    def list_available_binaries(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all Clean CSME binaries currently indexed in the local repository.
        """
        self.ensure_repo_exists()
        repo_files = []

        for root, _, files in os.walk(self.repo_dir):
            for file in files:
                if file.lower().endswith((".bin", ".rgn", ".me")):
                    path = os.path.join(root, file)
                    size = os.path.getsize(path)
                    repo_files.append({
                        "filename": file,
                        "path": path,
                        "size": size,
                    })

        return repo_files