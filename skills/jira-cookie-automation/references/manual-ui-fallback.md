# Manual UI Fallback

Use this only when cookie-backed REST automation cannot perform the requested Jira action or when the user explicitly asks to drive the website.

## Stable Create Modal Flow

1. Keep one Jira issue page open.
2. Open the `Create Task` modal.
3. Keep `Create another` checked when creating multiple issues.
4. Keep project and work type stable.
5. Fill `Summary`.
6. Fill `Description`.
7. Set `Assignee`.
8. Set `Priority`.
9. Confirm labels and sprint behavior.
10. Click `Create`.
11. Read the new `APP-*` or project-specific key from the created-work-items link.
12. Write the key back to the local queue or progress log.

## Description Format

Use plain text:

```text
Implement:
- item
- item
Notes:
- item
Done when:
- item
```

Rules:

- Avoid extra blank lines between bullets.
- Do not include dependency blocks when dependencies will be represented as Jira links.
- Do not mention internal planning files unless the user explicitly wants that in Jira.

## Assignee Handling

- If assigning to the current user, use `Assign to me` when available.
- For others, type the full display name and choose the first exact match.
- If the wrong assignee was selected and the issue was already created, log it and fix it with the REST `assign` command if possible.

## Batch Safety

- Create 3 to 5 issues, then sync local progress.
- If unsure whether a row was created, check Jira, the progress log, and the local queue before continuing.
- Do not recreate rows that already have issue keys.

