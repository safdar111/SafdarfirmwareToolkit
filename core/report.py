# =====================================================
# Safdar Firmware Toolkit Pro
# Report Generator
# Version 0.1.1
# =====================================================

class Report:

    def __init__(self):

        self.lines = []

    def add(self, text=""):

        self.lines.append(str(text))

    def separator(self):

        self.lines.append("-" * 60)

    def title(self, text):

        self.separator()

        self.add(text)

        self.separator()

    def build(self):

        return "\n".join(self.lines)