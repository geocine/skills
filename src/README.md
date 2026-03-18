# skills

`skills` is the public npm CLI for installing Geocine skills from a Git repository you can access.

## Usage

```bash
npx -y @geocine/skills
```

## Install A Skill

```bash
npx -y @geocine/skills <skill-name> --project
```

Examples:

```bash
npx -y @geocine/skills frontend-design --project
npx -y @geocine/skills zinc-design-system --project
npx -y @geocine/skills skill-creator --global
```

Omit `--project` for a global install. Add `--copy` if you want copies instead of symlinks.

## Requirements

- Node.js 18 or newer
- Git available in `PATH`
- Access to the Git repository that contains your skills

## Common Commands

```bash
npx -y @geocine/skills
npx -y @geocine/skills frontend-design --project
npx -y @geocine/skills install frontend-design --project
npx -y @geocine/skills add frontend-design --project
npx -y @geocine/skills list
npx -y @geocine/skills install --skills frontend-design,zinc-design-system --project
npx -y @geocine/skills install --skills frontend-design --project --copy
npx -y @geocine/skills update
```

## Repo Override

```bash
npx -y @geocine/skills --repo-url <git-url>
```

or:

```bash
SKILLS_REPO_URL=<git-url> npx -y @geocine/skills
```

## Notes

- The CLI keeps a local cache of the skills repository to make repeated runs fast.
- You can install a specific skill directly with `npx -y @geocine/skills install <skill-name>` or `npx -y @geocine/skills <skill-name>`.
- By default it symlinks each selected target directly to the source skill directory; use `--copy` to write independent copies instead.
- `update` forces a cache refresh.
- `--no-pull` uses the existing cache without refreshing it.
