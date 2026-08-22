# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.4.0 (Workshop Grade)
# File      : core/health.py
# Author    : Safdar Ali
# =====================================================

"""
Firmware Diagnostic & Health Scoring Engine.
Calculates overall structural health and categorizes issues 
into FATAL, CRITICAL, WARNING, and INFO for workshop reports.
"""

class FirmwareHealth:
    def __init__(self):
        self.score = 100
        self.is_fatal = False
        self.issues = {
            "CRITICAL": [],
            "WARNING": [],
            "INFO": []
        }

    def add_fatal(self, message: str):
        """
        Triggers an immediate failure for unrecoverable structural damage 
        (e.g., missing descriptor, empty 0xFF dump).
        """
        self.score = 0
        self.is_fatal = True
        self.issues["CRITICAL"].append(f"[FATAL] {message}")

    def add_issue(self, severity: str, points: int, message: str):
        """
        Deducts points and logs an issue based on severity (CRITICAL, WARNING, INFO).
        """
        if self.is_fatal:
            pass # Score is already 0, but we still log the issue
        else:
            self.score -= points
            if self.score < 0:
                self.score = 0

        sev = severity.upper()
        if sev in self.issues:
            self.issues[sev].append(message)
        else:
            self.issues["INFO"].append(message)

    def health(self) -> int:
        return self.score

    def status(self) -> str:
        """Returns a workshop-friendly string based on the current score."""
        if self.is_fatal or self.score < 40:
            return "CRITICAL (Requires Donor / Rebuild)"

        if self.score >= 95:
            return "EXCELLENT (Ready to Flash / Archive)"

        if self.score >= 80:
            return "GOOD (Minor Warnings / Missing Tags)"

        if self.score >= 60:
            return "FAIR (Review Required before Flash)"

        return "POOR (Repair Recommended)"

    def report(self) -> dict:
        """
        Returns a structured dictionary of all categorized issues for the GUI or CLI.
        """
        has_issues = any(len(lst) > 0 for lst in self.issues.values())
        
        if not has_issues:
            self.issues["INFO"].append("No problems detected. Firmware structure is pristine.")
            
        return self.issues
        
    def generate_text_report(self) -> str:
        """Generates a clean, readable text summary of the health state."""
        lines = []
        lines.append(f"Firmware Health Score : {self.score}/100")
        lines.append(f"Diagnostic Verdict    : {self.status()}")
        lines.append("-" * 50)
        
        for severity in ["CRITICAL", "WARNING", "INFO"]:
            if self.issues[severity]:
                lines.append(f"[{severity} ISSUES]")
                for issue in self.issues[severity]:
                    lines.append(f"  * {issue}")
                lines.append("")
                
        return "\n".join(lines).strip()

if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - Health Engine Loaded.")