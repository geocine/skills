#!/usr/bin/env python3
"""
Traverse local Cursor chat history and filter by project folder.

This script mirrors the extraction strategy used by cursor-view:
- Reads workspaceStorage state.vscdb files
- Reads globalStorage state.vscdb (or legacy cursor/*.sqlite fallback)
- Merges chat messages by composer/session ID
- Filters resulting sessions by normalized project root path
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import platform
import sqlite3
import sys
import urllib.parse
from collections import defaultdict
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple


def _force_utf8_stdio() -> None:
    """Avoid UnicodeEncodeError on Windows cp1252 consoles."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


_force_utf8_stdio()


def cursor_root(override: Optional[pathlib.Path] = None) -> pathlib.Path:
    if override:
        return override
    home = pathlib.Path.home()
    system = platform.system()
    if system == "Windows":
        return home / "AppData" / "Roaming" / "Cursor"
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Cursor"
    if system == "Linux":
        return home / ".config" / "Cursor"
    raise RuntimeError(f"Unsupported OS: {system}")


def load_json(cur: sqlite3.Cursor, table: str, key: str) -> Any:
    try:
        cur.execute(f"SELECT value FROM {table} WHERE key=?", (key,))
    except sqlite3.Error:
        return None
    row = cur.fetchone()
    if not row or row[0] is None:
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return None


def table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    )
    return cur.fetchone() is not None


def workspaces(base: pathlib.Path) -> Iterator[Tuple[str, pathlib.Path]]:
    ws_root = base / "User" / "workspaceStorage"
    if not ws_root.exists():
        return
    for folder in ws_root.iterdir():
        db = folder / "state.vscdb"
        if db.exists():
            yield folder.name, db


def normalize_path(p: str) -> str:
    if not p:
        return ""
    s = urllib.parse.unquote(p.strip()).replace("\\", "/")

    if s.startswith("file:///"):
        s = s[len("file:///") :]
    elif s.startswith("file://"):
        s = s[len("file://") :]

    if len(s) >= 3 and s[0] == "/" and s[2] == ":":
        s = s[1:]

    if len(s) >= 6 and s[0] == "/" and s[2] == "%" and s[5] == "/":
        s = f"{s[1]}:/{s[6:]}"

    while "//" in s:
        s = s.replace("//", "/")

    return s.rstrip("/").lower()


def extract_code_context_from_selections(selections: Any) -> List[Dict[str, Any]]:
    contexts: List[Dict[str, Any]] = []
    if not isinstance(selections, list):
        return contexts

    for selection in selections:
        if not isinstance(selection, dict):
            continue
        uri = selection.get("uri") or {}
        file_path = uri.get("fsPath") if isinstance(uri, dict) else None
        if not isinstance(file_path, str) or not file_path.strip():
            continue
        contexts.append(
            {
                "file": file_path,
                "code": selection.get("text", selection.get("rawText", "")),
                "range": selection.get("range"),
            }
        )
    return contexts


def extract_bubble_meta(
    bubble: Dict[str, Any], role: str, default_model: Optional[str] = None
) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}

    if role == "user":
        contexts = extract_code_context_from_selections(
            bubble.get("selections")
        )
        if not contexts and isinstance(bubble.get("context"), dict):
            contexts = extract_code_context_from_selections(
                bubble["context"].get("selections")
            )
        if contexts:
            meta["code_context"] = contexts
        return meta

    model = (
        bubble.get("modelId")
        or bubble.get("model")
        or bubble.get("modelName")
        or default_model
    )
    if isinstance(model, str) and model.strip():
        meta["model"] = model.strip()

    if bubble.get("codeBlocks"):
        meta["code_blocks"] = bubble.get("codeBlocks")
    if bubble.get("suggestedDiffs"):
        meta["suggested_diffs"] = bubble.get("suggestedDiffs")
    if bubble.get("suggestedCodeBlocks"):
        meta["suggested_code_blocks"] = bubble.get("suggestedCodeBlocks")
    if bubble.get("diffHistories"):
        meta["diff_histories"] = bubble.get("diffHistories")
    if bubble.get("toolResults"):
        meta["tool_results"] = bubble.get("toolResults")
    return meta


def message_from_parts(role: str, text: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    msg: Dict[str, Any] = {"role": role, "content": text}
    for key in (
        "model",
        "code_context",
        "code_blocks",
        "suggested_diffs",
        "suggested_code_blocks",
        "diff_histories",
        "tool_results",
    ):
        value = meta.get(key)
        if value:
            msg[key] = value
    return msg


def iter_text_values(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        text = value.strip()
        if text:
            yield text
        return
    if isinstance(value, list):
        for item in value:
            yield from iter_text_values(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from iter_text_values(item)


def extract_patch_blocks(text: str) -> List[str]:
    if not text:
        return []
    begin = "*** Begin Patch"
    end = "*** End Patch"
    blocks: List[str] = []
    cursor = 0

    while True:
        start = text.find(begin, cursor)
        if start < 0:
            break
        stop = text.find(end, start)
        if stop < 0:
            blocks.append(text[start:])
            break
        blocks.append(text[start : stop + len(end)])
        cursor = stop + len(end)

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


def enrich_patch_operations(chat: Dict[str, Any]) -> Dict[str, Any]:
    patch_events: List[Dict[str, Any]] = []
    timestamp_ms = (chat.get("date") or 0) * 1000
    seen: set[str] = set()

    for index, message in enumerate(chat.get("messages") or []):
        content = message.get("content")
        if not isinstance(content, str):
            continue
        key = f"message:{index}:{content}"
        if key in seen:
            continue
        seen.add(key)
        operations = parse_patch_operations(content)
        if not operations:
            continue
        patch_events.append(
            {
                "timestamp": dt.datetime.fromtimestamp(chat.get("date")).isoformat(timespec="seconds")
                if isinstance(chat.get("date"), int)
                else None,
                "timestamp_ms": timestamp_ms,
                "source": "message_content",
                "message_index": index,
                "role": message.get("role"),
                "operations": operations,
            }
        )

    for diff_index, entry in enumerate(chat.get("diff_entries") or []):
        if not isinstance(entry, dict):
            continue
        source = entry.get("source", "diff_entries")
        for text in iter_text_values(entry.get("data")):
            key = f"diff:{diff_index}:{text}"
            if key in seen:
                continue
            seen.add(key)
            operations = parse_patch_operations(text)
            if not operations:
                continue
            patch_events.append(
                {
                    "timestamp": dt.datetime.fromtimestamp(chat.get("date")).isoformat(timespec="seconds")
                    if isinstance(chat.get("date"), int)
                    else None,
                    "timestamp_ms": timestamp_ms,
                    "source": f"diff_entries:{source}",
                    "diff_index": diff_index,
                    "operations": operations,
                }
            )

    if patch_events:
        chat["patch_operations"] = patch_events
    return chat


def build_patch_replay(chats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    replay: List[Dict[str, Any]] = []
    ordinal = 0

    for chat in chats:
        session_id = chat.get("session_id")
        workspace_id = chat.get("workspace_id")
        session_file = chat.get("db_path")
        for patch_event in chat.get("patch_operations", []) or []:
            event_ms = patch_event.get("timestamp_ms") or 0
            for op in patch_event.get("operations", []) or []:
                ordinal += 1
                replay.append(
                    {
                        "_ordinal": ordinal,
                        "timestamp_ms": event_ms,
                        "timestamp": patch_event.get("timestamp"),
                        "session_id": session_id,
                        "workspace_id": workspace_id,
                        "session_file": session_file,
                        "source": patch_event.get("source"),
                        "message_index": patch_event.get("message_index"),
                        "diff_index": patch_event.get("diff_index"),
                        "role": patch_event.get("role"),
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


def clean_path_string(p: str) -> Optional[str]:
    if not isinstance(p, str) or not p.strip():
        return None
    s = urllib.parse.unquote(p.strip()).replace("\\", "/")
    if s.startswith("file:///"):
        s = s[len("file:///") :]
    elif s.startswith("file://"):
        s = s[len("file://") :]
    if len(s) >= 3 and s[0] == "/" and s[2] == ":":
        s = s[1:]
    return s.rstrip("/") or None


def looks_like_local_path(s: str) -> bool:
    return len(s) >= 4 and s[1] == ":" and s[2] == "/"


def harvest_paths(obj: Any, depth: int = 0, found: Optional[List[str]] = None) -> List[str]:
    """Collect Windows/file-URI path strings from arbitrary nested JSON."""
    if found is None:
        found = []
    if depth > 6 or len(found) >= 50:
        return found
    if isinstance(obj, str):
        if len(obj) < 500:
            cleaned = clean_path_string(obj)
            if cleaned and looks_like_local_path(cleaned):
                found.append(cleaned)
    elif isinstance(obj, dict):
        for value in obj.values():
            harvest_paths(value, depth + 1, found)
    elif isinstance(obj, list):
        for value in obj[:50]:
            harvest_paths(value, depth + 1, found)
    return found


def infer_root_from_file_paths(paths: List[str]) -> Optional[str]:
    """Infer a project root from file/folder paths (last-resort fallback)."""
    cleaned = []
    for p in paths:
        c = clean_path_string(p) if isinstance(p, str) else None
        if c and looks_like_local_path(c):
            cleaned.append(c.lower() + "/")
    if not cleaned:
        return None
    common = os.path.commonprefix(cleaned)
    cut = common.rfind("/")
    if cut <= 0:
        return None
    root = common[:cut]
    # Require at least drive + one folder segment to avoid roots like "d:".
    if len([seg for seg in root.split("/") if seg]) < 2:
        return None
    return root


def extract_project_name(root_path: str) -> str:
    if not root_path:
        return "(unknown)"
    path = pathlib.PurePosixPath(root_path.replace("\\", "/"))
    name = path.name.strip()
    if not name:
        return "(unknown)"
    return name


def workspace_root_from_json(ws_folder: pathlib.Path) -> Optional[str]:
    """Read the authoritative project root from workspaceStorage/<id>/workspace.json."""
    ws_json = ws_folder / "workspace.json"
    if not ws_json.exists():
        return None
    try:
        data = json.loads(ws_json.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None
    for key in ("folder", "workspace", "configuration"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            decoded = urllib.parse.unquote(value.strip())
            if decoded.startswith("file:///"):
                decoded = decoded[len("file:///") :]
            elif decoded.startswith("file://"):
                decoded = decoded[len("file://") :]
            return decoded.replace("\\", "/")
    return None


def workspace_info(db: pathlib.Path) -> Tuple[Dict[str, str], Dict[str, Dict[str, Any]]]:
    proj = {"name": "(unknown)", "rootPath": "(unknown)"}
    comp_meta: Dict[str, Dict[str, Any]] = {}

    # Primary root source: workspace.json next to state.vscdb (present in
    # virtually all workspaceStorage folders and always accurate).
    ws_json_root = workspace_root_from_json(db.parent)
    if ws_json_root:
        proj = {
            "name": extract_project_name(ws_json_root),
            "rootPath": ws_json_root,
        }

    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
    except sqlite3.Error:
        return proj, comp_meta

    try:
        # Fallback root source: common prefix of recently opened files.
        if proj["rootPath"] == "(unknown)":
            entries = load_json(cur, "ItemTable", "history.entries") or []
            paths: List[str] = []
            for entry in entries:
                resource = entry.get("editor", {}).get("resource", "")
                if isinstance(resource, str) and resource.startswith("file:///"):
                    decoded = urllib.parse.unquote(resource[len("file:///") :]).replace("\\", "/")
                    paths.append(decoded)

            if paths:
                common_prefix = os.path.commonprefix(paths)
                cut = common_prefix.rfind("/")
                if cut > 0:
                    root = common_prefix[:cut]
                    proj = {
                        "name": extract_project_name(root),
                        "rootPath": "/" + root.lstrip("/"),
                    }

        composer_data = load_json(cur, "ItemTable", "composer.composerData") or {}
        for composer in composer_data.get("allComposers", []):
            cid = composer.get("composerId")
            if not cid:
                continue
            comp_meta[cid] = {
                "title": composer.get("name", f"Chat {str(cid)[:8]}"),
                "createdAt": composer.get("createdAt"),
                "lastUpdatedAt": composer.get("lastUpdatedAt"),
            }

        chat_data = load_json(cur, "ItemTable", "workbench.panel.aichat.view.aichat.chatdata") or {}
        for tab in chat_data.get("tabs", []):
            tab_id = tab.get("tabId")
            if tab_id and tab_id not in comp_meta:
                comp_meta[tab_id] = {
                    "title": f"Chat {str(tab_id)[:8]}",
                    "createdAt": None,
                    "lastUpdatedAt": None,
                }
    finally:
        con.close()

    return proj, comp_meta


def iter_chat_from_item_table(
    db: pathlib.Path,
) -> Iterable[Tuple[str, str, str, str, Dict[str, Any]]]:
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
    except sqlite3.Error:
        return

    db_path = str(db)
    try:
        chat_data = load_json(cur, "ItemTable", "workbench.panel.aichat.view.aichat.chatdata") or {}
        for tab in chat_data.get("tabs", []):
            tab_id = tab.get("tabId")
            if not tab_id:
                continue
            for bubble in tab.get("bubbles", []):
                text = bubble.get("text") or bubble.get("content") or ""
                if not isinstance(text, str) or not text.strip():
                    continue
                role = "user" if bubble.get("type") == "user" else "assistant"
                meta = extract_bubble_meta(bubble, role)
                yield str(tab_id), role, text.strip(), db_path, meta

        composer_data = load_json(cur, "ItemTable", "composer.composerData") or {}
        for composer in composer_data.get("allComposers", []):
            cid = composer.get("composerId")
            if not cid:
                continue
            model = None
            if isinstance(composer.get("modelConfig"), dict):
                model = composer["modelConfig"].get("modelName")

            conversation = composer.get("conversation")
            if isinstance(conversation, list) and conversation:
                for bubble in conversation:
                    if not isinstance(bubble, dict):
                        continue
                    bubble_type = bubble.get("type")
                    role = "user" if bubble_type == 1 else "assistant"
                    text = bubble.get("text") or bubble.get("rawText") or ""
                    if not isinstance(text, str) or not text.strip():
                        continue
                    meta = extract_bubble_meta(bubble, role, default_model=model)
                    yield str(cid), role, text.strip(), db_path, meta
                continue

            for msg in composer.get("messages", []):
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content")
                if not isinstance(content, str) or not content.strip():
                    continue
                role = str(msg.get("role", "assistant")).strip().lower()
                role = "user" if role == "user" else "assistant"
                meta = extract_bubble_meta(msg, role, default_model=model)
                yield str(cid), role, content.strip(), db_path, meta
    finally:
        con.close()


def iter_bubbles_from_disk_kv(
    db: pathlib.Path,
) -> Iterable[Tuple[str, str, str, str, Dict[str, Any]]]:
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
    except sqlite3.Error:
        return

    db_path = str(db)
    try:
        if not table_exists(cur, "cursorDiskKV"):
            return
        cur.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'bubbleId:%'")
        rows = cur.fetchall()
        for key, value in rows:
            if value is None:
                continue
            try:
                bubble = json.loads(value)
            except Exception:
                continue
            text = (bubble.get("text") or bubble.get("richText") or "").strip()
            if not text:
                continue
            parts = str(key).split(":")
            if len(parts) < 2:
                continue
            composer_id = parts[1]
            role = "user" if bubble.get("type") == 1 else "assistant"
            meta = extract_bubble_meta(bubble, role)
            yield composer_id, role, text, db_path, meta
    finally:
        con.close()


def iter_composer_data(db: pathlib.Path) -> Iterable[Tuple[str, Dict[str, Any], str]]:
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
    except sqlite3.Error:
        return

    db_path = str(db)
    try:
        if not table_exists(cur, "cursorDiskKV"):
            return
        cur.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'")
        for key, value in cur.fetchall():
            if value is None:
                continue
            try:
                data = json.loads(value)
            except Exception:
                continue
            parts = str(key).split(":")
            if len(parts) < 2:
                continue
            yield parts[1], data, db_path
    finally:
        con.close()


def global_storage_path(base: pathlib.Path) -> Optional[pathlib.Path]:
    global_db = base / "User" / "globalStorage" / "state.vscdb"
    if global_db.exists():
        return global_db

    for folder in (base / "User" / "globalStorage" / "cursor.cursor", base / "User" / "globalStorage" / "cursor"):
        if folder.exists():
            candidates = list(folder.glob("*.sqlite")) + list(folder.glob("*.db")) + list(folder.glob("*.sqlite3"))
            if candidates:
                return candidates[0]
    return None


def extract_chats(base: pathlib.Path) -> List[Dict[str, Any]]:
    ws_proj: Dict[str, Dict[str, Any]] = {}
    comp_meta: Dict[str, Dict[str, Any]] = {}
    comp2ws: Dict[str, str] = {}
    sessions: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"messages": []})

    for ws_id, db in workspaces(base):
        proj, meta = workspace_info(db)
        ws_proj[ws_id] = proj

        for cid, m in meta.items():
            comp_meta[cid] = m
            comp2ws[cid] = ws_id

        for cid, role, text, db_path, meta in iter_chat_from_item_table(db):
            sessions[cid]["messages"].append(message_from_parts(role, text, meta))
            sessions[cid].setdefault("db_path", db_path)
            if cid not in comp_meta:
                comp_meta[cid] = {"title": f"Chat {cid[:8]}", "createdAt": None, "lastUpdatedAt": None}
                comp2ws[cid] = ws_id

    gdb = global_storage_path(base)
    if gdb:
        for cid, role, text, db_path, meta in iter_bubbles_from_disk_kv(gdb):
            sessions[cid]["messages"].append(message_from_parts(role, text, meta))
            sessions[cid].setdefault("db_path", db_path)
            if cid not in comp_meta:
                comp_meta[cid] = {"title": f"Chat {cid[:8]}", "createdAt": None, "lastUpdatedAt": None}
                comp2ws[cid] = "(global)"

        for cid, data, db_path in iter_composer_data(gdb):
            sessions[cid].setdefault("db_path", db_path)
            context_paths = harvest_paths(data)
            if context_paths:
                sessions[cid].setdefault("context_paths", []).extend(context_paths)
            if cid not in comp_meta:
                created_at = data.get("createdAt")
                comp_meta[cid] = {
                    "title": f"Chat {cid[:8]}",
                    "createdAt": created_at,
                    "lastUpdatedAt": created_at,
                }
                comp2ws[cid] = "(global)"

            model = None
            if isinstance(data.get("modelConfig"), dict):
                model = data["modelConfig"].get("modelName")

            for msg in data.get("conversation", []):
                msg_type = msg.get("type")
                role = "user" if msg_type == 1 else "assistant"
                content = msg.get("text")
                if isinstance(content, str) and content.strip():
                    meta = extract_bubble_meta(msg, role, default_model=model)
                    sessions[cid]["messages"].append(message_from_parts(role, content.strip(), meta))

        try:
            con = sqlite3.connect(f"file:{gdb}?mode=ro", uri=True)
            cur = con.cursor()
            chat_data = load_json(cur, "ItemTable", "workbench.panel.aichat.view.aichat.chatdata") or {}
            for tab in chat_data.get("tabs", []):
                tab_id = tab.get("tabId")
                if not tab_id:
                    continue
                if tab_id not in comp_meta:
                    comp_meta[tab_id] = {
                        "title": f"Global Chat {str(tab_id)[:8]}",
                        "createdAt": None,
                        "lastUpdatedAt": None,
                    }
                    comp2ws[tab_id] = "(global)"
                for bubble in tab.get("bubbles", []):
                    text = bubble.get("text") or bubble.get("content") or ""
                    if not isinstance(text, str) or not text.strip():
                        continue
                    role = "user" if bubble.get("type") == "user" else "assistant"
                    meta = extract_bubble_meta(bubble, role)
                    sessions[tab_id]["messages"].append(
                        message_from_parts(role, text.strip(), meta)
                    )
        except sqlite3.Error:
            pass
        finally:
            if "con" in locals():
                con.close()

    out: List[Dict[str, Any]] = []
    for cid, data in sessions.items():
        if not data.get("messages"):
            continue
        ws_id = comp2ws.get(cid, "(unknown)")
        project = ws_proj.get(ws_id, {"name": "(unknown)", "rootPath": "(unknown)"})
        meta = comp_meta.get(cid, {"title": "(untitled)", "createdAt": None, "lastUpdatedAt": None})

        chat: Dict[str, Any] = {
            "project": project,
            "session": {"composerId": cid, **meta},
            "messages": data["messages"],
            "workspace_id": ws_id,
        }
        if "db_path" in data:
            chat["db_path"] = data["db_path"]
        if data.get("context_paths"):
            chat["context_paths"] = data["context_paths"]
        out.append(chat)

    out.sort(key=lambda item: item.get("session", {}).get("lastUpdatedAt") or 0, reverse=True)
    return out


def format_chat(chat: Dict[str, Any]) -> Dict[str, Any]:
    session = chat.get("session") or {}
    project = chat.get("project") or {}
    created_at = session.get("createdAt")
    updated_at = session.get("lastUpdatedAt")
    ts_ms = created_at if isinstance(created_at, (int, float)) else updated_at
    ts = int(ts_ms / 1000) if isinstance(ts_ms, (int, float)) and ts_ms > 0 else None

    root_path = project.get("rootPath", "")
    if not isinstance(root_path, str):
        root_path = ""

    messages = chat.get("messages", [])
    code_contexts: List[Dict[str, Any]] = []
    diff_entries: List[Dict[str, Any]] = []

    for index, msg in enumerate(messages):
        if not isinstance(msg, dict):
            continue
        code_context = msg.get("code_context")
        if isinstance(code_context, list) and code_context:
            code_contexts.extend(code_context)

        for key in ("suggested_diffs", "suggested_code_blocks", "diff_histories"):
            if msg.get(key):
                diff_entries.append(
                    {
                        "source": key,
                        "message_index": index,
                        "role": msg.get("role"),
                        "data": msg.get(key),
                    }
                )

    # Last-resort root inference for sessions not mapped to any workspace:
    # derive the root from code-context file paths and any path-like strings
    # harvested from the raw composerData record.
    if not root_path or root_path == "(unknown)":
        candidate_paths = [
            ctx.get("file") for ctx in code_contexts if isinstance(ctx, dict)
        ]
        candidate_paths.extend(chat.get("context_paths") or [])
        inferred = infer_root_from_file_paths(candidate_paths)
        if inferred:
            root_path = inferred
            project = {
                "name": extract_project_name(inferred),
                "rootPath": inferred,
                "rootPathInferred": True,
            }

    formatted = {
        "project": {
            "name": project.get("name", "(unknown)"),
            "rootPath": root_path,
            "normalizedRootPath": normalize_path(root_path),
            "rootPathInferred": bool(project.get("rootPathInferred")),
        },
        "messages": messages,
        "date": ts,
        "session_id": session.get("composerId"),
        "workspace_id": chat.get("workspace_id", "(unknown)"),
        "db_path": chat.get("db_path"),
        "session": session,
    }
    if code_contexts:
        formatted["has_code_context"] = True
        formatted["code_contexts"] = code_contexts
    else:
        formatted["has_code_context"] = False

    if diff_entries:
        formatted["has_diffs"] = True
        formatted["diff_entries"] = diff_entries
    else:
        formatted["has_diffs"] = False

    return formatted


def filter_by_folder(
    chats: List[Dict[str, Any]],
    folder: str,
    contains: Optional[str],
    include_unknown: bool = False,
) -> List[Dict[str, Any]]:
    target = normalize_path(folder)
    contains_lc = contains.lower() if contains else None
    matched = []

    for chat in chats:
        root = (chat.get("project") or {}).get("normalizedRootPath", "")
        unknown_root = not root or root == "(unknown)"
        if unknown_root:
            if not include_unknown:
                continue
        elif not root.startswith(target):
            continue
        if contains_lc:
            messages = chat.get("messages") or []
            if not any(contains_lc in str(msg.get("content", "")).lower() for msg in messages):
                continue
        matched.append(chat)

    return matched


def brief_chat(chat: Dict[str, Any]) -> Dict[str, Any]:
    """Compact session view: metadata + first user message, no full transcript."""
    slim = {
        k: v
        for k, v in chat.items()
        if k not in ("messages", "code_contexts", "diff_entries", "tool_results")
    }
    messages = chat.get("messages") or []
    slim["message_count"] = len(messages)
    first_user = next(
        (m.get("content") for m in messages if m.get("role") == "user"), None
    )
    if isinstance(first_user, str):
        slim["first_user_message"] = first_user[:500]
    return slim


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
    return f"{date_text} | {msg_count:4d} msgs | {session_id} | {root} | {db_path}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Traverse Cursor chat history and filter by folder path.")
    parser.add_argument("--folder", required=True, help="Target folder path prefix, e.g. D:\\Projects\\my-app")
    parser.add_argument(
        "--out",
        default="cursor-folder-history.json",
        help="Output JSON path (default: cursor-folder-history.json)",
    )
    parser.add_argument(
        "--cursor-root",
        default=None,
        help="Optional explicit Cursor root path override.",
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
        "--include-unknown",
        action="store_true",
        help="Also include sessions whose project root could not be determined.",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Write session metadata only (no message contents) to keep output small.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = cursor_root(pathlib.Path(args.cursor_root) if args.cursor_root else None)

    chats = extract_chats(root)
    formatted = [format_chat(chat) for chat in chats]
    unknown_roots = sum(
        1
        for chat in formatted
        if (chat.get("project") or {}).get("normalizedRootPath", "") in ("", "(unknown)")
    )
    matched = filter_by_folder(
        formatted, args.folder, args.contains, include_unknown=args.include_unknown
    )

    if args.limit is not None and args.limit >= 0:
        matched = matched[: args.limit]

    matched = [enrich_patch_operations(chat) for chat in matched]
    patch_replay = build_patch_replay(matched)

    payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "cursor_root": str(root),
        "folder_filter": args.folder,
        "normalized_folder_filter": normalize_path(args.folder),
        "contains_filter": args.contains,
        "total_scanned_sessions": len(formatted),
        "sessions_with_unknown_root": unknown_roots,
        "matched_sessions": len(matched),
        "patch_replay_count": len(patch_replay),
        "patch_replay": patch_replay,
        "sessions": [brief_chat(c) for c in matched] if args.brief else matched,
    }

    output_path = pathlib.Path(args.out)
    if output_path.parent and not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Cursor root: {root}")
    print(f"Scanned sessions: {len(formatted)} ({unknown_roots} with unknown project root)")
    print(f"Matched sessions: {len(matched)}")
    print(f"Patch replay operations: {len(patch_replay)}")
    print(f"Output JSON: {output_path.resolve()}")
    print("")
    for chat in matched:
        print(timeline_line(chat))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
