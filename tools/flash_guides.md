Safdar Firmware Toolkit - Flashing & Workshop Guide

Overview
- This document provides conservative, safety-first guidance for backing up and restoring SPI BIOS flashes, donor matching, and ME handling. Always verify compatibility and keep multiple verified backups before writing.

1) Backup checklist (mandatory before any write)
- Verify good power and a charged battery where applicable.
- Make at least two independent binary backups of the SPI chip.
- Compute and record CRC32/SHA256 checksums for backups.
- Extract key regions: INTEL FPT, ME/CSE, UEFI/EFI region, and DMI blocks.

2) Recommended tools
- flashrom (Linux preferred): read/verify with a supported programmer (CH341A, buspirate, Dediprog, SPI-based clip)
- CH341A + SOIC8 clip for cheap chip-off or in-system reads (use cautiously)
- Dedicated SPI programmers (eg. RT809H, XGecu) for reliable writes
- ME Analyzer and UEFITool for deep inspection
- me_cleaner (only for advanced privacy/ME modifications) — requires programmer and knowledge

3) Common `flashrom` commands (example)

- Read full chip to file:
```bash
flashrom -p ch341a_spi -r backup.bin
```

- Verify image:
```bash
flashrom -p ch341a_spi -v backup.bin
```

- Write image (only after human review):
```bash
flashrom -p ch341a_spi -w image_to_write.bin
```

Notes:
- Do not use in-system flashing on many laptops; EC/BIOS interactions can brick systems.
- Prefer chip-off programmer or power-isolation trick when uncertain.

4) Donor matching & splicing checklist
- Match board part number (silk-screen/`board_number`) and chipset family.
- Prefer donor with identical `FitMajor.FitMinor` ME range and similar flash layout.
- Preserve DMI/NVRAM blocks: `Serial`, `BID`, `Service Tag` — restore them from original after splicing.
- If ME region differs (major version mismatch), do not blindly copy ME region — consult repair plan.

5) ME cleaning & notes
- `me_cleaner` can reduce ME functionality; it is NOT a universal fix and may cause boot issues on some platforms.
- Use `me_cleaner` only on extracted ME firmware and re-flash via external programmer.
- Respect legal and warranty constraints when modifying ME/CSME.

6) Safety & rollback
- Keep original untouched backups and verify they boot in a test board where possible.
- Test post-flash behavior: power-on, boot to BIOS, check serial number & DMI preserved.
- If failure occurs, stop and seek community help (Badcaps, VinaFix, Win-Raid) before further writes.

References
- UEFITool: https://github.com/LongSoft/UEFITool
- flashrom: https://flashrom.org
- me_cleaner: https://github.com/corna/me_cleaner
- ME Analyzer (local copy available in `copyies/MEAnalyzer-master`)


Legal / Warranty
- Modifying firmware or ME may void warranties and could violate laws in some jurisdictions. Use these guides only in a professional repair context with owner consent.
