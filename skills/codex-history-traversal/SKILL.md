---
name: codex-history-traversal
description: Traverse Codex rollout/session JSONL history from local Codex installations and filter sessions by project folder path. Use when asked to retrieve "all history" for a directory from Codex, extract tool usage and `apply_patch` operations, replay patch operations in chronological order, or export folder-scoped Codex timeline JSON.
---

# Codex History Traversal

## Overview

Use the prepackaged Python script in `scripts/traverse_codex_history.py` to scan Codex rollout JSONL files, merge messages and tool events by session, filter by folder path, and output timeline JSON compatible with the Cursor history traversal skill.

## Required Environment

Any Python 3.8+ interpreter works; the script uses only the standard library. Plain `python` on PATH is enough — do NOT run `conda activate base` first (conda is often not initialized in PowerShell and the command fails):

```powershell
python scripts/traverse_codex_history.py --folder "D:\Projects\my-app" --out "D:\Projects\my-app-history.json"
```

Only if `python` is missing from PATH, fall back to `py -3` or the Git Bash wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_traversal_via_git_bash.ps1 -Folder "D:\Projects\my-app" -Out "D:\Projects\my-app-history.json"
```

## Interface Compatibility

The script keeps the same CLI pattern as `cursor-history-traversal`:
1. `--folder` (required)
2. `--out`
3. `--contains`
4. `--limit`
5. `--brief` (metadata-only output, no transcripts)
6. `--cursor-root` (for compatibility; also accepts `--codex-root`)

## What The Script Traverses

1. Auto-discovered Codex installation roots (for example `.codex`, `codex`, `.codex-local`).
2. Session files under `sessions/**/rollout-*.jsonl`.
3. Optional project-style JSONL under `projects/**/*.jsonl`.
4. Event schemas including:
`session_meta`
`turn_context`
`message`
`response_item` (`message`, `function_call`, `function_call_output`, `custom_tool_call`)
`event_msg` (`user_message`, `agent_message`, `tool_use`, `tool_result`, `diff`)

## Patch Extraction

The script extracts patch operations from `apply_patch` usage and replays them in strict chronological order:
1. Select matched sessions/files after folder filtering.
2. Extract all `custom_tool_call` entries where `name == "apply_patch"`.
3. Also detect `apply_patch` embedded in `function_call` arguments (e.g. shell arrays).
4. Parse patch operations:
`Add File`
`Update File`
`Delete File`
5. Build top-level `patch_replay` ordered by timestamp and operation order.

## Command Patterns

Folder history export:

```powershell
python scripts/traverse_codex_history.py --folder "D:\Projects\my-app" --out ".\my-app-history.json"
```

Compact survey first (metadata only, no transcripts — start here, then re-run without `--brief` on a narrowed filter):

```powershell
python scripts/traverse_codex_history.py --folder "D:\Projects\my-app" --brief --out ".\my-app-brief.json"
```

Search messages by text while filtering folder (a drive root like `D:\` matches everything on that drive):

```powershell
python scripts/traverse_codex_history.py --folder "D:\" --contains "refactor" --out ".\refactor-history.json"
```

Limit the number of returned sessions:

```powershell
python scripts/traverse_codex_history.py --folder "D:\Projects\my-app" --limit 50
```

Use custom Codex root (auto-discovery finds `%USERPROFILE%\.codex` and similar locations by default):

```powershell
python scripts/traverse_codex_history.py --folder "D:\Projects\my-app" --codex-root "$env:USERPROFILE\.codex"
```

## Output

The script prints:
1. Number of total sessions scanned.
2. Number of sessions matching the folder filter.
3. Number of replayable patch operations.
4. A per-session timeline line (`date | messages | session_id | project_root | db_path`).
5. JSON written to `--out` with matched sessions plus top-level `patch_replay` (or compact metadata with `--brief`).

## Notes

1. Path matching is prefix-based and normalized (`D:\Projects\my-app` matches subfolders; `D:\` matches the whole drive).
2. If no sessions match, the script still writes an empty JSON result with scan metadata.
3. Patch replay order is deterministic: timestamp first, then operation appearance order.
4. Full-session output JSON can be tens of MB. Use `--brief` for surveys, and query large JSON files with a small script instead of reading them whole.
5. Console output is forced to UTF-8, and the `--out` parent directory is created automatically.
6. Full scans read every rollout JSONL under `sessions/` — with a large history this takes about a minute; allow for that in command timeouts.
