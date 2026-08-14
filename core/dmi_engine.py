import re


class DMIEngine:
    """
    Robust raw-firmware DMI metadata extractor for BIOS/SPI dumps.

    This engine intentionally prefers fast, vendor-aware regex scanning over
    a single brittle pattern set. It preserves the tool's public return contract
    while covering more common HP, Dell, Lenovo, Toshiba, and Asus patterns.
    """

    def __init__(self, binary_data: bytes, source_name: str = ""):
        self.data = binary_data or b""
        self.size = len(self.data)
        self.source_name = (source_name or "").strip()

    @staticmethod
    def _clean_text(raw: bytes) -> str:
        text = raw.decode("utf-8", errors="ignore")
        text = re.sub(r"[\x00-\x1f\x7f]+", " ", text)
        return text.strip()

    @staticmethod
    def _is_placeholder(value: str) -> bool:
        cleaned = (value or "").strip()
        if not cleaned:
            return True
        upper = cleaned.upper()
        if "BACKUP" in upper or "PHASE" in upper or "PLACEHOLDER" in upper or "TEST" in upper:
            return True
        # Common placeholder / default tokens seen in dumped firmware
        if any(tok in upper for tok in ("NOTPROVIDED", "UNKNOWN", "DEFAULT", "VOID", "N/A", "REMOVE", "REPLACE")):
            return True
        if upper.startswith("CNZZ") or "ZZZZ" in upper or "MMMM" in upper:
            return True
        if all(ch in "Z" for ch in upper if ch.isalpha()):
            return True
        if upper in {"MBSIGNED", "MBXFERERROR", "MBTRANSFER", "MBERROR", "MBTEST"}:
            return True
        # Reject very short or obviously synthetic sequences like "000000" or "XXXX"
        if re.fullmatch(r"[0-9]{2,}$", upper) and len(upper) < 6:
            return True
        return False

    def _first_match(self, patterns):
        for pattern in patterns:
            match = re.search(pattern, self.data, re.IGNORECASE)
            if match:
                # Prefer a capture group if the pattern defines one
                candidate_raw = match.group(1) if match.lastindex else match.group(0)
                candidate = self._clean_text(candidate_raw)
                if not self._is_placeholder(candidate):
                    return candidate
        return "Not Found"

    def extract_silk_screen_board_number(self) -> str:
        """
        Finds common laptop board silk-screen identifiers across OEMs.

        Examples:
          - HP/Inspiron/EliteBook: 6050A3136201-MB-A01 or 6050A3136201
          - Compal: LA-K091P
          - Quanta: DA0ZK3MB6E0
          - Lenovo: NM-xxxx
          - Asus: E1616A, M2N, etc. (partial support)
        """
        filename_patterns = [
            rb"6050A\d{6,10}",
            rb"6050A\d{6,8}-MB-[A-Z0-9]{2,3}",
            rb"6050A\d{6,8}-MB[A-Z0-9-]*",
            rb"LA-[A-Z0-9]{4,8}",
            rb"NM-[A-Z0-9]{4,10}",
            rb"DA0[A-Z0-9]{8,12}",
            rb"[A-Z0-9]{4,12}-MB-[A-Z0-9]{2,3}",
            rb"[A-Z0-9]{5,12}-[A-Z0-9]{2,4}P",
            rb"DDA30",
        ]

        if self.source_name:
            source_upper = self.source_name.upper()
            for pattern in filename_patterns:
                match = re.search(pattern, source_upper.encode("ascii", errors="ignore"), re.IGNORECASE)
                if match:
                    candidate = self._clean_text(match.group(0))
                    if candidate and not self._is_placeholder(candidate):
                        # Allow only likely OEM board patterns; reject generic MB* text fragments.
                        if re.search(r"(?:6050A|DA0|LA-|NM-|DDA30)", candidate.upper()):
                            return candidate.upper()
            # Explicit filename fallback for exact HP family style.
            hp_match = re.search(r"6050A\d{6,10}", source_upper)
            if hp_match:
                return hp_match.group(0).upper()

        patterns = [
            rb"6050A\d{6,10}",
            rb"6050A\d{6,8}-MB-[A-Z0-9]{2,3}",
            rb"6050A\d{6,8}-MB[A-Z0-9-]*",
            rb"LA-[A-Z0-9]{4,8}",
            rb"DA0[A-Z0-9]{8,12}",
            rb"NM-[A-Z0-9]{4,10}",
            rb"BA92-\d{5}[A-Z]",
            rb"DDA30",
        ]

        if self.size < 16:
            return "Not Found"

        label_patterns = [
            rb"(?:board|mainboard|motherboard|silk[- ]screen)[^A-Z0-9]{0,20}([A-Z0-9][A-Z0-9-]{5,30})",
            rb"(?:MB|M/B)[^A-Z0-9]{0,8}([A-Z0-9][A-Z0-9-]{5,30})",
        ]
        for pattern in label_patterns:
            for match in re.finditer(pattern, self.data, re.IGNORECASE):
                candidate = match.group(1) if match.lastindex else match.group(0)
                cleaned = self._clean_text(candidate)
                if not cleaned or self._is_placeholder(cleaned):
                    continue
                if len(cleaned) >= 6 and re.search(r"[A-Z]", cleaned):
                    if any(token in cleaned.upper() for token in ["MB", "LA-", "DA0", "NM-", "BID", "BOARD"]):
                        return cleaned.upper()

        return self._first_match(patterns)

    def extract_hp_bid(self) -> str:
        """Extracts HP Board ID (BID) from BIOS/SPI dumps."""
        patterns = [
            rb"BID[0-9A-Fa-f]{5,8}",
            rb"\$HP\$[^A-Z0-9]{0,8}[A-Z0-9]{6,12}",
            rb"(?:HP\s*BOARD\s*ID|BOARD\s*ID)\s*[:=\-]*\s*([A-Z0-9]{6,12})",
            rb"(?:BID|BOARD ID)\s*[:=\-]*\s*([A-Z0-9]{6,12})",
        ]

        for pattern in patterns:
            match = re.search(pattern, self.data, re.IGNORECASE)
            if match:
                value = match.group(1) if match.lastindex else match.group(0)
                cleaned = self._clean_text(value)
                if not cleaned or self._is_placeholder(cleaned):
                    continue
                # Normalize common BID prefixes
                up = cleaned.upper()
                if up.startswith("BID") and len(up) >= 6:
                    return up
                if re.search(r"[A-F0-9]", up) and len(up) >= 6:
                    return up

        hp_idx = self.data.find(b"$HP$")
        if hp_idx != -1 and hp_idx + 24 < self.size:
            chunk = self.data[hp_idx:hp_idx + 24]
            clean = re.sub(rb"[^A-Z0-9]", b"", chunk)
            if len(clean) >= 6:
                cand = self._clean_text(clean)
                if not self._is_placeholder(cand):
                    return cand

        return "Not Found"

    def extract_hp_bid_short(self) -> str:
        """Extract short numeric HP BID/revision codes often embedded near $HP$ or 'BID' markers (e.g., 0802)."""
        # Search for explicit BID: #### or three/four digit codes near HP markers
        # 1) patterns like BID[:=] ####
        match = re.search(rb"(?:BID\s*[:=\-]?\s*)([0-9]{3,4})", self.data, re.IGNORECASE)
        if match:
            val = self._clean_text(match.group(1))
            if val and not self._is_placeholder(val):
                return val

        # 2) look near $HP$ marker for a short numeric sequence
        hp_idx = self.data.find(b"$HP$")
        if hp_idx != -1:
            window = self.data[max(0, hp_idx - 32): min(self.size, hp_idx + 64)]
            m = re.search(rb"\b([0-9]{3,4})\b", window)
            if m:
                val = self._clean_text(m.group(1))
                if val and not self._is_placeholder(val):
                    return val

        # 3) fallback: look for patterns like 'REV 0802' or 'R0802' in the whole image
        for pattern in (rb"REV\s*([0-9]{3,4})", rb"R([0-9]{3,4})\b"):
            m = re.search(pattern, self.data, re.IGNORECASE)
            if m:
                val = self._clean_text(m.group(1))
                if val and not self._is_placeholder(val):
                    return val

        return "Not Found"

    def extract_dell_service_tag(self) -> str:
        """Extracts Dell service tag only when Dell-specific context is present."""
        patterns = [
            rb"(?:dell\s*service\s*tag|service\s*tag|dell\s*s\/n|service\s*number)\s*[:=\-]*\s*([A-Z0-9]{5,7})",
            rb"(?:dell)[^A-Z0-9]{0,20}([A-Z0-9]{5,7})",
            rb"([A-Z0-9]{5,7})\s*\|\s*DELL",
        ]

        seen = set()
        # Determine explicit Dell context: filename or nearby text
        has_dell_hint = False
        if self.source_name and "DELL" in self.source_name.upper():
            has_dell_hint = True
        for pattern in patterns:
            for match in re.finditer(pattern, self.data, re.IGNORECASE):
                tag = match.group(1) if match.lastindex else match.group(0)
                tag = self._clean_text(tag)
                if not tag:
                    continue
                if self._is_placeholder(tag):
                    continue
                if len(tag) in (5, 6, 7) and re.fullmatch(r"[A-Z0-9]+", tag):
                    # Only return if explicit Dell context is present or filename hints Dell
                    if not has_dell_hint:
                        # scan a small window around the match for the word 'dell'
                        start = max(0, match.start() - 64)
                        end = min(self.size, match.end() + 64)
                        window = self._clean_text(self.data[start:end])
                        if "DELL" not in window.upper():
                            continue
                    if tag not in seen and not re.match(r"^[0-9]+$", tag):
                        seen.add(tag)
                        return tag.upper()

        # Explicit Dell context is required; otherwise skip generic 5-7 char tokens.
        return "Not Found"

    def extract_serial_numbers(self) -> dict:
        """Extracts vendor serials and product key values from raw firmware bytes."""
        serials = {
            "serial_number": "Not Found",
            "model_name": "Not Found",
            "windows_dpk": "Not Found",
        }

        dpk_match = re.search(
            rb"([A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5})",
            self.data,
            re.IGNORECASE,
        )
        if dpk_match:
            serials["windows_dpk"] = self._clean_text(dpk_match.group(1)).upper()

        hp_serial_patterns = [
            rb"(?:5CG|2UA|2C[0-9A-Z]|4H[0-9A-Z]|CN[0-9A-Z]|CND[0-9A-Z]|CZ[0-9A-Z])[A-Z0-9]{7,12}",
            rb"(?:HP\s*SERIAL|SERIAL\s*NUMBER|S/N)\s*[:=\-]*\s*([A-Z0-9]{8,15})",
        ]
        for pattern in hp_serial_patterns:
            match = re.search(pattern, self.data, re.IGNORECASE)
            if match:
                value = match.group(1) if match.lastindex else match.group(0)
                cleaned = self._clean_text(value).upper()
                if self._is_placeholder(cleaned):
                    continue
                if len(cleaned) >= 8 and re.search(r"[A-Z]", cleaned):
                    serials["serial_number"] = cleaned
                    break

        other_patterns = [
            rb"(?:MODEL|SKU|PART\s*NO|P/N)\s*[:=\-]*\s*([A-Z0-9][A-Z0-9\-]{4,25})",
            rb"(?:SN|S/N|SERIAL)\s*[:=\-]*\s*([A-Z0-9]{6,18})",
        ]
        for pattern in other_patterns:
            match = re.search(pattern, self.data, re.IGNORECASE)
            if match:
                value = match.group(1) if match.lastindex else match.group(0)
                cleaned = self._clean_text(value).upper()
                if self._is_placeholder(cleaned):
                    continue
                if cleaned and cleaned != serials["serial_number"] and not re.fullmatch(r"[0-9A-F]{6,8}", cleaned):
                    serials["model_name"] = cleaned
                    break

        return serials

    def check_ifd_health(self) -> dict:
        """Validates the Intel Flash Descriptor signature and layout."""
        if self.size < 0x1000:
            return {"status": "FAIL", "reason": "File too small for descriptor validation"}

        sig = self.data[0x10:0x14]
        if sig == b"\x5a\xa5\xf0\x0f":
            return {"status": "OK", "reason": "Valid Intel Flash Descriptor (IFD)"}

        return {
            "status": "WARNING/NON-INTEL",
            "reason": "No Intel IFD signature found (AMD or non-descriptor layout)",
        }

    def check_intel_boot_guard(self) -> dict:
        """Checks for Intel Boot Guard manifest markers."""
        if b"$BKM" in self.data or b"$HAP" in self.data or b"$BPT" in self.data:
            return {
                "status": "ACTIVE / ENFORCED",
                "note": "Boot Guard is active; key manifest alignment must be maintained.",
            }
        return {"status": "DISABLED / NOT DETECTED", "note": "Standard boot flow."}

    def run_full_diagnostic(self) -> dict:
        """Returns the main DMI/structural summary used by the analyzer."""
        serials = self.extract_serial_numbers()
        return {
            "board_number": self.extract_silk_screen_board_number(),
            "hp_bid": self.extract_hp_bid(),
            "hp_bid_short": self.extract_hp_bid_short() ,
            "dell_tag": self.extract_dell_service_tag(),
            "serial_number": serials["serial_number"],
            "windows_dpk": serials["windows_dpk"],
            "ifd_health": self.check_ifd_health(),
            "boot_guard": self.check_intel_boot_guard(),
        }