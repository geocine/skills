# Geocine Skills

Public skill repository and installer for Geocine agent skills.

## Quick Start

```bash
npx -y @geocine/skills
```

Install a specific skill into the current repository:

```bash
npx -y @geocine/skills skill-judge --project
```

## Available Skills

| Skill | Description |
| --- | --- |
| `architecture-report` | Document a codebase's architecture, or a scoped part of it, as one self-contained HTML report with diagrams and a glossary. |
| `branch-backup-split-commits` | Back up a dirty Git worktree to a safety branch, split the changes into conventional commits, and verify tree-hash alignment. |
| `cargo-fork-optimize` | Move a Rust project onto the huacnlee/cargo fork for shared deps, small target dirs and less disk use. |
| `claude-history-traversal` | Traverse Claude Code session JSONL history and export folder-scoped timeline JSON. |
| `codex-history-traversal` | Traverse Codex rollout JSONL history and replay `apply_patch` operations chronologically. |
| `contributing-guide` | Generate a CONTRIBUTING.md and README section enforcing an issue-first workflow with AI disclosure. |
| `council` | Have Claude, Codex, Grok, and Gemini (through Cursor) independently review a design, decision, or change, then reconcile their verdicts. |
| `cursor-history-traversal` | Traverse Cursor chat history from local SQLite databases and export folder-scoped timeline JSON. |
| `decision-models` | Explain and apply decision models: TypeSafe System One (Jev), classifiers, encoders, and constrained decoding. |
| `grok-history-traversal` | Traverse Grok CLI session JSONL history and export folder-scoped timeline JSON. |
| `jira-cookie-automation` | Automate Jira through cookie-backed REST, bootstrapping the cookie from a Chrome DevTools MCP session. |
| `muse-windows-installer` | Install and update Meta Muse on Windows through Git Bash with a Windows-safe launcher fallback. |
| `pi-history-traversal` | Traverse Pi coding-agent session JSONL history, inspect branches and tool results, and export folder-scoped timeline JSON. |
| `skill-judge` | Test, score, and improve an agent skill before publishing, using subagent runs and a rubric-based judge. |
| `system-design-from-references` | Compare architecture reports of reference systems and write a clean-room architecture proposal and build plan. |
| `technical-writing` | Write, rewrite and review explainers and reference docs so a busy reader can follow and act on them. |
| `windows-minidump-analyzer` | Analyze Windows crash dumps (.dmp) and generate markdown reports via cdb.exe or header parsing. |
| `planpack` | Bootstrap a shared planning pack (graph wiki + comments). Lives in [geocine/planpack](https://github.com/geocine/planpack). |

## Commands

```bash
skills
skills <skill-name> --project
skills install <skill-name> --project
skills add <skill-name> --project
skills list --details
skills update
```

## Install Targets

- `.agents/skills` for GitHub Copilot, Cursor, Codex, and OpenCode
- `.claude/skills` for Claude Code

## Repository Override

The CLI defaults to `git@github.com:geocine/skills.git`.

Override it per run:

```bash
skills --repo-url <git-url>
```

Or via environment:

```bash
SKILLS_REPO_URL=<git-url> skills
```

## Local Development

```bash
npm install
npm run build
npm test
npm run skills
```

When run inside this repository, the CLI prefers the local checkout instead of cloning the cache.

## License

MIT
