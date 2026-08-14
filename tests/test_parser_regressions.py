import struct

from core.dmi_engine import DMIEngine
from core.csme_engine import CSMEEngine


def test_rejects_false_positive_board_tokens():
    assert DMIEngine(b"MBSIGNED").extract_silk_screen_board_number() == "Not Found"
    assert DMIEngine(b"MBXFERERROR").extract_silk_screen_board_number() == "Not Found"


def test_filename_pattern_recognizes_hp_board():
    source = "830 g7 840 g7 6050A3136201 ok 32mb .BIN"
    assert DMIEngine(b"", source_name=source).extract_silk_screen_board_number() == "6050A3136201"


def test_csme_version_from_fpt_header():
    fpt_offset = 0x1000
    payload = bytearray(b"\x00" * (fpt_offset + 0x80))
    payload[fpt_offset:fpt_offset + 4] = b"$FPT"
    struct.pack_into("<HHHH", payload, fpt_offset + 0x18, 14, 0, 36, 1158)

    engine = CSMEEngine(bytes(payload))
    assert engine._extract_me_version(fpt_offset) == "14.0.36.1158"
