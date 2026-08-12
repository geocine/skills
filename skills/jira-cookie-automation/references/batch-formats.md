# Batch Formats

Use this reference when converting planning files into repeatable Jira operations.

## CSV Issue Creation

Recommended columns:

```csv
Summary,Description,Assignee,Priority,Labels,CreatedKey,Created
"Build shared top bar","Implement:\n- Create reusable top bar","Riley Chen","High","app-v2",,
```

Run:

```powershell
python scripts\jira_cookie.py batch-create --csv queue.csv --project APP --type Task --summary-col Summary --description-col Description --assignee-col Assignee --priority-col Priority --labels-col Labels --limit 5 --write-back --verify
```

Rules:

- Keep `CreatedKey` and `Created` columns so reruns skip completed rows.
- Use `--limit 3` to `--limit 5` for fragile UI-derived queues.
- Use `--dry-run` before creating live issues.
- Use `--label` for fixed labels and `--labels-col` for row-specific labels.

## JSON Operation Plan

For more complex work, use `apply-plan` with this shape:

```json
{
  "creates": [
    {
      "id": "UXM-001",
      "project": "APP",
      "type": "Task",
      "summary": "Run baseline shell architecture audit",
      "description": "Implement:\n- Document shell ownership",
      "assignee": "Jordan Hale",
      "priority": "High",
      "labels": ["app-v2"]
    }
  ],
  "updates": [
    {
      "issueKey": "APP-123",
      "summary": "Implement shell route map",
      "assignee": "Jordan Hale",
      "priority": "Normal",
      "labels": ["app-v2"]
    }
  ],
  "links": [
    {
      "type": "Blocks",
      "inward": "APP-124",
      "outward": "APP-123"
    }
  ],
  "comments": [
    {
      "issueKey": "APP-125",
      "text": "Scope covered by APP-124."
    }
  ],
  "transitions": [
    {
      "issueKey": "APP-125",
      "to": "Done"
    }
  ],
  "sprints": [
    {
      "boardId": 42,
      "sprint": "App Sprint 6",
      "createMissing": true,
      "issues": ["APP-123", "APP-124"]
    }
  ]
}
```

Run:

```powershell
python scripts\jira_cookie.py apply-plan --json jira-plan.json --state jira-plan-state.json --verify
```

`apply-plan` records completed operation IDs in the state file so interrupted runs can resume without repeating successful writes. For creates, include a stable `id`; the created Jira key is recorded under `createdKeys`.

## Description Text

Prefer plain text input and let the CLI convert it into Jira ADF:

```text
Implement:
- item
- item
Notes:
- item
Done when:
- item
```

Avoid embedding internal planning-file references unless the Jira audience should see them.

