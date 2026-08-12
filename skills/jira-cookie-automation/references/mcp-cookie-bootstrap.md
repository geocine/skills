# Chrome DevTools MCP Cookie Bootstrap

Use this reference before asking the user to paste `JIRA_COOKIE`.

## Goal

Reuse the user's already-authenticated Jira browser session by reading the `Cookie` request header from Chrome DevTools MCP network data.

## Preferred Flow

1. Call Chrome DevTools MCP `list_pages`.
2. Prefer a page whose URL origin is the target Jira site, for example `https://example.atlassian.net`.
3. Call `list_network_requests` for the current page with preserved requests enabled when the tool supports it.
4. Prefer authenticated Jira REST requests in this order:
   - `/rest/api/3/myself`
   - `/rest/api/3/search` or `/rest/api/3/search/jql`
   - `/rest/api/3/issue/`
   - `/rest/agile/1.0/`
   - any same-origin Jira REST request
5. Call `get_network_request` for the selected request ID.
6. Extract the request header named `Cookie` or `cookie`.
7. Derive `JIRA_BASE_URL` from the request URL origin.
8. Run `scripts/jira_cookie.py whoami` with that cookie in the process environment to verify it.

## If No Request Has A Cookie Header

Ask the user to open Jira in the MCP-controlled Chrome session and trigger an authenticated request. The easiest options are:

- reload a Jira issue page
- open the Jira project board/backlog
- visit a URL that causes `/rest/api/3/myself` to appear in the Network panel

Then repeat the extraction flow.

## If The Only Available Cookie Is `document.cookie`

Do not rely on it for Jira automation unless there is no alternative. `document.cookie` omits HttpOnly cookies, which are often required for authenticated Jira REST calls.

## Handling The Cookie

- Do not print the cookie in user-facing messages.
- Do not write the cookie to repo files, temp files, progress logs, or skill resources.
- Do not include request headers in saved artifacts.
- Keep the cookie only long enough to run Jira commands for the current task.
- If a shell command must receive the cookie, pass it as `JIRA_COOKIE` for that command invocation and avoid echoing it.

