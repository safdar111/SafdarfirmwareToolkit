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
                "reason": "Descriptor is present but the ME region is missing; this may be a backup, partial, or recovery payload.",
            }

        return {
            "role": "Unknown / secondary or partial image",
            "confidence": "Low",
            "reason": "No strong evidence for a primary active BIOS image.",
        }

    def classify_chip_set(self, chip_summaries: list[dict]) -> dict:
        """Classify multiple chip dumps in a workshop workflow."""
        ranked = []
        for idx, chip in enumerate(chip_summaries):
            role = self.classify_chip_role(
                file_size=chip.get("file_size", 0),
                ifd_ok=chip.get("ifd_ok", False),
                has_me_region=chip.get("has_me_region", False),
                has_uefi=chip.get("has_uefi", False),
            )
            ranked.append({
                "index": idx,
                "path": chip.get("path", f"chip_{idx}"),
                "size": chip.get("file_size", 0),
                "role": role["role"],
                "confidence": role["confidence"],
                "reason": role["reason"],
            })

        primary = [c for c in ranked if "Primary BIOS" in c["role"]]
        recovery = [c for c in ranked if "Recovery" in c["role"] or "Secondary" in c["role"] or "Unknown" in c["role"]]

        return {
            "primary_chip": primary[0] if primary else None,
            "backup_or_recovery_chips": recovery,
            "all_chips": ranked,
            "summary": "Primary chip should be treated as likely active BIOS; secondary/recovery images should not be modified unless explicitly confirmed as active.",
        }

    def donor_compatibility(self, original: Dict[str, Any], donor: Dict[str, Any]) -> Dict[str, Any]:
        original_version = str(original.get("csme", {}).get("version", "unknown")).lower()
        donor_version = str(donor.get("csme", {}).get("version", "unknown")).lower()
        original_role = original.get("chip_role", {}).get("role", "unknown")
        donor_role = donor.get("chip_role", {}).get("role", "unknown")

        score = 0
        details = []
        # Version proximity scoring (major, minor, hotfix, build)
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
            # major/minor proximity
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

        # Board number matching: exact strong match, prefix/vendor partial match weaker
        obn = original.get("dmi", {}).get("board_number")
        dbn = donor.get("dmi", {}).get("board_number")
        if obn and dbn:
            if obn == dbn:
                score += 25
                details.append("Board number exact match.")
            else:
                # vendor prefix match (e.g., DA0, LA-, 6050A)
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

        # Short numeric HP BID/revision match (e.g., 0802) - lower weight but useful
        obn_short = original.get("dmi", {}).get("hp_bid_short")
        dbn_short = donor.get("dmi", {}).get("hp_bid_short")
        if obn_short and dbn_short:
            if str(obn_short) == str(dbn_short):
                score += 8
                details.append("HP short BID/revision matches (secondary indicator).")

        # Consider CSME clean/dirty characteristics: if donor is clean and original dirty, favorable
        if donor.get("csme", {}).get("is_clean") and not original.get("csme", {}).get("is_clean"):
            score += 5
            details.append("Donor CSME is clean while original is dirty (useful for repair).")

        if score >= 70:
            verdict = "Compatible / likely safe donor"
        elif score >= 45:
            verdict = "Possibly compatible / manual review recommended"
        else:
            verdict = "Incompatible / not recommended for repair"

        if original_role and donor_role and "Primary BIOS" in original_role and "Recovery" in donor_role:
            verdict = "Incompatible / recovery donor not recommended for active BIOS repair"
            score = min(score, 35)
            details.append("Donor is classified as a recovery or secondary image, which is a high-risk mismatch for active BIOS repair.")

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
                "Original serial / service tag / BID blocks",
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

    def password_storage_assessment(self, file_size: int, ifd_ok: bool, has_me_region: bool, has_uefi: bool = False) -> Dict[str, Any]:
        """Determine whether BIOS admin password storage is more likely in the main SPI or a secondary/recovery chip."""
        primary_like = ifd_ok and has_me_region and has_uefi
        if primary_like:
            return {
                "location": "Main SPI / active BIOS chip",
                "confidence": "High",
                "reason": "A valid descriptor, ME region, and UEFI image strongly indicate the active BIOS image contains the live platform configuration and password storage area.",
            }

        if ifd_ok and has_me_region:
            return {
                "location": "Main SPI / likely active BIOS chip",
                "confidence": "Medium",
                "reason": "Descriptor and ME data are present, so password-related NVRAM state is more likely on the primary chip than on a recovery backup chip.",
            }

        if file_size <= 2 * 1024 * 1024:
            return {
                "location": "Secondary / recovery chip likely",
                "confidence": "Medium",
                "reason": "Small dumps are often secondary or recovery images; do not assume they hold the primary BIOS password store unless hardware validation confirms it.",
            }

        return {
            "location": "Unknown / needs board-level confirmation",
            "confidence": "Low",
            "reason": "This dump does not provide enough evidence to safely assign password storage to the main chip or a secondary chip.",
        }
