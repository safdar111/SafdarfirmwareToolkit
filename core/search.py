# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.5.0 (Dynamic Workshop Engine)
# File      : core/search.py
# Author    : Safdar Ali
# =====================================================

"""
Local CSME/ME Repository Search Engine & Hex Offset Utilities.
Dynamically links to the user's selected UI database path.
Scans for EXACT matching Clean CSME binaries based on Version AND SKU 
(Corporate/Consumer, LP/H) to prevent PCH power states and 30-min shutdown issues.
"""

import os
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
    Optimized for high-speed scanning on large 16MB/32MB/64MB dumps.
    """
    positions = []
    pos = data.find(pattern)
    while pos != -1:
        positions.append(pos)
        pos = data.find(pattern, pos + len(pattern))
    return positions


def find_sequence(data: bytes, pattern: bytes) -> List[int]:
    """Alias for find_all to maintain backwards compatibility with older modules."""
    return find_all(data, pattern)


class CSMERepositorySearch:
    """
    Smart search engine that links to the GUI's custom folder path.
    Prioritizes Exact Match (Version + SKU) to prevent wrong platform injection.
    """

    def __init__(self, repo_dir: Optional[str] = None):
        # Default fallback, but allows dynamic injection from the PyQt6 dashboard
        self.repo_dir = repo_dir if repo_dir else os.path.join(os.getcwd(), "database", "csme_repository")

    def ensure_repo_exists(self) -> None:
        """Ensures the repository directory exists on disk."""
        if not os.path.exists(self.repo_dir):
            try:
                os.makedirs(self.repo_dir, exist_ok=True)
            except Exception:
                pass # If user selected a protected system drive, ignore creation

    def find_matching_clean_me(self, target_version: str, target_sku: Optional[str] = None) -> Optional[str]:
        """
        Scans repo directory for filenames matching the exact CSME version AND SKU profile.
        Example: Version "11.8.50.3425" + SKU "Corporate H" -> Matches "11.8.50.3425_COR_H.bin"
        """
        if not os.path.exists(self.repo_dir):
            return None

        if not target_version or target_version in ["N/A", "Detected (Version Header Unparsed)", "Unknown"]:
            return None

        clean_target = target_version.strip()
        
        # Build aggressive SKU filter tags
        sku_tags = []
        if target_sku:
            target_sku_upper = target_sku.upper()
            
            # Identify Corporate vs Consumer
            if "CORPORATE" in target_sku_upper or "COR" in target_sku_upper:
                sku_tags.append("COR")
            elif "CONSUMER" in target_sku_upper or "CON" in target_sku_upper:
                sku_tags.append("CON")
                
            # Identify Power Profile (Low Power vs High Performance)
            # Pad with underscores or dashes to prevent matching 'H' inside other words
            if "LP" in target_sku_upper:
                sku_tags.append("LP")
            elif " H " in target_sku_upper or "-H" in target_sku_upper or "_H" in target_sku_upper or target_sku_upper.endswith(" H"):
                sku_tags.append("H")

        best_match = None
        fallback_match = None

        # Recursively search the user's selected folder
        for root, _, files in os.walk(self.repo_dir):
            for file in files:
                file_upper = file.upper()
                if file_upper.endswith((".BIN", ".RGN", ".ME")):
                    
                    # 1. Primary Check: Version must be in the filename
                    if clean_target in file_upper:
                        
                        # 2. Secondary Check: SKU validation
                        if sku_tags:
                            matches_all_tags = all(tag in file_upper for tag in sku_tags)
                            if matches_all_tags:
                                best_match = os.path.join(root, file)
                                return best_match # Immediate return on perfect match
                            else:
                                # Save as fallback if version matches but SKU tags are missing/unclear
                                fallback_match = os.path.join(root, file)
                        else:
                            best_match = os.path.join(root, file)
                            return best_match

        # If we reach here, no perfect match was found.
        # We return the fallback, but the GUI will handle the risk warning.
        if fallback_match:
            print(f"[!] Warning: Found ME version {target_version}, but SKU {target_sku} may not exactly match.")
            return fallback_match

        return None

    def list_available_binaries(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all Clean CSME binaries currently indexed in the selected directory.
        """
        self.ensure_repo_exists()
        repo_files = []

        if not os.path.exists(self.repo_dir):
            return repo_files

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

if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - Dynamic Search Engine Ready.")