# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.4.0 (Workshop Grade)
# File      : core/repair_planner.py
# Author    : Safdar Ali
# =====================================================

import os
from typing import Dict, Any

class RepairPlanner:
    """
    Workshop-grade donor and chip-role assessment for BIOS repair planning.
    This is intentionally conservative: it prefers classifying a dump as
    primary/recovery/backup based on descriptor, volume presence, and size.
    """

    def classify_chip_role(self, file_size: int, ifd_ok: bool, has_me_region: bool, has_uefi: bool = False) -> Dict[str, Any]:
        if ifd_ok and has_me_region and has_uefi:
            return {
                "role": "Primary BIOS / likely active firmware",
                "confidence": "High",
                "reason": "Valid Intel IFD, ME region, and UEFI volume indicate this is likely the active firmware image.",
            }
        if ifd_ok and has_me_region:
            return {
                "role": "Primary BIOS / candidate active image",
                "confidence": "Medium",
                "reason": "Descriptor and ME region are present, but the UEFI volume is not strongly confirmed.",
            }
        if file_size <= 2 * 1024 * 1024:
            return {
                "role": "Recovery / small secondary image",
                "confidence": "Medium",
                "reason": "Small flash size often matches recovery or backup firmware rather than the active BIOS image.",
            }
        if ifd_ok and not has_me_region:
            return {
                "role": "Secondary / partial image",
                "confidence": "Low",
                "reason": "Descriptor is present but the ME region is missing; this may be a backup, partial, or EC payload.",
            }

        return {
            "role": "Unknown / secondary or partial image",
            "confidence": "Low",
            "reason": "No strong evidence for a primary active BIOS image.",
        }

    def donor_compatibility(self, original: Dict[str, Any], donor: Dict[str, Any]) -> Dict[str, Any]:
        original_version = str(original.get("csme", {}).get("version", "unknown")).lower()
        donor_version = str(donor.get("csme", {}).get("version", "unknown")).lower()
        original_role = original.get("chip_role", {}).get("role", "unknown")
        donor_role = donor.get("chip_role", {}).get("role", "unknown")

        score = 0
        details = []
        
        def parse_ver(v: str):
            try:
                parts = [int(x) for x in v.split('.') if x.isdigit() or x.isnumeric()]
                while len(parts) < 4:
                    parts.append(0)
                return parts[:4]
            except Exception:
                return [0, 0, 0, 0]

        ov = parse_ver(original_version)
        dv = parse_ver(donor_version)

        if ov == dv and any(ov):
            score += 45
            details.append("CSME version exact match.")
        else:
            if ov[0] and dv[0] and ov[0] == dv[0]:
                score += 25
                details.append(f"CSME major version match ({ov[0]}).")
                if ov[1] == dv[1]:
                    score += 10
                    details.append(f"CSME minor version match ({ov[1]}).")
            else:
                details.append("CSME version differs; manual compatibility review required.")

        if "Primary BIOS" in original_role and "Primary BIOS" in donor_role:
            score += 15
            details.append("Both images appear to be primary BIOS candidates.")
        elif "Recovery" in donor_role or "Secondary" in donor_role:
            score -= 15
            details.append("Donor looks like a recovery or secondary image; use with caution.")

        obn = original.get("dmi", {}).get("board_number")
        dbn = donor.get("dmi", {}).get("board_number")
        if obn and dbn:
            if obn == dbn:
                score += 25
                details.append("Board number exact match.")
            else:
                prefixes = ["DA0", "LA-", "6050A", "NM-", "DDA30"]
                matched_prefix = False
                for p in prefixes:
                    if obn.upper().startswith(p) and dbn.upper().startswith(p):
                        matched_prefix = True
                        break
                if matched_prefix:
                    score += 10
                    details.append("Board number vendor-prefix match (likely similar family).")
                else:
                    details.append("Board number differs; donor may not be a correct platform match.")

        if original.get("dmi", {}).get("dell_service_tag", {}).get("value") and donor.get("dmi", {}).get("dell_service_tag", {}).get("value"):
            if original["dmi"]["dell_service_tag"]["value"] == donor["dmi"]["dell_service_tag"]["value"]:
                score += 10
                details.append("Dell tag matches.")

        if original.get("dmi", {}).get("hp_bid") and donor.get("dmi", {}).get("hp_bid"):
            if str(original["dmi"]["hp_bid"]) == str(donor["dmi"]["hp_bid"]):
                score += 10
                details.append("HP BID matches.")

        if donor.get("csme", {}).get("is_clean") and not original.get("csme", {}).get("is_clean"):
            score += 5
            details.append("Donor CSME is clean while original is dirty (useful for repair).")

        if score >= 70:
            verdict = "Compatible / safe donor"
        elif score >= 45:
            verdict = "Possibly compatible / review recommended"
        else:
            verdict = "Incompatible / not recommended"

        return {
            "score": max(0, min(100, score)),
            "verdict": verdict,
            "details": details,
        }

    def repair_recommendation(self, original: Dict[str, Any], donor: Dict[str, Any]) -> Dict[str, Any]:
        compat = self.donor_compatibility(original, donor)
        recommendation = {
            "preserve": [
                "Original DMI / SMBIOS data",
                "Original board identity blocks",
                "Original MAC Address (GbE Region)",
                "Original NVRAM / variable regions when valid",
            ],
            "replace": [
                "Dirty or invalid CSME region",
                "Corrupt ME manifest area",
                "Missing or malformed firmware subregion",
            ],
            "risk": "Low to Medium" if compat["score"] >= 70 else "High",
            "compatibility": compat,
        }

        if compat["score"] < 45:
            recommendation["warning"] = "Do not proceed without manual confirmation. Donor does not appear to match the target platform closely enough."
        else:
            recommendation["warning"] = "Proceed only after verifying the donor is the active BIOS match and not a recovery or backup image."
        return recommendation

    def brand_recommendation(self, original: Dict[str, Any]) -> Dict[str, Any]:
        board = str(original.get("dmi", {}).get("board_number", "")).upper()
        hp_bid = str(original.get("dmi", {}).get("hp_bid", "")).upper()
        combined = f"{board} {hp_bid}".strip()

        if "HP" in combined or "6050A" in combined:
            return {
                "brand": "HP",
                "warning": "HP systems are identity-sensitive (Caps-Lock blink). Do not replace the full image with a random donor. Keep Original BID and DMI.",
            }

        if "NM-" in combined or "LENOVO" in combined:
            return {
                "brand": "Lenovo",
                "warning": "Lenovo password and identity issues are model-specific. Always transfer Original NVRAM blocks to Donor to preserve MTM and UUID.",
            }

        if "DELL" in combined or "LA-" in combined:
             return {
                "brand": "Dell",
                "warning": "Dell uses EVSA stores. For passwords with E7A8/8FC8 suffixes, master passwords fail. You MUST rebuild (Frankenstein) using Clean ME and Donor BIOS region.",
            }

        return {
            "brand": "Generic",
            "warning": "Preserve original board identity and use only an exact model-family match. Do not replace the whole image.",
        }

    def repair_source_priority(self, original: Dict[str, Any], donor: Dict[str, Any] = None, official_exe: bool = False, online_search_allowed: bool = False) -> Dict[str, Any]:
        brand_guidance = self.brand_recommendation(original)

        if donor is not None:
            compat = self.donor_compatibility(original, donor)
            if compat["score"] >= 70:
                return {
                    "preferred_source": "Exact donor match",
                    "priority": 1,
                    "warning": f"{brand_guidance['warning']} Use only as a region-matching source; keep original identity blocks.",
                    "risk": "Low to Medium",
                    "compatibility": compat,
                    "brand_guidance": brand_guidance,
                }

        return {
            "preferred_source": "No safe source available",
            "priority": -1,
            "warning": f"{brand_guidance['warning']} No compatible donor available.",
            "risk": "High",
            "compatibility": {"score": 0, "verdict": "Unsafe to proceed", "details": ["No verified repair source."]},
            "brand_guidance": brand_guidance,
        }

    def password_storage_assessment(self, file_size: int, ifd_ok: bool, has_me_region: bool, has_uefi: bool = False) -> Dict[str, Any]:
        primary_like = ifd_ok and has_me_region and has_uefi
        if primary_like:
            return {
                "location": "Main SPI / active BIOS chip",
                "confidence": "High",
                "reason": "A valid descriptor, ME region, and UEFI image strongly indicate the active BIOS image contains the live platform configuration and password storage area.",
            }
        if file_size <= 2 * 1024 * 1024:
            return {
                "location": "Secondary / recovery chip likely (Often EC/KBC chip)",
                "confidence": "Medium",
                "reason": "Small dumps are often secondary or EC images; some old Thinkpads store passwords here, but modern ones use Main SPI.",
            }

        return {
            "location": "Unknown / needs board-level confirmation",
            "confidence": "Low",
            "reason": "This dump does not provide enough evidence to safely assign password storage.",
        }

if __name__ == "__main__":
    print("[*] Safdar Firmware Toolkit - Repair Planner Ready.")