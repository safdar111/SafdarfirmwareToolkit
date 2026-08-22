# =====================================================
# Safdar Firmware Toolkit Pro
# Version   : 0.4.0 (Workshop Grade)
# File      : main.py
# Author    : Safdar Ali
# =====================================================

"""
Application Entry Point.
Initializes the PyQt6 event loop and displays the primary GUI window,
or runs Headless CLI analysis for batch processing.
"""

import sys
import os

# Ensure workspace root on sys.path so CLI analyzer works when invoked via main.py
workspace_root = os.path.abspath(os.path.dirname(__file__))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

def main():
    # CLI/help: print usage and exit when requested
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print("=====================================================")
        print(" Safdar Firmware Toolkit Pro - Command Line Interface")
        print("=====================================================\n")
        print("Usage: python main.py [--analyze <file>] [--no-gui]\n")
        print("Options:")
        print("  --analyze <file>   Run headless analysis on <file> and print report")
        print("  --no-gui           Do not attempt to start the GUI (useful for batch scripts)")
        print("  --save-ok          Save the binary and report if it passes health checks")
        print("  -h, --help         Show this help message and exit")
        return

    # If a path argument is provided, run headless analyzer and exit
    if len(sys.argv) > 1:
        arg_idx = 1
        if sys.argv[1] == "--analyze" and len(sys.argv) > 2:
            arg_idx = 2
        
        target = sys.argv[arg_idx]
        
        # Skip if the user just passed --no-gui without a file
        if target != "--no-gui" and os.path.exists(target):
            try:
                from core.analyzer import Analyzer
                a = Analyzer(target)
                
                # Assume analyzer has a run() or analyze_single() method that compiles the report
                results = a.analyze_single() 
                report = results.get("report_text", "No report generated.")
                print("\n" + report + "\n")
                
                # Optional: save OK binaries + report when requested
                if "--save-ok" in sys.argv:
                    saved = a.save_ok_report(report, output_dir="database/Repaired_Outputs")
                    if saved:
                        print(f"[+] Saved binary -> {saved['binary']}")
                        print(f"[+] Saved report -> {saved['report']}")
                    else:
                        print("[-] Not saved: file did not meet OK criteria (IFD+CSME required).")
                return
            except Exception as e:
                print("[-] Analyzer failed:", e)
                sys.exit(1)
        elif target != "--no-gui":
            print(f"[-] File not found: {target}")
            return

    # GUI mode: allow skipping GUI via --no-gui
    if "--no-gui" in sys.argv:
        print("[*] GUI disabled (--no-gui); execution finished.")
        return

    try:
        from PyQt6.QtWidgets import QApplication
        from gui.main_window import MainWindow
    except ImportError as e:
        print("[-] GUI unavailable — to run the GUI install PyQt6 (`pip install PyQt6`) or use --analyze. Error:", e)
        sys.exit(1)

    # Note: High-DPI attributes (AA_EnableHighDpiScaling) are removed 
    # because PyQt6 handles High-DPI scaling automatically by default.

    app = QApplication(sys.argv)
    app.setApplicationName("Safdar Firmware Toolkit Pro")
    app.setOrganizationName("Safdar Firmware Labs")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()