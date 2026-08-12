---
name: grok-history-traversal
description: Traverse Grok CLI session JSONL history from local `~/.grok/sessions` storage and filter sessions by project folder path. Use when asked to retrieve "all history" for a directory from Grok CLI, extract tool usage and file-edit (write/search_replace) operations, replay file operations in chronological order, or export folder-scoped Grok timeline JSON.
---

# Grok CLI History Traversal

## Overview

Use the prepackaged Python script in `scripts/traverse_grok_history.py` to scan Grok CLI session files, merge messages and tool events by session, filter by folder path, and output timeline JSON compatible with the sibling history traversal skills.

## Required Environment

Any Python 3.8+ interpreter works; the script uses only the standard library. Prefer plain `python` from PATH — no environment activation (such as `conda activate`) is needed or assumed:

```powershell
python scripts/traverse_grok_history.py --folder "D:\Projects\my-app" --out "D:\Projects\my-app-grok-history.json"
```

Only if `python` is missing from PATH, fall back to `py -3` or the Git Bash wrapper (uses conda when found, plain Git Bash `python` otherwise):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_traversal_via_git_bash.ps1 -Folder "D:\Projects\my-app" -Out "D:\Projects\my-app-grok-history.json"
```

## What The Script Traverses

1. Grok root: `%GROK_HOME%` if set, otherwise `~/.grok` (override with `--grok-root`).
2. Session directories: `sessions/<url-encoded-project-path>/<session-uuid>/` — e.g. `D:\Projects\my-app` becomes `D%3A%5CProjects%5Cmy-app`. Filtering uses the accurate `cwd` from each session's `summary.json`, with the decoded directory name as fallback.
3. Per-session files:
   - `chat_history.jsonl` — message records: `system` (skipped), `user`, `assistant` (text plus `tool_calls`), `tool_result`, `reasoning` (skipped), `backend_tool_call` (skipped)
   - `summary.json` — session id, `cwd`, title (`session_summary`), `created_at` / `last_active_at`, `current_model_id`, git branch/remotes
   - `events.jsonl` — runtime telemetry, not used for the timeline

## CLI

Same pattern as the sibling skills:
1. `--folder` (required) — path prefix filter matched against the session `cwd`
2. `--out` — output JSON path
3. `--contains` — case-insensitive message text filter
4. `--limit` — max matched sessions, newest first
5. `--brief` — metadata-only output (no transcripts), for surveys
6. `--grok-root` (also accepts `--cursor-root` for compatibility)

## Patch Extraction

Grok CLI does not use `apply_patch`; it edits files with the `write` and `search_replace` tools (plus `edit_file` variants). The script converts those tool calls into patch operations compatible with the other skills:
1. `write` / `write_file` -> `Add File`
2. `search_replace` / `edit_file` / `multi_edit` -> `Update File`
3. Top-level `patch_replay` is ordered by session start time, then appearance order — Grok chat records carry no per-record timestamps, so operations within a session are ordered by JSONL line order.

## Command Patterns

Folder history export:

```powershell
python scripts/traverse_grok_history.py --folder "D:\Projects\my-app" --out ".\my-app-grok-history.json"
```

Compact survey first (metadata only, no transcripts — start here, then re-run without `--brief` on a narrowed filter):

```powershell
python scripts/traverse_grok_history.py --folder "D:\Projects\my-app" --brief --out ".\my-app-grok-brief.json"
```

Search messages by text while filtering folder (a drive root like `D:\` matches everything on that drive):

```powershell
python scripts/traverse_grok_history.py --folder "D:\" --contains "refactor" --out ".\grok-refactor-history.json"
```

Limit the number of returned sessions:

```powershell
python scripts/traverse_grok_history.py --folder "D:\Projects\my-app" --limit 50
```

Use custom Grok root (defaults to `%GROK_HOME%` or `%USERPROFILE%\.grok`):

```powershell
python scripts/traverse_grok_history.py --folder "D:\Projects\my-app" --grok-root "$env:USERPROFILE\.grok"
```

## Output

The script prints:
1. Discovered Grok roots.
2. Number of total sessions scanned.
3. Number of sessions matching the folder filter.
4. Number of replayable patch operations.
5. A per-session timeline line (`date | messages | session_id | project_root | jsonl_path`).
6. JSON written to `--out` with matched sessions plus top-level `patch_replay` (or compact metadata with `--brief`).

Each session also carries `model` (from `current_model_id`) and `git_branch` when available.

## Notes

1. Path matching is prefix-based and normalized (`D:\Projects\my-app` matches subfolders; `D:\` matches the whole drive).
2. Grok also keeps `sessions/session_search.sqlite` and per-project `prompt_history.jsonl`; the script does not need them — `chat_history.jsonl` plus `summary.json` are the source of truth.
3. If no sessions match, the script still writes an empty JSON result with scan metadata.
4. Output JSON with all sessions can be huge. Prefer `--brief`, `--contains`, and `--limit` to narrow results, and query the JSON with a script instead of reading it whole.
5. Console output is forced to UTF-8, and the `--out` parent directory is created automatically.
