import sys
import os
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
from core.repair_planner import RepairPlanner


def make_sample(csme_version, board_number=None, role='Primary BIOS / likely active firmware', is_clean=False):
    return {
        'csme': {'version': csme_version, 'is_clean': is_clean},
        'dmi': {'board_number': board_number},
        'chip_role': {'role': role}
    }


def run():
    rp = RepairPlanner()

    o = make_sample('14.0.36.1158', board_number='6050A3136201')
    d = make_sample('14.0.36.1158', board_number='6050A3136201')
    res = rp.donor_compatibility(o, d)
    print('Exact match score:', res['score'], res['verdict'])

    o = make_sample('14.0.36.1158', board_number='DA0X8BMB6G0')
    d = make_sample('14.0.35.1000', board_number='DA0X8BMB6G0')
    res = rp.donor_compatibility(o, d)
    print('Major/minor match score:', res['score'], res['verdict'])

    o = make_sample('14.0.36.1158', board_number='6050A2881001')
    d = make_sample('11.0.0.0', board_number='NM-XXXX')
    res = rp.donor_compatibility(o, d)
    print('Incompatible board score:', res['score'], res['verdict'])

if __name__ == '__main__':
    run()
