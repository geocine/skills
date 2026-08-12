#!/usr/bin/env python3
"""
Traverse local Claude Code session history and filter by project folder.

Interface intentionally mirrors cursor-history-traversal / codex-history-traversal:
- --folder, --out, --contains, --limit, --claude-root (also accepts --cursor-root)
Output includes matched sessions and top-level patch replay data.

Claude Code stores history as:
  ~/.claude/projects/<encoded-project-path>/<session-uuid>.jsonl
Each line is a JSON record. Relevant record types:
  user / assistant  -> message payloads (content string or block list)
  ai-title          -> session title
  system            -> metadata (cwd, gitBranch)
File-edit tool calls (Write / Edit / MultiEdit / NotebookEdit) are converted
to patch operations compatible with the other traversal skills.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional


def _force_utf8_stdio() -> None:
    """Avoid UnicodeEncodeError on Windows cp1252 consoles."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


_force_utf8_stdio()


def normalize_path(path_value: str) -> str:
    if not path_value:
        return ""
    p = path_value.strip().replace("\\", "/")
    if p.startswith("file:///"):
        p = p[len("file:///") :]
    elif p.startswith("file://"):
        p = p[len("file://") :]
    if len(p) >= 3 and p[0] == "/" and p[2] == ":":
        p = p[1:]
    while "//" in p:
        p = p.replace("//", "/")
    return p.rstrip("/").lower()


def parse_timestamp_ms(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        n = int(value)
        return n if n > 10_000_000_000 else n * 1000
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return int(parsed.timestamp() * 1000)
        except ValueError:
            return None
    return None


def ms_to_iso(ms: Optional[int]) -> Optional[str]:
    if ms is None:
        return None
    return dt.datetime.fromtimestamp(ms / 1000).isoformat(timespec="seconds")


def find_claude_roots(override: Optional[pathlib.Path]) -> List[pathlib.Path]:
    if override:
        root = override.expanduser()
        if root.exists():
            return [root.resolve()]
        return []
    home = pathlib.Path.home()
    candidates = [home / ".claude", home / ".config" / "claude"]
    found = [c.resolve() for c in candidates if (c / "projects").exists()]
    return found


def find_session_files(root: pathlib.Path) -> List[pathlib.Path]:
    projects = root / "projects"
    if not projects.exists():
        return []
    return sorted(projects.rglob("*.jsonl"), key=lambda p: str(p).lower())


# Tool names that modify files, mapped to patch-replay operation labels.
FILE_TOOL_OPERATIONS = {
    "write": "Add File",
    "edit": "Update File",
    "multiedit": "Update File",
    "notebookedit": "Update File",
}


def collect_text_blocks(content: Any) -> str:
    """Extract user-visible text from a message content payload."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
        return "\n".join(parts)
    return ""


def looks_like_meta(text: str) -> bool:
    t = text.strip()
    return (
        t.startswith("<command-name>")
        or t.startswith("<local-command-stdout>")
        or t.startswith("Caveat: The messages below")
        or t.startswith("<system-reminder>")
    )


def extract_claude_session(
    session_file: pathlib.Path, root: pathlib.Path
) -> Optional[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    tool_results: List[Dict[str, Any]] = []
    patch_events: List[Dict[str, Any]] = []
    cwd_candidates: List[str] = []
    title: Optional[str] = None
    git_branch: Optional[str] = None
    session_id = session_file.stem
    first_seen_ms: Optional[int] = None
    last_seen_ms: Optional[int] = None
    error_count = 0

    try:
        with session_file.open("r", encoding="utf-8", errors="ignore") as handle:
            for line_number, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                record_type = obj.get("type")
                ts_raw = obj.get("timestamp")
                ts_ms = parse_timestamp_ms(ts_raw)
                if ts_ms is not None:
                    if first_seen_ms is None or ts_ms < first_seen_ms:
                        first_seen_ms = ts_ms
                    if last_seen_ms is None or ts_ms > last_seen_ms:
                        last_seen_ms = ts_ms

                sid = obj.get("sessionId")
                if isinstance(sid, str) and sid.strip():
                    session_id = sid.strip()

                cwd = obj.get("cwd")
                if isinstance(cwd, str) and cwd.strip():
                    cwd_candidates.append(cwd.strip())

                if record_type == "ai-title":
                    t = obj.get("aiTitle")
                    if isinstance(t, str) and t.strip():
                        title = t.strip()
                    continue

                branch = obj.get("gitBranch")
                if isinstance(branch, str) and branch.strip():
                    git_branch = branch.strip()

                if record_type not in ("user", "assistant"):
                    continue
                if obj.get("isMeta"):
                    continue

                message = obj.get("message") or {}
                content = message.get("content")
                role = record_type
                sidechain = bool(obj.get("isSidechain"))

                text = collect_text_blocks(content)
                if text.strip() and not looks_like_meta(text):
                    entry: Dict[str, Any] = {"role": role, "content": text.strip()}
                    if sidechain:
                        entry["sidechain"] = True
                    messages.append(entry)

                if not isinstance(content, list):
                    continue
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    item_type = item.get("type")
                    if item_type == "tool_use":
                        name = str(item.get("name") or "")
                        tool_input = item.get("input")
                        tool_results.append(
                            {
                                "type": "tool_use",
                                "tool": name,
                                "input": tool_input,
                                "call_id": item.get("id"),
                                "timestamp": ts_raw,
                                "line_number": line_number,
                            }
                        )
                        op = FILE_TOOL_OPERATIONS.get(name.strip().lower())
                        if op and isinstance(tool_input, dict):
                            path = (
                                tool_input.get("file_path")
                                or tool_input.get("notebook_path")
                                or tool_input.get("path")
                            )
                            if isinstance(path, str) and path.strip():
                                patch_events.append(
                                    {
                                        "timestamp": ts_raw,
                                        "timestamp_ms": ts_ms,
                                        "source": f"tool_use.{name}",
                                        "call_id": item.get("id"),
                                        "tool": name,
                                        "line_number": line_number,
                                        "operations": [
                                            {
                                                "operation": op,
                                                "path": path.strip(),
                                                "move_to": None,
                                                "block_index": 0,
                                                "op_index": 1,
                                            }
                                        ],
                                    }
                                )
                    elif item_type == "tool_result":
                        is_error = bool(item.get("is_error"))
                        if is_error:
                            error_count += 1
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "call_id": item.get("tool_use_id"),
                                "is_error": is_error,
                                "timestamp": ts_raw,
                                "line_number": line_number,
                            }
                        )
    except OSError:
        return None

    if not messages and not patch_events:
        return None

    root_path = next((c for c in cwd_candidates if c), "(unknown)")
    created_ms = first_seen_ms or last_seen_ms
    updated_ms = last_seen_ms or created_ms

    norm = root_path.replace("\\", "/").rstrip("/")
    project_name = pathlib.PurePosixPath(norm).name if norm and norm != "(unknown)" else "(unknown)"

    chat: Dict[str, Any] = {
        "project": {"name": project_name or "(unknown)", "rootPath": root_path},
        "session": {
            "composerId": session_id,
            "title": title or session_file.stem,
            "createdAt": created_ms,
            "lastUpdatedAt": updated_ms,
        },
        "messages": messages,
        "workspace_id": session_file.parent.name,
        "db_path": str(session_file),
        "source": "claude",
        "installation": str(root),
        "git_branch": git_branch,
        "tool_error_count": error_count,
    }
    if tool_results:
        chat["tool_results"] = tool_results
    if patch_events:
        chat["patch_operations"] = patch_events
    return chat


def format_chat(chat: Dict[str, Any]) -> Dict[str, Any]:
    session = chat.get("session") or {}
    project = chat.get("project") or {}
    created_ms = session.get("createdAt")
    updated_ms = session.get("lastUpdatedAt")
    ts_ms = created_ms if isinstance(created_ms, (int, float)) else updated_ms
    ts = int(ts_ms / 1000) if isinstance(ts_ms, (int, float)) and ts_ms > 0 else None

    root_path = project.get("rootPath", "")
    if not isinstance(root_path, str):
        root_path = ""

    formatted: Dict[str, Any] = {
        "project": {
            "name": project.get("name", "(unknown)"),
            "rootPath": root_path,
            "normalizedRootPath": normalize_path(root_path),
        },
        "messages": chat.get("messages", []),
        "date": ts,
        "session_id": session.get("composerId"),
        "workspace_id": chat.get("workspace_id", "(unknown)"),
        "db_path": chat.get("db_path"),
        "session": session,
    }
    for key in ("tool_results", "patch_operations", "source", "installation", "git_branch", "tool_error_count"):
        if chat.get(key) is not None:
            formatted[key] = chat[key]
    return formatted


def filter_by_folder(
    chats: List[Dict[str, Any]], folder: str, contains: Optional[str]
) -> List[Dict[str, Any]]:
    target = normalize_path(folder)
    contains_lc = contains.lower() if contains else None
    matched: List[Dict[str, Any]] = []
    for chat in chats:
        root = (chat.get("project") or {}).get("normalizedRootPath", "")
        if not root.startswith(target):
            continue
        if contains_lc:
            messages = chat.get("messages") or []
            if not any(
                contains_lc in str(m.get("content", "")).lower() for m in messages
            ):
                continue
        matched.append(chat)
    return matched


def build_patch_replay(chats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    replay: List[Dict[str, Any]] = []
    ordinal = 0
    for chat in chats:
        session_id = chat.get("session_id")
        session_file = chat.get("db_path")
        workspace_id = chat.get("workspace_id")
        chat_fallback_ms = (chat.get("date") or 0) * 1000
        for patch_event in chat.get("patch_operations", []) or []:
            event_ms = patch_event.get("timestamp_ms")
            if not isinstance(event_ms, int):
                event_ms = chat_fallback_ms if isinstance(chat_fallback_ms, int) else 0
            for op in patch_event.get("operations", []) or []:
                ordinal += 1
                replay.append(
                    {
                        "_ordinal": ordinal,
                        "timestamp_ms": event_ms,
                        "timestamp": patch_event.get("timestamp") or ms_to_iso(event_ms),
                        "session_id": session_id,
                        "workspace_id": workspace_id,
                        "session_file": session_file,
                        "source": patch_event.get("source"),
                        "call_id": patch_event.get("call_id"),
                        "operation": op.get("operation"),
                        "path": op.get("path"),
                        "move_to": op.get("move_to"),
                        "block_index": op.get("block_index"),
                        "op_index": op.get("op_index"),
                    }
                )
    replay.sort(key=lambda x: (x.get("timestamp_ms") or 0, x.get("_ordinal") or 0))
    for index, item in enumerate(replay, 1):
        item["replay_index"] = index
        item.pop("_ordinal", None)
    return replay


def timeline_line(chat: Dict[str, Any]) -> str:
    ts = chat.get("date")
    date_text = (
        dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(ts, int)
        else "unknown"
    )
    msg_count = len(chat.get("messages") or [])
    if not msg_count:
        msg_count = chat.get("message_count") or 0
    session_id = chat.get("session_id") or "(unknown)"
    root = (chat.get("project") or {}).get("rootPath") or "(unknown)"
    db_path = chat.get("db_path") or "(unknown)"
    return f"{date_text} | {msg_count:4d} msgs | {session_id} | {root} | {db_path}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Traverse Claude Code session history and filter by folder path."
    )
    parser.add_argument("--folder", required=True, help="Target folder path prefix, e.g. D:\\Projects\\my-app")
    parser.add_argument(
        "--out",
        default="claude-folder-history.json",
        help="Output JSON path (default: claude-folder-history.json)",
    )
    parser.add_argument(
        "--claude-root",
        dest="root_override",
        default=None,
        help="Optional Claude root override (default: ~/.claude).",
    )
    parser.add_argument(
        "--cursor-root",
        dest="root_override",
        default=None,
        help="Alias of --claude-root (kept for CLI compatibility).",
    )
    parser.add_argument(
        "--contains",
        default=None,
        help="Optional case-insensitive message text filter.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max number of matched sessions to keep (newest first).",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Write session metadata only (no message contents) to keep output small.",
    )
    return parser.parse_args()


def brief_chat(chat: Dict[str, Any]) -> Dict[str, Any]:
    """Compact session view: metadata + first user message, no full transcript."""
    slim = {k: v for k, v in chat.items() if k not in ("messages", "tool_results")}
    messages = chat.get("messages") or []
    slim["message_count"] = len(messages)
    first_user = next(
        (m.get("content") for m in messages if m.get("role") == "user"), None
    )
    if isinstance(first_user, str):
        slim["first_user_message"] = first_user[:500]
    return slim


def main() -> int:
    args = parse_args()
    roots = find_claude_roots(
        pathlib.Path(args.root_override) if args.root_override else None
    )

    chats: List[Dict[str, Any]] = []
    for root in roots:
        for session_file in find_session_files(root):
            session = extract_claude_session(session_file, root)
            if session:
                chats.append(session)
    chats.sort(
        key=lambda s: s.get("session", {}).get("lastUpdatedAt") or 0, reverse=True
    )

    formatted = [format_chat(chat) for chat in chats]
    matched = filter_by_folder(formatted, args.folder, args.contains)
    if args.limit is not None and args.limit >= 0:
        matched = matched[: args.limit]

    patch_replay = build_patch_replay(matched)

    payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "claude_roots": [str(path) for path in roots],
        "folder_filter": args.folder,
        "normalized_folder_filter": normalize_path(args.folder),
        "contains_filter": args.contains,
        "total_scanned_sessions": len(formatted),
        "matched_sessions": len(matched),
        "patch_replay_count": len(patch_replay),
        "patch_replay": patch_replay,
        "sessions": [brief_chat(c) for c in matched] if args.brief else matched,
    }

    output_path = pathlib.Path(args.out)
    if output_path.parent and not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Claude roots: {', '.join(payload['claude_roots']) if payload['claude_roots'] else '(none found)'}")
    print(f"Scanned sessions: {len(formatted)}")
    print(f"Matched sessions: {len(matched)}")
    print(f"Patch replay operations: {len(patch_replay)}")
    print(f"Output JSON: {output_path.resolve()}")
    print("")
    for chat in matched:
        print(timeline_line(chat))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
