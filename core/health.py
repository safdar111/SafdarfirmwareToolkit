# =====================================================
# Safdar Firmware Toolkit Pro
# Version : 0.3.0
# File    : health.py
# =====================================================


class FirmwareHealth:

    def __init__(self):

        self.score = 100
        self.messages = []

    def fail(self, points, message):

        self.score -= points

        if self.score < 0:
            self.score = 0

        self.messages.append(message)

    def health(self):

        return self.score

    def status(self):

        if self.score >= 95:
            return "EXCELLENT"

        if self.score >= 80:
            return "GOOD"

        if self.score >= 60:
            return "FAIR"

        if self.score >= 40:
            return "POOR"

        return "CRITICAL"

    def report(self):

        if not self.messages:
            return ["No problems detected."]

        return self.messages