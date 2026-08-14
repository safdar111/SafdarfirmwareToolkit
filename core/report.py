# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : core/report.py
# Author  : Safdar Ali
# =====================================================

"""
Structured Diagnostic Report Generation Engine.
Builds formatted ASCII text reports for GUI display and exported log files.
"""

from typing import List


class Report:
    """
    Helper class to format diagnostic lines, section headers, and separators.
    """

    def __init__(self, width: int = 65):
        self.width = width
        self.lines: List[str] = []

    def title(self, text: str) -> None:
        """
        Adds a centered main title box.
        """
        border = "=" * self.width
        self.lines.append(border)
        self.lines.append(text.center(self.width))
        self.lines.append(border)
        self.lines.append("")

    def add(self, text: str = "") -> None:
        """
        Adds a single text line.
        """
        self.lines.append(text)

    def separator(self, char: str = "-") -> None:
        """
        Adds a horizontal rule line across the report width.
        """
        self.lines.append(char * self.width)

    def key_val(self, key: str, val: str, padding: int = 20) -> None:
        """
        Adds a padded key-value pair line (e.g., Motherboard  : LA-F292P).
        """
        self.lines.append(f"{key.ljust(padding)}: {val}")

    def build(self) -> str:
        """
        Returns the full compiled text report string.
        """
        return "\n".join(self.lines)