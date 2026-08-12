---
name: branch-backup-split-commits
description: Back up a large dirty Git worktree onto a safety branch, return to the original branch, split the same final change set into logical conventional commits, and verify the final branch tree exactly matches the backup. Use when the user says they made a large swath of changes, wants a backup branch before cleanup, wants changes separated one by one into conventional commits, wants to compare or align a branch with a backup branch, or asks to preserve all code changes while rewriting commit structure.
---

# Branch Backup Split Commits

## Workflow

Use this skill for Git repositories when the goal is to preserve a large snapshot first, then reconstruct it as clean conventional commits on another branch.

1. Capture context before changing refs.
   - Run `git status --short`, `git branch --show-current`, and inspect recent history with `git log --oneline -5`.
   - If the worktree is not clean and the user asked to back it up, keep all existing changes. Do not reset or discard anything.
   - Choose a backup branch under `backup/...`, for example `backup/pre-conventional-commits-YYYY-MM-DD` or a suffix if that branch exists.

2. Create and commit the backup snapshot.
   - Create the backup branch from the current branch with `git switch -c <backup-branch>`.
   - Stage the requested snapshot with `git add -A` unless the user excludes files.
   - Watch for embedded repository warnings. If present, state that Git will commit a gitlink (`mode 160000`) unless the user wants a submodule or exclusion.
   - Commit with a plain backup message such as `backup: pre conventional commits`.
   - Record the backup commit SHA and branch name.

3. Return to the target branch.
   - Switch back to the original branch, normally `main`.
   - If switching leaves untracked embedded-repo directories on disk, treat them as expected local leftovers unless they block the workflow.
   - Use the backup branch as the source of truth for the intended final tree.

4. Split the backup snapshot into logical conventional commits.
   - Prefer 2-5 commits, grouped by user-facing concern rather than by file extension.
   - Common groups:
     - `fix: ...` for bug fixes and behavioral corrections.
     - `feat: ...` for user-visible functionality.
     - `test: ...` for test-only changes when separable.
     - `docs: ...` for documentation-only changes.
     - `chore: ...` for tooling, generated metadata, or embedded repository references.
   - Restore or patch one group at a time from the backup branch.
   - Use `git add <explicit paths>` for each commit. Avoid staging unrelated files by accident.
   - Commit each group with a conventional commit subject.

5. Verify each meaningful slice.
   - Run focused tests for each slice when practical.
   - If Go tests fail because the default cache is outside the sandbox, rerun with `GOCACHE` inside the repository, e.g. PowerShell: `$env:GOCACHE="$PWD\.gocache"; go test ...`.
   - If golden tests fail only due CRLF/LF representation after checkout, report it specifically and avoid modifying restored backup content unless the user wants newline normalization.
   - Remove temporary local caches such as `.gocache` after tests.

6. Align with the backup.
   - After all split commits, compare the target branch to the backup branch:
     - `git diff --stat <target> <backup>`
     - `git rev-parse '<target>^{tree}'`
     - `git rev-parse '<backup>^{tree}'`
   - The tree hashes must match for exact alignment. An empty diff is helpful but tree hashes are the final check.
   - If the trees differ, inspect `git diff --name-status <target> <backup>`, restore missing pieces from the backup, commit or amend as appropriate, and repeat the tree-hash check.

## Guardrails

- Never use `git reset --hard`, `git checkout -- .`, or destructive cleanup unless the user explicitly asks.
- Preserve user changes. If an untracked or modified file appears unrelated, back it up if the user asked for "all changes".
- On Windows PowerShell, quote revision expressions that contain `^`, for example `git rev-parse 'main^{tree}'`.
- Branch names are path-like refs. A branch named `backup/foo` prevents creating a branch named exactly `backup`.
- Prefer explicit path staging for split commits. Use `git add -A` only for the initial all-changes backup or when the user explicitly wants everything.

## Final Response

Report:

- Backup branch and backup commit SHA.
- Split commits in order, with short SHAs and subjects.
- Whether the working tree is clean.
- The target and backup tree hashes when alignment succeeds.
- Any test commands run and any residual test caveats.
