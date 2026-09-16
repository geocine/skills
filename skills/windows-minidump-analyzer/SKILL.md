---
name: windows-minidump-analyzer
description: Analyze Windows crash dump/minidump (.dmp) files to identify bugcheck codes, likely causes, and generate markdown reports using cdb.exe and/or header parsing. Use when asked to read or summarize Windows minidumps, run WinDbg/CDB analysis, or produce crash reports.
---

# Windows Minidump Analyzer

## Workflow
- Locate the dump file (explicit path or the newest `.dmp` in `C:\Windows\Minidump`).
- Prefer `scripts/analyze_minidump.py` to generate a markdown report next to the dump.
- Use `cdb.exe` when available; fall back to header parsing if `cdb.exe` is missing or fails.
- Keep reports concise: bugcheck, parameters, likely cause, stack (trimmed), OS build, uptime, and next steps.

## Usage
- Run: `python scripts/analyze_minidump.py "C:\Windows\Minidump\012526-6140-01.dmp"`
- Optional flags: `--out`, `--symbol-path`, `--cdb`, `--include-raw`, `--no-cdb`
- The script writes `*.md` next to the dump by default.

## Notes
- Default symbol path: `srv*C:\Symbols*https://msdl.microsoft.com/download/symbols`.
- `cdb.exe` ships with Windows SDK Debugging Tools and is typically under `C:\Program Files (x86)\Windows Kits\10\Debuggers`.
