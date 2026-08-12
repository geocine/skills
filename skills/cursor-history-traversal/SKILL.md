---
name: cursor-history-traversal
description: Traverse Cursor chat history from local Cursor SQLite databases and filter sessions by project folder path. Use when asked to retrieve "all history" for a directory from Cursor, extract patch operations from chat messages, replay file operations in chronological order, export folder-scoped Cursor timeline JSON, or debug workspace/global Cursor chat storage.
---

# Cursor History Traversal

## Overview

Use the prepackaged Python script in `scripts/traverse_cursor_history.py` to scan Cursor workspace and global storage databases, merge messages by composer/session ID, and output folder-specific history.

## Required Environment

Any Python 3.8+ interpreter works; the script uses only the standard library. Plain `python` on PATH is enough — do NOT run `conda activate base` first (conda is often not initialized in PowerShell and the command fails):

```powershell
python scripts/traverse_cursor_history.py --folder "D:\Projects\my-app" --out "D:\Projects\my-app-history.json"
```

Only if `python` is missing from PATH, fall back to `py -3` or the Git Bash wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_traversal_via_git_bash.ps1 -Folder "D:\Projects\my-app" -Out "D:\Projects\my-app-history.json"
```

## What The Script Traverses

1. Cursor root by OS (`%APPDATA%\Cursor` on Windows).
2. Workspace DBs: `User\workspaceStorage\*\state.vscdb`.
3. Global DB: `User\globalStorage\state.vscdb` (or legacy `cursor.cursor/*.sqlite` fallback).
4. Chat-related keys/tables:
`ItemTable.history.entries`
`ItemTable.workbench.panel.aichat.view.aichat.chatdata`
`ItemTable.composer.composerData`
`cursorDiskKV` keys: `bubbleId:*`, `composerData:*`

## Project Root Resolution

Folder filtering depends on resolving each session's project root. The script resolves roots in this order:

1. `workspaceStorage\<id>\workspace.json` `folder` URI (authoritative; present for nearly all workspaces).
2. Common prefix of `history.entries` file paths (legacy fallback).
3. Inference from file/folder paths found in the session itself (attached code selections and path-like strings inside the raw `composerData` record). Sessions resolved this way carry `"rootPathInferred": true`.

Sessions whose root still cannot be determined are excluded by folder filtering. The console summary prints how many sessions have unknown roots; pass `--include-unknown` to include them in results when the folder filter must not silently drop sessions.

## Command Patterns

Folder history export:

```powershell
python scripts/traverse_cursor_history.py --folder "D:\Projects\my-app" --out ".\my-app-history.json"
```

Compact survey first (metadata only, no transcripts — start here, then re-run without `--brief` on a narrowed filter):

```powershell
python scripts/traverse_cursor_history.py --folder "D:\Projects\my-app" --brief --out ".\my-app-brief.json"
```

Search messages by text while filtering folder (a drive root like `D:\` matches everything on that drive):

```powershell
python scripts/traverse_cursor_history.py --folder "D:\" --contains "refactor" --out ".\refactor-history.json"
```

Include sessions with unresolved project roots (avoids silently missing sessions):

```powershell
python scripts/traverse_cursor_history.py --folder "D:\Projects\my-app" --include-unknown --contains "my-app" --out ".\my-app-all.json"
```

Limit the number of returned sessions:

```powershell
python scripts/traverse_cursor_history.py --folder "D:\Projects\my-app" --limit 50
```

Use custom Cursor storage root:

```powershell
python scripts/traverse_cursor_history.py --folder "D:\Projects\my-app" --cursor-root "D:\Custom\CursorData"
```

## Output

The script prints:
1. Number of total sessions scanned.
2. Number of sessions matching the folder filter.
3. Number of replayable patch operations.
4. A per-session timeline line (`date | messages | session_id | project_root | db_path`).
5. JSON written to `--out` containing full matched sessions and metadata (or compact metadata with `--brief`).

## Patch Extraction

Cursor extraction in this workflow exposes chat messages (role/content) but not a structured tool-call name field.
Patch extraction therefore parses patch blocks directly from message text (`*** Begin Patch ... *** End Patch`) and outputs:
1. Session-level `patch_operations`
2. Top-level `patch_replay` in strict chronological order

The script also learns from richer Cursor bubble fields and exports:
1. `has_code_context` and `code_contexts` (from `selections` / `context.selections`)
2. `has_diffs` and `diff_entries` (from `suggestedDiffs`, `suggestedCodeBlocks`, `diffHistories`)
3. Assistant `model` values when available (`modelId`, `model`, `modelName`)

## Notes

1. Path matching is prefix-based and normalized (`D:\Projects\my-app` matches subfolders; `D:\` matches the whole drive).
2. Encoded Cursor paths like `/d%3A/Projects/my-app` are decoded automatically.
3. If no sessions match, the script still writes an empty JSON result with scan metadata.
4. If `Matched sessions: 0` looks wrong, check the `sessions_with_unknown_root` count in the summary and retry with `--include-unknown` plus a `--contains` filter — the session may exist but lack a resolvable root.
5. Full-session output JSON can be tens of MB. Use `--brief` for surveys, and query large JSON files with a small script instead of reading them whole.
6. Console output is forced to UTF-8, and the `--out` parent directory is created automatically.
