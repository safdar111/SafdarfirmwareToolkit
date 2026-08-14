import os
from core.dmi_engine import DMIEngine
from core.csme_engine import CSMEInspector
from core.firmware import FirmwareImage
from core.repair_planner import RepairPlanner


class Analyzer:
    """
    Main Diagnostic & Analyzer Engine for Safdar Firmware Toolkit Pro.
    Accepts extra GUI arguments gracefully to avoid positional argument mismatch.
    """

    def __init__(self, file_path: str, *args, **kwargs):
        self.file_path = file_path
        self.extra_args = args
        self.file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        with open(file_path, 'rb') as f:
            self.data = f.read()

        self.firmware = FirmwareImage(file_path)
        self.firmware.load()
        self.dmi = DMIEngine(self.data, source_name=os.path.basename(file_path))
        self.csme = CSMEInspector(self.data)
        self.planner = RepairPlanner()

    def _classify_chip_role(self) -> dict:
        """Heuristic classification for primary BIOS vs backup/recovery chip."""
        dmi_info = self.dmi.run_full_diagnostic()
        csme_info = self.csme.analyze_file(self.data)
        if dmi_info["ifd_health"]["status"] == "OK" and csme_info.get("has_me_region"):
            return {
                "role": "Primary BIOS / likely active firmware",
                "confidence": "High",
                "reason": "Valid Intel IFD plus ME region detected. This is the most likely active BIOS image.",
            }
        if self.file_size <= 2 * 1024 * 1024:
            return {
                "role": "Recovery / small secondary image",
                "confidence": "Medium",
                "reason": "Small image size often indicates recovery or partial backup image rather than the primary BIOS.",
            }
        return {
            "role": "Unknown / secondary or partial image",
            "confidence": "Low",
            "reason": "No strong descriptor/ME evidence for active BIOS ownership detected.",
        }

    def generate_report(self) -> str:
        dmi_info = self.dmi.run_full_diagnostic()
        csme_info = self.csme.analyze_file(self.data)
        csme_ver = csme_info.get("version", "Unknown")
        csme_status = csme_info.get("status_text", "Unknown State")

        is_ifd_ok = dmi_info["ifd_health"]["status"] in ["OK", "WARNING/NON-INTEL"]
        is_csme_detected = csme_ver not in ("Unknown", "N/A", "Version Unidentified")
        chip_role = self._classify_chip_role()

        report = []
        report.append("=================================================================")
        report.append("         SAFDAR FIRMWARE TOOLKIT PRO - DIAGNOSTIC REPORT         ")
        report.append("=================================================================")
        report.append(f"Target Binary Path : {os.path.basename(self.file_path)}")
        report.append(f"Binary Size        : {self.file_size} Bytes ({self.file_size // (1024*1024)} MB)")
        report.append(f"Chip Role          : {chip_role['role']}")
        report.append(f"Role Confidence    : {chip_role['confidence']}")
        report.append("")
        report.append("1. SYSTEM IDENTITY & HARDWARE TAGS (DMI & SILK-SCREEN)")
        report.append("-----------------------------------------------------------------")
        report.append(f"Motherboard Part No : {dmi_info['board_number']}")
        report.append(f"HP Board ID (BID)   : {dmi_info['hp_bid']}")
        report.append(f"HP Short BID/Rev   : {dmi_info.get('hp_bid_short', 'Not Found')}")
        report.append(f"Dell Service Tag    : {dmi_info['dell_tag']}")
        report.append(f"Serial Number       : {dmi_info['serial_number']}")
        report.append(f"Windows DPK         : {dmi_info['windows_dpk']}")
        report.append("")
        report.append("2. INTEL CSME / ME / TXE HEALTH ENGINE")
        report.append("-----------------------------------------------------------------")
        report.append(f"CSME Version        : {csme_ver}")
        report.append(f"CSME State          : {csme_status}")
        report.append(f"Flash Descriptor    : {dmi_info['ifd_health']['reason']}")
        report.append(f"Intel Boot Guard    : {dmi_info['boot_guard']['status']}")
        report.append("")
        report.append("3. REGION INTEGRITY & WORKSHOP DIAGNOSTIC RECOMMENDATION")
        report.append("-----------------------------------------------------------------")

        if is_ifd_ok:
            report.append("Integrity Status    : ✅ HEALTHY / STRUCTURE VALID")
        else:
            report.append("Integrity Status    : ⚠️ STRUCTURE SUSPECT / NOT CONFIRMED")

        if csme_status.lower().startswith("clean") or csme_status.lower().startswith("configured"):
            report.append("CSME State Summary  : 🟢 CLEAN / CONFIGURED (not necessarily corrupt)")
        else:
            report.append("CSME State Summary  : 🔴 DIRTY / INITIALIZED / REQUIRES REVIEW")

        if is_ifd_ok and is_csme_detected:
            report.append("Action Recommended  : 🛑 DO NOT REFLASH / REPAIR THIS BIOS IMMEDIATELY")
            report.append("Diagnostic Note     : The file is structurally intact; the firmware may still be configured or platform-paired.")
            report.append("")
            report.append("⚠️ WORKSHOP HARDWARE ADVISORY:")
            report.append("If motherboard has No Power, No Display, or Power-Looping:")
            report.append("  1. Verify VCCRAM, VCCIN, and +3VS5/+5VS5 power rails.")
            report.append("  2. Check RAM slot pins, SODIMM contacts, or CPU clock signals.")
            report.append("  3. Check RSMRST# and PWRBTN# signals on the Embedded Controller.")
        else:
            report.append("Action Recommended  : Proceed with CSME Cleaning, NVRAM Reset, or Splicing Wizard.")
            report.append("Repair Risk         : Keep original DMI blocks to preserve serial numbers & BID.")

        report.append("Chip Role Summary   : " + chip_role['reason'])
        report.append("=================================================================")
        return "\n".join(report)

    def analyze_single(self) -> dict:
        """Return the structured result the GUI expects for single file analysis."""
        dmi_info = self.dmi.run_full_diagnostic()
        csme_info = self.csme.analyze_file(self.data)
        chip_role = self._classify_chip_role()
        password_storage = self.planner.password_storage_assessment(
            file_size=self.file_size,
            ifd_ok=dmi_info.get("ifd_health", {}).get("status") in ["OK", "WARNING/NON-INTEL"],
            has_me_region=bool(csme_info.get("has_me_region", False)),
            has_uefi=self.firmware.get_flash_label() and "EFI" in self.firmware.get_flash_label(),
        )

        result = {
            "firmware": self.firmware,
            "csme": {
                "version": csme_info.get("version", "Unknown"),
                "state": csme_info.get("status_text", "Unknown State"),
                "has_me_region": csme_info.get("has_me_region", False),
                "is_clean": csme_info.get("is_clean", False),
                "description": csme_info.get("description", "No description available."),
            },
            "dmi": {
                "board_number": dmi_info.get("board_number", "Not Found"),
                "hp_bid": dmi_info.get("hp_bid", "Not Found"),
                "hp_bid_short": dmi_info.get("hp_bid_short", "Not Found"),
                "dell_service_tag": {"value": dmi_info.get("dell_tag", "Not Found")},
                "serial_number": dmi_info.get("serial_number", "Not Found"),
                "windows_dpk": {"value": dmi_info.get("windows_dpk", "Not Found")},
                "ifd_health": dmi_info.get("ifd_health", {"status": "UNKNOWN", "reason": "Not available"}),
                "boot_guard": dmi_info.get("boot_guard", {"status": "UNKNOWN", "note": "Not available"}),
            },
            "chip_role": chip_role,
            "password_storage": password_storage,
            "report_text": self.generate_report(),
        }
        return result

    def build_workshop_plan(self, donor_path: str = None) -> dict:
        """Create a structured workshop repair plan including chip role and donor compatibility."""
        original = self.analyze_single()
        if not donor_path:
            return {
                "original": original,
                "donor": None,
                "chip_role": original["chip_role"],
                "plan": {
                    "status": "Donor not provided",
                    "recommendation": "Select a known-good donor image to assess compatibility before repair.",
                },
            }

        donor = Analyzer(donor_path)
        donor_info = donor.analyze_single()
        compat = self.planner.donor_compatibility(original, donor_info)
        reco = self.planner.repair_recommendation(original, donor_info)

        return {
            "original": original,
            "donor": donor_info,
            "chip_role": original["chip_role"],
            "donor_compatibility": compat,
            "repair_recommendation": reco,
            "plan": {
                "status": "Ready for review",
                "recommendation": reco["warning"],
            },
        }

    def analyze_dual(self) -> dict:
        """Compare original dump with donor image and summarize compatibility and repair notes."""
        donor_path = self.extra_args[0] if len(self.extra_args) > 0 else None
        if not donor_path:
            raise ValueError("Dual analysis requires a donor BIOS file path as the second argument.")

        original = self.analyze_single()
        donor = Analyzer(donor_path)
        donor_info = donor.analyze_single()
        compat = self.planner.donor_compatibility(original, donor_info)
        recommendation = self.planner.repair_recommendation(original, donor_info)

        original_version = original["csme"]["version"]
        donor_version = donor_info["csme"]["version"]
        same_version = original_version == donor_version

        report = []
        report.append("=================================================================")
        report.append("          DUAL-BIOS REPAIR / DONOR COMPATIBILITY ANALYSIS         ")
        report.append("=================================================================")
        report.append(f"Original File     : {os.path.basename(self.file_path)}")
        report.append(f"Donor File        : {os.path.basename(donor_path)}")
        report.append(f"Original CSME     : {original_version}")
        report.append(f"Donor CSME        : {donor_version}")
        report.append(f"Version Match     : {'YES' if same_version else 'NO'}")
        report.append(f"Original Chip Role: {original['chip_role']['role']}")
        report.append(f"Donor Chip Role   : {donor_info['chip_role']['role']}")
        report.append(f"Compatibility     : {compat['verdict']} ({compat['score']}/100)")
        report.append("")
        report.append("Repair Recommendation:")
        for detail in compat["details"]:
            report.append(f"- {detail}")
        report.append(f"- {recommendation['warning']}")
        report.append("- Preserve original DMI/NVRAM identity blocks during repair.")
        report.append("=================================================================")

        return {
            "original": original,
            "donor": donor_info,
            "report_text": "\n".join(report),
            "version_match": same_version,
            "compatible": compat["score"] >= 70,
            "donor_compatibility": compat,
            "repair_recommendation": recommendation,
        }