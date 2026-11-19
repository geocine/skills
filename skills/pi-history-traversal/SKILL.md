---
name: pi-history-traversal
description: Traverse local Pi coding-agent session JSONL history by project folder. Use to retrieve past conversations, inspect branches and tool results, extract write/edit operations, or export a folder-scoped Pi timeline.
---

# Pi History Traversal

Use `scripts/traverse_pi_history.py` relative to this skill directory. It uses Python 3.8+ and the standard library; use `python` or `py -3` without activating an environment.

Start with a compact survey, then narrow the full export using text, session ID, or a limit:

```powershell
python scripts/traverse_pi_history.py --folder "D:\Projects\my-app" --brief --out ".\pi-history-brief.json"
python scripts/traverse_pi_history.py --folder "D:\Projects\my-app" --contains "refactor" --limit 10 --out ".\pi-history.json"
```

## Storage and discovery

Pi's coding agent saves `~/.pi/agent/sessions/--<encoded-cwd>--/<timestamp>_<session-id>.jsonl`. The header's `cwd` is authoritative; directory encoding replaces separators and colons with hyphens and cannot reliably be reversed. Folder matching includes the folder and its descendants, with path boundaries: `my-app` does not match `my-app-old`. Windows paths are case-insensitive; POSIX paths retain case.

Default discovery includes `~/.pi/agent`, `PI_CODING_AGENT_DIR`, `PI_CODING_AGENT_SESSION_DIR`, and `sessionDir` in discovered agent settings and the target folder's `.pi/settings.json`. These locations are combined for historical coverage. A custom CLI `--session-dir` used in a past Pi invocation cannot be discovered automatically; supply it explicitly.

```powershell
python scripts/traverse_pi_history.py --folder "D:\Projects\my-app" --pi-root "D:\Custom\pi-agent" --out ".\pi-history.json"
python scripts/traverse_pi_history.py --folder "D:\Projects\my-app" --session-dir "D:\ArchivedSessions" --out ".\pi-history.json"
```

`--pi-root` replaces default agent roots and accepts an agent directory, `.pi` directory, sessions directory, or single session file. Repeat `--session-dir` to add explicit locations. `--session-id` selects an exact header ID. Missing roots, malformed records, unknown working directories, and unsupported versions are reported in scan metadata. Use `--include-unknown` when you explicitly want sessions without a usable `cwd`; they remain marked unknown rather than assigned an inferred project.

This parser covers the coding agent's v1/v2/v3 session files. Ephemeral `--no-session` conversations have no files. JSON event-stream captures (`pi --mode json`) and experimental harness JSONL/SQLite backends have different schemas; do not report them as successfully traversed coding-agent history.

## Branches and messages

The default `--branch all` preserves every entry in append order, including abandoned branches, messages before compaction, model changes, summaries, labels, and extension state. Each message and tool event carries its entry ID, parent ID, timestamp, and source line. This is the recorded history, not the compacted prompt sent to the model.

```powershell
python scripts/traverse_pi_history.py --folder "D:\Projects\my-app" --branch latest --out ".\pi-latest-branch.json"
python scripts/traverse_pi_history.py --folder "D:\Projects\my-app" --session-id "session-id" --leaf-id "entry-id" --out ".\pi-selected-branch.json"
```

`latest` follows parents from the last persisted entry, matching Pi's load behavior. A navigation that moves only the live leaf without appending an entry is not recorded; the script cannot recover that runtime selection. `--leaf-id` selects a specific ancestor chain and excludes files without that entry. Compaction does not remove earlier entries from this history export. Legacy linear v1 records get deterministic synthetic IDs in memory; v2 `hookMessage` roles are exposed as `custom`.

Assistant `content` can contain text, thinking, and `toolCall` blocks. Results are messages with `role: toolResult` and `toolCallId`; matching follows the result's ancestry so sibling branches do not exchange results. Full exports retain provider/model/usage, system prompt sections, shell execution, result text/details, and unknown entry fields. Image payloads and provider signatures are omitted by default; pass `--include-images` if image base64 is needed. `--contains` searches selected entry text and tool arguments case-insensitively.

## File operations

Pi's built-in tools use `write {path, content}` and `edit {path, edits: [{oldText, newText}]}`. Older history can contain single `oldText`/`newText` arguments; the parser handles both recorded shapes. A write can create or overwrite, so its operation is `Write File`, not an inferred creation. All replacements in an edit apply against the original file; keep each call's edits grouped.

Session-level `patch_operations` contain attempted file calls with `succeeded`, `failed`, or `unknown` status. Top-level `patch_replay` includes only calls with an observed successful result, sorted by result timestamp, source file, and appearance order. Edit results retain `details.patch` and `details.diff` when present. Calls with no result are not evidence of a completed change; a failed call may still have produced partial side effects.

Forks and clones copy existing entries. The chronological export deduplicates identical copied calls and retains their session/file occurrences. Raw sessions remain separate, with `parentSession` lineage. Relative paths are resolved against the recorded header `cwd` and marked as such; forks into another project, cwd overrides, extensions, or remote tools can make the execution location uncertain.

Here, “replay” means an exported chronology. The script never applies operations or executes recorded commands. If the user separately asks to restore files, inspect the operations and target paths first. Shell and custom-tool mutations remain visible as tool events but are not inferred as structured file edits. JSONL alone does not establish a complete final filesystem snapshot or the completion order of simultaneous operations.

## Output

The JSON uses the sibling traversal skills' outer shape: `sessions`, `project.rootPath`, `messages`, `session_id`, `session`, `db_path`, and `patch_replay`, plus Pi entry/branch metadata and scan diagnostics. `--limit` keeps the newest matching sessions by recorded activity. `--brief` omits transcripts, entries, tool arguments, and replay bodies, retaining counts and a short first-user preview. Query large full exports selectively instead of reading them whole.

An empty result still writes JSON. When a result looks incomplete, inspect `scan`, `warnings`, discovered locations, unknown-root counts, branch selection, and filter/limit settings before concluding that no history exists. Input session files are opened read-only; Pi's own SessionManager is deliberately not invoked because opening legacy sessions can migrate or repair their files.
