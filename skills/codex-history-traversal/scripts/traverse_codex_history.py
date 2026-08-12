#!/usr/bin/env python3
"""
Traverse local Codex rollout history and filter by project folder.

Interface intentionally mirrors cursor-history-traversal:
- --folder, --out, --contains, --limit, --cursor-root
Output includes matched sessions and top-level patch replay data.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import platform
import re
import sys
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple


def _force_utf8_stdio() -> None:
    """Avoid UnicodeEncodeError on Windows cp1252 consoles."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


_force_utf8_stdio()


PATCH_BEGIN = "*** Begin Patch"
PATCH_END = "*** End Patch"


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
        if n > 1_000_000_000_000:
            return n
        if n > 10_000_000_000:
            return n
        return n * 1000
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if raw.isdigit():
            return parse_timestamp_ms(int(raw))
        try:
            f = float(raw)
            return parse_timestamp_ms(f)
        except ValueError:
            pass
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


def extract_cwd_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    match = re.search(r"<cwd>(.*?)</cwd>", text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def collect_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return content["text"]
        if isinstance(content.get("message"), str):
            return content["message"]
        if "content" in content:
            return collect_text(content["content"])
        return ""
    if isinstance(content, list):
        parts = []
        for item in content:
            text = collect_text(item)
            if text:
                parts.append(text)
        return "\n".join(parts)
    return str(content)


def should_skip_auto_context(text: str) -> bool:
    t = text.strip()
    return (
        t.startswith("<environment_context>")
        and "</environment_context>" in t
        and "<cwd>" in t
    )


def extract_patch_blocks(text: str) -> List[str]:
    if not text:
        return []
    blocks: List[str] = []
    cursor = 0
    while True:
        start = text.find(PATCH_BEGIN, cursor)
        if start < 0:
            break
        end = text.find(PATCH_END, start)
        if end < 0:
            blocks.append(text[start:])
            break
        blocks.append(text[start : end + len(PATCH_END)])
        cursor = end + len(PATCH_END)

    if blocks:
        return blocks

    if (
        "*** Add File: " in text
        or "*** Update File: " in text
        or "*** Delete File: " in text
    ):
        return [text]
    return []


def parse_patch_operations(patch_text: str) -> List[Dict[str, Any]]:
    operations: List[Dict[str, Any]] = []
    for block_index, block in enumerate(extract_patch_blocks(patch_text)):
        op_counter = 0
        for line in block.splitlines():
            line = line.rstrip("\n")
            entry: Optional[Dict[str, Any]] = None
            if line.startswith("*** Add File: "):
                op_counter += 1
                entry = {
                    "operation": "Add File",
                    "path": line[len("*** Add File: ") :].strip(),
                    "move_to": None,
                    "block_index": block_index,
                    "op_index": op_counter,
                }
            elif line.startswith("*** Update File: "):
                op_counter += 1
                entry = {
                    "operation": "Update File",
                    "path": line[len("*** Update File: ") :].strip(),
                    "move_to": None,
                    "block_index": block_index,
                    "op_index": op_counter,
                }
            elif line.startswith("*** Delete File: "):
                op_counter += 1
                entry = {
                    "operation": "Delete File",
                    "path": line[len("*** Delete File: ") :].strip(),
                    "move_to": None,
                    "block_index": block_index,
                    "op_index": op_counter,
                }
            elif line.startswith("*** Move to: ") and operations:
                operations[-1]["move_to"] = line[len("*** Move to: ") :].strip()

            if entry:
                operations.append(entry)
    return operations


def parse_json_if_possible(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


def extract_patch_from_function_call(name: Any, arguments: Any) -> Optional[str]:
    tool_name = str(name or "").strip().lower()
    args = parse_json_if_possible(arguments)

    if tool_name == "apply_patch":
        if isinstance(args, dict):
            for key in ("patch", "input", "text"):
                val = args.get(key)
                if isinstance(val, str) and val.strip():
                    return val
        if isinstance(args, str) and args.strip():
            return args
        return None

    if tool_name in {"shell", "shell_command", "bash", "powershell"}:
        command = None
        if isinstance(args, dict):
            command = args.get("command")
        elif isinstance(args, list):
            command = args
        elif isinstance(args, str):
            command = args

        if isinstance(command, list):
            if command and str(command[0]).strip().lower() == "apply_patch":
                if len(command) > 1 and isinstance(command[1], str):
                    return command[1]
            for part in command:
                if isinstance(part, str) and PATCH_BEGIN in part:
                    idx = part.find(PATCH_BEGIN)
                    return part[idx:]

        if isinstance(command, str):
            if PATCH_BEGIN in command:
                idx = command.find(PATCH_BEGIN)
                return command[idx:]
    return None


def find_codex_installations(override: Optional[pathlib.Path]) -> List[pathlib.Path]:
    if override:
        root = override.expanduser()
        if root.exists():
            return [root.resolve()]
        return []

    home = pathlib.Path.home()
    system = platform.system()
    discovered: List[pathlib.Path] = []

    patterns = [".codex", ".codex-local", "codex", "codex-local"]

    base_dirs: List[pathlib.Path] = [home]
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        localappdata = os.environ.get("LOCALAPPDATA")
        if appdata:
            base_dirs.append(pathlib.Path(appdata))
        if localappdata:
            base_dirs.append(pathlib.Path(localappdata))
        base_dirs.extend([home / "AppData" / "Roaming", home / "AppData" / "Local"])
    elif system == "Darwin":
        base_dirs.extend([home / "Library" / "Application Support", home / ".config"])
    else:
        base_dirs.extend([home / ".config", home / ".local" / "share"])

    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        base_dirs.append(pathlib.Path(codex_home))

    for base in base_dirs:
        if not base.exists():
            continue
        for pattern in patterns:
            candidate = base / pattern
            if candidate.exists():
                discovered.append(candidate.resolve())

    # Always prefer ~/.codex when present.
    preferred = home / ".codex"
    if preferred.exists():
        discovered.append(preferred.resolve())

    deduped: Dict[str, pathlib.Path] = {}
    for path in discovered:
        deduped[str(path).lower()] = path
    return sorted(deduped.values(), key=lambda p: str(p).lower())


def find_session_files(installation: pathlib.Path) -> List[pathlib.Path]:
    files: Dict[str, pathlib.Path] = {}

    sessions_dir = installation / "sessions"
    if sessions_dir.exists():
        for file in sessions_dir.rglob("rollout-*.jsonl"):
            files[str(file).lower()] = file

    projects_dir = installation / "projects"
    if projects_dir.exists():
        for file in projects_dir.rglob("*.jsonl"):
            files[str(file).lower()] = file

    if not files:
        for file in installation.rglob("rollout-*.jsonl"):
            files[str(file).lower()] = file

    return sorted(files.values(), key=lambda p: str(p).lower())


def select_cwd(candidates: List[str]) -> str:
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "(unknown)"


def project_name_from_root(root_path: str) -> str:
    norm = root_path.replace("\\", "/").rstrip("/")
    if not norm or norm == "(unknown)":
        return "(unknown)"
    return pathlib.PurePosixPath(norm).name or "(unknown)"


def extract_codex_session(
    session_file: pathlib.Path, installation: pathlib.Path
) -> Optional[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    message_dedupe = set()
    tool_results: List[Dict[str, Any]] = []
    patch_events: List[Dict[str, Any]] = []
    cwd_candidates: List[str] = []

    session_id = session_file.stem
    session_created_ms: Optional[int] = None
    first_seen_ms: Optional[int] = None
    last_seen_ms: Optional[int] = None

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

                ts_raw = obj.get("timestamp") or obj.get("ts")
                ts_ms = parse_timestamp_ms(ts_raw)
                if ts_ms is not None:
                    if first_seen_ms is None or ts_ms < first_seen_ms:
                        first_seen_ms = ts_ms
                    if last_seen_ms is None or ts_ms > last_seen_ms:
                        last_seen_ms = ts_ms

                # Legacy line with root metadata.
                if "type" not in obj and "id" in obj:
                    sid = obj.get("id")
                    if isinstance(sid, str) and sid.strip():
                        session_id = sid.strip()
                    created = parse_timestamp_ms(obj.get("timestamp"))
                    if created is not None:
                        session_created_ms = created

                record_type = obj.get("type")
                payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}

                if record_type == "session_meta":
                    sid = payload.get("id")
                    if isinstance(sid, str) and sid.strip():
                        session_id = sid.strip()
                    created = parse_timestamp_ms(payload.get("timestamp") or ts_raw)
                    if created is not None:
                        session_created_ms = created
                    cwd = payload.get("cwd")
                    if isinstance(cwd, str) and cwd.strip():
                        cwd_candidates.append(cwd.strip())
                    continue

                if record_type == "turn_context":
                    cwd = payload.get("cwd")
                    if isinstance(cwd, str) and cwd.strip():
                        cwd_candidates.append(cwd.strip())
                    continue

                def add_message(role: str, text: str) -> None:
                    text = (text or "").strip()
                    if not text:
                        return
                    if should_skip_auto_context(text):
                        return
                    if role not in {"user", "assistant"}:
                        return
                    key = (role, text, ts_raw or "")
                    if key in message_dedupe:
                        return
                    message_dedupe.add(key)
                    messages.append(
                        {
                            "role": role,
                            "content": text,
                            "timestamp": ts_raw,
                        }
                    )
                    maybe_cwd = extract_cwd_from_text(text)
                    if maybe_cwd:
                        cwd_candidates.append(maybe_cwd)

                if record_type == "message":
                    role = str(obj.get("role") or "").lower()
                    text = collect_text(obj.get("content"))
                    add_message(role, text)
                    continue

                if record_type == "event_msg":
                    event_kind = payload.get("type")
                    if event_kind == "user_message":
                        add_message("user", str(payload.get("message") or ""))
                    elif event_kind == "agent_message":
                        add_message("assistant", str(payload.get("message") or ""))
                    elif event_kind in {"tool_use", "tool_result", "diff"}:
                        tool_results.append(
                            {
                                "type": event_kind,
                                "tool": payload.get("tool"),
                                "input": payload.get("input"),
                                "output": payload.get("output"),
                                "timestamp": ts_raw,
                                "line_number": line_number,
                            }
                        )
                        patch_text = None
                        if (
                            event_kind == "tool_use"
                            and str(payload.get("tool") or "").strip().lower() == "apply_patch"
                        ):
                            if isinstance(payload.get("input"), str):
                                patch_text = payload.get("input")
                            elif isinstance(payload.get("input"), dict):
                                patch_text = payload.get("input", {}).get("patch")
                        if isinstance(patch_text, str):
                            ops = parse_patch_operations(patch_text)
                            if ops:
                                patch_events.append(
                                    {
                                        "timestamp": ts_raw,
                                        "timestamp_ms": ts_ms,
                                        "source": "event_msg.tool_use",
                                        "call_id": None,
                                        "tool": "apply_patch",
                                        "line_number": line_number,
                                        "operations": ops,
                                    }
                                )
                    continue

                if record_type == "response_item":
                    payload_type = payload.get("type")
                    if payload_type == "message":
                        role = str(payload.get("role") or "").lower()
                        text = collect_text(payload.get("content"))
                        add_message(role, text)
                        continue

                    if payload_type in {"function_call", "function_call_output", "custom_tool_call"}:
                        tool_record = {
                            "type": payload_type,
                            "tool": payload.get("name"),
                            "timestamp": ts_raw,
                            "call_id": payload.get("call_id"),
                            "line_number": line_number,
                        }
                        if payload_type == "function_call":
                            tool_record["input"] = parse_json_if_possible(payload.get("arguments"))
                        elif payload_type == "custom_tool_call":
                            tool_record["input"] = payload.get("input")
                            tool_record["status"] = payload.get("status")
                        elif payload_type == "function_call_output":
                            tool_record["output"] = payload.get("output")
                        tool_results.append(tool_record)

                        patch_text = None
                        if (
                            payload_type == "custom_tool_call"
                            and str(payload.get("name") or "").strip().lower() == "apply_patch"
                            and isinstance(payload.get("input"), str)
                        ):
                            patch_text = payload.get("input")
                        elif payload_type == "function_call":
                            patch_text = extract_patch_from_function_call(
                                payload.get("name"), payload.get("arguments")
                            )

                        if isinstance(patch_text, str) and patch_text.strip():
                            ops = parse_patch_operations(patch_text)
                            if ops:
                                patch_events.append(
                                    {
                                        "timestamp": ts_raw,
                                        "timestamp_ms": ts_ms,
                                        "source": f"response_item.{payload_type}",
                                        "call_id": payload.get("call_id"),
                                        "tool": "apply_patch",
                                        "line_number": line_number,
                                        "operations": ops,
                                    }
                                )
                    continue
    except OSError:
        return None

    if not messages and not patch_events:
        return None

    root_path = select_cwd(cwd_candidates)
    created_ms = session_created_ms or first_seen_ms or last_seen_ms
    updated_ms = last_seen_ms or created_ms

    chat: Dict[str, Any] = {
        "project": {
            "name": project_name_from_root(root_path),
            "rootPath": root_path,
        },
        "session": {
            "composerId": session_id,
            "title": session_file.stem,
            "createdAt": created_ms,
            "lastUpdatedAt": updated_ms,
        },
        "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
        "workspace_id": installation.name,
        "db_path": str(session_file),
        "source": "codex",
        "installation": str(installation),
    }

    if tool_results:
        chat["tool_results"] = tool_results
    if patch_events:
        chat["patch_operations"] = patch_events

    return chat


def extract_chats(installations: List[pathlib.Path]) -> List[Dict[str, Any]]:
    chats: List[Dict[str, Any]] = []
    for installation in installations:
        for session_file in find_session_files(installation):
            session = extract_codex_session(session_file, installation)
            if session:
                chats.append(session)
    chats.sort(
        key=lambda s: s.get("session", {}).get("lastUpdatedAt") or 0,
        reverse=True,
    )
    return chats


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
    if "tool_results" in chat:
        formatted["tool_results"] = chat["tool_results"]
    if "patch_operations" in chat:
        formatted["patch_operations"] = chat["patch_operations"]
    if "source" in chat:
        formatted["source"] = chat["source"]
    if "installation" in chat:
        formatted["installation"] = chat["installation"]
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
                contains_lc in str(message.get("content", "")).lower()
                for message in messages
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
    if isinstance(ts, int):
        date_text = dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    else:
        date_text = "unknown"
    msg_count = len(chat.get("messages") or [])
    if not msg_count:
        msg_count = chat.get("message_count") or 0
    session_id = chat.get("session_id") or "(unknown)"
    root = (chat.get("project") or {}).get("rootPath") or "(unknown)"
    db_path = chat.get("db_path") or "(unknown)"
    return (
        f"{date_text} | {msg_count:4d} msgs | {session_id} | "
        f"{root} | {db_path}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Traverse Codex rollout history and filter by folder path."
    )
    parser.add_argument("--folder", required=True, help="Target folder path prefix, e.g. D:\\Projects\\my-app")
    parser.add_argument(
        "--out",
        default="cursor-folder-history.json",
        help="Output JSON path (default: cursor-folder-history.json)",
    )
    parser.add_argument(
        "--cursor-root",
        dest="root_override",
        default=None,
        help="Optional Codex root override (kept for CLI compatibility).",
    )
    parser.add_argument(
        "--codex-root",
        dest="root_override",
        default=None,
        help="Optional Codex root override.",
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
    installations = find_codex_installations(
        pathlib.Path(args.root_override) if args.root_override else None
    )

    chats = extract_chats(installations)
    formatted = [format_chat(chat) for chat in chats]
    matched = filter_by_folder(formatted, args.folder, args.contains)

    if args.limit is not None and args.limit >= 0:
        matched = matched[: args.limit]

    patch_replay = build_patch_replay(matched)

    payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "cursor_root": str(installations[0]) if len(installations) == 1 else "(multiple)",
        "codex_roots": [str(path) for path in installations],
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

    print(f"Codex roots: {', '.join(payload['codex_roots']) if payload['codex_roots'] else '(none found)'}")
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
