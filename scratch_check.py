from core.analyzer import Analyzer
import tempfile, os

fd, path = tempfile.mkstemp(suffix='.bin')
os.close(fd)
with open(path, 'wb') as f:
    f.write(b'\x5a\xa5\xf0\x0f' + b'0' * 4096)

a = Analyzer(path)
r = a.analyze_single()
print('VERSION=', r['csme']['version'])
print('ROLE=', r['chip_role']['role'])
print('REPORT_HEAD=')
for line in a.generate_report().splitlines()[:8]:
    print(line)

os.remove(path)
