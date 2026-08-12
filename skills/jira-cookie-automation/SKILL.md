---
name: jira-cookie-automation
description: Automate Jira work with a live browser session cookie, automatically bootstrapping `JIRA_COOKIE` from an existing Chrome DevTools MCP Jira browser session when available. Use when Codex needs to create, file, update, assign, comment on, link, transition, search, sprint-assign, verify, or batch-process Jira issues, especially when a repo has planning CSV/JSON files or when the user wants Jira website actions made repeatable from any workspace.
---

# Jira Cookie Automation

## Core Rule

Prefer cookie-backed Jira REST automation over manual browser navigation. Use manual Jira UI only when REST is blocked, the user explicitly asks for website navigation, or an operation cannot be represented safely through the API.

Before asking the user to paste `JIRA_COOKIE`, try to extract the Cookie request header from an existing authenticated Jira page in Chrome DevTools MCP. Never store Jira cookies in files, logs, skill resources, commits, or generated artifacts.

## Cookie Bootstrap Order

1. If Chrome DevTools MCP tools are available, use `references/mcp-cookie-bootstrap.md` and try to read the `Cookie` header from an authenticated Jira network request.
2. If MCP extraction succeeds, set `JIRA_BASE_URL` from the request origin and use that Cookie header as `JIRA_COOKIE` for the CLI command.
3. If MCP extraction fails because no Jira page or request is available, ask the user to open Jira and trigger any authenticated REST request, such as `/rest/api/3/myself`.
4. Ask the user to paste a cookie manually only when MCP is unavailable or cannot expose request headers.

## Quick Start

Use the bundled CLI from this skill directory:

```powershell
$env:JIRA_BASE_URL = 'https://your-site.atlassian.net'
$env:JIRA_COOKIE = 'paste the full Cookie request header here'
python scripts\jira_cookie.py whoami
```

Run write operations as dry-runs first:

```powershell
python scripts\jira_cookie.py create --dry-run --project APP --type Task --summary "Build shared shell" --description "Implement:`n- Build the route shell"
```

Then run the same command without `--dry-run` only after the payload is correct.

## Workflow

1. Identify the Jira base URL, project key, issue type, board ID, labels, priority names, and assignee names or account IDs from the repo, user message, or Jira itself.
2. Bootstrap `JIRA_COOKIE` from Chrome DevTools MCP when available. Fall back to manual cookie setup only if needed.
3. Run `whoami` to verify the cookie and base URL.
4. Use `search`, `get`, `user-search`, and `transitions` to discover current Jira state before writing.
5. For writes, run with `--dry-run` first and inspect the JSON payload.
6. Apply small batches. For issue creation, keep batches to 3 to 5 unless the user explicitly wants a larger automated run.
7. Verify by reading Jira back after each batch. Prefer the CLI's `--verify` flag where available.
8. Keep a local progress file or write-back CSV updated after successful batches.

## Common Commands

Authentication check:

```powershell
python scripts\jira_cookie.py whoami
```

Search issues:

```powershell
python scripts\jira_cookie.py search --jql "project = APP ORDER BY created DESC" --fields summary,status,assignee,priority
```

Create an issue:

```powershell
python scripts\jira_cookie.py create --project APP --type Task --summary "Implement profile shell" --description-file issue.txt --assignee "Jordan Hale" --priority High --label app-v2 --verify
```

Update summary, description, assignee, priority, or labels:

```powershell
python scripts\jira_cookie.py update APP-123 --summary "Implement profile shell route" --assignee "Jordan Hale" --priority Normal --verify
```

Assign an issue:

```powershell
python scripts\jira_cookie.py assign APP-123 --assignee "Riley Chen" --verify
```

Add a dependency link:

```powershell
python scripts\jira_cookie.py link --type Blocks --inward APP-124 --outward APP-123
```

This means Jira stores a `Blocks` link where `APP-124` is blocked by `APP-123`.

Transition an issue:

```powershell
python scripts\jira_cookie.py transition APP-123 --to Done --comment "Scope covered by APP-122."
```

Assign issues to a sprint:

```powershell
python scripts\jira_cookie.py assign-sprint --board-id 42 --sprint "App Sprint 6" --create-missing --issues APP-123 APP-124
```

Batch-create from CSV:

```powershell
python scripts\jira_cookie.py batch-create --csv jira-ui-create-queue.csv --project APP --type Task --summary-col Summary --description-col Description --assignee-col Assignee --priority-col Priority --label app-v2 --limit 5 --write-back --verify
```

See `references/batch-formats.md` for CSV and JSON plan patterns.

## Operating Rules

- Treat `JIRA_COOKIE` as a short-lived session secret. If a request returns 401, 403, CAPTCHA, or unexpected HTML, ask the user to refresh the cookie.
- Prefer an MCP-extracted cookie over asking the user to copy/paste one.
- Do not invent assignee account IDs. Resolve names with `user-search` or use IDs already present in trusted local files.
- Do not create duplicate issues. Search by summary, project, labels, or known issue keys before creating.
- Do not silently close or transition issues. Comment first when closing duplicates or retargeting scope.
- Use Jira read-back verification for summary, assignee, priority, labels, status, sprint, and links after writes.
- Keep project-specific constants out of the skill. Use environment variables, command flags, or repo-local config/docs.
- Keep generated logs free of cookie values and request headers.

## Resources

- `scripts/jira_cookie.py`: reusable Jira REST CLI backed by `JIRA_COOKIE`.
- `references/mcp-cookie-bootstrap.md`: Chrome DevTools MCP flow for extracting the Cookie header from an existing Jira browser session.
- `references/cookie-auth.md`: safe cookie acquisition and environment setup.
- `references/batch-formats.md`: reusable CSV/JSON shapes for filing, assignment, linking, sprint work, and resumable runs.
- `references/manual-ui-fallback.md`: condensed website-navigation fallback for the Jira create-issue UI.
