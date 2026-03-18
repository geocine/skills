# Geocine Skills

Public skill repository and installer for Geocine agent skills.

## Quick Start

```bash
npx -y @geocine/skills
```

Install a specific skill into the current repository:

```bash
npx -y @geocine/skills frontend-design --project
```

## Available Skills

| Skill | Description |
| --- | --- |
| `frontend-design` | Create distinctive, production-grade frontend interfaces with high design quality. |
| `skill-creator` | Guide for creating effective skills. |
| `zinc-design-system` | Dark, technical design system built on pure black with zinc accents. |

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
