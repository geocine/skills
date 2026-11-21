---
name: council
description: Bring in four independent reviewers (Claude, Codex, Grok and Gemini, one per provider) to attack a design, a decision sheet, a document set or a change, then reconcile their verdicts and apply what holds. Use when the user says "council", "ask the council", "eval it with codex and grok", "ask gemini too", "get a second opinion from the other models", or wants a decision or a finished change reviewed before it is integrated or committed.
---

# Council

The council is four reviewers from four providers, each reading the same brief
and the same files, none seeing the others' answers. Its job is to find what the
author cannot see in their own work. You are the author's side: you write the
brief, check what comes back against the source, and decide with the user what
changes.

## Before you convene

Fix what you already know is wrong and run the project's checks. A reviewer's
time spent rediscovering a known problem is wasted. If the user wants to throw
the work away and explore something new, skip this and say so in the brief.

Put the thing under review in a form a reviewer can judge item by item. For a
design or a document set, that is a **decision sheet**: one numbered statement
per fact, each naming what it replaces and where it will live. Do not edit the
real documents first. Editing a large source before the verdicts means editing
it twice.

## The members

| Member | How to run it, read-only |
| --- | --- |
| Claude | A fresh subagent through the Agent tool (`general-purpose`, not a fork, so it does not inherit your view). Tell it not to edit. |
| Codex | `codex exec -s read-only -c model_reasoning_effort="high" -C <repo> --color never -o <out.md> - < <brief.md>` |
| Grok | `grok --prompt-file <brief.md> --cwd <repo> --reasoning-effort high --rules "Read-only review. Never create, edit or delete files."` with stdout to `<out.md>` |
| Gemini | Through the Cursor agent, run from inside the repo: `cursor-agent -p --mode ask --trust --model gemini-4-neon-high --output-format text "$(cat <brief.md>)"` with stdout to `<out.md>`. `--mode ask` is read-only; never pass `--force` or `--yolo`. `--trust` is needed or the run stops at a workspace prompt. |

Codex's read-only is a sandbox and Gemini's is the Cursor agent's ask mode. Grok's and Claude's are instructions only, so
run `git status --porcelain` before the round and after every member finishes,
and report any change a member made.

Use each provider's strongest model at high reasoning effort unless the user
names members, models or effort. For Gemini that is always `gemini-4-neon-high`. Check a member answers before the real run
(`codex login status`; a one-word `grok -p` prompt; `cursor-agent status`, and `cursor-agent --list-models` if the model name is refused). If a member is missing or
not signed in, say so and ask; never substitute a second model from a provider
already seated, and never stand in for a member yourself.

Sending files to Codex, Grok and Gemini (through Cursor) sends them to outside services. That is what
the user asked for when they asked for the council; do not widen it to anything
they did not name.

## The brief

All four get the same brief, and it is the only context they have.

- Write it to a file and pass the file. A shell heredoc mangles backslashes and
  quotes, and a long prompt on the command line is fragile.
- State that the review is read-only: no edits, no builds, no commits.
- Say what the project is in four or five lines, and where the current text is.
  Point at the compact form (generated Markdown, not megabytes of HTML).
- Say what the build or tests already prove, so nobody re-verifies it.
- Ask them to attack, not to praise. For each numbered item: **ACCEPT**,
  **AMEND** (the exact change) or **REJECT** (what to do instead), with the
  strongest objection, a short verbatim quote and file when the objection is a
  conflict with existing text, and **VERIFIED** (they read it) or **INFERRED**
  (from their own knowledge).
- Ask the platform or domain questions you could only infer an answer to, each
  with a confidence.
- Ask what the sheet leaves unsettled, most important first.
- Give a word limit. Give criteria, never the answer you expect.

Mark the calls you made alone as yours. A reviewer shown an unreviewed call as
if it were settled will treat it as settled.

## Running it

Start all four in the background in one step and write each answer to its own
file. Do not edit any file a member is still reading. While you wait, do work
that touches nothing under review: read the source passages you will need.

When an answer arrives, check its top findings against the source at once. A
review reads as confident whether or not it is right; a quote cut off before
its qualifier has misled this project before. Label what you re-read yourself
separately from what you are relaying.

## Reconciling

Write a second version of the sheet: for each item, the statement as it now
stands and what changed, with the member who raised it. Then sort the outcome:

- **All, or all but one, agree on a fix**: adopt it, and record the dissent.
- **They disagree, or the fix changes scope, security posture or a product
  promise**: it is the user's call. Bring it to them with a recommendation and
  the cost of each option. Do not pick silently.
- **A member is wrong on the facts**: say so with the passage that shows it,
  and keep the original.

Report the verdicts as a table. A member that gave no verdict on an item gets
`no verdict`; do not invent one.

```markdown
## Council review

Rounds: 2

| Item | Claude | Codex | Grok | Gemini | Outcome |
| --- | --- | --- | --- | --- | --- |
| B2 Trust boundaries | amend | reject | amend | amend | Rewritten: sealed macros |
| B4 Companion reach  | accept | amend | amend | accept | User chose desktop only |
```

## Applying

Integrate once, after the verdicts and the user's calls. Back up each file you
change and say where. Rebuild and run the checks. Then prove the change: search
for each old statement and show it is gone, because a green build only proves
the ids resolve, not that two passages agree.

Anything you had to decide while integrating that no member saw is a new
unreviewed call. List it for the user as such, and put it in front of the
council in the next round.

## Rounds

One full pass by all members is a round. A fresh review after changes starts a
new round, with a brief that says what changed since the last one. Stop when
the members have no rejections left and the remaining amendments are matters
of taste, or when the user says stop.

Reviews invite more scope every round. Keep the scope to what the user asked
the council to judge. New topics a member raises go on an "unsettled" list for
the user, not into this round's changes.

## Where things go

- Keep the brief, every member's raw answer, both versions of the sheet and a
  `reconciliation.md` (the verdict table, the calls you made alone, what is
  still unsettled) in `.council/<date>-<topic>/` at the workspace root, not in
  a temporary folder.
- Name each answer `member-<name>.md`. Never save one as `claude.md` or
  `agents.md`: on a case-insensitive filesystem those are loaded as instruction
  files by the next agent that works in the folder.
- While a round runs, the brief sits in a folder that holds no member's answer,
  so no member can read another's. Copy the answers in beside it afterwards.
- Council output is process. It changes the design; it does not appear in the
  product's documents. No verdict tables, member names or "the council found"
  in the docs themselves. In the Synapse Next docs the build rejects the phrase
  "design council".
- If the work ends in a pull request, put the review table in the description.
  Otherwise put it in your final reply.
