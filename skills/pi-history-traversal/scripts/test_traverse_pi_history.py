"""Offline behavior checks; run with python scripts/test_traverse_pi_history.py."""

import contextlib
import io
import json
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import traverse_pi_history as traversal


class TraversalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.history = self.root / "history"
        self.history.mkdir()
        self.environment = patch.dict(os.environ, {
            "PI_CODING_AGENT_DIR": "", "PI_CODING_AGENT_SESSION_DIR": "",
        })
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def save(self, filename, entries, cwd="D:\\Projects\\app", version=3, sid=None, parent=None):
        header = {"type": "session", "version": version, "id": sid or filename,
                  "timestamp": "2026-01-01T00:00:00Z", "cwd": cwd}
        if parent:
            header["parentSession"] = parent
        target = self.history / filename
        target.write_text("\n".join(json.dumps(record) for record in [header, *entries]), encoding="utf-8")
        return target

    def message(self, entry_id, parent_id, role, content, timestamp=1, **fields):
        return {"type": "message", "id": entry_id, "parentId": parent_id,
                "timestamp": timestamp, "message": {"role": role, "content": content, "timestamp": timestamp, **fields}}

    def tool(self, entry_id, parent_id, call_id, name="write", inputs=None, timestamp=2):
        return self.message(entry_id, parent_id, "assistant", [
            {"type": "toolCall", "id": call_id, "name": name,
             "arguments": inputs or {"path": "src/main.ts", "content": "export const x = 1;"}},
        ], timestamp, provider="example", model="model")

    def result(self, entry_id, parent_id, call_id, name="write", error=False, timestamp=3, **fields):
        return self.message(entry_id, parent_id, "toolResult", [{"type": "text", "text": "result"}],
                            timestamp, toolCallId=call_id, toolName=name, isError=error, **fields)

    def export(self, *options, folder="D:\\Projects\\app"):
        output = self.root / "output.json"
        with contextlib.redirect_stdout(io.StringIO()):
            status = traversal.main(["--folder", folder, "--pi-root", str(self.history), "--out", str(output), *options])
        self.assertEqual(status, 0)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_path_boundaries_and_platform_case(self):
        self.assertTrue(traversal.folder_matches("d:/Projects/APP/sub", "D:\\Projects\\app"))
        self.assertFalse(traversal.folder_matches("D:/Projects/app-old", "D:/Projects/app"))
        self.assertTrue(traversal.folder_matches("D:/Projects/app", "D:/"))
        self.assertTrue(traversal.folder_matches("file:///D:/Projects/my%20app", "D:/Projects/my app"))
        self.assertTrue(traversal.folder_matches("\\\\server\\share\\app", "//SERVER/share"))
        self.assertFalse(traversal.folder_matches("/home/APP", "/home/app"))
        self.assertTrue(traversal.folder_matches("/home/app", "/"))

    def test_success_failure_unknown_and_grouped_edits(self):
        edits = [{"oldText": "x", "newText": "y"}, {"oldText": "a", "newText": "b"}]
        self.save("session.jsonl", [
            self.tool("a", None, "write"), self.result("b", "a", "write"),
            self.tool("c", "b", "edit", "edit", {"path": "src/main.ts", "edits": edits}, 4),
            self.result("d", "c", "edit", "edit", timestamp=5, details={"patch": "patch", "diff": "diff"}),
            self.tool("e", "d", "fail", timestamp=6), self.result("f", "e", "fail", error=True, timestamp=7),
            self.tool("g", "f", "unfinished", timestamp=8),
        ])
        data = self.export()
        session = data["sessions"][0]
        self.assertEqual([event["status"] for event in session["patch_operations"]],
                         ["succeeded", "succeeded", "failed", "unknown"])
        self.assertEqual(data["patch_replay_count"], 2)
        self.assertEqual(session["tool_error_count"], 1)
        self.assertEqual(data["patch_replay"][0]["operation"], "Write File")
        self.assertEqual(data["patch_replay"][0]["resolved_path"], "D:\\Projects\\app\\src\\main.ts")
        self.assertEqual(data["patch_replay"][1]["edits"], edits)
        self.assertEqual(data["patch_replay"][1]["patch"], "patch")
        self.assertEqual(session["messages"][0]["provider"], "example")

    def test_branch_ancestry_matches_reused_call_ids(self):
        self.save("branches.jsonl", [
            self.message("root", None, "user", "initial"),
            self.tool("left", "root", "reused", timestamp=2),
            self.result("left-result", "left", "reused", error=True, timestamp=3),
            self.tool("right", "root", "reused", timestamp=4),
            self.result("right-result", "right", "reused", timestamp=5),
        ])
        all_data = self.export()
        self.assertEqual([call["status"] for call in all_data["sessions"][0]["tool_calls"]], ["failed", "succeeded"])
        latest = self.export("--branch", "latest")
        self.assertEqual([entry["id"] for entry in latest["sessions"][0]["entries"]], ["root", "right", "right-result"])
        left = self.export("--leaf-id", "left-result")
        self.assertEqual(left["patch_replay_count"], 0)
        self.assertEqual(self.export("--leaf-id", "absent")["matched_sessions"], 0)

    def test_fork_dedup_preserves_occurrences_and_readonly_inputs(self):
        entries = [self.tool("a", None, "call"), self.result("b", "a", "call")]
        original = self.save("original.jsonl", entries)
        fork = self.save("fork.jsonl", entries, parent=str(original))
        before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in (original, fork)}
        data = self.export()
        self.assertEqual(data["matched_sessions"], 2)
        self.assertEqual(data["patch_replay_count"], 1)
        self.assertEqual(len(data["patch_replay"][0]["occurrences"]), 2)
        for path, state in before.items():
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), state)

    def test_legacy_linear_and_single_edit_arguments(self):
        records = [self.message("a", None, "hookMessage", "custom"),
                   self.tool("b", "a", "edit", "edit", {"path": "f", "oldText": "a", "newText": "b"}),
                   self.result("c", "b", "edit", "edit")]
        for record in records:
            del record["id"]
            del record["parentId"]
        self.save("legacy.jsonl", records, version=1)
        data = self.export("--branch", "latest")
        session = data["sessions"][0]
        self.assertEqual(session["messages"][0]["role"], "custom")
        self.assertEqual(session["entries"][1]["parentId"], "legacy-line-2")
        self.assertEqual(data["patch_replay"][0]["edits"], [{"oldText": "a", "newText": "b"}])

    def test_compaction_keeps_history_and_brief_omits_bodies(self):
        self.save("compact.jsonl", [
            self.message("a", None, "user", "Original prompt"),
            {"type": "compaction", "id": "b", "parentId": "a", "summary": "summary", "firstKeptEntryId": "a"},
            self.tool("c", "b", "call"), self.result("d", "c", "call"),
        ])
        data = self.export()
        self.assertEqual(data["sessions"][0]["messages"][0]["content"], "Original prompt")
        self.assertEqual(data["sessions"][0]["messages"][1]["role"], "compactionSummary")
        brief = self.export("--brief")
        self.assertIsNone(brief["patch_replay_count"])
        self.assertEqual(brief["patch_replay"], [])
        for key in ("messages", "entries", "tool_calls", "tool_results", "patch_operations"):
            self.assertNotIn(key, brief["sessions"][0])
        self.assertEqual(brief["sessions"][0]["successful_file_operation_count"], 1)

    def test_malformed_unknown_future_and_partial_tail(self):
        known = self.save("known.jsonl", [self.message("a", None, "user", "valid")])
        with known.open("a", encoding="utf-8") as handle:
            handle.write('\n{"type":')
        before = known.read_bytes()
        self.save("unknown.jsonl", [], cwd="")
        self.save("future.jsonl", [], version=4)
        data = self.export()
        self.assertEqual(data["scan"]["malformed_lines"], 1)
        self.assertEqual(data["scan"]["unsupported_files"], 1)
        self.assertEqual(data["scan"]["sessions_with_unknown_root"], 1)
        self.assertEqual(data["matched_sessions"], 1)
        self.assertEqual(self.export("--include-unknown")["matched_sessions"], 2)
        self.assertEqual(known.read_bytes(), before)

    def test_ordering_uses_results_and_limit_uses_activity(self):
        self.save("parallel.jsonl", [
            self.tool("a", None, "first", timestamp=2), self.tool("b", "a", "second", timestamp=3),
            self.result("c", "b", "second", timestamp=4), self.result("d", "c", "first", timestamp=5),
        ])
        data = self.export()
        self.assertEqual([event["call_id"] for event in data["patch_replay"]], ["second", "first"])
        self.assertEqual(traversal.timestamp_ms(5), 5)
        self.save("new.jsonl", [self.message("e", None, "user", "new", 2000000000000)])
        self.assertEqual(self.export("--limit", "1")["sessions"][0]["session_id"], "new.jsonl")
        self.assertEqual(self.export("--limit", "0")["matched_sessions"], 0)

    def test_images_and_tool_argument_search(self):
        self.save("image.jsonl", [
            self.message("a", None, "user", [{"type": "image", "data": "BASE64", "mimeType": "image/png"}]),
            self.tool("b", "a", "call", inputs={"path": "needle.txt", "content": "search"}),
        ])
        data = self.export("--contains", "needle")
        self.assertEqual(data["matched_sessions"], 1)
        self.assertNotIn("data", data["sessions"][0]["messages"][0]["content_blocks"][0])
        included = self.export("--include-images")
        self.assertEqual(included["sessions"][0]["messages"][0]["content_blocks"][0]["data"], "BASE64")
        self.assertEqual(self.export("--contains", "missing")["matched_sessions"], 0)

    def test_explicit_and_settings_locations_and_input_protection(self):
        target = self.save("protected.jsonl", [])
        before = target.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()):
            status = traversal.main(["--folder", "D:/Projects/app", "--pi-root", str(target), "--out", str(target)])
        self.assertEqual(status, 2)
        self.assertEqual(target.read_bytes(), before)
        agent = self.root / "agent"
        agent.mkdir()
        (agent / "settings.json").write_text(json.dumps({"sessionDir": str(self.history)}), encoding="utf-8")
        args = traversal.parse_args(["--folder", str(self.root), "--pi-root", str(agent),
                                     "--session-dir", str(target)])
        warnings = []
        locations = traversal.discover_locations(args, warnings)
        self.assertIn(self.history, locations)
        self.assertEqual(traversal.discover_files(locations, warnings), [target])

    def test_event_stream_capture_is_reported_as_unsupported_input(self):
        self.save("events.jsonl", [{"type": "agent_start"},
                                  {"type": "message_end", "message": {"role": "assistant", "content": []}}])
        data = self.export()
        self.assertEqual(data["matched_sessions"], 0)
        self.assertEqual(data["scan"]["valid_sessions"], 0)
        self.assertEqual(data["scan"]["invalid_files"], 1)
        self.assertTrue(data["warnings"])


if __name__ == "__main__":
    unittest.main()
