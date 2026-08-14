import pytest
from core.repair_planner import RepairPlanner


def make_sample(csme_version, board_number=None, role='Primary BIOS / likely active firmware', is_clean=False):
    return {
        'csme': {'version': csme_version, 'is_clean': is_clean},
        'dmi': {'board_number': board_number},
        'chip_role': {'role': role}
    }


def test_exact_version_match():
    rp = RepairPlanner()
    o = make_sample('14.0.36.1158', board_number='6050A3136201')
    d = make_sample('14.0.36.1158', board_number='6050A3136201')
    res = rp.donor_compatibility(o, d)
    assert res['score'] >= 80
    assert 'exact' in ' '.join(res['details']).lower()


def test_major_minor_match():
    rp = RepairPlanner()
    o = make_sample('14.0.36.1158', board_number='DA0X8BMB6G0')
    d = make_sample('14.0.35.1000', board_number='DA0X8BMB6G0')
    res = rp.donor_compatibility(o, d)
    assert res['score'] >= 40
    assert any('major' in s.lower() for s in res['details'])


def test_incompatible_board():
    rp = RepairPlanner()
    o = make_sample('14.0.36.1158', board_number='6050A2881001')
    d = make_sample('11.0.0.0', board_number='NM-XXXX')
    res = rp.donor_compatibility(o, d)
    assert res['score'] < 50
    assert 'differs' in ' '.join(res['details']).lower()
