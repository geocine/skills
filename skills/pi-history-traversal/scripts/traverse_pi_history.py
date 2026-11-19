#!/usr/bin/env python3
"""Read Pi coding-agent JSONL history and export folder-scoped timelines."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import ntpath
import os
import pathlib
import posixpath
import re
import sys
from urllib.parse import unquote, urlsplit


def normalize_path(value: str) -> str:
    path = value.strip().replace("\\", "/")
    if path.startswith("file://"):
        uri = urlsplit(path)
        path = ("//" + uri.netloc if uri.netloc else "") + unquote(uri.path)
    if re.match(r"^/[A-Za-z]:/", path):
        path = path[1:]
    windows = bool(re.match(r"^[A-Za-z]:", path) or path.startswith("//"))
    path = posixpath.normpath(path)
    return path.casefold() if windows else path


def folder_matches(cwd: str, folder: str) -> bool:
    if not cwd:
        return False
    root, target = normalize_path(cwd), normalize_path(folder)
    return root == target or root.startswith(target.rstrip("/") + "/")


def timestamp_ms(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # Pi message timestamps are Unix milliseconds, including small values.
        return int(value)
    if isinstance(value, str):
        try:
            parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return int(parsed.timestamp() * 1000)
        except ValueError:
            pass
    return None


def clean_payload(value, include_images: bool):
    if isinstance(value, list):
        return [clean_payload(item, include_images) for item in value]
    if isinstance(value, dict):
        image = value.get("type") == "image"
        result = {
            key: clean_payload(item, include_images)
            for key, item in value.items()
            if key not in ("thinkingSignature", "thoughtSignature", "textSignature")
            and not (image and key == "data" and not include_images)
        }
        if image and "data" in value and not include_images:
            result["data_omitted"] = True
        return result
    return value


def text_content(value) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""
    return "\n".join(
        block["text"] for block in value
        if isinstance(block, dict) and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    )


def discover_locations(args, warnings: list) -> list:
    agent_roots = []
    if args.pi_root:
        root = pathlib.Path(args.pi_root).expanduser().resolve()
        if (root / "agent").is_dir():
            root = root / "agent"
        agent_roots.append(root)
    else:
        agent_roots.append(pathlib.Path.home() / ".pi" / "agent")
        if os.environ.get("PI_CODING_AGENT_DIR"):
            agent_roots.append(pathlib.Path(os.environ["PI_CODING_AGENT_DIR"]).expanduser().resolve())

    locations = []
    settings_files = []
    for root in agent_roots:
        locations.append(root / "sessions" if (root / "sessions").is_dir() else root)
        settings_files.append(root / "settings.json")
    if not args.pi_root:
        settings_files.append(pathlib.Path(args.folder).expanduser() / ".pi" / "settings.json")
        if os.environ.get("PI_CODING_AGENT_SESSION_DIR"):
            locations.append(pathlib.Path(os.environ["PI_CODING_AGENT_SESSION_DIR"]).expanduser())
    for settings_file in settings_files:
        if not settings_file.is_file():
            continue
        try:
            settings = json.loads(settings_file.read_text(encoding="utf-8-sig"))
            custom = settings.get("sessionDir") if isinstance(settings, dict) else None
            if isinstance(custom, str) and custom:
                # Pi resolves relative sessionDir values against launch cwd.
                configured = pathlib.Path(custom).expanduser()
                locations.append(configured if configured.is_absolute() else pathlib.Path(args.folder) / configured)
        except (OSError, ValueError) as error:
            warnings.append({"file": str(settings_file), "reason": str(error)})
    locations.extend(pathlib.Path(value).expanduser() for value in args.session_dir)
    unique = {}
    for location in locations:
        resolved = location.resolve()
        unique[str(resolved)] = resolved
        if not resolved.exists():
            warnings.append({"file": str(resolved), "reason": "History location does not exist"})
    return list(unique.values())


def discover_files(locations: list, warnings: list) -> list:
    files = {}
    for location in locations:
        if not location.exists():
            continue
        if location.is_file():
            candidates = [location]
        else:
            # os.walk follows directory aliases used for archived history, with
            # physical-directory deduplication to avoid symlink/junction loops.
            candidates = []
            visited = set()
            for directory, subdirs, names in os.walk(
                location, followlinks=True,
                onerror=lambda error: warnings.append({"file": error.filename, "reason": str(error)}),
            ):
                physical = str(pathlib.Path(directory).resolve())
                if physical in visited:
                    subdirs[:] = []
                    continue
                visited.add(physical)
                # An agent root may also hold unrelated package installations.
                if pathlib.Path(directory).resolve() == location and (
                    location.name == "agent" or (location / "settings.json").is_file()
                ):
                    subdirs[:] = [name for name in subdirs if name == "sessions"]
                candidates.extend(pathlib.Path(directory) / name for name in names if name.endswith(".jsonl"))
        for candidate in candidates:
            resolved = candidate.resolve()
            files[str(resolved)] = resolved
    return sorted(files.values(), key=str)


def read_session(path: pathlib.Path, args, scan: dict, warnings: list):
    header = None
    entries = []
    previous_id = None
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError:
                scan["malformed_lines"] += 1
                warnings.append({"file": str(path), "line": line_number, "reason": "Malformed JSON line skipped"})
                continue
            if not isinstance(record, dict):
                scan["malformed_lines"] += 1
                warnings.append({"file": str(path), "line": line_number, "reason": "Non-object JSON record skipped"})
                continue
            if header is None:
                if record.get("type") != "session" or not isinstance(record.get("id"), str):
                    scan["invalid_files"] += 1
                    warnings.append({"file": str(path), "reason": "Not a coding-agent session header"})
                    return None
                header = record
                version = header.get("version", 1)
                if version not in (1, 2, 3):
                    scan["unsupported_files"] += 1
                    warnings.append({"file": str(path), "reason": "Unsupported session version", "version": version})
                    return None
                scan["valid_sessions"] += 1
                cwd = header.get("cwd")
                cwd = cwd if isinstance(cwd, str) else ""
                if not cwd:
                    scan["sessions_with_unknown_root"] += 1
                if not folder_matches(cwd, args.folder) and not (not cwd and args.include_unknown):
                    return None
                if args.session_id and header["id"] != args.session_id:
                    return None
                continue
            if record.get("type") == "session":
                warnings.append({"file": str(path), "line": line_number, "reason": "Extra session header skipped"})
                continue
            if record.get("type") in (
                "agent_start", "agent_end", "turn_start", "turn_end", "message_start", "message_update",
                "message_end", "tool_execution_start", "tool_execution_update", "tool_execution_end",
            ):
                scan["valid_sessions"] -= 1
                scan["invalid_files"] += 1
                warnings.append({"file": str(path), "reason": "JSON event-stream capture is not persisted session history"})
                return None
            record = clean_payload(record, args.include_images)
            record["line_number"] = line_number
            if header.get("version", 1) == 1:
                record["id"] = "legacy-line-{}".format(line_number)
                record["parentId"] = previous_id
                record["synthetic_id"] = True
            if not isinstance(record.get("id"), str):
                scan["malformed_lines"] += 1
                warnings.append({"file": str(path), "line": line_number, "reason": "Entry without string ID skipped"})
                continue
            previous_id = record["id"]
            message = record.get("message")
            if isinstance(message, dict) and message.get("role") == "hookMessage":
                message["role"] = "custom"
            entries.append(record)
    if header is None:
        scan["invalid_files"] += 1
        warnings.append({"file": str(path), "reason": "No session header"})
        return None
    return header, entries


def select_entries(entries: list, args, path: pathlib.Path, warnings: list):
    by_id = {entry["id"]: entry for entry in entries}
    if len(by_id) != len(entries):
        warnings.append({"file": str(path), "reason": "Duplicate entry IDs; ancestry uses last occurrence"})
    if args.leaf_id and args.leaf_id not in by_id:
        return None
    if args.branch == "all" and not args.leaf_id:
        return entries
    current = args.leaf_id or (entries[-1]["id"] if entries else None)
    branch = []
    visited = set()
    while current is not None:
        if current in visited or current not in by_id:
            warnings.append({"file": str(path), "reason": "Broken or cyclic selected parent chain", "entry_id": current})
            break
        visited.add(current)
        entry = by_id[current]
        branch.append(entry)
        current = entry.get("parentId")
    return list(reversed(branch))


def extract_tools(entries: list) -> tuple:
    by_id = {entry["id"]: entry for entry in entries}
    calls = []
    results = []
    by_call = {}
    for entry in entries:
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        stamp = entry.get("timestamp", message.get("timestamp"))
        base = {"entry_id": entry["id"], "parent_id": entry.get("parentId"),
                "timestamp": stamp, "timestamp_ms": timestamp_ms(stamp), "line_number": entry["line_number"]}
        if message.get("role") == "assistant" and isinstance(message.get("content"), list):
            for block_index, block in enumerate(message["content"]):
                if not isinstance(block, dict) or block.get("type") != "toolCall":
                    continue
                call = {**base, "type": "tool_use", "call_id": block.get("id"), "tool": block.get("name"),
                        "input": block.get("arguments"), "block_index": block_index, "status": "unknown"}
                calls.append(call)
                if isinstance(call["call_id"], str):
                    by_call.setdefault(call["call_id"], []).append(call)
        elif message.get("role") == "toolResult":
            result = {**base, "type": "tool_result", "call_id": message.get("toolCallId"),
                      "tool": message.get("toolName"), "is_error": message.get("isError"),
                      "content": text_content(message.get("content")), "details": message.get("details")}
            results.append(result)
    for result in results:
        candidates = by_call.get(result["call_id"], [])
        if not candidates:
            continue
        candidates_by_entry = {call["entry_id"]: call for call in candidates}
        current = result["parent_id"]
        visited = set()
        while current in by_id and current not in visited:
            visited.add(current)
            call = candidates_by_entry.get(current)
            if call and (not result["tool"] or result["tool"] == call["tool"]):
                call["result"] = result
                call["status"] = "failed" if result["is_error"] is True else (
                    "succeeded" if result["is_error"] is False else "unknown")
                result["call_entry_id"] = current
                break
            current = by_id[current].get("parentId")
    return calls, results


def file_operations(calls: list, cwd: str) -> list:
    events = []
    for call in calls:
        tool, inputs = call["tool"], call["input"]
        if tool not in ("write", "edit") or not isinstance(inputs, dict):
            continue
        path = inputs.get("path")
        if not isinstance(path, str) or not path:
            continue
        operation = {"operation": "Write File" if tool == "write" else "Update File", "path": path,
                     "move_to": None, "op_index": 1, "block_index": call["block_index"]}
        if cwd:
            path_module = ntpath if re.match(r"^[A-Za-z]:", cwd) or cwd.startswith("\\\\") else posixpath
            operation["resolved_path"] = path_module.normpath(path_module.join(cwd, path))
            operation["path_basis"] = "absolute_argument" if path_module.isabs(path) else "header_cwd"
        if tool == "write":
            operation["content"] = inputs.get("content")
        else:
            edits = inputs.get("edits", [])
            if isinstance(edits, str):
                try:
                    edits = json.loads(edits)
                except ValueError:
                    edits = []
            if isinstance(edits, dict):
                edits = [edits]
            edits = list(edits) if isinstance(edits, list) else []
            if isinstance(inputs.get("oldText"), str) and isinstance(inputs.get("newText"), str):
                edits.append({"oldText": inputs["oldText"], "newText": inputs["newText"]})
            operation["edits"] = edits
            result = call.get("result", {})
            details = result.get("details")
            if isinstance(details, dict):
                operation.update({key: details[key] for key in ("patch", "diff", "firstChangedLine") if key in details})
        identity = [call["entry_id"], call["call_id"], call["timestamp"], tool, inputs]
        fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        events.append({**{key: call[key] for key in ("entry_id", "call_id", "tool", "timestamp", "timestamp_ms", "line_number", "status")},
                       "source": "toolCall." + tool, "fingerprint": fingerprint,
                       "result_timestamp_ms": call.get("result", {}).get("timestamp_ms"), "operations": [operation]})
    return events


def format_session(path: pathlib.Path, header: dict, all_entries: list, entries: list, args) -> dict:
    cwd = header.get("cwd") if isinstance(header.get("cwd"), str) else ""
    calls, results = extract_tools(entries)
    operations = file_operations(calls, cwd)
    messages = []
    for entry in entries:
        message = entry.get("message")
        if entry.get("type") == "custom_message":
            message = {"role": "custom", "content": entry.get("content"), "customType": entry.get("customType")}
        elif entry.get("type") in ("compaction", "branch_summary"):
            message = {"role": "compactionSummary" if entry["type"] == "compaction" else "branchSummary",
                       "content": entry.get("summary", "")}
        if not isinstance(message, dict):
            continue
        content = text_content(message.get("content"))
        if message.get("role") == "bashExecution":
            content = str(message.get("command", "")) + "\n" + str(message.get("output", ""))
        messages.append({**message, "content": content, "content_blocks": message.get("content"),
                         "entry_id": entry["id"], "parent_id": entry.get("parentId"),
                         "entry_timestamp": entry.get("timestamp"), "line_number": entry["line_number"]})
    stamps = [timestamp_ms(header.get("timestamp"))]
    for entry in all_entries:
        stamps.append(timestamp_ms(entry.get("timestamp")))
        if isinstance(entry.get("message"), dict):
            stamps.append(timestamp_ms(entry["message"].get("timestamp")))
    valid_stamps = [stamp for stamp in stamps if stamp is not None]
    created = timestamp_ms(header.get("timestamp"))
    updated = max(valid_stamps) if valid_stamps else None
    title = None
    for entry in all_entries:
        if entry.get("type") == "session_info":
            title = entry.get("name") or None
    child_parents = {entry.get("parentId") for entry in all_entries}
    chat = {
        "project": {"name": posixpath.basename(cwd.replace("\\", "/").rstrip("/")) or "(unknown)",
                    "rootPath": cwd, "normalizedRootPath": normalize_path(cwd) if cwd else ""},
        "session": {"composerId": header["id"], "title": title or path.stem,
                    "createdAt": created, "lastUpdatedAt": updated},
        "session_id": header["id"], "date": created // 1000 if created is not None else None,
        "workspace_id": path.parent.name, "db_path": str(path), "source": "pi",
        "session_version": header.get("version", 1), "parent_session": header.get("parentSession", header.get("branchedFrom")),
        "branch_mode": "selected" if args.leaf_id else args.branch,
        "last_persisted_entry_id": all_entries[-1]["id"] if all_entries else None,
        "branch_leaf_ids": [entry["id"] for entry in all_entries if entry["id"] not in child_parents],
        "entry_count": len(entries), "total_entry_count": len(all_entries), "message_count": len(messages),
        "tool_call_count": len(calls), "tool_error_count": sum(result["is_error"] is True for result in results),
        "file_operation_count": len(operations),
        "successful_file_operation_count": sum(event["status"] == "succeeded" for event in operations),
        "first_user_message": next((message["content"][:500] for message in messages if message.get("role") == "user"), None),
    }
    if not args.brief:
        chat.update({"header": clean_payload(header, args.include_images), "entries": entries, "messages": messages,
                     "tool_calls": calls, "tool_results": results, "patch_operations": operations})
    return chat


def build_patch_replay(sessions: list) -> list:
    unique = {}
    for chat in sorted(sessions, key=lambda item: item["db_path"]):
        for event in chat.get("patch_operations", []):
            if event["status"] != "succeeded":
                continue
            occurrence = {"session_id": chat["session_id"], "session_file": chat["db_path"],
                          "line_number": event["line_number"], "root_path": chat["project"]["rootPath"]}
            if event["fingerprint"] in unique:
                unique[event["fingerprint"]]["occurrences"].append(occurrence)
                continue
            operation = event["operations"][0]
            unique[event["fingerprint"]] = {
                **event, **operation, "session_id": chat["session_id"], "session_file": chat["db_path"],
                "workspace_id": chat["workspace_id"], "occurrences": [occurrence],
                "ordering_timestamp_ms": event["result_timestamp_ms"] if event["result_timestamp_ms"] is not None else event["timestamp_ms"],
            }
    replay = sorted(unique.values(), key=lambda item: (
        item["ordering_timestamp_ms"] if item["ordering_timestamp_ms"] is not None else -1,
        item["session_file"], item["line_number"], item["block_index"],
    ))
    for index, event in enumerate(replay, 1):
        event["replay_index"] = index
    return replay


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", required=True, help="Recorded cwd folder and descendants")
    parser.add_argument("--out", default="pi-folder-history.json", help="Output JSON file")
    parser.add_argument("--pi-root", help="Agent root, .pi root, sessions directory, or JSONL file")
    parser.add_argument("--session-dir", action="append", default=[], help="Additional history location (repeatable)")
    parser.add_argument("--session-id", help="Exact session header ID")
    parser.add_argument("--contains", help="Case-insensitive search of selected entries and tool inputs")
    parser.add_argument("--limit", type=int, help="Newest matched sessions to retain")
    parser.add_argument("--brief", action="store_true", help="Counts and metadata without transcripts or operations")
    parser.add_argument("--branch", choices=("all", "latest"), default="all")
    parser.add_argument("--leaf-id", help="Select one parent chain ending at this entry ID")
    parser.add_argument("--include-unknown", action="store_true", help="Include sessions without usable cwd")
    parser.add_argument("--include-images", action="store_true", help="Retain image base64 in full exports")
    args = parser.parse_args(argv)
    if not args.folder.strip() or (args.limit is not None and args.limit < 0):
        parser.error("--folder must be nonempty and --limit must be nonnegative")
    if not re.match(r"^(?:[A-Za-z]:[/\\]|[/\\]|file://)", args.folder):
        args.folder = str(pathlib.Path(args.folder).expanduser().resolve())
    return args


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    warnings = []
    locations = discover_locations(args, warnings)
    files = discover_files(locations, warnings)
    output = pathlib.Path(args.out).expanduser().resolve()
    if output in files:
        print("Refusing to overwrite an input session file", file=sys.stderr)
        return 2
    scan = {"files_discovered": len(files), "valid_sessions": 0, "invalid_files": 0,
            "unsupported_files": 0, "unreadable_files": 0, "malformed_lines": 0,
            "sessions_with_unknown_root": 0}
    sessions = []
    for path in files:
        try:
            parsed = read_session(path, args, scan, warnings)
        except (OSError, UnicodeError) as error:
            scan["unreadable_files"] += 1
            warnings.append({"file": str(path), "reason": str(error)})
            continue
        if parsed is None:
            continue
        header, all_entries = parsed
        entries = select_entries(all_entries, args, path, warnings)
        if entries is None:
            continue
        if args.contains and args.contains.casefold() not in json.dumps(entries, ensure_ascii=False).casefold():
            continue
        sessions.append(format_session(path, header, all_entries, entries, args))
    sessions.sort(key=lambda chat: (-(chat["session"]["lastUpdatedAt"] or 0), chat["db_path"]))
    matched_before_limit = len(sessions)
    if args.limit is not None:
        sessions = sessions[:args.limit]
    replay = build_patch_replay(sessions)
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "pi_roots": [str(path) for path in locations], "folder_filter": args.folder,
        "normalized_folder_filter": normalize_path(args.folder), "contains_filter": args.contains,
        "session_id_filter": args.session_id, "branch_mode": args.branch, "leaf_id_filter": args.leaf_id,
        "brief": args.brief, "total_scanned_sessions": scan["valid_sessions"], "scan": scan,
        "matched_before_limit": matched_before_limit, "matched_sessions": len(sessions),
        "patch_replay_count": None if args.brief else len(replay), "patch_replay": replay,
        "sessions": sessions, "warnings": warnings,
    }
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        print("Cannot write output: {}".format(error), file=sys.stderr)
        return 2
    print("Scanned sessions: {} | matched: {} | warnings: {}".format(scan["valid_sessions"], len(sessions), len(warnings)))
    print("Successful unique file operations: {}".format("omitted (--brief)" if args.brief else len(replay)))
    print("Output JSON: {}".format(output))
    for chat in sessions:
        created = chat["session"]["createdAt"]
        date = dt.datetime.fromtimestamp(created / 1000, dt.timezone.utc).isoformat(timespec="seconds") if created is not None else "unknown"
        print("{} | {} msgs | {} | {} | {}".format(
            date, chat["message_count"], chat["session_id"],
            chat["project"]["rootPath"] or "(unknown)", chat["db_path"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
