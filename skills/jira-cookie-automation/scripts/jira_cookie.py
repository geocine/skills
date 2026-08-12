#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WRITE_METHODS = {"POST", "PUT", "DELETE"}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def parse_json(text: str) -> Any | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def adf_from_text(text: str) -> dict[str, Any]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    content: list[dict[str, Any]] = []
    for line in text.split("\n"):
        if line == "":
            content.append({"type": "paragraph"})
        else:
            content.append({"type": "paragraph", "content": [{"type": "text", "text": line}]})
    if not content:
        content.append({"type": "paragraph"})
    return {"type": "doc", "version": 1, "content": content}


def read_text_arg(value: str | None, file_value: str | None) -> str | None:
    if value is not None and file_value is not None:
        raise SystemExit("Use either inline text or a file, not both.")
    if file_value is not None:
        return Path(file_value).read_text(encoding="utf-8")
    return value


def split_labels(values: list[str] | None) -> list[str]:
    labels: list[str] = []
    for value in values or []:
        for part in value.replace(";", ",").split(","):
            label = part.strip()
            if label and label not in labels:
                labels.append(label)
    return labels


def csv_cell(row: dict[str, str], column: str | None) -> str | None:
    if not column:
        return None
    value = row.get(column)
    if value is None:
        return None
    value = value.strip()
    return value or None


class JiraError(RuntimeError):
    pass


class JiraClient:
    def __init__(self, args: argparse.Namespace):
        base_url = args.base_url or os.environ.get("JIRA_BASE_URL")
        if not base_url:
            raise JiraError("Set JIRA_BASE_URL or pass --base-url.")
        self.base_url = base_url.rstrip("/")
        self.cookie_env = args.cookie_env
        self.referer = args.referer or os.environ.get("JIRA_REFERER") or self.base_url
        self.user_agent = args.user_agent or os.environ.get("JIRA_USER_AGENT") or DEFAULT_USER_AGENT
        self.dry_run = bool(getattr(args, "dry_run", False))

    @property
    def cookie(self) -> str | None:
        value = os.environ.get(self.cookie_env)
        return value if value else None

    def request(self, method: str, path: str, payload: Any | None = None) -> tuple[int, str, Any | None]:
        method = method.upper()
        url = f"{self.base_url}{path}"
        if self.dry_run and method in WRITE_METHODS:
            return 0, json.dumps({"dryRun": True, "method": method, "url": url, "payload": payload}), {
                "dryRun": True,
                "method": method,
                "url": url,
                "payload": payload,
            }

        cookie = self.cookie
        if not cookie:
            raise JiraError(f"{self.cookie_env} is not set in the shell environment.")

        headers = {
            "Cookie": cookie,
            "User-Agent": self.user_agent,
            "Referer": self.referer,
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                text = response.read().decode("utf-8", errors="replace")
                return response.status, text, parse_json(text)
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            return exc.code, text, parse_json(text)

    def expect(self, method: str, path: str, payload: Any | None, expected: set[int], action: str) -> Any | None:
        status, text, data = self.request(method, path, payload)
        if self.dry_run and method.upper() in WRITE_METHODS:
            return data
        if status not in expected:
            raise JiraError(f"{action} failed ({status}): {text}")
        return data

    def search_jql(self, jql: str, fields: list[str], max_results: int) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        next_page_token: str | None = None

        while True:
            payload: dict[str, Any] = {"jql": jql, "fields": fields, "maxResults": max_results}
            if next_page_token:
                payload["nextPageToken"] = next_page_token
            status, text, data = self.request("POST", "/rest/api/3/search/jql", payload)
            if status in {404, 410}:
                status, text, data = self.request("POST", "/rest/api/3/search", payload)
            if status != 200:
                raise JiraError(f"JQL search failed ({status}): {text}")
            issues.extend(data.get("issues", []))
            next_page_token = data.get("nextPageToken")
            if data.get("isLast", True) or not next_page_token:
                return issues

    def get_issue(self, issue_key: str, fields: list[str]) -> dict[str, Any]:
        query = urllib.parse.urlencode({"fields": ",".join(fields)})
        status, text, data = self.request("GET", f"/rest/api/3/issue/{issue_key}?{query}")
        if status != 200:
            raise JiraError(f"Fetch issue {issue_key} failed ({status}): {text}")
        return data

    def user_search(self, query: str) -> list[dict[str, Any]]:
        encoded = urllib.parse.urlencode({"query": query})
        status, text, data = self.request("GET", f"/rest/api/3/user/search?{encoded}")
        if status != 200:
            raise JiraError(f"User search failed ({status}): {text}")
        return data or []

    def resolve_user_id(self, query: str) -> str:
        users = self.user_search(query)
        normalized = query.strip().casefold()
        exact = [
            user
            for user in users
            if normalized
            in {
                str(user.get("accountId", "")).casefold(),
                str(user.get("displayName", "")).casefold(),
                str(user.get("emailAddress", "")).casefold(),
            }
        ]
        if len(exact) == 1:
            return exact[0]["accountId"]
        if len(users) == 1:
            return users[0]["accountId"]
        candidates = [
            {
                "accountId": user.get("accountId"),
                "displayName": user.get("displayName"),
                "emailAddress": user.get("emailAddress"),
            }
            for user in users[:10]
        ]
        raise JiraError(f"Could not resolve a single Jira user for {query!r}. Candidates: {json.dumps(candidates, ensure_ascii=False)}")

    def transition_id(self, issue_key: str, name: str) -> str:
        status, text, data = self.request("GET", f"/rest/api/3/issue/{issue_key}/transitions?expand=transitions.fields")
        if status != 200:
            raise JiraError(f"Fetch transitions failed for {issue_key} ({status}): {text}")
        transitions = data.get("transitions", [])
        for row in transitions:
            if row.get("name", "").casefold() == name.casefold():
                return row["id"]
        names = [row.get("name") for row in transitions]
        raise JiraError(f"No transition named {name!r} for {issue_key}. Available: {names}")

    def sprint_by_name(self, board_id: int, sprint_name: str, create_missing: bool = False) -> dict[str, Any]:
        status, text, data = self.request("GET", f"/rest/agile/1.0/board/{board_id}/sprint?maxResults=100")
        if status != 200:
            raise JiraError(f"Fetch sprints failed ({status}): {text}")
        for sprint in data.get("values", []):
            if sprint.get("name") == sprint_name:
                return sprint
        if not create_missing:
            raise JiraError(f"Sprint {sprint_name!r} not found on board {board_id}.")
        created = self.expect(
            "POST",
            "/rest/agile/1.0/sprint",
            {"name": sprint_name, "originBoardId": board_id},
            {201},
            f"Create sprint {sprint_name}",
        )
        return created


def common_fields_from_args(args: argparse.Namespace, client: JiraClient, include_project: bool) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if include_project:
        fields["project"] = {"key": args.project}
        fields["issuetype"] = {"name": args.type}
    if getattr(args, "summary", None):
        fields["summary"] = args.summary
    description = read_text_arg(getattr(args, "description", None), getattr(args, "description_file", None))
    if description is not None:
        fields["description"] = adf_from_text(description)
    if getattr(args, "priority", None):
        fields["priority"] = {"name": args.priority}
    labels = split_labels(getattr(args, "label", None))
    if labels:
        fields["labels"] = labels
    assignee_id = getattr(args, "assignee_id", None)
    assignee = getattr(args, "assignee", None)
    if assignee_id:
        fields["assignee"] = {"id": assignee_id}
    elif assignee and not client.dry_run:
        fields["assignee"] = {"id": client.resolve_user_id(assignee)}
    elif assignee:
        fields["assigneeLookup"] = assignee
    return fields


def issue_summary(issue: dict[str, Any]) -> dict[str, Any]:
    fields = issue.get("fields", {})
    assignee = fields.get("assignee") or {}
    priority = fields.get("priority") or {}
    status = fields.get("status") or {}
    return {
        "key": issue.get("key"),
        "summary": fields.get("summary"),
        "status": status.get("name"),
        "assignee": assignee.get("displayName"),
        "priority": priority.get("name"),
        "labels": fields.get("labels"),
    }


def verify_issue_fields(client: JiraClient, issue_key: str, expected_fields: dict[str, Any]) -> dict[str, Any]:
    fields_to_read = ["summary", "assignee", "priority", "labels", "status"]
    if "description" in expected_fields:
        fields_to_read.append("description")
    issue = client.get_issue(issue_key, fields_to_read)
    fields = issue["fields"]
    problems: list[str] = []
    if "summary" in expected_fields and fields.get("summary") != expected_fields["summary"]:
        problems.append("summary")
    if "priority" in expected_fields and (fields.get("priority") or {}).get("name") != expected_fields["priority"]["name"]:
        problems.append("priority")
    if "labels" in expected_fields and sorted(fields.get("labels") or []) != sorted(expected_fields["labels"]):
        problems.append("labels")
    if "description" in expected_fields and fields.get("description") != expected_fields["description"]:
        problems.append("description")
    if "assignee" in expected_fields:
        actual = (fields.get("assignee") or {}).get("accountId")
        if actual != expected_fields["assignee"]["id"]:
            problems.append("assignee")
    if problems:
        raise JiraError(f"Verification failed for {issue_key}: {', '.join(problems)} mismatch")
    return issue_summary(issue)


def cmd_whoami(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    status, text, data = client.request("GET", "/rest/api/3/myself")
    if status != 200:
        raise JiraError(f"Authentication check failed ({status}): {text}")
    print_json(
        {
            "baseUrl": client.base_url,
            "accountId": data.get("accountId"),
            "displayName": data.get("displayName"),
            "emailAddress": data.get("emailAddress"),
        }
    )


def cmd_user_search(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    users = client.user_search(args.query)
    print_json(
        [
            {
                "accountId": user.get("accountId"),
                "displayName": user.get("displayName"),
                "emailAddress": user.get("emailAddress"),
                "active": user.get("active"),
            }
            for user in users
        ]
    )


def cmd_search(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    fields = [part.strip() for part in args.fields.split(",") if part.strip()]
    issues = client.search_jql(args.jql, fields, args.max_results)
    print_json([issue_summary(issue) for issue in issues])


def cmd_get(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    fields = [part.strip() for part in args.fields.split(",") if part.strip()]
    print_json(client.get_issue(args.issue_key, fields))


def cmd_create(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    fields = common_fields_from_args(args, client, include_project=True)
    payload = {"fields": {k: v for k, v in fields.items() if k != "assigneeLookup"}}
    dry_note = {"assigneeLookup": fields["assigneeLookup"]} if "assigneeLookup" in fields else {}
    data = client.expect("POST", "/rest/api/3/issue", payload, {201}, "Create issue")
    if client.dry_run:
        print_json({**data, **dry_note})
        return
    issue_key = data["key"]
    result = {"key": issue_key}
    if args.verify:
        result["verified"] = verify_issue_fields(client, issue_key, payload["fields"])
    print_json(result)


def cmd_update(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    fields = common_fields_from_args(args, client, include_project=False)
    if args.add_label:
        issue = client.get_issue(args.issue_key, ["labels"]) if not client.dry_run else {"fields": {"labels": []}}
        fields["labels"] = sorted(set((issue["fields"].get("labels") or []) + split_labels(args.add_label)))
    fields = {k: v for k, v in fields.items() if k != "assigneeLookup"}
    if not fields:
        raise JiraError("No update fields were provided.")
    payload = {"fields": fields}
    data = client.expect("PUT", f"/rest/api/3/issue/{args.issue_key}", payload, {204}, f"Update {args.issue_key}")
    if client.dry_run:
        print_json(data)
        return
    result = {"key": args.issue_key, "updated": sorted(fields)}
    if args.verify:
        result["verified"] = verify_issue_fields(client, args.issue_key, fields)
    print_json(result)


def cmd_assign(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    if args.assignee_id:
        account_id = args.assignee_id
    elif client.dry_run:
        account_id = args.assignee
    else:
        account_id = client.resolve_user_id(args.assignee)
    payload = {"accountId": account_id}
    data = client.expect("PUT", f"/rest/api/3/issue/{args.issue_key}/assignee", payload, {204}, f"Assign {args.issue_key}")
    if client.dry_run:
        print_json(data)
        return
    result = {"key": args.issue_key, "assigneeAccountId": account_id}
    if args.verify:
        issue = client.get_issue(args.issue_key, ["assignee"])
        result["verified"] = issue_summary(issue)
    print_json(result)


def cmd_comment(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    text = read_text_arg(args.text, args.file)
    if not text:
        raise JiraError("Comment text is required.")
    payload = {"body": adf_from_text(text)}
    data = client.expect("POST", f"/rest/api/3/issue/{args.issue_key}/comment", payload, {201}, f"Comment on {args.issue_key}")
    print_json(data if client.dry_run else {"key": args.issue_key, "commentId": data.get("id")})


def cmd_transitions(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    status, text, data = client.request("GET", f"/rest/api/3/issue/{args.issue_key}/transitions?expand=transitions.fields")
    if status != 200:
        raise JiraError(f"Fetch transitions failed ({status}): {text}")
    print_json([{"id": row.get("id"), "name": row.get("name")} for row in data.get("transitions", [])])


def cmd_transition(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    if args.comment:
        payload = {"body": adf_from_text(args.comment)}
        client.expect("POST", f"/rest/api/3/issue/{args.issue_key}/comment", payload, {201}, f"Comment on {args.issue_key}")
    transition_id = args.transition_id if args.transition_id else client.transition_id(args.issue_key, args.to)
    payload = {"transition": {"id": transition_id}}
    data = client.expect("POST", f"/rest/api/3/issue/{args.issue_key}/transitions", payload, {204}, f"Transition {args.issue_key}")
    if client.dry_run:
        print_json(data)
        return
    result = {"key": args.issue_key, "transition": args.to, "transitionId": transition_id}
    if args.verify:
        issue = client.get_issue(args.issue_key, ["status"])
        result["verified"] = issue_summary(issue)
    print_json(result)


def cmd_link(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    payload = {
        "type": {"name": args.type},
        "inwardIssue": {"key": args.inward},
        "outwardIssue": {"key": args.outward},
    }
    status, text, data = client.request("POST", "/rest/api/3/issueLink", payload)
    if client.dry_run:
        print_json(data)
        return
    if status == 201 or (status == 400 and "already exists" in text.lower() and args.ignore_existing):
        print_json({"type": args.type, "inward": args.inward, "outward": args.outward, "status": "ok"})
        return
    raise JiraError(f"Create link failed ({status}): {text}")


def cmd_sprints(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    status, text, data = client.request("GET", f"/rest/agile/1.0/board/{args.board_id}/sprint?maxResults={args.max_results}")
    if status != 200:
        raise JiraError(f"Fetch sprints failed ({status}): {text}")
    print_json(data.get("values", []))


def cmd_ensure_sprint(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    sprint = client.sprint_by_name(args.board_id, args.name, create_missing=True)
    print_json(sprint)


def cmd_assign_sprint(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    if args.sprint_id:
        sprint_id = args.sprint_id
        sprint_name = args.sprint or str(sprint_id)
    else:
        if not args.sprint:
            raise JiraError("Pass --sprint or --sprint-id.")
        sprint = client.sprint_by_name(args.board_id, args.sprint, create_missing=args.create_missing)
        sprint_id = sprint["id"]
        sprint_name = sprint["name"]
    payload = {"issues": args.issues}
    data = client.expect("POST", f"/rest/agile/1.0/sprint/{sprint_id}/issue", payload, {204}, f"Assign sprint {sprint_name}")
    if client.dry_run:
        print_json(data)
        return
    print_json({"sprint": sprint_name, "sprintId": sprint_id, "issues": args.issues})


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fields_from_csv_row(args: argparse.Namespace, client: JiraClient, row: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    summary = csv_cell(row, args.summary_col)
    if not summary:
        raise JiraError(f"Missing summary column {args.summary_col!r} in row: {row}")
    fields: dict[str, Any] = {
        "project": {"key": args.project},
        "issuetype": {"name": args.type},
        "summary": summary,
    }
    description = csv_cell(row, args.description_col)
    if description:
        fields["description"] = adf_from_text(description)
    priority = csv_cell(row, args.priority_col)
    if priority:
        fields["priority"] = {"name": priority}
    labels = split_labels(args.label)
    labels_from_col = csv_cell(row, args.labels_col)
    if labels_from_col:
        labels = sorted(set(labels + split_labels([labels_from_col])))
    if labels:
        fields["labels"] = labels
    dry_note: dict[str, Any] = {}
    assignee_id = csv_cell(row, args.assignee_id_col)
    assignee = csv_cell(row, args.assignee_col)
    if assignee_id:
        fields["assignee"] = {"id": assignee_id}
    elif assignee and not client.dry_run:
        fields["assignee"] = {"id": client.resolve_user_id(assignee)}
    elif assignee:
        dry_note["assigneeLookup"] = assignee
    return fields, dry_note


def cmd_batch_create(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    path = Path(args.csv)
    rows, fieldnames = read_csv_rows(path)
    for column in [args.created_key_col, args.created_flag_col]:
        if column and column not in fieldnames:
            fieldnames.append(column)

    planned: list[dict[str, Any]] = []
    created: list[dict[str, Any]] = []
    processed = 0
    backup_path: Path | None = None

    for index, row in enumerate(rows, start=1):
        if not args.include_created and csv_cell(row, args.created_key_col):
            continue
        if args.limit and processed >= args.limit:
            break
        fields, dry_note = fields_from_csv_row(args, client, row)
        payload = {"fields": fields}
        if client.dry_run:
            planned.append({"row": index, "payload": payload, **dry_note})
            processed += 1
            continue

        data = client.expect("POST", "/rest/api/3/issue", payload, {201}, f"Create row {index}")
        issue_key = data["key"]
        if args.verify:
            verify_issue_fields(client, issue_key, fields)
        row[args.created_key_col] = issue_key
        row[args.created_flag_col] = "yes"
        created.append({"row": index, "key": issue_key, "summary": fields["summary"]})
        processed += 1

        if args.write_back:
            if backup_path is None:
                backup_path = path.with_suffix(path.suffix + f".{utc_stamp()}.bak")
                shutil.copy2(path, backup_path)
            write_csv_rows(path, rows, fieldnames)

    if client.dry_run:
        print_json({"planned": planned, "count": len(planned)})
    else:
        print_json({"created": created, "count": len(created), "writeBack": args.write_back, "backup": str(backup_path) if backup_path else None})


def operation_done(state: dict[str, Any], operation_id: str) -> bool:
    return operation_id in state.setdefault("done", [])


def mark_done(state_path: Path | None, state: dict[str, Any], operation_id: str) -> None:
    if operation_id not in state.setdefault("done", []):
        state["done"].append(operation_id)
    if state_path:
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def load_plan_state(path: str | None) -> tuple[Path | None, dict[str, Any]]:
    if not path:
        return None, {"done": [], "createdKeys": {}}
    state_path = Path(path)
    if state_path.exists():
        return state_path, json.loads(state_path.read_text(encoding="utf-8"))
    state = {"done": [], "createdKeys": {}}
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    return state_path, state


def key_from_plan_ref(state: dict[str, Any], value: str) -> str:
    created = state.get("createdKeys", {})
    return created.get(value, value)


def fields_from_plan_item(client: JiraClient, item: dict[str, Any], include_project: bool) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if include_project:
        fields["project"] = {"key": item["project"]}
        fields["issuetype"] = {"name": item.get("type", "Task")}
    for key in ["summary"]:
        if item.get(key):
            fields[key] = item[key]
    if item.get("description"):
        fields["description"] = adf_from_text(item["description"])
    elif item.get("descriptionAdf"):
        fields["description"] = item["descriptionAdf"]
    if item.get("priority"):
        fields["priority"] = {"name": item["priority"]}
    if item.get("labels"):
        fields["labels"] = item["labels"]
    if item.get("assigneeAccountId"):
        fields["assignee"] = {"id": item["assigneeAccountId"]}
    elif item.get("assignee") and not client.dry_run:
        fields["assignee"] = {"id": client.resolve_user_id(item["assignee"])}
    elif item.get("assignee"):
        fields["assigneeLookup"] = item["assignee"]
    return fields


def cmd_apply_plan(args: argparse.Namespace) -> None:
    client = JiraClient(args)
    plan = json.loads(Path(args.json).read_text(encoding="utf-8"))
    state_path, state = load_plan_state(args.state)
    results: list[dict[str, Any]] = []

    for index, item in enumerate(plan.get("creates", []), start=1):
        stable_id = item.get("id") or f"create:{index}:{item.get('summary', '')}"
        op_id = f"create:{stable_id}"
        if operation_done(state, op_id):
            continue
        fields = fields_from_plan_item(client, item, include_project=True)
        payload = {"fields": {k: v for k, v in fields.items() if k != "assigneeLookup"}}
        data = client.expect("POST", "/rest/api/3/issue", payload, {201}, f"Create {stable_id}")
        if client.dry_run:
            results.append({"operation": op_id, "dryRun": data})
            continue
        issue_key = data["key"]
        state.setdefault("createdKeys", {})[stable_id] = issue_key
        if args.verify:
            verify_issue_fields(client, issue_key, payload["fields"])
        mark_done(state_path, state, op_id)
        results.append({"operation": op_id, "key": issue_key})

    for item in plan.get("updates", []):
        issue_key = key_from_plan_ref(state, item["issueKey"])
        op_id = f"update:{issue_key}"
        if operation_done(state, op_id):
            continue
        fields = fields_from_plan_item(client, item, include_project=False)
        fields = {k: v for k, v in fields.items() if k != "assigneeLookup"}
        payload = {"fields": fields}
        data = client.expect("PUT", f"/rest/api/3/issue/{issue_key}", payload, {204}, f"Update {issue_key}")
        if client.dry_run:
            results.append({"operation": op_id, "dryRun": data})
            continue
        if args.verify:
            verify_issue_fields(client, issue_key, fields)
        mark_done(state_path, state, op_id)
        results.append({"operation": op_id, "key": issue_key})

    for index, item in enumerate(plan.get("comments", []), start=1):
        issue_key = key_from_plan_ref(state, item["issueKey"])
        op_id = item.get("id") or f"comment:{issue_key}:{index}"
        if operation_done(state, op_id):
            continue
        data = client.expect(
            "POST",
            f"/rest/api/3/issue/{issue_key}/comment",
            {"body": adf_from_text(item["text"])},
            {201},
            f"Comment {issue_key}",
        )
        if client.dry_run:
            results.append({"operation": op_id, "dryRun": data})
            continue
        mark_done(state_path, state, op_id)
        results.append({"operation": op_id, "key": issue_key})

    for item in plan.get("links", []):
        inward = key_from_plan_ref(state, item["inward"])
        outward = key_from_plan_ref(state, item["outward"])
        link_type = item.get("type", "Blocks")
        op_id = item.get("id") or f"link:{link_type}:{inward}:{outward}"
        if operation_done(state, op_id):
            continue
        payload = {"type": {"name": link_type}, "inwardIssue": {"key": inward}, "outwardIssue": {"key": outward}}
        status, text, data = client.request("POST", "/rest/api/3/issueLink", payload)
        if client.dry_run:
            results.append({"operation": op_id, "dryRun": data})
            continue
        if status != 201 and not (status == 400 and "already exists" in text.lower()):
            raise JiraError(f"Create link failed ({status}): {text}")
        mark_done(state_path, state, op_id)
        results.append({"operation": op_id, "inward": inward, "outward": outward})

    for item in plan.get("transitions", []):
        issue_key = key_from_plan_ref(state, item["issueKey"])
        transition_name = item["to"]
        op_id = item.get("id") or f"transition:{issue_key}:{transition_name}"
        if operation_done(state, op_id):
            continue
        transition_id = item.get("transitionId") or client.transition_id(issue_key, transition_name)
        data = client.expect(
            "POST",
            f"/rest/api/3/issue/{issue_key}/transitions",
            {"transition": {"id": transition_id}},
            {204},
            f"Transition {issue_key}",
        )
        if client.dry_run:
            results.append({"operation": op_id, "dryRun": data})
            continue
        mark_done(state_path, state, op_id)
        results.append({"operation": op_id, "key": issue_key})

    for index, item in enumerate(plan.get("sprints", []), start=1):
        board_id = int(item["boardId"])
        sprint_name = item["sprint"]
        issues = [key_from_plan_ref(state, key) for key in item["issues"]]
        op_id = item.get("id") or f"sprint:{board_id}:{sprint_name}:{index}"
        if operation_done(state, op_id):
            continue
        sprint = client.sprint_by_name(board_id, sprint_name, create_missing=bool(item.get("createMissing")))
        data = client.expect(
            "POST",
            f"/rest/agile/1.0/sprint/{sprint['id']}/issue",
            {"issues": issues},
            {204},
            f"Assign sprint {sprint_name}",
        )
        if client.dry_run:
            results.append({"operation": op_id, "dryRun": data})
            continue
        mark_done(state_path, state, op_id)
        results.append({"operation": op_id, "sprint": sprint_name, "issues": issues})

    print_json({"results": results, "state": state})


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default=None, help="Jira base URL. Defaults to JIRA_BASE_URL.")
    parser.add_argument("--cookie-env", default="JIRA_COOKIE", help="Environment variable containing the full Cookie header.")
    parser.add_argument("--referer", default=None, help="Referer header. Defaults to JIRA_REFERER or base URL.")
    parser.add_argument("--user-agent", default=None, help="User-Agent header. Defaults to a Chrome-like value.")
    parser.add_argument("--dry-run", action="store_true", help="Print write payloads instead of sending POST/PUT/DELETE requests.")


def add_issue_write_args(parser: argparse.ArgumentParser, include_project: bool) -> None:
    if include_project:
        parser.add_argument("--project", required=True)
        parser.add_argument("--type", default="Task")
    parser.add_argument("--summary")
    parser.add_argument("--description")
    parser.add_argument("--description-file")
    parser.add_argument("--assignee")
    parser.add_argument("--assignee-id")
    parser.add_argument("--priority")
    parser.add_argument("--label", action="append")
    parser.add_argument("--verify", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jira REST automation using a live browser session cookie.")
    add_common(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("whoami")
    p.set_defaults(func=cmd_whoami)

    p = sub.add_parser("user-search")
    p.add_argument("query")
    p.set_defaults(func=cmd_user_search)

    p = sub.add_parser("search")
    p.add_argument("--jql", required=True)
    p.add_argument("--fields", default="summary,status,assignee,priority,labels")
    p.add_argument("--max-results", type=int, default=100)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("get")
    p.add_argument("issue_key")
    p.add_argument("--fields", default="summary,status,assignee,priority,labels,description")
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("create")
    add_issue_write_args(p, include_project=True)
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("update")
    p.add_argument("issue_key")
    add_issue_write_args(p, include_project=False)
    p.add_argument("--add-label", action="append")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("assign")
    p.add_argument("issue_key")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--assignee")
    group.add_argument("--assignee-id")
    p.add_argument("--verify", action="store_true")
    p.set_defaults(func=cmd_assign)

    p = sub.add_parser("comment")
    p.add_argument("issue_key")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--text")
    group.add_argument("--file")
    p.set_defaults(func=cmd_comment)

    p = sub.add_parser("transitions")
    p.add_argument("issue_key")
    p.set_defaults(func=cmd_transitions)

    p = sub.add_parser("transition")
    p.add_argument("issue_key")
    p.add_argument("--to", required=True)
    p.add_argument("--transition-id")
    p.add_argument("--comment")
    p.add_argument("--verify", action="store_true")
    p.set_defaults(func=cmd_transition)

    p = sub.add_parser("link")
    p.add_argument("--type", default="Blocks")
    p.add_argument("--inward", required=True)
    p.add_argument("--outward", required=True)
    p.add_argument("--ignore-existing", action="store_true", default=True)
    p.set_defaults(func=cmd_link)

    p = sub.add_parser("sprints")
    p.add_argument("--board-id", type=int, required=True)
    p.add_argument("--max-results", type=int, default=100)
    p.set_defaults(func=cmd_sprints)

    p = sub.add_parser("ensure-sprint")
    p.add_argument("--board-id", type=int, required=True)
    p.add_argument("--name", required=True)
    p.set_defaults(func=cmd_ensure_sprint)

    p = sub.add_parser("assign-sprint")
    p.add_argument("--board-id", type=int, required=True)
    p.add_argument("--sprint")
    p.add_argument("--sprint-id", type=int)
    p.add_argument("--create-missing", action="store_true")
    p.add_argument("--issues", nargs="+", required=True)
    p.set_defaults(func=cmd_assign_sprint)

    p = sub.add_parser("batch-create")
    p.add_argument("--csv", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--type", default="Task")
    p.add_argument("--summary-col", default="Summary")
    p.add_argument("--description-col", default="Description")
    p.add_argument("--assignee-col")
    p.add_argument("--assignee-id-col")
    p.add_argument("--priority-col")
    p.add_argument("--labels-col")
    p.add_argument("--label", action="append")
    p.add_argument("--created-key-col", default="CreatedKey")
    p.add_argument("--created-flag-col", default="Created")
    p.add_argument("--include-created", action="store_true")
    p.add_argument("--limit", type=int)
    p.add_argument("--write-back", action="store_true")
    p.add_argument("--verify", action="store_true")
    p.set_defaults(func=cmd_batch_create)

    p = sub.add_parser("apply-plan")
    p.add_argument("--json", required=True)
    p.add_argument("--state")
    p.add_argument("--verify", action="store_true")
    p.set_defaults(func=cmd_apply_plan)

    return parser


def normalize_global_args(argv: list[str]) -> list[str]:
    """Allow global options before or after the subcommand.

    argparse normally requires top-level options before the subcommand. Agents
    and humans commonly type `create --dry-run`, so move known global options to
    the front before parsing.
    """

    flags = {"--dry-run"}
    options = {"--base-url", "--cookie-env", "--referer", "--user-agent"}
    front: list[str] = []
    rest: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token in flags:
            front.append(token)
            i += 1
            continue
        if token in options and i + 1 < len(argv):
            front.extend([token, argv[i + 1]])
            i += 2
            continue
        if any(token.startswith(option + "=") for option in options):
            front.append(token)
            i += 1
            continue
        rest.append(token)
        i += 1
    return front + rest


def main() -> None:
    parser = build_parser()
    args = parser.parse_args(normalize_global_args(sys.argv[1:]))
    try:
        args.func(args)
    except JiraError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
