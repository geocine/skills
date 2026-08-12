# Cookie Auth

Use this reference when Chrome DevTools MCP cookie bootstrap is unavailable or fails. Prefer `mcp-cookie-bootstrap.md` first when an authenticated Jira browser session already exists.

## Required Environment

```powershell
$env:JIRA_BASE_URL = 'https://your-site.atlassian.net'
$env:JIRA_COOKIE = 'paste the full Cookie request header value here'
```

`JIRA_BASE_URL` may also be passed as `--base-url`.

## Getting The Cookie

1. Sign in to Jira in a normal browser session.
2. Open DevTools on a Jira page from the same Atlassian site.
3. Open the Network tab.
4. Click a successful same-origin Jira API request, such as `/rest/api/3/myself`.
5. Copy the full `Cookie` request header value.
6. Paste it into `JIRA_COOKIE` for the current shell only.

## Validation

Run:

```powershell
python scripts\jira_cookie.py whoami
```

If validation fails:

- 401 or 403 usually means the cookie expired, was copied incompletely, or belongs to the wrong Jira site.
- HTML instead of JSON usually means Jira redirected to login or an interstitial.
- Empty cookie errors mean the shell environment variable is not visible to the command.

## Security Rules

- Never write the cookie into a repo file, skill file, log, or command output.
- Never include request headers in progress logs.
- Ask the user for a fresh cookie instead of trying to recover one from browser storage.
