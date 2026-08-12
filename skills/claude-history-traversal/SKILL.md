---
name: claude-history-traversal
description: Traverse Claude Code session JSONL history from local `~/.claude/projects` storage and filter sessions by project folder path. Use when asked to retrieve "all history" for a directory from Claude Code, extract tool usage and file-edit (Write/Edit/MultiEdit) operations, replay file operations in chronological order, or export folder-scoped Claude timeline JSON.
---

# Claude Code History Traversal

## Overview

Use the prepackaged Python script in `scripts/traverse_claude_history.py` to scan Claude Code session JSONL files, merge messages and tool events by session, filter by folder path, and output timeline JSON compatible with the Cursor and Codex history traversal skills.

## Required Environment

Any Python 3.8+ interpreter works; the script uses only the standard library. Prefer plain `python` from PATH — no environment activation (such as `conda activate`) is needed or assumed:

```powershell
python scripts/traverse_claude_history.py --folder "D:\Projects\my-app" --out "D:\Projects\my-app-claude-history.json"
```

Only if `python` is missing from PATH, fall back to `py -3` or the Git Bash wrapper (uses conda when found, plain Git Bash `python` otherwise):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_traversal_via_git_bash.ps1 -Folder "D:\Projects\my-app" -Out "D:\Projects\my-app-claude-history.json"
```

## What The Script Traverses

1. Claude root: `~/.claude` (override with `--claude-root`); also checks `~/.config/claude`.
2. Session files: `projects/<encoded-project-path>/<session-uuid>.jsonl` (one file per session; folder names encode the project path, e.g. `D:\Projects\my-app` becomes `D--Projects-my-app`, but filtering uses the accurate per-record `cwd` field instead).
3. Record types:
   - `user` / `assistant` — messages; `content` is either a string or a list of blocks (`text`, `thinking`, `tool_use`, `tool_result`)
   - `ai-title` — session title
   - `system`, `attachment`, `file-history-snapshot`, etc. — skipped for the message timeline
4. Per-record metadata used: `cwd` (folder filtering), `timestamp` (ISO 8601), `sessionId`, `gitBranch`, `isSidechain` (subagent messages are kept and tagged `"sidechain": true`), `isMeta` (skipped).

## CLI

Same pattern as the sibling skills:
1. `--folder` (required) — path prefix filter matched against session `cwd`
2. `--out` — output JSON path
3. `--contains` — case-insensitive message text filter
4. `--limit` — max matched sessions, newest first
5. `--brief` — metadata-only output (no transcripts), for surveys
6. `--claude-root` (also accepts `--cursor-root` for compatibility)

## Patch Extraction

Claude Code does not use `apply_patch`; it edits files with the `Write`, `Edit`, `MultiEdit`, and `NotebookEdit` tools. The script converts those `tool_use` blocks into patch operations compatible with the other skills:
1. `Write` -> `Add File`
2. `Edit` / `MultiEdit` / `NotebookEdit` -> `Update File`
3. Top-level `patch_replay` is ordered by timestamp, then operation appearance order.

Each session also carries `tool_error_count` (number of `tool_result` blocks with `is_error: true`), useful for spotting sessions where tooling struggled.

## Command Patterns

Folder history export:

```powershell
python scripts/traverse_claude_history.py --folder "D:\Projects\my-app" --out ".\my-app-claude-history.json"
```

Search messages by text while filtering folder (drive root matches everything on that drive):

```powershell
python scripts/traverse_claude_history.py --folder "D:\" --contains "refactor" --out ".\claude-refactor-history.json"
```

Limit the number of returned sessions:

```powershell
python scripts/traverse_claude_history.py --folder "D:\Projects\my-app" --limit 50
```

Use custom Claude root (defaults to `%USERPROFILE%\.claude`):

```powershell
python scripts/traverse_claude_history.py --folder "D:\Projects\my-app" --claude-root "$env:USERPROFILE\.claude"
```

## Output

The script prints:
1. Discovered Claude roots.
2. Number of total sessions scanned.
3. Number of sessions matching the folder filter.
4. Number of replayable patch operations.
5. A per-session timeline line (`date | messages | session_id | project_root | jsonl_path`).
6. JSON written to `--out` with matched sessions plus top-level `patch_replay` (or compact metadata with `--brief`).

## Notes

1. Path matching is prefix-based and normalized (`D:\Projects\my-app` matches subfolders; `D:\` matches the whole drive).
2. Session JSONL files can be very large (80+ MB); the script streams line by line, so no memory concern, but full scans of all projects take a few seconds.
3. If no sessions match, the script still writes an empty JSON result with scan metadata.
4. Output JSON with all sessions can be huge. Prefer `--brief`, `--contains`, and `--limit` to narrow results, and query the JSON with a script instead of reading it whole.
5. Console output is forced to UTF-8, and the `--out` parent directory is created automatically.
