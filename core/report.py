# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.4.0 (Workshop Grade)
# File      : core/report.py
# Author    : Safdar Ali
# =====================================================

"""
Structured Diagnostic Report Generation Engine.
Builds formatted ASCII text reports for GUI display, 
customer printouts, and exported log files.
"""

import os
from typing import List

class Report:
    """
    Helper class to format diagnostic lines, section headers, 
    warnings, and structured workshop outputs.
    """

    def __init__(self, width: int = 70):
        self.width = width
        self.lines: List[str] = []

    def title(self, text: str) -> None:
        """Adds a centered main title box."""
        border = "=" * self.width
        self.lines.append(border)
        self.lines.append(text.center(self.width))
        self.lines.append(border)
        self.lines.append("")

    def section(self, title: str) -> None:
        """Adds a distinct section header (e.g., 1. SYSTEM IDENTITY)."""
        self.lines.append("")
        self.lines.append(title.upper())
        self.lines.append("-" * self.width)

    def add(self, text: str = "") -> None:
        """Adds a single text line."""
        self.lines.append(text)

    def success(self, text: str) -> None:
        """Adds a success/ok line with a visual tag."""
        self.lines.append(f"[+] {text}")

    def warning(self, text: str) -> None:
        """Adds a critical warning line with a visual tag."""
        self.lines.append(f"[!] WARNING: {text}")

    def separator(self, char: str = "-") -> None:
        """Adds a horizontal rule line across the report width."""
        self.lines.append(char * self.width)

    def key_val(self, key: str, val: str, padding: int = 22) -> None:
        """
        Adds a padded key-value pair line. 
        Handles multi-line values to keep alignment clean.
        """
        val_str = str(val)
        if "\n" in val_str:
            parts = val_str.split("\n")
            self.lines.append(f"{key.ljust(padding)}: {parts[0]}")
            for part in parts[1:]:
                self.lines.append(f"{' ' * padding}  {part}")
        else:
            self.lines.append(f"{key.ljust(padding)}: {val_str}")

    def build(self) -> str:
        """Returns the full compiled text report string."""
        return "\n".join(self.lines)

    def save_to_log(self, filepath: str) -> bool:
        """Saves the compiled report to a text file for workshop records."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.build())
            return True
        except Exception as e:
            self.warning(f"Failed to save report: {str(e)}")
            return False

if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - Report Engine Ready.")