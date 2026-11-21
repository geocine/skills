---
name: mcp-switch
description: Turn a heavy MCP server (blender, cascadeur, or any other gated one) on or off for the current project, or say which are on. Use when the user says "turn on blender", "enable the cascadeur mcp", "I need blender here", "turn off blender", "disable cascadeur", "which mcps are on", or wants to gate a new MCP server so it only runs in projects that ask for it.
---

# MCP switch

Some MCP servers are defined once, globally, in `~/.claude.json`, but start
through a launcher, `%USERPROFILE%\.claude\mcp-gate\gate.cmd <name>`. The
launcher starts the real server only when the session's folder (or one of its
parents) has a file `.claude/mcp-on/<name>`. Anywhere else it exits at once:
`/mcp` shows the server as failed there, which is expected and harmless, and
nothing keeps running.

The real command line for each gated server is one file,
`%USERPROFILE%\.claude\mcp-gate\servers\<name>.cmd`. `%MCP_PROJECT%` there is
the folder that holds the marker (useful as a server's workspace argument).
The gated servers are the files in that folder; list them rather than assume.

Windows only: the launcher is a `cmd` batch file.

## Install the launcher

Do this once, when `%USERPROFILE%\.claude\mcp-gate\gate.cmd` doesn't exist.

1. Copy `mcp-gate/gate.cmd` from this skill's directory to
   `%USERPROFILE%\.claude\mcp-gate\gate.cmd`, keeping CRLF line endings.
2. Create the empty folder `%USERPROFILE%\.claude\mcp-gate\servers\`.
3. `mcp-gate/servers.example/` in this skill holds sample server files
   (blender, cascadeur). They are examples, not installed: gate a server with
   "Gate a new server" below, which writes its file from the user's real
   `~/.claude.json` entry.

## Turn one on

1. Take the project root: the git root of the current folder
   (`git rev-parse --show-toplevel`), else the current folder. Say which folder
   you use.
2. Check the name is gated: `%USERPROFILE%\.claude\mcp-gate\servers\<name>.cmd`
   exists. If not, say so and offer "Gate a new server" below.
3. Create the empty file `<root>/.claude/mcp-on/<name>`.
4. Tell the user it takes effect in a new session here, or now with `/mcp`
   (pick the server, Reconnect). Claude can't reconnect its own servers.

The marker is a plain file in the repo. If the project is shared and they
don't want it committed, offer to add `.claude/mcp-on/` to `.gitignore`; don't
do it unasked.

## Turn one off

Delete `<root>/.claude/mcp-on/<name>` (and the folder if it's empty). The
server already running in open sessions stops when those sessions end or on
`/mcp` Reconnect.

## Which are on

List the `.claude/mcp-on/` folders from the current folder up to the drive
root, and name each file found.

## Gate a new server

Only when the user asks to gate one (for example, "make godot opt-in too").
Install the launcher first if it's missing.

1. Read its entry in `~/.claude.json` `mcpServers` (don't print `env` values:
   they can be secrets).
2. Write `%USERPROFILE%\.claude\mcp-gate\servers\<name>.cmd`: one line,
   `@"<command>" <args...>`, quoting paths, CRLF line endings. Use
   `%MCP_PROJECT%` for any argument that should be the project folder.
3. Back up `~/.claude.json`, then set that entry's `command` to `cmd` and
   `args` to `["/d", "/c", "<gate path>", "<name>"]`, keeping `type` and
   `env`. `<gate path>` is the launcher's absolute path with `%USERPROFILE%`
   expanded and backslashes escaped for JSON, for example
   `"C:\\Users\\<you>\\.claude\\mcp-gate\\gate.cmd"`.
4. Check with `claude mcp list` in a folder with the marker (Connected) and one
   without (Failed to connect).

A project-scoped entry with the same name (`projects[...].mcpServers` in
`~/.claude.json`, or a project `.mcp.json`) wins over the global one and isn't
gated. If a server still starts in a project without a marker, look for one of
those.
