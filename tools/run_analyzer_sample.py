import sys
import os
# Ensure workspace root is on sys.path so `core` package imports resolve
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
from core.analyzer import Analyzer

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_analyzer_sample.py <path-to-binary>")
        sys.exit(2)
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(3)
    try:
        a = Analyzer(path)
        print(a.generate_report())
    except Exception as e:
        print("Analyzer failed:", e)
        raise

if __name__ == '__main__':
    main()
