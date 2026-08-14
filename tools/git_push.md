Safdar Firmware Toolkit - Safe Git Commit & Push Guide

1) Review changes locally
- Inspect diffs and run tests before committing.

```powershell
cd "C:\Users\Safdar Ali\Desktop\SafdarFirmwareToolkit"
# Show staged/unstaged changes
git status
# Review diffs
git diff
# Run quick tests (examples provided)
python tools\run_analyzer_sample.py "copyies\HP PROBOOK X360 11 G1 EE6050a2881001-mb-A01BIOS.BIN"
python tools\run_repair_planner_tests.py
```

2) Create a clear commit
- Use a single focused commit message describing the changes.

```powershell
git add core/dmi_engine.py core/csme_engine.py core/repair_planner.py tools/run_analyzer_sample.py tools/run_repair_planner_tests.py tools/flash_guides.md tools/git_push.md
git commit -m "Harden DMI & CSME parsing; improve donor compatibility scoring; add tools and guides"
```

3) Push to a feature branch

```powershell
# Create branch
git checkout -b feat/parser-hardening
# Push branch
git push -u origin feat/parser-hardening
```

4) Create a PR from the branch on GitHub
- Use the web UI to open a pull request titled: "Parser hardening: DMI/CSME + repair planner improvements" and include the test outputs in the PR description.

5) Safety notes
- Do not merge into `main` without CI and a peer review.
- Keep original backups for any firmware used in testing; do not publish real dumps in the repo.

