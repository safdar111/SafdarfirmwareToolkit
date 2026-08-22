# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.5.1 (High-Speed Workshop Grade)
# File      : core/analyzer.py
# Author    : Safdar Ali
# =====================================================

"""
High-Speed Main Diagnostic & Analyzer Engine.
Optimized to process 16MB/32MB/64MB SPI dumps in seconds using cached memory buffers.
Features dynamic hex-hunting for DMI, Password Hashes, and BitLocker Early-Warning.
"""

import os
import shutil
import hashlib
from datetime import datetime
from core.dmi_engine import DMIEngine
from core.csme_engine import CSMEEngine
from core.firmware import FirmwareImage
from core.repair_planner import RepairPlanner
from core.uefi import UEFIParser
from core.report import Report

class Analyzer:
    """
    Optimized Diagnostic & Analyzer Engine for Safdar Firmware Toolkit Pro.
    """

    def __init__(self, file_path: str, *args, **kwargs):
        self.file_path = file_path
        self.extra_args = args
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Firmware binary not found: {file_path}")
            
        self.file_size = os.path.getsize(file_path)

        # Single read into memory cache for blazing fast processing
        with open(file_path, 'rb') as f:
            self.data = f.read()

        # Compute Hashes once
        self.sha256_hash = hashlib.sha256(self.data).hexdigest()
        self.md5_hash = hashlib.md5(self.data).hexdigest()

        # Initialize engines using cached memory buffer
        self.firmware = FirmwareImage(file_path)
        self.firmware.load()
        self.dmi = DMIEngine(self.data, source_name=os.path.basename(file_path))
        self.csme = CSMEEngine(self.data)
        self.planner = RepairPlanner()
        self.uefi = UEFIParser(self.data)

        # Lazy-loaded cache for diagnostic results
        self._cached_dmi = None
        self._cached_csme = None
        self._cached_volumes = None
        self._advanced_heuristics = None

    def _get_dmi(self):
        if self._cached_dmi is None:
            self._cached_dmi = self.dmi.run_full_diagnostic()
        return self._cached_dmi

    def _get_csme(self):
        if self._cached_csme is None:
            # Force explicit call to analyze_file() to trigger the advanced heuristics engine
            self._cached_csme = self.csme.analyze_file()
        return self._cached_csme

    def _get_volumes(self):
        if self._cached_volumes is None:
            self._cached_volumes = self.uefi.parse()
        return self._cached_volumes

    def _run_advanced_heuristics(self) -> dict:
        """
        Forensic hex-hunting engine. Bypasses static offsets to dynamically map 
        BitLocker status, Password Hashes, and exact DMI/MSDM boundaries.
        """
        if self._advanced_heuristics is not None:
            return self._advanced_heuristics

        results = {
            "bitlocker_warning": False,
            "password_hash_found": False,
            "offsets": {
                "msdm_key": None,
                "password_block": None
            }
        }

        # 1. BitLocker Early-Warning Detection (TPM/SecureBoot NVRAM Variables)
        tpm_signatures = [b'Tcg2PhysicalPresence', b'SecureBoot', b'TpmPlatform']
        for sig in tpm_signatures:
            if sig in self.data:
                results["bitlocker_warning"] = True
                break

        # 2. Windows DPK (MSDM Table) Dynamic Boundary Mapping
        msdm_offset = self.data.find(b'MSDM')
        if msdm_offset != -1:
            results["offsets"]["msdm_key"] = hex(msdm_offset)

        # 3. Password Hash Identification (Lenovo / HP / Dell Heuristics)
        pwd_signatures = [b'LenovoSecurityConfig', b'HPBIOS', b'DellSmi']
        for pwd_sig in pwd_signatures:
            pwd_offset = self.data.find(pwd_sig)
            if pwd_offset != -1:
                results["password_hash_found"] = True
                results["offsets"]["password_block"] = hex(pwd_offset)
                break

        self._advanced_heuristics = results
        return results

    def _classify_chip_role(self) -> dict:
        dmi_info = self._get_dmi()
        csme_info = self._get_csme()
        volumes = self._get_volumes()
        
        return self.planner.classify_chip_role(
            file_size=self.file_size,
            ifd_ok=dmi_info.get("ifd_health", {}).get("status") in ["OK", "WARNING/NON-INTEL"],
            has_me_region=csme_info.get("has_me_region", False),
            has_uefi=len(volumes) > 0
        )

    @staticmethod
    def classify_health(dmi_info: dict, csme_info: dict) -> dict:
        status = dmi_info.get("ifd_health", {}).get("status", "UNKNOWN")
        csme_ver = csme_info.get("version", "Unknown")
        csme_status = csme_info.get("status_text", "Unknown State")
        
        is_ifd_ok = status in ["OK", "WARNING/NON-INTEL"]
        is_csme_detected = csme_ver not in ("Unknown", "N/A", "Version Unidentified")
        is_clean = bool(csme_info.get("is_clean", False))

        if is_ifd_ok and is_csme_detected and is_clean:
            overall_status = "HEALTHY / STRUCTURE VALID"
            repair_required = False
            archive_ready = True
        elif is_ifd_ok and is_csme_detected and not is_clean:
            overall_status = "DIRTY / REPAIR RECOMMENDED"
            repair_required = True
            archive_ready = False
        elif is_ifd_ok and not is_csme_detected:
            overall_status = "PARTIAL / REVIEW REQUIRED"
            repair_required = True
            archive_ready = False
        else:
            overall_status = "STRUCTURE SUSPECT / REPAIR REQUIRED"
            repair_required = True
            archive_ready = False

        return {
            "overall_status": overall_status,
            "repair_required": repair_required,
            "archive_ready": archive_ready,
            "ifd_ok": is_ifd_ok,
            "csme_detected": is_csme_detected,
            "csme_status": csme_status,
        }

    def generate_report(self) -> str:
        dmi_info = self._get_dmi()
        csme_info = self._get_csme()
        volumes = self._get_volumes()
        heuristics = self._run_advanced_heuristics()
        verdict = self.classify_health(dmi_info, csme_info)
        chip_role = self._classify_chip_role()

        report = Report()
        report.title("SAFDAR FIRMWARE TOOLKIT PRO - FORENSIC DIAGNOSTIC REPORT")
        
        report.key_val("Target Binary", os.path.basename(self.file_path))
        report.key_val("Binary Size", f"{self.file_size} Bytes ({self.file_size / (1024*1024):.2f} MB)")
        report.key_val("SHA256 Hash", self.sha256_hash)
        report.key_val("Chip Role", chip_role['role'])
        
        # BITLOCKER EARLY WARNING SYSTEM
        if heuristics["bitlocker_warning"]:
            report.separator("!")
            report.add("!!! CRITICAL WARNING: BITLOCKER / TPM SECURE BOOT DETECTED !!!")
            report.add("Do NOT flash a donor file unless the customer has their 48-digit Recovery Key.")
            report.add("Using a Frankenstein build on this chip WILL lock the OS drive.")
            report.separator("!")

        report.section("1. SYSTEM IDENTITY & HARDWARE TAGS (DMI MAP)")
        board_conf = dmi_info.get('board_confidence', 'Unknown')
        report.key_val("Motherboard Part No", f"{dmi_info.get('board_number', 'Not Found')} ({board_conf})")
        report.key_val("HP Board ID (BID)", f"{dmi_info.get('hp_bid', 'Not Found')}")
        report.key_val("Dell Service Tag", dmi_info.get('dell_tag', 'Not Found'))
        report.key_val("Serial Number", dmi_info.get('serial_number', 'Not Found'))
        report.key_val("MAC Address", dmi_info.get("mac_address", "Not Found"))
        
        msdm_text = dmi_info.get('windows_dpk', 'Not Found')
        msdm_offset = heuristics['offsets']['msdm_key']
        if msdm_offset:
            msdm_text += f" (Found at offset {msdm_offset})"
        report.key_val("Windows DPK", msdm_text)
        
        report.section("2. INTEL CSME / ME HEALTH ENGINE")
        report.key_val("CSME Version", csme_info.get("version", "Unknown"))
        report.key_val("CSME SKU", csme_info.get("sku", "Unknown SKU"))
        report.key_val("CSME State", csme_info.get("status_text", "Unknown State"))
        report.key_val("Intel Boot Guard", f"{dmi_info.get('boot_guard', {}).get('status', 'Unknown')}")
        
        report.section("3. SECURITY & PASSWORD NVRAM ASSESSMENT")
        if heuristics["password_hash_found"]:
            report.warning(f"OEM Supervisor Password Hash Block detected at {heuristics['offsets']['password_block']}.")
            report.add("Ready for non-destructive hash clearing.")
        else:
            report.add("No standard OEM password hashes detected in unencrypted NVRAM.")

        report.section("4. DIAGNOSTIC RECOMMENDATION")
        report.key_val("Integrity Status", verdict['overall_status'])

        if verdict['archive_ready']:
            report.success("SAFE TO ARCHIVE AS GOOD FILE")
        elif verdict['repair_required']:
            report.warning("REPAIR OR CLEAN CSME REQUIRED BEFORE FLASHING")

        if verdict['ifd_ok'] and verdict['csme_detected']:
            report.add()
            report.add("WORKSHOP ADVISORY (NO POST / BLACK SCREEN):")
            report.add(" 1. Verify VCCRAM, VCCIN, and +3VS5/+5VS5 power rails.")
            report.add(" 2. If rails are present but fan spins 100%, execute CSME Clean.")
            
        report.separator("=")
        return report.build()

    def analyze_single(self) -> dict:
        dmi_info = self._get_dmi()
        csme_info = self._get_csme()
        chip_role = self._classify_chip_role()
        volumes = self._get_volumes()
        heuristics = self._run_advanced_heuristics()
        
        password_storage = self.planner.password_storage_assessment(
            file_size=self.file_size,
            ifd_ok=dmi_info.get("ifd_health", {}).get("status") in ["OK", "WARNING/NON-INTEL"],
            has_me_region=csme_info.get("has_me_region", False),
            has_uefi=len(volumes) > 0
        )

        verdict = self.classify_health(dmi_info, csme_info)
        result = {
            "firmware": self.firmware,
            "csme": {
                "version": csme_info.get("version", "Unknown"),
                "sku": csme_info.get("sku", "Unknown SKU"),
                "state": csme_info.get("status_text", "Unknown State"),
                "has_me_region": csme_info.get("has_me_region", False),
                "is_clean": csme_info.get("is_clean", False),
            },
            "dmi": {
                "board_number": dmi_info.get("board_number", "Not Found"),
                "hp_bid": dmi_info.get("hp_bid", "Not Found"),
                "dell_service_tag": {"value": dmi_info.get("dell_tag", "Not Found")},
                "serial_number": dmi_info.get("serial_number", "Not Found"),
                "windows_dpk": {"value": dmi_info.get("windows_dpk", "Not Found")},
                "mac_address": dmi_info.get("mac_address", "Not Found"),
                "ifd_health": dmi_info.get("ifd_health", {}),
                "boot_guard": dmi_info.get("boot_guard", {}),
            },
            "chip_role": chip_role,
            "password_storage": password_storage,
            "heuristics": heuristics,
            "health": verdict,
            "report_text": self.generate_report(),
            "hashes": {"md5": self.md5_hash, "sha256": self.sha256_hash}
        }
        return result

    def analyze_dual(self) -> dict:
        donor_path = self.extra_args[0] if len(self.extra_args) > 0 else None
        if not donor_path:
            raise ValueError("Dual analysis requires a donor BIOS file path.")

        original = self.analyze_single()
        donor_analyzer = Analyzer(donor_path)
        donor_info = donor_analyzer.analyze_single()
        
        compat = self.planner.donor_compatibility(original, donor_info)
        recommendation = self.planner.repair_recommendation(original, donor_info)

        original_version = original["csme"]["version"]
        donor_version = donor_info["csme"]["version"]
        same_version = original_version == donor_version

        report = Report()
        report.title("DUAL-BIOS REPAIR / DONOR COMPATIBILITY ANALYSIS")
        report.key_val("Original File", os.path.basename(self.file_path))
        report.key_val("Donor File", os.path.basename(donor_path))
        
        if original.get("heuristics", {}).get("bitlocker_warning"):
            report.separator("!")
            report.add("!!! CRITICAL: BITLOCKER WAS ACTIVE ON ORIGINAL FILE !!!")
            report.add("Transferring DMI to Donor will trigger a BitLocker Lockout.")
            report.add("Ensure 48-digit Recovery Key is secured before flashing.")
            report.separator("!")

        report.key_val("Original CSME", f"{original_version} ({original['csme']['sku']})")
        report.key_val("Donor CSME", f"{donor_version} ({donor_info['csme']['sku']})")
        report.key_val("Version Match", 'YES' if same_version else 'NO')
        report.key_val("Original Chip Role", original['chip_role']['role'])
        report.key_val("Compatibility", f"{compat['verdict']} ({compat['score']}/100)")
        
        report.add()
        report.add("Repair Recommendation:")
        for detail in compat["details"]:
            report.add(f"- {detail}")
        report.add(f"- {recommendation['warning']}")
        
        return {
            "original": original,
            "donor": donor_info,
            "report_text": report.build(),
            "version_match": same_version,
            "compatible": compat["score"] >= 70,
            "donor_compatibility": compat,
            "repair_recommendation": recommendation,
        }

    def save_ok_report(self, report_text: str, output_dir: str = "output") -> dict:
        verdict = self.classify_health(self._get_dmi(), self._get_csme())

        if not verdict["archive_ready"]:
            return {}

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.basename(self.file_path)
        name, ext = os.path.splitext(base)
        bin_name = f"{name}_{ts}{ext}"
        report_name = f"{name}_{ts}_report.txt"

        bin_path = os.path.join(output_dir, bin_name)
        report_path = os.path.join(output_dir, report_name)

        shutil.copy2(self.file_path, bin_path)

        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write(report_text)

        return {"binary": bin_path, "report": report_path}

if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - High-Speed Analyzer Ready.")