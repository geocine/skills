---
name: contributing-guide
description: >-
  Generate a CONTRIBUTING.md and a matching README Contributing section for a
  repository. Enforces an issue-first workflow with collaborator promotion, AI
  disclosure policy, and a PR checklist. Use when setting up contribution
  guidelines, creating a CONTRIBUTING.md, or adding a Contributing section to a
  README.
---

# Contributing Guide Generator

Create a `CONTRIBUTING.md` and a companion README section that enforce an
issue-first contribution workflow. The tone should be **friendly and relaxed** —
firm on the process, but never hostile.

## When to use

- User asks to create or update contribution guidelines
- User wants a CONTRIBUTING.md
- User wants a Contributing section in a README

## Step 1 — Gather context

Before generating, check:

1. **Repo name** — read the first heading of `README.md` or infer from the directory / git remote.
2. **Existing README** — read it so you know where to insert the Contributing section.
3. **Existing CONTRIBUTING.md** — if one exists, update rather than overwrite.

## Step 2 — Generate CONTRIBUTING.md

Use this template. Replace `{repo_name}` with the actual repository name.
Preserve the heading structure and section order; adapt wording only to fit the
project's tone (keep it relaxed for small projects, slightly more formal for
larger ones).

````markdown
# Contributing to {repo_name}

Thanks for your interest in contributing!

This is a small project, so the process is lightweight — but there is one firm
rule to keep things organized and protect maintainer time from drive-by PRs.

## The one rule: open an issue first

Before you start working on a PR, **open an issue** that describes:

- What you want to change or fix
- Why it matters / how it aligns with the project
- A rough idea of your approach

Then **wait for a thumbs-up** from a maintainer. If the change looks good, I'll
add you as a collaborator so you can push a branch and open the PR directly.

This keeps the project focused and avoids wasted effort on both sides.

## AI / LLM usage

AI-assisted contributions are welcome, but:

- You must **review, understand, and test** any AI-generated code before submitting.
- Disclose AI usage in the PR description (e.g. "AI tools used: Cursor, Copilot")
- PRs that look like unreviewed AI output (failing builds, generic filler, no
  evidence of testing) will be closed.

## Commit authorship

All commits must use **your own name and email** as the author — not a bot, AI
agent, or service account. If you use AI tools to help write code, that's fine
(see above), but the commit itself should come from you.

## PR checklist

Once you're a collaborator and have an approved issue:

- [ ] Reference the issue (`Fixes #N` or `Closes #N`)
- [ ] Commits are authored under your own name/email (not a bot or agent)
- [ ] Code builds and passes existing tests
- [ ] New features include tests where applicable
- [ ] Docs updated if the change affects public behavior
- [ ] Follow existing code style
- [ ] Keep changes focused — one logical change per PR

## PRs without an approved issue

PRs opened without a corresponding approved issue will be closed with a pointer
back to this file. Nothing personal — it just keeps the project manageable.

## Questions?

Open an issue. Happy to chat there.
````

## Step 3 — Add a Contributing section to the README

Insert a `## Contributing` section **directly above** the `## License` section
(or at the bottom if no License section exists). Use this template:

```markdown
## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md)
before opening a pull request.

The short version: **open an issue first** describing what you want to change
and wait for maintainer approval. If the change fits the project, I'll add you
as a collaborator so you can push a branch directly.
```

Do **not** add a separate link in any existing doc-links bar at the top of the
README unless the user asks for it.

## Tone guidelines

- Friendly, not corporate. Write like a person, not a legal document.
- Firm on process (issue-first is non-negotiable), light on threats.
- Avoid phrases like "slop", "spam", or "low-quality" — just state the process
  and the consequence (PR closed with a pointer to CONTRIBUTING.md).
- Use "nothing personal" or similar to keep it human.
